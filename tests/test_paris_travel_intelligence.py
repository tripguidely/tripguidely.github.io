"""Synthetic travel-monitor tests. No network or real travel claims in fixtures."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from email.message import Message
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.error import URLError

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('paris_monitor', ROOT / 'scripts/paris-travel-intelligence.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
NOW = datetime(2026, 10, 22, 10, tzinfo=timezone.utc)


def feed(summary='Safety and security - general editorial update'):
    return {'metadata': {'generated': {'timestamp': int(NOW.timestamp())}}, 'data': {'FR': {
        'country-iso': 'FR', 'date-published': {'timestamp': int((NOW - timedelta(hours=1)).timestamp())},
        'recent-updates-type': 'Regular text update', 'has-regional-advisory': 0,
        'has-advisory-warning': 0, 'has-content': 1,
        'eng': {'url-slug': 'france', 'advisory-text': 'Exercise a high degree of caution',
                'recent-updates': summary}}}}


def event(**changes):
    e = {'id': 'synthetic-works', 'source': 'ratp', 'source_url': m.SOURCE_URLS['ratp'],
         'category': 'planned_works', 'locations': ['Synthetic station'],
         'starts_at': m.stamp(NOW + timedelta(hours=1)),
         'ends_at': m.stamp(NOW + timedelta(hours=5)),
         'verified_at': m.stamp(NOW - timedelta(hours=1)),
         'review_due_at': m.stamp(NOW + timedelta(hours=12)),
         'review_status': 'human_verified', 'reviewed_by': 'Synthetic test reviewer',
         'publication_requested': True,
         'confirmed_fact': 'Synthetic maintenance fixture, not a real disruption.',
         'summary_en': 'Synthetic maintenance fixture for testing only.',
         'relevance_en': 'Synthetic station journey planning.'}
    e.update(changes)
    return e


def registry(*events):
    return {'version': 2, 'events': list(events)}


def page(section=None):
    return '<head><title>Existing SEO</title></head>\n' + m.START + ' test -->\n' + (
        section or m.evergreen_section()) + '\n' + m.END + '\n<footer>Existing affiliate content</footer>\n'


def empty():
    return {'version': 2, 'signatures': {}, 'last_success_at': None, 'snapshot': None}


def run(events=(), previous=None, payload=None, now=NOW, public=None, fetcher=None):
    return m.monitor(now, registry(*events), public or page(), previous or empty(),
                     fetcher=fetcher or (lambda: payload or feed()))


class MonitorTests(unittest.TestCase):
    def test_new_official_signal_is_not_a_confirmed_paris_event(self):
        report, state, proposed = run(payload=feed('Safety - added information on demonstrations'))
        self.assertTrue(report['sources'][0]['changed'])
        self.assertEqual(report['sources'][0]['category_hint'], 'demonstration')
        self.assertFalse(proposed)
        self.assertFalse(report['proposal_available'])
        self.assertIsNone(report['safety_conclusion'])
        self.assertFalse(report['publication_authorized'])
        self.assertEqual(report['events'], [])

    def test_unchanged_information_and_duplicates_do_not_repeat_findings(self):
        first, state, _ = run()
        second, _, proposed = run(previous=state)
        self.assertEqual(len(first['new_findings']), 1)
        self.assertEqual(second['new_findings'], [])
        self.assertFalse(second['sources'][0]['changed'])
        self.assertFalse(proposed)

    def test_unrelated_countries_and_export_clock_do_not_trigger_changes(self):
        _, state, _ = run()
        data = feed()
        data['data']['XX'] = {'unrelated': 'noise'}
        data['metadata']['generated']['timestamp'] += 50
        report, _, _ = run(previous=state, payload=data)
        self.assertEqual(report['new_findings'], [])

    def test_semantic_whitespace_is_normalized(self):
        _, state, _ = run(payload=feed('General\n  advice'))
        report, _, _ = run(previous=state, payload=feed(' General advice '))
        self.assertEqual(report['new_findings'], [])

    def test_publication_date_change_is_review_signal_even_with_same_summary(self):
        _, state, _ = run()
        data = feed()
        data['data']['FR']['date-published']['timestamp'] += 60
        report, _, proposed = run(previous=state, payload=data)
        self.assertTrue(report['sources'][0]['changed'])
        self.assertEqual(len(report['new_findings']), 1)
        self.assertFalse(proposed)
        self.assertEqual(report['sources'][0]['change_kind'], 'publication metadata changed; significance requires review')

    def test_national_advisory_level_change_is_significant_but_not_local_event_copy(self):
        _, state, _ = run()
        data = feed()
        data['data']['FR']['eng']['advisory-text'] = 'Avoid non-essential travel'
        report, _, proposed = run(previous=state, payload=data)
        self.assertEqual(report['sources'][0]['change_kind'], 'national advisory level or scope changed')
        self.assertFalse(proposed)

    def test_precise_human_record_generates_only_unapplied_proposal(self):
        report, _, proposed = run(events=[event()])
        self.assertTrue(report['proposal_available'])
        self.assertIn('Dated notice:', proposed)
        self.assertIn('Synthetic maintenance', proposed)
        self.assertIn('snapshot does not confirm', proposed)
        self.assertIn('data-travel-review-deadline', proposed)
        self.assertIn('2026-10-22T17:00:00+02:00', proposed)  # end precedes review deadline
        self.assertNotIn('a/hotels/paris/luxury-hotels/', proposed)

    def test_precise_event_without_publication_request_has_no_patch(self):
        report, _, proposed = run(events=[event(publication_requested=False)])
        self.assertFalse(proposed)
        self.assertFalse(report['proposal_available'])

    def test_expired_event_is_excluded_without_claim_of_normality(self):
        e = event(starts_at=m.stamp(NOW - timedelta(hours=4)), ends_at=m.stamp(NOW - timedelta(hours=1)))
        report, _, proposed = run(events=[e])
        self.assertEqual(report['events'][0]['status'], 'expired')
        self.assertIn('does not prove normal', report['events'][0]['reason'])
        self.assertFalse(proposed)

    def test_expired_public_notice_proposes_removal_and_offline_guard_fails(self):
        e = event()
        rendered = m.proposed_section(m.event_records(registry(e), NOW))
        later = NOW + timedelta(hours=6)
        report, _, proposed = run(events=[e], now=later, public=page(rendered))
        self.assertEqual(report['public_status'], 'review overdue')
        self.assertEqual(report['proposal_kind'], 'removal / evergreen fallback')
        self.assertIn('-        <p><strong>Dated notice:', proposed)
        self.assertNotIn('+        <p><strong>Dated notice:', proposed)
        self.assertIsNotNone(m.public_status(page(rendered), later, [e])[1])

    def test_unknown_end_requires_short_review_and_never_predicts_reopening(self):
        e = event(ends_at=None)
        report, _, proposed = run(events=[e])
        self.assertIn('End time not confirmed', proposed)
        later, _, proposed = run(events=[e], now=NOW + timedelta(hours=13))
        self.assertEqual(later['events'][0]['status'], 'review overdue')
        self.assertFalse(proposed)

    def test_legacy_v1_date_is_preserved_but_not_promoted_to_precise_verification(self):
        e = event(verified_at=None, verified_on='2026-10-22', reviewed_by=None,
                  review_status='legacy_reference', publication_requested=False)
        report, _, proposed = run(events=[e])
        self.assertEqual(report['events'][0]['status'], 'verification required')
        self.assertIn('exact time not recorded', m.markdown(report))
        self.assertFalse(proposed)

    def test_network_failure_retains_last_good_observation_and_deduplicates_error(self):
        _, good, _ = run()
        def broken():
            raise URLError('private token and response must never be logged')
        report, failed, proposed = run(previous=good, fetcher=broken)
        self.assertTrue(report['network_failure'])
        self.assertEqual(failed['snapshot'], good['snapshot'])
        self.assertEqual(failed['last_success_at'], good['last_success_at'])
        self.assertIsNone(report['sources'][0]['checked_at'])
        self.assertIsNone(report['safety_conclusion'])
        self.assertFalse(proposed)
        self.assertNotIn('private token', json.dumps(report))
        again, _, _ = run(previous=failed, fetcher=broken)
        self.assertEqual(again['new_findings'], [])
        recovered, _, _ = run(previous=failed)
        self.assertFalse(recovered['network_failure'])
        self.assertEqual(len(recovered['new_findings']), 1)

    def test_stale_or_future_exports_and_unknown_schema_require_verification(self):
        for offset in (-49 * 3600, 11 * 60):
            data = feed()
            data['metadata']['generated']['timestamp'] += offset
            report, _, proposed = run(payload=data)
            self.assertTrue(report['network_failure'])
            self.assertFalse(proposed)
        report, _, _ = run(payload={'unexpected': 'schema'})
        self.assertTrue(report['network_failure'])

    def test_unavailable_source_never_claims_no_disruption(self):
        report, _, _ = run(fetcher=lambda: (_ for _ in ()).throw(TimeoutError()))
        self.assertTrue(all(s['status'] == 'verification required' for s in report['sources']))
        self.assertTrue(all(s['checked_at'] is None for s in report['sources']))
        self.assertIsNone(report['safety_conclusion'])

    def test_failed_verification_with_human_record_still_has_no_new_notice_patch(self):
        report, _, proposed = run(events=[event()], fetcher=lambda: (_ for _ in ()).throw(TimeoutError()))
        self.assertFalse(proposed)
        self.assertFalse(report['proposal_available'])
        self.assertTrue(report['network_failure'])

    def test_oversized_feed_is_refused(self):
        headers = Message()
        headers['Content-Type'] = 'application/json'
        response = SimpleNamespace(status=200, geturl=lambda: m.FEED, headers=headers,
                                   read1=lambda _: b'x' * (m.MAX_BYTES + 1))
        fake = unittest.mock.MagicMock()
        fake.open.return_value.__enter__.return_value = response
        with patch.object(m, 'build_opener', return_value=fake), self.assertRaises(ValueError):
            m.fetch_canada()

    def test_oversized_cached_json_and_excessive_nesting_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / 'state.json'
            target.write_bytes(b' ' * (m.MAX_BYTES + 1))
            with self.assertRaises(ValueError):
                m.load_json(target)
            _, note = m.read_state(target)
            self.assertIn('invalid', note)
        report, _, proposed = run(fetcher=lambda: (_ for _ in ()).throw(RecursionError()))
        self.assertTrue(report['network_failure'])
        self.assertFalse(proposed)

    def test_no_events_means_no_detected_event_records_not_safe_paris(self):
        report, _, proposed = run()
        self.assertEqual(report['events'], [])
        self.assertEqual(report['coverage'], 'partial')
        self.assertIsNone(report['safety_conclusion'])
        self.assertFalse(proposed)

    def test_works_and_demonstrations_remain_separate(self):
        self.assertEqual(m.category_hint('Planned works; demonstration mentioned elsewhere'), 'planned_works')
        self.assertEqual(m.category_hint('Information on demonstrations'), 'demonstration')
        self.assertEqual(m.category_hint('Rail disruption'), 'transport_disruption')
        self.assertEqual(m.category_hint('Entry requirements'), 'general_advice')
        report, _, _ = run(events=[event()], payload=feed('Information on demonstrations'))
        self.assertEqual(report['events'][0]['category'], 'planned_works')

    def test_invalid_and_ambiguous_dates_or_duplicate_events_are_rejected(self):
        for changes in ({'starts_at': '24/10'}, {'verified_at': '2026-10-22'},
                        {'verified_at': '2026-10-22T10:00:00'},
                        {'review_due_at': m.stamp(NOW + timedelta(days=3))},
                        {'verified_at': m.stamp(NOW + timedelta(hours=1))}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                run(events=[event(**changes)])
        with self.assertRaises(ValueError):
            run(events=[event(), event()])
        with self.assertRaises(ValueError):
            run(events=[event(), event(id='same-facts-different-id')])

    def test_external_urls_and_markup_are_not_accepted_as_event_data(self):
        for changes in ({'source_url': 'https://www.ratp.fr.evil.test/'},
                        {'source_url': 'file:///etc/passwd'},
                        {'source_url': 'https://www.ratp.fr/infos-trafic?redirect=https://evil.test/'},
                        {'summary_en': '<script>malicious()</script>'},
                        {'publication_requested': 'true'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                run(events=[event(**changes)])

    def test_feed_markup_or_unknown_level_never_generates_copy(self):
        for risk in ('Safe everywhere', '<img src=x onerror=x>'):
            data = feed()
            data['data']['FR']['eng']['advisory-text'] = risk
            report, _, proposed = run(payload=data)
            self.assertTrue(report['network_failure'])
            self.assertFalse(proposed)

    def test_redirects_and_html_challenges_are_refused_without_retry(self):
        with self.assertRaises(ValueError):
            m.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://other.test/')
        headers = Message()
        headers['Content-Type'] = 'text/html'
        response = SimpleNamespace(status=200, geturl=lambda: m.FEED, headers=headers)
        fake = unittest.mock.MagicMock()
        fake.open.return_value.__enter__.return_value = response
        with patch.object(m, 'build_opener', return_value=fake), self.assertRaises(ValueError):
            m.fetch_canada()
        self.assertEqual(fake.open.call_count, 1)

    def test_unmanaged_v1_alert_is_detected_and_replaced_only_in_patch(self):
        public = page('<section id="travel-updates">Closures from an old bulletin</section>')
        report, _, proposed = run(public=public)
        self.assertEqual(report['public_status'], 'verification required')
        self.assertIn('evergreen', report['proposal_kind'])
        self.assertIn('Closures from an old bulletin', public)
        self.assertIn('-<section', proposed)

    def test_state_loss_corruption_gap_and_future_timestamp_are_explicit(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / 'state.json'
            state, note = m.read_state(target)
            self.assertIn('initial comparison', note)
            target.write_text('{"version":2,"version":2}')
            state, note = m.read_state(target)
            self.assertIn('invalid', note)
        _, previous, _ = run()
        previous['last_success_at'] = m.stamp(NOW - timedelta(hours=40))
        report, _, _ = run(previous=previous)
        self.assertIn('gap', report['state_note'])
        previous['last_success_at'] = m.stamp(NOW + timedelta(days=1))
        report, _, _ = run(previous=previous)
        self.assertIn('future', report['state_note'])

    def test_paris_timezone_handles_dst_boundary(self):
        self.assertEqual(m.stamp(datetime(2026, 10, 25, 0, 30, tzinfo=timezone.utc)), '2026-10-25T02:30:00+02:00')
        self.assertEqual(m.stamp(datetime(2026, 10, 25, 1, 30, tzinfo=timezone.utc)), '2026-10-25T02:30:00+01:00')

    def test_reports_without_proposal_remove_old_output_and_never_write_pages(self):
        before = (ROOT / m.HUB).read_bytes()
        report, state, proposed = run()
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            (out / 'proposal.patch').write_text('old proposal')
            (out / 'draft-pr.md').write_text('old draft')
            m.write_outputs(out, report, state, proposed)
            self.assertFalse((out / 'proposal.patch').exists())
            self.assertFalse((out / 'draft-pr.md').exists())
            self.assertTrue((out / 'report.md').exists())
            self.assertEqual(m.load_json(out / 'report.json')['safety_conclusion'], None)
        self.assertEqual((ROOT / m.HUB).read_bytes(), before)

    def test_configuration_error_produces_report_without_state_or_proposal(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            with patch.object(m, 'load_json', side_effect=ValueError('bad registry')), patch.object(m, 'fetch_canada') as fetch:
                self.assertEqual(m.main(['--output', str(out)]), 2)
            self.assertFalse(fetch.called)
            self.assertIn('Verification required', (out / 'report.md').read_text())
            self.assertFalse((out / 'proposal.patch').exists())
            self.assertFalse((out / 'state.json').exists())

    def test_workflow_has_only_read_permissions_no_publish_and_pinned_actions(self):
        workflow = (ROOT / '.github/workflows/paris-travel-intelligence.yml').read_text()
        self.assertIn('contents: read', workflow)
        for forbidden in ('contents: write', 'pull-requests: write', 'issues: write', 'pull_request_target:', 'secrets.', 'git push', 'gh pr', 'deploy', 'auto-merge'):
            self.assertNotIn(forbidden, workflow)
        self.assertIn('workflow_dispatch:', workflow)
        self.assertIn("23 5 * * *", workflow)
        self.assertIn("github.ref == 'refs/heads/main'", workflow)
        self.assertNotIn('needs: validate', workflow)  # stale-page gate must not prevent removal report
        import re
        actions = re.findall(r'uses: (\S+)', workflow)
        self.assertTrue(actions)
        self.assertTrue(all(re.fullmatch(r'actions/[a-z-]+(?:/[a-z]+)?@[0-9a-f]{40}', a) for a in actions))


if __name__ == '__main__':
    unittest.main()
