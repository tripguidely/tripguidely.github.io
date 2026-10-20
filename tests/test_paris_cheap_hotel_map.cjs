// Local Chrome integration QA; only screenshot mode permits OSM viewport tiles.
// node tests/test_paris_cheap_hotel_map.cjs PLAYWRIGHT_MODULE CHROME_EXECUTABLE OUTPUT_DIR [--screenshots]
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require(process.argv[2] || 'playwright-core');
const root = path.resolve(__dirname, '..');
const out = path.resolve(process.argv[4]);
assert(!out.startsWith(root + path.sep) && out !== root, 'QA artifacts must stay outside the worktree');
fs.mkdirSync(out, {recursive: true});
const origin = 'https://tripguidely.github.io';
const routePath = '/hotels/paris/cheap-hotels/';
const screenshotMode = process.argv.includes('--screenshots');
const mime = {'.html':'text/html', '.js':'text/javascript', '.css':'text/css', '.webp':'image/webp', '.avif':'image/avif', '.png':'image/png', '.svg':'image/svg+xml', '.woff2':'font/woff2'};
const tile = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a5qkAAAAASUVORK5CYII=', 'base64');
const positions = [[48.847653,2.301453],[48.894501,2.312604],[48.8781526,2.3698083]];
let checks = 0;
const report = {passed:false, checks:0, scenarios:[], screenshots:[]};

(async function () {
  const browser = await chromium.launch({headless:true, executablePath:process.argv[3]});
  try {
    async function open(options = {}) {
      const context = await browser.newContext({viewport:{width:options.width || 1440,height:1000},
        isMobile:!!options.mobile, hasTouch:!!options.mobile, javaScriptEnabled:options.js !== false,
        reducedMotion:'reduce', serviceWorkers:'block'});
      const requests = [], errors = [], external = [];
      await context.route('**/*', async handler => {
        const url = new URL(handler.request().url()); requests.push(url.href);
        if (url.hostname === 'tile.openstreetmap.org') {
          if (options.tiles === 'real') return handler.continue();
          if (options.tiles === 'fail') return handler.abort();
          return handler.fulfill({body:tile,contentType:'image/png'});
        }
        if (url.origin !== origin) { external.push(url.href); return handler.abort(); }
        if (options.libraryFail && url.pathname.endsWith('/leaflet.js')) return handler.abort();
        let file = path.resolve(root, '.' + decodeURIComponent(url.pathname));
        if (!file.startsWith(root + path.sep)) return handler.abort();
        if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file,'index.html');
        if (!fs.existsSync(file)) return handler.fulfill({status:404,body:''});
        return handler.fulfill({body:fs.readFileSync(file),contentType:mime[path.extname(file)] || 'application/octet-stream'});
      });
      await context.addInitScript(consent => {
        if (consent !== null) localStorage.setItem('tg_consent_v2',consent);
        window.trackingCalls = [];
        window.gtag = function () { window.trackingCalls.push(Array.from(arguments)); };
        document.addEventListener('click',event => { if (event.target.closest('a.js-aff')) event.preventDefault(); },true);
      }, options.consent === undefined ? 'granted' : options.consent);
      if(options.noObserver) await context.addInitScript(() => { delete window.IntersectionObserver; });
      const page = await context.newPage(); page.on('pageerror',error => errors.push(error.message));
      page.on('console', message => { if(message.type()==='warning') console.error(message.text()); });
      await page.goto(origin+(options.path || routePath));
      if (options.js !== false) await page.waitForFunction(() => document.documentElement.getAttribute('data-affiliateclicks-bound') === '1');
      return {context,page,requests,errors,external};
    }
    async function events(page) { return page.evaluate(() => trackingCalls.filter(c => c[0]==='event' && c[1]==='affiliate_click').map(c=>c[2])); }
    async function activate(page) {
      await page.locator('#hotel-map').scrollIntoViewIfNeeded();
      try { await page.locator('#hotel-map-canvas[data-map-ready="1"]').waitFor({timeout:15000}); }
      catch (error) {
        console.error(await page.locator('#hotel-map').evaluate(el=>({status:el.querySelector('[role="status"]').textContent, html:el.outerHTML.slice(-1800), L:typeof window.L})));
        throw error;
      }
    }
    for (const consent of [null,'denied','granted']) {
      const {context,page,requests,errors} = await open({consent});
      try {
        const originals = await page.locator('#hotel-options a.js-aff').evaluateAll(links=>links.map(a=>a.outerHTML));
        assert.equal(await page.locator('#hotel-options > .tg-hotel-grid > article').count(),3); checks++;
        assert.equal(await page.locator('#hotel-map-view').isVisible(),true); checks++;
        assert.equal(await page.locator('#hotel-map-choices button').count(),3); checks++;
        assert.equal(await page.locator('#hotel-map-toggle').count(),0); checks++;
        assert.equal(await page.locator('#hotel-options').evaluate(el=>el.innerText.includes('Opens in a new tab')),false); checks++;
        assert.equal(await page.locator('#hotel-options a[href^="https://www."]').count(),0); checks++;
        assert.equal(requests.filter(url=>url.includes('/leaflet-1.9.4/') || url.includes('tile.openstreetmap.org')).length,0); checks++;
        await activate(page);
        assert.equal(await page.locator('.tg-hotel-map__pin').count(),3); checks++;
        assert.deepEqual(await page.locator('.tg-hotel-map__pin').allTextContents(),['1','2','3']); checks++;
        assert.equal(requests.filter(url=>url.endsWith('/leaflet.js')).length,1); checks++;
        assert.equal(requests.filter(url=>url.endsWith('/leaflet.css')).length,1); checks++;
        assert.deepEqual(await events(page),[], 'Opening the map must not count as an affiliate click'); checks++;
        assert.equal(await page.locator('.leaflet-control-attribution a[href="https://www.openstreetmap.org/copyright"]').count(),1); checks++;
        for (let i=0;i<3;i++) {
          const pin = page.locator('.tg-hotel-map__pin').nth(i);
          if (i===1) { await pin.focus(); await page.keyboard.press('Enter'); }
          else if (i===2) { await pin.focus(); await page.keyboard.press('Space'); }
          else await pin.click();
          const expected = await page.locator('#hotel-options a.js-aff').nth(i).evaluate(a=>({id:a.dataset.hotelId,subid:a.dataset.subid,href:a.getAttribute('href'),name:a.closest('article').querySelector('h3').textContent}));
          assert.equal(await page.locator('#hotel-map-card-title').textContent(),expected.name); checks++;
          assert.equal(await pin.getAttribute('aria-pressed'),'true'); checks++;
          const booking=page.locator('#hotel-map-card a.js-aff');
          assert.match(await booking.getAttribute('aria-label'), /opens in a new tab/i); checks++;
          assert.equal(await page.locator('#hotel-map-card').evaluate(el=>el.innerText.includes('Opens in a new tab')),false); checks++;
          assert.deepEqual(await booking.evaluate(a=>({id:a.dataset.hotelId,subid:a.dataset.subid,href:a.getAttribute('href'),placement:a.dataset.placement,variant:a.dataset.experimentVariant,rel:a.getAttribute('rel'),target:a.getAttribute('target')})),
            {id:expected.id,subid:expected.subid,href:expected.href,placement:'map',variant:'with_map',rel:'nofollow sponsored noopener',target:'_blank'}); checks++;
          const summary=page.locator('#hotel-map-card details summary');
          assert.equal(await page.locator('#hotel-map-card > a.tg-hotel-map__details').count(),0);checks++;
          assert.equal(await page.locator('#hotel-map-card .tg-hotel-map__note').count(),0);checks++;
          const beforeUrl=page.url(), beforeEvents=(await events(page)).length;
          await summary.focus();
          await page.keyboard.press(i%2 ? 'Space' : 'Enter');
          assert.equal(await page.locator('#hotel-map-card details').evaluate(d=>d.open),true);checks++;
          assert.equal(page.url(),beforeUrl);checks++;
          assert.equal((await events(page)).length,beforeEvents);checks++;
          const originalDetails=await page.locator('#hotel-options article').nth(i).evaluate(a=>[...a.children].filter(n=>n.tagName==='P' && !n.matches('.tg-hotel-area, .tg-hotel-use')).map(n=>n.textContent.trim()));
          assert.deepEqual(await page.locator('#hotel-map-card details > p').allTextContents(),originalDetails);checks++;
          const facts=locator=>locator.evaluate(el=>Object.fromEntries([...el.querySelectorAll('[data-fact]')].map(n=>[n.dataset.fact,n.textContent.trim()])));
          assert.deepEqual(await facts(page.locator('#hotel-map-card')),await facts(page.locator('#hotel-options article').nth(i)));checks++;
          assert.equal(await page.locator('#hotel-map-card > .tg-hotel-facts > div').count(),2);checks++;
          assert.equal(await page.locator('#hotel-map-card details [data-fact="budget"]').isVisible(),true);checks++;
          assert.equal(await page.locator('#hotel-map > .tg-hotel-map__note').isVisible(),true);checks++;
          await booking.click();
          const observed = await events(page);
          assert.equal(observed.length,consent==='granted'?i+1:0); checks++;
          if(consent==='granted') {
            assert.deepEqual(observed[i],{affiliate_program:'klook',page_type:'guide',destination:expected.href,transport_type:'beacon',hotel_id:expected.id,placement:'map',experiment_variant:'with_map',page_path:routePath}); checks++;
          }
        }
        assert.deepEqual(await page.locator('#hotel-options a.js-aff').evaluateAll(links=>links.map(a=>a.outerHTML)), originals); checks++;
        if(consent==='granted') {
          for (let i=0;i<3;i++) {
            const original=page.locator('#hotel-options a.js-aff').nth(i);
            await original.focus(); await page.keyboard.press('Enter');
            const observed=(await events(page))[3+i];
            const expected=await original.evaluate(a=>({id:a.dataset.hotelId,href:a.getAttribute('href')}));
            assert.deepEqual(observed,{affiliate_program:'klook',page_type:'guide',destination:expected.href,transport_type:'beacon',hotel_id:expected.id,placement:'list',experiment_variant:'baseline',page_path:routePath});checks++;
          }
          // Reinitializing the existing shared script must not double-bind clicks.
          await page.addScriptTag({content:fs.readFileSync(path.join(root,'assets/js/site.js'),'utf8')});
          await page.locator('#hotel-options a.js-aff').first().click();
          assert.equal((await events(page)).length,7);checks++;
          await page.evaluate(()=>localStorage.setItem('tg_consent_v2','denied'));
          await page.locator('#hotel-map-card a.js-aff').click();
          assert.equal((await events(page)).length,7); checks++;
        }
        if(consent!=='granted') {
          await page.evaluate(()=>localStorage.setItem('tg_consent_v2','granted'));
          await page.locator('#hotel-map-card a.js-aff').click();
          assert.equal((await events(page)).length,1);checks++;
        }
        await page.locator('#hotel-map-choices button').last().focus();
        await page.keyboard.press('Escape');
        assert.equal(await page.locator('#hotel-map-view').isVisible(),true); checks++;
        assert.equal(await page.locator('#hotel-map-toggle').count(),0); checks++;
        await activate(page);
        assert.equal(requests.filter(url=>url.endsWith('/leaflet.js')).length,1); checks++;
        assert.equal(await page.locator('.tg-hotel-map__pin').count(),3); checks++;
        assert.deepEqual(errors,[]); checks++;
        report.scenarios.push('consent '+String(consent));
      } finally {await context.close();}
    }
    for(const width of [320,390,768,1440]) {
      const {context,page,errors}=await open({width,mobile:width<500});
      try {
        await activate(page);
        assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true); checks++;
        const targets=await page.locator('.tg-hotel-map__pin, #hotel-map-choices button').evaluateAll(nodes=>nodes.map(n=>({w:n.getBoundingClientRect().width,h:n.getBoundingClientRect().height})));
        assert(targets.every(r=>r.w>=44 && r.h>=44)); checks++;
        await page.locator('#hotel-map-choices button').nth(2).click();
        assert.equal(await page.locator('#hotel-map-card a.js-aff').isVisible(),true); checks++;
        const summary=page.locator('#hotel-map-card details summary');
        await summary.click();
        assert.equal(await page.locator('#hotel-map-card details').evaluate(d=>d.open),true);checks++;
        assert.equal(await page.locator('#hotel-map-card .tg-hotel-tradeoff').isVisible(),true);checks++;
        const cta=await page.locator('#hotel-map-card a.js-aff').evaluate(a=>({top:a.getBoundingClientRect().top,bottom:a.getBoundingClientRect().bottom,height:innerHeight}));
        assert(cta.top>=0 && cta.bottom<=cta.height,'Klook CTA must remain in the viewport with full details open');checks++;
        const cards=await page.locator('#hotel-options article').evaluateAll(nodes=>nodes.map(a=>({factsBeforeDescription:[...a.children].findIndex(n=>n.matches('.tg-hotel-facts'))<[...a.children].findIndex(n=>n.tagName==='P' && !n.className),tradeoff:!!a.querySelector('.tg-hotel-tradeoff'),facts:a.querySelectorAll('.tg-hotel-facts > div').length})));
        assert(cards.every(c=>c.factsBeforeDescription && c.tradeoff && c.facts===5));checks++;
        const region=page.locator('#comparison .tg-hotel-table-region');
        await region.focus();
        if(width<=760) {
          assert(await region.evaluate(el=>el.scrollWidth<=el.clientWidth+1),'Mobile comparison requires no horizontal scroll');checks++;
          assert.equal(await page.locator('#comparison tbody th[scope="row"]').count(),3);checks++;
          assert.equal(await page.locator('#comparison tbody td[data-label]').count(),12);checks++;
        } else if(width<1000) {
          await page.keyboard.press('End');
          await region.evaluate(el=>el.scrollLeft=el.scrollWidth);
          assert(await region.evaluate(el=>el.scrollLeft>0));checks++;
          assert.equal(await page.locator('#comparison tbody th[scope="row"]').count(),3);checks++;
          await region.evaluate(el=>el.scrollLeft=0);
          await page.keyboard.press('ArrowRight');
          await page.waitForTimeout(150);
          assert(await region.evaluate(el=>el.scrollLeft>0));checks++;
        }
        assert.equal(await page.locator('#hotel-options article .tg-hotel-facts dt').allTextContents().then(xs=>xs.filter(x=>x==='Budget checks').length),3);checks++;
        await page.evaluate(()=>document.documentElement.style.fontSize='200%');
        assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true); checks++;
        assert.deepEqual(errors,[]); checks++;
        report.scenarios.push('responsive '+width);
      }finally{await context.close();}
    }
    for(const failure of ['tiles','library']) {
      const {context,page,errors}=await open({width:390,mobile:true,tiles:failure==='tiles'?'fail':'fake',libraryFail:failure==='library'});
      try {
        await page.locator('#hotel-map').scrollIntoViewIfNeeded();
        await page.waitForFunction(()=>document.getElementById('hotel-map').dataset.tileState==='unavailable');
        await page.locator('#hotel-map-choices button').nth(2).click();
        await page.locator('#hotel-map-card a.js-aff').click();
        assert.equal((await events(page)).length,1); checks++;
        assert.equal((await events(page))[0].placement,'map'); checks++;
        assert.equal(await page.locator('#hotel-options a.js-aff').count(),3); checks++;
        assert.deepEqual(errors,[]); checks++;
        if(failure==='tiles') await page.locator('#hotel-map').screenshot({path:path.join(out,'mobile-tile-fallback.png')});
        report.scenarios.push('failure '+failure);
      }finally{await context.close();}
    }

    for(const noObserver of [false,true]) {
    const deferred=await open({noObserver});
    try {
      assert.equal(deferred.requests.filter(url=>url.includes('/leaflet-1.9.4/') || url.includes('tile.openstreetmap.org')).length,0);checks++;
      // The section is still below the screen, but within the 250px loading margin.
      await deferred.page.evaluate(()=>{
        const top=document.getElementById('hotel-map').getBoundingClientRect().top+scrollY;
        window.scrollTo({top:top-innerHeight-200,behavior:'instant'});
      });
      await deferred.page.locator('#hotel-map-canvas[data-map-ready="1"]').waitFor();
      const near=await deferred.page.locator('#hotel-map').evaluate(el=>({top:el.getBoundingClientRect().top,h:innerHeight}));
      assert(near.top>near.h && near.top<near.h+250);checks++;
      assert.equal(deferred.requests.filter(url=>url.endsWith('/leaflet.js')).length,1);checks++;
      assert.deepEqual(await events(deferred.page),[]);checks++;
      report.scenarios.push(noObserver ? 'viewport loading without IntersectionObserver' : 'automatic loading before viewport entry');
    }finally{await deferred.context.close();}
    }
    const nojs=await open({js:false,width:390});
    try{
      assert.equal(await nojs.page.locator('#hotel-map-toggle').count(),0);checks++;
      assert.equal(await nojs.page.locator('#hotel-options a.js-aff').count(),3);checks++;
      assert.equal(nojs.requests.filter(url=>url.includes('/leaflet-1.9.4/') || url.includes('tile.openstreetmap.org')).length,0);checks++;
    }finally{await nojs.context.close();}
    const other=await open({path:'/hotels/paris/'});
    try{assert.equal(other.requests.filter(url=>url.includes('paris-cheap-hotel-map') || url.includes('leaflet-1.9.4')).length,0);checks++;}finally{await other.context.close();}
    if(screenshotMode) {
      for(const [label,width] of [['desktop',1440],['mobile',390]]) {
        const {context,page,errors}=await open({width,mobile:width<500,tiles:'real'});
        try {
          await activate(page);
          await page.waitForFunction(()=>document.getElementById('hotel-map').dataset.tileState==='ready',{},{timeout:20000});
          await page.waitForFunction(()=>[...document.querySelectorAll('.leaflet-tile')].every(img=>img.complete),{},{timeout:20000});
          assert.deepEqual(errors,[]); checks++;
          await page.locator('#hotel-map-card details summary').click();
          const name=label+'-hotel-map.png'; await page.locator('#hotel-map').screenshot({path:path.join(out,name)});
          const cardsName=label+'-hotel-cards.png';
          await (width<500 ? page.locator('#hotel-options article').first() : page.locator('#hotel-options')).screenshot({path:path.join(out,cardsName)});
          const compareName=label+'-comparison.png';
          await page.locator('#comparison').screenshot({path:path.join(out,compareName)});
          report.screenshots.push(compareName);
          report.screenshots.push(cardsName);
          report.screenshots.push(name);
        }finally{await context.close();}
      }
    }
    // Fixed point data is explicit and must not change unnoticed.
    const script=fs.readFileSync(path.join(root,'assets/js/paris-cheap-hotel-map.js'),'utf8');
    positions.forEach(pair=>{assert(script.includes(pair[0]+', '+pair[1]));checks++;});
    report.passed=true;report.checks=checks;
    fs.writeFileSync(path.join(out,'map-browser-report.json'),JSON.stringify(report,null,2)+'\n');
    console.log(JSON.stringify(report));
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
