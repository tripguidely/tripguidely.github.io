// Offline browser integration: all routes are fulfilled locally or aborted.
// node tests/test_universal_affiliate_tracking.cjs PLAYWRIGHT_MODULE CHROME_EXECUTABLE [BASE_REF]
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {execFileSync} = require('node:child_process');
const {chromium} = require(process.argv[2] || 'playwright-core');
const root = path.resolve(__dirname, '..');
const pagePath = 'attractions/universal-studios-tickets/index.html';
const routePath = '/attractions/universal-studios-tickets/';
const origin = 'https://tripguidely.github.io';
const base = process.argv[4] || 'b193a14f190ea63118e371b316a3e7ef50827ef1';
const html = fs.readFileSync(path.join(root, pagePath), 'utf8');
const source = fs.readFileSync(path.join(root, 'assets/js/site.js'), 'utf8');
const before = execFileSync('git', ['show', base + ':' + pagePath], {cwd: root, encoding: 'utf8'});
const lf = value => value.replace(/\r\n/g, '\n');
assert.equal(lf(html.replace(/ data-(?:offer-id|cta-id|cta-location)="[^"]+"/g, '')), lf(before),
  'Only the three tracking attributes may change: URLs, SubIDs, content, SEO, styles and accessibility stay exact');
const parks = ['japan', 'singapore', 'hollywood', 'orlando', 'beijing'];
const urls = ['https://klook.tpk.ro/NS3OqxdG', 'https://klook.tpk.ro/R6L9zn5A',
  'https://klook.tpk.ro/Ymc25gvB', 'https://klook.tpk.ro/duswzuOU', 'https://klook.tpk.ro/V3doLaEz'];
const destinations = new Set(urls);
// Explicit document order: a missing, duplicated or moved placement fails the inventory.
const inventory = [
  ['japan', 'hero'],
  ...parks.slice(0, 4).map(park => [park, 'quick_picks']),
  ['japan', 'quick_answer'],
  ...parks.map(park => [park, 'comparison_table']),
  ...parks.map(park => [park, 'traveler_type_table']),
  ['japan', 'ticket_tips'],
  ...parks.map(park => [park, 'park_section']),
  ['japan', 'sidebar']
].map(([park, location]) => ({park, url: urls[parks.indexOf(park)], subid: 'us_' + park,
  offer: 'universal_' + park, id: 'universal_' + park + '_' + location, location}));
const mime = {'.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css',
  '.svg': 'image/svg+xml', '.webp': 'image/webp', '.avif': 'image/avif', '.png': 'image/png'};
let checks = 1;
let mockedAffiliateNavigations = 0;
const check = (actual, expected, label) => { assert.deepEqual(actual, expected, label); checks++; };
const events = page => page.evaluate(() => window.trackingCalls
  .filter(call => call[0] === 'event' && call[1] === 'affiliate_click').map(call => call[2]));
const customEvents = page => page.evaluate(() => window.trackingCalls.filter(call => call[0] === 'event'));
const expectedEvent = item => ({affiliate_program: 'klook', page_type: 'attractions-universal-studios-tickets', destination: item.url,
  transport_type: 'beacon', page_path: routePath, offer_id: item.offer, cta_id: item.id, cta_location: item.location});

(async () => {
  const browser = await chromium.launch({headless: true,
    ...(process.argv[3] ? {executablePath: process.argv[3]} : {})});
  try {
    async function open(consent, js = true) {
      const context = await browser.newContext({viewport: {width: 1440, height: 1000},
        serviceWorkers: 'block', reducedMotion: 'reduce', javaScriptEnabled: js});
      await context.route('**/*', async handler => {
        const url = new URL(handler.request().url());
        if (destinations.has(url.href)) {
          mockedAffiliateNavigations++;
          return handler.fulfill({contentType: 'text/html', body: '<title>Offline destination fixture</title>'});
        }
        if (url.origin !== origin) return handler.abort();
        let file = path.resolve(root, '.' + decodeURIComponent(url.pathname));
        if (!file.startsWith(root + path.sep)) return handler.abort();
        if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
        if (!fs.existsSync(file)) return handler.fulfill({status: 404, body: ''});
        return handler.fulfill({body: fs.readFileSync(file), contentType: mime[path.extname(file)] || 'application/octet-stream'});
      });
      await context.addInitScript(value => {
        // The existing lazy YouTube iframe is blocked and has no usable storage.
        if (window.top !== window || location.origin !== 'https://tripguidely.github.io') return;
        if (value !== null) localStorage.setItem('tg_consent_v2', value);
        window.trackingCalls = [];
        window.gtag = function () { window.trackingCalls.push(Array.from(arguments)); };
        // Invalid-destination probes must not leave the test page.
        // Valid links retain native navigation, verified through offline popups.
        document.addEventListener('click', event => {
          if (window.blockTestNavigation && event.target.closest('a.js-aff')) event.preventDefault();
        }, true);
      }, consent);
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.stack || error.message));
      await page.goto(origin + routePath);
      if (js) await page.waitForFunction(() => document.documentElement.getAttribute('data-affiliateclicks-bound') === '1');
      return {context, page, errors};
    }
    async function navigate(page, link, destination, activate) {
      const beforeNavigation = mockedAffiliateNavigations;
      const [popup] = await Promise.all([page.context().waitForEvent('page'), activate ? activate() : link.click()]);
      await popup.waitForLoadState('domcontentloaded');
      check(popup.url(), destination, 'Native target=_blank navigation retains the exact short URL');
      if (destinations.has(destination)) {
        check(await popup.title(), 'Offline destination fixture', 'No live partner page is loaded');
        check(mockedAffiliateNavigations, beforeNavigation + 1, 'The partner request was fulfilled locally');
      }
      check(page.url(), origin + routePath, 'The source page stays in place');
      await popup.close();
    }
    for (const consent of [null, 'denied', 'granted']) {
      const {context, page, errors} = await open(consent);
      try {
        const links = page.locator('a.js-aff');
        check(await links.count(), 23, 'Exactly 23 original CTAs');
        const observed = await links.evaluateAll(anchors => anchors.map(a => ({
          url: a.getAttribute('href'), subid: a.dataset.subid, offer: a.dataset.offerId,
          id: a.dataset.ctaId, location: a.dataset.ctaLocation, program: a.dataset.aff,
          rel: a.getAttribute('rel'), target: a.getAttribute('target')
        })));
        check(observed, inventory.map(({park, ...item}) => ({...item, program: 'klook',
          rel: 'sponsored nofollow noopener', target: '_blank'})), 'Exact mappings, identity, target and rel');
        check(new Set(observed.map(item => item.id)).size, 23);
        check(new Set(observed.map(item => item.offer)).size, 5);
        check(new Set(observed.map(item => item.url)).size, 5);
        for (let i = 0; i < inventory.length; i++) {
          const link = links.nth(i);
          const activation = i % 3 === 1 ? async () => {
            await link.focus(); await page.keyboard.press('Enter');
          } : i % 3 === 2 ? async () => {
            await link.evaluate(a => {
              const span = document.createElement('span');
              span.textContent = a.textContent; a.replaceChildren(span);
            });
            await link.locator('span').click();
          } : undefined;
          await navigate(page, link, inventory[i].url, activation);
          check(await events(page), consent === 'granted' ? inventory.slice(0, i + 1).map(expectedEvent) : [],
            'One event per activation after consent only');
        }
        if (consent !== 'granted') {
          check(await customEvents(page), [], 'Unknown/refused consent emits no custom GA4 event');
          check(await page.locator('script[src*="googletagmanager.com/gtag/js"]').count(), 0,
            'GA4 stays unloaded without consent');
          // Exercise the existing consent UI after page load.
          if (consent === 'denied') await page.locator('a.js-consent').click();
          await page.locator('#tg-consent-accept').click();
          await navigate(page, links.first(), urls[0]);
          check(await events(page), [expectedEvent(inventory[0])], 'Accept enables the existing listener');
        } else {
          await page.addScriptTag({content: source});
          await navigate(page, links.first(), urls[0]);
          check((await events(page)).length, 24, 'Reloading site.js must not duplicate listeners');
          // Chrome can start background-tab requests before route interception.
          // Exercise the trusted modified click with navigation suppressed here.
          await page.evaluate(() => { window.blockTestNavigation = true; });
          await links.first().click({modifiers: ['Control']});
          check((await events(page)).length, 25, 'Modified clicks count once');
          await page.evaluate(() => { window.blockTestNavigation = false; });
          await navigate(page, links.first(), urls[0]);
          check((await events(page)).length, 26, 'A repeated legitimate activation counts separately');
          await page.evaluate(() => localStorage.setItem('tg_consent_v2', 'denied'));
          const beforeRevocation = await customEvents(page);
          await navigate(page, links.first(), urls[0]);
          check(await customEvents(page), beforeRevocation, 'Revocation suppresses all further custom events');
        }
        check(errors, [], 'No uncaught JavaScript errors: ' + JSON.stringify(errors));
        console.log(JSON.stringify({scenario: 'all-ctas', consent: consent || 'unknown', passed: true, checks}));
      } finally { await context.close(); }
    }
    const {context, page, errors} = await open('granted');
    try {
      const link = page.locator('a.js-aff').first();
      const invalid = [null, '', '   ', '#japan', '#missing-target', '?failed=1', routePath,
        origin + routePath, origin + routePath + '#japan', 'http://tripguidely.github.io' + routePath,
        'javascript:void(0)', 'mailto:test@example.com', 'tel:123', 'data:text/html,invalid', 'https://', 'http://['];
      await page.evaluate(() => { window.blockTestNavigation = true; });
      for (const href of invalid) {
        await link.evaluate((a, value) => value === null ? a.removeAttribute('href') : a.setAttribute('href', value), href);
        await link.click();
        check(await events(page), [], 'Invalid or same-host destinations cannot emit affiliate_click: ' + href);
      }
      await link.evaluate((a, url) => { a.href = url; }, urls[0]);
      for (const button of [1, 2]) {
        await link.dispatchEvent('click', {button});
        check(await events(page), [], 'A non-primary click event is not a primary activation');
      }
      // Reproduce Drive-style clearing without loading or altering Drive.
      await page.evaluate(() => { window.blockTestNavigation = false; });
      await link.evaluate(a => a.setAttribute('href', ''));
      await navigate(page, link, origin + routePath);
      check(await events(page), [], 'A blank href that opens this guide is not an outbound affiliate click');
      await link.evaluate((a, url) => a.setAttribute('href', url), urls[0]);
      await navigate(page, link, urls[0]);
      check(await events(page), [expectedEvent(inventory[0])], 'Restored href works without stale attribution');
      await link.evaluate(a => a.removeAttribute('data-cta-location'));
      await navigate(page, link, urls[0]);
      check((await events(page))[1], {affiliate_program: 'klook', page_type: 'attractions-universal-studios-tickets',
        destination: urls[0], transport_type: 'beacon'}, 'Incomplete opt-in metadata keeps the legacy payload');
      check(errors, []);
    } finally { await context.close(); }
    const nojs = await open(null, false);
    try {
      check(await nojs.page.locator('a.js-aff').count(), 23);
      await navigate(nojs.page, nojs.page.locator('a.js-aff').first(), urls[0]);
      check(nojs.errors, [], 'Native links also work with JavaScript disabled');
    } finally { await nojs.context.close(); }
    console.log(JSON.stringify({passed: true, checks, ctas: 23, parks: 5,
      mockedAffiliateNavigations, realAnalyticsAndAffiliateRequestsSent: 0, ga4ReceiptVerified: false}));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
