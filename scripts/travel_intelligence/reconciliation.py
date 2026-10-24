"""Non-destructive observation groups; matching sources are not independent proofs."""
from .validation import digest


def reconcile(events):
    parent = {e["event_id"]: e["event_id"] for e in events}
    def find(ident):
        while parent[ident] != ident:
            parent[ident] = parent[parent[ident]]; ident = parent[ident]
        return ident
    def union(left, right):
        a, b = find(left), find(right)
        if a != b: parent[max(a,b)] = min(a,b)
    usgs = {}
    gdacs_families = {}
    reasons = []
    unmatched_gdacs = []
    for event in events:
        if event["source_id"] == "usgs-earthquakes":
            aliases = event["source_data"]["aliases"].strip(",").split(",")
            for ident in aliases:
                usgs.setdefault(ident, []).append(event["event_id"])
        elif event["source_id"] == "gdacs-multi-hazard":
            d = event["source_data"]; family = (d["event-type"], d["gdacs-id"])
            previous = gdacs_families.setdefault(family, event["event_id"])
            union(previous, event["event_id"])
    for event in events:
        if event["source_id"] != "gdacs-multi-hazard" or event["category"] != "earthquake": continue
        d = event["source_data"]
        matches = usgs.get(d["upstream-id"], []) if d["upstream-source"] in {"USGS", "NEIC"} else []
        # An alias referring to several USGS observations is ambiguous, not a certain match.
        if len(matches) == 1:
            union(event["event_id"], matches[0])
            reasons.append({"event_ids":sorted([event["event_id"],matches[0]]),
                "basis":"shared_official_identifier", "official_identifier":d["upstream-id"],
                "independent_confirmations":False, "impact_confirmed":False, "needs_human_review":True})
        else: unmatched_gdacs.append(event["event_id"])
    groups = {}
    for event in events: groups.setdefault(find(event["event_id"]),[]).append(event["event_id"])
    review = []
    usgs_ids = sorted({ident for values in usgs.values() for ident in values})
    if unmatched_gdacs and usgs_ids:
        review.append({"gdacs_observation_ids":sorted(unmatched_gdacs),"usgs_observation_ids":usgs_ids,
            "basis":"official_identity_unresolved", "needs_human_review":True,
            "matching_asserted":False, "merged":False})
    return {"observation_groups":[{"group_id":"group-"+digest(sorted(ids)),"observation_ids":sorted(ids),
                "merged":False,"independent_confirmations":False,"impact_confirmed":False}
                for _,ids in sorted(groups.items())],
            "cross_source_relationships":reasons,"possible_duplicate_review":review,
            "grouping_statement":"Groups preserve every source/episode; they are not a confirmed disaster count."}
