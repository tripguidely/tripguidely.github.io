"""Offline GDACS multi-hazard, identity, clock and persistence regressions."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from email.message import Message
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from travel_intelligence.engine import Monitor
from travel_intelligence.gdacs import (FEED, GDACSAdapter, checked_url, event_url, fetch_gdacs,
                                       geometry_summary, source_date)
from travel_intelligence.model import content_hash, validate_event
from travel_intelligence.providers import adapters_for
from travel_intelligence.reconciliation import reconcile
from travel_intelligence.registry import Registry
from travel_intelligence.reporting import markdown, write_report
from travel_intelligence.storage import LocalStateStore, StoreError, validate_state
from travel_intelligence.validation import MAX_INPUT_BYTES, ValidationError, canonical, load_json, stamp

NOW=datetime(2026,10,23,12,tzinfo=timezone.utc)
FIXTURE=ROOT/"tests/fixtures/travel-intelligence/gdacs-synthetic.geojson"


def fixture():return load_json(FIXTURE)


class GDACSTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="gti-gdacs-tests-");self.addCleanup(self.temp.cleanup)
        self.directory=Path(self.temp.name)
        self.registry=Registry.from_directory(ROOT/"config/travel-intelligence","gdacs-sources.json")
        self.adapters=adapters_for(self.registry);self.adapter=self.adapters["gdacs-multi-hazard"]
        self.store=LocalStateStore(self.directory/"state",self.registry,ROOT)

    def run_monitor(self,data=None,now=NOW,reader=None):
        return Monitor(self.registry,self.store,self.adapters).run(now,reader or (lambda _:canonical(data if data is not None else fixture())))

    def combined(self,data=None,usgs=None,now=NOW):
        registry=Registry.from_directory(ROOT/"config/travel-intelligence","gdacs-usgs-sources.json")
        payloads={"gdacs-multi-hazard":data or fixture(),"usgs-earthquakes":usgs or load_json(ROOT/"tests/fixtures/travel-intelligence/usgs-synthetic.geojson")}
        return Monitor(registry,LocalStateStore(self.directory/"combined",registry,ROOT),adapters_for(registry)).run(now,lambda ident:canonical(payloads[ident]))

    def test_six_hazards_normalize_without_impact_or_publication(self):
        report=self.run_monitor()
        self.assertTrue(report["persistence"]["committed"])
        self.assertEqual({e["category"] for e in report["events"]},{"severe_weather","earthquake","flood","volcanic_activity","drought","wildfire"})
        for e in report["events"]:
            self.assertEqual(e["severity"],"unknown");self.assertEqual(e["source_status"],"needs_validation")
            self.assertEqual(e["publication_status"],"withheld");self.assertIsNone(e["summary_en"])
            self.assertEqual(e["traveler_impact"],{"status":"unknown","text_en":None,"evidence_urls":[]})
        self.assertFalse(report["publication_authorized"]);self.assertFalse(report["automatic_publication"])
        self.assertIsNone(report["safety_conclusion"])

    def test_same_country_candidates_are_context_only_not_city_incidents(self):
        report=self.run_monitor()
        for e in report["events"]:
            self.assertIsNone(e["city"]);self.assertIsNone(e["region"]);self.assertEqual(e["country_codes"],[])
            self.assertEqual(e["affected_locations"],[])
            contexts=report["destination_contexts"][e["event_id"]]
            self.assertEqual([c["destination_id"] for c in contexts],["it-rome"])
            self.assertEqual(contexts[0]["relationship"],"country_context_to_verify")
            self.assertFalse(contexts[0]["local_incident_confirmed"])
        data=fixture()
        for f in data["features"]:
            f["properties"]["affectedcountries"]=[]
            f["properties"]["datemodified"]="2026-10-23T11:55:00"
        self.assertTrue(all(not v for v in self.run_monitor(data,NOW+timedelta(minutes=1))["destination_contexts"].values()))

    def test_offset_free_dates_and_unknown_export_are_not_invented_utc(self):
        report=self.run_monitor()
        self.assertIsNone(report["sources"]["gdacs-multi-hazard"]["source_generated_at"])
        for e in report["events"]:
            self.assertIsNone(e["starts_at"]);self.assertIsNone(e["source_updated_at"])
            self.assertIsNone(e["provenance"]["source_generated_at"])
            self.assertEqual(e["source_data"]["time-basis"],"offset_unspecified")
            self.assertNotIn("Z",e["source_data"]["modified-text"])
        self.assertEqual(len(self.store.load(NOW).data["events"]),6)

    def test_explicit_offsets_normalize_and_equivalent_offsets_do_not_revise(self):
        data=fixture()
        for f in data["features"]:
            for k in ("fromdate","todate","datemodified"):f["properties"][k]+='Z'
        first=self.run_monitor(data)
        for f in data["features"]:
            for k in ("fromdate","todate","datemodified"):
                dt=datetime.fromisoformat(f["properties"][k].replace('Z','+00:00'))
                f["properties"][k]=dt.astimezone(timezone(timedelta(hours=2))).isoformat()
        second=self.run_monitor(data,NOW+timedelta(minutes=1))
        self.assertEqual(second["changes"],[])
        self.assertTrue(all(e["source_updated_at"].endswith('Z') for e in second["events"]))

    def test_revision_same_episode_keeps_identity_and_audits_change(self):
        first=self.run_monitor();data=fixture()
        data["features"][0]["properties"].update(alertlevel="Orange",datemodified="2026-10-23T11:55:00")
        second=self.run_monitor(data,NOW+timedelta(minutes=1))
        self.assertEqual({e["event_id"] for e in first["events"]},{e["event_id"] for e in second["events"]})
        self.assertEqual(second["changes"][0]["kind"],"source_revised")
        changed=next(e for e in second["events"] if e["source_data"]["event-type"]=='TC')
        self.assertEqual(changed["human_review_status"],"needs_reverification")
        self.assertEqual(len(list((self.directory/'state/generations').glob('*.json'))),2)

    def test_episode_changes_remain_separate_but_are_not_independent_hazards(self):
        data=fixture();second=deepcopy(data["features"][0]);p=second["properties"];p["episodeid"]=2
        p["datemodified"]="2026-10-23T11:55:00"
        p["url"]={k:event_url(k,'TC',p['eventid'],2) for k in ('geometry','report','details')}
        data["features"].append(second);report=self.run_monitor(data)
        self.assertEqual(len(report["events"]),7);self.assertEqual(len(report["observation_groups"]),6)
        self.assertTrue(any(len(g["observation_ids"])==2 for g in report["observation_groups"]))

    def test_duplicate_same_episode_consolidates_conflicting_versions_fail(self):
        data=fixture();data["features"].append(deepcopy(data["features"][0]))
        report=self.run_monitor(data);self.assertEqual(len(report["events"]),6);self.assertEqual(report["duplicates_in_batch"],1)
        data["features"][-1]["properties"]["episodealertscore"]=2.8
        failed=self.run_monitor(data,NOW+timedelta(minutes=1))
        self.assertEqual(failed["sources"]["gdacs-multi-hazard"]["error_code"],"conflicting_duplicate")
        self.assertEqual(len(failed["events"]),6)

    def test_unchanged_run_does_not_extend_review_deadline(self):
        first=self.run_monitor();second=self.run_monitor(now=NOW+timedelta(minutes=1))
        self.assertEqual(first['pending_review'],second['pending_review'])
        self.assertEqual([e['review_due_at'] for e in first['events']],[e['review_due_at'] for e in second['events']])
        self.assertEqual(second['changes'],[]);self.assertTrue(second['no_change'])

    def test_rollback_and_conflicting_same_revision_preserve_last_valid_content(self):
        self.run_monitor()
        for case in ('older','conflict','basis'):
            data=fixture();p=data['features'][0]['properties']
            if case=='older':p['datemodified']='2026-10-23T11:49:00'
            elif case=='conflict':p['alertlevel']='Green'
            else:
                for k in ('fromdate','todate','datemodified'):p[k]+='Z'
            with self.subTest(case=case):
                report=self.run_monitor(data,NOW+timedelta(minutes=1))
                self.assertEqual(report['sources']['gdacs-multi-hazard']['status'],'unavailable')
                self.assertEqual(next(e for e in report['events'] if e['source_data']['event-type']=='TC')['source_data']['alert-level'],'Red')

    def test_rolling_omission_and_expiry_never_resolve_danger(self):
        self.run_monitor();empty={'type':'FeatureCollection','features':[],'bbox':[]}
        report=self.run_monitor(empty,NOW+timedelta(hours=2))
        self.assertEqual(len(report['events']),6)
        self.assertTrue(all(e['source_status']=='unverifiable' and e['ends_at'] is None and e['lifecycle_status']=='expired' for e in report['events']))
        self.assertIsNone(report['safety_conclusion'])
        self.assertTrue(any(d['code']=='records_missing_not_withdrawn' for d in report['diagnostics']))

    def test_outage_and_recovery_preserve_identities_without_new_incidents(self):
        first=self.run_monitor()
        outage=self.run_monitor(now=NOW+timedelta(minutes=1),reader=MagicMock(side_effect=URLError('private-response')))
        self.assertNotIn('private-response',json.dumps(outage));self.assertEqual(len(outage['events']),6)
        recovery=self.run_monitor(now=NOW+timedelta(minutes=2))
        self.assertEqual({e['event_id'] for e in first['events']},{e['event_id'] for e in recovery['events']})
        self.assertFalse(any(c['kind'] in {'new_information','initial_observation'} for c in recovery['changes']))

    def test_not_current_and_reported_end_are_not_cancellations(self):
        data=fixture()
        for f in data['features']:f['properties']['iscurrent']='false'
        report=self.run_monitor(data)
        self.assertTrue(all(e['source_data']['source-current'] is False and e['ends_at'] is None and
                            e['human_review_status']=='needs_reverification' for e in report['events']))
        self.assertFalse(any(e['source_status']=='withdrawn' for e in report['events']))
        data['features'][0]['properties']['iscancelled']=True
        failed=self.run_monitor(data,NOW+timedelta(minutes=1))
        self.assertEqual(failed['sources']['gdacs-multi-hazard']['status'],'unavailable')

    def test_tsunami_html_and_impact_text_are_not_public_warnings(self):
        data=fixture();p=data['features'][-1]['properties']
        p['htmldescription']='<script>EVACUATE; hotels destroyed</script>'
        p['severitydata']['severitytext']='Synthetic alleged deaths: unverified'
        report=self.run_monitor(data);text=markdown(report)
        self.assertNotIn('EVACUATE',text);self.assertNotIn('hotels destroyed',text);self.assertNotIn('alleged deaths',text)
        self.assertIn('no active tsunami warning or evacuation order inferred',text)
        eq=next(e for e in report['events'] if e['category']=='earthquake')
        self.assertEqual(eq['source_data']['tsunami-context'],'not_assessed_not_official_warning')
        self.assertFalse(report['automatic_publication'])

    def test_exact_usgs_identifier_groups_without_merging_originals(self):
        report=self.combined();self.assertEqual(len(report['events']),8)
        self.assertEqual(len(report['observation_groups']),7)
        self.assertEqual(len(report['cross_source_relationships']),1)
        relation=report['cross_source_relationships'][0]
        self.assertEqual(relation['basis'],'shared_official_identifier');self.assertFalse(relation['independent_confirmations'])
        self.assertTrue(all(not g['merged'] for g in report['observation_groups']))
        self.assertEqual(sum(e['source_id']=='usgs-earthquakes' for e in report['events']),2)

    def test_missing_or_untrusted_upstream_identity_only_requests_review(self):
        for provider,ident in (('NEIC',''),('UNQUALIFIED','ussynthetic001'),('NEIC','https://evil.test/ussynthetic001')):
            data=fixture();data['features'][-1]['properties'].update(source=provider,sourceid=ident)
            report=self.combined(data)
            self.assertEqual(report['cross_source_relationships'],[])
            self.assertTrue(report['possible_duplicate_review'])
            self.assertFalse(report['possible_duplicate_review'][0]['matching_asserted'])
            self.assertEqual(len(report['events']),8)

    def test_ambiguous_usgs_alias_does_not_confirm_identity(self):
        report=self.combined();events=deepcopy(report['events'])
        other=next(e for e in events if e['source_id']=='usgs-earthquakes' and e['source_event_id']=='ussynthetic002')
        other['source_data']['aliases']=',ussynthetic001,ussynthetic002,'
        result=reconcile(events)
        self.assertEqual(result['cross_source_relationships'],[])
        self.assertTrue(result['possible_duplicate_review'])

    def test_missing_area_and_broad_geometry_never_assign_destinations(self):
        for geo in (None,{'type':'Polygon','coordinates':[[[-179,-80],[179,-80],[179,80],[-179,-80]]]}):
            data=fixture();data['features'][0]['geometry']=geo
            event=self.adapter.parse(canonical(data),NOW).events[0]
            self.assertEqual(event['geographic_scope'],'uncertain');self.assertIsNone(event['city'])
            summary=json.loads(event['source_data']['geometry-summary'])
            self.assertIn(summary['kind'],{'missing','unqualified_area'})

    def test_nullable_collection_bbox_is_accepted_but_invalid_bounds_are_refused(self):
        data=fixture();self.assertIsNone(data['bbox'])
        self.assertEqual(len(self.adapter.parse(canonical(data),NOW).events),6)
        for box in ([0,91,1,92],[0,0,1],[True,0,1,1],[0,10,1,0]):
            broken=fixture();broken['bbox']=box
            with self.subTest(box=box):
                with self.assertRaises(ValueError):self.adapter.parse(canonical(broken),NOW)

    def test_invalid_geometries_bounds_and_polygons_fail_closed(self):
        for geo in ({'type':'Point','coordinates':[181,0]}, {'type':'Point','coordinates':[0,91]},
                    {'type':'Point','coordinates':[True,0]}, {'type':'Point','coordinates':[1,2,3]},
                    {'type':'Polygon','coordinates':[[[0,0],[1,0],[1,1],[0,1]]]},
                    {'type':'LineString','coordinates':[[0,0],[1,1]]}):
            with self.subTest(geo=geo):
                with self.assertRaises(ValueError):geometry_summary(geo)

    def test_dates_invalid_mixed_future_and_order_are_refused(self):
        for date in ('2026-02-30T00:00:00','tomorrow','2026-10-23','2026-10-23T11:00:00+25:00'):
            with self.subTest(date=date):
                with self.assertRaises(ValueError):source_date(date)
        for case in ('mixed','order','future'):
            data=fixture();p=data['features'][0]['properties']
            if case=='mixed':p['fromdate']+='Z'
            elif case=='order':p['todate']='2026-01-01T00:00:00'
            else:
                for k in ('fromdate','todate','datemodified'):p[k]+='Z'
                p['datemodified']='2026-10-25T12:00:00Z'
            with self.subTest(case=case):
                with self.assertRaises(ValueError):self.adapter.parse(canonical(data),NOW)

    def test_urls_identifiers_flags_levels_and_payload_schema_are_strict(self):
        for field,value in (('eventid',True),('episodeid',-1),('eventtype','TS'),('iscurrent',True),
                            ('alertlevel','Evacuate'),('alertscore',float('inf')),('sourceid',123)):
            data=fixture();data['features'][0]['properties'][field]=value
            with self.subTest(field=field):
                with self.assertRaises(ValueError):self.adapter.parse(canonical(data),NOW)
        for value in ('https://www.gdacs.org.evil.test/report.aspx','http://127.0.0.1/','https://www.gdacs.org/report.aspx?eventid=1&eventid=2',
                      event_url('report','TC',9000001,1)+'&redirect=https://evil.test'):
            with self.assertRaises(ValueError):checked_url(value,'report','TC',9000001,1)
        data=fixture();data['features'][0]['properties']['unknown']='not accepted'
        with self.assertRaises(ValueError):self.adapter.parse(canonical(data),NOW)
        for raw in (b'{broken',b'{"x":1,"x":2}',b'{"x":NaN}',b'x'*(MAX_INPUT_BYTES+1)):
            with self.assertRaises(ValueError):self.adapter.parse(raw,NOW)

    def test_persisted_record_cannot_forge_impact_utc_or_resolution(self):
        original=self.adapter.parse(canonical(fixture()),NOW).events[0]
        for field,value in (('city','it-rome'),('category','tsunami'),('source_status','officially_confirmed'),
                            ('ends_at',stamp(NOW)),('starts_at',stamp(NOW)),('source_url',FEED),('severity','critical'),
                            ('publication_status','approved')):
            event=deepcopy(original);event[field]=value;event['content_hash']=content_hash(event)
            with self.subTest(field=field):
                with self.assertRaises(ValueError):validate_event(event,self.registry,NOW)

    def test_configuration_and_old_provider_contracts_remain_closed(self):
        destinations=load_json(ROOT/'config/travel-intelligence/destinations.json')
        sources=load_json(ROOT/'config/travel-intelligence/gdacs-sources.json')
        for field,value in (('endpoint',FEED+'?override=1'),('publication_enabled',True),('countries',['IT']),('review_hours',48)):
            broken=deepcopy(sources);broken['sources'][0][field]=value
            with self.assertRaises(ValueError):Registry(destinations,broken)
        default=Registry.from_directory(ROOT/'config/travel-intelligence')
        self.assertEqual(set(adapters_for(default)),{'ca-travel-advisories'})
        usgs=Registry.from_directory(ROOT/'config/travel-intelligence','usgs-sources.json')
        self.assertEqual(set(adapters_for(usgs)),{'usgs-earthquakes'})
        self.assertNotEqual(default.config_hash,self.registry.config_hash)
        # Unknown export timestamps must remain forbidden for a checked Canada source.
        state={'schema_version':3,'config_hash':default.config_hash,'last_run_at':stamp(NOW),'events':[],
               'sources':{'ca-travel-advisories':{'status':'checked','last_attempt_at':stamp(NOW),'last_success_at':stamp(NOW),'source_generated_at':None,'error_code':None}}}
        with self.assertRaises(ValueError):validate_state(state,default,NOW)

    def test_corrupt_state_stops_before_reader_and_explicit_recovery_preserves_history(self):
        self.run_monitor();pointer=self.directory/'state/CURRENT.json';pointer.write_bytes(b'{broken')
        reader=MagicMock(return_value=canonical(fixture()))
        with self.assertRaises(StoreError):self.run_monitor(reader=reader)
        reader.assert_not_called();pointer.unlink()
        recovered=self.store.recover(NOW)
        self.assertEqual(len(recovered.data['events']),6);self.assertEqual(recovered.generation,1)

    def test_fixed_transport_limits_status_size_encoding_time_and_no_retry(self):
        for case in ('ok','status','redirect','html','gzip','size','timeout','unavailable','429'):
            headers=Message();headers['Content-Type']='text/html' if case=='html' else 'application/json'
            if case=='gzip':headers['Content-Encoding']='gzip'
            response=SimpleNamespace(status=500 if case=='status' else 200,headers=headers,
                geturl=lambda:FEED+('/foreign' if case=='redirect' else ''),
                read1=MagicMock(side_effect=[b'x'*(MAX_INPUT_BYTES+1),b''] if case=='size' else [b'{}',b'']))
            context=MagicMock();context.__enter__.return_value=response
            opener=MagicMock();opener.open.return_value=context
            if case=='unavailable':opener.open.side_effect=TimeoutError()
            if case=='429':opener.open.side_effect=HTTPError(FEED,429,'rate limit',{},None)
            clock=iter([0,31,31]) if case=='timeout' else iter([0]*10)
            with self.subTest(case=case),patch('travel_intelligence.gdacs.build_opener',return_value=opener),patch(
                    'travel_intelligence.gdacs.time.monotonic',side_effect=lambda:next(clock)):
                if case=='ok':self.assertEqual(fetch_gdacs(),b'{}')
                else:
                    with self.assertRaises((ValueError,OSError)):fetch_gdacs()
                self.assertEqual(opener.open.call_count,1)
                request=opener.open.call_args.args[0]
                self.assertEqual(request.full_url,FEED);self.assertEqual(opener.open.call_args.kwargs,{'timeout':15})
                self.assertNotIn('Authorization',request.headers);self.assertNotIn('Cookie',request.headers)

    def test_offline_cli_single_and_combined_write_only_external_reports(self):
        files=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
        before={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files if f}
        for provider in ('gdacs','gdacs-usgs'):
            input_path=FIXTURE
            if provider=='gdacs-usgs':
                input_path=self.directory/'replay.json'
                input_path.write_bytes(canonical({'schema_version':3,'payloads':{'gdacs-multi-hazard':fixture(),
                    'usgs-earthquakes':load_json(ROOT/'tests/fixtures/travel-intelligence/usgs-synthetic.geojson')}}))
            result=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/global-travel-intelligence.py'),
                '--provider',provider,'--input',str(input_path),'--now',stamp(NOW),
                '--state-dir',str(self.directory/(provider+'-state')),'--output',str(self.directory/(provider+'-reports'))],
                capture_output=True,text=True,cwd=ROOT)
            self.assertEqual(result.returncode,0,result.stderr)
            report=load_json(self.directory/(provider+'-reports')/'report.json')
            self.assertFalse(report['automatic_publication']);self.assertIn('observation_groups',report)
        self.assertEqual(before,{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in before})
        # Combined mode cannot start even one live request.
        result=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/global-travel-intelligence.py'),
            '--provider','gdacs-usgs','--live','--state-dir',str(self.directory/'x'),'--output',str(self.directory/'y')],
            capture_output=True,text=True,cwd=ROOT)
        self.assertEqual(result.returncode,2);self.assertFalse((self.directory/'x').exists())


if __name__=='__main__':unittest.main()
