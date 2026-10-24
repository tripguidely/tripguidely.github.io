# TripGuidely — Automatic Travel Alert Banner V4

Fondation V4 et revue finale du 24 octobre 2026. **GO pour une PR Draft de fondation, sans activation publique.**

## État vérifié et périmètre

Branche : `feat/tripguidely-automatic-travel-alert-banner` ; worktree isolé :
`C:\Users\1995\AppData\Local\Temp\tripguidely-automatic-travel-alert-banner`.
Base : `000285edf8829c261729cd51826c494909e042f3`, dernier `origin/main` récupéré.
Les PR #60, #61, #62 et #63 sont fusionnées ; #63 correspond à cette base.
Les anciens worktrees et la branche de design déjà modifiée n'ont pas été utilisés pour développer V4.

L'API GitHub Pages consultée en lecture indique `build_type: legacy`, source `main`, chemin `/`,
URL `https://tripguidely.github.io/`, sans CNAME. Il ne s'agit pas d'un site servi par un serveur Python.
Les trois workflows existants ont été examinés : audit du site, tests V3 hors réseau et Paris V2.
Le workflow Paris V2 conserve sa planification existante. Seul le workflow de tests V3 est étendu aux tests V4 et à une construction Jekyll de vérification, sans déploiement.
La persistance V3 reste celle de la Phase 4, sans backend distant activé.

Le seul fichier déjà suivi modifié est le workflow de tests V3. Les pages hôtels, les Hero, les liens affiliés,
les SubIDs, les CTA, `affiliate_click`, le consentement, les cartes, les canonicals,
JSON-LD, Paris V2 et le baseline demeurent identiques à la base.
Les composants restent dans `scripts/travel_alert_banner/`, hors assets publics, sans référence dans les pages publiques.

## Démonstration et fichiers

Lancement depuis ce worktree :

```powershell
python -B scripts/travel-alert-banner.py --port 8766
```

Ouvrir `http://127.0.0.1:8766/`. Le serveur écoute exclusivement l'adresse loopback,
ne sert aucun répertoire et n'écrit aucun fichier HTML ou flux dans le site.
Il utilise les validateurs JSON et le catalogue de destinations existants de V3.
Il n'appelle aucun adaptateur en direct et ne charge aucun tracking ni asset distant.

| Cas local | URL / résultat attendu |
|---|---|
| Cyclone fictif | `/?case=cyclone` : un avis marqué SYNTHETIC |
| Santé fictive | `/?case=health` : un avis marqué SYNTHETIC |
| Aucune alerte | `/?case=empty` : aucun bandeau |
| Expiré | `/?case=expired` : aucun bandeau |
| Autre pays | `/?case=other-country` : aucun bandeau |
| Autre ville dans le même pays | `/?case=other-city` : destination inconnue refusée |
| Plusieurs avis | `/?case=multiple` : un seul avis, priorité déterministe |
| Disparition | `/?case=expires-soon` : retrait après huit secondes sans autre requête |
| Panne / JSON invalide | `/?case=unavailable` / `/?case=malformed` : aucun bandeau |

Les références GDACS/WHO du prototype sont des liens officiels de référence seulement,
**elles ne prouvent aucun événement fictif**. Aucune nouvelle intégration WHO n'est réalisée.
Les fixtures sont identifiées comme synthétiques. Aucun faux incident ne devient une alerte réelle.
Le composant refuse les données synthétiques hors de `localhost`, `127.0.0.1` et `[::1]`,
même si le paramètre de démonstration est activé accidentellement.

Fichiers de la fondation et des tests ajoutés :

- `scripts/travel_alert_banner/banner.js` : validation, sélection, rendu texte et retrait.
- `scripts/travel_alert_banner/banner.css` : styles isolés et emplacement réservé.
- `scripts/travel-alert-banner.py` : démonstration loopback et verrou de publication.
- `tests/fixtures/travel-alert-banner/scenarios.json` : scénarios fictifs.
- `tests/test_travel_alert_banner.py` : politique et isolation.
- `tests/test_travel_alert_banner.mjs` : contrat client et réseau simulé.
- `tests/test_travel_alert_banner_browser.mjs` : intégration navigateur locale.
- `docs/travel-alert-banner-v4.md` : présent rapport.
- `_config.yml` : exclusion Pages des seuls nouveaux outils, fixtures, tests et rapport V4.

Fichier existant modifié : `.github/workflows/global-travel-intelligence-v3-tests.yml`.
Le diff final contient neuf ajouts et une modification. Aucun changement du baseline.

## Politique d'affichage et couverture réelle

**Aucune catégorie n'est actuellement qualifiée pour une publication automatique A.**
La fonction `automatic_publication_candidates` retourne toujours une liste vide.
Le composant lui-même refuse actuellement tout flux de production : le contrat implémenté
est un contrat synthétique de qualification, pas un service d'alertes déjà opérationnel.
Un champ `approved: true` dans une donnée non fiable ne constitue pas une autorisation.

| Source opérationnelle V3 | Ce qui existe | Ce qui manque pour un bandeau local réel |
|---|---|---|
| Canada, quatre pays FR/GB/IT/US | Avis nationaux, provenance, changements, revue | Preuve précise du périmètre local et qualification de l'affirmation ; un avis national n'est pas un incident urbain |
| USGS | Séismes, mesures, identifiants, corrections | Impact touristique local établi et autorité compétente ; magnitude, point épicentral et indicateur tsunami ne suffisent pas |
| GDACS | EQ, TC, FL, VO, DR, WF : six familles normalisées | Confirmation locale, géométrie exploitable, statut officiel et droits du produit exact |
| Tsunami associé | Contexte/modèle lié à un événement | Bulletin actif d'une autorité déléguée, zones et dates de validité |
| Santé, guerre, couvre-feu, évacuation, manifestations | Aucune nouvelle source intégrée dans V4 | Source officielle adaptée, droits, portée locale et première validation humaine B |
| Fermetures majeures de transports | Aucune nouvelle source intégrée | Autorité de transport, identifiant, service/zone, validité et validation de la pertinence |

Le cache GDACS `events4app` reste partiel : ce n'est ni une archive complète ni une liste
exhaustive d'alertes locales actives. Les sources conservent leur provenance indépendante ;
le rapprochement USGS/GDACS existant n'efface pas une observation fournisseur.
Aucune proximité géographique arbitraire, égalité de pays ou niveau de danger ne confirme
un hôtel fermé, des morts, des dommages, une évacuation ou un lieu sûr.

Pour une future politique A, qualifier séparément faits, statut actif, zone officielle explicite,
fraîcheur, identifiant/version, source et droits. L'autorisation devra être limitée à une source,
un produit et un type de phrase ; jamais une permission générale de réécriture par IA.
Pour B, l'approbation doit être liée au hash de l'affirmation, à la version du bulletin,
à la destination, à la preuve et à une échéance. Une correction invalide l'approbation ;
aucune relance ne doit prolonger mécaniquement sa durée de vie.

## Exposition Pages et CI de validation

Placer un outil dans `scripts/` ne suffit pas à le retirer de GitHub Pages : l'audit local
et le générateur Jekyll ont des périmètres différents. `_config.yml` exclut explicitement
les nouveaux chemins V4, y compris le rapport, afin de ne créer aucune page ou donnée publique.
Ces [exclusions Jekyll](https://jekyllrb.com/docs/configuration/options/) sont appliquées par la
[construction Pages actuelle](https://docs.github.com/en/pages/setting-up-a-github-pages-site-with-jekyll/about-github-pages-and-jekyll).
Aucune règle ne retire un fichier préexistant. Ajouter `.nojekyll` contournerait cette protection :
le nouveau test d'exposition refuse donc sa présence. Une migration future du mode Pages devra
conserver le filtrage dans son artifact, avec le même contrôle d'absence.

La CI conserve Ubuntu 24.04, Python 3.12, `contents: read`, les déclencheurs PR et manuel.
Elle ajoute Node 22 avec `actions/setup-node` officiel épinglé par SHA, les 42 tests client,
et neuf tests V4 Python aux 148 cas existants : **157 cas Python attendus, zéro ignoré sous Linux**.
Les trois contrôles de chemins et la garde Paris V2 restent obligatoires.
Le garde réseau Python existant couvre aussi les neuf tests V4 ; le fetch Node réel est interdit.
Aucune collecte, publication, nouvelle permission ou planification n'est ajoutée.

Jekyll 3.10.0 correspond à la [version annoncée par GitHub Pages](https://pages.github.com/versions/).
La CI installe ce constructeur dans le répertoire temporaire, construit un artifact de test
également temporaire, puis réexécute les neuf tests V4 avec `BANNER_PUBLISHED_DIR` : les chemins
exclus et `feed.json` doivent être absents, et les HTML hôtels doivent être identiques octet pour
octet aux sources. L'artifact n'est ni téléversé ni déployé. L'installation des dépendances est
l'unique étape réseau ajoutée ; les tests ne consultent aucun fournisseur.
Ruby et WSL ne sont pas disponibles localement ; la construction réelle sera vérifiée sur Ubuntu
par cette CI, et non présentée comme un test Windows déjà exécuté.

## Protection officielle du baseline

Le premier audit a refusé le placement initial du composant dans les assets publics :
`new_integration_needs_review` pour `assets/js/travel-alert-banner.js`.
Le prototype local reste donc dans le répertoire d'outillage `scripts/travel_alert_banner/`,
que l'audit distingue des intégrations du site. Aucun script public ni autorisation baseline
n'est ajouté. Les tests du composant sont exécutés séparément ; un audit du site inchangé
ne constitue pas une validation de son intégration publique.

La future intégration publique nécessiterait une revue explicite de l'autorisation suivante,
à recalculer si le contenu ou la base change :

```json
{
  "kind": "new_integration_script",
  "source": "assets/js/travel-alert-banner.js",
  "base_revision": "000285edf8829c261729cd51826c494909e042f3",
  "before": null,
  "after": "3bf8b0056d512dc319a7974ba4e4c3f28082d721c82769ad4a831dc77d771cdc"
}
```

Il s'agit du hash du prototype actuel, pas d'une autorisation appliquée ou demandée ici.
L'ajout de références dans les HTML nécessiterait également la revue correspondante.

## Contrat, interface et expiration indépendante

Contrat strict v1 : schéma et clés exactes, au plus 20 avis et 64 Kio, textes courts sans HTML
ni contrôles ambigus, identifiants uniques, dates UTC avec validation calendaire,
pays/destination explicitement concordants avec le catalogue pilote.
Les URL sont une liste exacte de références officielles dans cette démonstration.
Une future source réelle exigera l'autorisation de ses URL de bulletin exactes.
Le client ne consulte jamais les fournisseurs externes.

La priorité est fixée par le producteur validé : rang 1 à 3, puis catégorie, date de vérification
décroissante, identifiant stable. Le rang n'est jamais calculé depuis une magnitude ou un
modèle de dommages. Un seul avis est visible ; un avis expiré peut laisser place au suivant
s'il est encore admissible. Les autres ne s'accumulent pas.

Le rendu utilise `textContent`, sans insertion HTML. Requête de même origine, timeout de cinq
secondes, sans credentials, cache, redirection ou referrer ; réponse JSON bornée pendant la
lecture. Un flux invalide entier est refusé. Aucun message « safe » n'est produit.
Le prototype ne réessaie pas en boucle et n'utilise ni service worker ni cache local.

L'échéance absolue du flux et de chaque avis est bornée à une heure dans le prototype,
sans renouvellement local. Un timer efface le texte et le lien à échéance même si Actions
ne redémarre jamais. La sélection est recalculée ; onglet masqué : retrait immédiat ;
retour visible et `pageshow` : revalidation avant affichage. L'horloge combine temps civil
et temps monotone pour éviter qu'un recul de l'horloge prolonge un avis déjà chargé.
La suspension du navigateur diffère d'une exécution continue ; les événements de reprise
empêchent de réafficher un avis périmé. Les [timers peuvent être retardés en arrière-plan](https://developer.mozilla.org/en-US/docs/Web/API/Window/setTimeout).

Limite : le premier chargement dépend de l'horloge du client ; un navigateur compromis ou
une horloge initialement fausse ne constituent pas une source de temps fiable. Une future
qualification publique doit tester une borne de temps serveur/CDN et les politiques de cache,
ainsi que les retours BFCache, veille prolongée et plusieurs navigateurs.
Sans JavaScript, fichier inaccessible, mauvais pays, JSON invalide ou délai dépassé : aucun
bandeau, aucune conclusion de sécurité. Un ancien avis n'est pas réutilisé comme actuel.
L'indisponibilité doit être visible dans le rapport opérateur futur, sans exposer d'erreurs
techniques dans le parcours de réservation.

Le composant est une région avec titre, date machine et lien explicite, notification polie,
focus clavier visible, sans popup ni prise de focus. Les textes restent lisibles et non tronqués.
L'emplacement réservé mesure 9,5 rem sur desktop et 13,5 rem sur petit écran ; le retrait ne
remonte pas le contenu. **Compromis explicite : l'espace reste vide sans avis.**
La carte peut défiler si le texte agrandi dépasse cet espace. Aucun style global n'est changé.
L'impact SEO/affiliation réel est préservé ici par absence d'intégration. Les tests de prototype
ne constituent pas une mesure PageSpeed de toutes les pages de production.

## Architecture automatique minimale proposée, non activée

Réutiliser les adaptateurs et la déduplication V3 : trois états indépendants, rapports par source,
changements nouveauté/correction/expiration/indisponibilité ; dernier état valide conservé.
Le moteur existant garde les observations brutes séparées du futur registre d'avis approuvés.
Une source absente ou une omission de flux n'est jamais une résolution. Le flux public n'expose
que les avis encore admissibles ; l'historique conserve le motif du retrait, sans « all clear ».

| Option | Avantages | Limites / permissions futures |
|---|---|---|
| Workflow Pages complet dans le dépôt actuel | Pas de commit de données ; déploiement d'un artifact | Publie un site complet, pas une surcouche JSON. Risque de remplacer les pages ; `pages: write`, `id-token: write`, `contents: read`. Migration à forte portée : non retenue ici |
| JSON versionné dans le `main` du site | Lecture simple et historique Git | Exige un writer dans le dépôt commercial ; reconstructions fréquentes, conflits et protections de main : non recommandé |
| **Dépôt de données dédié + JSON versionné + Pages de projet** | Petite surface ; historique récupérable ; aucun droit d'écrire le `main` du site | Dépôt à créer seulement après accord ; writer `contents: write` limité au dépôt de données, publication Pages `pages: write` et `id-token: write` sur ce même dépôt |

**Recommandation future : troisième option**, si les conditions Pages et les droits de sources
sont confirmés. Un workflow de données produit un artifact Pages minuscule depuis le snapshot
validé, et le déploie via les actions Pages officielles. L'historique JSON et états est versionné
séparément dans ce dépôt ; ce n'est pas un cache Actions. Un déploiement échoué laisse le précédent
snapshot public, dont les avis expirent néanmoins côté client. Un artifact de revue ne doit pas
être confondu avec un registre durable.

Le Pages de projet pourrait servir `/travel-alerts/alerts.json` sous la même origine github.io,
à vérifier lors de la création du dépôt et si un domaine personnalisé est ajouté. Cette option
**n'est pas encore configurée**. Le composant actuel n'accepte pas de flux cross-origin.
Le dépôt du site n'aurait besoin d'aucun droit d'écriture pour les collectes. Une PR séparée,
approuvée par le propriétaire, ajouterait une seule fois le composant et l'emplacement aux
pages pilotes ; le chargement du JSON s'effectuerait ensuite sans changement quotidien des HTML.

GitHub exige les [permissions de déploiement Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).
Un `GITHUB_TOKEN` utilisé pour committer ne déclenche pas automatiquement les workflows ordinaires :
le futur workflow doit donc committer puis déployer explicitement son snapshot, sans compter
sur une chaîne `push` implicite. Vérifier le SHA attendu avant commit, conflit = relire et recalculer,
jamais force-push. Concurrence unique, `cancel-in-progress: false`, état/manifeste/hash validés,
reprise explicite après corruption, aucun écrasement silencieux. Le stockage Git convient au petit
snapshot d'avis, pas à une archive mondiale illimitée : conserver les journaux détaillés 90 jours,
preuves ciblées jusqu'à 365 jours selon droits/besoin ; prévoir une revue de croissance trimestrielle.
Effacer un fichier Git ne purge pas ses anciennes versions : données publiques non personnelles
uniquement ; politique d'archive/purge à qualifier avant tout volume important.

Cadence proposée, sous réserve des quotas et licences actuels : Canada 6 heures, USGS 15 minutes,
GDACS 30 minutes. Un orchestrateur fréquent peut ne lancer que les sources dues ; aucune cadence
n'est activée ici. Budget de requêtes, timeout, taille, backoff borné avec jitter, respect de
`Retry-After`, un essai par source et rapport d'indisponibilité. Pas de rafale de rattrapage.
Les [exécutions planifiées peuvent être retardées ou perdues](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule) ;
aucune promesse de temps réel. Le système futur fonctionnerait sur runners GitHub, ordinateur fermé.

Séparer le job de collecte en lecture, le job de qualification et le job d'écriture/déploiement.
Les PR et forks ne reçoivent jamais de token d'écriture ou secret. Actions officielles épinglées
par SHA, checkout sans credentials persistants, environnement protégé pour toute première
publication B, règles sans contournement automatique. Sur le dépôt du site : PR obligatoire,
CI requise, pas de push direct ni bypass de bot. Aucune règle GitHub n'a été changée ici.
Prévoir un kill switch, retrait explicite, rapport d'échec, revue des permissions et restauration
sur une version connue valide. Un writer compromis peut fabriquer du JSON approuvé : le client
ne remplace pas les protections de la chaîne de publication.

## Coûts, droits et risques

**Dépense locale engagée : 0 USD.** Aucun abonnement, bucket, compte AWS, secret ou service créé.
Le scénario futur d'un petit dépôt public avec runners Linux standard et Pages est estimé à
0 USD/mois pour le service GitHub dans les conditions actuelles, hors temps humain et domaine.
Les [runners standard des dépôts publics sont gratuits](https://docs.github.com/en/billing/concepts/product-billing/github-actions).
Ce n'est pas une garantie illimitée : Pages a notamment des limites de taille et bande passante,
et des [conditions d'usage](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits).
L'adéquation du site affilié et du futur service de données à ces conditions doit être confirmée
avant de retenir définitivement l'hébergement. Aucun basculement payant automatique autorisé.

Canada : licence gouvernement ouvert et attribution à conserver ; la page catalogue a répondu
403 lors de la vérification web de cette session. Aucun contournement effectué ; requalification
avant publication. USGS : mesures et révisions documentées, crédit U.S. Geological Survey,
droits tiers à vérifier. GDACS : attribution GDACS/Commission européenne/ONU selon produit,
pas de licence générale supposée sur tous les contenus amont ; aucune carte redistribuée ici.
Les [conditions GDACS de mars 2025](https://www.gdacs.org/Documents/2025/GDACS_Terms_of_use_Mar_25.pdf)
indiquent modèles incertains, confirmation nécessaire, couverture/délai non garantis et primauté
des autorités mandatées. Le [format USGS](https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php)
décrit des mesures ; sa fréquence d'actualisation n'accorde aucune preuve d'impact local.

Risques principaux : preuve locale insuffisante, faux positif, source ou runner indisponible,
cache CDN ancien, horloge du client, token writer compromis, erreur de destination, droits tiers,
et intervention humaine non assurée pour B. Les protections et l'expiration réduisent ces risques
sans transformer TripGuidely en service d'urgence. Une observation passée n'est jamais une preuve
que le danger persiste ni qu'il est terminé.

## Critères objectifs pour qualifier une première source

Tous les critères suivants sont bloquants ; aucun score moyen ne compense un échec.

| Critère | Preuve et règle de refus |
|---|---|
| Portée géographique explicite | Zone ou polygone officiel, identifiant stable, correspondance documentée avec la destination/son quartier. Refuser pays seul, proximité, point touristique arbitraire et géométrie incertaine |
| Fraîcheur | Horodatage de publication/révision et dernière vérification réussie ; seuil par produit documenté. Une nouvelle collecte ne renouvelle pas la date du bulletin |
| Statut officiel | Autorité mandatée, bulletin opérationnel réel, statut actif et chaîne de correction/annulation identifiée. Refuser exercice, test, modèle et source non authentifiée |
| Durée de validité | Début et fin exploitables ; échéance publique égale au minimum de la validité officielle, de la fraîcheur autorisée et de l'échéance de validation. Sans fin qualifiée : revue humaine |
| Droits de republication | Conditions actuelles archivées, attribution exacte, droit du produit et des éléments tiers. Pas de logo ou d'approbation implicite |
| Absence d'interprétation sensible | Reprendre le titre officiel et la zone explicitement nommée, sans inférer impact hôtelier, dégâts, victimes ou évacuation. Tout ajout sensible revient en B |

**Premier candidat concret : NWS/NOAA, un seul produit météorologique pour une zone de New York,
par exemple un avis de chaleur, à qualifier avant tout développement d'adaptateur.**
Le [service d'alertes NWS](https://www.weather.gov/documentation/services-web-alerts) documente
les bulletins CAP et leur redistribution. L'[API officielle](https://www.weather.gov/documentation/services-web-api)
est gratuite, nécessite un User-Agent d'identification et applique des limites non chiffrées.
Proposition technique : index `/alerts/active` filtré par zone, puis bulletin officiel par identifiant ;
aucun appel à ces endpoints d'alertes n'est effectué par cette PR.

Qualifier d'abord une zone officielle de quartier/borough par la documentation NWS, sans supposer
qu'un code de zone couvre toute la ville. L'accès de vérification à l'exemple de zone NYZ072
n'a pas abouti dans l'outil web ; ce code n'est donc pas retenu comme mapping validé.
L'équipe doit vérifier la zone, les champs CAP de statut et validité, les références d'annulation,
les URL et les droits avant tout GO d'affichage. La première phrase candidate se limite à
un titre officiel inchangé, sa zone nommée, ses dates et son lien ; aucune synthèse de dommages.

Les [conditions NWS](https://www.weather.gov/disclaimer) permettent généralement la réutilisation
avec exceptions et sans approbation implicite ; un contenu modifié ne doit pas être présenté comme
un produit gouvernemental original. Conserver l'attribution et séparer les libellés TripGuidely.
Plan de qualification : revue humaine d'un petit corpus de bulletins et métadonnées de zones,
fixtures hors réseau pour mise à jour/annulation/fin absente/zone ambiguë, sept jours de shadow
seulement après accord, puis rapport d'écarts et décision propriétaire. Acceptation : aucun faux
rattachement local ni avis expiré, toutes les versions traçables, retraits testés, aucun impact
inventé. Ce candidat n'est pas une source intégrée ou autorisée à publier aujourd'hui.

## Vérifications et plan minimal d'activation

Résultats réellement obtenus dans ce worktree :

| Vérification | Résultat |
|---|---|
| Contrat client Node | 42 tests réussis, zéro ignoré |
| Politique/démonstration Python V4 | 9 tests réussis, zéro ignoré |
| Chrome headless | 13 contrôles réussis, aucune exception JS, aucune requête hors loopback |
| axe-core, WCAG 2 A/AA et 2.1 AA / bonnes pratiques | Zéro violation sur la démonstration |
| V3/Canada/USGS/GDACS/Paris/Phase 4 existants | 148 cas : 147 réussis, un symlink ignoré sous Windows |
| Garde publique Paris V2 | `evergreen` |
| Autotest officiel de l'audit | `passed: true` |
| Audit officiel du site après retrait des assets publics | `passed: true`, zéro erreur, 956 constats historiques inchangés |
| Diff et espaces des fichiers V4 et de la CI | Sans erreur |

Aucune exécution Ubuntu n'est revendiquée pour V4 et aucune sécurité Windows n'a été changée.
Le contrôle de disparition utilise une vraie attente de huit secondes : le texte et le lien sont
retirés, une seule requête de flux est effectuée, et la position du contenu suivant reste identique.
Les événements de visibilité et `pageshow` sont aussi simulés ; une avance puis un recul de
l'horloge ne ressuscitent pas l'avis. Il ne s'agit pas d'un test exhaustif de BFCache natif ou de
lecteur d'écran humain. Les largeurs 320, 390, 768 et 1440 px, le texte agrandi et le focus clavier
ont été contrôlés. Le JS fait 7 995 octets et le CSS 1 168 octets non compressés.

Les preuves sont hors checkout dans
`C:\Users\1995\AppData\Local\Temp\tripguidely-banner-v4-qa-1a6y7o6s` :
`audit-final.json`, `browser-results.json`, `axe.json`, `banner-desktop.png`, `banner-mobile.png`,
`expiry-before.png`, `expiry-after.png`, journaux de tests, `file-manifest.json` et `v4-complete.diff`.

Tests ciblés : `node --test tests/test_travel_alert_banner.mjs` et
`python -B -m unittest discover -s tests -p test_travel_alert_banner.py -v`.
Tests navigateur : `node tests/test_travel_alert_banner_browser.mjs` avec `BANNER_BROWSER_TOOLS`
et `BANNER_AXE_TOOLS` pointant vers des `node_modules` temporaires contenant respectivement
`playwright-core@1.64.0` et `axe-core@4.10.3`, `BANNER_QA` hors checkout, Chrome local installé.
Aucune dépendance de test n'est ajoutée au site. L'outil d'interface n'ayant aucun navigateur
connecté, les captures proviennent des tests Chrome headless, pas d'une session utilisateur pilotée.

Les résultats finaux et les captures de disparition sont consignés dans le dossier QA externe.
La CI conserve les 148 cas V3 existants et exige désormais 157 cas Python au total ;
les 42 tests Node s'exécutent dans une étape distincte. Les 13 contrôles navigateur restent locaux.

Avant activation :

1. Valider la démonstration et le compromis d'espace réservé sur une page pilote.
2. Qualifier une source locale précise et ses droits ; désigner le responsable de revue B.
3. Approuver le contrat de production (source, preuve, géographie, approbation liée au hash, TTL),
   puis étendre le composant avec tests dédiés ; le verrou actuel interdit cette publication.
4. Autoriser séparément le dépôt de données, ses règles, les permissions minimales et la CI hors réseau.
5. Exécuter le mode shadow sans publication ; tester panne, corruption, conflit, expiration, cache
   CDN, BFCache, reprise, plusieurs navigateurs, budget et restauration.
6. Approuver une PR limitée à une destination puis un premier avis humainement validé ; tester le
   retrait et le kill switch. Autoriser une planification seulement après ces validations.

**Verdict : GO pour une PR Draft de fondation. Activation publique non autorisée et non prête ;
aucune publication automatique de catégorie A admissible avec les seules sources actuelles.**
La revue autorise uniquement un commit ciblé, le push de cette branche et une PR Draft.
Aucun merge, déploiement, secret, changement de permissions, dépôt de données distant ou activation planifiée.
