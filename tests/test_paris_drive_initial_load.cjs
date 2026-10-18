// Deterministic offline regression: original HTML + a minimal Drive-lock test double
// must reproduce the empty clone; corrected actual HTML must never request Drive.
// No vendor JavaScript is copied, no affiliate/Google request leaves the harness.
// node tests/test_paris_drive_initial_load.cjs PLAYWRIGHT_MODULE CHROME OUTPUT_DIR
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {execFileSync}=require('node:child_process');
const {chromium}=require(process.argv[2]||'playwright-core');
const root=path.resolve(__dirname,'..'),out=path.resolve(process.argv[4]);
assert(out!==root&&!out.startsWith(root+path.sep));fs.mkdirSync(out,{recursive:true});
const base='ee86ecbd38f68bad7e5647d1451c2ca497a9d3b7';
const origin='https://tripguidely.github.io',drive='https://tp-em.com/NDkyNzI0.js?t=492724';
const mime={'.html':'text/html','.js':'application/javascript','.css':'text/css','.svg':'image/svg+xml','.png':'image/png','.webp':'image/webp','.avif':'image/avif','.woff2':'font/woff2'};
const tile=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a5qkAAAAASUVORK5CYII=','base64');
const report={passed:false,checks:0,scenarios:[],screenshots:[],metrics:[],networkSentToAffiliateOrGoogle:0};
function eq(actual,expected,label){assert.deepEqual(actual,expected,label);report.checks++;}
function ok(value,label){assert(value,label);report.checks++;}
// This models only the independently observed lock/restore mechanism, not Drive's
// account settings or its full runtime. The five-second fallback is retained.
const lockFixture='(function(){function start(){if(document.readyState==="loading"){setTimeout(start,0);return;}var saved=[];function lock(a){if(a instanceof HTMLAnchorElement&&/^https:\\/\\/klook\\.tpk\\.ro\\//.test(a.getAttribute("href")||"")){saved.push([a,a.getAttribute("href")]);a.setAttribute("href","");}}document.querySelectorAll("a").forEach(lock);var observer=new MutationObserver(function(rs){rs.forEach(function(r){r.addedNodes.forEach(function(n){if(n instanceof Element){lock(n);n.querySelectorAll("a").forEach(lock);}});});});observer.observe(document,{subtree:true,childList:true});setTimeout(function(){observer.disconnect();saved.forEach(function(pair){pair[0].setAttribute("href",pair[1]);});window.qaLockRestored=true;},5000);window.qaLockStarted=true;window.qaDriveLocked();}start();})();';
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.argv[3]});
 try{
  async function open(category,options={}){
   const pagePath='hotels/paris/'+category+'-hotels/index.html';
   const html=options.baseline?execFileSync('git',['show',base+':'+pagePath],{cwd:root}):fs.readFileSync(path.join(root,pagePath));
   const context=await browser.newContext({viewport:{width:options.mobile?390:1440,height:1000},isMobile:!!options.mobile,hasTouch:!!options.mobile,javaScriptEnabled:options.js!==false,reducedMotion:'reduce',serviceWorkers:'block'});
   const requests=[],errors=[];let release;const locked=new Promise(resolve=>{release=resolve;});
   await context.exposeBinding('qaDriveLocked',()=>release());
   await context.route('**/*',async handler=>{
    const req=handler.request(),url=new URL(req.url());requests.push(url.href);
    if(url.href===drive)return handler.fulfill({contentType:'application/javascript',body:lockFixture});
    if(url.hostname==='tile.openstreetmap.org')return handler.fulfill({body:tile,contentType:'image/png'});
    if(url.hostname==='klook.tpk.ro'&&req.isNavigationRequest())return handler.fulfill({body:'<title>Offline partner destination</title><p>Navigation fixture</p>',contentType:'text/html'});
    if(url.origin!==origin)return handler.abort();
    let p=path.resolve(root,'.'+decodeURIComponent(url.pathname));if(!p.startsWith(root+path.sep))return handler.abort();
    if(fs.existsSync(p)&&fs.statSync(p).isDirectory())p=path.join(p,'index.html');
    if(!fs.existsSync(p))return handler.fulfill({status:404,body:''});
    if(options.baseline&&p.endsWith('paris-'+category+'-hotel-map.js'))await locked;
    if(options.slow&&(/paris-.*-hotel-map\.js$/.test(p)||url.pathname.startsWith('/partials/')))await new Promise(r=>setTimeout(r,350));
    return handler.fulfill({body:p===path.join(root,pagePath)?html:fs.readFileSync(p),contentType:mime[path.extname(p)]||'application/octet-stream'});
   });
   await context.addInitScript(consent=>{
    if(consent!==null)localStorage.setItem('tg_consent_v2',consent);
    window.qaCalls=[];window.gtag=function(){qaCalls.push(Array.from(arguments));};
    window.qaPreventNavigation=false;window.qaBadHrefs=[];window.qaAddedLinks=[];
    document.addEventListener('click',e=>{if(window.qaPreventNavigation&&e.target.closest('a.js-aff'))e.preventDefault();},true);
    function check(a,reason,old){if(!a.matches('a.js-aff'))return;var href=a.getAttribute('href');if(!href||new URL(href,location.href).origin===location.origin||old==='')qaBadHrefs.push({time:performance.now(),reason,href,old,subid:a.dataset.subid,map:!!a.closest('#hotel-map-card')});}
    new MutationObserver(rs=>{for(var r of rs){if(r.type==='attributes'&&r.target instanceof HTMLAnchorElement)check(r.target,'attribute',r.oldValue);if(r.type==='childList')for(var n of r.addedNodes)if(n instanceof Element){if(n.matches('a.js-aff')){check(n,'added');qaAddedLinks.push(n.getAttribute('href'));}for(var a of n.querySelectorAll('a.js-aff')){check(a,'added-subtree');qaAddedLinks.push(a.getAttribute('href'));}}}}).observe(document,{subtree:true,childList:true,attributes:true,attributeFilter:['href'],attributeOldValue:true});
    window.qaVitals={cls:0,lcp:0};
    new PerformanceObserver(es=>{for(var e of es.getEntries())if(!e.hadRecentInput)qaVitals.cls+=e.value;}).observe({type:'layout-shift',buffered:true});
    new PerformanceObserver(es=>{for(var e of es.getEntries())qaVitals.lcp=e.startTime;}).observe({type:'largest-contentful-paint',buffered:true});
   },options.consent===undefined?'granted':options.consent);
   const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
   await page.goto(origin+'/hotels/paris/'+category+'-hotels/'+(options.direct?'#hotel-map':''),{waitUntil:'domcontentloaded',timeout:15000});
   return {context,page,requests,errors,category,options};
  }
  async function affiliateEvents(page){return page.evaluate(()=>qaCalls.filter(c=>c[0]==='event'&&c[1]==='affiliate_click').map(c=>c[2]));}
  async function assertClean(state){
   eq(state.requests.filter(u=>u.startsWith('https://tp-em.com/')),[],'No Drive script/config/collect requests');
   eq(await state.page.evaluate(()=>qaBadHrefs),[],'No transient empty/same-page affiliate href from document start');
   eq(await state.page.locator('a.js-aff[href=""],a.js-aff:not([href])').count(),0,'All current booking anchors usable');
   eq(state.errors,[],'No page JavaScript error');
  }
  // The original source must fail the same invariant, even after its fallback restores originals.
  for(const category of ['family','cheap','luxury']){
   const s=await open(category,{baseline:true});
   try{
    const map=s.page.locator('#hotel-map-card a.js-aff');await map.waitFor({state:'attached'});
    eq(await map.getAttribute('href'),'','Negative control: clone captures locked href');
    await s.page.waitForFunction(()=>window.qaLockRestored===true,{},{timeout:8000});
    eq(await map.getAttribute('href'),'','Negative control: clone still empty after five-second restore');
    ok(await s.page.locator('#hotel-options a.js-aff').evaluateAll(as=>as.length>0&&as.every(a=>a.getAttribute('href').startsWith('https://klook.tpk.ro/'))),'Original list links restored');
    eq(s.requests.filter(u=>u===drive).length,1,'Negative fixture actually executed from original inclusion');
    report.scenarios.push({category,mode:'negative-base',persistentEmptyMap:true});
   }finally{await s.context.close();}
  }
  for(const category of ['family','cheap','luxury'])for(const mobile of [false,true]){
   const s=await open(category,{mobile,direct:true,slow:mobile});
   try{
    const p=s.page,map=p.locator('#hotel-map-card a.js-aff');await map.waitFor({state:'attached'});
    const originals=await p.locator('a.js-aff').evaluateAll(as=>as.filter(a=>!a.closest('#hotel-map-card')).map(a=>({href:a.getAttribute('href'),subid:a.dataset.subid,rel:a.rel,target:a.target})));
    eq(originals.length,category==='cheap'?3:4,'Expected exact property count including the separate Luxury alternative');
    eq(await p.locator('#hotel-map-choices button').count(),originals.length,'Every map choice has an original booking anchor');
    eq(await map.getAttribute('href'),originals[0].href,'Initial clone ready without waiting for Drive');
    // The FIRST booking activation is native, before selection/reinitialization.
    const popupPromise=p.waitForEvent('popup');
    if(mobile)await map.tap();else {await map.focus();await p.keyboard.press('Enter');}
    const popup=await popupPromise;await popup.waitForLoadState('domcontentloaded');
    eq(popup.url(),originals[0].href,'Native first CTA reaches exact original short URL');
    eq(await popup.evaluate(()=>window.opener),null,'noopener retained');await popup.close();
    eq((await affiliateEvents(p)).length,1,'Exactly one event on first native activation');
    await p.evaluate(()=>{qaPreventNavigation=true;});
    for(let i=0;i<originals.length;i++){
     const choice=p.locator('#hotel-map-choices button').nth(i);await choice.focus();await p.keyboard.press(i%2?'Space':'Enter');
     eq(await map.evaluate(a=>({href:a.getAttribute('href'),subid:a.dataset.subid,rel:a.rel,target:a.target})),originals[i],'Selected clone retains full commercial identity');
     if(i){await map.focus();await p.keyboard.press('Enter');}
     eq((await affiliateEvents(p)).length,i+1,'One affiliate event per activation; none from selection');
    }
    await p.addScriptTag({content:fs.readFileSync(path.join(root,'assets/js/site.js'),'utf8')});
    await p.addScriptTag({content:fs.readFileSync(path.join(root,'assets/js/paris-'+category+'-hotel-map.js'),'utf8')});
    await map.click();eq((await affiliateEvents(p)).length,originals.length+1,'Reinitialization does not duplicate tracking');
    await p.evaluate(()=>localStorage.setItem('tg_consent_v2','denied'));await map.click();eq((await affiliateEvents(p)).length,originals.length+1,'Revoked consent suppresses events');
    await p.waitForTimeout(5200);await assertClean(s);
    report.metrics.push({category,mobile,...await p.evaluate(()=>qaVitals)});
    await p.locator('#hotel-map').screenshot({path:path.join(out,category+'-'+(mobile?'mobile':'desktop')+'-map.png')});report.screenshots.push(category+'-'+(mobile?'mobile':'desktop')+'-map.png');
    await p.reload({waitUntil:'domcontentloaded'});await p.locator('#hotel-map-card a.js-aff').waitFor({state:'attached'});await assertClean(s);
    eq(await p.locator('#hotel-map-card a.js-aff').getAttribute('href'),originals[0].href,'Reload starts with a working first map link');
    report.scenarios.push({category,mobile,mode:'corrected-native',hotels:originals.length,reloaded:true});
   }finally{await s.context.close();}
  }
  for(const category of ['family','cheap','luxury'])for(const consent of [null,'denied']){
   const s=await open(category,{consent,mobile:true});
   try{
    await s.page.evaluate(()=>{qaPreventNavigation=true;});
    await s.page.locator('#hotel-map-card a.js-aff').click();
    eq(await s.page.evaluate(()=>qaCalls.filter(c=>c[0]==='event')),[],'No custom events without granted consent');
    await assertClean(s);report.scenarios.push({category,mode:'consent',consent});
   }finally{await s.context.close();}
  }
  for(const category of ['family','cheap','luxury']){
   const s=await open(category,{js:false,mobile:true});
   try{
    const links=s.page.locator('a.js-aff');eq(await links.count(),category==='cheap'?3:4,'Static no-JS booking fallback preserved');
    ok(await links.evaluateAll(as=>as.every(a=>a.href.startsWith('https://klook.tpk.ro/'))),'No-JS destinations intact');
    eq(s.requests.filter(u=>u.startsWith('https://tp-em.com/')),[]);report.scenarios.push({category,mode:'no-js'});
   }finally{await s.context.close();}
  }
  report.passed=true;
 }finally{await browser.close();fs.writeFileSync(path.join(out,'initial-load-report.json'),JSON.stringify(report,null,2));}
 console.log(JSON.stringify(report));
})().catch(error=>{fs.writeFileSync(path.join(out,'failure.txt'),error.stack||String(error));console.error(error);process.exitCode=1;});
