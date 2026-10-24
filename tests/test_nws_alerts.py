"""Offline NWS qualification, projection, persistence and publication-boundary tests."""
from copy import deepcopy
from datetime import timedelta
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from travel_intelligence import nws
from travel_intelligence.nws_storage import NWSStore
from travel_intelligence.storage import ConflictError
from travel_intelligence.validation import ValidationError, canonical, instant
spec=importlib.util.spec_from_file_location('nws_cli',ROOT/'scripts/nws-travel-alerts.py')
cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
FETCH=nws.fetch
NOW=instant('2026-10-24T12:00:00Z')
BASE=json.loads((ROOT/'tests/fixtures/nws/heat-synthetic.json').read_bytes())


class NWSTests(unittest.TestCase):
    def setUp(self):
        self.data=deepcopy(BASE)
        self.temp=tempfile.TemporaryDirectory(prefix='nws-test-');self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name);self.store=NWSStore(self.folder/'state',ROOT)
        self.guard=patch('travel_intelligence.nws.fetch',side_effect=AssertionError('Live fetch forbidden'))
        self.guard.start();self.addCleanup(self.guard.stop)

    def collect(self,data=None):
        return nws.collect(canonical(self.data if data is None else data),NOW,synthetic=True)

    def test_fetch_bounds_redirects_encoding_endpoint_and_elapsed_time(self):
        from email.message import Message
        cases=[('valid',None),('size','nws_size'),('encoding','nws_compression'),
               ('type','nws_content_type'),('url','nws_http'),('timeout','nws_timeout')]
        for case,code in cases:
            with self.subTest(case=case):
                response=MagicMock();response.status=200;response.geturl.return_value=nws.ENDPOINT
                response.headers=Message();response.headers['Content-Type']='application/geo+json'
                response.read1.side_effect=[b'{}',b'']
                if case=='size':response.headers['Content-Length']='2000001'
                if case=='encoding':response.headers['Content-Encoding']='gzip'
                if case=='type':response.headers.replace_header('Content-Type','text/html')
                if case=='url':response.geturl.return_value='https://evil.example/'
                opener=MagicMock();opener.open.return_value.__enter__.return_value=response
                with patch('travel_intelligence.nws.build_opener',return_value=opener), patch('travel_intelligence.nws.time.monotonic',side_effect=[0,31] if case=='timeout' else [0]*10):
                    if code:
                        with self.assertRaisesRegex(ValidationError,code):FETCH()
                    else:self.assertEqual(FETCH(),b'{}')
                opener.open.assert_called_once()
                request=opener.open.call_args.args[0]
                self.assertEqual(request.full_url,nws.ENDPOINT)
                self.assertEqual(request.get_header('Accept-encoding'),'identity')
                self.assertEqual(opener.open.call_args.kwargs['timeout'],15)
        from travel_intelligence.providers import NoRedirect
        with self.assertRaises(ValidationError):NoRedirect().redirect_request(None,None,None,None,None,None)

    def test_precise_manhattan_projection(self):
        feed,report=self.collect();item=feed['advisories'][0]
        self.assertEqual(item['zones'],['NYZ072']);self.assertTrue(feed['synthetic'])
        self.assertEqual(item['event'],'Heat Advisory');self.assertNotIn('description',item)
        self.assertIsNone(report['safetyConclusion'])
        self.data['features'][0]['properties']['response']='Execute'
        self.assertEqual(len(self.collect()[0]['advisories']),1)
        self.data['features'][0]['properties']['eventCode']['NationalWeatherService']=['TSW']
        self.assertEqual(self.collect()[0]['advisories'],[])

    def test_neighbor_is_not_nyc(self):
        p=self.data['features'][0]['properties'];p['affectedZones']=['https://api.weather.gov/zones/forecast/NYZ079'];p['geocode']['UGC']=['NYZ079']
        feed,report=self.collect();self.assertEqual(feed['advisories'],[]);self.assertEqual(report['held']['outside_nyc'],1)

    def test_explicit_zone_membership_without_polygon(self):
        self.data['features'][0]['geometry']=None
        self.assertEqual(len(self.collect()[0]['advisories']),1)
        self.data['features'][0]['geometry']={'type':'Point','coordinates':[-72.0,41.0]}
        self.assertEqual(self.collect()[0]['advisories'],[])

    def test_uncertain_text_or_polygon_cannot_replace_zone_codes(self):
        p=self.data['features'][0]['properties'];p['affectedZones']=[];p['areaDesc']='New York City'
        self.assertEqual(self.collect()[0]['advisories'],[])

    def test_queens_splits_preserved(self):
        p=self.data['features'][0]['properties'];p['affectedZones']=['https://api.weather.gov/zones/forecast/NYZ176'];p['geocode']['UGC']=['NYZ176']
        self.assertEqual(self.collect()[0]['advisories'][0]['zones'],['NYZ176'])

    def test_unsupported_hazard_not_automated(self):
        for event in ['Tornado Warning','Tsunami Warning','Civil Emergency Message','Frost Advisory']:
            self.data['features'][0]['properties']['event']=event
            self.assertEqual(self.collect()[0]['advisories'],[])

    def test_test_exercise_private_and_other_issuer_held(self):
        for key,value in [('status','Exercise'),('scope','Private')]:
            data=deepcopy(BASE);data['features'][0]['properties'][key]=value
            self.assertEqual(self.collect(data)[0]['advisories'],[])
        data=deepcopy(BASE);data['features'][0]['properties']['senderName']='NWS Other Office'
        with self.assertRaises(ValidationError):self.collect(data)

    def test_sensitive_response_held(self):
        for response in ['Evacuate','AllClear','Avoid','Shelter']:
            self.data['features'][0]['properties']['response']=response
            self.assertEqual(self.collect()[0]['advisories'],[])

    def test_bad_geocode_or_external_zone_url_held(self):
        self.data['features'][0]['properties']['geocode']['UGC']=['NYZ073']
        self.assertEqual(self.collect()[0]['advisories'],[])
        self.data['features'][0]['properties']['affectedZones']=['https://api.weather.gov.evil/zones/forecast/NYZ072']
        self.assertEqual(self.collect()[0]['advisories'],[])

    def test_malicious_text_is_not_published(self):
        self.data['features'][0]['properties']['headline']='<img src=x onerror=alert(1)>'
        self.assertEqual(self.collect()[0]['advisories'],[])

    def test_invalid_or_expired_dates(self):
        for key,value in [('expires','2026-10-24T12:00:00Z'),('effective','2026-10-25T12:00:00Z'),('onset','2026-02-30T12:00:00Z')]:
            data=deepcopy(BASE);data['features'][0]['properties'][key]=value
            self.assertEqual(self.collect(data)[0]['advisories'],[])

    def test_maximum_public_lifetime_and_source_expiry(self):
        feed,_=self.collect();item=feed['advisories'][0]
        self.assertEqual(instant(item['expiresAt']),NOW+timedelta(minutes=20))
        self.data['features'][0]['properties']['expires']='2026-10-24T12:05:00Z'
        self.assertEqual(instant(self.collect()[0]['advisories'][0]['expiresAt']),NOW+timedelta(minutes=5))

    def test_stale_future_partial_and_malformed_exports_refused(self):
        for value in ['2026-10-24T11:00:00Z','2026-10-24T12:00:01Z']:
            data=deepcopy(BASE);data['updated']=value
            with self.assertRaises(ValidationError):self.collect(data)
        self.data['pagination']={'next':'https://evil.example/'}
        with self.assertRaises(ValidationError):self.collect()
        with self.assertRaises(ValidationError):nws.collect(b'{',NOW,synthetic=True)

    def test_expired_geography_qualification_stops_collection(self):
        with self.assertRaises(ValidationError):nws.collect(canonical(BASE),instant('2026-11-24T12:00:00Z'),synthetic=True)

    def test_exact_duplicate_is_collapsed(self):
        self.data['features']*=2
        self.assertEqual(len(self.collect()[0]['advisories']),1)

    def test_conflicting_duplicate_fails_batch_closed(self):
        other=deepcopy(self.data['features'][0]);other['properties']['description']='Different same-ID content'
        self.data['features'].append(other)
        with self.assertRaises(ValidationError):self.collect()

    def revision(self,kind='Update'):
        previous=deepcopy(self.data['features'][0]);new=deepcopy(previous)
        p=new['properties'];p['id']=p['id'].replace('a'*40,'b'*40)
        new['id']=p['@id']=nws.PREFIX+p['id'];p['messageType']=kind;p['sent']=p['effective']='2026-10-24T11:10:00Z'
        p['references']=[{'@id':previous['id'],'identifier':previous['properties']['id'],'sender':p['sender'],'sent':previous['properties']['sent']}]
        self.data['features']=[previous,new]
        return p

    def test_update_replaces_only_explicitly_referenced_id(self):
        revised=self.revision();feed,_=self.collect()
        self.assertEqual([i['id'] for i in feed['advisories']],[revised['id']])

    def test_cancellation_retires_original_without_all_clear(self):
        self.revision('Cancel');feed,report=self.collect();self.assertEqual(feed['advisories'],[]);self.assertIsNone(report['safetyConclusion'])

    def test_unqualified_revision_cannot_leave_original_visible(self):
        self.revision()['event']='Tornado Warning'
        self.assertEqual(self.collect()[0]['advisories'],[])

    def test_bad_reference_chain_fails_closed(self):
        self.revision()['references'][0]['@id']='https://evil.example/'
        with self.assertRaises(ValidationError):self.collect()

    def test_omission_never_means_safe_or_resolved(self):
        old,_=self.collect();self.data['features']=[];new,_=self.collect()
        changes=nws.changes(old,new,NOW)
        self.assertEqual(changes[0]['change'],'not_in_current_qualified_feed')

    def test_repeat_collection_deduplicates_changes(self):
        first=cli.run(self.store,lambda:canonical(BASE),NOW,True)
        second=cli.run(self.store,lambda:canonical(BASE),NOW,True)
        self.assertEqual(second['report']['changes'],[]);self.assertEqual(len(second['history']),len(first['history']))

    def test_unavailable_preserves_last_good_but_public_feed_is_empty(self):
        good=cli.run(self.store,lambda:canonical(BASE),NOW,True)
        def unavailable():raise OSError('fixture outage')
        bad=cli.run(self.store,unavailable,NOW+timedelta(minutes=1),True)
        self.assertEqual(bad['lastGoodFeed'],good['feed']);self.assertEqual(bad['feed']['advisories'],[])
        self.assertEqual(bad['feed']['status'],'unavailable');self.assertIsNone(bad['report']['safetyConclusion'])

    def test_fixture_and_live_state_cannot_mix(self):
        cli.run(self.store,lambda:canonical(BASE),NOW,True)
        with self.assertRaises(ValidationError):cli.run(self.store,lambda:canonical(BASE),NOW,False)

    def test_generation_conflict_and_writer_lock(self):
        state=cli.run(self.store,lambda:canonical(BASE),NOW,True)
        with self.assertRaises(ConflictError):self.store.commit(state,None)
        (self.folder/'state/.writer.lock').write_text('owner')
        with self.assertRaises(ConflictError):self.store.commit(state,self.store.load()[0])

    def test_crash_before_pointer_keeps_previous_state(self):
        cli.run(self.store,lambda:canonical(BASE),NOW,True);old=self.store.load()[0]
        from travel_intelligence.nws_storage import atomic_json
        def interrupt(path,value):
            if path.name=='CURRENT.json':raise OSError('interrupted')
            return atomic_json(path,value)
        with patch('travel_intelligence.nws_storage.atomic_json',side_effect=interrupt):
            with self.assertRaises(OSError):cli.run(self.store,lambda:canonical(BASE),NOW,True)
        self.assertEqual(self.store.load()[0],old)
        replay=cli.run(self.store,lambda:canonical(BASE),NOW,True)
        self.assertEqual(replay['report']['changes'],[])

    def test_corruption_requires_explicit_known_token_recovery(self):
        cli.run(self.store,lambda:canonical(BASE),NOW,True);token=self.store.load()[0]
        (self.folder/'state/CURRENT.json').write_text('{')
        with self.assertRaises(ValidationError):self.store.load()
        self.store.recover(token);self.assertEqual(self.store.load()[0],token)

    def test_missing_history_is_refused(self):
        cli.run(self.store,lambda:canonical(BASE),NOW,True);first=self.store.load()[0]
        cli.run(self.store,lambda:canonical(BASE),NOW+timedelta(seconds=1),True)
        (self.folder/'state/generations'/ (first+'.json')).unlink()
        with self.assertRaises(OSError):self.store.load()

    def test_checkout_and_symlink_export_refused(self):
        with self.assertRaises(ValidationError):NWSStore(ROOT/'hotels/new-york',ROOT)
        cli.run(self.store,lambda:canonical(BASE),NOW,True)
        with self.assertRaises(ValidationError):self.store.export(ROOT/'data')
        with patch.object(Path,'is_symlink',return_value=True):
            with self.assertRaises(ValidationError):self.store.export(self.folder/'export')

    def test_nws_tools_and_fixtures_are_excluded_from_pages(self):
        lines=(ROOT/'_config.yml').read_text(encoding='utf-8').splitlines()
        excluded={line[4:] for line in lines if line.startswith('  - ')}
        expected={'scripts/nws-travel-alerts.py','scripts/nws-preview.py',
                  'scripts/travel_intelligence/nws.py','scripts/travel_intelligence/nws_storage.py',
                  'config/travel-intelligence/nws-nyc.json','tests/fixtures/nws',
                  'tests/test_nws_alerts.py','tests/test_nws_alerts.mjs','tests/test_nws_alerts_browser.mjs',
                  'docs/tripguidely-nws-automatic-alerts-phase5.md','docs/workflows'}
        self.assertTrue(expected <= excluded)
        import os
        if os.environ.get('BANNER_PUBLISHED_DIR'):
            for name in expected:self.assertFalse((Path(os.environ['BANNER_PUBLISHED_DIR'])/name).exists(),name)

    def test_only_actual_nonempty_pages_are_candidates(self):
        config=json.loads((ROOT/'config/travel-intelligence/nws-nyc.json').read_bytes())
        self.assertEqual(config['zones'],nws.ZONES);self.assertEqual(len(config['pages']),12)
        self.assertNotIn('/transport/new-york/',config['pages'])
        for route in config['pages']:
            page=ROOT/route.strip('/')/'index.html';self.assertIn('<h1',page.read_text(encoding='utf-8'))


if __name__=='__main__':unittest.main()
