# Paris Luxury Hotels — revue UX/CRO locale

État : commit, push et PR vers main autorisés par le propriétaire le 12 octobre
2026, après intégration de main et validation. Attendre GitHub Actions, puis
STOP pour validation humaine. Aucun merge ni déploiement autorisé.
Worktree : `C:/Users/1995/tripguidely-luxury-ux-cro`.
Branche : `feat/paris-luxury-ux-cro`.
Base initiale : `421e6652744e6793347103a09e9ccbb879abfd01`.
Base intégrée pour la PR : `9d3301f0ffff927ba796d7f33e06e3031fb319a2`
(main après fusion de Cheap Hotels PR #34).
Recherche : 11 octobre 2026 ; validation achevée le 12 octobre 2026,
America/Toronto. La date de revue visible et les deux `dateModified` reflètent
la recherche du 11 octobre, sans prétendre que la page a été publiée.

## Résultat UX/CRO

Les trois hôtels de luxe gardent leur shortlist ; Pullman Paris Tour Eiffel
reste une alternative premium distincte, y compris sur la carte et dans le
tableau. Les fiches présentent quartier, adresse, catégories publiées,
services, avantages et points à vérifier. Les détails supplémentaires se
déplient avec un contrôle HTML natif. Les CTA du hero mènent à la comparaison
et à la carte. La palette crème/bordeaux et les accents discrets restent
limités à cette page ; les boutons gardent l'identité TripGuidely.

La carte est ouverte automatiquement. Le petit script prépare le sélecteur
et la première fiche ; Leaflet et les tuiles ne sont demandés qu'à moins de
250 pixels du viewport. Quatre épingles numérotées correspondent aux fiches.
La fiche sélectionnée donne l'adresse et un CTA Klook immédiatement, puis
les catégories, services, avantages, limites et questions dans les détails
dépliables. Le CTA précède ces détails pour rester facile à retrouver.

Les quatre liens Klook originaux sont conservés à l'identique, et la carte
clone ces mêmes ancres avec tous leurs attributs : URL, SubID, `data-aff`,
classes, `rel`, `target` et nom accessible. Aucun ID Klook ou attribut de
tracking n'est inventé. Le payload GA4 hérité reste inchangé et soumis au
consentement ; aucune mesure n'est déclenchée par l'ouverture ou la sélection
de la carte. La divulgation d'affiliation reste unique et visible avant les
fiches, sans note répétée sous les boutons.

## Vérification des établissements et positions

Les sites officiels confirment les quatre identités et adresses. Les catégories
publiées ne prouvent ni disponibilité Klook, ni inclusion dans une offre.
Les avantages et compromis sont des appréciations éditoriales du lieu et du
format, pas des comptes rendus de séjours personnels.

| Établissement | Adresse officielle | Latitude | Longitude | IGN/BAN : score et type |
| --- | --- | --- | --- | --- |
| Le Meurice | 228 rue de Rivoli, 75001 Paris | 48.865194 | 2.328101 | 0.970431 ; housenumber |
| Mandarin Oriental Lutetia, Paris | 45 boulevard Raspail, 75006 Paris | 48.85117 | 2.327156 | 0.972959 ; housenumber |
| Shangri-La Paris | 10 avenue d'Iéna, 75116 Paris | 48.863783 | 2.293219 | 0.978292 ; housenumber |
| Pullman Paris Tour Eiffel | 18 avenue de Suffren ; entrée au 22 rue Jean Rey, 75015 Paris | 48.855371 | 2.292365 | 0.975669 ; housenumber, entrée rue Jean Rey |

Points d'adresse géocodés, pas relevés d'entrées accessibles. Les coordonnées
GeoJSON longitude/latitude sont inversées pour Leaflet latitude/longitude.
La première requête Iéna utilisait 75016 : elle a été corroborée par une
requête exacte avec 75116 et l'apostrophe/accent, donnant le même point avec
un meilleur score. Les deux réponses sont conservées dans le dossier QA.

Sources officielles consultées :

- [Le Meurice](https://www.dorchestercollection.com/paris/le-meurice) : identité,
  adresse, catégories de chambres et suites, vues nommées, Valmont, gym et restauration.
- [Lutetia : hébergement](https://www.mandarinoriental.com/en/paris/lutetia/stay),
  [bien-être](https://www.mandarinoriental.com/en/paris/lutetia/wellness) et
  [contact](https://www.mandarinoriental.com/en/paris/lutetia/contact-us) : identité,
  adresse, formats, piscine de 17 m, fitness et conditions des jeunes hôtes,
  Brasserie Lutetia et Bar Joséphine.
- [Shangri-La](https://www.shangri-la.com/paris/shangrila/),
  [adresse](https://www.shangri-la.com/paris/shangrila/about/map-directions/),
  [services](https://www.shangri-la.com/paris/shangrila/about/services-facilities/) et
  [health club](https://www.shangri-la.com/paris/shangrila/health-leisure/health-club/) :
  catégories Eiffel View/Terrace Eiffel View et suites duplex, spa, piscine,
  fitness, room service et transferts.
- [Pullman officiel](https://pullman.accor.com/en/hotels/paris/7229.html) : adresse
  et entrée, Classic Garden View, Superior Eiffel Tower View, Deluxe balcon et
  distinction des étages, suites, fitness, restauration et connexions de transport.
- Géocodage officiel gratuit IGN/BAN :
  [228 rue de Rivoli](https://data.geopf.fr/geocodage/search?q=228%20rue%20de%20Rivoli%2075001%20Paris&limit=1),
  [45 boulevard Raspail](https://data.geopf.fr/geocodage/search?q=45%20boulevard%20Raspail%2075006%20Paris&limit=1),
  [10 avenue d'Iéna](https://data.geopf.fr/geocodage/search?q=10%20avenue%20d%27I%C3%A9na%2075116%20Paris&limit=1),
  [22 rue Jean Rey](https://data.geopf.fr/geocodage/search?q=22%20rue%20Jean%20Rey%2075015%20Paris&limit=1).

## Accessibilité, performance et services externes

Contrôles et épingles de 44 px minimum, sélection annoncée avec `aria-pressed`,
focus transmis au titre de la fiche, régions nommées, statut `aria-live`,
réduction des animations et contraste forcé. La comparaison conserve tableau,
caption, en-têtes et région défilable au clavier. Sur écran tactile, le glissement
à un doigt permet de faire défiler la page ; les contrôles et le zoom par pincement
restent disponibles. Le déplacement au clavier reste possible.

Échec des tuiles : épingles, sélecteur et réservations restent utilisables.
Échec de Leaflet : sélecteur et fiches restent utilisables. Sans JavaScript :
les quatre fiches originales, liens natifs et détails restent accessibles.

Leaflet 1.9.4 et sa licence BSD existants sont réutilisés sans modification.
Les [conditions OSM](https://operations.osmfoundation.org/policies/tiles/)
sont respectées par l'attribution liée, le Referer existant, les seules tuiles
du viewport, `keepBuffer: 0`, sans multiplication retina, proxy ou téléchargement
hors ligne. Aucun service payant ni nouvel asset photo/logo. L'imagerie
illustrative existante et son avertissement sont conservés.

| Asset | Taille brute | Gzip |
| --- | ---: | ---: |
| Bootstrap luxury map | 9 969 octets | 3 374 octets |
| CSS locale luxe | 7 655 octets | 1 794 octets |
| Leaflet JS, différé | 147 568 octets | 42 453 octets |
| Leaflet CSS, différé | 14 806 octets | 3 522 octets |

Tailles mesurées localement ; aucune promesse de Core Web Vitals terrain.

## Tests et audit

| Vérification | Résultat |
| --- | --- |
| Chrome, tests locaux et captures | 361 assertions réussies |
| Auditor : autotests hérités | 57/57 réussis |
| Audit site/SEO complet | PASS, zéro erreur nouvelle ; 965 constats historiques inchangés |
| Préservation | 13 contrôles : périmètre, ancres, SEO/Schema, divulgation, fichiers hors périmètre et fixture |
| Syntaxe JS et diff | PASS |

Chrome teste 320/390/768/1440 px, texte à 200 %, clavier Enter/Space, focus,
cibles tactiles, couleurs forcées, défilement du tableau, chaque fiche et
chaque CTA, absence/refus/accord/révocation du consentement, compte unique
des événements, chargement différé avec et sans IntersectionObserver,
échec tuiles/Leaflet et fonctionnement sans JavaScript.

Le head reste exact sauf la CSS locale et les deux dates de revue. Canonical,
title, description, OG, hreflang, graph Schema, H1, scripts partagés,
consentement, GA4, robots et sitemaps sont préservés. Tous les autres fichiers
suivis sont comparés à la base, notamment Cheap Hotels, Family Hotels, Disney,
photos, Leaflet et licences. Aucun autre worktree n'est utilisé ou modifié.

L'audit initial ne demandait que deux revues de nouvelles intégrations :
la balise script de cette page et le fichier JS local. La fixture reçoit
uniquement deux enregistrements supplémentaires, attachés aux empreintes
SHA-256 exactes et à cette base, correspondant à la carte explicitement
demandée. Toutes les exceptions, contrats et autorisations précédentes restent
identiques ; l'auditeur n'est pas modifié.

## Fichiers préparés

1. `hotels/paris/luxury-hotels/index.html`
2. `assets/css/pages/paris-luxury-hotels.css`
3. `assets/js/paris-luxury-hotel-map.js`
4. `tests/test_paris_luxury_hotel_map.cjs`
5. `tests/test_paris_luxury_preservation.py`
6. `tests/fixtures/site-baseline.json` : uniquement deux enregistrements d'intégration.
7. `docs/paris-luxury-ux-cro.md`

## Rapports et captures

Dossier : `C:/Users/1995/AppData/Local/Temp/tripguidely-paris-luxury-ux-cro-qa`.

Rapports : `browser-report.json`, `preservation-report.json`, `self-tests.json`,
`site-audit-initial.json`, `site-audit.json`, `coordinate-evidence.json`,
`iena-exact-evidence.json`. Toutes les neuf captures ont été examinées :
desktop/mobile hero, fiches, carte et comparaison, plus `mobile-tile-fallback.png`.

[Carte desktop](C:/Users/1995/AppData/Local/Temp/tripguidely-paris-luxury-ux-cro-qa/desktop-hotel-map.png) ·
[Carte mobile](C:/Users/1995/AppData/Local/Temp/tripguidely-paris-luxury-ux-cro-qa/mobile-hotel-map.png) ·
[Fiches desktop](C:/Users/1995/AppData/Local/Temp/tripguidely-paris-luxury-ux-cro-qa/desktop-hotel-cards.png) ·
[Fiche mobile](C:/Users/1995/AppData/Local/Temp/tripguidely-paris-luxury-ux-cro-qa/mobile-hotel-cards.png).

Commandes reproductibles (PowerShell) :

```powershell
$qaDir = Join-Path $env:TEMP 'tripguidely-paris-luxury-ux-cro-qa'
python -B scripts/audit-site.py --base-ref 9d3301f0ffff927ba796d7f33e06e3031fb319a2 --self-test
python -B scripts/audit-site.py --base-ref 9d3301f0ffff927ba796d7f33e06e3031fb319a2
python -B tests/test_paris_luxury_preservation.py --output (Join-Path $qaDir 'preservation-report.json')
node tests/test_paris_luxury_hotel_map.cjs C:/Users/1995/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core 'C:/Program Files/Google/Chrome/Application/chrome.exe' $qaDir
```

Ajouter `--screenshots` au test navigateur seulement pour les captures avec
tuiles réelles ; les autres scénarios utilisent des réponses interceptées.
Les requêtes partenaires et analytics sont bloquées pendant tous ces tests :
ils prouvent le dispatch local, pas la réception GA4 ni l'attribution commerciale.
Pas de test direct Safari/Firefox, lecteur d'écran ou appareil physique.
L'absence de modification des autres worktrees repose sur le périmètre des
opérations ; leur état n'a pas été inspecté.

La validation locale initiale s’est arrêtée sans commit, push ou PR.
L’autorisation suivante couvre commit, push et PR après les contrôles ci-dessous ;
le merge et le déploiement restent interdits. STOP après GitHub Actions.


## Préparation de la PR après intégration de main

Le 12 octobre 2026, `origin/main` a été récupéré : la PR #34 est fusionnée
au commit `9d3301f0ffff927ba796d7f33e06e3031fb319a2`. Les sept fichiers Luxury
ont été sauvegardés avec leurs empreintes dans le dossier QA ci-dessous avant
l’intégration en fast-forward avec autostash. Aucun conflit ; les six fichiers
Luxury hors fixture sont restés identiques après réapplication. Les nouveaux
fichiers Cheap et ses trois enregistrements d’audit sont intégralement conservés.

Seuls les deux enregistrements Luxury ont changé de `base_revision` pour
la nouvelle base, sans changer leurs empreintes. Le test navigateur compare
les ancres à cette base immuable ; le test de préservation accepte désormais
un commit descendant de main pour rester exécutable après le commit autorisé.
Le code HTML/CSS/JS validé localement n’a pas été modifié lors de cette phase.

Les sites officiels ont été relus et l’IGN interrogé de nouveau : identités,
adresses et les quatre positions exactes sont reconfirmées, sans changement.
Les coordonnées restent des points d’adresse, sans garantie d’entrée accessible.
Les ancres affiliées sont comparées intégralement à main, et la carte clone
ces ancres exactes. La validation navigateur intercepte partenaires et GA4 ;
elle ne prouve pas la réception analytics ou l’attribution commerciale.

Les résultats finaux et la CI sont consignés dans la PR. Rapports locaux :
`C:/Users/1995/AppData/Local/Temp/tripguidely-paris-luxury-pr-qa`.
Les captures de la revue initiale restent dans le dossier précédent.
Les contrôles de compatibilité exécutent les tests navigateur Luxury, Cheap,
Family et le test affilié Family, sans modifier ces pages ni ces tests hérités.
La différence vers main reste limitée aux sept fichiers listés ci-dessus.
Aucun autre worktree n’a été utilisé, changé ou inspecté.


Validation après intégration : Luxury 359 assertions navigateur ; Cheap 283 ;
Family 279 ; affiliations Family 43. Les 57 autotests de l’auditeur passent.
L’audit contre la nouvelle base passe avec zéro erreur nouvelle, 965 constats
historiques inchangés et uniquement les deux enregistrements Luxury attendus.
Les 13 contrôles de préservation, la syntaxe des deux scripts JS Luxury et
`git diff --check` passent. Les fichiers hors périmètre restent exacts à main.
