/* TripGuidely V4 local qualification. No production publication policy is enabled. */
const MAX_BYTES = 65536;
const SOURCES = new Set(['https://www.gdacs.org/', 'https://www.who.int/']);
const DESTINATIONS = {'fr-paris':'FR','gb-london':'GB','it-rome':'IT','us-new-york-city':'US'};
const CATEGORIES = ['cyclone','health'];
const fields = (value, names) => value && Object.getPrototypeOf(value) === Object.prototype &&
  Object.keys(value).sort().join('|') === [...names].sort().join('|');
const text = (value, limit) => typeof value === 'string' && value.length > 0 && value.length <= limit &&
  !/[<>\u0000-\u001f\u007f-\u009f\u202a-\u202e\u2066-\u2069]/u.test(value);
const instant = value => typeof value === 'string' && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(value) &&
  Number.isFinite(Date.parse(value)) && new Date(value).toISOString() === value;
export const isLoopback = hostname => ['127.0.0.1','localhost','[::1]'].includes(hostname);

export function validateFeed(feed, now, context, {demo = false, hostname = ''} = {}) {
  if (!Number.isFinite(now) || DESTINATIONS[context.destination] !== context.country ||
      !fields(feed, ['schema','synthetic','generatedAt','expiresAt','advisories']) || feed.schema !== 1 ||
      feed.synthetic !== true || !demo || !isLoopback(hostname)) throw Error('policy_disabled');
  // The automatic production allowlist is deliberately empty. A browser flag is not approval.
  if (!instant(feed.generatedAt) || !instant(feed.expiresAt) ||
      Date.parse(feed.generatedAt) > now || Date.parse(feed.expiresAt) <= now ||
      Date.parse(feed.expiresAt) <= Date.parse(feed.generatedAt) ||
      Date.parse(feed.expiresAt) - Date.parse(feed.generatedAt) > 3600000 ||
      !Array.isArray(feed.advisories) || feed.advisories.length > 20) throw Error('feed_invalid');
  const seen = new Set();
  for (const item of feed.advisories) {
    if (!fields(item, ['id','category','priority','destination','country','area','title','description',
      'verifiedAt','expiresAt','sourceUrl','sourceName','evidence']) ||
      !text(item.id, 64) || !/^[a-z0-9-]+$/.test(item.id) || seen.has(item.id) ||
      !CATEGORIES.includes(item.category) || !Number.isInteger(item.priority) || item.priority < 1 || item.priority > 3 ||
      DESTINATIONS[item.destination] !== item.country || !text(item.area, 60) || !text(item.title, 48) ||
      !text(item.description, 160) || !text(item.sourceName, 32) || !SOURCES.has(item.sourceUrl) ||
      item.evidence !== 'synthetic-review-only' || !instant(item.verifiedAt) || !instant(item.expiresAt) ||
      Date.parse(item.verifiedAt) > Date.parse(feed.generatedAt) ||
      Date.parse(feed.generatedAt) - Date.parse(item.verifiedAt) > 3600000 ||
      Date.parse(item.expiresAt) <= Date.parse(item.verifiedAt) ||
      Date.parse(item.expiresAt) - Date.parse(item.verifiedAt) > 3600000 ||
      Date.parse(item.expiresAt) > Date.parse(feed.expiresAt)) throw Error('advisory_invalid');
    seen.add(item.id);
  }
  return feed;
}

export function selectAdvisory(feed, context, now) {
  return feed.advisories.filter(item => item.destination === context.destination && item.country === context.country &&
    Date.parse(item.expiresAt) > now).sort((a,b) => a.priority - b.priority ||
      CATEGORIES.indexOf(a.category) - CATEGORIES.indexOf(b.category) ||
      Date.parse(b.verifiedAt) - Date.parse(a.verifiedAt) || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0))[0] || null;
}

export async function readFeed(url, {signal, fetcher = fetch} = {}) {
  const response = await fetcher(url, {signal, cache:'no-store', credentials:'omit', redirect:'error', referrerPolicy:'no-referrer'});
  if (!response.ok || response.redirected || response.url !== url ||
      !/^application\/json(?:;|$)/i.test(response.headers.get('content-type') || '') ||
      Number(response.headers.get('content-length')) > MAX_BYTES || !response.body) throw Error('feed_unavailable');
  const reader = response.body.getReader();
  const chunks = []; let size = 0;
  try {
    for (;;) {
      const {value, done} = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > MAX_BYTES) throw Error('feed_too_large');
      chunks.push(value);
    }
  } finally { await reader.cancel(); }
  const bytes = new Uint8Array(size); let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
  return JSON.parse(new TextDecoder('utf-8', {fatal:true}).decode(bytes));
}

export function createClock(wall = Date.now, monotonic = () => performance.now()) {
  const startWall = wall(), startMono = monotonic(); let latest = startWall;
  return () => { latest = Math.max(latest, wall(), startWall + Math.max(0, monotonic() - startMono)); return latest; };
}

export async function mountBanner(host, {feedUrl, destination, country, demo = false}) {
  if (!(host instanceof HTMLElement) || !host.id || !/^[a-z][a-z0-9-]{0,63}$/.test(host.id)) throw Error('host_invalid');
  const url = new URL(feedUrl, location.href);
  const context = {destination, country};
  host.replaceChildren();
  const card = document.createElement('section'); card.className = 'tg-advisory'; card.hidden = true;
  const heading = document.createElement('h2'); heading.id = host.id + '-heading';
  card.setAttribute('aria-labelledby', heading.id);
  const body = document.createElement('p'); const meta = document.createElement('p'); meta.className = 'tg-advisory__meta';
  const status = document.createElement('span'); status.className = 'tg-advisory__status';
  status.setAttribute('role','status'); status.setAttribute('aria-live','polite');
  card.append(heading, body, meta); host.append(card, status);
  const now = createClock(); let feed = null, timer = null, controller = new AbortController(), disposed = false;
  const clear = () => { card.hidden = true; card.replaceChildren(); };
  const check = () => {
    clearTimeout(timer);
    if (disposed) return;
    if (document.hidden) { clear(); return; }
    try {
      validateFeed(feed, now(), context, {demo, hostname:location.hostname});
      const item = selectAdvisory(feed, context, now());
      if (!item) { clear(); status.textContent = 'Travel advisory removed or unavailable.'; return; }
      heading.textContent = 'Travel advisory · ' + item.title + ' · SYNTHETIC';
      body.textContent = item.description;
      const area = document.createElement('span'); area.textContent = item.area + ' · Verified ';
      const time = document.createElement('time'); time.dateTime = item.verifiedAt;
      time.textContent = new Date(item.verifiedAt).toLocaleString('en-GB', {timeZone:'UTC',dateStyle:'medium',timeStyle:'short'}) + ' UTC';
      const source = document.createElement('a'); source.href = item.sourceUrl; source.rel = 'noreferrer';
      source.textContent = item.sourceName + ' — official reference';
      meta.replaceChildren(area,time,document.createTextNode(' · '),source);
      card.replaceChildren(heading,body,meta); card.hidden = false;
      status.textContent = 'Synthetic travel advisory available.';
      timer = setTimeout(check, Math.max(1, Math.min(Date.parse(feed.expiresAt), Date.parse(item.expiresAt)) - now()));
    } catch { clear(); status.textContent = 'Travel advisory unavailable.'; }
  };
  const onVisibility = () => check();
  document.addEventListener('visibilitychange', onVisibility); window.addEventListener('pageshow', check);
  const timeout = setTimeout(() => controller.abort(), 5000);
  try {
    if (url.origin !== location.origin || url.username || url.password || url.hash) throw Error('feed_origin');
    feed = await readFeed(url.href, {signal:controller.signal}); if (!disposed) check();
  } catch { if (!disposed) clear(); }
  finally { clearTimeout(timeout); }
  return () => { disposed = true; controller.abort(); clearTimeout(timer); clear();
    document.removeEventListener('visibilitychange', onVisibility); window.removeEventListener('pageshow', check); };
}
