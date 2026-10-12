// Audit every outbound anchor in the live DOM, including all selected map cards.
// node tests/test_paris_hotel_official_links.cjs PLAYWRIGHT_MODULE CHROME OUTPUT_DIR
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {execFileSync} = require('node:child_process');
const {chromium} = require(process.argv[2] || 'playwright-core');
const root = path.resolve(__dirname, '..');
const out = path.resolve(process.argv[4]);
assert(out !== root && !out.startsWith(root + path.sep));
fs.mkdirSync(out, {recursive:true});
const base = '13b6ddac77e910bf96279c67e70a4359479ddb86';
const origin = 'https://tripguidely.github.io';
const mime = {'.html':'text/html','.css':'text/css','.js':'text/javascript','.webp':'image/webp','.avif':'image/avif','.png':'image/png','.svg':'image/svg+xml'};
const tile = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a5qkAAAAASUVORK5CYII=', 'base64');
const attribution = ['https://leafletjs.com/', 'https://www.openstreetmap.org/copyright'];
let checks = 0;
const report = {passed:false,checks:0,pages:[],screenshots:[]};
function equal(a,b,message) {assert.deepEqual(a,b,message);checks++;}
(async()=>{
  const browser=await chromium.launch({headless:true,executablePath:process.argv[3]});
  try {
    for(const name of ['family','cheap','luxury']) {
      const routePath='/hotels/paris/'+name+'-hotels/';
      const file='hotels/paris/'+name+'-hotels/index.html';
      const baseline=execFileSync('git',['show',base+':'+file],{cwd:root,encoding:'utf8'});
      const opening=baseline.match(/<a\b[^>]*class="[^"]*\bjs-aff\b[^>]*>/g);
      equal(opening.length,name==='cheap'?3:4);
      async function open(consent,js=true) {
        const context=await browser.newContext({viewport:{width:390,height:1000},isMobile:true,hasTouch:true,javaScriptEnabled:js,reducedMotion:'reduce',serviceWorkers:'block'});
        const requests=[],errors=[],missing=[];
        await context.route('**/*',async handler=>{
          const url=new URL(handler.request().url());requests.push(url.href);
          if(url.hostname==='tile.openstreetmap.org')return handler.fulfill({body:tile,contentType:'image/png'});
          if(url.origin!==origin)return handler.abort();
          let target=path.resolve(root,'.'+decodeURIComponent(url.pathname));
          if(!target.startsWith(root+path.sep))return handler.abort();
          if(fs.existsSync(target)&&fs.statSync(target).isDirectory())target=path.join(target,'index.html');
          if(!fs.existsSync(target)){missing.push(url.pathname);return handler.fulfill({status:404,body:''});}
          return handler.fulfill({body:fs.readFileSync(target),contentType:mime[path.extname(target)]||'application/octet-stream'});
        });
        await context.addInitScript(value=>{
          if(value!==null)localStorage.setItem('tg_consent_v2',value);
          window.trackingCalls=[];window.gtag=function(){trackingCalls.push(Array.from(arguments));};
          document.addEventListener('click',e=>{if(e.target.closest('a.js-aff'))e.preventDefault();},true);
        },consent);
        const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
        await page.goto(origin+routePath);
        if(js) {
          await page.waitForFunction(()=>document.documentElement.dataset.affiliateclicksBound==='1');
          await page.waitForFunction(()=>document.getElementById('site-header').childElementCount>0&&document.getElementById('site-footer').childElementCount>0);
        }
        return {context,page,requests,errors,missing};
      }
      async function inventory(page,loaded,mapCard=true) {
        const links=await page.locator('a[href]').evaluateAll(nodes=>nodes.filter(a=>/^https?:$/.test(new URL(a.href).protocol)&&new URL(a.href).origin!==location.origin).map(a=>({href:a.getAttribute('href'),attrs:Object.fromEntries([...a.attributes].map(n=>[n.name,n.value])),text:a.textContent.trim()})));
        const nonAffiliate=links.filter(n=>!n.attrs.class?.split(' ').includes('js-aff')).map(n=>n.href).sort();
        equal(nonAffiliate,loaded?[...attribution].sort():[],'Only mandatory Leaflet/OSM attribution may be non-affiliate outbound');
        const affiliate=links.filter(n=>n.attrs.class?.split(' ').includes('js-aff'));
        equal(affiliate.length,opening.length+(mapCard?1:0));
        const urls=opening.map(a=>a.match(/href="([^"]+)"/)[1]);
        equal(affiliate.every(a=>urls.includes(a.href)&&new URL(a.href).hostname==='klook.tpk.ro'),true);
        return links;
      }
      for(const consent of [null,'denied','granted']) {
        const {context,page,requests,errors,missing}=await open(consent);
        try {
          await inventory(page,false);
          const originals=await page.locator('#hotel-options a.js-aff, #premium-alternative a.js-aff').evaluateAll(nodes=>nodes.map(n=>({attrs:Object.fromEntries([...n.attributes].map(a=>[a.name,a.value])),text:n.textContent})));
          await page.locator('#hotel-map').scrollIntoViewIfNeeded();
          await page.locator('#hotel-map-canvas[data-map-ready="1"]').waitFor();
          equal(await page.locator('.tg-hotel-map__pin').count(),opening.length);
          const observations=[];
          for(let i=0;i<opening.length;i++) {
            await page.locator('#hotel-map-choices button').nth(i).focus();await page.keyboard.press('Enter');
            await page.locator('#hotel-map-card details summary').focus();await page.keyboard.press('Space');
            equal(await page.locator('#hotel-map-card details').evaluate(n=>n.open),true);
            const booking=page.locator('#hotel-map-card a.js-aff');
            const attributes=await booking.evaluate(n=>Object.fromEntries([...n.attributes].map(a=>[a.name,a.value])));
            const expected={...originals[i].attrs};
            if(name!=='luxury'){expected['data-placement']='map';expected['data-experiment-variant']='with_map';}
            equal(attributes,expected,'Full cloned affiliate attribute contract');
            equal(await booking.isVisible(),true);
            observations.push(await inventory(page,true));
            await booking.click();
            const events=await page.evaluate(()=>trackingCalls.filter(c=>c[0]==='event'&&c[1]==='affiliate_click').map(c=>c[2]));
            equal(events.length,consent==='granted'?i+1:0);
            if(consent==='granted') {
              const payload={affiliate_program:'klook',page_type:'guide',destination:expected.href,transport_type:'beacon'};
              if(name!=='luxury')Object.assign(payload,{hotel_id:expected['data-hotel-id'],placement:'map',experiment_variant:'with_map',page_path:routePath});
              equal(events[i],payload);
            }
          }
          equal(requests.some(u=>new URL(u).hostname==='klook.tpk.ro'),false,'No partner request sent');
          equal(errors,[]);equal(missing,[]);
          if(consent==='granted') {
            await page.locator('#hotel-map-card').screenshot({path:path.join(out,name+'-map-card.png')});
            report.screenshots.push(name+'-map-card.png');
          }
          report.pages.push({page:name,consent,outgoing_by_selected_hotel:observations});
        }finally{await context.close();}
      }
      const nojs=await open(null,false);
      try {await inventory(nojs.page,false,false);equal(nojs.requests.some(u=>u.includes('leaflet-1.9.4')),false);equal(nojs.errors,[]);}finally{await nojs.context.close();}
    }
    report.passed=true;report.checks=checks;
    fs.writeFileSync(path.join(out,'outgoing-browser-report.json'),JSON.stringify(report,null,2)+'\n');
    console.log(JSON.stringify({passed:report.passed,checks,scenarios:report.pages.length,screenshots:report.screenshots}));
  }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
