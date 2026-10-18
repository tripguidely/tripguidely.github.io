# TripGuidely — retrait ciblé de Travelpayouts Drive V1

Préparé le 18 octobre 2026 pour revue humaine. Branche : fix/travelpayouts-drive-removal-v1. Worktree neuf : C:/Users/1995/AppData/Local/Temp/tripguidely-drive-removal-v1. Base et origin/main vérifiés : ee86ecbd38f68bad7e5647d1451c2ca497a9d3b7. Preuves et captures externes : C:/Users/1995/AppData/Local/Temp/tripguidely-drive-removal-v1-qa.

## Verdict

**NEEDS FIXES avant publication. Le correctif local de navigation est fonctionnel et prêt pour revue.** Aucun défaut fonctionnel nouveau n'est identifié dans les contrôles finaux. L'audit officiel reste volontairement bloqué par les 116 autorisations non appliquées. La validation du compte Travelpayouts et la réception GA4 restent à réaliser. Les problèmes d'accessibilité hérités sont documentés ci-dessous et n'ont pas été modifiés.

Aucun commit, staging, push, PR, merge ou déploiement. Aucun réglage Travelpayouts modifié et aucun message envoyé au support. L'implémentation n'est pas publiée : les pages publiques gardent donc leur comportement antérieur tant qu'une publication séparée n'est pas autorisée.

## Changement exact

112 fichiers HTML perdent chacun une seule balise dont le src vaut exactement https://tp-em.com/NDkyNzI0.js?t=492724. Seule son indentation devenue isolée est également retirée ; la ligne vide et les fins de ligne existantes sont conservées. Aucun formatage général ni remplacement de contenu n'est effectué. La liste complète et les empreintes avant/après sont dans [l'inventaire](qa/travelpayouts-drive-removal-inventory.json).

Chaque page corrigée est vérifiée contre le blob du commit de base après cette seule suppression. Les autres balises de script, ancres, formulaires, meta et link restent identiques. Le contrôle global protège tous les autres fichiers suivis, notamment les images binaires, site.js, les contrôleurs/cartes Paris, les CSS, les partials, le baseline, l'auditeur, les workflows, robots et sitemaps. Les conversions CRLF/LF de Git sont reconnues pour les types texte existants, Python/CJS, .gitkeep et LICENSE ; les autres octets sont comparés strictement.

Les 24 scripts de widgets manuels tpemb.com/content sont conservés à l'identique. Aucun lien affilié, SubID, target/rel, marqueur, métadonnée GA4 ou règle de consentement n'est modifié. Les cinq liens Klook du hub New York restent identiques. Les balises travelpayouts-verification, préconnexions et CSP restent en place. La présence de préconnexions peut encore entraîner DNS/TLS ; le correctif supprime l'exécution et les requêtes HTTP de Drive, pas tous les contacts possibles avec un domaine Travelpayouts.

Un seul test historique est adapté : tests/test_paris_family_affiliate_tracking.cjs vérifie que le src Drive est absent et soustrait exactement la balise recensée du HTML de référence, avec son indentation propre. Il ne retire pas arbitrairement les autres scripts et conserve ses contrôles de payload, consentement et déduplication. Les nouveaux tests globaux vérifient indépendamment l'intégralité du diff.

## Preuve du problème et du résultat

Le nouveau test navigateur utilise le HTML réel de la base et un petit simulateur indépendant du verrouillage observé : mémoriser les URL, vider les href Klook, restaurer les ancres mémorisées après cinq secondes. Aucun code fournisseur n'est copié et le simulateur ne prétend pas représenter les réglages du compte ou tout le runtime Drive.

Sur chacune des trois pages d'origine, ce contrôle négatif reproduit le premier CTA de carte vide, qui reste vide après restauration des liens sources. Sur le HTML corrigé, aucun script Drive n'est demandé et aucun href affilié vide ou de même origine n'est observé depuis le démarrage du document. Le premier clic natif intervient avant toute attente de secours ou changement de sélection.

La navigation native utilise les URL courtes originales, avec réponses de destination interceptées hors ligne. Elle vérifie la destination exacte et window.opener=null. Elle prouve que l'ancre fonctionne, pas qu'un serveur marchand accepte une session ni qu'une commission est attribuée.

Le test complet couvre Family (4 choix), Cheap (3 choix) et Luxury (4 choix, dont l'alternative Pullman séparée des trois hôtels principaux), à 390 et 1440 px. Il vérifie clic/tap et Entrée, navigation initiale, sélection de tous les hôtels, conservation des attributs commerciaux, rechargement, ressources retardées, arrivée directe sur #hotel-map, réinitialisation des scripts, refus/retrait du consentement et repli sans JavaScript. Le suivi de mutations débute avant les scripts de page ; il ne se limite pas à constater un lien rétabli après plusieurs secondes.

## Résultats finaux

| Contrôle | Résultat |
|---|---|
| Conservation globale | PASS — 8 tests ; 112 suppressions exactes, 24 widgets, autres fichiers/scripts/liens/SEO et baseline conservés |
| Premier chargement Paris | PASS — 197 assertions, 18 scénarios dont 3 contrôles négatifs, desktop/mobile et premier clic natif |
| Universal | PASS — 432 assertions |
| Tracking Family | PASS — 45 assertions, dont deux vérifications ajoutées pour le retrait exact de Drive |
| Carte Family | PASS — 279 assertions |
| Carte Cheap | PASS — 283 assertions |
| Carte Luxury | PASS — 359 assertions |
| Liens officiels hôtels | PASS — 323 assertions |
| Carte des quartiers | PASS — 1 055 assertions |
| Autotests de l'auditeur | PASS — 57/57 exécutés sur la base propre ; code de l'auditeur inchangé ensuite |
| Contrôles négatifs d'autorisation | PASS — 470 ; mauvais hash/base/chemin et suppression de chaque entrée, mutations affiliées/liens/scripts/Croisières |
| Audit officiel avant retrait | PASS — aucune nouvelle erreur |
| Audit officiel après retrait | EXIT 1 attendu — exactement 112 contract_changed/integration_markup et 4 protected_file_changed/cruise_file ; aucune autre nouvelle erreur |
| Revue visuelle et cache | PASS — 6 vues desktop/mobile, vrais fonds OSM, 20–26 ressources servies depuis le cache au rechargement ; aucune erreur JS |
| Accessibilité comparée | Aucune nouvelle violation dans main ; défauts hérités conservés et détaillés ci-dessous |
| Git diff --check | PASS après nettoyage de l'indentation isolée des balises retirées |

Les six suites hôtels totalisent 2 344 assertions. L'audit après retrait conserve 965 constats historiques connus et 48 anciennes réparations déclarées résolues ; ce ne sont pas 965 régressions introduites par ce travail. Zéro des 116 changements est autorisé dans le baseline actuel. Les 116 autorisations complètes passent uniquement dans le contrôle synthétique en mémoire.

La suite Universal utilise son ancienne référence pré-tracking b193a14f190ea63118e371b316a3e7ef50827ef1, comme prévu par son harnais. Le contrôle de conservation globale protège séparément tous les fichiers Universal contre le main actuel. Les anciens tests Python qui imposent une branche ou un ancien périmètre de projet ne sont pas présentés comme réexécutés ici : leurs fichiers restent intacts et la conservation globale est vérifiée contre la nouvelle base. Les suites navigateur hôtels ont été réexécutées sur le correctif final.

Aucune requête affiliée ni analytics Google n'a quitté les tests fonctionnels. Les essais visuels autorisent les tuiles OSM, avec les conséquences réseau habituelles de cette connexion. La réception GA4 et les rapports du partenaire ne sont pas simulés comme des preuves réelles.

## Échecs intermédiaires et corrections du harnais

- Les premières comparaisons texte ont signalé à tort les fins de ligne Windows de LICENSE, puis Python/CJS. Le test a été aligné sur les conversions Git de ces textes ; aucun fichier concerné, aucune règle d'audit et aucun octet binaire n'ont été modifiés pour faire passer le contrôle.
- Une première attente utilisait le nombre d'hôtels principaux Luxury comme nombre total. Le test final prend toutes les ancres sources, inclut l'alternative Pullman et vérifie leur correspondance avec les quatre choix de carte.
- Le premier serveur visuel externe mélangeait les séparateurs de chemin Windows et renvoyait lui-même 403. Le chemin du harnais a été normalisé. Ce 403 ne provenait ni du site publié, ni de Drive, ni de Klook.
- Le retrait littéral des balises laissait des espaces seuls sur 111 lignes. Ces seules indentations ont été supprimées ; les quatre empreintes de fichier Croisières ont été recalculées. Les contrôles finaux, dont les 470 contrôles négatifs, ont été rejoués sur ces empreintes.

Ces échecs intermédiaires ne sont pas masqués par une exclusion d'audit. Aucun échec fonctionnel final ne reste ouvert. L'audit officiel n'est cependant pas déclaré vert tant que les 116 autorisations n'ont pas été réellement revues et appliquées.

## Autorisations en attente

[Brouillon complet des 116 entrées](qa/travelpayouts-drive-removal-pending-authorizations.json). SHA-256 du fichier préparé en UTF-8/LF : 8fd59853dace013f8af0be28a5bf263c2144829024c09f46ae37404275e00bb1.

Toutes les entrées ont base_revision=ee86ecbd38f68bad7e5647d1451c2ca497a9d3b7, recorded_on=2026-10-18 et reviewed_by=null. Elles ne sont pas valides pour application directe sans la référence de revue réelle. Le fichier de brouillon n'est pas lu par l'auditeur.

112 entrées integration_markup portent sur les compteurs d'empreintes de scripts de chaque page. Leurs valeurs before/after sont les hashes de l'ensemble du contrat de scripts de la source, pas les hashes des HTML complets ni de la seule balise retirée. Les quatre entrées supplémentaires cruise_file protègent le fichier entier :

| Source | before | after |
|---|---|---|
| cruises/best-cruises-2026/index.html | 820c050c2ca4e3ea6735783337d9b192f5584909493f11718b495a88079cf44b | 33a5cbb81efd128efb51b2564348eb77b20947b3b5eb1ee9f209eb70b4502f5a |
| cruises/caribbean/index.html | a7dcab1499652256707d608b87295464cfa980463bf85ee63c319260068f6cd5 | 0fa6548a497e0a14981219f4bc0c82ae6ea2ad0753633f487d32fe791b569c48 |
| cruises/index.html | 36ebf204ed5d3252663b61452897ce39855d6ccdb9ffafa33c04cd3c915d46cf | 91c4e68f413d71ed24b941e7fd1a2d5ee86fefa3c2b9a3a3080a9c4eadd4f25e |
| cruises/mediterranean/index.html | 64ffc3b6df399307db6dd9453d68c390388982152821455dd9e255f99cc17377 | c08a3f4f7914a8c4d3ee3e3524109ff54af6b504b859134cbfe6d7453f0b8be7 |

Chaque entrée est liée à un chemin, un type, un commit et deux empreintes précis. Les contrôles négatifs invalident chacun des 116 enregistrements si le hash, la base ou le chemin change, ou si l'entrée manque. Des liens invalides, une destination interne absente, un nouveau script externe ou un autre changement Croisières ne sont pas masqués par ces autorisations. Les identités synthétiques utilisées pour cette preuve existent uniquement en mémoire, jamais dans le baseline.

Le [contrat d'audit](redesign-contract.md#approving-intentional-contract-changes) impose une revue du diff exact. Après votre prochain accord, l'application éventuelle devra ajouter uniquement ces 116 entrées avec la vraie référence de revue, puis relancer l'audit. Aucun ancien enregistrement, exception, compteur historique ou règle ne doit être réécrit. Les quatre autorisations New York restent dans leur autre worktree et ne sont pas reprises ici.

## Accessibilité et performances : portée des preuves

Dans les six vues comparées à la base avec Drive bloqué, axe retrouve les mêmes défauts dans main : color-contrast sérieux sur le fil d'Ariane span[aria-current=page], et landmark-unique modéré sur #comparison. Aucun nouveau défaut de main n'est détecté. Un scan complet après rechargement retrouve le défaut critique aria-valid-attr-value de .js-consent dans le footer partagé. Ces contrôles interviennent à des positions/états de page différents ; le scan complet ne doit pas être interprété comme une annulation des défauts de main observés plus haut. Aucun de ces éléments n'a été modifié par ce retrait. Une correction partagée distincte et une revue manuelle sont nécessaires pour revendiquer la conformité de la page entière.

Le relevé local avant défilement mesure LCP 96–144 ms à froid et 228–312 ms au rechargement avec cache, CLS 0 sur mobile et environ 0,053 à 0,073 sur desktop. Ce sont des observations locales ponctuelles, pas des scores Lighthouse, des données terrain ni un comparatif avec Drive réellement actif. Le serveur visuel n'intercepte pas les ressources locales et les événements CDP confirment le cache. Le premier prototype de mesure réutilisait déjà le cache des ressources de la base ; il est conservé séparément et n'est pas utilisé pour ces chiffres à froid.

Les métriques du test fonctionnel initial-load-report.json couvrent aussi des changements de sélection et le chargement paresseux après défilement ; ses valeurs CLS desktop plus élevées ne sont pas des mesures de chargement seules. La source de référence pour les chiffres froid/chaud est visual-accessibility-cache-final.json. Le correctif n'ajoute aucun asset ni code JavaScript au site. Les CSS, images et bibliothèques restent identiques. Aucun gain de Core Web Vitals ou de classement SEO n'est revendiqué. Chrome tactile émulé ne remplace pas un essai sur appareil iOS/Android physique ou un lecteur d'écran.

## Risques commerciaux et validations restantes

| Sujet | État et action nécessaire avant publication |
|---|---|
| Content Analytics | Le script commun sert à la collecte par page. Son retrait peut interrompre ou réduire ces données et leur ventilation. L'effet exact sur le compte n'a pas été vérifié. Convenir de la perte acceptable ou obtenir une confirmation du partenaire ; ne pas confondre ce rapport avec une preuve d'attribution de lien court. |
| Vérification Travelpayouts | La balise meta existante reste intacte. La procédure actuelle du fournisseur passe par l'installation Drive ; le maintien du statut après retrait doit être confirmé dans le compte ou auprès du support. Aucune garantie ne découle de la seule présence de la meta. |
| SubID et compte crédité | Les URL/SubID HTML restent inchangés, mais data-subid n'est pas automatiquement transmis par une ancre. Les neuf alias New York avaient un aff_sid vide dans les redirections du diagnostic précédent ; une configuration serveur reste possible mais non prouvée. Vérifier les alias existants/Get full link et Reports → Performance par SubID, sans régénérer ni modifier les URL. |
| Programme Klook hôtels | Confirmer l'éligibilité des réservations hôtelières et les conditions du programme effectivement connecté. Aucun crédit, réservation ou commission n'a été confirmé ici. |
| GA4 | Appels locaux, consentement et absence de doublon affiliate_click validés. Réception DebugView/Realtime, dimensions personnalisées, éventuelle mesure améliorée et configuration des événements clés non vérifiées. Ne pas additionner outbound_click et affiliate_click pour compter un geste unique. |
| HTTP 403 et CORS | Le retrait élimine le besoin de charger Drive sur ces pages. Il ne corrige pas les protections marchand Klook observées auparavant. Aucune nouvelle attribution causale des anciens messages CORS n'est revendiquée. |
| Widgets et CSP | Les widgets manuels et la CSP sont conservés. Les erreurs de télémétrie propres aux widgets, notamment observées sur eSIM, peuvent donc subsister. Pas d'élargissement de la CSP dans cette intervention. |
| Accessibilité héritée | Contraste du fil d'Ariane, nommage des régions et contrôle Privacy choices du footer : revue/correctif séparés nécessaires. |

Sources primaires revérifiées le 18 octobre 2026 : [Content Analytics](https://support.travelpayouts.com/hc/en-us/articles/22641653439506-Content-analytics), [vérification du site](https://support.travelpayouts.com/hc/en-us/articles/26411796684818-How-to-confirm-that-you-own-a-website), [ID/SubID et rapports Performance](https://support.travelpayouts.com/hc/en-us/articles/203955653-ID-and-SubID-Affiliate-marker-and-additional-marker). Aucun accès authentifié au compte n'a été utilisé et aucun support n'a été contacté.

La solution proposée pour protéger l'attribution conserve les liens courts originaux et les widgets manuels, enlève le mécanisme qui peut neutraliser les ancres, puis exige une vérification partenaire des alias, SubID et compte crédité avant publication. Aucun paramètre sub_id n'a été ajouté comme contournement.

## Isolation et état Git

Un nouveau worktree propre a été créé après fetch du main exact. Le checkout Disney, les autres branches et le worktree New York ne sont ni réinitialisés, ni déplacés, ni nettoyés. Les 623 fichiers New York sont contrôlés par empreinte ; les neuf liens et leurs placeholders restent dans leur travail non commité, sans copie ni fusion dans cette branche.

La preuve externe final-integrity.json enregistre les HEAD/statuts des 34 autres worktrees enregistrés avant l'intervention et les empreintes des fichiers présents des checkouts New York/Disney. Elle compare ensuite ces données et les 112 empreintes de sortie. Les anciens worktrees présentant des fichiers absents restent dans leur état initial, sans tentative de réparation.

Le baseline de cette branche conserve les neuf exceptions de destinations New York encore absentes de main. Les modifications propres à New York et leurs autorisations ne sont pas importées. Cette séparation explique notamment les 965 constats connus de cet audit, contre 956 dans le worktree New York où les neuf destinations étaient réparées.

## Preuves et commandes

Les sorties brutes sont dans C:/Users/1995/AppData/Local/Temp/tripguidely-drive-removal-v1-qa. Fichiers principaux : audit-before.json, audit-final.json, auditor-self-tests.json, preservation.stdout.log/preservation.stderr.log, authorization-negative-controls.json, initial-load-complete/initial-load-report.json, visual-accessibility-cache-final.json, final-integrity.json et final-tracked.diff. Les sept suites existantes ont chacune leur JSON et leurs journaux stdout/stderr. Les anciennes tentatives et les empreintes avant nettoyage d'indentation restent séparées pour traçabilité.

Commandes exécutées depuis le nouveau worktree :

```powershell
python -B tests/test_travelpayouts_drive_removal.py
& 'C:/Program Files/nodejs/node.exe' tests/test_paris_drive_initial_load.cjs C:/Users/1995/AppData/Local/Temp/tripguidely-foundation-qa-tools/node_modules/playwright-core 'C:/Program Files/Google/Chrome/Application/chrome.exe' 'C:/Users/1995/AppData/Local/Temp/tripguidely-drive-removal-v1-qa/initial-load-complete'
python -B scripts/audit-site.py --base-ref ee86ecbd38f68bad7e5647d1451c2ca497a9d3b7 --self-test
python -B scripts/audit-site.py --base-ref ee86ecbd38f68bad7e5647d1451c2ca497a9d3b7 --json
python -B 'C:/Users/1995/AppData/Local/Temp/tripguidely-drive-removal-v1-qa/authorization-negative-controls.py'
python -B 'C:/Users/1995/AppData/Local/Temp/tripguidely-drive-removal-v1-qa/regressions.py' universal family-tracking family-map cheap-map luxury-map official-links neighborhood-map
```

Six captures avec vrais fonds OSM montrent les premiers panneaux et CTA : family-390-real-map.png, family-1440-real-map.png, cheap-390-real-map.png, cheap-1440-real-map.png, luxury-390-real-map.png et luxury-1440-real-map.png. Elles sont dans le répertoire QA externe. Les six captures supplémentaires du test fonctionnel utilisent des tuiles hors ligne et montrent les sélections ; ne pas les présenter comme des fonds réels.

## Liste complète des fichiers modifiés ou ajoutés

118 chemins : 112 HTML de production, un test existant adapté et cinq nouveaux fichiers de tests/documentation. Aucun autre fichier suivi n'est modifié.

```text
attractions/disneyland-paris-tickets/index.html
attractions/index.html
attractions/tokyo-disney-resort-tickets/index.html
car-rental/bangkok/index.html
car-rental/dubai/index.html
car-rental/index.html
car-rental/london/index.html
car-rental/new-york/index.html
car-rental/paris/index.html
car-rental/quebec-city/index.html
car-rental/rome/index.html
car-rental/tokyo/index.html
cruises/best-cruises-2026/index.html
cruises/caribbean/index.html
cruises/index.html
cruises/mediterranean/index.html
docs/qa/travelpayouts-drive-removal-inventory.json
docs/qa/travelpayouts-drive-removal-pending-authorizations.json
docs/travelpayouts-drive-removal.md
esim/best-esim-europe/index.html
esim/canada/index.html
esim/esim-compatibility-check/index.html
esim/esim-setup-guide/index.html
esim/france/index.html
esim/index.html
esim/italy/index.html
esim/japan/index.html
esim/thailand/index.html
esim/uae/index.html
esim/uk/index.html
esim/usa/index.html
fr/travel-guides/index.html
hotels/bangkok/index.html
hotels/dubai/index.html
hotels/index.html
hotels/las-vegas/index.html
hotels/london/index.html
hotels/new-york/index.html
hotels/paris/cheap-hotels/index.html
hotels/paris/family-hotels/index.html
hotels/paris/index.html
hotels/paris/luxury-hotels/index.html
hotels/rome/index.html
hotels/tokyo/index.html
index.html
itinerary/bangkok/2-days/index.html
itinerary/bangkok/3-days/index.html
itinerary/bangkok/4-days/index.html
itinerary/bangkok/first-time/index.html
itinerary/bangkok/index.html
itinerary/bangkok/rainy-day/index.html
itinerary/dubai/days-2/index.html
itinerary/dubai/days-3/index.html
itinerary/dubai/days-4/index.html
itinerary/dubai/first-time/index.html
itinerary/dubai/index.html
itinerary/dubai/rainy-day/index.html
itinerary/las-vegas/2-days/index.html
itinerary/las-vegas/3-days/index.html
itinerary/las-vegas/4-days/index.html
itinerary/las-vegas/first-time/index.html
itinerary/las-vegas/index.html
itinerary/las-vegas/rainy-day/index.html
itinerary/london/days-2/index.html
itinerary/london/days-3/index.html
itinerary/london/days-4/index.html
itinerary/london/first-time/index.html
itinerary/london/index.html
itinerary/london/rainy-day/index.html
itinerary/new-york/2-days/index.html
itinerary/new-york/3-days/index.html
itinerary/new-york/4-days/index.html
itinerary/new-york/first-time/index.html
itinerary/new-york/index.html
itinerary/new-york/rainy-day/index.html
itinerary/paris/2-days/index.html
itinerary/paris/3-days/index.html
itinerary/paris/4-days/index.html
itinerary/paris/first-time/index.html
itinerary/paris/index.html
itinerary/paris/rainy-day/index.html
itinerary/rome/days-2/index.html
itinerary/rome/days-3/index.html
itinerary/rome/days-4/index.html
itinerary/rome/first-time/index.html
itinerary/rome/index.html
itinerary/rome/rainy-day/index.html
itinerary/tokyo/days-2/index.html
itinerary/tokyo/days-3/index.html
itinerary/tokyo/days-4/index.html
itinerary/tokyo/first-time/index.html
itinerary/tokyo/index.html
itinerary/tokyo/rainy-day/index.html
tests/test_paris_drive_initial_load.cjs
tests/test_paris_family_affiliate_tracking.cjs
tests/test_travelpayouts_drive_removal.py
things-to-do/bangkok/index.html
things-to-do/dubai/aquaventure-waterpark/index.html
things-to-do/dubai/burj-khalifa/index.html
things-to-do/dubai/index.html
things-to-do/index.html
things-to-do/las-vegas/index.html
things-to-do/london/harry-potter/index.html
things-to-do/london/index.html
things-to-do/new-york/index.html
things-to-do/paris/index.html
things-to-do/quebec-city/index.html
things-to-do/rome/index.html
things-to-do/switzerland/swiss-travel-pass/index.html
things-to-do/tokyo/index.html
transport/bangkok/index.html
transport/dubai/index.html
transport/las-vegas/index.html
transport/london/index.html
transport/paris/index.html
transport/rome/index.html
transport/tokyo/index.html
travel-guides/index.html
```

Arrêt pour revue humaine. Les 116 autorisations sont en attente et aucune intervention supplémentaire n'est engagée sans votre prochain accord.
