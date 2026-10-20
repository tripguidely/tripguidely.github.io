# Rome hotel hub and guides V1 — local review

- Branch: `feat/rome-hotel-guides-v1`; base: `5c02894cb346e5d5efc8c8531ea062b1fbf77364`.
- Owner authorized the Rome-only commit, push and Draft PR after exact baseline approval. No merge or deployment authorized. Auditor, shared JavaScript, other city pages and PR #49 untouched.
- Verdict: **GO for Draft PR**: the one exact owner-approved SEO authorization is applied locally. Official audit passes with zero errors.

## Pages and behavior

| Page | Changes |
| --- | --- |
| `/hotels/rome/` | Original area content, H1, complete original anchors, scripts, JSON-LD and existing two Klook links retained. New guide navigation and three photo previews; mobile neighborhood comparison retained with no sideways scroll. Title/description and matching social text updated. |
| `/hotels/rome/luxury-hotels/` | Three quick choices, accessible comparison, three property cards, category-specific booking checks and FAQs. Hotel Manfredi identified as the Via Margutta property, not Palazzo Manfredi. |
| `/hotels/rome/family-hotels/` | Three choices with occupancy and bed caveats. Adagio kitchen/category and Balduina location distinguished; no unverified four-person Michelangelo claim. Both supplied Adagio photos included. |
| `/hotels/rome/cheap-hotels/` | Private-room versus dorm-bed comparisons, arrival and total-cost checks, Sonya main/annex distinction. Sonya photo labeled as Opera House surroundings. |

New guides use a scoped cream/clay/olive design, shared header/footer and existing site.js. No new tracking system, JavaScript library, interactive map or third-party embed. The existing hub Drive integration remains unchanged; no Drive script added to new guides. Three new canonical URLs added to `sitemap-rome.xml` without altering existing entries.

## Nine exact commercial mappings

| Hotel | Supplied Klook URL | SubID / offer_id |
| --- | --- | --- |
| Hotel de Russie | https://klook.tpk.ro/EhpVKmPP | `rome_luxury_de_russie` |
| Hotel Eden | https://klook.tpk.ro/SDLGFYxA | `rome_luxury_eden` |
| Hotel Manfredi Suite in Rome | https://klook.tpk.ro/zPDNGWTg | `rome_luxury_manfredi` |
| Hotel Quirinale | https://klook.tpk.ro/vcSdop54 | `rome_family_quirinale` |
| Starhotels Michelangelo | https://klook.tpk.ro/bFtOh2pO | `rome_family_michelangelo` |
| Aparthotel Adagio Rome Vatican | https://klook.tpk.ro/a5kPTk1Q | `rome_family_adagio_vatican` |
| The Beehive | https://klook.tpk.ro/aRiWjt7I | `rome_cheap_beehive` |
| Hotel Sonya | https://klook.tpk.ro/cKrHWayp | `rome_cheap_sonya` |
| Generator Rome | https://klook.tpk.ro/dUIajjoc | `rome_cheap_generator` |

One CTA per hotel, before detailed room facts. `data-cta-id` is `<SubID>_hotel_card`, location `hotel_card`, program `klook`; target `_blank`, rel `nofollow sponsored noopener`. Existing hub link `https://klook.tpk.ro/rtJMmDia`, SubID `rome_hotels`, preserved twice exactly. No clickable official hotel booking/source links in new guides; official URLs remain in the source register and schema identity references. Practical ATAC and internal itinerary/transport links retained.

**Not verified:** short-link final property routing, partner account attribution, embedded Travelpayouts SubIDs, conversions, bookings or commissions. HTML data-subid is not proof of the server-side short-link configuration. No live test affiliate clicks made. GA4 custom event generation was tested against a stub; actual GA4 receipt was not observed.

## Ten supplied photographs

All ten original downloads decoded successfully and remain intact outside Git. Source URLs, download SHA-256, dimensions, exact supplied hotel association, source format, generated asset SHA-256 and factual sources are preserved in `docs/qa/rome-hotels-sources.json`.

Processing: full-frame proportional LANCZOS resize to 480w/960w; rounded integer height, no crop, retouch, upscale or composition change. WebP quality 86/method 6; AVIF quality 65/speed 6. AVIF source with WebP fallback, responsive srcset/sizes, explicit intrinsic dimensions, descriptive alt and lazy/async/low-priority loading below the hero. CSS object-fit: contain. Originals and temporary converters are not included in Git.

| Hotel / photo | Original | Optimized dimensions (480w / 960w) | WebP KiB (480 / 960) | AVIF KiB (480 / 960) |
| --- | --- | --- | --- | --- |
| Hotel de Russie | JPEG 1920×1279 | 480×320 / 960×640 | 59.8 / 219.3 | 35.2 / 128.3 |
| Hotel Eden | WEBP 1680×1194 | 480×341 / 960×682 | 31.8 / 81.1 | 20.3 / 52.6 |
| Hotel Manfredi Suite in Rome | WEBP 1680×954 | 480×273 / 960×545 | 36.1 / 100.3 | 23.8 / 70.3 |
| Hotel Quirinale | JPEG 1920×1440 | 480×360 / 960×720 | 68.2 / 251.7 | 40.8 / 151.9 |
| Starhotels Michelangelo | WEBP 1680×1121 | 480×320 / 960×641 | 19.5 / 51.8 | 13.8 / 38.0 |
| Aparthotel Adagio Rome Vatican | WEBP 1680×1121 | 480×320 / 960×641 | 26.2 / 75.5 | 16.7 / 48.5 |
| Aparthotel Adagio Rome Vatican — pool | JPEG 1920×1440 | 480×360 / 960×720 | 50.8 / 172.0 | 30.2 / 100.3 |
| The Beehive | WEBP 1680×1121 | 480×320 / 960×641 | 16.1 / 38.6 | 11.5 / 29.5 |
| Hotel Sonya | WEBP 1680×1121 | 480×320 / 960×641 | 33.0 / 87.9 | 21.0 / 57.6 |
| Generator Rome | WEBP 1680×1121 | 480×320 / 960×641 | 45.1 / 121.9 | 27.4 / 71.8 |

40 generated assets total: 2,638,142 bytes (2.52 MiB); a visitor loads responsive selected variants, not all forty. Ten pictures across three guides; three existing variants reused in hub previews.

Photo association limits: these are the exact owner-supplied files and hotel assignments. Visual inspection and file integrity were verified; every specific interior photo was not independently matched to a live property gallery. Hotel Sonya is an area photo, not its facade or a promised view. Pool imagery does not establish seasonal access. No new permission or license has been inferred from prior Paris practices. Publication requires owner review.

## Fact-sensitive checks

- Hotel Manfredi Suite in Rome: Via Margutta 61, near the Spanish Steps; distinguish Palazzo Manfredi by the Colosseum.
- Quirinale: official Standard/Superior table up to three; Junior Suite up to four. Actual additional beds and connecting arrangements still require confirmation.
- Michelangelo: current official room list shows one/two-person categories. Group-wide family program is not proof of a four-person room at this property; exact family arrangement requires confirmation.
- Adagio: apartment kitchens and a named apartment for four are documented. The hotel-room category must not inherit these assumptions; Balduina requires journey planning.
- Beehive: private/shared and bathroom/AC arrangements differ; arrival reception and group-size rules included.
- Sonya main/annex categories and Generator private-room/dorm distinction retained; no rates, ratings, availability or personal-stay claims fabricated.

Official source URLs and review dates are in the source register; no direct hotel booking anchors added to pages.

## Validation

- Targeted offline Chrome suite: **2576 assertions passed**, 24 page/width views (320, 390, 641, 760, 900, 1440 px).
- Additional focused checks: 24 keyboard assertions passed across three guides (skip link/main focus, native details, Enter CTA); all 40 AVIF/WebP assets independently decoded at their recorded dimensions; original ten SHA-256 files unchanged.
- Eight main-content axe WCAG A/AA runs at 390/1440 px: zero violations. Not an exhaustive accessibility certification of the shared site.
- All nine exact URL/SubID pairs, two original hub anchors, internal destinations/fragments, canonical/schema, photo decoding/aspect ratio, asset integrity, touch-sized CTAs and no-JS links checked.
- Consent unknown/refused: zero affiliate_click; granted: exactly one per activation. Reinitializing unchanged site.js creates no duplicate. Empty/same-page href cannot register as successful outbound affiliate activation. No external partner/analytics requests allowed in the harness.
- Before approval: official audit identified only the expected seo_metadata contract change. After explicit approval: official audit run once, PASS, zero errors, one exact authorization recognized; 956 unchanged historical findings and 48 resolved fixture findings. Historic findings are not a new clean-site certification.
- Baseline: exactly one owner-approved seo_metadata entry appended; all 31 historic authorizations and all other records preserved. Auditor unchanged. Existing Paris/NY suites not repeated because their files and shared scripts are unchanged. The Rome test now checks the exact approved baseline delta; only its static checks were repeated. The 2,576 browser assertions and 24 keyboard checks were not repeated because functional code and images are unchanged.
- Browser screenshots: external QA directory `browser/`: heroes, quick choices, comparisons and first hotel cards desktop/mobile; Adagio both-photo card also captured.
- Lighthouse, field CWV, live GA4 receipt, partner attribution and production network behavior were not measured. Local layout/image checks do not establish field performance.

## Exact owner-approved authorization

```json
{
  "kind": "seo_metadata",
  "source": "hotels/rome/index.html",
  "base_revision": "5c02894cb346e5d5efc8c8531ea062b1fbf77364",
  "before": "dbcd1fffad79c3390a15986b68a962d214a48d87eb4ee103e29f8cf6c5860457",
  "after": "2f3e6aed1c3ba57b08e575d2d2ef670d23cd4c9451e04686bf022aaa99d35c1e",
  "reason": "Owner explicitly approved the exact Rome hub SEO metadata transition in TRIPGUIDELY — ROME : APPROBATION SEO ET CRÉATION PR. Only the title, description and matching social title/description change; preserve canonical, hreflang, original JSON-LD, affiliate anchors and integrations.",
  "reviewed_by": "owner instruction: TRIPGUIDELY — ROME : APPROBATION SEO ET CRÉATION PR (Codex conversation, 2026-10-20)",
  "recorded_on": "2026-10-20"
}
```

This authorizes only the hub metadata fingerprint transition at this base. It is not a whole-file whitelist or approval for affiliate/script changes. It was applied to the baseline only after exact owner approval.

## Remaining steps

1. Prepare the authorized Rome-only commit and Draft PR; no merge or deployment.
2. Verify Rome short-link property destinations and account-side SubIDs in Travelpayouts without treating redirects or HTML attributes as commission proof. In particular check the Via Margutta Manfredi identity.
3. Review GitHub Actions and the Draft PR before any merge. Baseline approval, local official audit, and commit/push/Draft PR authorization are recorded in the owner conversation.
4. After authorized publication: check mobile booking hrefs on the hub because its existing Drive script remains; verify actual GA4 receipts with consent and observe partner reports. This change does not resolve Drive behavior or alter PR #49.

## Exact changed-file inventory

- `assets/css/pages/rome-hotels.css`
- `assets/images/hotels/rome/adagio-rome-vatican-exterior-480x320.avif`
- `assets/images/hotels/rome/adagio-rome-vatican-exterior-480x320.webp`
- `assets/images/hotels/rome/adagio-rome-vatican-exterior-960x641.avif`
- `assets/images/hotels/rome/adagio-rome-vatican-exterior-960x641.webp`
- `assets/images/hotels/rome/adagio-rome-vatican-pool-480x360.avif`
- `assets/images/hotels/rome/adagio-rome-vatican-pool-480x360.webp`
- `assets/images/hotels/rome/adagio-rome-vatican-pool-960x720.avif`
- `assets/images/hotels/rome/adagio-rome-vatican-pool-960x720.webp`
- `assets/images/hotels/rome/generator-rome-exterior-480x320.avif`
- `assets/images/hotels/rome/generator-rome-exterior-480x320.webp`
- `assets/images/hotels/rome/generator-rome-exterior-960x641.avif`
- `assets/images/hotels/rome/generator-rome-exterior-960x641.webp`
- `assets/images/hotels/rome/hotel-de-russie-rome-garden-480x320.avif`
- `assets/images/hotels/rome/hotel-de-russie-rome-garden-480x320.webp`
- `assets/images/hotels/rome/hotel-de-russie-rome-garden-960x640.avif`
- `assets/images/hotels/rome/hotel-de-russie-rome-garden-960x640.webp`
- `assets/images/hotels/rome/hotel-eden-rome-exterior-480x341.avif`
- `assets/images/hotels/rome/hotel-eden-rome-exterior-480x341.webp`
- `assets/images/hotels/rome/hotel-eden-rome-exterior-960x682.avif`
- `assets/images/hotels/rome/hotel-eden-rome-exterior-960x682.webp`
- `assets/images/hotels/rome/hotel-manfredi-suite-rome-room-480x273.avif`
- `assets/images/hotels/rome/hotel-manfredi-suite-rome-room-480x273.webp`
- `assets/images/hotels/rome/hotel-manfredi-suite-rome-room-960x545.avif`
- `assets/images/hotels/rome/hotel-manfredi-suite-rome-room-960x545.webp`
- `assets/images/hotels/rome/hotel-quirinale-rome-garden-480x360.avif`
- `assets/images/hotels/rome/hotel-quirinale-rome-garden-480x360.webp`
- `assets/images/hotels/rome/hotel-quirinale-rome-garden-960x720.avif`
- `assets/images/hotels/rome/hotel-quirinale-rome-garden-960x720.webp`
- `assets/images/hotels/rome/hotel-sonya-rome-opera-surroundings-480x320.avif`
- `assets/images/hotels/rome/hotel-sonya-rome-opera-surroundings-480x320.webp`
- `assets/images/hotels/rome/hotel-sonya-rome-opera-surroundings-960x641.avif`
- `assets/images/hotels/rome/hotel-sonya-rome-opera-surroundings-960x641.webp`
- `assets/images/hotels/rome/starhotels-michelangelo-rome-room-480x320.avif`
- `assets/images/hotels/rome/starhotels-michelangelo-rome-room-480x320.webp`
- `assets/images/hotels/rome/starhotels-michelangelo-rome-room-960x641.avif`
- `assets/images/hotels/rome/starhotels-michelangelo-rome-room-960x641.webp`
- `assets/images/hotels/rome/the-beehive-rome-private-room-480x320.avif`
- `assets/images/hotels/rome/the-beehive-rome-private-room-480x320.webp`
- `assets/images/hotels/rome/the-beehive-rome-private-room-960x641.avif`
- `assets/images/hotels/rome/the-beehive-rome-private-room-960x641.webp`
- `docs/qa/rome-hotels-pending-authorizations.json`
- `docs/qa/rome-hotels-sources.json`
- `docs/rome-hotel-guides-v1.md`
- `hotels/rome/cheap-hotels/index.html`
- `hotels/rome/family-hotels/index.html`
- `hotels/rome/index.html`
- `hotels/rome/luxury-hotels/index.html`
- `sitemap-rome.xml`
- `tests/fixtures/site-baseline.json`
- `tests/test_rome_hotels.cjs`
