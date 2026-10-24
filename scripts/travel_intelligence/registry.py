"""Closed configuration: locations are not inferred from national advisories."""
from __future__ import annotations

from .validation import country, digest, keys, load_json, plain, require, slug, local_time

KINDS = {"country", "region", "city", "neighborhood", "airport", "transport_zone",
         "station", "route", "poi"}


class Registry:
    def __init__(self, destinations, sources):
        keys(destinations, {"schema_version", "destinations"})
        keys(sources, {"schema_version", "publication_enabled", "sources"})
        require(type(destinations["schema_version"]) is int and destinations["schema_version"] == 3,
                "destination_schema")
        require(type(sources["schema_version"]) is int and sources["schema_version"] == 3,
                "source_schema")
        require(sources["publication_enabled"] is False, "publication_disabled_in_phase1")
        require(type(destinations["destinations"]) is list and
                1 <= len(destinations["destinations"]) <= 2000, "destination_count")
        self.destinations = {}
        for d in destinations["destinations"]:
            keys(d, {"destination_id", "name_en", "kind", "country_code", "parent_id",
                     "timezone", "pages"})
            ident = slug(d["destination_id"])
            require(ident not in self.destinations and d["kind"] in KINDS, "duplicate_or_invalid_destination")
            plain(d["name_en"], 120)
            country(d["country_code"])
            if d["parent_id"] is not None:
                slug(d["parent_id"])
            if d["timezone"] is not None:
                local_time("2026-01-01T00:00:00Z", d["timezone"])
            require(d["kind"] != "city" or d["timezone"] is not None, "city_timezone_required")
            require(type(d["pages"]) is list and len(d["pages"]) <= 100, "invalid_pages")
            for page in d["pages"]:
                require(type(page) is str and page.startswith("/") and not page.startswith("//")
                        and page.endswith("/") and not any(x in page for x in ("..", "?", "#", "\\", "%")),
                        "invalid_page_route")
            require(len(d["pages"]) == len(set(d["pages"])), "duplicate_page")
            self.destinations[ident] = d
        self.countries = {}
        for d in self.destinations.values():
            seen = set()
            node = d
            while node["parent_id"] is not None:
                require(node["destination_id"] not in seen, "destination_cycle")
                seen.add(node["destination_id"])
                parent = self.destinations.get(node["parent_id"])
                require(parent is not None and parent["country_code"] == d["country_code"],
                        "invalid_destination_parent")
                allowed_parents = {
                    "country": set(), "region": {"country", "region"},
                    "city": {"country", "region"}, "neighborhood": {"city", "neighborhood"},
                    "airport": {"country", "region", "city"},
                    "transport_zone": {"country", "region", "city", "transport_zone"},
                    "station": {"region", "city", "neighborhood", "airport", "transport_zone"},
                    "route": {"country", "region", "city", "transport_zone"},
                    "poi": {"country", "region", "city", "neighborhood", "airport", "transport_zone"},
                }
                require(parent["kind"] in allowed_parents[node["kind"]], "invalid_hierarchy")
                node = parent
            require(node["kind"] == "country", "country_root_required")
            if d["kind"] == "country":
                require(d["parent_id"] is None and d["country_code"] not in self.countries,
                        "duplicate_country_root")
                self.countries[d["country_code"]] = d["destination_id"]
        require(type(sources["sources"]) is list and 1 <= len(sources["sources"]) <= 50, "source_count")
        self.sources = {}
        for source in sources["sources"]:
            keys(source, {"source_id", "adapter", "endpoint", "publisher", "licence", "licence_url",
                          "documentation_url", "countries", "country_slugs", "allowed_urls",
                          "audience_nationalities", "max_export_age_hours", "freshness_hours",
                          "review_hours", "qualification", "publication_enabled"})
            ident = slug(source["source_id"])
            require(ident not in self.sources, "duplicate_source")
            require(source["publication_enabled"] is False, "publication_disabled_in_phase1")
            require(source["qualification"] == "CONFIRMED AUTOMATABLE", "source_not_qualified")
            for field in ("publisher", "licence", "adapter"):
                plain(source[field], 160)
            worldwide = source["adapter"] == "usgs-summary-v1"
            if worldwide:
                from .usgs import validate_source
                validate_source(source)
            require(type(source["countries"]) is list and (source["countries"] or worldwide) and
                    len(source["countries"]) == len(set(source["countries"])) <= 64, "source_countries")
            require(type(source["country_slugs"]) is dict and
                    set(source["country_slugs"]) == set(source["countries"]), "source_slugs")
            require(type(source["allowed_urls"]) is list and 1 <= len(source["allowed_urls"]) <= 100,
                    "source_allowlist")
            from .validation import official_url
            for url in source["allowed_urls"]:
                official_url(url, source["allowed_urls"])
            for field in ("endpoint", "licence_url", "documentation_url"):
                official_url(source[field], source["allowed_urls"])
            for code in source["countries"]:
                country(code)
                require(code in self.countries, "unknown_source_country")
                slug(source["country_slugs"][code])
            require(type(source["audience_nationalities"]) is list and
                    (0 if worldwide else 1) <= len(source["audience_nationalities"]) <= 64, "source_audience")
            for code in source["audience_nationalities"]:
                country(code)
            for field in ("max_export_age_hours", "freshness_hours", "review_hours"):
                require(type(source[field]) is int and 1 <= source[field] <= 48, "source_duration")
            self.sources[ident] = source
        self.config_hash = digest([destinations, sources])

    @classmethod
    def from_directory(cls, directory, source_file="sources.json"):
        require(source_file in {"sources.json", "usgs-sources.json"}, "unsupported_source_profile")
        return cls(load_json(directory / "destinations.json"), load_json(directory / source_file))

    def contexts(self, event):
        """Report associations, never assertions that the city is affected."""
        result = []
        for d in self.destinations.values():
            if d["kind"] != "city":
                continue
            relation = None
            if (event["record_kind"] == "advisory" and event["geographic_scope"] == "country"
                    and d["country_code"] == event["country_code"]):
                relation = "country_context"
            elif event["city"] == d["destination_id"] and event["geographic_scope"] == "city":
                relation = "explicit_city_scope"
            if relation:
                result.append({"destination_id": d["destination_id"], "relationship": relation,
                               "local_incident_confirmed": False, "pages": d["pages"]})
        return sorted(result, key=lambda x: x["destination_id"])
