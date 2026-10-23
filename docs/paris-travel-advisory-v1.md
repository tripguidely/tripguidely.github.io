# Paris travel advisory V1

> Historique V1 conservé. La [V2 locale](paris-travel-intelligence-v2.md) reprend
> la section et les trois liens ; elle archive les avis temporaires ci-dessous
> et prépare une veille partielle avec validation humaine. Aucun workflow activé.

Branche : `feat/paris-travel-advisory-v1`, worktree isolé dans
`C:/Users/1995/AppData/Local/Temp/tripguidely-paris-travel-advisory-v1`.
Base : `27c98abb1185da3364ecf7ac904e33117f729f99`, dernier `origin/main`
récupéré le 22 octobre 2026. La branche n'existait pas avant cette intervention.
La mission V1 initiale n'autorisait aucun commit, push, PR, merge ou déploiement.
L'autorisation finale V1/V2 permet désormais le commit, le push de cette branche
et une PR Draft après validation. Merge et déploiement restent non autorisés.

## Vérification des sources : 22 octobre 2026

- [RATP, bulletin général](https://www.ratp.fr/infos-trafic) : restrictions
  explicitement datées du 22 octobre à 22 h et du 24 octobre à 9 h, heures de
  Paris. Le premier avis cite République, Châtelet, Les Halles et
  Châtelet–Les Halles, sans arrêts ni correspondances. Le second, associé à une
  manifestation, cite notamment Charles de Gaulle–Étoile, Concorde et Tuileries,
  et subordonne la réouverture à l'autorisation de la Préfecture. La note donne
  des exemples et renvoie au bulletin pour la liste complète et les itinéraires.
  Elle ne donne pas de date de réouverture inventée.
- [Gouvernement du Canada, France](https://travel.gc.ca/destinations/france) :
  page affichant une mise à jour au 19 octobre 2026, 18 h 38 ET ; prudence accrue
  pour menace terroriste, recommandations d'éviter les manifestations et de
  s'adapter aux perturbations. C'est un conseil national, distinct des restrictions
  RATP locales. Les mentions nationales d'incidents et de couvre-feux ne permettent
  pas de les attribuer à Paris ou à un hôtel ; elles ne sont pas reprises.
- [SNCF Connect, transports perturbés](https://www.sncf-connect.com/aide/informations-situation-perturbee) :
  conseils accessibles pour vérifier son train par numéro et date. La mention
  générale d'une tempête ne confirme aucune restriction parisienne précise ;
  aucune fermeture SNCF liée à cette tempête n'est affirmée.
- [France Diplomatie, Visiting France](https://www.diplomatie.gouv.fr/en/services-to-foreigners/visiting-france) :
  page touristique accessible, mise à jour affichée au 16 octobre 2026 ;
  aucun avis opérationnel local pertinent sur cette page.
- [Préfecture de Police](https://www.prefecturedepolice.interieur.gouv.fr/) :
  accès direct limité à une demande JavaScript/cookies. Aucun arrêté ni périmètre
  local n'a pu être vérifié directement. L'attribution à la police des fermetures
  et conditions de réouverture repose uniquement sur le bulletin officiel RATP.

Aucune fermeture d'hôtel ou d'attraction ni danger propre à un établissement ou
quartier n'est établi par ces sources. Aucune vidéo ni source virale utilisée.
La recommandation de vérifier l'accès à une attraction est un conseil de
préparation ; elle n'affirme pas que l'attraction est fermée.

## Contenu et entretien

Les quatre pages contrôlées et modifiées sont :

- `hotels/paris/index.html` : courte section anglaise `#travel-updates`, après les
  breadcrumbs et avant la navigation ; date de vérification visible, heures de
  Paris explicites, trois liens officiels et conseils pratiques.
- `hotels/paris/luxury-hotels/index.html` : lien daté vers cette section.
- `hotels/paris/family-hotels/index.html` : même lien discret.
- `hotels/paris/cheap-hotels/index.html` : même lien discret.

Les styles existants `callout tg-callout tg-guide-tip` suffisent : aucun CSS,
JavaScript, bandeau rouge, popup, animation ou dépendance ajouté. La note est une
section éditoriale nommée, sans rôle `alert`, avec liens natifs et cible de fragment
`tabindex="-1"`. Elle ne prétend pas être un flux en temps réel.

**Revoir avant toute publication et au plus tard le 25 octobre 2026, heure de
Paris**, après les dernières restrictions annoncées. Cette date est une échéance
éditoriale, pas une promesse de réouverture. Aucun mécanisme automatique ou rappel
n'a été installé. Si la publication intervient après les dates citées, vérifier à
nouveau les sources et actualiser ou retirer les quatre blocs avant publication.

Pour actualiser : vérifier les sources officielles, modifier uniquement les faits
confirmés et la date `<time>` du hub, puis la date du lien dans les trois guides.
Ne jamais avancer la date sans vérification. Ne pas changer la date générale de
révision hôtelière ou les données structurées pour cette seule note.

Pour retirer : supprimer du hub le bloc entre les commentaires
`PARIS TRAVEL UPDATES START` et `PARIS TRAVEL UPDATES END`, ainsi que la ligne vide
ajoutée ; supprimer les trois blocs entre `PARIS TRAVEL UPDATES LINK START` et
`PARIS TRAVEL UPDATES LINK END`. Retirer les quatre ensemble évite les liens morts.
Ne pas laisser une alerte nationale générique seule à la place de ces avis datés
si aucune perturbation pertinente ne justifie plus la section.

## Périmètre préservé

Le retrait des seuls blocs ajoutés restitue exactement le texte original des
quatre pages, après normalisation CRLF/LF. Cela couvre les titres, descriptions,
H1, canonicals, hreflang, JSON-LD, hôtels, photos, quartiers, comparatifs,
recommandations, liens internes existants, CTA, Klook, SubIDs et scripts.
Sitemaps, consentement, tracking, baseline et scripts partagés restent inchangés.
Les autres destinations, PR #49, branches et worktrees existants ne sont pas
modifiés. Le checkout Disney conserve ses modifications préexistantes.

Les preuves ciblées sont dans [checks.json](qa/paris-travel-advisory-v1/checks.json)
et les captures mobile/desktop dans le même dossier. L'audit officiel est consigné
dans [official-audit.json](qa/paris-travel-advisory-v1/official-audit.json).

Contrôles ciblés réussis dans Chrome local, toutes requêtes externes bloquées :

- Conservation exacte des quatre pages originales hors ajouts ; 21 liens affiliés
  d'origine conservés (hub 10, Luxury 4, Family 4, Cheap 3).
- 16 vues à 320, 390, 768 et 1440 px, sans débordement horizontal.
- Huit captures à 390 et 1440 px inspectées visuellement ; note lisible,
  présentation cohérente et liens discrets.
- Focus clavier visible et navigation Entrée depuis les trois guides vers le
  fragment du hub ; une seule H1 par page.
- Contraste mesuré dans la note : texte 13,56:1 et liens 4,80:1 sur fond sable.
  Ces contrôles ciblés ne constituent pas un audit WCAG complet du site.
- Sur chaque page, un clic affilié représentatif : zéro `affiliate_click` avec
  consentement refusé, exactement un avec consentement accordé. Navigation
  affiliée empêchée dans le navigateur de test ; aucun partenaire ouvert.
- Affichage et liens présents sans JavaScript sur les quatre pages à 390 px.

Commande d'audit officiel, à exécuter une seule fois après la finalisation :
`python -B scripts/audit-site.py --base-ref 27c98abb1185da3364ecf7ac904e33117f729f99 --json`.
Le fichier JSON porte le verdict de l'auditeur et ses éventuelles demandes
d'autorisation ; aucune autorisation n'a été ajoutée au baseline.
