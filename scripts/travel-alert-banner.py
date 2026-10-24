"""Loopback-only synthetic preview. No live reader, public feed or publisher.

python -B scripts/travel-alert-banner.py --port 8766
"""
from __future__ import annotations
import argparse
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
from travel_intelligence.validation import canonical, parse_json

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ('cyclone', 'health', 'empty', 'expired', 'other-country', 'other-city', 'multiple', 'expires-soon', 'unavailable', 'malformed')


def automatic_publication_candidates(report):
    """No V3 source is qualified for automatic destination-impact publication.

    Return no claims irrespective of severity or review flags. This explicit gate
    does not rebuild the existing collection/normalization engine.
    """
    return []


def synthetic_feed(case, now=None):
    if case not in SCENARIOS:
        raise ValueError('unknown_scenario')
    now = now or datetime.now(timezone.utc)
    stamp = lambda value: value.isoformat(timespec='milliseconds').replace('+00:00', 'Z')
    fixtures = parse_json((ROOT / 'tests/fixtures/travel-alert-banner/scenarios.json').read_bytes(), limit=65536)
    cities = parse_json((ROOT / 'config/travel-intelligence/destinations.json').read_bytes())['destinations']
    city = next(item for item in cities if item['destination_id'] == 'us-new-york-city')
    generated = now - timedelta(seconds=60) if case == 'expired' else now
    expires = now + timedelta(seconds=8 if case == 'expires-soon' else 1800)
    if case == 'expired':
        expires = now - timedelta(seconds=1)
    advisories = []
    for kind in (('cyclone', 'health') if case == 'multiple' else ('health' if case == 'health' else 'cyclone',)):
        item = dict(fixtures[kind])
        item.update(id='synthetic-' + kind, priority=1 if kind == 'health' else 2,
                    destination=city['destination_id'], country=city['country_code'], area='New York City · demonstration area',
                    verifiedAt=stamp(generated), expiresAt=stamp(expires), evidence='synthetic-review-only')
        if case == 'other-country':
            item.update(destination='gb-london', country='GB', area='London · demonstration area')
        if case == 'other-city':
            item.update(destination='us-boston', country='US', area='Boston · demonstration area')
        advisories.append(item)
    return dict(schema=1, synthetic=True, generatedAt=stamp(generated), expiresAt=stamp(expires),
                advisories=[] if case == 'empty' else advisories)


HTML = b'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>TripGuidely | Local advisory prototype</title>
<link rel="icon" href="data:,"><link rel="stylesheet" href="/demo.css"><link rel="stylesheet" href="/banner.css"></head>
<body><header><div class="demo-note">LOCAL SYNTHETIC DEMO &middot; No real travel alerts &middot; Not connected to production</div>
<div class="brand"><a href="/">TripGuidely<span> / local preview</span></a></div></header>
<main><p class="eyebrow">DESTINATION GUIDE / UNITED STATES</p><h1>A considered stay<br>in New York.</h1>
<p class="intro">A quiet place for practical travel information, before you explore.</p>
<form><label for="scenario">Synthetic scenario</label> <select id="scenario" name="case">
<option value="cyclone">Fictional cyclone</option><option value="health">Fictional health notice</option>
<option value="empty">No advisory</option><option value="expired">Expired advisory</option>
<option value="other-country">Another country</option><option value="other-city">Another city</option>
<option value="multiple">Multiple: one priority notice</option><option value="expires-soon">Disappears after 8 seconds</option>
<option value="unavailable">Feed unavailable</option><option value="malformed">Malformed feed</option>
</select> <button type="submit">Preview</button></form>
<div class="tg-advisory-slot" id="destination-advisory"></div>
<section class="guide" aria-labelledby="guide-heading"><div><p class="eyebrow">PLAN WITH CONFIDENCE</p>
<h2 id="guide-heading">Make room for the trip.</h2><p>This is a local interface exercise. No hotel inventory, booking links or public pages are loaded.</p>
<p>Blank advisory space is reserved to prevent content movement. An absent notice makes no statement about safety.</p></div>
<aside><span>01 / THE ESSENTIALS</span><p>One notice.<br>Clear provenance.<br>A defined expiry.</p></aside></section>
<p class="footnote">With JavaScript disabled or an invalid feed, the advisory remains absent. Official references do not substantiate these fictional scenarios.</p>
</main><script type="module" src="/demo.js"></script></body></html>'''

DEMO_JS = b'''import {mountBanner} from '/banner.js';
const scenario = new URL(location.href).searchParams.get('case') || 'cyclone';
const select = document.querySelector('select'); if ([...select.options].some(x=>x.value===scenario)) select.value=scenario;
mountBanner(document.querySelector('#destination-advisory'), {feedUrl:'/feed.json?case='+encodeURIComponent(scenario),
 destination:'us-new-york-city',country:'US',demo:true});'''
DEMO_CSS = b'''*{box-sizing:border-box}body{margin:0;background:#faf8f3;color:#12243a;font:16px/1.6 system-ui,sans-serif}
.demo-note{text-align:center;background:#12243a;color:white;padding:.5rem 1rem;font-size:.75rem;letter-spacing:.04em}
header .brand{max-width:1056px;margin:auto;padding:1.4rem 2rem;border-bottom:1px solid #d9dedc}header a{font-weight:750;font-size:1.3rem;color:#0b7478;text-decoration:none}header span{font-size:.8rem;font-weight:400;color:#475569}
main{max-width:960px;margin:3rem auto;padding:0 2rem}.eyebrow{font-size:.72rem;font-weight:650;letter-spacing:.12em;color:#475569}
h1{font:400 clamp(2.6rem,6vw,4rem)/1.1 Georgia,serif;margin:1rem 0}.intro{color:#475569;max-width:40rem}form{margin-top:2rem;display:flex;gap:.5rem;align-items:center;flex-wrap:wrap;font-size:.875rem}select,button{font:inherit;min-height:44px;padding:.5rem .7rem;border:1px solid #798a89;border-radius:.4rem;background:white;color:#12243a}button{background:#0b7478;color:white;cursor:pointer}a:focus-visible,select:focus-visible,button:focus-visible{outline:3px solid #0b7478;outline-offset:3px}
.guide{border-top:1px solid #d9dedc;padding-top:2rem;display:grid;grid-template-columns:2fr 1fr;gap:3rem}.guide h2{font:400 2rem Georgia,serif}.guide p,.footnote{color:#475569}.guide aside{border-left:1px solid #d9dedc;padding-left:2rem}.guide aside span{font-size:.7rem;letter-spacing:.08em}.guide aside p{font:400 1.4rem/1.5 Georgia,serif}.footnote{font-size:.8rem;margin-top:2rem}@media(max-width:640px){main{margin-top:2rem;padding:0 1.25rem}header .brand{padding:1rem 1.25rem}.guide{grid-template-columns:1fr;gap:1rem}.guide aside{display:none}}'''


class PreviewHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Fixed routes only: no directory serving, writes, external assets or requests.
        route = urlsplit(self.path)
        if self.headers.get('Host') not in {'127.0.0.1:' + str(self.server.server_port), 'localhost:' + str(self.server.server_port)}:
            self.send_error(403); return
        status = 200
        assets = {'/banner.js': ('text/javascript', ROOT / 'scripts/travel_alert_banner/banner.js'),
                  '/banner.css': ('text/css', ROOT / 'scripts/travel_alert_banner/banner.css')}
        if route.path == '/':
            mime, body = 'text/html', HTML
        elif route.path == '/demo.js':
            mime, body = 'text/javascript', DEMO_JS
        elif route.path == '/demo.css':
            mime, body = 'text/css', DEMO_CSS
        elif route.path in assets:
            mime, path = assets[route.path]; body = path.read_bytes()
        elif route.path == '/feed.json':
            case = parse_qs(route.query).get('case', ['cyclone'])[0]
            if case not in SCENARIOS:
                self.send_error(400); return
            mime = 'application/json'
            body = b'{' if case == 'malformed' else canonical(synthetic_feed(case))
            if case == 'unavailable':
                status, body = 503, b'{}'
        else:
            self.send_error(404); return
        self.send_response(status)
        self.send_header('Content-Type', mime + '; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Robots-Tag', 'noindex, nofollow')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src data:; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
        self.end_headers(); self.wfile.write(body)

    def log_message(self, *args):
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8766)
    args = parser.parse_args()
    ThreadingHTTPServer.allow_reuse_address = False
    server = ThreadingHTTPServer(('127.0.0.1', args.port), PreviewHandler)
    print('SYNTHETIC LOCAL PREVIEW http://127.0.0.1:' + str(server.server_port), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
