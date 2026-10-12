"""Read-only scope, affiliate, SEO and integration preservation checks."""
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = "9d3301f0ffff927ba796d7f33e06e3031fb319a2"
PAGE = "hotels/paris/luxury-hotels/index.html"
ALLOWED = {
    PAGE, "assets/js/paris-luxury-hotel-map.js",
    "assets/css/pages/paris-luxury-hotels.css",
    "tests/test_paris_luxury_hotel_map.cjs",
    "tests/test_paris_luxury_preservation.py",
    "tests/fixtures/site-baseline.json", "docs/paris-luxury-ux-cro.md",
}


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def normalized(data):
    return data.replace(b"\r\n", b"\n")


class Structure(HTMLParser):
    def __init__(self, content):
        super().__init__()
        self.ids = []
        self.h1 = 0
        self.anchors = []
        self.links = []
        self.feed(content)

    def handle_starttag(self, tag, attributes):
        a = dict(attributes)
        if "id" in a:
            self.ids.append(a["id"])
        if tag == "h1":
            self.h1 += 1
        if tag == "a":
            self.links.append(a)
            if "js-aff" in a.get("class", "").split():
                self.anchors.append(self.get_starttag_text())


def run():
    checks = []

    def check(name, condition):
        assert condition, name
        checks.append(name)

    check("same branch and latest integrated main is an ancestor", git("branch", "--show-current").decode().strip() == "feat/paris-luxury-ux-cro" and subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", BASE, "HEAD"], check=False).returncode == 0)
    check("empty index", not git("diff", "--cached", "--name-only").strip())
    changed = set(git("diff", "--name-only", BASE).decode().splitlines())
    untracked = set(git("ls-files", "--others", "--exclude-standard").decode().splitlines())
    check("all edits and additions within luxury scope", (changed | untracked) <= ALLOWED)
    check("no deleted files", not git("diff", "--name-only", "--diff-filter=D", BASE).strip())
    checked = 0
    for name in git("ls-tree", "-r", "--name-only", BASE).decode().splitlines():
        if name in ALLOWED:
            continue
        current = ROOT / name
        assert current.exists(), name
        assert normalized(current.read_bytes()) == normalized(git("show", BASE + ":" + name)), name
        checked += 1
    check("all other tracked files exact (including Cheap, Family, Disney, shared GA4/consent, images and vendors)", checked > 0)
    before = git("show", BASE + ":" + PAGE).decode()
    after = (ROOT / PAGE).read_text(encoding="utf-8")
    b, a = Structure(before), Structure(after)
    check("four native affiliate opening tags exact", a.anchors == b.anchors and len(a.anchors) == 4)
    check("single H1 and unique IDs", a.h1 == 1 and len(a.ids) == len(set(a.ids)))
    check("all page-local fragments resolve", all(link["href"][1:] in a.ids for link in a.links if link.get("href", "").startswith("#")))
    head = lambda s: s.split("<head>", 1)[1].split("</head>", 1)[0].replace("\r\n", "\n")
    changed_head = head(after).replace('  <link rel="stylesheet" href="/assets/css/pages/paris-luxury-hotels.css" />\n', "").replace("2026-10-11", "2026-10-09")
    check("head exact except scoped CSS and truthful review dates", changed_head == head(before))
    schema = lambda s: json.loads(re.search(r'<script type="application/ld\+json">([\s\S]*?)</script>', s)[1])
    graph = schema(after)
    for node in graph["@graph"]:
        if "dateModified" in node:
            assert node["dateModified"] == "2026-10-11"
            node["dateModified"] = "2026-10-09"
    check("Schema graph exact except review date", graph == schema(before))
    disclosure = lambda s: re.search(r'<p class="tg-hotel-disclosure"><strong>Affiliate disclosure:</strong>[\s\S]*?</p>', s)[0]
    check("single exact affiliation disclosure before cards and map", disclosure(after) == disclosure(before) and after.count("Affiliate disclosure:") == 1 and after.index("Affiliate disclosure:") < after.index('id="hotel-options"'))
    fixture = "tests/fixtures/site-baseline.json"
    old = json.loads(git("show", BASE + ":" + fixture))
    new = json.loads((ROOT / fixture).read_text(encoding="utf-8"))
    check("all old fixture content and authorizations retained", {k:v for k,v in new.items() if k != "authorizations"} == {k:v for k,v in old.items() if k != "authorizations"} and new["authorizations"][:-2] == old["authorizations"])
    records = new["authorizations"][-2:]
    script = 'assets/js/paris-luxury-hotel-map.js'
    markup = '<script src="/assets/js/paris-luxury-hotel-map.js" defer></script>'
    encoded_markup = json.dumps(markup, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    check("only two new exact-hash integrations bound to this base", len(records) == 2 and records[0]["kind"] == "new_integration_markup" and records[0]["source"] == PAGE and records[0]["after"] == hashlib.sha256(encoded_markup).hexdigest() and records[1]["kind"] == "new_integration_script" and records[1]["source"] == script and records[1]["after"] == hashlib.sha256(normalized((ROOT / script).read_bytes())).hexdigest() and all(r["base_revision"] == BASE and r["before"] is None for r in records))
    return {"passed": True, "checks": len(checks), "scenarios": checks, "other_tracked_files_verified": checked, "changed_paths": sorted(changed | untracked), "base_revision": BASE}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run()
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
