# TripGuidely — Phase 5: NWS New York automatic advisory qualification

24 octobre 2026. **GO pour revue finale et PR Draft ; aucune activation autorisée.**
Branche `feat/tripguidely-nws-automatic-alerts`, worktree
`C:\Users\1995\AppData\Local\Temp\tripguidely-nws-automatic-alerts`.
Base `d5ffa70f5e37cecfcc9477f2df160b8616d3c94c` : PR #64 fusionnée, dernier `origin/main` récupéré.
Le propriétaire autorise désormais un commit ciblé, le push de cette branche et une PR Draft
après validation locale. La validation Ubuntu se fera sur cette PR ; aucune fusion, collecte
planifiée, publication, dépense, permission supplémentaire ou activation n'est autorisée.

## Pages existantes et intégration préparée

Douze routes existantes possèdent un vrai contenu et une destination NYC :

- `/hotels/new-york/`
- `/hotels/new-york/cheap-hotels/`
- `/hotels/new-york/family-hotels/`
- `/hotels/new-york/luxury-hotels/`
- `/things-to-do/new-york/`
- `/car-rental/new-york/`
- `/itinerary/new-york/`
- `/itinerary/new-york/2-days/`
- `/itinerary/new-york/3-days/`
- `/itinerary/new-york/4-days/`
- `/itinerary/new-york/first-time/`
- `/itinerary/new-york/rainy-day/`

`/transport/new-york/` existe sous forme de placeholder vide : il est exclu. Les pages
peuvent évoquer des excursions ou Newark ; cela n'étend jamais le périmètre de l'avis NYC.
La destination demeure l'identifiant V3 existant `us-new-york-city`, pays US.

Aucun HTML de production n'est modifié. Le bootstrap et le composant restent dans les outils
exclus de Pages. La prévisualisation lit les vrais HTML, retire les scripts tiers et iframes
uniquement dans leur copie en mémoire, ajoute le slot après le Hero et sert des données
synthétiques clairement marquées. Les liens commerciaux des fichiers source restent identiques.
Une future intégration dans les assets/HTML publics nécessitera une revue baseline explicite ;
aucune autorisation n'est ajoutée au baseline dans cette phase.

```powershell
python -B scripts/nws-preview.py --port 8767
```

Démonstration : `http://127.0.0.1:8767/hotels/new-york/`.
Cas : `?case=valid`, `empty`, `expired`, `neighbor`, `malformed`, `unavailable`, `expires-soon`.
Le dernier retire l'avis après six secondes sans nouvelle requête de flux.
Le texte synthétique ne prétend pas rapporter un vrai avis ; son lien est une référence à la
documentation NWS. Un avis réel utilisera l'URL API originale de son identifiant CAP.

## Source et géographie qualifiées

Documentation consultée : [API NWS](https://www.weather.gov/documentation/services-web-api),
[service CAP](https://www.weather.gov/documentation/services-web-alerts),
[conditions NWS](https://www.weather.gov/disclaimer).
Le schéma OpenAPI et les réponses du catalogue et des alertes ont aussi été récupérés en HTTPS,
en lecture seule, avec un User-Agent d'identification. Les réponses réelles restent hors checkout.
Les tests automatiques utilisent exclusivement des fixtures synthétiques et des lecteurs simulés.

Endpoint de collecte fixé : `https://api.weather.gov/alerts/active?area=NY`.
L'index entier de NY permet de voir les références des mises à jour/annulations ; la sélection
locale vient ensuite. Aucun lien de pagination, URL fournie par une alerte, redirection ou URL
libre n'est suivi. Une réponse partielle ou paginée est refusée.

Le [catalogue officiel](https://api.weather.gov/zones/forecast?area=NY), contrôlé le 24 octobre,
confirme les six identifiants suivants. Le champ de catalogue `type` vaut `public` pour ces
zones, servies par le chemin `/zones/forecast/`. État NY et fuseau America/New_York vérifiés.
La date, l'URL et le hash SHA-256 de cette vérification figurent dans le profil local.

| Zone officielle | Libellé d'affichage limité à cette zone |
|---|---|
| NYZ072 | Manhattan |
| NYZ073 | Bronx |
| NYZ074 | Staten Island |
| NYZ075 | Brooklyn |
| NYZ176 | Northern Queens |
| NYZ178 | Southern Queens |

`affectedZones` doit contenir les URL officielles exactes ; ses codes doivent correspondre aux
codes `geocode.UGC`. Seule l'intersection avec cette liste est affichée, toujours préfixée
« New York City ». Northern Queens n'est pas généralisé à tout Queens. Une alerte uniquement
pour Suffolk, Nassau, le Connecticut ou le New Jersey reste exclue, même renvoyée par `area=NY`.
Un point ou une distance n'est jamais utilisé comme preuve. Ce premier profil accepte une
géométrie nulle avec zones explicites et refuse une géométrie non nulle non qualifiée.

La qualification géographique expire **le 23 novembre 2026 à 00:00 UTC**. Le collecteur et le
client cessent alors d'admettre ce profil. Avant cette date, revoir le catalogue et ses changements,
puis approuver et tester une nouvelle révision ; aucune réaffectation géographique silencieuse.

## Produit admissible et limites de l'affirmation

**Un seul type : `Heat Advisory`**, produit météo officiel documenté dans les
[avis de chaleur NWS](https://www.weather.gov/safety/heat-ww). Il est admissible sous toutes
les conditions suivantes, sans prétendre couvrir toutes ses variantes :

- Bulletin NWS Upton NY, sender `w-nws.webmaster@noaa.gov`, langue en-US.
- Statut CAP `Actual`, portée `Public`, catégorie `Met`, message `Alert` ou `Update`.
- Certitude Observed/Likely, urgence Immediate/Expected, sévérité Minor/Moderate/Severe.
- Code produit NWS `HTY`. Réponse Prepare/Monitor/None/Execute. Execute est un champ CAP
  standard observé pour Heat Advisory ; aucune instruction n'est reproduite. Evacuate, Shelter,
  AllClear et les variantes non admises sont retenues pour revue.
- Identifiants cohérents entre Feature, `@id`, identifiant CAP et URL API ; références explicites
  obligatoires pour Update/Cancel ; dates cohérentes, bulletin envoyé il y a au plus 72 heures.
- Information déjà effective ; fin de validité connue et non passée. L'onset peut être futur,
  ce qui décrit un avis prévisionnel, sans prétendre que le phénomène est déjà observé.

Le fait affiché se limite au type officiel émis, aux zones listées et à son lien. Le texte NWS
libre n'est pas paraphrasé ni recopié en description. Le libellé fixe TripGuidely invite à lire
l'original ; aucun dommage, victime, évacuation, fermeture d'hôtel ou impact de transport n'est
inféré. Tornado Warning, tsunami, urgence civile, conflit, santé publique et tous les types
absents de cette liste restent non qualifiés. Une absence d'avis n'est pas une déclaration de sécurité.
`Actual` décrit le statut opérationnel du message CAP, et ne transforme pas une prévision en
observation de dommages. Cette qualification technique n'est pas une approbation de TripGuidely par NWS.

Un échantillon officiel récent du [produit Heat Advisory](https://api.weather.gov/alerts?event=Heat%20Advisory&limit=1),
consulté pour vérifier les champs, présente le code HTY, une géométrie nulle et la réponse Execute.
Il date du 17 octobre, concerne la Californie et est expiré : il n'est jamais projeté vers NYC,
ni affiché comme avis actuel. Cette vérification complète les fixtures sans les confondre avec
un cas réel NYC encore à observer.

Les conditions officielles permettent généralement la réutilisation des produits NWS, avec
exceptions pour les éléments tiers et sans approbation implicite. L'affichage conserve le type,
l'attribution et la source, sans logo ni produit modifié présenté comme bulletin gouvernemental.
L'accès API est gratuit avec User-Agent ; le quota numérique n'est pas publié. Le service CAP
recommande de ne pas interroger plus souvent que toutes les trente secondes. La proposition
est **un GET toutes les quinze minutes**, sans rafale de retry, soit 96 requêtes/jour au rythme nominal.
Aucune garantie de temps réel ou d'exhaustivité ; les délais Internet restent possibles.

## Collecteur et JSON minimal

`scripts/travel_intelligence/nws.py` réutilise les validateurs JSON/temps et le refus des
redirections de V3 ; Canada, USGS, GDACS et Paris V2 ne changent pas.
Une requête fixe HTTPS, corps au plus 2 Mo, MIME GeoJSON/JSON-LD attendu, sans compression
ni cookies/authentification. Timeout socket 15 secondes ; budget de lecture 30 secondes vérifié
entre les lectures, donc une lecture bloquée peut encore consommer son timeout socket.
Ce n'est pas une promesse de délai total strict de trente secondes. Aucun retry automatique.

L'export doit avoir été généré depuis moins de vingt minutes et ne pas être futur. JSON malformé,
identité incohérente, doublon contradictoire ou chaîne de référence invalide rendent la source
indisponible. Les avis non qualifiés sont comptabilisés par motif, sans texte source dans le JSON public.
Une donnée potentiellement HTML ou excessivement longue est refusée, même si elle n'est pas rendue.

Le JSON de projection contient : schema 2, sourceId, policy versionnée, synthetic, status,
generatedAt, expiresAt, puis pour chaque avis : id, event, zones, sentAt, effectiveAt, onsetAt,
verifiedAt, sourceExpiresAt, expiresAt et sourceUrl. L'expiration affichable est le minimum de
l'expiration officielle, d'une fin plus courte, de vingt minutes après vérification et de la
validité du profil géographique. Une collecte ne change pas la date d'émission du bulletin.

Les doublons identiques sont écrasés dans la projection par identifiant, sans répétition visuelle.
Un Update/Cancel retire seulement les identifiants qu'il référence officiellement. Une correction
non qualifiée ne laisse pas l'ancienne version visible. Sans correspondance explicite, les avis
restent distincts. Le client en affiche un seul, d'abord par date d'émission décroissante puis
identifiant ; aucune magnitude ou interprétation d'impact ne détermine la priorité.

Une collecte vide est conservée comme observation technique. La disparition du flux produit
`not_in_current_qualified_feed`, jamais « resolved », « safe » ou « all clear ».
Une panne produit un JSON vide `status: unavailable`, conserve le dernier état vérifié pour audit
et ne le remet pas en publication. Si le futur déploiement échoue, le précédent JSON expire
indépendamment. Les rapports de changements et d'indisponibilité restent séparés du flux public.

## Stockage local et reprise

La CLI n'a aucun mode live implicite. Les sorties dans tout checkout Git, chemins symboliques,
jonctions ou métadonnées Git sont refusées. Exemples vers un dossier temporaire externe :

```powershell
python -B scripts/nws-travel-alerts.py --fixture tests/fixtures/nws/heat-synthetic.json --now 2026-10-24T12:00:00Z --state $env:TEMP/nws-fixture-state --output $env:TEMP/nws-fixture-output
python -B scripts/nws-travel-alerts.py --live --state $env:TEMP/nws-live-state --output $env:TEMP/nws-live-output
```

Tout `--fixture`, même contenant une copie d'un vrai flux, force `synthetic: true`. Les états
fixture/live ne peuvent pas se mélanger ; l'horloge live ne peut pas être forcée. La collecte réelle
locale de qualification du 24 octobre à 20:16 UTC a réussi avec **zéro avis admissible**, aucun événement inventé.
Les exports se trouvent dans le dossier QA externe, pas dans un répertoire `data/` du site.

Le store NWS emploie les écritures atomiques V3 : générations immuables avec hash, pointeur
CURRENT atomique, verrou exclusif et CAS sur la génération attendue. Un conflit ne remplace
pas un état plus récent. Les exports relisent le dernier pointeur sous verrou. Une interruption
entre génération et pointeur conserve l'ancien pointeur ; un rejeu identique est idempotent.
Une corruption ou un historique incomplet est refusé. La reprise exige un token connu :
`--recover-token <hash>` au lieu de `--live`, hors de toute autre exécution ; aucun choix arbitraire
du fichier le plus récent et aucun verrou cassé automatiquement.

Limites locales : 10 000 générations et 1 000 entrées dans la vue récente des changements.
Les générations antérieures gardent leur histoire. Avant la limite, prévoir un checkpoint et une
archive vérifiés. À quinze minutes, 90 jours représentent environ 8 640 générations ; ce prototype
ne met pas en œuvre une purge ni un backend distant. Le hash détecte la corruption ; il ne signe
pas l'identité d'un opérateur malveillant ayant accès en écriture au store.

## Client et expiration

Le bandeau V4 conserve son contrat synthétique v1 et accepte désormais le contrat NWS v2.
Le schéma, les clés, les identifiants, les six zones, l'URL originale, la policy et toutes les
bornes de validité sont revalidés. Les textes et zones affichés sont dérivés de constantes
contrôlées, via `textContent`. Le flux est limité à 64 Kio/20 avis, lu en streaming, même origine,
sans credentials/referrer/cache/redirection et avec un timeout de cinq secondes.

Pour NWS, la réponse doit fournir une date HTTP valide. Le temps client est borné par Date et
Age de la réponse et avance avec une horloge monotone ; un recul local ne ressuscite pas un avis.
Une ancienne réponse rejouée avec une horloge initiale fausse est refusée dans le test navigateur.
Cette protection dépend encore de l'horloge HTTPS/CDN : ce n'est pas un service de temps signé.
Une horloge très future peut masquer un avis valide, ce qui est un échec d'affichage conservateur.

Le timer retire le texte et le lien à échéance, indépendamment de la prochaine collecte. Onglet
masqué : retrait ; retour visible/pageshow : revalidation. Le bootstrap consulte seulement le
JSON de même origine toutes les cinq minutes en premier plan et à la reprise, avec un minimum
de trente secondes entre tentatives. Le navigateur ne consulte jamais NWS directement.
Sans JS ou sur flux inaccessible/invalide/expiré, aucun bandeau, sans message de sécurité.
L'espace réservé reste stable ; il est vide sans avis. Aucun popup ou déplacement de focus.

Les données synthétiques v1/v2 restent interdites hors loopback, même avec le flag demo.
Dans la démonstration NWS, le titre et la description sont explicitement synthétiques et le lien
pointe vers la documentation, pas un faux bulletin présenté comme réel.

## Workflow préparé et publication isolée

`docs/workflows/nws-shadow.yml.example` est un modèle **inerte**, hors `.github/workflows`.
Ubuntu 24.04, Python 3.12, actions officielles épinglées, `contents: read`, concurrence unique,
exécution manuelle uniquement, timeout cinq minutes. Collecte vers runner.temp et artifact de
revue sept jours ; aucune publication Pages, aucun Git writer, aucun schedule actif.
Il n'est pas installé ou exécuté sur GitHub. Un échec source fait échouer le contrôle shadow,
tout en conservant son rapport si disponible.

Le modèle utilise un état temporaire par job : **il n'assure pas la durabilité ni l'historique
entre jobs GitHub**. Cache/artifacts ne remplacent pas un stockage durable. L'idempotence et la
reprise entre collectes sont implémentées et testées localement ; leur transport durable doit
être approuvé avant d'installer une surveillance de production.

Solution proposée après accord : dépôt de données distinct sous le même propriétaire, Pages de
projet servant uniquement `/travel-alerts/nws-nyc.json`. Le dépôt du site demeure sans writer
pour les collectes. Le dépôt de données contiendrait l'état versionné, le journal et les snapshots
non synthétiques validés. Un writer compare le SHA de départ, refuse un conflit, recalcule puis
committe sans force-push ; un déploiement Pages y publie uniquement le snapshot qualifié.
Ne jamais déployer un artifact JSON partiel dans le dépôt du site, ce qui remplacerait le site complet.

Permissions futures à autoriser séparément : `contents: write` uniquement dans le dépôt de données
pour l'état versionné ; `pages: write` et `id-token: write` seulement dans son job de déploiement.
Aucun PAT ou secret inter-dépôt n'est requis dans cette architecture. L'approbation de ces droits,
la création du dépôt et les workflows correspondants restent à faire ; rien n'est configuré ici.
Un token compromis dans le dépôt de données pourrait falsifier un avis : seules les références
protégées et le code approuvé doivent avoir accès au writer. Un navigateur ne prouve pas à lui
seul qu'un JSON a vraiment été produit par NWS.

## Protections et étapes exactes d'activation

Lecture API du 24 octobre : `main` est **non protégée**, aucun ruleset, Actions par défaut en
lecture et création/approbation de PR par Actions désactivée. Aucun paramètre modifié.

1. Soumettre les 17 fichiers dans une PR Draft après revue locale, conformément à l'autorisation
   finale du propriétaire. Attendre les contrôles Ubuntu puis une approbation explicite avant fusion.
   Le workflow de collecte reste un exemple inerte hors de `.github/workflows`.
2. Exiger une PR vers main, une approbation humaine au minimum, révocation après nouveaux commits,
   contrôles V3/V4/NWS offline et Site regression audit requis, branche à jour, conversations résolues,
   interdiction des push directs/force-push/suppressions et aucun bypass pour les automatisations.
3. Valider le profil Heat Advisory, les six zones, la date de revue et les droits ; renouveler la
   qualification avant le 23 novembre. Observer/revoir au moins un vrai bulletin NYC admissible
   avant première publication. Les fixtures ne remplacent pas cette revue de bout en bout réelle.
4. Après accord, installer uniquement le modèle shadow manuel, faire les essais d'indisponibilité,
   annulation, conflit, corruption et reprise, sans Pages. Le shadow peut rester sans aucun avis
   admissible ; cela ne doit jamais être remplacé par un événement fictif.
5. Autoriser le dépôt de données, sa protection et les permissions minimales ; implémenter et
   qualifier le transfert CAS de l'état durable, l'archive 90 jours et les preuves ciblées jusqu'à
   365 jours selon droits/besoin. Définir un responsable de disponibilité et de retrait.
6. Soumettre les assets et slots des pages pilotes à la revue baseline exacte, vérifier le JSON
   de même origine, les dates HTTP/CDN et les caches, puis approuver un premier déploiement limité.
   Tester le retrait et le kill switch ; aucun changement commercial/SEO n'est nécessaire.
7. Autoriser enfin une planification à quinze minutes dans le dépôt isolé. Actions peut retarder
   ou manquer une exécution : l'affichage expirera après vingt minutes, sans promettre du temps réel.
   Définir les notifications opérateur et une revue des coûts, des refus et des mappings.

Coût engagé : **0 USD**, aucun AWS, abonnement, secret ou dépôt créé. L'API NWS est gratuite.
Le futur scénario GitHub public avec runners standard/Pages vise 0 USD/mois sous réserve des
[conditions et quotas GitHub](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits) ;
aucun basculement payant automatique. Pas de promesse d'exhaustivité mondiale ou de disponibilité.

## Fichiers et validation

Ajouts :

- `config/travel-intelligence/nws-nyc.json`
- `scripts/travel_intelligence/nws.py`
- `scripts/travel_intelligence/nws_storage.py`
- `scripts/nws-travel-alerts.py`
- `scripts/nws-preview.py`
- `scripts/travel_alert_banner/nws-bootstrap.js`
- `tests/fixtures/nws/heat-synthetic.json`
- `tests/test_nws_alerts.py`
- `tests/test_nws_alerts.mjs`
- `tests/test_nws_alerts_browser.mjs`
- `docs/workflows/nws-shadow.yml.example`
- `docs/tripguidely-nws-automatic-alerts-phase5.md`

Modifications limitées à `_config.yml`, au composant JS/CSS V4 local, à son test d'exclusion
Pages et au workflow offline V3. Aucun HTML, image, donnée commerciale, CTA, affiliation,
tracking, canonical, JSON-LD, source Paris V2 ou baseline modifié.

- Python NWS : 32 tests réussis, aucune requête réelle pendant les tests.
- Ensemble Python : 189 cas, 188 réussis, un symlink ignoré par Windows. Garde réseau héritée
  par les sous-processus : aucune tentative. La sécurité Windows n'a pas été changée.
- JavaScript : 42 V4 + 28 NWS, tous réussis, zéro ignoré, fetch réel interdit.
- Navigateur local : 12 contrôles NWS sur les routes existantes et 13 contrôles V4 ; accessibilité
  du composant sans violation détectée, responsive, réseau externe bloqué, expiration vérifiée.
- CI préparée : 189 Python attendus sur Ubuntu 24.04/Python 3.12, zéro ignoré, symlink et trois
  contrôles de chemins obligatoires ; 70 tests Node V4/NWS, 25 contrôles navigateur/accessibilité
  sur prévisualisations synthétiques loopback, garde Paris V2, Jekyll d'exclusion et diff check.
  Playwright/axe épinglés sont installés hors checkout ; aucun appel aux fournisseurs dans les tests.
- La CI et le modèle shadow sont validés par actionlint. Les résultats Ubuntu et Jekyll seront
  vérifiés après le push autorisé et reliés depuis la PR. Ruby/WSL absents localement : construction
  Jekyll Phase 5 non revendiquée comme exécutée sous Windows ; elle est préparée dans la CI.
- Audit officiel final, autotest, garde Paris V2 et contrôle du diff : preuves dans le dossier QA
  externe `C:\Users\1995\AppData\Local\Temp\tripguidely-nws-phase5-qa-z_ib4x14`.

**Verdict : GO pour revue et PR Draft, sous réserve des résultats Ubuntu.** L'activation attend la protection de main, le premier
bulletin réel admissible vérifié, la publication/durabilité isolées et les autorisations explicites.
Aucune collecte planifiée ou publication n'est active ; le site public reste inchangé.
