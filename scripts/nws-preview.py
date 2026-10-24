"""Read-only preview of existing NYC pages; synthetic NWS data never leaves loopback."""
import argparse
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
from urllib.parse import parse_qs, urlsplit

from travel_intelligence.nws import collect, empty_feed
from travel_intelligence.validation import canonical, load_json, stamp

ROOT=Path(__file__).resolve().parents[1]
PROFILE=load_json(ROOT/'config/travel-intelligence/nws-nyc.json')
CASES={'valid','empty','expired','neighbor','malformed','unavailable','expires-soon'}


def preview_feed(case,now=None):
    now=now or datetime.now(timezone.utc)
    data=load_json(ROOT/'tests/fixtures/nws/heat-synthetic.json')
    p=data['features'][0]['properties']
    data['updated']=stamp(now)
    p['sent']=p['effective']=stamp(now-timedelta(minutes=5));p['onset']=stamp(now-timedelta(minutes=2))
    p['expires']=stamp(now+timedelta(seconds=6 if case=='expires-soon' else 1800));p['ends']=stamp(now+timedelta(hours=1))
    if case=='neighbor':
        p['affectedZones']=['https://api.weather.gov/zones/forecast/NYZ079'];p['geocode']['UGC']=['NYZ079']
    if case=='empty':data['features']=[]
    feed,_=collect(canonical(data),now,synthetic=True)
    if case=='expired':feed['expiresAt']=stamp(now-timedelta(seconds=1))
    if case=='unavailable':feed=empty_feed(now,True,'unavailable')
    return feed


def preview_html(route,case):
    if route not in PROFILE['pages'] or case not in CASES:raise ValueError('preview_route')
    page=(ROOT/route.strip('/')/'index.html').read_text(encoding='utf-8')
    # Only the preview copy is altered. Avoid loading consent, trackers or third-party scripts.
    page=re.sub(r'<script\b(?![^>]*type=["\']application/ld\+json["\'])[^>]*>.*?</script>', '',page,flags=re.I|re.S)
    page=re.sub(r'<link\b(?=[^>]*href=[\"\']https?://)[^>]*>', '', page, flags=re.I)
    page=re.sub(r'<iframe\b[^>]*>.*?</iframe>','',page,flags=re.I|re.S)
    page=page.replace('</head>','<meta name="robots" content="noindex,nofollow"><link rel="stylesheet" href="/__nws/banner.css"></head>',1)
    note='<div role="note" class="nws-preview-note">LOCAL SYNTHETIC NWS PREVIEW — No real weather alert. Public pages are unchanged.</div>'
    page=re.sub(r'(<body\b[^>]*>)',lambda m:m[1]+note,page,count=1,flags=re.I)
    slot='<div class="tg-advisory-slot" id="destination-nws-advisory" data-preview-feed="/travel-alerts/nws-nyc.json?case='+case+'"></div>'
    # A reserved slot after the existing hero, not inside booking controls or above the LCP image.
    start=page.find('<section class="hero ')
    end=page.find('</section>',start)
    if start<0 or end<0:
        match=re.search(r'<main\b[^>]*>',page,re.I)
        if not match:raise ValueError('preview_main')
        end=match.end()
    else:end+=len('</section>')
    page=page[:end]+slot+page[end:]
    return page.replace('</body>','<script type="module" src="/__nws/nws-bootstrap.js"></script></body>').encode('utf-8')


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.headers.get('Host')!='127.0.0.1:'+str(self.server.server_port):self.send_error(403);return
        url=urlsplit(self.path);case=parse_qs(url.query).get('case',['valid'])[0]
        if case not in CASES:self.send_error(400);return
        status=200
        if url.path=='/':
            body=b'<a href="/hotels/new-york/">Open synthetic preview on the existing New York hotel page</a>';mime='text/html'
        elif url.path in PROFILE['pages']:
            body=preview_html(url.path,case);mime='text/html'
        elif url.path=='/travel-alerts/nws-nyc.json':
            body=b'{' if case=='malformed' else canonical(preview_feed(case));mime='application/json'
            if case=='unavailable':status=503
        elif url.path.startswith('/__nws/') and url.path.split('/')[-1] in {'banner.js','banner.css','nws-bootstrap.js'}:
            name=url.path.split('/')[-1];body=(ROOT/'scripts/travel_alert_banner'/name).read_bytes();mime='text/css' if name.endswith('.css') else 'text/javascript'
        elif url.path.startswith('/assets/'):
            # Serve local design assets only; never scripts, symlinks, directories or paths outside assets.
            candidate=ROOT/url.path.lstrip('/')
            parts=[candidate,*candidate.parents]
            if any(p.is_symlink() or p.is_junction() for p in parts) or not candidate.resolve().is_relative_to((ROOT/'assets').resolve()) or not candidate.is_file() or candidate.suffix not in {'.css','.jpg','.jpeg','.png','.webp','.svg','.woff','.woff2'}:
                self.send_error(404);return
            body=candidate.read_bytes();mime={'.css':'text/css','.svg':'image/svg+xml','.woff':'font/woff','.woff2':'font/woff2'}.get(candidate.suffix,'image/'+candidate.suffix[1:])
        else:self.send_error(404);return
        self.send_response(status);self.send_header('Content-Type',mime+'; charset=utf-8');self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store');self.send_header('X-Robots-Tag','noindex,nofollow');self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
        self.end_headers();self.wfile.write(body)

    def log_message(self,*args):pass


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--port',type=int,default=8767);args=parser.parse_args()
    ThreadingHTTPServer.allow_reuse_address=False
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    print('LOCAL SYNTHETIC NWS http://127.0.0.1:'+str(server.server_port)+'/hotels/new-york/',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
