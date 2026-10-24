"""Conservative NWS NYC Heat Advisory projection; no Git, scheduler or publisher.

Raw provider input and public projection stay separate. Fixtures are always synthetic.
"""
from __future__ import annotations
from collections import Counter
from datetime import timedelta
import re
import time
from urllib.request import Request, build_opener

from .providers import NoRedirect
from .validation import ValidationError, canonical, digest, instant, keys, parse_json, plain, require, stamp

ENDPOINT = 'https://api.weather.gov/alerts/active?area=NY'
PREFIX = 'https://api.weather.gov/alerts/'
POLICY = 'nws-nyc-heat-v1'
ZONES = {'NYZ072':'Manhattan', 'NYZ073':'Bronx', 'NYZ074':'Staten Island',
         'NYZ075':'Brooklyn', 'NYZ176':'Northern Queens', 'NYZ178':'Southern Queens'}
TTL = timedelta(minutes=20)
GEOGRAPHY_VALID_UNTIL = instant('2026-11-23T00:00:00Z')
ID = re.compile(r'urn:oid:2\.49\.0\.1\.840\.0\.[a-f0-9]{40}\.\d{3}\.\d{1,3}')
MAX_BYTES = 2_000_000


def alert_id(value):
    require(type(value) is str and ID.fullmatch(value), 'nws_id')
    return value


def fetch():
    """One fixed HTTPS GET; redirect/compression/oversize/slow responses refused."""
    req = Request(ENDPOINT, headers={
        'User-Agent':'TripGuidelyNWSQualification/5 (+https://tripguidely.github.io/contact/)',
        'Accept':'application/geo+json', 'Accept-Encoding':'identity'})
    started = time.monotonic()
    with build_opener(NoRedirect()).open(req, timeout=15) as response:
        require(response.status == 200 and response.geturl() == ENDPOINT, 'nws_http')
        require(response.headers.get_content_type() in {'application/geo+json','application/ld+json'}, 'nws_content_type')
        require(response.headers.get('Content-Encoding', 'identity') == 'identity', 'nws_compression')
        size = response.headers.get('Content-Length')
        require(size is None or (size.isdecimal() and int(size) <= MAX_BYTES), 'nws_size')
        chunks, total = [], 0
        while True:
            require(time.monotonic() - started <= 30, 'nws_timeout')
            chunk = response.read1(16384)
            if not chunk:
                break
            total += len(chunk)
            require(total <= MAX_BYTES, 'nws_size')
            chunks.append(chunk)
        require(time.monotonic() - started <= 30, 'nws_timeout')
    return b''.join(chunks)


def metadata(feature, now):
    require(type(feature) is dict and feature.get('type') == 'Feature', 'nws_feature')
    p = feature.get('properties')
    require(type(p) is dict, 'nws_properties')
    ident = alert_id(p.get('id'))
    require(feature.get('id') == p.get('@id') == PREFIX + ident, 'nws_identity')
    sent = instant(p.get('sent'))
    require(sent <= now, 'nws_sent')
    require(p.get('sender') == 'w-nws.webmaster@noaa.gov' and p.get('senderName') == 'NWS Upton NY', 'nws_issuer')
    require(p.get('status') == 'Actual' and p.get('scope') == 'Public' and p.get('language') == 'en-US', 'nws_status')
    require(p.get('messageType') in {'Alert','Update','Cancel'}, 'nws_message_type')
    refs = p.get('references')
    require(type(refs) is list and len(refs) <= 50, 'nws_references')
    ref_ids = []
    for ref in refs:
        require(type(ref) is dict, 'nws_reference')
        rid = alert_id(ref.get('identifier'))
        require(rid != ident and ref.get('@id') == PREFIX + rid and
                ref.get('sender') == p['sender'] and instant(ref.get('sent')) <= sent, 'nws_reference')
        ref_ids.append(rid)
    require(p['messageType'] == 'Alert' or bool(ref_ids), 'nws_reference')
    return p, sent, ref_ids


def project(p, now, geometry=None):
    require(p.get('event') == 'Heat Advisory' and p.get('category') == 'Met', 'event_not_qualified')
    require(geometry is None, 'nws_geometry_unqualified')
    require(type(p.get('eventCode')) is dict and p['eventCode'].get('NationalWeatherService') == ['HTY'], 'nws_event_code')
    require(p.get('messageType') in {'Alert','Update'}, 'nws_cancelled')
    require(p.get('severity') in {'Minor','Moderate','Severe'} and
            p.get('certainty') in {'Observed','Likely'} and p.get('urgency') in {'Immediate','Expected'}, 'nws_hazard_status')
    # Execute is standard CAP metadata for Heat Advisory, not an instruction we reproduce.
    # Evacuation, shelter and all-clear response products stay outside this policy.
    require(p.get('response') in {'Prepare','Monitor','None','Execute'}, 'sensitive_response')
    effective, expires = instant(p.get('effective')), instant(p.get('expires'))
    sent = instant(p['sent'])
    require(now - timedelta(hours=72) <= sent, 'nws_bulletin_age')
    require(sent <= effective <= now and now < expires <= now + timedelta(hours=72), 'nws_validity')
    onset = None if p.get('onset') is None else instant(p['onset'])
    ends = None if p.get('ends') is None else instant(p['ends'])
    require(onset is None or sent <= onset and onset <= (ends or expires), 'nws_onset')
    if ends is not None:
        require(now < ends <= now + timedelta(hours=72), 'nws_ends')
    zones = p.get('affectedZones')
    require(type(zones) is list and 0 < len(zones) <= 200 and len(set(zones)) == len(zones), 'nws_zones')
    codes = []
    for url in zones:
        require(type(url) is str and re.fullmatch(r'https://api\.weather\.gov/zones/forecast/[A-Z]{2}Z\d{3}', url), 'nws_zone_url')
        codes.append(url.rsplit('/',1)[1])
    geocode = p.get('geocode')
    require(type(geocode) is dict and type(geocode.get('UGC')) is list and
            all(type(code) is str for code in geocode['UGC']) and set(geocode['UGC']) == set(codes), 'nws_geocode')
    local = sorted(set(codes) & set(ZONES))
    require(bool(local), 'outside_nyc')
    # No geometry inference: explicit forecast-zone membership is required. Null geometry is normal.
    # A hostile headline/description is rejected even though it is never copied to the public feed.
    plain(p.get('headline'), 500)
    plain(p.get('description'), 16000)
    if p.get('instruction'):
        plain(p['instruction'], 8000)
    source_expiry = min(expires, ends) if ends else expires
    require(onset is None or onset <= source_expiry, 'nws_onset_after_information_expiry')
    return {'id':p['id'], 'event':'Heat Advisory', 'zones':local,
            'sentAt':stamp(sent), 'effectiveAt':stamp(effective),
            'onsetAt':stamp(onset) if onset else None, 'verifiedAt':stamp(now),
            'sourceExpiresAt':stamp(source_expiry), 'expiresAt':stamp(min(now + TTL, source_expiry, GEOGRAPHY_VALID_UNTIL)),
            'sourceUrl':PREFIX + p['id']}


def empty_feed(now, synthetic=False, status='checked'):
    return {'schema':2, 'policy':POLICY, 'sourceId':'nws-nyc', 'synthetic':synthetic,
            'status':status, 'generatedAt':stamp(now), 'expiresAt':stamp(now + TTL), 'advisories':[]}


def collect(raw, now, *, synthetic):
    require(now.utcoffset() is not None and type(synthetic) is bool, 'nws_clock')
    require(now < GEOGRAPHY_VALID_UNTIL, 'nws_geography_review_due')
    data = parse_json(raw, limit=MAX_BYTES)
    require(type(data) is dict and data.get('type') == 'FeatureCollection', 'nws_collection')
    require(now - timedelta(minutes=20) <= instant(data.get('updated')) <= now, 'nws_export_age')
    require(not data.get('pagination'), 'nws_partial_collection')
    features = data.get('features')
    require(type(features) is list and len(features) <= 1000, 'nws_count')
    records, seen, held, superseded = {}, {}, Counter(), set()
    for feature in features:
        # Neighboring issuing offices are held; malformed identities/revisions fail the batch closed.
        require(type(feature) is dict and type(feature.get('properties')) is dict, 'nws_feature')
        p = feature['properties']
        ident = alert_id(p.get('id'))
        fingerprint = digest(feature)
        require(ident not in seen or seen[ident] == fingerprint, 'nws_conflicting_duplicate')
        if ident in seen:
            held['exact_duplicate'] += 1
            continue
        seen[ident] = fingerprint
        try:
            meta, sent, refs = metadata(feature, now)
        except ValidationError as error:
            # Unsafe identity or reference chains must not let an old observation survive.
            local_urls = {'https://api.weather.gov/zones/forecast/' + code for code in ZONES}
            affected = p.get('affectedZones')
            local_issuer_change = (str(error) == 'nws_issuer' and type(affected) is list and
                                  any(type(url) is str and url in local_urls for url in affected))
            if local_issuer_change or str(error) not in {'nws_issuer','nws_status'}:
                raise
            held[str(error)] += 1
            continue
        if p['messageType'] in {'Update','Cancel'}:
            superseded.update(refs)
        records[ident] = (p, sent, feature.get('geometry'))
    advisories = []
    for ident, (p, _, geometry) in records.items():
        if ident in superseded:
            held['superseded'] += 1
            continue
        try:
            advisories.append(project(p, now, geometry))
        except (ValidationError, TypeError) as error:
            held[str(error) if isinstance(error, ValidationError) else 'nws_schema'] += 1
    require(len(advisories) <= 20, 'nws_public_count')
    advisories.sort(key=lambda item: (item['sentAt'],item['id']), reverse=True)
    feed = empty_feed(now, synthetic)
    feed['advisories'] = advisories
    return feed, {'status':'checked','source':ENDPOINT,'sourceUpdatedAt':stamp(instant(data['updated'])),
                  'verifiedAt':stamp(now),'qualified':len(advisories),'held':dict(sorted(held.items())),
                  'safetyConclusion':None}


def changes(previous, current, now):
    before = {item['id']:item for item in previous.get('advisories',[])}
    after = {item['id']:item for item in current['advisories']}
    result = []
    for ident in sorted(before.keys() | after.keys()):
        if ident not in before:
            kind = 'new_observation'
        elif ident not in after:
            kind = 'source_unavailable' if current['status'] == 'unavailable' else (
                'expired_observation' if instant(before[ident]['expiresAt']) <= now else 'not_in_current_qualified_feed')
        else:
            old, new = dict(before[ident]), dict(after[ident])
            for key in ('verifiedAt','expiresAt'):
                old.pop(key); new.pop(key)
            if old == new:
                continue
            kind = 'corrected_observation'
        result.append({'id':ident,'change':kind})
    return result
