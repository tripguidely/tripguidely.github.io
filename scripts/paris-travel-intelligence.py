#!/usr/bin/env python3
"""Paris editorial monitoring. Standard library only; never writes public files.

Network text is evidence for a reviewer, never an instruction or approved copy.
Only the documented Canadian open-data endpoint is fetched. Other sources stay
manual until an authorized, tested adapter exists. No Git, shell or GitHub writes.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import difflib
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import socket
import sys
import time
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
PARIS = ZoneInfo('Europe/Paris')
UTC = timezone.utc
FEED = 'https://data.international.gc.ca/travel-voyage/index-alpha-eng.json'
REGISTRY = 'docs/travel-intelligence/paris-events.json'
HUB = 'hotels/paris/index.html'
MAX_BYTES = 2_000_000
TIMEOUT = 15
START = '      <!-- PARIS TRAVEL UPDATES START:'
END = '      <!-- PARIS TRAVEL UPDATES END -->'
SOURCE_URLS = {
    'canada': 'https://travel.gc.ca/destinations/france',
    'ratp': 'https://www.ratp.fr/infos-trafic',
    'prefecture': 'https://www.prefecturedepolice.interieur.gouv.fr/',
    'diplomatie': 'https://www.diplomatie.gouv.fr/en/services-to-foreigners/visiting-france',
    'sncf': 'https://www.sncf-connect.com/aide/informations-situation-perturbee',
}
CATEGORIES = {'demonstration', 'transport_disruption', 'planned_works', 'general_advice'}
RISK = {'Exercise normal security precautions', 'Exercise a high degree of caution',
        'Avoid non-essential travel', 'Avoid all travel'}


def stamp(value):
    return value.astimezone(PARIS).isoformat(timespec='seconds')


def instant(value):
    if not isinstance(value, str) or not re.fullmatch(
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})', value):
        raise ValueError('A full ISO timestamp with timezone is required')
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.utcoffset() is None:
        raise ValueError('Missing timezone')
    return result


def text(value, limit=800):
    if not isinstance(value, str) or len(value) > limit:
        raise ValueError('Invalid or oversized text')
    if any(unicodedata.category(c).startswith('C') and c not in '\n\t\r' for c in value):
        raise ValueError('Control characters are not allowed')
    result = ' '.join(unicodedata.normalize('NFC', value).split())
    if not result or '<' in result or '>' in result:
        raise ValueError('Nonempty plain text required')
    return result


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
                                     separators=(',', ':')).encode()).hexdigest()


def load_json(path):
    with path.open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('Oversized JSON')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result
    return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Invalid number')))


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Redirect refused; source needs manual review')


def fetch_canada():
    """One allowlisted request, no retry/redirect/authentication/cookies.

    Socket timeout plus workflow timeout bound failure. A wall-time check between
    small reads limits slow responses; compressed responses are not requested.
    """
    request = Request(FEED, headers={
        'User-Agent': 'TripGuidelyTravelMonitor/2 (+https://tripguidely.github.io/contact/)',
        'Accept': 'application/json', 'Accept-Encoding': 'identity',
    })
    started = time.monotonic()
    with build_opener(NoRedirect()).open(request, timeout=TIMEOUT) as response:
        if response.status != 200 or response.geturl() != FEED:
            raise ValueError('Unexpected HTTP response')
        if response.headers.get_content_type() != 'application/json':
            raise ValueError('Expected JSON; challenge or format change requires review')
        if response.headers.get('Content-Encoding', 'identity') != 'identity':
            raise ValueError('Unexpected content encoding')
        chunks, size = [], 0
        while True:
            chunk = response.read1(16384)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_BYTES or time.monotonic() - started > 30:
                raise ValueError('Response size or time limit exceeded')
            chunks.append(chunk)
    raw = b''.join(chunks)
    # JSON contains no executable content; nothing is evaluated or imported.
    def unique(pairs):
        out = {}
        for k, v in pairs:
            if k in out:
                raise ValueError('Duplicate JSON key')
            out[k] = v
        return out
    return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Invalid number')))


def canada_snapshot(payload, now):
    """Country summary only. It cannot establish Paris event dates or locations."""
    try:
        entry = payload['data']['FR']
        generated_ts = payload['metadata']['generated']['timestamp']
        published_ts = entry['date-published']['timestamp']
        if type(generated_ts) is not int or type(published_ts) is not int:
            raise ValueError('Invalid source timestamps')
        generated = datetime.fromtimestamp(generated_ts, UTC)
        published = datetime.fromtimestamp(published_ts, UTC)
        if generated > now + timedelta(minutes=10) or now - generated > timedelta(hours=48):
            raise ValueError('Source export is stale or future-dated')
        if published > generated + timedelta(minutes=10):
            raise ValueError('Inconsistent source timestamps')
        if entry['country-iso'] != 'FR' or entry['eng']['url-slug'] != 'france':
            raise ValueError('Unexpected country')
        risk = text(entry['eng']['advisory-text'], 160)
        if risk not in RISK and risk not in {x + ' (with regional advisories)' for x in RISK}:
            raise ValueError('Unknown advisory level')
        update = text(entry['eng']['recent-updates'])
        update_type = text(entry['recent-updates-type'], 120)
        for key in ('has-regional-advisory', 'has-advisory-warning', 'has-content'):
            if type(entry[key]) is not int or entry[key] not in (0, 1):
                raise ValueError('Invalid advisory flag')
        if entry['has-content'] != 1:
            raise ValueError('France content unavailable')
        result = {'risk': risk, 'update_summary': update, 'update_type': update_type,
                  'regional_advisory': entry['has-regional-advisory'],
                  'advisory_warning': entry['has-advisory-warning'],
                  'published_at': stamp(published)}
        return result, stamp(generated)
    except (KeyError, TypeError, OverflowError, OSError) as exc:
        raise ValueError('Canadian feed schema changed') from exc


def category_hint(summary):
    """Review routing, never event confirmation. Works take priority over protests."""
    value = summary.lower()
    if any(x in value for x in ('planned work', 'maintenance', 'engineering work')):
        return 'planned_works'
    if any(x in value for x in ('demonstration', 'protest')):
        return 'demonstration'
    if any(x in value for x in ('transport', 'rail', 'metro', 'strike')):
        return 'transport_disruption'
    return 'general_advice'


def read_state(path):
    if path is None or not path.exists():
        return {'version': 2, 'signatures': {}, 'last_success_at': None,
                'snapshot': None}, 'No previous state; initial comparison requires review.'
    try:
        state = load_json(path)
        if state['version'] != 2 or not isinstance(state['signatures'], dict) or len(state['signatures']) > 100:
            raise ValueError('Invalid state')
        for key, value in state['signatures'].items():
            text(key, 160)
            if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
                raise ValueError('Invalid state signature')
        if state['last_success_at'] is not None:
            instant(state['last_success_at'])
        if state['snapshot'] is not None and not isinstance(state['snapshot'], dict):
            raise ValueError('Invalid state snapshot')
        return state, None
    except (ValueError, KeyError, TypeError, OSError, RecursionError):
        return {'version': 2, 'signatures': {}, 'last_success_at': None,
                'snapshot': None}, 'State invalid; comparison reset, verification required.'


def event_records(registry, now):
    if registry.get('version') != 2 or not isinstance(registry.get('events'), list) or len(registry['events']) > 30:
        raise ValueError('Invalid event registry')
    records, ids, identities = [], set(), set()
    for original in registry['events']:
        event = dict(original)
        ident = event.get('id', '')
        if not re.fullmatch('[a-z0-9-]{1,60}', ident) or ident in ids:
            raise ValueError('Duplicate or invalid event ID')
        ids.add(ident)
        if event.get('category') not in CATEGORIES or event.get('source') not in SOURCE_URLS:
            raise ValueError('Unknown source or category')
        if event.get('source_url') != SOURCE_URLS[event['source']]:
            raise ValueError('Only exact reviewed official reference URLs are allowed')
        start = instant(event['starts_at']) if event.get('starts_at') else None
        end = instant(event['ends_at']) if event.get('ends_at') else None
        due = instant(event['review_due_at'])
        if end and (not start or end <= start):
            raise ValueError('Invalid event interval')
        if event.get('review_status') not in ('legacy_reference', 'verification_required', 'human_verified'):
            raise ValueError('Invalid review status')
        if type(event.get('publication_requested')) is not bool:
            raise ValueError('Publication request must be an explicit boolean')
        verified = instant(event['verified_at']) if event.get('verified_at') else None
        if verified and verified > now + timedelta(minutes=5):
            raise ValueError('Future verification')
        if verified and not verified < due <= verified + timedelta(hours=24):
            raise ValueError('Review deadline must be within 24 hours of verification')
        if not isinstance(event.get('locations'), list) or not 1 <= len(event['locations']) <= 12:
            raise ValueError('Explicit affected locations required')
        event['locations'] = [text(x, 100) for x in event['locations']]
        event['summary_en'] = text(event['summary_en'], 500)
        event['relevance_en'] = text(event['relevance_en'], 300)
        event['confirmed_fact'] = text(event['confirmed_fact'], 600)
        identity = digest([event['source'], event['category'], stamp(start) if start else None,
                           stamp(end) if end else None, sorted(x.casefold() for x in event['locations']),
                           event['confirmed_fact'].casefold()])
        if identity in identities:
            raise ValueError('Duplicate event facts; consolidate the records before review')
        identities.add(identity)
        status = 'verification required'
        reason = 'Human verification with a recorded time is required.'
        if end and end <= now:
            status, reason = 'expired', 'Known event interval ended; this does not prove normal conditions.'
        elif due <= now:
            status, reason = 'review overdue', 'Review deadline elapsed; end of disruption is not established.'
        elif event['review_status'] == 'human_verified' and verified:
            text(event.get('reviewed_by'), 100)
            if not start:
                raise ValueError('Verified temporary event needs an explicit start')
            status, reason = 'reviewed proposal candidate', 'Facts entered by a human; publication still requires approval.'
        event['status'], event['reason'] = status, reason
        records.append(event)
    return records


def evergreen_section():
    return '''      <section id="travel-updates" class="callout tg-callout tg-guide-tip" aria-labelledby="travel-updates-title" tabindex="-1">
        <h2 id="travel-updates-title">Paris travel updates</h2>
        <p>For your travel dates, check the <a href="https://www.ratp.fr/infos-trafic">RATP traffic bulletin (French)</a>, <a href="https://www.sncf-connect.com/aide/informations-situation-perturbee">SNCF train information (French)</a> and <a href="https://travel.gc.ca/destinations/france">Canada's France travel advice</a>. Conditions can vary by neighborhood, day and time. Allow extra time for your hotel journey and check attraction access notices before setting out.</p>
        <p>Planning reference reviewed: <time datetime="2026-10-22">22 October 2026</time>. Recheck the official sources before each journey; this page does not provide live service status.</p>
      </section>'''


def section_bounds(page):
    if page.count(START) != 1 or page.count(END) != 1:
        raise ValueError('Expected one existing V1 section boundary')
    start = page.index('\n', page.index(START)) + 1
    end = page.index(END)
    if start >= end:
        raise ValueError('Invalid section boundaries')
    return start, end


class DeadlineParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.deadlines = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if 'data-travel-review-deadline' in values:
            if tag != 'time' or 'datetime' not in values:
                raise ValueError('Invalid public deadline')
            self.deadlines.append(instant(values['datetime']))


def public_status(page, now, events=None):
    start, end = section_bounds(page)
    section = page[start:end].rstrip()
    parser = DeadlineParser()
    parser.feed(section)
    if section == evergreen_section():
        return 'evergreen', None
    if not parser.deadlines:
        return 'verification required', 'Unmanaged dated content; replace with evergreen reference or reviewed dated template.'
    if any(x <= now for x in parser.deadlines):
        return 'review overdue', 'Published snapshot needs removal or re-verification; no all-clear is inferred.'
    if events is None or section != proposed_section(events):
        return 'verification required', 'Public snapshot does not match the validated human-reviewed registry.'
    return 'dated snapshot', None


def proposed_section(events):
    section = evergreen_section()
    notices = []
    for event in events:
        # No text from the Canadian feed is eligible for this path.
        if event['status'] != 'reviewed proposal candidate' or event.get('publication_requested') is not True:
            continue
        esc = html.escape
        end = stamp(instant(event['ends_at'])) if event.get('ends_at') else 'End time not confirmed'
        deadline = min(instant(event['review_due_at']), instant(event['ends_at'])) if event.get('ends_at') else instant(event['review_due_at'])
        notices.append(
            '        <p><strong>Dated notice:</strong> ' + esc(event['summary_en']) +
            ' Affected: ' + esc(', '.join(event['locations'])) +
            '. From ' + esc(stamp(instant(event['starts_at']))) + '; ' + esc(end) +
            '. Verified ' + esc(stamp(instant(event['verified_at']))) +
            '. Review due: <time data-travel-review-deadline="" datetime="' + esc(stamp(deadline), quote=True) +
            '">' + esc(stamp(deadline)) + '</time>. ' +
            '<a href="' + esc(event['source_url'], quote=True) + '">Official source</a>. ' +
            'This dated snapshot does not confirm conditions after verification.</p>')
    if notices:
        section = section.replace('      </section>', '\n'.join(notices) + '\n      </section>')
    return section


def replacement_patch(page, section):
    start, end = section_bounds(page)
    after = page[:start] + section + '\n' + page[end:]
    return ''.join(difflib.unified_diff(page.splitlines(keepends=True), after.splitlines(keepends=True),
                                        fromfile='a/' + HUB, tofile='b/' + HUB))


def monitor(now, registry, page, previous, fetcher=fetch_canada, state_note=None):
    if previous.get('last_success_at'):
        last = instant(previous['last_success_at'])
        if last > now + timedelta(minutes=5):
            previous = {'version': 2, 'signatures': {}, 'last_success_at': None, 'snapshot': None}
            state_note = 'State timestamp is in the future; comparison reset, verification required.'
        elif now - last > timedelta(hours=36):
            state_note = 'Monitoring gap over 36 hours since last successful check; changes during the gap may be missing.'
    source = {'id': 'canada', 'url': SOURCE_URLS['canada'], 'feed_url': FEED,
              'publisher': 'Government of Canada / Global Affairs Canada',
              'licence': 'Open Government Licence - Canada',
              'attempted_at': stamp(now), 'checked_at': None, 'status': 'verification required',
              'last_success_at': previous.get('last_success_at')}
    snapshot, hard_failure = None, False
    try:
        snapshot, generated = canada_snapshot(fetcher(), now)
        source.update(status='checked', checked_at=stamp(now), snapshot=snapshot, export_generated_at=generated,
                      last_success_at=stamp(now), category_hint=category_hint(snapshot['update_summary']),
                      interpretation='Country-level change signal only; Paris dates and places require human review.')
        source['changed'] = previous.get('snapshot') != snapshot
        old = previous.get('snapshot')
        if old is None:
            source['change_kind'] = 'initial observation'
        elif any(old.get(k) != snapshot[k] for k in ('risk', 'regional_advisory', 'advisory_warning')):
            source['change_kind'] = 'national advisory level or scope changed'
        elif old.get('update_summary') != snapshot['update_summary']:
            source['change_kind'] = 'summary changed; significance requires review'
        elif source['changed']:
            source['change_kind'] = 'publication metadata changed; significance requires review'
        else:
            source['change_kind'] = 'unchanged'
    except (ValueError, TypeError, HTTPError, URLError, TimeoutError, socket.timeout,
            OSError, UnicodeError, json.JSONDecodeError, RecursionError):
        # Never put response bodies, credentials or detailed network exceptions in logs.
        source['reason'] = 'Official feed inaccessible, stale or invalid; no safety conclusion can be made.'
        hard_failure = True
    events = event_records(registry, now)
    public, problem = public_status(page, now, events)
    # A failed verification can only propose removal of stale/unmanaged content.
    # It cannot produce a new factual notice, even from a human-entered record.
    section_start, section_end = section_bounds(page)
    desired = evergreen_section() if problem else (
        page[section_start:section_end].rstrip() if hard_failure else proposed_section(events))
    patch = replacement_patch(page, desired)
    findings = []
    signatures = {}
    def record(key, value, message):
        signature = digest(value)
        signatures[key] = signature
        findings.append({'id': key, 'new': previous.get('signatures', {}).get(key) != signature,
                         'message': message})
    if snapshot is not None:
        record('canada', snapshot, 'Official France advisory summary observed; inspect changes and the full source before interpreting.')
    else:
        record('canada', {'error': source['reason']}, source['reason'])
    for event in events:
        record('event:' + event['id'], {k: event.get(k) for k in ('status', 'verified_at', 'review_due_at', 'ends_at', 'confirmed_fact')},
               event['status'] + ': ' + event['id'] + '. ' + event['reason'])
    if problem:
        record('public', {'status': public, 'problem': problem}, problem)
    if state_note:
        record('state', state_note, state_note)
    manual = [{'id': ident, 'url': url, 'status': 'verification required',
               'checked_at': None, 'reason': 'Manual reference only; no authorized reliable adapter is enabled.'}
              for ident, url in SOURCE_URLS.items() if ident != 'canada']
    report = {'version': 2, 'generated_at_paris': stamp(now), 'coverage': 'partial',
              'status': 'verification required', 'public_status': public,
              'scope': 'Canadian France advice summary plus local expiry review; not Paris live transport monitoring.',
              'sources': [source] + manual, 'state_note': state_note,
              'events': events, 'new_findings': [x for x in findings if x['new']],
              'pending_review': findings, 'proposal_available': bool(patch),
              'proposal_kind': ('removal / evergreen fallback' if problem else 'human-entered dated snapshot') if patch else None,
              'publication_authorized': False, 'network_failure': hard_failure,
              'safety_conclusion': None}
    next_state = {'version': 2, 'signatures': signatures,
                  'last_success_at': source['last_success_at'],
                  'snapshot': snapshot if snapshot is not None else previous.get('snapshot')}
    return report, next_state, patch


def markdown(report):
    lines = ['# Paris travel intelligence — human review', '',
             '- Run time (Paris): ' + report['generated_at_paris'],
             '- Coverage: **partial**. Status: **verification required**.',
             '- ' + report['scope'],
             '- No safety conclusion, automatic publication, PR, notification or all-clear.',
             '- New findings: ' + str(len(report['new_findings'])),
             '- Public section: ' + report['public_status'], '']
    if report['state_note']:
        lines += [html.escape(report['state_note']), '']
    for source in report['sources']:
        lines += ['## ' + source['id'], '', '[' + source['id'] + '](' + source['url'] + ')',
                  '- Status: ' + source['status'],
                  '- Consulted: ' + (source.get('checked_at') or 'not automatically consulted')]
        if source.get('last_success_at'):
            lines.append('- Last successful automated check: ' + source['last_success_at'])
        if source.get('snapshot'):
            # Escape Markdown/HTML so source text cannot impersonate links or markup.
            safe = lambda s: html.escape(s).replace('`', '&#96;').replace('[', '&#91;').replace(']', '&#93;')
            lines += ['- Advisory: ' + safe(source['snapshot']['risk']),
                      '- Update signal: ' + safe(source['snapshot']['update_summary']),
                      '- Source published: ' + source['snapshot']['published_at'],
                      '- Category hint (unconfirmed): ' + source['category_hint'],
                      '- Change classification: ' + source['change_kind'],
                      '- Changed since last good snapshot: ' + str(source['changed']).lower()]
        if source.get('reason'):
            lines.append('- ' + source['reason'])
        lines.append('')
    lines += ['## Human-entered event records', '']
    for event in report['events']:
        safe = lambda s: html.escape(str(s)).replace('`', '&#96;').replace('[', '&#91;').replace(']', '&#93;')
        lines += ['- ' + event['id'] + ': **' + event['status'] + '**; review due ' + event['review_due_at'] +
                  '. ' + event['reason'],
                  '  Source: ' + event['source_url'],
                  '  Verified at: ' + (event.get('verified_at') or 'exact time not recorded; requires re-verification'),
                  '  Confirmed fact (human record): ' + safe(event['confirmed_fact']),
                  '  Category: ' + event['category'] + '; affected places: ' + safe(', '.join(event['locations'])),
                  '  Starts: ' + (event.get('starts_at') or 'unknown') + '; ends: ' + (event.get('ends_at') or 'unknown'),
                  '  Relevance: ' + safe(event['relevance_en']),
                  '  Candidate English copy (not authorized): ' + safe(event['summary_en'])
                  if event['status'] == 'reviewed proposal candidate' else
                  '  Public copy withheld pending precise human re-verification.']
    lines += ['', '## Publication proposal', '',
              'A bounded proposal.patch and draft-pr.md are attached for human review only.' if report['proposal_available']
              else 'No publication proposal. Raw source changes never generate public event copy.', '',
              'Open the official pages manually. Confirm place, cause, start/end, exact Paris verification time and travel relevance.',
              'If approved, apply only the reviewed patch locally, run the expiry guard and official site audit, then request explicit Draft PR authorization.',
              'An elapsed deadline means re-verification or removal, never proof that normal service resumed.', '']
    return '\n'.join(lines)


def write_outputs(out, report, state, patch):
    out.mkdir(parents=True, exist_ok=True)
    for name, value in [('report.json', report), ('state.json', state)]:
        (out / name).write_text(json.dumps(value, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')
    (out / 'report.md').write_text(markdown(report), encoding='utf-8')
    # Reusing an output directory must not leave a stale proposal behind.
    for name in ('proposal.patch', 'draft-pr.md'):
        (out / name).unlink(missing_ok=True)
    if patch:
        (out / 'proposal.patch').write_text(patch, encoding='utf-8')
        (out / 'draft-pr.md').write_text(
            '# Draft proposal: Paris travel updates\n\n' + report['proposal_kind'] +
            '\n\nHuman approval required. Apply only proposal.patch; do not include monitor state in public pages. '
            'No PR has been created. Verify sources and dates again before opening or merging.\n\n' + markdown(report), encoding='utf-8')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, help='Previous state.json (untrusted, validated JSON)')
    parser.add_argument('--output', type=Path, help='Dedicated report directory outside public site content')
    parser.add_argument('--check-public', action='store_true', help='Offline stale-content gate; makes no network calls')
    args = parser.parse_args(argv)
    now = datetime.now(UTC)
    page = (ROOT / HUB).read_text(encoding='utf-8')
    if args.check_public:
        events = event_records(load_json(ROOT / REGISTRY), now)
        status, problem = public_status(page, now, events)
        print('Paris travel section: ' + status)
        return 1 if problem else 0
    if args.output is None:
        parser.error('--output is required for monitoring')
    out = args.output.resolve()
    # Outputs must be outside the checkout, or inside excluded docs/qa only.
    if out.is_relative_to(ROOT) and not out.is_relative_to(ROOT / 'docs' / 'qa'):
        parser.error('Output must be outside checkout or within docs/qa')
    previous, state_note = read_state(args.state)
    try:
        registry = load_json(ROOT / REGISTRY)
        report, state, patch = monitor(now, registry, page, previous, state_note=state_note)
    except (ValueError, TypeError, KeyError, OSError, RecursionError):
        # Configuration failures fail closed, produce a readable report, no patch.
        report = {'version': 2, 'generated_at_paris': stamp(now), 'status': 'verification required',
                  'publication_authorized': False, 'proposal_available': False,
                  'configuration_failure': True, 'safety_conclusion': None}
        out.mkdir(parents=True, exist_ok=True)
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        (out / 'report.md').write_text('# Verification required\n\nInvalid local registry or page structure. No publication proposal.\n', encoding='utf-8')
        for name in ('proposal.patch', 'draft-pr.md', 'state.json'):
            (out / name).unlink(missing_ok=True)
        print('Verification required: invalid local configuration. No proposal generated.')
        return 2
    write_outputs(out, report, state, patch)
    print('Paris monitoring: partial coverage; verification required; '
          + str(len(report['new_findings'])) + ' new review items; no publication.')
    return 2 if report['network_failure'] or report['public_status'] in ('verification required', 'review overdue') else 0


if __name__ == '__main__':
    raise SystemExit(main())
