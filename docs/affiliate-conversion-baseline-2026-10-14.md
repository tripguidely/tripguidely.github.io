# TripGuidely — affiliate conversion baseline

Date: 2026-10-14. Scope: repository code inspection. This is **not** a claim about actual GA4, GSC, partner conversions, or revenue.

## Confirmed implementation
- `index.html` includes a Travelpayouts script.
- `assets/js/site.js` defines GA4 measurement ID `G-0GGMM5GYXJ`, Consent Mode v2, and consent-gated loading.
- The code emits `outbound_click` for external anchor clicks after analytics consent.
- The code emits `affiliate_click` only when the clicked anchor has class `js-aff` and analytics consent is granted.
- Affiliate events include program, page type, destination and beacon transport. Hotel links can include hotel ID, placement, experiment variant and page path when corresponding data attributes exist.

## Commercial audit priorities (not yet verified)
1. Inventory all affiliate destinations and identify monetizable CTAs missing `js-aff`; check dynamically injected links/widgets separately.
2. Check GA4 event delivery in a consented browser session, without bypassing consent. Compare `affiliate_click` and `outbound_click` to avoid double-counting.
3. Query real GSC page/query data to select three pages with commercial intent and meaningful impressions; never select by invented traffic.
4. For those pages, map offer availability, CTA placement, destination validity, and event attribution. Propose targeted PRs.
5. Establish weekly baseline of organic landing-page sessions, affiliate clicks, partner bookings, commission and EPC where accessible. GA4 clicks alone are not confirmed sales.

## Release guardrails
- Do not alter consent behavior or add tracking before consent.
- Do not modify `main` or merge automatically; request user merge after tests.
- Validate link destinations, JavaScript syntax and affected pages before recommending merge.
- This document changes no live page behavior.
