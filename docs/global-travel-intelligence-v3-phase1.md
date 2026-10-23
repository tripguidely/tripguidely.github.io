# Global Travel Intelligence V3 — socle local, phase 1

23 octobre 2026, America/Toronto. Autorisation du propriétaire : implémentation locale uniquement, dans le worktree existant `feat/global-travel-intelligence-v3-architecture`, base `f28ac0d97092732034e6e234517ef8a122b9c145`.

**GO pour le socle local et les essais contrôlés.** Le propriétaire a ensuite autorisé une revue finale, un commit, un push de la branche existante et une PR Draft uniquement. Aucun déploiement, workflow V3, branche d'état distante, changement de permissions ou merge n'est autorisé. Paris V2 reste opérationnelle et inchangée. Le plan d'architecture initial reste conservé localement, hors du commit de phase 1 ; ce document décrit de manière autonome les choix et limites livrés.

## 1. Ce qui est implémenté

```text
Un index Canada → un adaptateur → validation fermée → observations nationales
                                        ↓
État local précédent → comparaison / déduplication → contexte pays des villes
                                        ↓
                          rapports locaux JSON et Markdown
                                        ↓
              nouvelle génération d'état locale, atomique et versionnée
```

Le collecteur est partagé, sans script par pays ou ville. Les registres décrivent quatre pays, quatre régions et les quatre villes pilotes. Les pages hôtels sont des références de contexte pour les rapports, sans injection ni modification de HTML. Aucune géométrie approximative n'est créée et aucune API de géocodage n'est utilisée.

| Fichier créé | Rôle |
| --- | --- |
| `scripts/global-travel-intelligence.py` | CLI locale : replay, collecte Canada explicite ou restauration explicite ; jamais de Git ou publication. |
| `scripts/travel_intelligence/__init__.py` | Version et package du moteur partagé. |
| `scripts/travel_intelligence/validation.py` | JSON borné, clés uniques, texte brut, URL exactes, instants et chemins de sortie. |
| `scripts/travel_intelligence/registry.py` | Schémas de configuration fermés, hiérarchie des lieux, fuseaux et contexte pays → plusieurs villes. |
| `scripts/travel_intelligence/model.py` | Modèle commun fermé, normalisation, identité, comparaison, expiration et rapprochement inter-sources prudent. |
| `scripts/travel_intelligence/providers.py` | Protocole `Adapter`, lot `Batch`, adaptateur Canada multi-pays et un seul endpoint réseau autorisé. |
| `scripts/travel_intelligence/storage.py` | Protocole `StateStore`, backend local à générations, verrou, contrôle optimiste et restauration. |
| `scripts/travel_intelligence/engine.py` | Orchestration, états indépendants des sources, déduplication et rapports sans conclusion de sécurité. |
| `scripts/travel_intelligence/reporting.py` | Rapports locaux, textes distants échappés et écriture atomique des fichiers. |
| `config/travel-intelligence/destinations.json` | France/Paris, United Kingdom/London, Italy/Rome, United States/New York City et leurs parents. |
| `config/travel-intelligence/sources.json` | Canada uniquement, FR/GB/IT/US, licence, allowlist, audience et délais ; publication désactivée. |
| `tests/fixtures/travel-intelligence/canada-pilot-synthetic.json` | Données synthétiques contrôlées, sans conseil de voyage réel. |
| `tests/test_global_travel_intelligence.py` | Tests ciblés déterministes, réseau simulé. |
| Ce document | Utilisation, décisions de stockage, expiration, sécurité, validation et limites. |

Aucun fichier suivi de la base n'est modifié. Le plan d'architecture était déjà un fichier non suivi à l'ouverture de cette phase et n'a pas été réécrit. Les sorties de runtime et de QA restent **hors de tout checkout Git**.

## 2. Adaptateur Canada et pays vérifiés

Source déjà qualifiée par Paris V2 et l'audit V3 : [index officiel EN](https://data.international.gc.ca/travel-voyage/index-alpha-eng.json), [catalogue et licence](https://open.canada.ca/data/dataset/bef2ebb3-ca9a-485f-aaff-5dc36eb89426). Aucun autre fournisseur externe n'est activé. La configuration ne charge pas de module distant ; un adaptateur non reconnu ou un endpoint différent est refusé.

| Code trouvé dans le flux réel | Slug officiel vérifié | Pilote de ville / fuseau |
| --- | --- | --- |
| `FR` | `france` | `fr-paris` / `Europe/Paris` |
| `GB` | `united-kingdom` | `gb-london` / `Europe/London` |
| `IT` | `italy` | `it-rome` / `Europe/Rome` |
| `US` | `united-states` | `us-new-york-city` / `America/New_York` |

Collecte locale réelle réalisée **une fois** avec la CLI à `2026-10-23T22:14:10.554376Z` (18:14 à Toronto) : sortie 0, quatre observations nationales, état local génération 1, aucune publication. Export annoncé : `2026-10-23T20:00:30Z`. Empreinte SHA-256 de la réponse : `dc9d9b4e60824a2808253744a7168d192482b6cdc09cc9fc68dfabfd11827621`. Les slugs et codes ci-dessus ont été vérifiés par le parseur, et pas seulement supposés depuis les noms des villes.

Preuve locale hors dépôt : `reports/report.json` et dossier `state/` voisin dans le dossier temporaire QA de la collecte. Aucun état de runtime ni chemin personnel n'est publié dans cette PR. Le corps brut n'est pas ajouté au dépôt ; l'état local contient les résumés officiels, identités, dates et provenance. Les rapports sont des preuves ponctuelles, pas des avis courants destinés au public.

Le texte du niveau et du résumé reste une **observation d'un bulletin national pour Canadiens**. Il ne confirme ni manifestation, ni épidémie, ni fermeture de station, ni conséquence dans une ville. `severity: informational` décrit la veille de document ; le niveau consulaire original reste dans `source_severity_raw`. L'impact voyageur est `unknown`, le texte public `summary_en` reste null.

L'ajout d'une seconde ville d'un même pays ajoute un contexte dans les rapports sans seconde requête et sans incident local confirmé. L'association est `country_context`, `local_incident_confirmed: false`. Un événement régional ou de portée incertaine ne remonte pas automatiquement vers une ville.

## 3. Utilisation locale et reproductibilité

Python 3.12, bibliothèque standard uniquement. Les données IANA doivent être accessibles à `zoneinfo` : présentes sur Ubuntu ; sous Windows, fournir une base IANA existante. Aucun paquet n'a été installé pour cette phase. Pour la QA de cette machine, le dossier temporaire `tzdata 2026.5` déjà utilisé par V2 a été réutilisé avec `PYTHONPATH` ; ce chemin personnel n'est pas requis par le moteur.

Depuis le worktree, replay reproductible, **sans réseau**, avec des répertoires externes dédiés (adapter les chemins à son environnement) :

```powershell
python -B scripts/global-travel-intelligence.py --input tests/fixtures/travel-intelligence/canada-pilot-synthetic.json --now 2026-10-22T12:00:00Z --state-dir "$env:TEMP/gti-v3-replay-state" --output "$env:TEMP/gti-v3-replay-report"
python -B scripts/global-travel-intelligence.py --input tests/fixtures/travel-intelligence/canada-pilot-synthetic.json --now 2026-10-22T12:10:00Z --state-dir "$env:TEMP/gti-v3-replay-state" --output "$env:TEMP/gti-v3-replay-report"
```

Premier run : `initial_observation`, pas « tous ces événements sont survenus aujourd'hui ». Second run avec données équivalentes : même identité et empreinte sémantique, zéro nouveau changement, génération 2. Utiliser un nouveau répertoire pour un scénario de test indépendant ; ne pas mélanger replay synthétique et état de collecte réelle. Une horloge antérieure au dernier run est refusée.

Collecte réseau locale volontaire, un seul GET global pour quatre pays, sans horloge artificielle :

```powershell
python -B scripts/global-travel-intelligence.py --live --state-dir "$env:TEMP/gti-v3-live-state" --output "$env:TEMP/gti-v3-live-report"
```

`--live` ne programme rien et n'appelle pas V2. Il n'existe aucun mode implicite : `--input`, `--live` ou `--recover-state` est obligatoire. `--now` est refusé avec `--live`. Les répertoires d'état et de rapports doivent être séparés, sans relation parent/enfant, hors de tous checkouts Git et chemins `.git`/`.github`. Un chemin vers le site, un autre worktree, un symlink ou une junction est refusé. Une invocation comme `--output hotels/paris` ne peut pas modifier la page.

Codes de sortie : 0 pour un run local terminé/persisté sans panne source, **toujours couverture partielle** ; 2 si source indisponible/invalide, configuration/état invalide ou persistance échouée. Une indisponibilité peut être correctement journalisée et persistée tout en conservant le code 2. La restauration explicite seule retourne 0 en cas de succès, sans prétendre que la couverture perdue est rétablie.

Rapports produits : `report.json` et `report.md` seulement. Pas de patch, Draft PR, texte public approuvé, email ou notification. Chaque rapport porte un `run_id` ; les deux fichiers sont remplacés atomiquement individuellement. Une interruption entre ces deux remplacements peut laisser deux run IDs différents : le JSON est la référence de reprise, jamais le Markdown seul. Une erreur d'écriture ne transforme pas un run en publication.

## 4. Modèle commun réellement accepté

Le schéma exécutable et fermé est dans `model.py` (`FIELDS`, `SEMANTIC_FIELDS`, `validate_event`). Toute clé inconnue est rejetée ; les timestamps sont convertis UTC avant comparaison. Le modèle de cette phase est volontairement plus restrictif que le schéma futur de l'architecture : **approbation humaine, texte public et publication ne sont pas implémentés**.

| Groupe | Champs et contraintes principales |
| --- | --- |
| Identité | `schema_version: 3`, `source_id`, `source_event_id` et `event_id = gti- + SHA256([source_id, source_event_id])`. Révision du document distincte de l'identité. |
| Type | `record_kind`: advisory/incident/publication_notice ; catégorie dans l'ensemble fermé de `CATEGORIES`. Canada ne produit que `travel_advisory`. `severity` limitée à unknown/informational tant que la revue d'impact n'existe pas. |
| Géographie | `country_code`, `country_codes`, `region`, `city`, `affected_locations`, `geographic_scope`, `geographic_basis`. Pays/parents/lieux cohérents ; portée pays ne peut contenir une ville ; ville/région explicites requièrent leur ID. Aucune géométrie activée. |
| Dates | `starts_at`, `ends_at`, `published_at`, `source_published_date`, `first_observed_at`, `observed_at`, `last_verified_at`, `review_due_at`, `fresh_until`, `source_updated_at`. ISO/RFC3339 avec offset obligatoire pour les instants ; précision date seule conservée sans inventer minuit. Fin doit suivre début. |
| Origine | `source_url` officielle exacte, `source_status`, `verification_method`, `confidence`, `confidence_basis`, `source_revision`, `source_severity_raw`, `source_data`, `provenance`, `content_hash`, `related_event_reference`, `withdrawal_evidence_url`. Retrait exige preuve officielle explicite. |
| Contrôle | `human_review_status` pending/not_requested/rejected/needs_reverification, `publication_status` **withheld uniquement**, `summary_en` **null uniquement**, `traveler_impact` **unknown sans texte**, `audience_nationalities` égal au profil de la source. Un état contenant approved/published est refusé. |
| Cycle de vie | `lifecycle_status`: active/review_overdue/expired/withdrawn/unverifiable. « Active » signifie seulement échéances techniques non écoulées ; cela ne signifie jamais danger confirmé ni destination sûre. |

Validation JSON : 2 Mo d'entrée, 10 Mo d'état, profondeur maximale 32, tailles de collections/texte bornées, UTF-8, clés uniques, rejet de NaN/Infinity et `1e999`. Les booléens ne sont pas acceptés comme timestamps ou indicateurs entiers. Texte NFC normalisé, sans balise ; contenu distant échappé dans Markdown. Aucun contenu distant n'est exécuté.

Dates : UTC en état, fonction `local_time` pour les fuseaux IANA des pilotes et tests DST. Offset absent/heure locale ambiguë sans offset : refus. Date de publication ≠ début d'un événement. Date de collecte ≠ publication ni validation humaine. Publication/génération future incohérente, export Canada >48 h, slug/code inattendu, nouveau niveau consulaire inconnu ou absence d'un pays pilote : lot Canada intégralement refusé, sans commit partiel de pays.

## 5. Déduplication, classification et rapports

La comparaison ignore l'heure de collecte et de génération de l'export dans l'empreinte sémantique, mais conserve les dates officielles de publication/révision, niveau, résumé, zone et identité. Les espaces, ordres sans sens et offsets équivalents sont normalisés. Modification de niveau → `severity_changed` ; autre modification pertinente → `new_information`. Un duplicata exact dans un lot est consolidé ; deux contenus contradictoires pour le même ID dans le même lot font échouer ce lot.

Entre sources : **aucune fusion de deux avis nationaux** ou de titres ressemblants. Pour le modèle générique, un incident peut seulement former un *groupe candidat de revue* si deux sources ont une référence officielle commune explicite, la même catégorie, une portée précise identique et les mêmes bornes temporelles. Les deux observations restent séparées, `merged: false`, `needs_human_review: true`. Les tests de cette situation utilisent une seconde source synthétique injectée en mémoire ; aucun second fournisseur réel n'est activé.

Rapports : nouveaux changements séparés des éléments toujours en attente, absence de changement seulement après comparaison valide, diagnostics de source, perte de fraîcheur, dépassement de revue, retrait étayé, rétablissement source et panne de persistance. Une panne répétée ne devient pas un nouvel incident à chaque run ; elle reste visible dans les diagnostics et `no_change` reste false. Un trou >12 h depuis le dernier succès Canada est signalé ; le feed courant ne permet pas de reconstituer les changements intermédiaires.

Une réponse valide qui omet une ancienne observation ne l'efface pas : `unverifiable`, jamais `withdrawn` ni « fin du danger ». Lors d'une panne, le dernier contenu valide, `observed_at`, `last_verified_at` et sa borne de fraîcheur sont conservés. Les autres adaptateurs pourront avoir leurs propres états/échecs grâce au protocole partagé ; ils devront être qualifiés et enregistrés dans le code avant activation.

## 6. Stockage local retenu et restauration

### Backend livré

`StateStore` expose `load(now) -> Snapshot` et `commit(data, expected_token, now) -> Snapshot`. Une future implémentation Git peut respecter cette interface sans réécrire l'adaptateur Canada. **Aucun backend Git distant ni commande Git n'est livré dans le moteur.**

```text
state-dir/
  CURRENT.json
  generations/
    00000001-<sha256>.json
    00000002-<sha256>.json
  .writer.lock                       # uniquement pendant une écriture/restauration
  recovery-pointer-<sha256>.bin       # preuve bornée lors d'une restauration explicite
```

Chaque génération contient schéma, numéro, jeton de la précédente, instant et état complet (observations + statuts par source). Le nom de fichier inclut son hash canonique. À la lecture, toute la chaîne sélectionnée est validée : contenu/hash, lien au parent, ordre chronologique, schéma des événements et empreinte de configuration. Un changement de registre exige une migration explicitement conçue ; le moteur ne supprime pas silencieusement les anciennes données devenues incompatibles.

Commit local : validation → acquisition d'un verrou exclusif → relecture de CURRENT → comparaison du jeton attendu → écriture d'une génération immuable avec flush/fsync → remplacement atomique de CURRENT sur le même système de fichiers. Conflit : refus, aucun écrasement de la génération plus récente. Un seul writer local à la fois ; ne pas utiliser ce backend comme verrou distribué entre runners ou sur un partage réseau non validé.

Un crash avant remplacement du pointeur laisse la génération précédente sélectionnée et peut laisser un fichier orphelin. Un retry exactement identique peut réutiliser cet orphelin après validation. Si l'écriture durable échoue, le rapport est `persistence_failed`, `committed: false` ; rien n'annonce un curseur acquis. La prochaine exécution repart du dernier état réellement sélectionné. Le job de collecte ne met jamais à jour un pointeur à partir d'une réponse invalide.

### Restauration explicite

```powershell
python -B scripts/global-travel-intelligence.py --recover-state --state-dir "$env:TEMP/gti-v3-live-state" --output "$env:TEMP/gti-v3-recovery-report"
```

Pas de collecte réseau dans cette commande. Elle examine les générations existantes, choisit la plus récente dont **toute la chaîne** est valide, archive les premiers 1 025 octets au maximum du pointeur remplacé, puis remplace CURRENT atomiquement. Fichiers corrompus et anciennes générations restent disponibles pour investigation. Plusieurs têtes valides concurrentes de même numéro : restauration ambiguë, refus de deviner. Aucun état valide : refus, pas de réinitialisation silencieuse. Après retour à une ancienne génération, le rapport exige revue du trou ; les dates par source permettent de détecter la couverture perdue au prochain run.

Un verrou laissé par un processus interrompu n'est jamais cassé automatiquement. Vérifier d'abord qu'aucun writer n'est actif ; conserver une copie de preuve et retirer **uniquement** `.writer.lock` hors ligne après cette vérification, puis lancer la restauration. Aucun nettoyage récursif ni effacement automatique d'historique n'existe.

Bornes de phase 1 : 1 000 observations, 1 000 générations, 10 Mo par génération, 1 100 fichiers candidats lors de la restauration. À la limite, refus explicite ; pas de pruning ou compaction automatique risquant la provenance. La lecture complète de l'historique coûte davantage à mesure qu'il croît ; un pilote court suffit ici, rotation/compaction sera une décision de la persistance de production. Fichiers fsync avant remplacement ; synchronisation du répertoire sur POSIX, pas de garantie universelle de coupure électrique sur tous systèmes Windows. Les hashes détectent incohérences/corruptions, ne sont pas une signature contre un utilisateur local capable de réécrire tout l'historique. Droits du compte local et sauvegarde hors machine restent nécessaires. Ce stockage est durable sur disque, pas une sauvegarde distante déjà acquise.

## 7. Option prioritaire : branche Git d'état, avant toute activation

### Vérifications effectuées en lecture seule

API GitHub consultée le 23 octobre 2026 : dépôt **public**, branche par défaut `main`, taille déclarée 129 351 Ko ; permissions par défaut des workflows **read**, `can_approve_pull_request_reviews: false` ; API de branche : **`main.protected: false`** ; liste des rulesets renvoyée vide. Ce sont des observations de configuration à cet instant, pas une modification. Les droits administrateur du compte humain connecté ne doivent pas devenir les droits d'un collecteur.

La [documentation GITHUB_TOKEN](https://docs.github.com/en/actions/tutorials/authenticate-with-github_token) permet des permissions par job. La [mise à jour d'une référence Git](https://docs.github.com/en/rest/git/refs#update-a-reference) nécessite `Contents: write` pour les jetons concernés et permet le refus des mises à jour non fast-forward avec `force: false`. Ces droits sont à l'échelle du dépôt ; ils ne constituent **pas** une permission limitée à `state/*.json` ou à une seule branche.

| Aspect | Évaluation / exigence future |
| --- | --- |
| Permission minimale de collecte | Lecture seule ; pas de secret pour Canada. Aucun changement à faire pour cette phase locale. |
| Écriture d'une branche d'état dans ce dépôt | Un writer aurait besoin de `contents: write`, limité au seul job de confiance ; pas de permission workflows/PR/Pages. Cette permission peut néanmoins permettre d'autres écritures de contenu si les règles de branche ne les bloquent pas. |
| Limitation stricte des chemins | Une allowlist dans le writer empêche les erreurs ordinaires mais n'est pas une frontière GitHub contre un jeton compromis. Une branche dédiée seule n'apporte pas l'isolation demandée. |
| Protection effective | Avant tout writer : protéger `main` et les autres références de code, exclure le bot des bypass correspondants, tester les refus réels avec un mécanisme autorisé. Les [rulesets disponibles](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets) ont des capacités/conditions de plan ; ne pas présumer qu'une restriction de chemins de push est disponible sur ce dépôt public. Aucune règle créée ici. |
| Concurrence | Sérialisation par groupe Actions + relecture du SHA de branche + commit parent attendu + mise à jour fast-forward sans force. Deux commits frères : un seul doit être accepté, l'autre recharge/recompare ; pas de force-push. Un PATCH de ref n'est pas à lui seul une transaction CAS avec paramètre « ancien SHA ». |
| Code exécuté | Collecte sur code de confiance, pas PR/fork avec secrets ; writer séparé ne revalide que des JSON bornés et ne lance jamais du code de la branche d'état. Pas de workflows ou de Pages sur cette branche. |
| Historique/restauration | Commits de données seulement, journal versionné ; validation avant restauration. Un retour à une ancienne donnée devient un nouveau commit revu, jamais suppression forcée d'historique. |
| Visibilité | Branche d'un dépôt public visible publiquement, y compris historique. Données officielles et provenance uniquement ; aucun jeton, donnée de voyageur, identité privée de relecteur ou corps sous licence incompatible. Supprimer un fichier courant ne supprime pas son histoire. |
| Coûts | [Runners standards d'un dépôt public gratuits](https://docs.github.com/en/billing/concepts/product-billing/github-actions) pour les minutes ; stockage, historique et quotas ne sont pas illimités. Ne pas augmenter cache/plan ou acheter service. Le backend local n'emploie aucune minute Actions. |

**Décision retenue pour maintenant : local seulement.** L'option branche technique dans ce même dépôt reste conditionnelle et **NO-GO pour activation dans la configuration observée**, car l'isolation vis-à-vis de `main` n'est pas démontrée. Alternative plus robuste à soumettre : dépôt d'état distinct + App limitée à ce dépôt, avec branche d'état dédiée ; cela réduit la portée d'un jeton compromis mais demande votre accord pour ressources/secrets supplémentaires. Pas de PAT personnel administrateur comme raccourci.

## 8. Expiration sûre sans dépendance au workflow

Dans le moteur : `lifecycle(event, now)` compare des dates absolues et fonctionne sans réseau ni Actions. `fresh_until` Canada est le minimum de la génération source +48 h et de l'observation +12 h. `review_due_at` initial vaut observation +24 h ; un polling inchangé **ne prolonge pas** ce délai de revue. Une modification substantielle ouvre une nouvelle échéance de revue, avec `needs_reverification`, toujours sans droit de publier. Une panne ne fait avancer aucune date de vérification de l'événement. Une échéance dépassée n'est jamais une preuve de résolution.

Un état ou un ancien rapport sauvegardé est un snapshot ; son champ `active` ne doit pas être lu des jours plus tard sans recalcul de `lifecycle(event, now)`. Les rapports locaux ne sont pas publiés et **aucune donnée V3 n'est intégrée aux pages** : l'arrêt des workflows V3 ne peut donc laisser une nouvelle alerte V3 confirmée visible.

**Solution précise à approuver avant toute intégration publique :**

1. HTML durable sans fait temporaire : titre Travel Updates, liens officiels et limites de couverture. Sans JavaScript, cette référence reste utile ; pas d'alerte temporaire inscrite dans le HTML ou le JSON-LD.
2. Couche progressive ultérieure facultative, masquée/absente par défaut ; elle ne reçoit que des versions déjà approuvées et des droits d'usage confirmés. Pas d'accès direct du visiteur aux feeds opérateurs si leurs conditions exigent rehosting.
3. Avant chaque affichage, vérifier schéma/version/destination, heure de génération, dernière vérification et `display_until = min(fin connue, review_due_at, approval_expires_at, fresh_until, limite de licence)`. Aucun nouvel avis sensible sans approbation liée à son hash. Un polling ne renouvelle pas une approbation.
4. JSON expiré en cache, fetch échoué, JS absent ou erreur de validation : seulement liens permanents. Timer, retour de visibilité et `pageshow` réévaluent avant affichage ; expiration enlève l'avis sans PR manuelle et sans annoncer la fin du danger.

Cette couche **n'est pas implémentée ni activée dans la phase 1**. Une horloge client incorrecte et un retrait nouveau non encore collecté restent des limites. Sur GitHub Pages statique seul, garantir le retrait d'un fait temporaire déjà inscrit en HTML sans JS et sans nouveau déploiement est impossible ; cela demanderait une couche serveur/edge distincte. Le choix proposé évite ce cas en gardant les faits temporaires hors du HTML sans JS.

## 9. Compatibilité et migration Paris V2

Le script, registre d'événements, tests et workflow Paris V2 ne sont ni importés ni modifiés par V3. Les principes prouvés sont repris : même URL fixe Canada, normalisation texte, format/niveau/flags contrôlés, absence de publication et bonne conservation après panne. Le namespace et le schéma d'état V3 sont distincts du cache V2. Pas de conversion implicite du cache V2 ou des fiches historiques sans heure de vérification.

Migration future proposée : capture autorisée du dernier état V2 → importateur versionné à concevoir, conservant les signatures et provenance V2 dans une enveloppe séparée → comparaison FR V2/V3 sur le **même payload capturé**, sans double polling de production → restauration/rollback testés → bascule de propriétaire du collecteur lors d'une intervention autorisée. Conserver le dernier snapshot V2 et la possibilité de revenir à son fonctionnement. Le schéma actuel refuse un état d'une autre version/configuration au lieu de l'écraser.

Aucun deuxième collecteur de production n'est programmé. La sonde V3 de cette phase est un essai local ponctuel autorisé ; le workflow Paris continue seul en production. Déploiement V3 et éventuel retrait V2 doivent être coordonnés dans une autorisation ultérieure pour éviter interruption, perte de comparaison ou requêtes redondantes.

## 10. Tests, invariants et limites

Tests ciblés :

```text
python -B -m unittest discover -s tests -p test_global_travel_intelligence.py -v
python -B -m unittest discover -s tests -p test_paris_travel_intelligence.py -v
python -B scripts/paris-travel-intelligence.py --check-public
git diff --check
```

La suite V3 n'utilise aucun réseau réel : payload synthétique figé au 22 octobre 2026 à 12:00 UTC, horloge injectée et mocks d'erreurs HTTP. Elle couvre collecte multi-pays et multi-villes ; national ≠ local ; région incorrecte ; doublons intra/inter-sources ; absence de position ; offsets/DST/date seule ; péremption sans workflow ; source inaccessible/429/timeout ; JSON malformé, doublons de clés, profondeur et taille ; lot partiellement invalide ; disparition de record ; état absent/corrompu/configuration changée ; historique/restauration ; verrou/conflit de génération ; crash avant pointeur ; redirections/HTML/compression/URLs hostiles ; injection Markdown ; CLI bout en bout et conservation des références Git/protections V2.

Un test symlink est conditionnel : Windows peut refuser sa création faute de privilège. Dans ce cas il est explicitement marqué skipped ; les refus de chemins vers checkouts et Git sont néanmoins testés. Aucun test ne modifie les pages, le baseline, les règles GitHub ou `main` ; les fixtures et sorties temporaires sont isolées.

Résultats finaux du 23 octobre 2026 : **79 tests ciblés découverts, 78 réussis, 1 skipped** (symlink Windows) : 49 tests V3 dont 48 réussis, et les 30 tests Paris V2 réussis. Garde Paris hors réseau : **evergreen**. Audit officiel en lecture seule contre `f28ac0d97092732034e6e234517ef8a122b9c145` : **`passed: true`, `errors: []`**. Vérification syntaxique des dix fichiers Python nouveaux (tests inclus), `git diff --check` et whitespace des nouveaux fichiers effectués. Les tests ont utilisé le shell Windows PowerShell explicite après un échec de lancement du shell d'escalade par défaut ; aucune modification de dépendance n'a été nécessaire.

Les limites restent : un seul fournisseur réel, conseils nationaux pour Canadiens, aucune couverture locale santé/sécurité/transports ajoutée ; pas de preuve d'exhaustivité, pas de restitution des changements intermédiaires du feed ; pas d'importateur V2, backend Git, approbation/publication ou composant public. Les formats/protocoles sont extensibles, leur ajout n'est pas activé par simple configuration distante.

## 11. Coûts et accords encore requis

Coût de service engagé : **0**, pas d'API payante, de dépendance installée ou d'exécution Actions V3. Une requête Canada a vérifié le fonctionnement local ; la charge habituelle de cette phase dépend uniquement de vos lancements locaux. Disque et historique augmentent avec les générations ; pas de coût distant ou de rétention GitHub présumé déjà validé.

Accords nécessaires avant la suite :

- Choix de branche/dépôt d'état distant, protections effectives et permissions/secrets du writer ; **aucune création de branche distante ni hausse de droits sans accord supplémentaire**.
- Autorisation d'un workflow/planification et organisation de la bascule avec V2 ; pas de polling redondant.
- Validation du mécanisme public d'expiration, organisation de la revue et autorisation de toute modification de page/publication.
- Qualification et autorisation de chaque nouveau fournisseur, bibliothèque optionnelle ou service payant.
- Commit, push de la branche existante et PR Draft sont autorisés après validation finale ; merge, déploiement, activation et changement de droits exigent toujours un accord distinct.

**Verdict limité : GO pour le socle local de phase 1 ; production, stockage distant et publication restent en attente des accords ci-dessus.**

## 12. Revue finale et protections recommandées

Périmètre du commit proposé : **les 14 fichiers de phase 1 listés en section 1**, dont ce document. Le plan d'architecture antérieur non suivi reste local et n'est pas inclus. Aucun fichier suivi de `main`, workflow, page publique, baseline ou état de collecte ne figure dans le diff proposé.

Nouvelle inspection GitHub en lecture seule le 23 octobre 2026 : `main` pointe toujours sur `f28ac0d97092732034e6e234517ef8a122b9c145`, `protected: false`, aucun ruleset retourné, permissions Actions par défaut `read`, approbation de PR par Actions désactivée. Aucun réglage n'est changé dans cette phase.

Protections à faire approuver puis configurer séparément :

- PR obligatoire vers `main`, au moins une approbation humaine, invalidation des approbations après modification substantielle et conversations résolues avant fusion.
- Audit existant `Site regression audit / audit` requis après vérification de son nom de check réel ; base à jour et interdiction de fusion en cas d'échec. Le job Paris `validate` reste soumis à ses filtres de chemins actuels : ne pas en faire un contrôle requis inconditionnel sans traiter les PR où il ne s'exécute pas.
- Contrôle Ubuntu V3 hors réseau recommandé pour une phase CI ultérieure autorisée ; il n'existe pas dans cette PR. Ne pas déclarer comme requis un check jamais exécuté ou systématiquement absent. Les tests V3 de cette revue sont locaux et ne doivent pas être présentés comme des tests Actions.
- Push directs, force-push et suppression de `main` interdits ; protections applicables aussi aux administrateurs, sans bypass accordé aux bots de collecte. Limiter les droits d'écriture du dépôt aux acteurs nécessaires.
- Workflows par défaut en lecture ; futur collecteur `contents: read`, checkout sans credentials persistés, actions épinglées à des SHA revus, aucun secret sur code PR/fork et aucun `pull_request_target` pour exécuter ce code. Revue humaine des modifications de workflows et de permissions.
- Aucun writer d'état dans cette phase. Un éventuel writer futur serait séparé et limité au stockage technique autorisé ; `contents: write` ne fournit pas à lui seul une restriction à un dossier ou une branche. Ne pas utiliser les droits administrateur du compte humain comme credentials d'automatisation.

Ubuntu local : `wsl --list --quiet` indique que WSL n'est pas installé ; aucun Docker disponible dans les commandes trouvées. Ni installation, ni changement des privilèges Windows, ni ajout d'un workflow ne sont réalisés pour contourner cette limite. Le test de création de symlink peut donc rester skipped sur cette machine et la limite doit être conservée dans le rapport.

L'ouverture de la PR peut déclencher l'audit PR existant, en lecture seule. Aucun lancement manuel d'Actions, déploiement ou activation V3 n'est prévu. La réussite de cet audit ne remplace pas les tests locaux V3 ni une autorisation de fusion.

Validation de cette revue : nouvelle exécution locale des suites V3 et Paris V2, **79 tests, 78 réussis et un symlink skipped**, garde Paris **evergreen**. Analyse des 14 fichiers : aucun secret réel, credential, donnée voyageur ou état de runtime identifié ; les valeurs `secret` des tests sont des sentinelles synthétiques. Aucun import de client GitHub/Git/subprocess dans le moteur ; le seul accès réseau est un GET Canada fixe. L'audit final du site est réalisé une seule fois après finalisation du diff ; son résultat et celui des Actions de la PR sont à distinguer dans le rapport de livraison.

Paris V2 : workflow `active`, dernière exécution planifiée observée [39937722426](https://github.com/tripguidely/tripguidely.github.io/actions/runs/39937722426) réussie. GitHub Pages utilise `main` et `/`, mode `legacy`, état `built` : le push de cette branche de fonctionnalité n'est pas un déploiement du site et n'active aucun collecteur V3.
