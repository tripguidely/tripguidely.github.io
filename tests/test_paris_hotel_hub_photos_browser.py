"""Local Chromium visual/geometry QA; no outbound affiliate navigation.

python -B tests/test_paris_hotel_hub_photos_browser.py
Requires playwright (the ignored .qa-paris-hub/deps install is detected).
"""
import argparse
import asyncio
import base64
import json
import mimetypes
from pathlib import Path
import re
import sys
import subprocess
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.qa-paris-hub/deps'))
from playwright.async_api import async_playwright

ORIGIN = 'https://tripguidely.github.io'
TILE = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a5qkAAAAASUVORK5CYII=')
WIDTHS = [320, 375, 390, 430, 768, 1024, 1440]
OBSERVE = """() => {
window.__photoQA={lcp:[],shifts:[]};
new PerformanceObserver(list => {for(const e of list.getEntries())window.__photoQA.lcp.push({url:e.url,ms:e.startTime});}).observe({type:'largest-contentful-paint',buffered:true});
new PerformanceObserver(list => {for(const e of list.getEntries())if(!e.hadRecentInput)window.__photoQA.shifts.push(e.value);}).observe({type:'layout-shift',buffered:true});
localStorage.setItem('tg_consent_v2','denied');
}"""


async def run(args):
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / '.qa-paris-hub'), 'Screenshots and runtime data stay in ignored QA folder'
    qa_root = ROOT / '.qa-paris-hub'
    qa_root.mkdir(parents=True, exist_ok=True)
    ignore = qa_root / '.gitignore'
    if not ignore.exists():
        ignore.write_text('*\n', encoding='utf-8')
    out.mkdir(parents=True, exist_ok=True)
    before = subprocess.check_output(['git', '-C', str(ROOT), 'show', '2549de3c4aae381e4117e3e659639962bc6429a4:hotels/paris/index.html'])
    report = {'passed': False, 'checks': 0, 'scenarios': [], 'performance': [],
              'network': 'Local route fulfillment; third-party scripts blocked; OSM tiles mocked. No field performance claim.'}
    def check(value, message):
        assert value, message
        report['checks'] += 1

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, executable_path=args.chrome)
        try:
            async def open_page(width, js=True, baseline=False):
                context = await browser.new_context(viewport={'width':width,'height':1000},
                    java_script_enabled=js, is_mobile=width<500, has_touch=width<500,
                    reduced_motion='reduce', service_workers='block', device_scale_factor=1)
                requests, missing, errors = [], [], []
                async def route(handler):
                    url = urlsplit(handler.request.url)
                    if url.hostname == 'tile.openstreetmap.org':
                        await handler.fulfill(body=TILE, content_type='image/png'); return
                    if url.scheme+'://'+url.netloc != ORIGIN:
                        await handler.abort(); return
                    requests.append(url.path)
                    target = (ROOT / unquote(url.path).lstrip('/')).resolve()
                    if not target.is_relative_to(ROOT) or target.is_relative_to(ROOT/'.qa-paris-hub'):
                        await handler.abort(); return
                    if target.is_dir(): target = target/'index.html'
                    if not target.is_file():
                        missing.append(url.path); await handler.fulfill(status=404,body=''); return
                    data = before if baseline and url.path=='/hotels/paris/' else target.read_bytes()
                    mime = {'.avif':'image/avif','.webp':'image/webp','.css':'text/css','.js':'text/javascript'}.get(target.suffix) or mimetypes.guess_type(str(target))[0] or 'application/octet-stream'
                    await handler.fulfill(body=data,content_type=mime)
                await context.route('**/*', route)
                if js: await context.add_init_script('(' + OBSERVE + ')()')
                page = await context.new_page()
                page.on('pageerror',lambda e: errors.append(str(e)))
                await page.goto(ORIGIN+'/hotels/paris/',wait_until='networkidle')
                if js: await page.wait_for_function("document.getElementById('area-map').dataset.mapBound === '1'")
                return context,page,requests,missing,errors

            # Same local harness, three repetitions for both variants at mobile/desktop.
            for width in (390,1440):
                for repetition in range(3):
                    for baseline in (True,False):
                        context,page,requests,missing,errors = await open_page(width,baseline=baseline)
                        try:
                            perf = await page.evaluate('window.__photoQA')
                            check(not any('/assets/images/hotels/paris/' in r for r in requests), 'No shortlist photo requested at initial viewport')
                            check(not missing and not errors, 'Initial load has no local missing asset or JS exception')
                            report['performance'].append({'width':width,'repetition':repetition+1,'variant':'base' if baseline else 'photos','lcp':perf['lcp'][-1] if perf['lcp'] else None,'cls':sum(perf['shifts']),'hotel_requests_initial':0})
                        finally: await context.close()

            for width in WIDTHS:
                for js in (True,False):
                    context,page,requests,missing,errors = await open_page(width,js=js)
                    try:
                        photos = page.locator('#hotel-picks .tg-hotel-photo img')
                        check(await photos.count()==7, 'Seven photos in browser')
                        frames = []
                        for i in range(7):
                            img = photos.nth(i)
                            await img.scroll_into_view_if_needed()
                            await img.evaluate('(n) => n.decode()')
                            geometry = await img.evaluate("""n => {
                              const f=n.closest('figure').getBoundingClientRect(),c=n.closest('article').getBoundingClientRect();
                              const s=getComputedStyle(n),r=getComputedStyle(n.closest('figure'));
                              return {width:n.width,height:n.height,naturalWidth:n.naturalWidth,naturalHeight:n.naturalHeight,
                                attrWidth:Number(n.getAttribute('width')),attrHeight:Number(n.getAttribute('height')),
                                fit:s.objectFit,frameWidth:f.width,frameHeight:f.height,frameLeft:f.left,frameRight:f.right,
                                cardLeft:c.left,cardRight:c.right,radius:r.borderTopLeftRadius,
                                alt:n.alt,loading:n.loading,decoding:n.decoding};
                            }""")
                            check(geometry['naturalWidth']==geometry['attrWidth'] and geometry['naturalHeight']==geometry['attrHeight'], 'Decoded dimensions match HTML')
                            check(geometry['fit']=='contain', 'Full composition retained with contain')
                            check(abs(geometry['frameWidth']/geometry['frameHeight']-1.5)<.01, 'Consistent 3:2 frame')
                            check(geometry['cardLeft']>=-.5 and geometry['cardRight']<=width+.5 and geometry['frameLeft']>=-.5 and geometry['frameRight']<=width+.5, 'Photo/card fit viewport')
                            check(geometry['radius']!='0px' and geometry['alt'] and geometry['loading']=='lazy' and geometry['decoding']=='async', 'Rounded photo and accessible loading attributes')
                            frames.append(geometry)
                        check(await page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'No horizontal document overflow')
                        check(await page.locator('#hotel-picks figcaption').count()==0, 'No photo captions')
                        check(await page.locator('#hotel-picks a.js-aff').count()==7, 'Seven hotel CTA remain')
                        check(await page.locator('#hotel-picks .tg-hotel-action > span').count()==0, 'No visible new-tab note under hotel CTA')
                        check('Opens in a new tab' not in await page.locator('#hotel-picks').inner_text(), 'Removed note absent from visible shortlist text')
                        accessible_names = []
                        for link in await page.locator('#hotel-picks a.js-aff').all():
                            name = await link.get_attribute('aria-label')
                            check(name.endswith('(opens in a new tab)'), 'Accessible name still announces new tab')
                            check(await page.get_by_role('link', name=name, exact=True).count()==1, 'Expected accessible link name resolves uniquely')
                            check(await link.inner_text()=='Check availability on Klook', 'Visible CTA wording exact')
                            check(await link.get_attribute('target')=='_blank' and set((await link.get_attribute('rel')).split())=={'nofollow','sponsored','noopener'}, 'New-tab behavior and safety rel exact')
                            accessible_names.append(name)
                        # Focus each CTA through Tab without following its affiliate destination.
                        for i in range(7):
                            article=page.locator('#hotel-picks article').nth(i)
                            await article.locator('h3').evaluate("n=>{n.setAttribute('tabindex','-1');n.focus();}")
                            await page.keyboard.press('Tab')
                            focused = await article.locator('a.js-aff').evaluate("n=>document.activeElement===n")
                            check(focused, 'Hotel CTA keyboard reachable')
                        if js:
                            await page.locator('#area-map-canvas').scroll_into_view_if_needed()
                            await page.wait_for_selector('#area-map-canvas[data-map-ready="1"]')
                            check(await page.locator('#area-map-choices button').count()==10, 'Ten neighborhood controls')
                            check(await page.locator('.tg-zone-map__pin').count()==10, 'Ten Leaflet pins')
                        else:
                            check(await page.locator('#area-map-choices a').count()==10, 'Ten fallback neighborhood links without JS')
                        check(not missing and not errors, 'No local 404 or JS exception throughout scroll')
                        await page.locator('#hotel-picks').screenshot(path=str(out/f'hotels-{width}-{"js" if js else "nojs"}.png'))
                        if js and width in (390,1440):
                            await photos.first.scroll_into_view_if_needed()
                            await page.screenshot(path=str(out/f'viewport-{width}.png'))
                        report['scenarios'].append({'width':width,'javascript':js,'images':frames,'accessible_names':accessible_names,'missing':missing,'errors':errors})
                    finally: await context.close()
            report['passed']=True
        finally:
            await browser.close()
            (out/'browser-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
            args.report.resolve().write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':report['passed'],'checks':report['checks'],'scenarios':len(report['scenarios']),'performance_runs':len(report['performance']),'output':str(out)}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chrome',default=None, help='Optional installed Chromium/Chrome executable; otherwise use Playwright Chromium')
    parser.add_argument('--output',type=Path,default=ROOT/'.qa-paris-hub/browser')
    parser.add_argument('--report',type=Path,default=ROOT/'.qa-paris-hub/browser/browser-report.json')
    asyncio.run(run(parser.parse_args()))
