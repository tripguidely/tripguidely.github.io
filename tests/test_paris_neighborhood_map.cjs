// Page-scoped neighborhood-map integration QA. Repeated tests use fake tiles.
// node tests/test_paris_neighborhood_map.cjs PLAYWRIGHT_MODULE CHROME OUTPUT_DIR [--screenshots]
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {execFileSync}=require('node:child_process');
const {chromium}=require(process.argv[2]||'playwright-core');
const root=path.resolve(__dirname,'..'),out=path.resolve(process.argv[4]);
assert(out!==root&&!out.startsWith(root+path.sep));
fs.mkdirSync(out,{recursive:true});
const base='5f3c1d0db4ee88689352607e6adf4bc6b83407a5',origin='https://tripguidely.github.io',route='/hotels/paris/';
const before=execFileSync('git',['show',base+':hotels/paris/index.html'],{cwd:root,encoding:'utf8'});
const originals=before.match(/<a\b[^>]*class="[^"]*js-aff[^>]*>/g);
const data=JSON.parse(fs.readFileSync(path.join(root,'assets/js/paris-neighborhood-map.js'),'utf8').match(/var data = (\[[\s\S]*?\n\]);/)[1]);
const tile=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a5qkAAAAASUVORK5CYII=','base64');
const mime={'.html':'text/html','.css':'text/css','.js':'text/javascript','.webp':'image/webp','.png':'image/png','.svg':'image/svg+xml','.jpg':'image/jpeg'};
const report={passed:false,checks:0,scenarios:[],screenshots:[]};
const same=(a,b,m)=>{assert.deepEqual(a,b,m);report.checks++;},ok=(a,m)=>{assert(a,m);report.checks++;};
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.argv[3]});
 try {
  async function open(opts={}){
   const context=await browser.newContext({viewport:{width:opts.width||1440,height:1000},isMobile:!!opts.mobile,hasTouch:!!opts.mobile,javaScriptEnabled:opts.js!==false,reducedMotion:opts.motion||'reduce',serviceWorkers:'block'});
   const requests=[],errors=[],missing=[];
   await context.route('**/*',async h=>{
    const u=new URL(h.request().url());requests.push(u.href);
    if(u.hostname==='tile.openstreetmap.org'){
     if(opts.tiles==='real')return h.continue();
     if(opts.tiles==='fail')return h.abort();
     return h.fulfill({body:tile,contentType:'image/png'});
    }
    if(u.origin!==origin)return h.abort();
    if(opts.failAsset&&u.pathname.endsWith('/leaflet.'+opts.failAsset))return h.abort();
    let file=path.resolve(root,'.'+decodeURIComponent(u.pathname));
    if(!file.startsWith(root+path.sep))return h.abort();
    if(fs.existsSync(file)&&fs.statSync(file).isDirectory())file=path.join(file,'index.html');
    if(!fs.existsSync(file)){missing.push(u.pathname);return h.fulfill({status:404,body:''});}

    let body=fs.readFileSync(file);
    if(u.pathname.endsWith('/leaflet.js')){
     // QA-only observation: preserve the original map factory and capture its options.
     body=Buffer.concat([body,Buffer.from('\n;(function(){var original=L.map;L.map=function(id,options){window.__mapQaOptions=options;return original.apply(this,arguments);};})();')]);
    }
    return h.fulfill({body,contentType:mime[path.extname(file)]||'application/octet-stream'});

   });
   await context.addInitScript(c=>{
    if(c!==null)localStorage.setItem('tg_consent_v2',c);
    window.calls=[];window.gtag=function(){window.calls.push(Array.from(arguments));};
    document.addEventListener('click',e=>{if(e.target.closest('a.js-aff'))e.preventDefault();},true);
   },opts.consent===undefined?'granted':opts.consent);
   if(opts.noObserver)await context.addInitScript(()=>{delete window.IntersectionObserver;});
   const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
   await page.goto(origin+(opts.path||route),{waitUntil:'networkidle'});
   if(opts.js!==false&&(!opts.path||opts.path===route))await page.waitForFunction(()=>document.getElementById('area-map').dataset.mapBound==='1');
   return {context,page,requests,errors,missing};
  }
  const events=p=>p.evaluate(()=>calls.filter(c=>c[0]==='event'&&c[1]==='affiliate_click').map(c=>c[2]));
  const activate=async p=>{await p.locator('#area-map-canvas').scrollIntoViewIfNeeded();await p.locator('#area-map-canvas[data-map-ready="1"]').waitFor();};
  for(const consent of [null,'denied','granted']){
   const s=await open({consent}),p=s.page;
   try{
    same(await p.locator('#area-map-view').isVisible(),true);
    same(await p.locator('#area-map-choices button').count(),10);
    same(await p.locator('#area-map-profiles button').count(),6);
    same(s.requests.filter(u=>u.includes('leaflet-1.9.4')||u.includes('tile.openstreetmap.org')).length,0,'Map network deferred');
    same(await p.locator('main a.js-aff').evaluateAll(as=>as.map(a=>a.outerHTML.match(/^<a[^>]*>/)[0])),originals,'Original affiliate opening tags exact');
    // Profile selection is available before the street map is ready.
    await p.locator('[data-profile="budget"]').click();
    same(await p.locator('#area-map-choices li:not([hidden]) button').allTextContents(),['3. Latin Quarter','10. Opéra / 9th Arrondissement']);
    same(await p.locator('#area-map-card-title').textContent(),'Latin Quarter');
    await p.locator('[data-profile="all"]').click();
    await activate(p);
    same(await p.locator('.tg-zone-map__pin').count(),10);
    same(await p.locator('.tg-zone-map__pin').allTextContents(),data.map((z,i)=>String(i+1)));
    same(s.requests.filter(u=>u.endsWith('/leaflet.js')).length,1);
    same(s.requests.filter(u=>u.endsWith('/leaflet.css')).length,1);
    same(await p.locator('.leaflet-control-attribution a[href="https://www.openstreetmap.org/copyright"]').count(),1);
    for(let i=0;i<10;i++){
     const pin=p.locator('.tg-zone-map__pin').nth(i);
     await pin.focus();await p.keyboard.press(i%2?'Space':'Enter');
     same(await p.locator('#area-map-card-title').textContent(),data[i].name);
     same(await p.evaluate(()=>document.activeElement.id),'area-map-card-title');
     same(await pin.getAttribute('aria-pressed'),'true');
     same(await p.locator('#area-map-choices button').nth(i).getAttribute('aria-pressed'),'true');
     const original=p.locator('#'+data[i].id).locator('..');
     const facts=await original.locator('li').evaluateAll(lis=>lis.map(li=>li.textContent.slice(li.querySelector('strong').textContent.length).trim()));
     same(await p.locator('#area-map-card dd').allTextContents(),facts);
     same(await p.locator('#area-map-card a').evaluateAll(as=>as.map(a=>a.getAttribute('href'))),await original.locator('a[href^="/"]').evaluateAll(as=>as.map(a=>a.getAttribute('href'))));
     same(await p.locator('#area-map-card a.js-aff').count(),0,'No invented area-specific affiliate CTA');
    }
    for(const profile of ['budget','family','couple','attractions','nightlife','all']){
     await p.locator('[data-profile="'+profile+'"]').click();
     const expected=data.map((z,i)=>({z,i})).filter(({z})=>profile==='all'||z.profiles.includes(profile)).map(({i})=>String(i+1));
     same(await p.locator('.tg-zone-map__pin').allTextContents(),expected);
     same(await p.locator('#area-map-choices li:not([hidden])').count(),expected.length);
     same(await p.locator('#area-map-select option').allTextContents(),expected.map(n=>n+'. '+data[Number(n)-1].name),'Native options preserve original numbering');
     same(await p.locator('#area-map-select').inputValue(),await p.locator('#area-map-choices button[aria-pressed="true"]').evaluate(n=>n.closest('li').dataset.zone));
     ok((await p.locator('#area-map-selection-status').textContent()).includes(expected.length+' suggested areas.'),'Announced result count');
     same(await p.locator('[data-profile="'+profile+'"]').getAttribute('aria-pressed'),'true');
    }
    same(await events(p),[],'Exploring areas never counts as affiliate clicks');
    // Reinitialization is idempotent.
    await p.addScriptTag({content:fs.readFileSync(path.join(root,'assets/js/paris-neighborhood-map.js'),'utf8')});
    same(await p.locator('#area-map-choices button').count(),10);
    same(await p.locator('#area-map-profiles button').count(),6);
    for(let i=0;i<10;i++){
     const a=p.locator('main a.js-aff').nth(i);await a.click();
     const ev=await events(p);same(ev.length,consent==='granted'?i+1:0);
     if(consent==='granted')same(ev[i],{affiliate_program:'klook',page_type:'guide',destination:await a.getAttribute('href'),transport_type:'beacon'});
    }
    if(consent==='granted'){
     await p.addScriptTag({content:fs.readFileSync(path.join(root,'assets/js/site.js'),'utf8')});
     await p.locator('main a.js-aff').first().click();same((await events(p)).length,11,'No duplicate affiliate listener');
     await p.evaluate(()=>localStorage.setItem('tg_consent_v2','denied'));
     await p.locator('main a.js-aff').first().click();same((await events(p)).length,11,'Consent revocation');
    }
    same(s.errors,[]);same(s.missing,[]);
    report.scenarios.push('10 zones, profile filtering and consent '+String(consent));
   }finally{await s.context.close();}
  }
  for(const width of [320,390,430,768,1440]){
   const s=await open({width,mobile:width<500}),p=s.page;
   try{
    await activate(p);
    for(const font of ['100%','200%']){
     await p.evaluate(v=>document.documentElement.style.fontSize=v,font);
     same(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'No document overflow');
     const compact=await p.locator('#area-map-select').isVisible();
     same(await p.locator('#area-map-choices').isVisible(),!compact,'Exactly one visible area chooser');
     const geometry=await p.evaluate(()=>{
      const rect=id=>{const r=document.getElementById(id).getBoundingClientRect();return {top:r.top,bottom:r.bottom,left:r.left,right:r.right};};
      return {profiles:rect('area-map-profiles'),picker:rect('area-map-picker'),card:rect('area-map-card'),map:rect('area-map-view')};
     });
     if(compact){
      ok(geometry.picker.top>=geometry.profiles.bottom,'Mobile choice follows profiles');
      ok(geometry.card.top>=geometry.picker.bottom&&geometry.map.top>=geometry.card.bottom,'Decision before single mobile canvas');
      same(await p.locator('#area-map-select option').count(),10,'All ten native options');
      for(let i=0;i<data.length;i++){
       await p.locator('#area-map-select').selectOption(data[i].id);
       same(await p.locator('#area-map-card-title').textContent(),data[i].name,'Native chooser updates each card');
       same(await p.locator('#area-map-select').inputValue(),data[i].id);
      }
     }else{
      ok(geometry.map.right<=geometry.card.left,'Desktop map left, card right');
      ok(Math.abs(geometry.map.top-geometry.card.top)<0.5,'Aligned desktop columns');
     }
     same(await p.locator('#area-map-select').getAttribute('aria-controls'),'area-map-card');
     same(await p.locator('#area-map-select').getAttribute('aria-describedby'),'area-map-selection-status');
     same(await p.locator('label[for="area-map-select"]').textContent(),'Choose a numbered Paris area');
     same(await p.locator('#area-map-selection-status').getAttribute('role'),'status');
     same(await p.locator('#area-map-selection-status').getAttribute('aria-live'),'polite');
     same(await p.locator('#area-map-selection-status').getAttribute('aria-atomic'),'true');
     same(await p.evaluate(()=>[__mapQaOptions.zoomAnimation,__mapQaOptions.fadeAnimation,__mapQaOptions.markerZoomAnimation]),[false,false,false],'Reduced motion disables all three Leaflet animations');
     for(const profileButton of await p.locator('#area-map-profiles button').all()){
      const controls=(await profileButton.getAttribute('aria-controls')).split(' ');
      for(const id of controls)same(await p.locator('[id="'+id+'"]').count(),1,'ARIA controls resolves');
     }

     const sizes=await p.locator('#area-map button,.tg-zone-map__pin,#area-map-select,.leaflet-control-zoom a,#area-map-card a').evaluateAll(ns=>ns.filter(n=>n.getClientRects().length).map(n=>({w:n.getBoundingClientRect().width,h:n.getBoundingClientRect().height})));
     ok(sizes.every(n=>n.w>=44&&n.h>=44),'44px touch targets');
     if(await p.locator('#area-map-select').isVisible()){
      await p.locator('#area-map-select').focus();await p.keyboard.press('Home');await p.keyboard.press('End');
      same(await p.evaluate(()=>document.activeElement.id),'area-map-select','Native keyboard selection retains focus');
     }else{
      await p.locator('#area-map-choices button').last().focus();await p.keyboard.press('Enter');
     }
     same(await p.locator('#area-map-card-title').textContent(),data[9].name);
     for(const a of await p.locator('#area-map-card a').all()){
      // Chrome rounds scroll offsets to pixels; allow at most half a CSS pixel.
      await a.scrollIntoViewIfNeeded();ok(await a.evaluate(n=>{const r=n.getBoundingClientRect();return r.top>=-0.5&&r.bottom<=innerHeight+0.5;}),'Internal CTA reachable');
     }
    }
    await p.emulateMedia({forcedColors:'active'});
    await p.locator('[data-profile="all"]').focus();
    ok(await p.locator('[data-profile="all"]').evaluate(n=>getComputedStyle(n).outlineStyle!=='none'),'Forced-color focus');

    if(await p.locator('#area-map-select').isVisible()){
     await p.locator('#area-map-select').focus();
     ok(await p.locator('#area-map-select').evaluate(n=>getComputedStyle(n).outlineStyle!=='none'),'Forced-color native chooser focus');
     const cdp=await s.context.newCDPSession(p),ax=await cdp.send('Accessibility.getFullAXTree');
     ok(ax.nodes.some(n=>!n.ignored&&n.role?.value==='combobox'&&n.name?.value==='Choose a numbered Paris area'),'Exposed native chooser accessible name and role');
     ok(ax.nodes.some(n=>!n.ignored&&n.role?.value==='status'&&n.properties?.some(v=>v.name==='live'&&v.value?.value==='polite')),'Live status exposed to accessibility tree');
     await cdp.detach();
    }
    same(s.errors,[]);report.scenarios.push('viewport '+width+' and 200% text');
   }finally{await s.context.close();}
  }
  for(const opts of [{tiles:'fail'},{failAsset:'js'},{failAsset:'css'}])for(const width of [390,1440]){
   const s=await open({...opts,width,mobile:width<500}),p=s.page;
   try{
    await p.locator('#area-map-canvas').scrollIntoViewIfNeeded();
    await p.waitForFunction(()=>document.getElementById('area-map').dataset.tileState==='unavailable');
    await p.locator('[data-profile="family"]').click();
    if(await p.locator('#area-map-select').isVisible())await p.locator('#area-map-select').selectOption(data[4].id);
    else await p.locator('#area-map-choices button').nth(4).click();
    same(await p.locator('#area-map-card-title').textContent(),data[4].name);
    same(await p.locator('#area-map-card a[href="/hotels/paris/family-hotels/"]').count(),1);
    ok(await p.locator('#area-map-status').evaluate(n=>n.getBoundingClientRect().height>20),'Map failure message visibly restored');
    same(await events(p),[]);

    same(await p.locator('#area-map-view').isVisible(),!opts.failAsset,'Tile failure retains map; library failure hides it');
    same(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'No fallback overflow');
    if(opts.failAsset&&width===1440){
     ok(await p.evaluate(()=>Math.abs(document.getElementById('area-map-card').getBoundingClientRect().width-document.querySelector('.tg-zone-map__layout').getBoundingClientRect().width)<0.5),'Desktop library failure restores full-width card');
    }
    same(s.errors,[]);report.scenarios.push('fallback '+width+' '+JSON.stringify(opts));
   }finally{await s.context.close();}
  }

  const normalMotion=await open({motion:'no-preference'});
  try{
   await activate(normalMotion.page);
   same(await normalMotion.page.evaluate(()=>[__mapQaOptions.zoomAnimation,__mapQaOptions.fadeAnimation,__mapQaOptions.markerZoomAnimation]),[true,true,true],'Normal motion options preserved');
   report.scenarios.push('normal motion Leaflet options');
  }finally{await normalMotion.context.close();}
  const legacy=await open({noObserver:true});
  try{
   same(legacy.requests.filter(u=>u.includes('leaflet-1.9.4')).length,0);
   await activate(legacy.page);same(await legacy.page.locator('.tg-zone-map__pin').count(),10);
   report.scenarios.push('deferred scroll fallback without IntersectionObserver');
  }finally{await legacy.context.close();}
  const nojs=await open({js:false,width:390});
  try{
   same(await nojs.page.locator('#area-map-choices a').count(),10);
   same(await nojs.page.locator('#area-map-view').isVisible(),false);
   await nojs.page.locator('#area-map-choices a').last().click();
   same(new URL(nojs.page.url()).hash,'#areas-budget');
   same(nojs.requests.filter(u=>u.includes('leaflet-1.9.4')).length,0);
   same(await nojs.page.locator('main a.js-aff').count(),10);
   report.scenarios.push('no JavaScript native links and original hotel buttons');
  }finally{await nojs.context.close();}
  for(const routePath of ['/hotels/paris/family-hotels/','/hotels/paris/cheap-hotels/','/hotels/paris/luxury-hotels/','/attractions/disneyland-paris-tickets/']){
   const s=await open({path:routePath});
   try{same(s.requests.filter(u=>u.includes('paris-neighborhood-map')).length,0);}finally{await s.context.close();}
  }
  if(process.argv.includes('--screenshots')){
   for(const [label,width] of [['desktop',1440],['mobile',390]]){
    const s=await open({width,mobile:width<500,tiles:'real'}),p=s.page;
    try{
     await activate(p);
     await p.waitForFunction(()=>document.getElementById('area-map').dataset.tileState==='ready'||document.getElementById('area-map').dataset.tileState==='unavailable',{},{timeout:20000});
     const state=await p.locator('#area-map').getAttribute('data-tile-state');
     if(state==='ready')await p.waitForFunction(()=>[...document.querySelectorAll('.leaflet-tile')].every(n=>n.complete));
     const file=label+'-neighborhood-map.png';
     await p.locator('#area-map').screenshot({path:path.join(out,file)});
     report.screenshots.push({file,tiles:state});same(s.errors,[]);
    }finally{await s.context.close();}
   }
  }
  report.passed=true;
 }finally{await browser.close();fs.writeFileSync(path.join(out,'browser-report.json'),JSON.stringify(report,null,2));}
 console.log(JSON.stringify(report));
})().catch(e=>{console.error(e);process.exitCode=1;});
