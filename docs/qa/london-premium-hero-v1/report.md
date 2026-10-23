# London Premium Hero V1 — rapport de validation

Branche : `feat/london-premium-hero-v1`. Worktree : `C:/Users/1995/AppData/Local/Temp/tripguidely-london-premium-hero-v1`. Base : `ba230ddfae87a14f78057070350f37b6b3268ba5`, dernier `origin/main` récupéré le 22 octobre 2026 (PR #56). Le checkout Disney et les autres worktrees sont restés intacts. Le propriétaire a explicitement autorisé les quatre changements sociaux exacts, les quatre entrées du baseline, le commit, le push de cette branche et une PR Draft vers main. Aucun merge ou déploiement manuel autorisé.

**Verdict : GO.** Les quatre Hero et leurs métadonnées sociales sont finalisés. Les empreintes avant/après approuvées ont été vérifiées avant application. Le baseline contient exactement quatre nouvelles autorisations et conserve ses 41 autorisations historiques. Aucun défaut technique nouveau détecté.

## Images

Originaux PNG intacts dans Downloads, hors Git. Inspection visuelle des quatre sources, vérification PNG et décodage intégral. SHA-256 sources et fichiers produits dans [images.json](images.json). Les scènes illustrent une ambiance ; elles ne sont jamais attribuées à un établissement réel.

| Page | Original PNG | Dimensions natives |
|---|---|---|
| Hub | `where-to-stay-in-london-westminster-skyline.png` | 1672 × 941 |
| Luxury | `luxury-hotels-in-london-elegant-hotel-interior.png` | 1672 × 941 |
| Family | `family-hotels-in-london-spacious-aparthotel.png` | 1942 × 809 |
| Cheap | `cheap-hotels-in-london-budget-accommodation.png` | 1774 × 887 |

Dossier final : `assets/images/hero/london/`. Chaque fichier conserve le nom de base exact de son original, suivi de `-<largeur>.avif` ou `-<largeur>.webp` (ex. `family-hotels-in-london-spacious-aparthotel-960.avif`). Les 26 noms complets, dimensions, octets et empreintes sont dans l’inventaire. Poids ci-dessous en Ko décimaux (1 Ko = 1 000 octets).

| Page | Variante | Dimensions exactes | AVIF (Ko) | WebP (Ko) |
|---|---:|---|---:|---:|
| Hub | 640 | 640 × 360 | 36.0 | 51.7 |
| Hub | 960 | 960 × 540 | 73.7 | 103.1 |
| Hub | 1440 | 1440 × 810 | 138.5 | 199.7 |
| Hub | 1672 | 1672 × 941 | 172.4 | 247.4 |
| Luxury | 640 | 640 × 360 | 39.4 | 58.9 |
| Luxury | 960 | 960 × 540 | 79.4 | 114.6 |
| Luxury | 1440 | 1440 × 810 | 143.4 | 209.0 |
| Family | 640 | 640 × 267 | 24.5 | 35.4 |
| Family | 960 | 960 × 400 | 46.7 | 67.9 |
| Family | 1440 | 1440 × 600 | 91.7 | 134.1 |
| Cheap | 640 | 640 × 320 | 26.4 | 37.8 |
| Cheap | 960 | 960 × 480 | 51.0 | 71.8 |
| Cheap | 1440 | 1440 × 720 | 95.2 | 133.7 |

Encodage temporaire avec Pillow 12.3.0 : AVIF qualité 65, vitesse 6, sous-échantillonnage 4:4:4 ; WebP qualité 84, méthode 6. Redimensionnement Lanczos, aucun filtre esthétique, recadrage ou upscaling. La hauteur est arrondie au pixel le plus proche. Les 26 variantes se décodent et correspondent aux dimensions annoncées. AVIF et WebP ont été inspectés visuellement sans artefact gênant. Aucune dépendance ajoutée au site.

Catégories : image complète à ratio naturel, `height:auto` et `object-fit:contain`. Composition texte / image sur desktop ; image après les CTA sur mobile et tablette ≤ 900 px. L’encadré conserve ses conseils utiles et indique que le visuel est une illustration générée. Aucun recadrage.

Hub : interface, H1, sous-titre, liens et boutons conservés. Desktop : `object-fit:cover`, `object-position:70% 50%`, largeur plafonnée à 1672 px ; léger recadrage vertical selon la largeur, tour de l’horloge conservée à droite. Overlay pour le contraste. Mobile ≤ 760 px : panorama intégral au-dessus des contrôles, à ratio naturel ; aucun recadrage agressif.

`picture` AVIF prioritaire, `img` WebP avec `srcset`, `sizes`, dimensions natives, `loading=eager`, `decoding=async` et `fetchpriority=high`. Aucun préchargement d’image, aucun nouveau JavaScript. Le vrai candidat LCP mesuré est l’image sur les quatre pages. ALT descriptifs pour les catégories ; ALT vide et `aria-hidden` pour le panorama décoratif du hub.

## Qualité et mesures

Chrome local, vues de 390/768/1440/1920 px ; DPR 2 pour 390/768, DPR 1 pour 1440/1920 ; hauteur 1000 px. Une comparaison avant/après par page à 390/768/1440, sans ralentissement réseau/CPU ; services tiers bloqués pour ces mesures. Ces mesures de laboratoire servent de comparaison locale, sans promesse sur les Core Web Vitals réels, INP ou les classements Google.

| Page | Largeur | LCP avant → après (ms) | CLS avant → après | Fichier choisi | Hero (Ko) | Ressources locales (Ko) |
|---|---:|---:|---|---|---:|---:|
| hub | 390 | 688 → 272 | 0.0650 → 0.0650 | `…-960.avif` | 73.7 | 510.4 |
| hub | 768 | 324 → 300 | 0.1195 → 0.1195 | `…-1672.avif` | 172.4 | 701.7 |
| hub | 1440 | 296 → 296 | 0.0535 → 0.0535 | `…-1440.avif` | 138.5 | 445.6 |
| hub | 1920 | — → 280 | — → 0.0401 | `…-1672.avif` | 172.4 | 479.5 |
| luxury | 390 | 232 → 196 | 0.0000 → 0.0000 | `…-960.avif` | 79.4 | 299.1 |
| luxury | 768 | 244 → 176 | 0.0422 → 0.0422 | `…-1440.avif` | 143.4 | 363.0 |
| luxury | 1440 | 276 → 208 | 0.0000 → 0.0000 | `…-640.avif` | 39.4 | 259.1 |
| luxury | 1920 | — → 176 | — → 0.0000 | `…-640.avif` | 39.4 | 259.1 |
| family | 390 | 260 → 188 | 0.0000 → 0.0000 | `…-960.avif` | 46.7 | 266.4 |
| family | 768 | 240 → 156 | 0.0422 → 0.0422 | `…-1440.avif` | 91.7 | 311.4 |
| family | 1440 | 276 → 192 | 0.0000 → 0.0000 | `…-640.avif` | 24.5 | 244.2 |
| family | 1920 | — → 200 | — → 0.0000 | `…-640.avif` | 24.5 | 244.2 |
| cheap | 390 | 292 → 272 | 0.0000 → 0.0000 | `…-960.avif` | 51.0 | 270.7 |
| cheap | 768 | 244 → 164 | 0.0422 → 0.0422 | `…-1440.avif` | 95.2 | 314.9 |
| cheap | 1440 | 296 → 176 | 0.0000 → 0.0000 | `…-640.avif` | 26.4 | 246.1 |
| cheap | 1920 | — → 172 | — → 0.0000 | `…-640.avif` | 26.4 | 246.1 |

La dernière colonne additionne les corps des sous-ressources téléchargées pendant la fenêtre initiale ; elle exclut le document HTML principal, les en-têtes HTTP, les tiers bloqués et les téléchargements après défilement. Ce n’est pas une estimation du poids réseau complet en production. La colonne Hero donne les octets réels du corps d’image reçu.

Le CLS existant du hub à 768 px reste 0,1195 ; les autres déplacements du hub et ceux des catégories à 768 px sont également identiques à la base. Les sources de déplacement sont le contenu principal lors de l’injection du header existant. Aucun déplacement supplémentaire attribuable aux nouvelles images. Ce problème préexistant du header n’a pas été modifié hors périmètre.

16 vues finales : aucun débordement horizontal, aucun chevauchement constaté, images nettes et proportions respectées, CTA d’au moins 44 px, clavier et contour de focus contrôlés. Axe WCAG 2 A/AA et 2.1 AA ciblé sur les Hero : zéro violation détectée après correction d’une couleur héritée. Cela ne constitue pas un audit d’accessibilité de tout le site. Une seule variante Hero téléchargée par page. Repli WebP testé séparément par retrait du source AVIF dans la réponse de test : un seul WebP 960 px chargé sur chaque page à 390 px / DPR 2.

Les huit captures nécessaires ont été revues ; consentement décliné dans le navigateur de test avant capture pour voir les Hero en entier :

- hub : [mobile 390 px](hub-390.png), [desktop 1440 px](hub-1440.png).
- luxury : [mobile 390 px](luxury-390.png), [desktop 1440 px](luxury-1440.png).
- family : [mobile 390 px](family-390.png), [desktop 1440 px](family-1440.png).
- cheap : [mobile 390 px](cheap-390.png), [desktop 1440 px](cheap-1440.png).

Données : [responsive.json](responsive.json), [interactions.json](interactions.json). Les tests de cartes utilisent séparément une vue tactile 390 × 844 et de vraies tuiles OpenStreetMap.

## Préservation

- Les neuf URL Klook / SubIDs sont exactement conservés ; tous les liens des quatre pages sont inchangés. Inventaire exact dans [preservation.json](preservation.json).
- Les 27 photographies réelles, leurs blocs HTML et leurs 108 variantes restent inchangés.
- H1, introductions, comparatifs, itinéraires internes et scripts fonctionnels sont conservés. Seuls les champs sociaux d’image approuvés et les références d’image JSON-LD nécessaires du hub changent. Titles SEO, descriptions, canonical, hreflang, CSP et consentement inchangés.
- Trois cartes en état `ready`, trois choix par carte, sélection synchronisée avec les panneaux, marqueurs au clavier et verrouillage tactile vérifiés.
- Tracking local : aucun `affiliate_click` avec consentement refusé ; exactement trois événements de fiches et un événement de carte par page avec consentement accordé. Aucun lien affilié réellement ouvert.
- `site.js` et `london-hotel-map.js` sont identiques à la base. Le baseline ne reçoit que les quatre autorisations approuvées ; ses autres données sont inchangées. Aucune modification sur Paris, Rome, New York, les autres destinations ou PR #49.

## Audit et fichiers

**Audit officiel : PASS, zéro erreur nouvelle**, exécuté une seule fois après les dernières modifications de code : `python -B scripts/audit-site.py --base-ref ba230ddfae87a14f78057070350f37b6b3268ba5 --json`. [Résultat intégral](official-audit.json). Les constats historiques couverts par le baseline restent présents ; ce PASS ne signifie pas que l’ensemble du site est exempt de défauts historiques. `git diff --check` : PASS.

Fichiers de code et de politique modifiés :

- `hotels/london/index.html`
- `hotels/london/luxury-hotels/index.html`
- `hotels/london/family-hotels/index.html`
- `hotels/london/cheap-hotels/index.html`
- `assets/css/pages/london-hotels.css`
- `tests/fixtures/site-baseline.json` (quatre autorisations exactes uniquement)

Ajouts : 26 images dans `assets/images/hero/london/` ; ce rapport, huit captures, les inventaires et preuves JSON ainsi que le patch social dans `docs/qa/london-premium-hero-v1/`. Aucun original PNG ajouté au dépôt.

## Autorisation appliquée : images sociales

Le propriétaire a explicitement approuvé les quatre tuples ci-dessous dans « Final Approval · Social Metadata · Baseline · Draft PR ». Avant application, la version courante et le patch ont été comparés aux empreintes exactes approuvées ; aucun écart. Le [patch approuvé et appliqué](social-images-proposed.patch), validé par `git apply --check`, remplace uniquement les images / ALT sociaux et annonce leurs dimensions naturelles exactes ; pour le hub il actualise aussi les deux références d’image JSON-LD. Les fichiers WebP 1440 px déjà générés servent aux aperçus ; aucun nouveau recadrage social. Titles, descriptions, canonical et hreflang restent inchangés.

Les empreintes ci-dessous sont calculées avec les fonctions `Document` et `digest` de l’auditeur du projet, selon son contrat `seo_metadata`. Elles correspondent exactement au patch appliqué après l’accord explicite du propriétaire. Seules les quatre entrées correspondantes ont été ajoutées au baseline. [JSON exact](pending-authorizations.json).

```json
[
  {
    "kind": "seo_metadata",
    "source": "hotels/london/index.html",
    "base_revision": "ba230ddfae87a14f78057070350f37b6b3268ba5",
    "before": "eef06c27f00ef7841b9fabd7018e7fd27898d059a6983f466fae89db22c3ee0b",
    "after": "edf09bd32b395d901429ad450d278832704c4260dff2f5e9fcf1942081f81aef"
  },
  {
    "kind": "seo_metadata",
    "source": "hotels/london/luxury-hotels/index.html",
    "base_revision": "ba230ddfae87a14f78057070350f37b6b3268ba5",
    "before": "b640ea6bef2b5dd57585f26b3c6ac1aa78309a65fdfc73c678669b9cf1173b09",
    "after": "33f81c2ae1c46bb5d1db2d269be4728dfedc742be4b5840bc95c8e38b078163c"
  },
  {
    "kind": "seo_metadata",
    "source": "hotels/london/family-hotels/index.html",
    "base_revision": "ba230ddfae87a14f78057070350f37b6b3268ba5",
    "before": "f91959e3744f474f4a66ef454334d2e895be52ecae4dc12edb951b967e6a2f95",
    "after": "aff37676607c07b1e9d53d865383eb0366ba77b94ef74b05aea0bc2df3a49a68"
  },
  {
    "kind": "seo_metadata",
    "source": "hotels/london/cheap-hotels/index.html",
    "base_revision": "ba230ddfae87a14f78057070350f37b6b3268ba5",
    "before": "f9a3a256ca367374440c4cf827cd9ddb434942c8cdcbe7181cc3d690c3e415cd",
    "after": "c3a48570f96d0e7c6f55866d40139f2d490c1d4e9f935b32f1c8bce23095a86c"
  }
]
```

Les quatre images sociales sont les WebP 1440 px réellement présents : hub 1440 × 810, luxury 1440 × 810, family 1440 × 600, cheap 1440 × 720. Leur intégrité et les 26 variantes Hero ont été vérifiées par décodage et SHA-256 ; chaque page utilise son bon Hero. Preuves : [final-approval-verification.json](final-approval-verification.json). Les validations responsive et cartographiques précédentes n’ont pas été relancées, aucun code fonctionnel n’ayant changé pendant cette finalisation. Aucun merge ni déploiement manuel.
