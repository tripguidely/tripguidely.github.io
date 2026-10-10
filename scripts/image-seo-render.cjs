/* Opt-in local Chrome sampler. HTTP/WebSocket guards are not an OS network sandbox.
 * node scripts/image-seo-render.cjs ROOT OUTPUT PLAYWRIGHT_MODULE CHROME_EXECUTABLE --allow-browser-sampling
 * OUTPUT must be a fresh directory outside all Git worktrees. See documented limits.
 */
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
if (!process.argv.slice(6).includes('--allow-browser-sampling')) {
  console.error('Browser sampling is disabled by default. Review network limits and explicitly use --allow-browser-sampling for trusted source only.');
  process.exit(2);
}
const {chromium} = require(process.argv[4] || 'playwright-core');
const root = fs.realpathSync(process.argv[2]);
const requestedOutput = path.resolve(process.argv[3]);
function prospectiveRealPath(p) {
  try {
    if (fs.lstatSync(p).isSymbolicLink()) throw Error('Symlink/reparse output ancestry forbidden');
    return fs.realpathSync(p);
  } catch (error) { if (error.code !== 'ENOENT') throw error; }
  return path.join(prospectiveRealPath(path.dirname(p)), path.basename(p));
}
for (let p = requestedOutput; ; p = path.dirname(p)) {
  try {if (fs.lstatSync(p).isSymbolicLink()) throw Error('Symlink/reparse output ancestry forbidden');}
  catch (error) {if (error.code !== 'ENOENT') throw error;}
  if (p === path.dirname(p)) break;
}
const output = prospectiveRealPath(requestedOutput);
function inside(p, parent) { const rel = path.relative(parent, p); return rel === '' || (!rel.startsWith('..' + path.sep) && rel !== '..' && !path.isAbsolute(rel)); }
if (inside(output, root) || inside(root, output)) throw Error('Output must be outside repository and its ancestors');
for (let p = output; ; p = path.dirname(p)) {
  try {fs.lstatSync(path.join(p, '.git')); throw Error('Output inside a Git worktree forbidden');}
  catch (error) {if (error.code !== 'ENOENT') throw error;}
  if (p === path.dirname(p)) break;
}
fs.mkdirSync(path.dirname(output), {recursive:true});
// Atomic fresh-directory reservation rejects all prior files, hardlinks and failed runs.
fs.mkdirSync(output, {mode:0o700});
const outputIdentity = fs.statSync(output, {bigint:true});
function checkOutputIdentity() {
  if (prospectiveRealPath(output) !== output) throw Error('Output directory path changed');
  const current = fs.statSync(output, {bigint:true});
  if (current.dev !== outputIdentity.dev || current.ino !== outputIdentity.ino) throw Error('Output directory identity changed');
}
function writeExclusive(name, bytes) {
  if (path.basename(name) !== name || ['','.','..'].includes(name)) throw Error('Invalid output filename');
  checkOutputIdentity();
  const fd = fs.openSync(path.join(output,name), fs.constants.O_WRONLY | fs.constants.O_CREAT | fs.constants.O_EXCL | (fs.constants.O_NOFOLLOW || 0), 0o600);
  try {
    if (fs.fstatSync(fd,{bigint:true}).nlink !== 1n) throw Error('Output file alias detected');
    checkOutputIdentity();
    fs.writeFileSync(fd, bytes);
  } finally {fs.closeSync(fd);}
}
const pages = [];
function walk(dir) {
  for (const entry of fs.readdirSync(dir, {withFileTypes: true}).sort((a,b) => a.name.localeCompare(b.name))) {
    if (entry.isSymbolicLink()) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory() && !['.git','node_modules','venv','.venv','__pycache__'].includes(entry.name) && !fs.existsSync(path.join(full,'.git'))) walk(full);
    else if (entry.isFile() && /\.html?$/.test(entry.name) && /<title[\s>]/i.test(fs.readFileSync(full,'utf8'))) pages.push(path.relative(root, full).split(path.sep).join('/'));
  }
}
walk(root);
const mime = {'.html':'text/html','.css':'text/css','.js':'application/javascript','.svg':'image/svg+xml','.png':'image/png','.webp':'image/webp','.avif':'image/avif','.jpg':'image/jpeg','.woff2':'font/woff2'};
const server = http.createServer((req,res) => {
  try {
    let file = path.resolve(root, '.' + decodeURIComponent(new URL(req.url,'http://localhost').pathname));
    if (!inside(file,root)) { res.writeHead(403).end(); return; }
    if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file,'index.html');
    if (!fs.existsSync(file) || !fs.statSync(file).isFile() || !inside(fs.realpathSync(file),root)) { res.writeHead(404).end(); return; }
    res.writeHead(200, {'Content-Type': mime[path.extname(file)] || 'application/octet-stream', 'Cache-Control':'no-store',
      'Content-Security-Policy': "connect-src 'self'; worker-src 'none'; frame-src 'self'; object-src 'none'; form-action 'none'"});
    fs.createReadStream(file).pipe(res);
  } catch { res.writeHead(400).end(); }
});
(async () => {
  await new Promise(resolve => server.listen(0,'127.0.0.1',resolve));
  const origin = `http://127.0.0.1:${server.address().port}`;
  let browser;
  const runs = [];
  const representatives = new Set(['index.html','hotels/paris/index.html','hotels/paris/luxury-hotels/index.html','itinerary/paris/2-days/index.html','things-to-do/london/harry-potter/index.html','transport/index.html','cruises/mediterranean/index.html']);
  try {
    browser = await chromium.launch({executablePath: process.argv[5], headless:true});
    for (const [viewport,dpr] of [[390,2],[1440,1],[320,1],[768,1],[1024,1]]) {
      const context = await browser.newContext({viewport:{width:viewport,height:900},deviceScaleFactor:dpr,serviceWorkers:'block',acceptDownloads:false});
      if (typeof context.routeWebSocket !== 'function') throw Error('Runtime lacks required WebSocket interception; sampling refused');
      await context.route('**/*', route => {
        const url = new URL(route.request().url());
        return url.protocol === 'http:' && url.origin === origin ? route.continue() : route.abort();
      });
      // Never connectToServer(): intercepted sockets have no upstream connection.
      await context.routeWebSocket(/.*/, socket => socket.close({code:1008,reason:'Image audit blocks WebSockets'}));
      await context.addInitScript(() => {
        // Unsupported transport APIs are rejected in page realms. This is defense
        // in depth for trusted pages, not isolation from hostile browser code.
        for (const name of ['WebTransport','RTCPeerConnection','webkitRTCPeerConnection']) {
          Object.defineProperty(globalThis,name,{value:class {constructor(){throw new TypeError('Transport disabled for image audit');}},writable:false,configurable:false});
        }
        window.imageAuditPerf = {lcp: null, cls:0};
        try {new PerformanceObserver(list => {for(const e of list.getEntries()) window.imageAuditPerf.lcp={ms:e.startTime,tag:e.element?.tagName,src:e.element?.currentSrc,id:e.element?.id};}).observe({type:'largest-contentful-paint',buffered:true});} catch {}
        try {new PerformanceObserver(list => {for(const e of list.getEntries()) if(!e.hadRecentInput) window.imageAuditPerf.cls += e.value;}).observe({type:'layout-shift',buffered:true});} catch {}
      });
      const tab = await context.newPage();
      for (const source of pages.filter(p => viewport === 390 || viewport === 1440 || representatives.has(p))) {
        await tab.goto(origin + '/' + source,{waitUntil:'domcontentloaded',timeout:15000});
        await tab.waitForLoadState('load').catch(() => {});
        await tab.waitForTimeout(150);
        await tab.evaluate(() => document.fonts.ready).catch(() => {});
        const actualUrl = tab.url();
        const originalHtml = fs.readFileSync(path.join(root,source),'utf8');
        const result = await tab.evaluate(html => {
          const staticImages = Array.from(new DOMParser().parseFromString(html,'text/html').images);
          const available = Array.from(document.images);
          const images = staticImages.flatMap((original,index) => {
            const position = available.findIndex(im => im.getAttribute('src') === original.getAttribute('src') && im.getAttribute('alt') === original.getAttribute('alt'));
            if(position < 0) return [];
            const im = available.splice(position,1)[0];
          const rect=im.getBoundingClientRect(), css=getComputedStyle(im);
          return [{index,width:rect.width,height:rect.height,top:rect.top,naturalWidth:im.naturalWidth,naturalHeight:im.naturalHeight,currentSrc:im.currentSrc,complete:im.complete,objectFit:css.objectFit,objectPosition:css.objectPosition,loading:im.loading,alt:im.getAttribute('alt')}];
          });
          return {images,performance:window.imageAuditPerf,scrollWidth:document.documentElement.scrollWidth};
        },originalHtml);
        if(actualUrl !== origin + '/' + source) result.images = [];
        runs.push({page:source,origin,viewport,dpr,actualUrl,redirected:actualUrl !== origin + '/' + source,...result});
        if(representatives.has(source) && [390,1440].includes(viewport)) writeExclusive(source.replace(/\//g,'_') + `-${viewport}.png`, await tab.screenshot({fullPage:true}));
      }
      await context.close();
      console.log(`Measured ${viewport}px at DPR ${dpr}; total samples ${runs.length}`);
    }
    writeExclusive('render.json',JSON.stringify(runs,null,2));
    console.log(`Saved ${runs.length} opt-in local lab samples; HTTP/WebSocket guards active, not an OS network sandbox or field CWV measurement.`);
  } finally { if (browser) await browser.close(); server.close(); }
})().catch(error => { console.error(error); server.close(); process.exitCode=1; });
