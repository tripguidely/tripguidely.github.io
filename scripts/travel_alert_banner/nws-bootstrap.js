/* Future page bootstrap, currently served only by the local qualification preview. */
import {mountBanner,isLoopback} from './banner.js';
const routes = ['/car-rental/new-york/','/hotels/new-york/','/hotels/new-york/cheap-hotels/',
 '/hotels/new-york/family-hotels/','/hotels/new-york/luxury-hotels/','/itinerary/new-york/',
 '/itinerary/new-york/2-days/','/itinerary/new-york/3-days/','/itinerary/new-york/4-days/',
 '/itinerary/new-york/first-time/','/itinerary/new-york/rainy-day/','/things-to-do/new-york/'];
const host=document.getElementById('destination-nws-advisory');
if (host && routes.includes(location.pathname)) {
 const local=isLoopback(location.hostname);
 const feedUrl=local && host.dataset.previewFeed ? host.dataset.previewFeed : '/travel-alerts/nws-nyc.json';
 let cleanup=()=>{},pending=false,timer=null,lastAttempt=0;
 async function refresh() {
  clearTimeout(timer);
  if (pending || document.hidden) return;
  if (Date.now()-lastAttempt < 30000) { timer=setTimeout(refresh,30000); return; }
  pending=true;lastAttempt=Date.now();cleanup();
  try { cleanup=await mountBanner(host,{feedUrl,destination:'us-new-york-city',country:'US',demo:local}); }
  finally { pending=false;host.dataset.nwsReady='true';timer=setTimeout(refresh,300000); }
 }
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});
 window.addEventListener('pageshow',()=>refresh());
 window.addEventListener('pagehide',()=>{clearTimeout(timer);cleanup();});
 refresh();
}
