// Offline Chrome integration tests. No affiliate or analytics requests leave this harness.
// node tests/test_new_york_hotel_maps.cjs PLAYWRIGHT_MODULE CHROME_EXECUTABLE OUTPUT_DIR [--screenshots]
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require(process.argv[2] || 'playwright-core');
const root = path.resolve(__dirname, '..'), out = path.resolve(process.argv[4]);
assert(out !== root && !out.startsWith(root + path.sep), 'Keep QA artifacts outside the worktree');
fs.mkdirSync(out, {recursive:true});
const origin = 'https://tripguidely.github.io';
const registry = JSON.parse(fs.readFileSync(path.join(root,'docs/qa/new-york-hotels-sources.json')));
const mime = {'.html':'text/html','.js':'text/javascript','.css':'text/css','.svg':'image/svg+xml','.png':'image/png','.webp':'image/webp','.avif':'image/avif','.woff2':'font/woff2'};
const tile = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a5qkAAAAASUVORK5CYII=', 'base64');
const report = {passed:false, checks:0, scenarios:[], screenshots:[], localMetrics:[]};
function eq(a,b,message) { assert.deepEqual(a,b,message); report.checks++; }
function ok(value,message) { assert(value,message); report.checks++; }
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.argv[3]});
 try {
  async function open(category,options={}) {
   const context=await browser.newContext({viewport:{width:options.width||1440,height:1000},hasTouch:!!options.mobile,isMobile:!!options.mobile,javaScriptEnabled:options.js!==false,reducedMotion:'reduce',serviceWorkers:'block'});
   const requests=[],external=[],errors=[];
   await context.route('**/*',async route=>{
    const url=new URL(route.request().url());requests.push(url.href);
    if(url.hostname==='tile.openstreetmap.org') {
     if(options.realTiles) return route.continue();
     if(options.tilesFail) return route.abort();
     return route.fulfill({body:tile,contentType:'image/png'});
    }
    if(options.nativeNavigation && registry.hotels.some(h=>h.affiliate_url===url.href))return route.fulfill({body:'<title>Offline partner fixture</title>',contentType:'text/html'});
    if(url.origin!==origin) {external.push(url.href);return route.abort();}
    if(options.libraryFail && url.pathname.endsWith('/leaflet.js'))return route.abort();
    let file=path.resolve(root,'.'+decodeURIComponent(url.pathname));
    if(!file.startsWith(root+path.sep))return route.abort();
    if(fs.existsSync(file)&&fs.statSync(file).isDirectory())file=path.join(file,'index.html');
    if(!fs.existsSync(file))return route.fulfill({status:404,body:''});
    return route.fulfill({body:fs.readFileSync(file),contentType:mime[path.extname(file)]||'application/octet-stream'});
   });
   await context.addInitScript(value=>{
    if(value!==null)localStorage.setItem('tg_consent_v2',value);
    window.trackingCalls=[];window.gtag=function(){trackingCalls.push(Array.from(arguments));};
    document.addEventListener('click',e=>{if(!window.qaAllowNavigation && e.target.closest('a.js-aff'))e.preventDefault();},true);
    window.localMetrics={cls:0,lcp:0};
    new PerformanceObserver(list=>{for(const e of list.getEntries())if(!e.hadRecentInput)localMetrics.cls+=e.value;}).observe({type:'layout-shift',buffered:true});
    new PerformanceObserver(list=>{for(const e of list.getEntries())localMetrics.lcp=e.startTime;}).observe({type:'largest-contentful-paint',buffered:true});
   },options.consent===undefined?'granted':options.consent);
   if(options.noObserver)await context.addInitScript(()=>{delete window.IntersectionObserver;});
   // Wrap Leaflet only to inspect the real instance / marker coordinates, not replace it.
   await context.addInitScript(()=>{
    let lib;Object.defineProperty(window,'L',{configurable:true,get(){return lib;},set(value){lib=value;if(value&&value.map&&!value.map.__observed){const original=value.map;const wrapper=function(...args){window.qaMap=original.apply(this,args);return window.qaMap;};wrapper.__observed=true;value.map=wrapper;}}});
   });
   const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
   await page.goto(origin+'/hotels/new-york/'+category+'-hotels/');
   if(options.js!==false)await page.waitForFunction(()=>document.documentElement.getAttribute('data-affiliateclicks-bound')==='1');
   return {context,page,requests,external,errors};
  }
  async function events(page){return page.evaluate(()=>trackingCalls.filter(c=>c[0]==='event'&&c[1]==='affiliate_click').map(c=>c[2]));}
  async function activate(page,state='ready') {await page.locator('#hotel-map').scrollIntoViewIfNeeded();await page.waitForFunction(s=>document.querySelector('#hotel-map').dataset.mapState===s,state,{timeout:16000});}
  async function noOverflow(page){ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'No body horizontal overflow');}
  for(const category of ['luxury','family','cheap']) {
   const hotels=registry.hotels.filter(h=>h.category===category);
   for(const consent of [null,'denied','granted']) {
    const {context,page,requests,errors,external}=await open(category,{consent});
    try {
     eq(await page.locator('.ny-hotel-card').count(),3);eq(await page.locator('a.js-aff').count(),7);
     eq(requests.filter(x=>x.includes('leaflet-1.9.4')||x.includes('tile.openstreetmap.org')).length,0,'Map assets lazy');
     const before=await page.locator('#hotel-options a.js-aff').evaluateAll(a=>a.map(x=>x.outerHTML));
     await activate(page);eq(await page.locator('.ny-map-pin').count(),3);
     eq(await page.locator('.ny-map-pin').allTextContents(),['1','2','3']);
     eq(requests.filter(x=>x.endsWith('/leaflet.js')).length,1);eq(requests.filter(x=>x.endsWith('/leaflet.css')).length,1);
     eq(await page.evaluate(()=>{const points=[];qaMap.eachLayer(l=>{if(l instanceof L.Marker){const p=l.getLatLng();points.push([p.lat,p.lng]);}});return points;}),hotels.map(h=>[h.lat,h.lon]));
     eq(await events(page),[]);let expectedCount=0;
     for(let i=0;i<3;i++) {
      const pin=page.locator('.ny-map-pin').nth(i);
      if(i===0)await pin.click();else {await pin.focus();await page.keyboard.press(i===1?'Enter':'Space');}
      eq(await page.locator('#hotel-map-card-title').textContent(),hotels[i].name);
      eq(await pin.getAttribute('aria-pressed'),'true');
      eq(await page.locator('.ny-hotel-card.is-selected').getAttribute('data-offer-id'),hotels[i].offer_id);
      eq(await page.locator('#hotel-map-choices button[aria-pressed=true]').count(),1);
      for(const location of ['comparison','hotel_card','map']) {
       const link=page.locator('a[data-cta-id="'+hotels[i].offer_id+'_'+location+'"]');
       eq(await link.evaluate(a=>[a.getAttribute('href'),a.dataset.subid,a.dataset.offerId,a.dataset.ctaLocation,a.rel,a.target]),[hotels[i].affiliate_url,hotels[i].subid,hotels[i].offer_id,location,'nofollow sponsored noopener','_blank']);
       if(location==='hotel_card') {await link.focus();await page.keyboard.press('Enter');}else await link.click();
       if(consent==='granted')expectedCount++;
       const observed=await events(page);eq(observed.length,expectedCount,'Exactly one event per legitimate activation with granted consent');
       if(consent==='granted')eq(observed.at(-1),{affiliate_program:'klook',page_type:'guide',destination:hotels[i].affiliate_url,transport_type:'beacon',page_path:'/hotels/new-york/'+category+'-hotels/',offer_id:hotels[i].offer_id,cta_id:hotels[i].offer_id+'_'+location,cta_location:location});
      }
     }
     eq(await page.locator('#hotel-options a.js-aff').evaluateAll(a=>a.map(x=>x.outerHTML)),before,'Map never edits static URLs/attributes');
     await page.addScriptTag({path:path.join(root,'assets/js/new-york-hotel-map.js')});
     await page.addScriptTag({path:path.join(root,'assets/js/site.js')});
     eq(await page.locator('#hotel-map-choices button').count(),3);eq(await page.locator('.ny-map-pin').count(),3);
     await page.locator('#hotel-map-card a.js-aff').click();if(consent==='granted')expectedCount++;eq((await events(page)).length,expectedCount,'Reinitialization does not duplicate analytics');
     const link=page.locator('#hotel-map-card a.js-aff');
     for(const href of ['', '#hotel-map', '/hotels/new-york/'+category+'-hotels/']) {await link.evaluate((a,href)=>a.setAttribute('href',href),href);await link.click();eq((await events(page)).length,expectedCount,'Cleared / same-page href is never an outbound click');}
     await link.evaluate((a,href)=>a.setAttribute('href',href),hotels[2].affiliate_url);
     await page.evaluate(()=>localStorage.setItem('tg_consent_v2','denied'));await link.click();eq((await events(page)).length,expectedCount);
     await page.evaluate(()=>localStorage.setItem('tg_consent_v2','granted'));await link.click();eq((await events(page)).length,expectedCount+1);
     await page.locator('.ny-show-map').first().click();eq(await page.locator('#hotel-map-card-title').evaluate(el=>document.activeElement===el),true);
     await page.locator('#hotel-map-reset').click();ok(await page.evaluate(()=>{const b=qaMap.getBounds();let all=true;qaMap.eachLayer(l=>{if(l instanceof L.Marker)all=all&&b.contains(l.getLatLng());});return all;}),'Reset shows every marker');
     eq(await page.evaluate(()=>qaMap.scrollWheelZoom.enabled()),false);
     eq(await page.evaluate(()=>{const ids=[...document.querySelectorAll('[id]')].map(e=>e.id);return ids.length-new Set(ids).size;}),0,'No duplicate DOM IDs');
     await noOverflow(page);eq(errors,[]);eq(external.filter(x=>/klook|travelapi/.test(x)),[]);
     report.scenarios.push(category+' consent '+String(consent));
    }finally{await context.close();}
   }
   for(const width of [320,390,640,641,700,768,900,901,1024,1440]) {
    const {context,page,errors}=await open(category,{width,mobile:width<641});
    try {
     await noOverflow(page);await activate(page);await noOverflow(page);
     if(width<641) {
      eq(await page.evaluate(()=>qaMap.dragging.enabled()),false);
      eq(await page.locator('#hotel-map-touch').isVisible(),true);
      eq(await page.locator('#hotel-map-canvas').evaluate(e=>getComputedStyle(e).touchAction),'pan-y');
      await page.locator('#hotel-map-touch').click();eq(await page.evaluate(()=>qaMap.dragging.enabled()),true);
      eq(await page.locator('#hotel-map-canvas').evaluate(e=>getComputedStyle(e).touchAction),'none');
      await page.locator('#hotel-map-canvas').focus();await page.keyboard.press('Escape');eq(await page.evaluate(()=>qaMap.dragging.enabled()),false);
     }else eq(await page.locator('#hotel-map-touch').isVisible(),false);
     for(let i=0;i<3;i++){
      await page.locator('#hotel-map-choices button').nth(i).click();eq(await page.locator('#hotel-map-card-title').textContent(),hotels[i].name);
      const panel=await page.locator('#hotel-map-card').evaluate(el=>{const a=el.querySelector('a.js-aff').getBoundingClientRect(),p=el.getBoundingClientRect(),canvas=document.querySelector('#hotel-map-canvas').getBoundingClientRect();return {ctaInside:a.top>=p.top && a.bottom<=p.bottom,stacked:p.top>=canvas.bottom-1,scrollTop:el.scrollTop,overflow:getComputedStyle(el).overflowY};});
      ok(panel.ctaInside,'Map booking CTA fits inside its panel for every hotel and breakpoint');
      eq(panel.scrollTop,0,'Each hotel selection starts at the heading');
      if(width<=900){ok(panel.stacked,'Tablet map and booking panel are stacked');eq(panel.overflow,'visible');}
      else eq(panel.stacked,false,'Desktop keeps the side-by-side map');
     }
     for(const link of await page.locator('a.js-aff').all()) {
      ok((await link.innerText()).includes('on Klook'),'Visible commercial label identifies the booking partner');
      ok(await link.evaluate(el=>el.getBoundingClientRect().height>=44),'Booking target is at least 44px high');
     }
     ok(await page.locator('.ny-hotel-summary').first().evaluate(el=>parseFloat(getComputedStyle(el).fontSize)>=16),'Hotel summary remains readable');
     ok(await page.locator('.ny-hotel-facts').first().evaluate(el=>parseFloat(getComputedStyle(el).fontSize)>=14),'Factual details remain readable');
     const table=page.locator('.tg-hotel-table-region');
     eq(await table.getAttribute('aria-describedby'),'comparison-help');
     ok(await page.locator('#comparison-help').isVisible(),'Swipe and keyboard guidance is visible');
     ok(/swipe.*left and right arrow keys/.test(await page.locator('#comparison-help').innerText()),'Guidance covers touch and keyboard');
     if(width===390){await table.scrollIntoViewIfNeeded();await table.focus();const before=await table.evaluate(el=>el.scrollLeft);await page.keyboard.press('ArrowRight');await page.waitForTimeout(100);ok(await table.evaluate((el,n)=>el.scrollLeft>n,before),'The table scrolls with a real arrow-key activation');}
     eq(await page.locator('aside.ny-location-aside').count(),0);
     eq(await page.getByRole('navigation',{name:'Plan the wider trip'}).count(),1);
     ok(await page.locator('.ny-art-note').evaluate(el=>parseFloat(getComputedStyle(el).fontSize)>=12),'Illustration caption is at least 12px');
     eq(await events(page),[]);eq(errors,[]);
     if([390,1440].includes(width)) {
      report.localMetrics.push({category,width,...await page.evaluate(()=>localMetrics),...await page.evaluate(()=>({navigationMs:performance.getEntriesByType('navigation')[0].duration,htmlBytes:document.documentElement.outerHTML.length}))});
      if(process.argv.includes('--screenshots')) {
       // Only screenshot mode requests real OSM tiles; all other external requests remain blocked.
       await page.screenshot({path:path.join(out,category+'-'+width+'-map-fixture.png'),fullPage:true});
       await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:path.join(out,category+'-'+width+'-hero.png')});
       report.screenshots.push(category+'-'+width+'-hero.png',category+'-'+width+'-map-fixture.png');
      }
     }
    }finally{await context.close();}
   }
   for(const options of [{js:false},{libraryFail:true},{tilesFail:true},{noObserver:true}]) {
    const {context,page,errors}=await open(category,options);
    try {
     if(options.js===false){eq(await page.locator('#hotel-map-view').isVisible(),false);eq(await page.locator('.ny-show-map:visible').count(),0);eq(await page.locator('#hotel-options a.js-aff').count(),3);}
     else {
      await activate(page,options.libraryFail?'unavailable':options.tilesFail?'tiles-unavailable':'ready');
      eq(await page.locator('#hotel-map-choices button').count(),3);
      await page.locator('#hotel-map-choices button').last().click();eq(await page.locator('#hotel-map-card-title').textContent(),hotels[2].name);
      eq(await page.locator('#hotel-map-card a.js-aff').getAttribute('href'),hotels[2].affiliate_url);
      eq(await events(page),[]);eq(errors,[]);
     }
     report.scenarios.push(category+' fallback '+JSON.stringify(options));
    }finally{await context.close();}
   }
  }

  // Native touch gestures in Chrome emulation: locked map preserves page scroll;
  // explicitly enabling movement pans the map instead of trapping default scrolling.
  {
   const {context,page}=await open('family',{width:390,mobile:true});
   try {
    await activate(page);await page.locator('#hotel-map-canvas').scrollIntoViewIfNeeded();
    const session=await context.newCDPSession(page);
    async function swipe(dx,dy,selector='#hotel-map-canvas'){
     const box=await page.locator(selector).boundingBox(),x=box.x+box.width/2,y=box.y+box.height/2;
     await session.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]});
     for(let step=1;step<=8;step++){await session.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:x+dx*step/8,y:y+dy*step/8}]});await page.waitForTimeout(20);}
     await session.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await page.waitForTimeout(250);
    }
    const beforeScroll=await page.evaluate(()=>scrollY);await swipe(0,-110);
    ok(await page.evaluate(before=>scrollY>before+40,beforeScroll),'Locked map permits a native one-finger page scroll');
    await page.locator('#hotel-map-touch').click();await page.locator('#hotel-map-canvas').scrollIntoViewIfNeeded();
    const before=await page.evaluate(()=>({scroll:scrollY,lng:qaMap.getCenter().lng}));await swipe(100,0);
    ok(await page.evaluate(v=>Math.abs(qaMap.getCenter().lng-v.lng)>.0001,before),'Enabled map pans under a native touch gesture');
    ok(await page.evaluate(v=>Math.abs(scrollY-v.scroll)<5,before),'Enabled horizontal map drag does not scroll the page');
    await page.locator('.tg-hotel-table-region').scrollIntoViewIfNeeded();await page.locator('.tg-hotel-table-region').evaluate(el=>el.scrollLeft=0);
    await swipe(-110,0,'.tg-hotel-table-region');
    ok(await page.locator('.tg-hotel-table-region').evaluate(el=>el.scrollLeft>40),'Comparison supports a native horizontal touch swipe');
    eq(await events(page),[]);report.scenarios.push('Native touch scroll, explicit map panning and horizontal comparison swipe');
   }finally{await context.close();}
  }

  for(const category of ['luxury','family','cheap']){
   const {context,page}=await open(category,{nativeNavigation:true});
   try{
    await page.evaluate(()=>{window.qaAllowNavigation=true;});
    const hotels=registry.hotels.filter(h=>h.category===category);
    for(let i=0;i<3;i++){
     const popupPromise=context.waitForEvent('page');await page.locator('#hotel-options a.js-aff').nth(i).click();
     const popup=await popupPromise;await popup.waitForLoadState('domcontentloaded');
     eq(popup.url(),hotels[i].affiliate_url,'Native popup keeps exact commercial URL');
     eq(await popup.evaluate(()=>!!window.opener),false,'noopener keeps partner window isolated');
     await popup.close();eq((await events(page)).length,i+1,'Native activation emits exactly one event');
    }
    report.scenarios.push(category+' native outbound navigation (offline destination fixtures)');
   }finally{await context.close();}
  }

  // A constrained desktop panel can have an internal scroll position. Replacing
  // its contents must reset that position, including keyboard marker selection.
  for(const category of ['luxury','family','cheap']){
   const {context,page}=await open(category,{width:1024,consent:'granted'});
   try{
    await activate(page);await page.locator('#hotel-map-card').evaluate(el=>el.style.height='180px');
    await page.locator('#hotel-map-card').evaluate(el=>el.scrollTop=100);
    ok(await page.locator('#hotel-map-card').evaluate(el=>el.scrollTop>0),'Regression fixture actually scrolls');
    await page.locator('#hotel-map-choices button').nth(1).click();
    eq(await page.locator('#hotel-map-card').evaluate(el=>el.scrollTop),0,'Choice resets the old scroll offset');
    await page.locator('#hotel-map-card').evaluate(el=>el.scrollTop=100);
    await page.locator('.ny-map-pin').nth(2).focus();await page.keyboard.press('Enter');
    eq(await page.locator('#hotel-map-card').evaluate(el=>el.scrollTop),0,'Keyboard marker selection resets the old scroll offset');
    eq(await events(page),[],'Panel navigation is never an affiliate activation');
    report.scenarios.push(category+' scrolled panel reset');
   }finally{await context.close();}
  }
  // Reflow checks complement normal viewport coverage after increasing text sizes.
  for(const category of ['luxury','family','cheap'])for(const width of [320,641,1024]) {
   const {context,page}=await open(category,{width,consent:'denied'});
   try {
    await page.addStyleTag({content:'html{font-size:200%!important}'});
    await activate(page);await noOverflow(page);
    for(let i=0;i<3;i++) {
     await page.locator('#hotel-map-choices button').nth(i).click();
     const link=page.locator('#hotel-map-card a.js-aff');await link.scrollIntoViewIfNeeded();
     ok(await link.evaluate(el=>{const a=el.getBoundingClientRect(),p=el.parentElement.getBoundingClientRect();return a.left>=p.left-1&&a.right<=p.right+1;}),'Enlarged map CTA stays horizontally within its panel');
    }
    eq(await events(page),[]);report.scenarios.push(category+' 200% text at '+width);
   } finally {await context.close();}
  }
  report.passed=true;
 }catch(error){report.error=error.stack;process.exitCode=1;}finally{await browser.close();fs.writeFileSync(path.join(out,'new-york-browser-report.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));}
})();
