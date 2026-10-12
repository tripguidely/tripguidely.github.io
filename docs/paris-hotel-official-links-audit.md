# Audit et correction des liens hôteliers — Paris

Date : 12 octobre 2026, America/Toronto.
Base initiale : `d4a5c987e56bea339af5f02a303a0c0d7dc96490`,
avec les fusions Cheap #34 et Luxury #35.
Base intégrée pour la PR : `13b6ddac77e910bf96279c67e70a4359479ddb86`,
dernier origin/main récupéré après fusion de Where to Stay PR #36.
Nouveau worktree :
`C:/Users/1995/AppData/Local/Temp/tripguidely-paris-hotel-official-links`.
Nouvelle branche : `fix/paris-hotel-official-links`.
État : commit, push et PR vers main autorisés après synchronisation et
validation. Attendre GitHub Actions, puis STOP pour validation humaine.
Aucun merge ni déploiement autorisé.

## Inventaire et correction

L'audit porte sur toutes les ancres sortantes des trois fichiers HTML, puis
sur le DOM complet après chargement du header/footer et de chacune des fiches
de carte. Les ressources techniques et métadonnées externes sont distinguées
des liens éditoriaux vers les hôtels : elles restent nécessaires au fonctionnement.

| Page | Liens officiels avant | Liens officiels après | Ancres Klook HTML conservées | Correction |
| --- | ---: | ---: | ---: | --- |
| Family Hotels | 0 | 0 | 4 | Déjà conforme ; fichier inchangé |
| Cheap Hotels | 0 | 0 | 3 | Déjà conforme ; fichier inchangé |
| Luxury Hotels | 4 | 0 | 4 | Quatre ancres de source remplacées par leur texte exact |

Changement unique dans le contenu public :
`<a href="URL_OFFICIELLE">official property information</a>` devient
`official property information`. Les quatre paragraphes `Source:`, leur
ponctuation et les classes existantes sont conservés. Aucun texte utile,
adresse, catégorie, équipement, conseil, avantage ou compromis n'est retiré.
Les cartes clonent déjà le contenu des fiches : leurs détails bénéficient
automatiquement de la correction, sans modifier leurs scripts.

Aucun lien officiel n'est converti en CTA affilié. Les onze ancres Klook
existantes restent exactes, y compris tous les attributs et noms accessibles.
Les clones de carte gardent leur contrat existant : placement `map` et variante
`with_map` sur Family/Cheap ; clone intégral sans nouvel attribut sur Luxury.

## Sources officielles conservées en interne

Ces URL sont des références éditoriales conservées pour vérification future,
pas des liens à remettre dans les fiches publiées. Leur présence dans les
documents historiques est également préservée. Cette correction ne constitue
pas une nouvelle vérification de disponibilité ou de conditions de réservation.

| Page | Établissement | Référence officielle |
| --- | --- | --- |
| Family | Citadines Les Halles Paris | https://www.discoverasr.com/en/citadines/france/citadines-les-halles-paris |
| Family | Pullman Paris Montparnasse | https://www.pullmanparismontparnasse.com/fr/chambres-suites/chambres-deluxe-famille-amis/ |
| Family | Hôtel Régence Étoile | https://www.hotelregenceetoile.com/en/ |
| Family | B&B HOTEL Paris 17 Batignolles | https://www.hotel-bb.com/en/hotel/paris-17-batignolles |
| Cheap | ibis Paris Tour Eiffel Cambronne 15ème | https://all.accor.com/hotel/1400/index.en.shtml |
| Cheap | B&B HOTEL Paris 17 Batignolles | https://www.hotel-bb.com/en/hotel/paris-17-batignolles |
| Cheap | Generator Paris | https://staygenerator.com/hostels/paris |
| Luxury | Le Meurice | https://www.dorchestercollection.com/paris/le-meurice |
| Luxury | Mandarin Oriental Lutetia, Paris | https://www.mandarinoriental.com/en/paris/lutetia/wellness |
| Luxury | Shangri-La Paris | https://www.shangri-la.com/paris/shangrila/ |
| Luxury, alternative premium | Pullman Paris Tour Eiffel | https://pullman.accor.com/en/hotels/paris/7229.html |

Les quatre dernières URL sont exactement celles des ancres retirées. Les
références Family/Cheap proviennent des documents de recherche conservés :
`docs/paris-family-hotel-map.md`, `docs/paris-cheap-hotel-map.md`,
`docs/paris-hotel-subguides.md`. Les sources détaillées Luxury restent aussi
dans `docs/paris-luxury-ux-cro.md`. Aucun de ces documents historiques n'est modifié.

## Inventaire affilié exact

| Page / établissement | URL Klook | SubID |
| --- | --- | --- |
| Family / Citadines Les Halles | https://klook.tpk.ro/7c3IV7YH | paris_hotel_citadines_halles |
| Family / Pullman Montparnasse | https://klook.tpk.ro/w9gvKJbA | paris_hotel_pullman_montparnasse |
| Family / Régence Étoile | https://klook.tpk.ro/LsvOTPx3 | paris_hotel_regence_etoile |
| Family / B&B Batignolles | https://klook.tpk.ro/gX4TDO9u | paris_hotel_bb_batignolles |
| Cheap / ibis Cambronne | https://klook.tpk.ro/jor8wPCP | paris_hotel_ibis_cambronne |
| Cheap / B&B Batignolles | https://klook.tpk.ro/gX4TDO9u | paris_hotel_bb_batignolles |
| Cheap / Generator | https://klook.tpk.ro/t3aQhbjX | paris_hotel_generator |
| Luxury / Le Meurice | https://klook.tpk.ro/GOOv5HfU | paris_luxury_le_meurice |
| Luxury / Lutetia | https://klook.tpk.ro/C2ZHDWrY | paris_luxury_lutetia |
| Luxury / Shangri-La | https://klook.tpk.ro/D8WBtyB5 | paris_luxury_shangrila |
| Luxury, alternative / Pullman Eiffel | https://klook.tpk.ro/QlEUdy0e | paris_hotel_pullman_eiffel |

`rel="nofollow sponsored noopener"`, `target="_blank"`, `data-aff="klook"`,
classes, `aria-label`, IDs et attributs d'expérience restent inchangés.
Le lien B&B commun à deux pages n'est pas remplacé ou dupliqué davantage.

## Liens et ressources externes maintenus

Après correction, les seules ancres sortantes dans les trois HTML sont les
onze Klook existantes. Dans le DOM avec carte initialisée, chaque page ajoute
un seul clone Klook de l'hôtel sélectionné et deux liens d'attribution :
`https://leafletjs.com/` et `https://www.openstreetmap.org/copyright`.
Ces liens d'attribution ne sont pas des sites d'hôtels et doivent être conservés.
Ils sont vérifiés pour chacune des onze sélections, pas seulement la première.

Le script Travelpayouts, les indications de connexion Klook/Travelpayouts,
le modèle d'URL des tuiles OSM, la référence Schema.org, les canonicals et
les URL du domaine TripGuidely dans les métadonnées restent exacts. Leaflet,
ses licences, l'attribution, les coordonnées et le chargement différé sont
conservés. Aucun compte, service payant ou nouveau visuel n'est introduit.

## Validation et preuve de préservation

Les tests nouveaux comparent la page Luxury complète à la base après la seule
transformation des quatre ancres. Family et Cheap doivent être intégralement
identiques. Texte, head, Schema, dates, H1, fragments, divulgation et onze
ancres Klook sont comparés ; tous les autres fichiers suivis sont vérifiés
contre les blobs Git immuables de la base.

Le test navigateur inspecte toutes les ancres du DOM, puis chaque fiche de
carte dépliée, avec consentement absent/refusé/accordé et sans JavaScript.
Il vérifie les attributs des clones, l'activation clavier, les événements
affiliés et l'absence de requêtes Klook réelles. Les tests navigateur existants
des trois cartes et du tracking Family sont également exécutés. Les anciens
scripts Python de préservation Cheap/Luxury décrivent leurs phases de création
et leurs branches historiques ; la comparaison exacte de cette correction
est assurée par le nouveau test commun, sans modifier ces anciens tests.

Résultats de la validation locale initiale :

| Contrôle | Résultat |
| --- | --- |
| Nouveau test exact HTML/périmètre | 49 contrôles réussis ; 580 autres fichiers suivis exacts |
| Nouveau test des liens DOM et cartes | 323 assertions réussies ; neuf scénarios page/consentement, plus trois sans JS |
| Carte Luxury, test existant | 359 assertions réussies |
| Carte Cheap, test existant | 283 assertions réussies |
| Carte Family, test existant | 279 assertions réussies |
| Affiliations Family, test existant | 43 assertions réussies ; zéro requête partenaire/analytics envoyée |
| Autotests hérités de l'auditeur | 57/57 réussis |
| Audit complet contre main | PASS ; zéro erreur nouvelle, 965 constats historiques inchangés |
| Fixture/contrats/autorisations | Tous inchangés ; aucune nouvelle exception ni autorisation nécessaire |
| Syntaxe JS, git diff --check | PASS |
| HEAD/index | HEAD à la base ; index vide, aucun commit |

Les cartes existantes restent ouvertes automatiquement et se chargent à
l'approche du viewport. Les tests hérités couvrent 320/390/768/1440 px, texte
à 200 %, clavier, focus, cibles tactiles, couleurs forcées, échec des tuiles
et de Leaflet, défilement du tableau, absence de JavaScript, consentement et
révocation. La conservation de la totalité du head et des scripts partagés
est vérifiée, pas seulement la présence d'un canonical ou d'un CTA.

Inventaire DOM après initialisation et pour chaque sélection : Family
cinq ancres Klook (quatre originales + un clone) et deux attributions ;
Cheap quatre Klook et deux attributions ; Luxury cinq Klook et deux
attributions. Aucune ancre sortante vers un site officiel hôtelier, même
après dépliage des détails. Aucun bouton supplémentaire n'est ajouté.
Les onze liens natifs et tous les clones activés dans les tests hérités
restent fonctionnels.

## Périmètre

Quatre fichiers préparés :

1. `hotels/paris/luxury-hotels/index.html` : quatre ancres de source retirées.
2. `docs/paris-hotel-official-links-audit.md` : ce rapport et l'inventaire interne.
3. `tests/test_paris_hotel_official_links.py` : préservation et inventaire HTML.
4. `tests/test_paris_hotel_official_links.cjs` : inventaire de toutes les fiches de carte.

`hotels/paris/family-hotels/index.html`, `hotels/paris/cheap-hotels/index.html`
et `hotels/paris/index.html` restent inchangés. Aucun script partagé, carte,
CSS, image, sitemap, robots, fixture d'audit, autorisation ou ancien test
n'est modifié. Aucun fichier des autres worktrees n'est modifié : Disney et le
travail Where to Stay restent hors périmètre. Leurs états ne sont pas inspectés.

## Reproduction et artefacts

Dossier QA extérieur au worktree :
`C:/Users/1995/AppData/Local/Temp/tripguidely-paris-hotel-official-links-qa`.

```powershell
$qaDir = Join-Path $env:TEMP 'tripguidely-paris-hotel-official-links-qa'
python -B tests/test_paris_hotel_official_links.py --output (Join-Path $qaDir 'preservation-report.json')
python -B scripts/audit-site.py --base-ref 13b6ddac77e910bf96279c67e70a4359479ddb86 --self-test
python -B scripts/audit-site.py --base-ref 13b6ddac77e910bf96279c67e70a4359479ddb86
```

Rapports : `preservation-report.json`, `outgoing-browser-report.json`,
`self-tests.json`, `site-audit.json`, `luxury/browser-report.json`,
`cheap/map-browser-report.json`, `family/map-browser-report.json`.
Le résultat du test affilié Family est aussi conservé dans la sortie d'exécution.

Trois captures des détails de carte ouverts ont été examinées ; elles montrent
les informations et boutons conservés, et le libellé de source Luxury en texte :

- [Family](C:/Users/1995/AppData/Local/Temp/tripguidely-paris-hotel-official-links-qa/family-map-card.png)
- [Cheap](C:/Users/1995/AppData/Local/Temp/tripguidely-paris-hotel-official-links-qa/cheap-map-card.png)
- [Luxury](C:/Users/1995/AppData/Local/Temp/tripguidely-paris-hotel-official-links-qa/luxury-map-card.png)

Commande du nouveau test navigateur (PowerShell) :

```powershell
node tests/test_paris_hotel_official_links.cjs C:/Users/1995/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core 'C:/Program Files/Google/Chrome/Application/chrome.exe' $qaDir
```

Les tests Chrome utilisent le module Playwright et Chrome déjà installés,
sans téléchargement. Les tuiles sont interceptées pour les tests de régression.
Les requêtes analytics et partenaires sont bloquées ; les tests établissent
le dispatch local et l'intégrité des liens, pas la réception GA4 ni les
commissions, tarifs, disponibilité ou statut HTTP final des offres Klook.
Pas de revue directe de lecteur d'écran ou d'appareil physique.

La revue initiale s’est arrêtée sans commit, push ou PR. L’autorisation
suivante couvre commit, push et PR après les contrôles de synchronisation.
STOP après GitHub Actions ; aucun merge ni déploiement.


## Synchronisation et préparation de la PR

Après fusion de Where to Stay PR #36, main a été intégré en fast-forward
sans conflit. Les quatre fichiers préparés ont été sauvegardés avec leurs
empreintes dans le dossier QA de cette phase et sont restés identiques après
synchronisation. Seul `hotels/paris/index.html` a évolué par héritage de main ;
il reste strictement identique à cette nouvelle base et n'apparaît pas dans
la différence de la PR.

Les deux tests de cette correction sont désormais liés à la nouvelle base
immuable `13b6ddac77e910bf96279c67e70a4359479ddb86`. Le contrôle d'ascendance
accepte le commit autorisé de la branche, pour être relancé après le commit.
L'HTML Luxury n'a pas été modifié au cours de cette synchronisation. Family,
Cheap, cartes, scripts partagés, SEO, consentement et fixture restent exacts
au dernier main.

Rapports de cette phase :
`C:/Users/1995/AppData/Local/Temp/tripguidely-paris-hotel-official-links-pr-qa`.
Les résultats GitHub Actions sont disponibles dans la PR ; aucun merge
n'est autorisé. Aucun autre worktree, dossier ou branche n'est modifié ou supprimé.


Validation après intégration de PR #36 : 49 contrôles de préservation réussis,
580 fichiers hors périmètre exacts à la nouvelle base, y compris
`hotels/paris/index.html`, Family et Cheap. Le nouveau test DOM passe ses
323 assertions ; les tests existants Luxury/Cheap/Family/affiliations Family
passent respectivement 359/283/279/43 assertions, soit 1 287 vérifications
navigateur au total. Les 57 autotests et l'audit SEO/site passent : zéro
nouvelle erreur, 965 constats historiques inchangés, aucune nouvelle
exception ou autorisation. Les trois captures de cette phase sont examinées.
La syntaxe JS et `git diff --check` passent. La différence vers main contient
uniquement les quatre fichiers de cette correction.
