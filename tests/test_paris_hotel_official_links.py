"""Exact offline regression checks for the three published Paris hotel guides."""
import argparse
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
BASE = "13b6ddac77e910bf96279c67e70a4359479ddb86"
REPORT = "docs/paris-hotel-official-links-audit.md"
PAGES = {name: f"hotels/paris/{name}-hotels/index.html" for name in ("family", "cheap", "luxury")}
SOURCES = (
    "https://www.dorchestercollection.com/paris/le-meurice",
    "https://www.mandarinoriental.com/en/paris/lutetia/wellness",
    "https://www.shangri-la.com/paris/shangrila/",
    "https://pullman.accor.com/en/hotels/paris/7229.html",
)
ALLOWED = {PAGES["luxury"], REPORT, "tests/test_paris_hotel_official_links.py", "tests/test_paris_hotel_official_links.cjs"}
TEXT = {".py", ".cjs", ".html", ".css", ".js", ".mjs", ".xml", ".svg", ".json", ".txt", ".webmanifest", ".md", ".yml", ".yaml"}


def git(*args, input=None):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], input=input)


class Document(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.anchors = []
        self.ids = []
        self.h1 = 0
        self.text_parts = []
        self.feed(text)

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "a":
            self.anchors.append({"attrs": attrs, "opening": self.get_starttag_text()})
        if attrs.get("id"):
            self.ids.append(attrs["id"])
        self.h1 += tag == "h1"

    def handle_data(self, data):
        self.text_parts.append(data)


def run():
    checks = []

    def check(condition, name):
        assert condition, name
        checks.append(name)

    check(git("branch", "--show-current").decode().strip() == "fix/paris-hotel-official-links", "New dedicated branch")
    check(subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", BASE, "HEAD"], check=False).returncode == 0, "Latest integrated main is an ancestor")
    check(not git("diff", "--cached", "--name-only").strip(), "Nothing staged")
    changed = set(git("diff", "--name-only", BASE).decode().splitlines())
    untracked = set(git("ls-files", "--others", "--exclude-standard").decode().splitlines())
    check(changed | untracked <= ALLOWED, "Four-file scope only")
    check(not git("diff", "--name-only", "--diff-filter=D", BASE).strip(), "No deleted files")
    docs = (ROOT / REPORT).read_text(encoding="utf-8")
    inventories = {}
    for name, path in PAGES.items():
        before = git("show", BASE + ":" + path).decode().replace("\r\n", "\n")
        after = (ROOT / path).read_text(encoding="utf-8").replace("\r\n", "\n")
        expected = before
        if name == "luxury":
            for url in SOURCES:
                markup = f'<a href="{url}">official property information</a>'
                check(expected.count(markup) == 1, "Exactly one original source anchor: " + url)
                expected = expected.replace(markup, "official property information")
                check(url in docs, "Removed exact URL retained in internal report: " + url)
        check(after == expected, name + ": whole page exact after only source-anchor removal")
        check(after.split("</head>", 1)[0] == before.split("</head>", 1)[0], name + ": head/SEO/Schema/scripts/dates exact")
        b, a = Document(before), Document(after)
        check("".join(b.text_parts) == "".join(a.text_parts), name + ": all text retained")
        aff = lambda d: [n["opening"] for n in d.anchors if "js-aff" in n["attrs"].get("class", "").split()]
        check(aff(b) == aff(a) and len(aff(a)) == (3 if name == "cheap" else 4), name + ": all Klook opening tags exact")
        outgoing = [n["attrs"] for n in a.anchors if urlsplit(n["attrs"].get("href", "")).netloc]
        check(all(urlsplit(n["href"]).hostname == "klook.tpk.ro" for n in outgoing), name + ": all outgoing HTML anchors are inherited Klook links")
        check(len(outgoing) == len(aff(a)), name + ": no extra outbound CTA")
        check(a.h1 == 1 and len(a.ids) == len(set(a.ids)), name + ": one H1 and unique IDs")
        check(a.ids == b.ids, name + ": all fragments and map IDs exact")
        for n in outgoing:
            check(n["href"] in docs and n["data-subid"] in docs, name + ": exact URL/SubID inventory documented")
        inventories[name] = outgoing

    # Read immutable Git blobs in one batch, rather than spawning Git for every file.
    entries = []
    for entry in git("ls-tree", "-r", "-z", BASE).split(b"\0"):
        if not entry:
            continue
        metadata, name = entry.split(b"\t", 1)
        mode, kind, oid = metadata.split()
        path = name.decode()
        if path not in ALLOWED:
            assert kind == b"blob" and mode in (b"100644", b"100755"), path
            entries.append((path, oid))
    blobs = git("cat-file", "--batch", input=b"\n".join(oid for _, oid in entries) + b"\n")
    offset = 0
    for path, oid in entries:
        end = blobs.index(b"\n", offset)
        header = blobs[offset:end].split()
        assert header[:2] == [oid, b"blob"], path
        size = int(header[2])
        old = blobs[end + 1:end + 1 + size]
        offset = end + 2 + size
        new = (ROOT / path).read_bytes()
        if Path(path).suffix.lower() in TEXT or Path(path).name in {".gitkeep", "LICENSE"}:
            old, new = old.replace(b"\r\n", b"\n"), new.replace(b"\r\n", b"\n")
        assert old == new, "Unchanged file: " + path
    check(offset == len(blobs), "All other tracked files exact, including Paris parent, Disney, GA4, consent, maps, vendors, fixture and historical tests")
    return {"passed": True, "checks": len(checks), "base_revision": BASE, "other_tracked_files_verified": len(entries), "changed_paths": sorted(changed | untracked), "outgoing_html_links": inventories, "results": checks}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run()
    if args.output:
        assert ROOT != args.output.resolve() and ROOT not in args.output.resolve().parents
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k not in ("results", "outgoing_html_links")}, ensure_ascii=False))
