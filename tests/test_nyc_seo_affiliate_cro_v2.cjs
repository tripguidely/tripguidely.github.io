// Targeted V2 preservation and offline Chrome checks. No live partner/analytics requests.
// node tests/test_nyc_seo_affiliate_cro_v2.cjs PLAYWRIGHT CHROME OUTPUT_DIR AXE
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),assert=require('node:assert/strict');
const {chromium}=require(process.argv[2]),root=path.resolve(__dirname,'..'),out=path.resolve(process.argv[4]);
assert(!out.startsWith(root+path.sep)&&out!==root);fs.mkdirSync(out,{recursive:true});
const base='1cd006b75c1de7aa8a2a1611ab0e42974673a0fe',origin='https://tripguidely.github.io';
const categories=['luxury','family','cheap'],routes=['',...categories.map(c=>c+'-hotels/')];
const report={passed:false,checks:0,views:[],axe:[],externalRequestsAllowed:0};
function ok(v,m){assert(v,m);report.checks++}function eq(a,b,m){assert.deepEqual(a,b,m);report.checks++}
const git=args=>cp.execFileSync('git',args,{cwd:root,encoding:'utf8'}).trim().split(/\r?\n/).filter(Boolean);
const approved=['assets/css/pages/new-york-hotels.css','hotels/new-york/index.html',...categories.map(c=>'hotels/new-york/'+c+'-hotels/index.html'),'tests/test_nyc_seo_affiliate_cro_v2.cjs','tests/test_new_york_hotels_preservation.py','tests/fixtures/site-baseline.json'].sort();
eq([...new Set([...git(['diff','--name-only',base]),...git(['ls-files','--others','--exclude-standard'])])].sort(),approved,'exact V2 scope including direct-link preservation checks');
const documents={};
for(const route of routes){const file='hotels/new-york/'+route+'index.html',html=fs.readFileSync(path.join(root,file),'utf8').replace(/\r\n/g,'\n'),before=cp.execFileSync('git',['show',base+':'+file],{cwd:root,encoding:'utf8'}).replace(/\r\n/g,'\n');
 for(const [label,re] of [['all original complete affiliate anchors',/<a\b[^>]*\bjs-aff\b[^>]*>[\s\S]*?<\/a>/g],['all scripts including JSON-LD and Drive',/<script\b[\s\S]*?<\/script>/g],['all image and source markup',/<(?:img|source)\b[^>]*>/g],['canonical and hreflang',/<link\b[^>]*(?:rel="canonical"|hreflang=)[^>]*>/g]])eq(html.match(re),before.match(re),label+' '+route);
 eq((html.match(/<h1\b/g)||[]).length,1);ok(!/AggregateRating|ratingValue|lowPrice|highPrice/.test(html),'no fabricated price/review schema');documents[route]=html;
}
const registry=JSON.parse(fs.readFileSync(path.join(root,'docs/qa/new-york-hotels-sources.json')));
const registryFile='docs/qa/new-york-hotels-sources.json';
eq(fs.readFileSync(path.join(root,registryFile),'utf8').replace(/\r\n/g,'\n'),cp.execFileSync('git',['show',base+':'+registryFile],{cwd:root,encoding:'utf8'}).replace(/\r\n/g,'\n'),'official source registry remains exact');
const hotelDomains=new Set(['fairmont.com','langhamhotels.com','hilton.com','marriott.com','thepodhotel.com']);
for(const [route,html] of Object.entries(documents)){
 const hrefs=[...html.matchAll(/<a\b[^>]*\bhref="([^"]*)"/g)].map(m=>m[1]);
 eq(hrefs.filter(h=>hotelDomains.has(new URL(h,origin).hostname.replace(/^www\./,''))),[],'no clickable direct hotel source/booking links '+route);
 if(route)ok(hrefs.includes('https://www.mta.info/maps'),'practical MTA link preserved');
}
const baselinePath='tests/fixtures/site-baseline.json';
const baselineBefore=JSON.parse(cp.execFileSync('git',['show',base+':'+baselinePath],{cwd:root,encoding:'utf8'}));
const baselineNow=JSON.parse(fs.readFileSync(path.join(root,baselinePath),'utf8'));
const priorCount=baselineBefore.authorizations.length,addedAuthorizations=baselineNow.authorizations.slice(priorCount);
eq({...baselineNow,authorizations:baselineNow.authorizations.slice(0,priorCount)},baselineBefore,'historic authorizations, exceptions, auditor inventory and contracts preserved');
eq(addedAuthorizations.map(e=>[e.kind,e.source,e.base_revision,e.before,e.after]),[["seo_metadata", "hotels/new-york/index.html", "1cd006b75c1de7aa8a2a1611ab0e42974673a0fe", "7e6bc5fac095cefbf6481af1731b76cbea2581460f7eebf55e8aa8bbc46ee1a7", "0ef6559720708a872231f449e17d5cfd5f1bbf973efb9405594057e149b5cc22"], ["seo_metadata", "hotels/new-york/luxury-hotels/index.html", "1cd006b75c1de7aa8a2a1611ab0e42974673a0fe", "d16ab2d4701bbe7c47390eabcbdab43457d1d4f416ab36fcc57bea2f0b2bc03d", "5dd13c928fff502364d28d9bfe8716d6cf0b8bb503d734e891d27fbc2a60a022"], ["seo_metadata", "hotels/new-york/family-hotels/index.html", "1cd006b75c1de7aa8a2a1611ab0e42974673a0fe", "7d74a79c8ec14694b7028ae0e4ab15574c1fedd8ca9323a5c10853305e66480c", "9ca387f7859bed01ee1b1d61c399aee76cf64b07ff287e314f5ade01006516fb"], ["seo_metadata", "hotels/new-york/cheap-hotels/index.html", "1cd006b75c1de7aa8a2a1611ab0e42974673a0fe", "48a3baf15316caede3d3ba461d7b0eeb0cc60ea3fec11cf46ab6e9d864ec60d5", "c5dad241cbcfa7295df39efd6fbbf15ebca04ccdf70baa60bd391f95f13c397b"]],'exact four owner-approved SEO authorizations only');
ok(addedAuthorizations.every(e=>e.reviewed_by==='owner instruction: TRIPGUIDELY — APPROBATION FINALE SEO/CRO NEW YORK V2 (Codex conversation, 2026-10-20)'&&e.recorded_on==='2026-10-20'),'explicit owner review recorded without invented identity');
if(process.argv.includes('--static-only')){console.log(JSON.stringify({passed:true,checks:report.checks,mode:'static preservation and direct-hotel links'}));process.exit(0);}

const mime={'.html':'text/html','.css':'text/css','.js':'text/javascript','.webp':'image/webp','.avif':'image/avif','.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.ico':'image/x-icon'};
const tile=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a5qkAAAAASUVORK5CYII=','base64');
async function open(browser,route,width,consent='granted',js=true){
 const context=await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce',serviceWorkers:'block',javaScriptEnabled:js});
 await context.route('**/*',r=>{const u=new URL(r.request().url());if(u.hostname==='tile.openstreetmap.org')return r.fulfill({body:tile,contentType:'image/png'});if(u.origin!==origin)return r.abort();let f=path.resolve(root,'.'+decodeURIComponent(u.pathname));if(!f.startsWith(root+path.sep))return r.abort();if(fs.existsSync(f)&&fs.statSync(f).isDirectory())f=path.join(f,'index.html');return fs.existsSync(f)?r.fulfill({body:fs.readFileSync(f),contentType:mime[path.extname(f)]||'application/octet-stream'}):r.fulfill({status:404,body:''});});
 await context.addInitScript(value=>{if(value!==null)localStorage.setItem('tg_consent_v2',value);window.trackingCalls=[];window.gtag=function(){trackingCalls.push(Array.from(arguments));};document.addEventListener('click',e=>{if(e.target.closest('a.js-aff'))e.preventDefault();},true);},consent);
 const page=await context.newPage();await page.goto(origin+'/hotels/new-york/'+route);if(js)await page.waitForFunction(()=>document.documentElement.dataset.affiliateclicksBound==='1');return {context,page};
}
async function events(page){return page.evaluate(()=>trackingCalls.filter(x=>x[0]==='event'&&x[1]==='affiliate_click').map(x=>x[2]));}
async function mapReady(page){await page.locator('#hotel-map').scrollIntoViewIfNeeded();await page.waitForFunction(()=>document.querySelector('#hotel-map').dataset.mapState==='ready');}
(async()=>{const browser=await chromium.launch({headless:true,executablePath:process.argv[3]});try{
 for(const route of routes)for(const width of [320,390,641,760,900,1440]){const {context,page}=await open(browser,route,width);try{
  ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'no body overflow '+route+' '+width);
  eq(await page.locator('h1').count(),1);const ids=await page.locator('[id]').evaluateAll(es=>es.map(e=>e.id));eq(ids.length,new Set(ids).size,'unique IDs');
  const hrefs=await page.locator('main a[href]').evaluateAll(es=>es.map(e=>e.getAttribute('href')));
  for(const href of hrefs.filter(h=>h.startsWith('/')||h.startsWith('#'))){const u=new URL(href,page.url());let f=path.join(root,decodeURIComponent(u.pathname));if(fs.existsSync(f)&&fs.statSync(f).isDirectory())f=path.join(f,'index.html');ok(fs.existsSync(f),'internal path '+href);if(u.hash)ok(fs.readFileSync(f,'utf8').includes('id="'+decodeURIComponent(u.hash.slice(1))+'"'),'internal fragment '+href);}
  if(route){const category=route.replace('-hotels/',''),hotels=registry.hotels.filter(h=>h.category===category);
   eq(await page.locator('.ny-fit-list a').count(),3);eq(await page.locator('#comparison a.js-aff').count(),3);eq(await page.locator('#hotel-options a.js-aff').count(),3);
   for(const h of hotels){const card=page.locator('#card-'+h.key),cta=card.locator('a.js-aff'),choice=page.locator('.ny-fit-list a[href="#card-'+h.key+'"]');
    ok(await choice.evaluate(e=>e.getBoundingClientRect().height>=44),'fit link touch target');
    ok(await card.evaluate(e=>e.querySelector('.ny-hotel-actions').compareDocumentPosition(e.querySelector('.ny-hotel-tradeoff'))&Node.DOCUMENT_POSITION_FOLLOWING),'existing CTA before long trade-offs');
    eq(await cta.getAttribute('href'),h.affiliate_url);eq(await cta.getAttribute('data-subid'),h.subid);
    await cta.scrollIntoViewIfNeeded();ok(await cta.evaluate(e=>{const r=e.getBoundingClientRect();return r.left>=0&&r.right<=innerWidth+1;}),'card CTA fits');
   }
   if(width<=760){const region=page.locator('.tg-hotel-table-region');ok(await region.evaluate(e=>e.scrollWidth<=e.clientWidth+1),'mobile comparison needs no sideways scroll');for(const a of await page.locator('#comparison a.js-aff').all()){await a.scrollIntoViewIfNeeded();ok(await a.evaluate(e=>{const r=e.getBoundingClientRect();return r.left>=0&&r.right<=innerWidth+1&&r.height>=44;}),'comparison CTA visible and touch sized');}}
   if(width===641||width===1440){await mapReady(page);eq(await page.locator('.ny-map-pin').count(),3);await page.locator('#hotel-map-choices button').nth(1).click();eq(await page.locator('#hotel-map-card-title').textContent(),hotels[1].name);eq(await page.locator('.ny-hotel-card.is-selected').getAttribute('data-offer-id'),hotels[1].offer_id);await page.locator('#hotel-map-card a.js-aff').scrollIntoViewIfNeeded();ok(await page.locator('#hotel-map-card a.js-aff').evaluate(e=>{const r=e.getBoundingClientRect();return r.left>=0&&r.right<=innerWidth+1;}),'map CTA fits after new CSS');eq(await events(page),[],'no click event on map selection');}
   if(width===390){await page.locator('#quick-answer').screenshot({path:path.join(out,category+'-choice-mobile.png')});await page.locator('#comparison').screenshot({path:path.join(out,category+'-comparison-mobile.png')});}
  }
  if(width===390||width===1440){if(process.argv[5]){await page.addScriptTag({path:process.argv[5]});const result=await page.evaluate(()=>axe.run(document.querySelector('main'),{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}}));report.axe.push({route,width,violations:result.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)}))});eq(result.violations.length,0,'no main WCAG violations');}await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:path.join(out,(route||'hub/').replace('/','')+'-hero-'+width+'.png')});}
  report.views.push({route,width});
 }finally{await context.close();}}
 // Exercise all nine original offers at all placements with each consent state.
 for(const category of categories)for(const consent of [null,'denied','granted']){const {context,page}=await open(browser,category+'-hotels/',641,consent);try{await mapReady(page);const hotels=registry.hotels.filter(h=>h.category===category);let expected=0;for(let i=0;i<hotels.length;i++){const h=hotels[i];await page.locator('#hotel-map-choices button').nth(i).click();for(const location of ['comparison','hotel_card','map']){const link=page.locator('a[data-cta-id="'+h.offer_id+'_'+location+'"]');await link.click();if(consent==='granted')expected++;const observed=await events(page);eq(observed.length,expected,'exactly one event with consent, none if denied/unknown');if(consent==='granted'){eq(observed.at(-1).offer_id,h.offer_id);eq(observed.at(-1).cta_location,location);eq(observed.at(-1).destination,h.affiliate_url);}}}
 await page.addScriptTag({path:path.join(root,'assets/js/site.js')});await page.addScriptTag({path:path.join(root,'assets/js/new-york-hotel-map.js')});await page.locator('#hotel-map-card a.js-aff').click();if(consent==='granted')expected++;eq((await events(page)).length,expected,'no duplicate listeners after reinitialization');
 }finally{await context.close();}}
 for(const route of routes){const {context,page}=await open(browser,route,390,'denied',false);try{eq(await page.locator(route?'#hotel-options a.js-aff':'a.js-aff').count(),route?3:5);ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'no-JS fallback');}finally{await context.close();}}
 report.passed=true;
 }finally{await browser.close();fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));}console.log(JSON.stringify({passed:report.passed,checks:report.checks,views:report.views.length,axe:report.axe},null,2));})().catch(e=>{console.error(e);process.exitCode=1});
