// Chrome integration QA. Affiliate/analytics requests never leave the test.
// node tests/test_paris_luxury_hotel_map.cjs PLAYWRIGHT_MODULE CHROME_EXECUTABLE OUTPUT_DIR [--screenshots]
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {execFileSync} = require('node:child_process');
const {chromium} = require(process.argv[2] || 'playwright-core');
const root = path.resolve(__dirname, '..');
const out = path.resolve(process.argv[4]);
assert(out !== root && !out.startsWith(root + path.sep));
fs.mkdirSync(out, {recursive:true});
const routePath = '/hotels/paris/luxury-hotels/';
const origin = 'https://tripguidely.github.io';
const originals = execFileSync('git', ['show', '9d3301f0ffff927ba796d7f33e06e3031fb319a2:hotels/paris/luxury-hotels/index.html'], {cwd:root,encoding:'utf8'});
const anchors = originals.match(/<a class="tg-button tg-button--primary js-aff"[^>]*>Check availability on Klook<\/a>/g);
const listSelector = '#hotel-options article, #premium-alternative article';
const linkSelector = '#hotel-options a.js-aff, #premium-alternative a.js-aff';
const mime = {'.html':'text/html','.css':'text/css','.js':'text/javascript','.webp':'image/webp','.avif':'image/avif','.png':'image/png','.svg':'image/svg+xml'};
const tile = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a5qkAAAAASUVORK5CYII=', 'base64');
let checks = 0;
const report = {passed:false,checks:0,scenarios:[],screenshots:[]};
function equal(a,b,msg) { assert.deepEqual(a,b,msg); checks++; }
function ok(a,msg) { assert(a,msg); checks++; }
(async () => {
  const browser = await chromium.launch({headless:true,executablePath:process.argv[3]});
  try {
    async function open(options={}) {
      const context = await browser.newContext({viewport:{width:options.width||1440,height:1000},isMobile:!!options.mobile,hasTouch:!!options.mobile,javaScriptEnabled:options.js!==false,reducedMotion:'reduce',serviceWorkers:'block'});
      const requests=[],errors=[],missing=[];
      await context.route('**/*', async handler => {
        const u=new URL(handler.request().url()); requests.push(u.href);
        if(u.hostname==='tile.openstreetmap.org') {
          if(options.tiles==='real') return handler.continue();
          if(options.tiles==='fail') return handler.abort();
          return handler.fulfill({body:tile,contentType:'image/png'});
        }
        if(u.origin!==origin) return handler.abort();
        if(options.libraryFail && u.pathname.endsWith('/leaflet.js')) return handler.abort();
        let file=path.resolve(root,'.'+decodeURIComponent(u.pathname));
        if(!file.startsWith(root+path.sep)) return handler.abort();
        if(fs.existsSync(file) && fs.statSync(file).isDirectory()) file=path.join(file,'index.html');
        if(!fs.existsSync(file)) {missing.push(u.pathname); return handler.fulfill({status:404,body:''});}
        return handler.fulfill({body:fs.readFileSync(file),contentType:mime[path.extname(file)]||'application/octet-stream'});
      });
      await context.addInitScript(consent=>{
        if(consent!==null) localStorage.setItem('tg_consent_v2',consent);
        window.trackingCalls=[];
        window.gtag=function(){window.trackingCalls.push(Array.from(arguments));};
        document.addEventListener('click',event=>{if(event.target.closest('a.js-aff'))event.preventDefault();},true);
      },options.consent===undefined?'granted':options.consent);
      if(options.noObserver) await context.addInitScript(()=>{delete window.IntersectionObserver;});
      const page=await context.newPage(); page.on('pageerror',e=>errors.push(e.message));
      await page.goto(origin+(options.path||routePath));
      if(options.js!==false) await page.waitForFunction(()=>document.documentElement.dataset.affiliateclicksBound==='1');
      return {context,page,requests,errors,missing};
    }
    async function activate(page) {
      await page.locator('#hotel-map').scrollIntoViewIfNeeded();
      await page.locator('#hotel-map-canvas[data-map-ready="1"]').waitFor();
    }
    async function events(page) {return page.evaluate(()=>trackingCalls.filter(c=>c[0]==='event'&&c[1]==='affiliate_click').map(c=>c[2]));}
    const payload = destination=>({affiliate_program:'klook',page_type:'guide',destination,transport_type:'beacon'});
    for(const consent of [null,'denied','granted']) {
      const {context,page,requests,errors,missing}=await open({consent});
      try {
        equal(await page.locator(linkSelector).evaluateAll(a=>a.map(n=>n.outerHTML)),anchors,'All original list anchors must remain exact');
        equal(await page.locator('#hotel-map-view').isVisible(),true);
        equal(await page.locator('#hotel-map-choices button').count(),4);
        equal(requests.filter(u=>u.includes('/leaflet-1.9.4/')||u.includes('tile.openstreetmap.org')).length,0);
        equal(await page.locator('#how-we-select .tg-hotel-disclosure').count(),1);
        equal(await page.locator('.tg-hotel-action span, .tg-hotel-map__action span').count(),0);
        await activate(page);
        equal(await page.locator('.tg-hotel-map__pin').allTextContents(),['1','2','3','4']);
        equal(requests.filter(u=>u.endsWith('/leaflet.js')).length,1);
        equal(requests.filter(u=>u.endsWith('/leaflet.css')).length,1);
        equal(await events(page),[]);
        equal(await page.locator('.leaflet-control-attribution a[href="https://www.openstreetmap.org/copyright"]').count(),1);
        for(let i=0;i<4;i++) {
          const pin=page.locator('.tg-hotel-map__pin').nth(i);
          await pin.focus(); await page.keyboard.press(i%2?'Space':'Enter');
          equal(await pin.getAttribute('aria-pressed'),'true');
          equal(await page.locator('#hotel-map-choices button').nth(i).getAttribute('aria-pressed'),'true');
          const title=await page.locator(listSelector).nth(i).locator('h3').textContent();
          equal(await page.locator('#hotel-map-card-title').textContent(),title);
          equal(await page.evaluate(()=>document.activeElement.id),'hotel-map-card-title');
          const booking=page.locator('#hotel-map-card a.js-aff');
          equal(await booking.evaluate(a=>a.outerHTML),anchors[i],'Map clone preserves every affiliate attribute');
          const summary=page.locator('#hotel-map-card details summary');
          await summary.focus(); await page.keyboard.press(i%2?'Space':'Enter');
          equal(await page.locator('#hotel-map-card details').evaluate(d=>d.open),true);
          equal(await page.locator('#hotel-map-card .tg-hotel-facts').textContent(),await page.locator(listSelector).nth(i).locator('.tg-hotel-facts').textContent());
          for(const selector of ['.tg-hotel-benefit','.tg-hotel-tradeoff']) equal(await page.locator('#hotel-map-card '+selector).textContent(),await page.locator(listSelector).nth(i).locator(selector).textContent());
          equal(await page.locator('#hotel-map-card details > p:not([class])').allTextContents(),await page.locator(listSelector).nth(i).locator('details > p:not([class])').allTextContents());
          await summary.focus(); await page.keyboard.press(i%2?'Space':'Enter');
          equal(await page.locator('#hotel-map-card details').evaluate(d=>d.open),false);
          equal(await events(page),consent==='granted'?anchors.slice(0,i).map(a=>payload(a.match(/href="([^"]+)"/)[1])):[]);
          await booking.click();
          equal(await events(page),consent==='granted'?anchors.slice(0,i+1).map(a=>payload(a.match(/href="([^"]+)"/)[1])):[]);
        }
        for(let i=0;i<4;i++) {
          await page.locator(linkSelector).nth(i).focus(); await page.keyboard.press('Enter');
          equal((await events(page)).length,consent==='granted'?5+i:0);
        }
        if(consent==='granted') {
          await page.evaluate(()=>localStorage.setItem('tg_consent_v2','denied'));
          await page.locator('#hotel-map-card a.js-aff').click(); equal((await events(page)).length,8);
          await page.addScriptTag({content:fs.readFileSync(path.join(root,'assets/js/paris-luxury-hotel-map.js'),'utf8')});
          equal(await page.locator('#hotel-map-choices button').count(),4);
        }
        equal(await page.locator(linkSelector).evaluateAll(a=>a.map(n=>n.outerHTML)),anchors);
        equal(errors,[]); equal(missing,[]);
        report.scenarios.push('consent '+String(consent)+'; four map/list CTAs; keyboard details; exact clones');
      } finally {await context.close();}
    }
    for(const width of [320,390,768,1440]) {
      const {context,page,errors}=await open({width,mobile:width<500});
      try {
        await activate(page);
        for(const size of ['100%','200%']) {
          await page.evaluate(s=>document.documentElement.style.fontSize=s,size);
          equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'No document overflow');
          const targets=await page.locator('.tg-hotel-map__pin, #hotel-map-choices button, '+linkSelector).evaluateAll(a=>a.map(n=>({w:n.getBoundingClientRect().width,h:n.getBoundingClientRect().height})));
          ok(targets.every(n=>n.w>=44&&n.h>=44),'44px targets');
          for(let i=0;i<4;i++) {
            await page.locator('#hotel-map-choices button').nth(i).click();
            equal(await page.locator('#hotel-map-card a.js-aff').isVisible(),true);
            const summary=page.locator('#hotel-map-card details summary');
            await summary.focus(); await page.keyboard.press('Enter');
            equal(await page.locator('#hotel-map-card .tg-hotel-tradeoff').isVisible(),true);
            await page.locator('#hotel-map-card a.js-aff').scrollIntoViewIfNeeded();
            ok(await page.locator('#hotel-map-card a.js-aff').evaluate(a=>{const r=a.getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight;}),'CTA reachable with details open');
          }
        }
        await page.evaluate(()=>document.documentElement.style.fontSize='100%');
        await page.locator('.tg-hotel-table-region').scrollIntoViewIfNeeded();
        equal(await page.locator('.tg-hotel-comparison tbody tr').count(),4);
        const region=page.locator('.tg-hotel-table-region');
        await region.focus(); await page.keyboard.press('ArrowRight');
        if(width<=760) ok(await region.evaluate(n=>n.scrollWidth<=n.clientWidth+1),'Mobile comparison readable without horizontal scrolling');
        else if(width<768) ok(await region.evaluate(n=>n.scrollLeft>0),'Keyboard table scrolling');
        await page.emulateMedia({forcedColors:'active'});
        await page.locator('#hotel-map-choices button').first().focus();
        ok(await page.locator('#hotel-map-choices button').first().evaluate(n=>getComputedStyle(n).outlineStyle!=='none'));
        equal(errors,[]); report.scenarios.push('responsive '+width+'; 200% text; touch targets; table; forced colors');
      }finally{await context.close();}
    }
    for(const failure of ['tiles','library']) {
      const {context,page,errors}=await open({width:390,mobile:true,tiles:failure==='tiles'?'fail':'fake',libraryFail:failure==='library'});
      try {
        await page.locator('#hotel-map').scrollIntoViewIfNeeded();
        await page.waitForFunction(()=>document.getElementById('hotel-map').dataset.tileState==='unavailable');
        await page.locator('#hotel-map-choices button').last().click();
        equal(await page.locator('#hotel-map-card a.js-aff').evaluate(a=>a.outerHTML),anchors[3]);
        await page.locator('#hotel-map-card details summary').click();
        equal(await page.locator('#hotel-map-card .tg-hotel-tradeoff').isVisible(),true);
        await page.locator('#hotel-map-card a.js-aff').click(); equal((await events(page)).length,1);
        equal(errors,[]);
        if(failure==='tiles') await page.locator('#hotel-map').screenshot({path:path.join(out,'mobile-tile-fallback.png')});
        report.scenarios.push(failure+' failure');
      }finally{await context.close();}
    }
    for(const noObserver of [false,true]) {
      const {context,page,requests}=await open({noObserver});
      try {
        equal(requests.filter(u=>u.includes('leaflet-1.9.4')||u.includes('tile.openstreetmap.org')).length,0);
        await page.evaluate(()=>{const top=document.getElementById('hotel-map').getBoundingClientRect().top+scrollY;scrollTo({top:top-innerHeight-200,behavior:'instant'});});
        await page.locator('#hotel-map-canvas[data-map-ready="1"]').waitFor();
        ok(await page.locator('#hotel-map').evaluate(n=>n.getBoundingClientRect().top>innerHeight));
        equal(await events(page),[]); report.scenarios.push('deferred load; IntersectionObserver '+!noObserver);
      }finally{await context.close();}
    }
    const nojs=await open({js:false,width:390});
    try {
      equal(await nojs.page.locator(linkSelector).count(),4);
      await nojs.page.locator('#hotel-options details summary').first().click();
      equal(await nojs.page.locator('#hotel-options details').first().evaluate(n=>n.open),true);
      equal(nojs.requests.filter(u=>u.includes('leaflet-1.9.4')).length,0);
      report.scenarios.push('no JavaScript: native details and four affiliate anchors');
    }finally{await nojs.context.close();}
    for(const p of ['/hotels/paris/','/hotels/paris/cheap-hotels/','/hotels/paris/family-hotels/','/attractions/disneyland-paris-tickets/']) {
      const {context,requests}=await open({path:p});
      try {equal(requests.filter(u=>u.includes('paris-luxury')).length,0);}finally{await context.close();}
    }
    if(process.argv.includes('--screenshots')) {
      for(const [label,width] of [['desktop',1440],['mobile',390]]) {
        const {context,page,errors}=await open({width,mobile:width<500,tiles:'real'});
        try {
          await activate(page);
          await page.waitForFunction(()=>document.getElementById('hotel-map').dataset.tileState==='ready',null,{timeout:20000});
          await page.waitForFunction(()=>[...document.querySelectorAll('.leaflet-tile')].every(n=>n.complete),null,{timeout:20000});
          equal(errors,[]);
          for(const [part,selector] of [['hotel-map','#hotel-map'],['hotel-cards',width<500?'#hotel-options article:first-child':'#hotel-options'],['comparison','.tg-hotel-table-region'],['hero','.tg-hotels-hero']]) {
            const name=label+'-'+part+'.png';
            await page.locator(selector).screenshot({path:path.join(out,name)});report.screenshots.push(name);
          }
        }finally{await context.close();}
      }
    }
    report.passed=true;report.checks=checks;
    fs.writeFileSync(path.join(out,'browser-report.json'),JSON.stringify(report,null,2)+'\n');
    console.log(JSON.stringify(report));
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
