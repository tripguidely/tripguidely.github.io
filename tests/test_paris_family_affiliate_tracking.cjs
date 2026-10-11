// Offline browser integration test. No analytics or affiliate requests are sent.
// Usage: node tests/test_paris_family_affiliate_tracking.cjs PLAYWRIGHT_MODULE CHROME_EXECUTABLE [BASE_REF]
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {execFileSync} = require('node:child_process');
const {chromium} = require(process.argv[2] || 'playwright-core');
const root = path.resolve(__dirname, '..');
const pagePath = 'hotels/paris/family-hotels/index.html';
const origin = 'https://tripguidely.github.io';
const hotels = [
  ['247912', 'paris_hotel_citadines_halles', 'https://klook.tpk.ro/7c3IV7YH'],
  ['732134', 'paris_hotel_pullman_montparnasse', 'https://klook.tpk.ro/w9gvKJbA'],
  ['248416', 'paris_hotel_regence_etoile', 'https://klook.tpk.ro/LsvOTPx3'],
  ['412657', 'paris_hotel_bb_batignolles', 'https://klook.tpk.ro/gX4TDO9u']
];
const mime = {'.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css',
  '.svg': 'image/svg+xml', '.webp': 'image/webp', '.avif': 'image/avif', '.png': 'image/png'};
const source = fs.readFileSync(path.join(root, 'assets/js/site.js'), 'utf8');
const html = fs.readFileSync(path.join(root, pagePath), 'utf8');
const original = execFileSync('git', ['show', (process.argv[4] || 'origin/main') + ':' + pagePath], {cwd: root, encoding: 'utf8'});
const withoutTracking = value => value.replace(/ data-hotel-id="[^"]+" data-placement="list" data-experiment-variant="baseline"/g, '')
  // The separately tested map is additive; original article and SEO stay exact.
  .replace(/<section id="hotel-map"[\s\S]*?<\/section>\r?\n/, '')
  .replace(/  <link rel="stylesheet" href="\/assets\/css\/pages\/paris-family-hotel-map.css" \/>\r?\n/, '')
  .replace(/<script src="\/assets\/js\/paris-family-hotel-map.js" defer><\/script>\r?\n/, '')
  .replace(/\r\n/g, '\n');
assert.equal(withoutTracking(html), withoutTracking(original),
  'Only the four tracking attribute groups may change in the HTML, including its SEO metadata');

(async () => {
  const browser = await chromium.launch({headless: true,
    ...(process.argv[3] ? {executablePath: process.argv[3]} : {})});
  let checks = 1;
  try {
    async function open(consent, route = '/hotels/paris/family-hotels/') {
      const context = await browser.newContext({serviceWorkers: 'block'});
      await context.route('**/*', async request => {
        const url = new URL(request.request().url());
        if (url.origin !== origin) return request.abort();
        let file = path.resolve(root, '.' + decodeURIComponent(url.pathname));
        if (!file.startsWith(root + path.sep)) return request.abort();
        if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
        if (!fs.existsSync(file)) return request.fulfill({status: 404, body: ''});
        await request.fulfill({body: fs.readFileSync(file), contentType: mime[path.extname(file)] || 'application/octet-stream'});
      });
      await context.addInitScript(value => {
        if (value !== null) localStorage.setItem('tg_consent_v2', value);
        window.trackingCalls = [];
        window.gtag = function () { window.trackingCalls.push(Array.from(arguments)); };
        // Observe actual click dispatch without opening a partner/analytics URL.
        document.addEventListener('click', event => {
          if (event.target.closest('a.js-aff')) event.preventDefault();
        }, true);
      }, consent);
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.goto(origin + route);
      await page.waitForFunction(() => document.documentElement.getAttribute('data-affiliateclicks-bound') === '1');
      return {context, page, errors};
    }
    async function events(page) {
      return page.evaluate(() => window.trackingCalls.filter(call => call[0] === 'event' && call[1] === 'affiliate_click').map(call => call[2]));
    }
    for (const consent of [null, 'denied', 'granted']) {
      const {context, page, errors} = await open(consent);
      try {
        const links = page.locator('a.js-aff');
        assert.equal(await links.count(), 4); checks++;
        for (let i = 0; i < hotels.length; i++) {
          const [id, subid, url] = hotels[i];
          const link = links.nth(i);
          assert.deepEqual(await link.evaluate(a => [a.getAttribute('data-hotel-id'), a.getAttribute('data-subid'), a.getAttribute('href'), a.getAttribute('rel'), a.getAttribute('target')]),
            [id, subid, url, 'nofollow sponsored noopener', '_blank']); checks++;
          // Cover descendant targets as well as keyboard activation.
          if (i % 2) { await link.focus(); await page.keyboard.press('Enter'); }
          else { await link.evaluate(a => { const span = document.createElement('span'); span.textContent = a.textContent; a.replaceChildren(span); }); await link.locator('span').click(); }
          const observed = await events(page);
          assert.equal(observed.length, consent === 'granted' ? i + 1 : 0); checks++;
          if (consent === 'granted') {
            assert.deepEqual(observed[i], {affiliate_program: 'klook', page_type: 'guide', destination: url,
              transport_type: 'beacon', hotel_id: id, placement: 'list', experiment_variant: 'baseline',
              page_path: '/hotels/paris/family-hotels/'}); checks++;
          }
        }
        if (consent === 'granted') {
          await page.addScriptTag({content: source});
          await links.first().click();
          assert.equal((await events(page)).length, 5, 'Reinitialization must not duplicate events'); checks++;
          // Future map buttons can opt in through the same handler; no map is built.
          await links.first().evaluate(a => { a.dataset.placement = 'map'; a.dataset.experimentVariant = 'with_map'; });
          await links.first().click();
          assert.deepEqual((await events(page))[5], {affiliate_program: 'klook', page_type: 'guide', destination: hotels[0][2],
            transport_type: 'beacon', hotel_id: hotels[0][0], placement: 'map', experiment_variant: 'with_map',
            page_path: '/hotels/paris/family-hotels/'}); checks++;
          await links.first().evaluate(a => { a.dataset.placement = 'invalid'; });
          await links.first().click();
          assert.deepEqual((await events(page))[6], {affiliate_program: 'klook', page_type: 'guide', destination: hotels[0][2], transport_type: 'beacon'}); checks++;
          await page.evaluate(() => localStorage.setItem('tg_consent_v2', 'denied'));
          await links.first().click();
          assert.equal((await events(page)).length, 7, 'Revoked consent must suppress clicks'); checks++;
        } else {
          await page.evaluate(() => localStorage.setItem('tg_consent_v2', 'granted'));
          await links.first().click();
          assert.equal((await events(page)).length, 1, 'Consent granted after page load must enable tracking'); checks++;
        }
        assert.deepEqual(errors, []); checks++;
      } finally { await context.close(); }
    }
    const {context, page, errors} = await open('granted', '/hotels/paris/');
    try {
      const link = page.locator('a.js-aff').first();
      const destination = await link.getAttribute('href');
      await link.click();
      assert.deepEqual(await events(page), [{affiliate_program: 'klook', page_type: 'guide', destination, transport_type: 'beacon'}]); checks++;
      assert.deepEqual(errors, []); checks++;
    } finally { await context.close(); }
    console.log(JSON.stringify({passed: true, checks, hotels: 4, analyticsAndAffiliateRequestsSent: 0}));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
