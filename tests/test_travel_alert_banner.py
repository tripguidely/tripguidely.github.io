"""V4 fixture/policy qualification; no provider or external storage calls."""
from datetime import datetime, timezone
import importlib.util
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('banner_demo', ROOT / 'scripts/travel-alert-banner.py')
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)
NOW = datetime(2026, 10, 24, 12, tzinfo=timezone.utc)


class BannerPolicyTests(unittest.TestCase):
    def test_synthetic_fixtures_reuse_exact_v3_destination(self):
        for case in demo.SCENARIOS:
            with self.subTest(case=case):
                feed = demo.synthetic_feed(case, NOW)
                self.assertIs(feed['synthetic'], True)
                for item in feed['advisories']:
                    self.assertEqual(item['evidence'], 'synthetic-review-only')
                    self.assertIn('Synthetic exercise', item['description'])
                    self.assertNotIn('evacuate', item['description'].lower())

    def test_expired_fixture_is_already_expired(self):
        self.assertLess(demo.synthetic_feed('expired', NOW)['expiresAt'], NOW.isoformat(timespec='milliseconds').replace('+00:00', 'Z'))

    def test_empty_fixture_contains_no_claim(self):
        self.assertEqual(demo.synthetic_feed('empty', NOW)['advisories'], [])

    def test_unknown_scenario_refused(self):
        with self.assertRaises(ValueError):
            demo.synthetic_feed('../hotels', NOW)

    def test_no_v3_measurement_severity_or_approval_flag_can_publish(self):
        for source in ('canada', 'usgs', 'gdacs'):
            for report in ({'source': source, 'tsunami': 1, 'magnitude': 9.9},
                           {'source': source, 'approved': True, 'impact': 'unknown'}, None):
                self.assertEqual(demo.automatic_publication_candidates(report), [])

    def test_demo_build_never_calls_a_provider(self):
        with patch('urllib.request.urlopen', side_effect=AssertionError('Live access forbidden')):
            for case in demo.SCENARIOS:
                demo.synthetic_feed(case, NOW)

    def test_public_pages_have_no_component_reference(self):
        for directory in ('hotels', 'attractions', 'things-to-do'):
            for page in (ROOT / directory).rglob('*.html'):
                self.assertNotIn('travel-alert-banner', page.read_text(encoding='utf-8'))

    def test_pages_excludes_every_v4_demo_resource(self):
        config = (ROOT / '_config.yml').read_text(encoding='utf-8')
        lines = [line for line in config.splitlines() if line.strip() and not line.startswith('#')]
        self.assertEqual(lines[0], 'exclude:')
        self.assertTrue(all(line.startswith('  - ') for line in lines[1:]))
        excluded = {line[4:] for line in lines[1:]}
        expected = {'scripts/travel-alert-banner.py', 'scripts/travel_alert_banner',
                    'tests/fixtures/travel-alert-banner', 'tests/test_travel_alert_banner.py',
                    'tests/test_travel_alert_banner.mjs', 'tests/test_travel_alert_banner_browser.mjs',
                    'docs/travel-alert-banner-v4.md'}
        self.assertEqual(excluded, expected)
        self.assertFalse((ROOT / '.nojekyll').exists(), 'A raw Pages copy would bypass exclusions')
        # CI sets this after a real Jekyll build into a temporary directory.
        if os.environ.get('BANNER_PUBLISHED_DIR'):
            output = Path(os.environ['BANNER_PUBLISHED_DIR']).resolve(strict=True)
            self.assertFalse(output.is_relative_to(ROOT))
            for path in expected:
                self.assertFalse((output / path).exists(), path)
            self.assertFalse((output / 'feed.json').exists())
            for page in (ROOT / 'hotels').rglob('*.html'):
                self.assertEqual((output / page.relative_to(ROOT)).read_bytes(), page.read_bytes())

    def test_demo_is_not_a_static_public_html_file(self):
        self.assertIn('127.0.0.1', (ROOT / 'scripts/travel-alert-banner.py').read_text(encoding='utf-8'))
        self.assertNotIn('affiliate_click', demo.HTML.decode())
        self.assertNotIn('travelpayouts', demo.HTML.decode())
        self.assertNotIn('klook', demo.HTML.decode())


if __name__ == '__main__':
    unittest.main()
