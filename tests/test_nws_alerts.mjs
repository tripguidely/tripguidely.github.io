import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import test, {after} from 'node:test';
const attempts=[];globalThis.fetch=async(...args)=>{attempts.push(args[0]);throw Error('Live network forbidden');};
after(()=>assert.deepEqual(attempts,[]));
const source=await readFile(new URL('../scripts/travel_alert_banner/banner.js',import.meta.url),'utf8');
const {validateFeed,selectAdvisory}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
const now=Date.parse('2026-10-24T12:00:00.000Z');
const context={destination:'us-new-york-city',country:'US'};
const options={demo:true,hostname:'127.0.0.1'};
const ts=ms=>new Date(ms).toISOString().replace('.000Z','.000000Z');
function feed(){const id='urn:oid:2.49.0.1.840.0.'+'a'.repeat(40)+'.001.1';return {
 schema:2,policy:'nws-nyc-heat-v1',sourceId:'nws-nyc',synthetic:true,status:'checked',generatedAt:ts(now),expiresAt:ts(now+1200000),
 advisories:[{id,event:'Heat Advisory',zones:['NYZ072'],sentAt:ts(now-3600000),effectiveAt:ts(now-3600000),onsetAt:ts(now-1800000),verifiedAt:ts(now),sourceExpiresAt:ts(now+3600000),expiresAt:ts(now+1200000),sourceUrl:'https://api.weather.gov/alerts/'+id}]};}
function refused(name,change,opts=options,ctx=context){test(name,()=>{const f=feed();change(f);assert.throws(()=>validateFeed(f,now,ctx,opts));});}
test('qualified NWS contract derives text instead of trusting external prose',()=>{const f=validateFeed(feed(),now,context,options);assert.equal(f.advisories[0].area,'New York City: Manhattan');assert.equal(f.advisories[0].title,'Heat Advisory');assert.ok(!f.advisories[0].description.includes('destruction'));});
test('real mode validates without a demo flag; no DOM or live network involved',()=>{const f=feed();f.synthetic=false;assert.equal(validateFeed(f,now,context,{hostname:'tripguidely.github.io'}).advisories.length,1);});
test('empty qualified collection displays nothing',()=>{const f=feed();f.advisories=[];assert.equal(selectAdvisory(validateFeed(f,now,context,options),context,now),null);});
test('expiry removes item independently of collection',()=>{const f=validateFeed(feed(),now,context,options);assert.equal(selectAdvisory(f,context,now+1200000),null);});
test('Queens remains partial rather than entire city',()=>{const f=feed();f.advisories[0].zones=['NYZ176'];assert.equal(validateFeed(f,now,context,options).advisories[0].area,'New York City: Northern Queens');});
refused('synthetic NWS data refused on public origin',()=>{},{demo:true,hostname:'tripguidely.github.io'});
refused('synthetic NWS data requires explicit local demo mode',()=>{},{hostname:'127.0.0.1'});
refused('wrong destination cannot show a NYC notice',()=>{},options,{destination:'fr-paris',country:'FR'});
refused('neighboring NY zone cannot become NYC',f=>{f.advisories[0].zones=['NYZ079'];});
refused('statewide code is insufficient',f=>{f.advisories[0].zones=['NY'];});
refused('duplicate zones refused',f=>{f.advisories[0].zones=['NYZ072','NYZ072'];});
refused('unqualified NWS event refused',f=>{f.advisories[0].event='Tsunami Warning';});
refused('unavailable source cannot reuse an old notice',f=>{f.status='unavailable';});
refused('unrecognized policy refused',f=>{f.policy='publish-everything';});
refused('unknown fields and HTML refused',f=>{f.advisories[0].description='<script>alert(1)</script>';});
refused('source lookalike refused',f=>{f.advisories[0].sourceUrl=f.advisories[0].sourceUrl.replace('api.weather.gov','api.weather.gov.evil');});
refused('mismatched source identity refused',f=>{f.advisories[0].sourceUrl+='1';});
refused('duplicate CAP identifiers refused',f=>{f.advisories.push({...f.advisories[0]});});
refused('malformed calendar date refused',f=>{f.advisories[0].sentAt='2026-02-30T11:00:00.000000Z';});
refused('future verification refused',f=>{f.generatedAt=ts(now+1);});
refused('stale bulletin refused',f=>{f.advisories[0].sentAt=ts(now-259200001);});
refused('different verification instant refused',f=>{f.advisories[0].verifiedAt=ts(now-1000);});
refused('overlong freshness refused',f=>{f.expiresAt=ts(now+1200001);});
refused('item cannot outlive source information',f=>{f.advisories[0].sourceExpiresAt=ts(now+1);});
refused('expired feed refused',f=>{f.expiresAt=ts(now);});
refused('onset after information expiry refused',f=>{f.advisories[0].onsetAt=ts(now+3600001);});
test('geography qualification expiry disables old policy',()=>assert.throws(()=>validateFeed(feed(),Date.parse('2026-11-24T00:00:00Z'),context,options)));
test('client and collector zone labels agree',async()=>{const config=JSON.parse(await readFile(new URL('../config/travel-intelligence/nws-nyc.json',import.meta.url),'utf8'));for(const [zone,label]of Object.entries(config.zones)){const f=feed();f.advisories[0].zones=[zone];assert.equal(validateFeed(f,now,context,options).advisories[0].area,'New York City: '+label);}});
