"""Read-only preservation checks; optional JSON report must be outside the repo.

python -B tests/test_paris_cheap_preservation.py BASE_REF [OUTPUT_JSON]
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = sys.argv[1]
PAGE = "hotels/paris/cheap-hotels/index.html"
checks = []


def check(condition, label):
    assert condition, label
    checks.append(label)


def before(path):
    return subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT).decode("utf-8").replace("\r\n", "\n")


def current(path):
    return (ROOT / path).read_text(encoding="utf-8")


def sections(value, ident):
    return re.findall(r'<section id="' + re.escape(ident) + r'"[\s\S]*?</section>\n', value)


# This historical test compares the pre-map Cheap project stage. For the
# exact approved photo base, use the strict shared three-guide contract.
if subprocess.check_output(["git", "rev-parse", BASE + "^{commit}"], cwd=ROOT).decode().strip() == "04f83bc14e02150387d0f2b7b8e3a1351a69fcac":
    from test_paris_hotel_photos_preservation import main as photo_preservation_main
    raise SystemExit(photo_preservation_main(sys.argv[1:]))


a, b = before(PAGE), current(PAGE)
resource = '  <link rel="stylesheet" href="/assets/css/pages/paris-cheap-hotel-map.css" />\n'
check(a[a.index("<head>"):a.index("</head>")] == b[b.index("<head>"):b.index("</head>")].replace(resource, ""), "Head, Schema and metadata unchanged except local stylesheet")


def untouched(value):
    value = value.replace(resource, "")
    value = value.replace('<script src="/assets/js/paris-cheap-hotel-map.js" defer></script>\n', "")
    value = value.replace("tg-hotels tg-cheap-hotels", "tg-hotels")
    value = value.replace('<a href="#hotel-map">Find the three stays on the map</a>', "")
    value = re.sub(r'<section id="hotel-map"[\s\S]*?</section>\n', "", value)
    for ident in ("hotel-options", "comparison"):
        value = re.sub(r'<section id="' + ident + r'"[\s\S]*?</section>\n', f"APPROVED:{ident}\n", value)
    return value


check(untouched(a) == untouched(b), "All content outside approved cards/comparison/map/resources stays exact")
for ident in ("hotel-options", "comparison", "hotel-map"):
    check(len(sections(b, ident)) == 1, f"One {ident} section")

anchors = lambda value: re.findall(r'<a\b[^>]*\bjs-aff\b[^>]*>', value)
strip_metadata = lambda tag: re.sub(r' data-hotel-id="[^"\n]+" data-placement="list" data-experiment-variant="baseline"', "", tag)
check(len(anchors(a)) == len(anchors(b)) == 3, "Exactly three original affiliate anchors")
check(anchors(a) == [strip_metadata(x) for x in anchors(b)], "Affiliate opening tags exact except opt-in metadata")
inventory = [
    ("2846", "paris_hotel_ibis_cambronne", "https://klook.tpk.ro/jor8wPCP"),
    ("412657", "paris_hotel_bb_batignolles", "https://klook.tpk.ro/gX4TDO9u"),
    ("448880", "paris_hotel_generator", "https://klook.tpk.ro/t3aQhbjX"),
]
for tag, (hotel_id, subid, url) in zip(anchors(b), inventory):
    check(all(fragment in tag for fragment in (f'data-hotel-id="{hotel_id}"', f'data-subid="{subid}"', f'href="{url}"', 'rel="nofollow sponsored noopener"', 'target="_blank"', "opens in a new tab")), f"Exact mapping and accessible new-tab behavior: {hotel_id}")

articles = lambda value: re.findall(r'<article class="tg-card tg-hotel-card"[\s\S]*?</article>', value)
check(len(articles(a)) == len(articles(b)) == 3, "Three original accommodation articles retained")
for old, new in zip(articles(a), articles(b)):
    # Sources move to documentation. All other original P elements remain intact.
    paragraphs = lambda value: [p for p in re.findall(r'<p\b[^>]*>[\s\S]*?</p>', value) if not p.startswith("<p>Source:")]
    check(paragraphs(old) == paragraphs(new), "Original neighborhood, fit, description and trade-off retained")
    check(re.findall(r'<h3\b[^>]*>[\s\S]*?</h3>', old) == re.findall(r'<h3\b[^>]*>[\s\S]*?</h3>', new), "Original hotel heading and fragment retained")
    for address in re.findall(r'<dt>Address</dt><dd>(.*?)</dd>', old):
        check(f"<dd>{address}</dd>" in new, "Original address retained")
    check(re.findall(r'data-fact="([^"]+)"', new) == ["capacity", "bedding", "transport", "budget", "address"], "Five complete facts in budget-first order")
    check(new.index('class="tg-hotel-facts"') < new.index(paragraphs(new)[2]), "Facts precede long description")

check(not re.search(r'<a\b[^>]*href="https://(?:all\.accor|www\.hotel-bb|staygenerator)\.', sections(b, "hotel-options")[0]), "No direct official-site links in commercial cards")
check("<span>Opens in a new tab</span>" not in b, "Visible repeated new-tab notes removed")
check('scope="row"' in sections(b, "comparison")[0] and sections(b, "comparison")[0].count('scope="col"') == 5, "Native comparison headers retained")
check("No nightly price or tourist-tax rate is quoted here" in b and "No property is always the cheapest" in b, "Original price and tax caveats retained")
check("No option is guaranteed cheapest. Compare the same dates, guests and cancellation conditions.</p>" in sections(b, "comparison")[0], "Price reminder outside scrollable table")

script = current("assets/js/paris-cheap-hotel-map.js")
for row in ('["2846", "hotel-ibis-cambronne", 48.847653, 2.301453]', '["412657", "hotel-bb-batignolles", 48.894501, 2.312604]', '["448880", "hotel-generator", 48.8781526, 2.3698083]'):
    check(row in script, "Audited property point unchanged")
check("hotel.link.cloneNode(true)" in script and "gtag(" not in script and "affiliate_click" not in script, "Booking links cloned; no second analytics emitter")
check('data-map-page") !== "paris-cheap"' in script, "Bootstrap requires cheap-page opt-in")
check("paris-family-hotel-map" not in b + script + current("assets/css/pages/paris-cheap-hotel-map.css"), "No dependency on Family page assets")
check(all(rule.lstrip().startswith(".tg-ui .tg-cheap-hotels") for rule in current("assets/css/pages/paris-cheap-hotel-map.css").splitlines() if rule.lstrip().startswith(".tg-ui")), "Styles require cheap-page scope")

for path in ("assets/js/site.js", "hotels/paris/family-hotels/index.html", "assets/js/paris-family-hotel-map.js", "assets/css/pages/paris-family-hotel-map.css", "assets/css/templates/hotels.css", "scripts/audit-site.py"):
    check(before(path) == current(path), f"Unchanged: {path}")
for path in subprocess.check_output(["git", "ls-tree", "-r", "--name-only", BASE, "assets/vendor/leaflet-1.9.4"], cwd=ROOT).decode().splitlines():
    old = subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT)
    new = (ROOT / path).read_bytes()
    if Path(path).suffix in (".js", ".css") or Path(path).name == "LICENSE":
        old, new = old.replace(b"\r\n", b"\n"), new.replace(b"\r\n", b"\n")
    check(old == new, f"Vendor/license unchanged: {path}")

original = json.loads(before("tests/fixtures/site-baseline.json"))
baseline = json.loads(current("tests/fixtures/site-baseline.json"))
added = baseline["authorizations"][:3]
baseline["authorizations"] = baseline["authorizations"][3:]
check(baseline == original, "Baseline unchanged except three exact review records")
check({x["kind"] for x in added} == {"affiliate_anchor", "new_integration_markup", "new_integration_script"}, "Only required auditor review kinds")
check(all(x["base_revision"] == BASE and x["source"] in (PAGE, "assets/js/paris-cheap-hotel-map.js") for x in added), "Approvals limited to this page/bootstrap and exact base")
record = next(x for x in added if x["kind"] == "new_integration_script")
check(record["after"] == hashlib.sha256(script.encode()).hexdigest(), "Bootstrap approval matches current normalized hash")

report = {"passed": True, "checks": len(checks), "base": BASE, "results": checks}
if len(sys.argv) > 2:
    output = Path(sys.argv[2]).resolve()
    check(output != ROOT and ROOT not in output.parents, "QA report outside worktree")
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"passed": True, "checks": report["checks"], "base": BASE}))
