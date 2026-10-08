#!/usr/bin/env python3
"""Deterministic, offline site checks. Ordinary audits never rewrite the fixture.

Python 3.12+ and Git are the only runtime dependencies. --self-test uses immutable
in-memory copies of the base tree; it never edits website files or invokes links.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date
import hashlib
from html.parser import HTMLParser
import io
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import subprocess
import sys
import tarfile
import time
from urllib.parse import unquote, urljoin, urlsplit
import xml.etree.ElementTree as ET


FIXTURE = "tests/fixtures/site-baseline.json"
ORIGIN = "https://tripguidely.github.io"
NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
EXCLUDED = {".git", ".github", ".worktrees", ".codex", ".agents", "scripts",
            "tests", "docs", "node_modules", "__pycache__", "dist", "build",
            "tmp", "temp", ".tmp", ".cache", ".pytest_cache", "coverage", ".venv", "venv"}
TEXT_EXT = {".html", ".css", ".js", ".mjs", ".xml", ".svg", ".json", ".txt",
            ".webmanifest", ".md", ".yml", ".yaml"}
VOID = set("area base br col embed hr img input link meta param source track wbr".split())
MEDIA_EXT = {".png", ".jpg", ".jpeg", ".webp", ".avif", ".gif", ".svg",
             ".ico", ".pdf", ".mp4", ".woff", ".woff2", ".css", ".js", ".mjs"}
PARTNERS = {
    "klook": {"klook.tpk.ro", "www.klook.com", "klook.com"},
    "airalo": {"airalo.tpk.ro", "www.airalo.com", "airalo.com"},
    "tiqets": {"tiqets.tpk.ro", "www.tiqets.com", "tiqets.com"},
    "kiwi": {"kiwi.tpk.ro", "www.kiwi.com", "kiwi.com"},
    "travelpayouts": {"tp.media", "tp-em.com", "tpemb.com", "travelpayouts.com"},
}


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else encoded(value)).hexdigest()


def invalid_json_constant(value):
    raise ValueError("Non-JSON constant: " + value)


def blob_hash(path, content):
    # Git blobs use LF; checkout CRLF must not create a Windows-only regression.
    if PurePosixPath(path).suffix.lower() in TEXT_EXT:
        content = content.replace(b"\r\n", b"\n")
    return digest(content)


def public(path):
    return not any(part in EXCLUDED for part in PurePosixPath(path).parts)


def git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=False)
    if result.returncode:
        raise ValueError(result.stderr.decode("utf-8", "replace").strip())
    return result.stdout


@dataclass
class Tree:
    files: dict[str, bytes]
    revision: str = "working-tree"

    @classmethod
    def working(cls, root):
        names = git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
        files = {}
        for name in sorted(set(names.decode().split("\0")) - {""}):
            if not public(name):
                continue
            path = root / name
            if path.is_symlink():
                raise ValueError(f"Site symlink needs review: {name}")
            if path.is_file():
                files[name] = path.read_bytes()
        return cls(files)

    @classmethod
    def revision_tree(cls, root, ref):
        sha = git(root, "rev-parse", "--verify", ref + "^{commit}").decode().strip()
        files = {}
        archive = git(root, "archive", "--format=tar", sha)
        with tarfile.open(fileobj=io.BytesIO(archive)) as handle:
            for member in handle:
                if not public(member.name):
                    continue
                if member.issym() or member.islnk():
                    raise ValueError(f"Site symlink needs review: {member.name}")
                if member.isfile():
                    files[member.name] = handle.extractfile(member).read()
        return cls(files, sha)

    def copy(self):
        return Tree(dict(self.files), self.revision)


@dataclass
class Node:
    tag: str
    attrs: dict
    opening: str
    line: int
    parent: Node | None = None
    children: list = field(default_factory=list)
    parts: list = field(default_factory=list)
    closing: str = ""

    def text(self):
        return "".join(part if isinstance(part, str) else part.text() for part in self.parts)

    def markup(self):
        return self.opening + "".join(part if isinstance(part, str) else part.markup()
                                       for part in self.parts) + self.closing

    def descendants(self):
        for child in self.children:
            yield child
            yield from child.descendants()


class Document(HTMLParser):
    """Extract references/contracts, without pretending to be an HTML5 validator."""

    def __init__(self, content):
        super().__init__(convert_charrefs=False)
        self.root = Node("root", {}, "", 0)
        self.stack = [self.root]
        self.nodes = []
        self.duplicate_attributes = []
        self.feed(content.decode("utf-8-sig").replace("\r\n", "\n"))
        self.close()

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs), self.get_starttag_text(), self.getpos()[0], self.stack[-1])
        if len(attrs) != len(dict(attrs)):
            self.duplicate_attributes.append(node)
        self.nodes.append(node)
        self.stack[-1].children.append(node)
        self.stack[-1].parts.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.stack.pop()

    def handle_endtag(self, tag):
        # Tolerate optional HTML end tags; full conformance belongs to HTML QA.
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                self.stack[i].closing = f"</{tag}>"
                del self.stack[i:]
                break

    def handle_data(self, text):
        self.stack[-1].parts.append(text)

    def handle_entityref(self, name):
        self.handle_data("&" + name + ";")

    def handle_charref(self, name):
        self.handle_data("&#" + name + ";")

    def handle_comment(self, text):
        self.handle_data("<!--" + text + "-->")

    def find(self, tag):
        return [node for node in self.nodes if node.tag == tag]


@dataclass
class Finding:
    category: str
    source: str
    target: str
    locator: str
    occurrence: int
    line: int
    detail: str = ""

    @property
    def identifier(self):
        identity = [self.category, self.source, self.target, self.locator, self.occurrence]
        return self.category + ":" + digest(identity)[:20]

    def record(self):
        return {"id": self.identifier, **self.__dict__}


def route(path):
    if path == "index.html":
        return "/"
    return "/" + (path[:-10] if path.endswith("/index.html") else path)


def affiliate(node):
    attrs = node.attrs
    href = attrs.get("href") or ""
    return (node.tag == "a" and (bool(attrs.get("data-aff")) or bool(attrs.get("data-subid"))
            or "js-aff" in (attrs.get("class") or "").split()
            or "sponsored" in (attrs.get("rel") or "").split()
            or any(value in href for value in ("tpk.ro", "tp.media", "travelpayouts"))))


def redirect(document):
    for node in document.find("meta"):
        if (node.attrs.get("http-equiv") or "").lower() == "refresh":
            match = re.fullmatch(r"\s*\d+(?:\.\d+)?\s*;\s*url\s*=\s*(.+?)\s*",
                                 node.attrs.get("content") or "", re.I)
            return (match.group(1).strip("\"'") if match else ""), node
    return None


def srcset_urls(value):
    # HTML's URL token is followed by whitespace/descriptors. A data URL can
    # contain commas, so consume it as one token rather than splitting blindly.
    result = []
    offset = 0
    while offset < len(value):
        while offset < len(value) and (value[offset].isspace() or value[offset] == ","):
            offset += 1
        start = offset
        while offset < len(value) and not value[offset].isspace():
            offset += 1
        token = value[start:offset]
        if not token:
            break
        result.append(token.rstrip(","))
        if token.endswith(","):
            continue
        depth = 0
        while offset < len(value):
            character = value[offset]
            offset += 1
            if character == "(":
                depth += 1
            elif character == ")":
                depth = max(0, depth - 1)
            elif character == "," and not depth:
                break
    return result


class Audit:
    def __init__(self, tree, origin=ORIGIN):
        self.tree = tree
        self.origin = origin
        self.host = urlsplit(origin).netloc
        self.folded_paths = {p.casefold(): p for p in tree.files}
        self.findings = []
        self.sequence = Counter()
        self.docs = {}
        self.contracts = defaultdict(lambda: defaultdict(Counter))
        self.affiliates = defaultdict(list)
        self.references = Counter()
        self.missing_assets = defaultdict(set)
        self.sitemap_urls = []
        self.sitemap_index = []
        self.roles = {}
        self.canonicals = {}
        self.article_paths = set()
        self.exclusions = []
        self.review = []
        self.integration_scripts = {}
        for path, content in sorted(tree.files.items()):
            if path.endswith(".html"):
                self.docs[path] = Document(content)
        self.scan()

    def issue(self, category, source, target, locator, line=0, detail=""):
        key = category, source, str(target), locator
        self.sequence[key] += 1
        finding = Finding(category, source, str(target), locator, self.sequence[key], line, detail)
        self.findings.append(finding)
        return finding

    def contract(self, path, kind, value):
        self.contracts[path][kind][digest(value)] += 1

    def resolve(self, source, value):
        if not value:
            return "ignored", None, None
        for scheme in ("data", "mailto", "tel", "javascript", "blob"):
            if value.lower().startswith(scheme + ":"):
                return scheme, None, None
        if re.search(r"%(?![a-fA-F0-9]{2})", value) or any(c in value for c in "\r\n\x00"):
            return "malformed", None, None
        try:
            parsed = urlsplit(urljoin(self.origin + route(source), value))
            if parsed.scheme not in ("http", "https"):
                return "ignored", None, None
            if parsed.netloc.lower() != self.host.lower():
                return "external", None, parsed
            decoded = unquote(parsed.path)
            if "\x00" in decoded or "\\" in decoded:
                return "malformed", None, parsed
            normalized = posixpath.normpath("/" + decoded.lstrip("/")).lstrip("/")
            if normalized == ".":
                normalized = ""
            candidates = [] if decoded.endswith("/") else [normalized]
            if decoded.endswith("/") or not PurePosixPath(normalized).suffix:
                candidates.append((normalized.rstrip("/") + "/" if normalized else "") + "index.html")
            found = next((p for p in candidates if p in self.tree.files), None)
            if found:
                return "local", found, parsed
            folded = self.folded_paths
            wrong_case = next((folded[p.casefold()] for p in candidates if p.casefold() in folded), None)
            return "case_error" if wrong_case else "missing", wrong_case or normalized, parsed
        except ValueError:
            return "malformed", None, None

    def reference(self, source, value, locator, line=0, media=False, node=None):
        state, target, parsed = self.resolve(source, value)
        self.references[state] += 1
        if state in ("ignored", "external", "data", "mailto", "tel", "javascript", "blob"):
            return
        if state == "malformed":
            self.issue("malformed_reference", source, value, locator, line)
            return
        is_asset = media or (parsed and (parsed.path.startswith("/assets/")
                                        or PurePosixPath(parsed.path).suffix.lower() in MEDIA_EXT))
        if state in ("missing", "case_error"):
            category = "case_sensitive_reference" if state == "case_error" else (
                "missing_asset" if is_asset else "missing_internal_page")
            self.issue(category, source, value, locator, line, f"Resolved local target: {target}")
            if is_asset:
                self.missing_assets[PurePosixPath(unquote(parsed.path)).suffix.lower()].add(unquote(parsed.path))
            return
        if parsed.fragment and not media:
            fragment = unquote(parsed.fragment)
            ids = set()
            document = self.docs.get(target)
            if document:
                ids = {n.attrs.get("id") for n in document.nodes}
                ids |= {n.attrs.get("name") for n in document.find("a")}
                for mount, partial in (("site-header", "partials/header.html"),
                                       ("site-footer", "partials/footer.html")):
                    if any(n.attrs.get("id") == mount for n in document.nodes) and partial in self.docs:
                        ids |= {n.attrs.get("id") for n in self.docs[partial].nodes}
                for include in document.nodes:
                    include_path = (include.attrs.get("data-include") or "").lstrip("/")
                    if include_path in self.docs:
                        ids |= {n.attrs.get("id") for n in self.docs[include_path].nodes}
            elif target.endswith(".svg"):
                try:
                    ids = {n.get("id") for n in ET.fromstring(self.tree.files[target]).iter()}
                except ET.ParseError:
                    pass
            if fragment not in ids:
                attrs = node.attrs if node else {}
                if fragment == "privacy-choices" and "js-consent" in (attrs.get("class") or "").split():
                    self.issue("runtime_fragment_review", source, value, locator, line,
                               "Privacy choices is bound by site.js, not a static anchor target.")
                else:
                    self.issue("broken_fragment", source, value, locator, line)

    def json_references(self, source, value, line, location="jsonld"):
        if isinstance(value, dict):
            for key, child in sorted(value.items()):
                loc = location + "." + key
                if isinstance(child, str) and ("/assets/" in child or
                        key in {"image", "logo", "thumbnailUrl", "contentUrl"}):
                    self.reference(source, child, loc, line, media=True)
                self.json_references(source, child, line, loc)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                if isinstance(child, str) and "/assets/" in child:
                    self.reference(source, child, f"{location}[{index}]", line, media=True)
                else:
                    self.json_references(source, child, line, f"{location}[{index}]")

    def scan_html(self, path, document):
        full = bool(document.find("html"))
        redirection = redirect(document)
        verification = path.startswith("google") and not full
        role = "redirect" if redirection else "content" if full else (
            "partial" if path.startswith("partials/") else "verification" if verification else "empty")
        self.roles[path] = role
        schemas = []
        for node in document.find("script"):
            if node.attrs.get("type") == "application/ld+json":
                try:
                    value = json.loads(node.text(), parse_constant=invalid_json_constant)
                    schemas.append(value)
                    self.json_references(path, value, node.line)
                except (ValueError, TypeError) as error:
                    self.issue("invalid_jsonld", path, str(error), "script[ld+json]", node.line)
            elif not node.attrs.get("src") or not node.attrs.get("src", "").startswith("data:"):
                self.contract(path, "integration_markup", node.markup())
        metadata = []
        for node in document.nodes:
            attrs = node.attrs
            if (node.tag == "title" or (node.tag == "meta" and (
                    attrs.get("name") in {"description", "robots", "twitter:title", "twitter:description",
                                          "twitter:image", "twitter:card"} or (attrs.get("property") or "").startswith("og:")))
                    or (node.tag == "link" and (attrs.get("rel") == "canonical" or attrs.get("hreflang")))):
                metadata.append(node.markup())
            if affiliate(node):
                self.contract(path, "affiliate_anchor", node.opening)
                self.affiliates[path].append(node)
            if node.tag == "form" and (attrs.get("data-affiliate-base") or attrs.get("data-aff")):
                self.contract(path, "affiliate_form", node.markup())
            if "tp-widget" in (attrs.get("class") or "").split():
                self.contract(path, "widget", node.markup())
            cls = set((attrs.get("class") or "").split())
            disclosure = (bool(cls & {"aff-note", "aff-note-lg", "foot-disclaimer"})
                          or attrs.get("id") == "disclosure"
                          or attrs.get("aria-label", "").lower() in {"disclosure", "affiliate disclosure"}
                          or (node.tag == "p" and "affiliate" in node.text().lower()))
            if disclosure:
                self.contract(path, "disclosure", node.markup())
            for attr in ("src", "poster", "data-preview-image", "data-include"):
                if attrs.get(attr):
                    self.reference(path, attrs[attr], node.tag + "[" + attr + "]", node.line,
                                   media=attr != "data-include")
            if attrs.get("href") and node.tag in {"a", "link"}:
                if node.tag == "a" or attrs.get("rel") not in {"canonical", "alternate", "preconnect", "dns-prefetch"}:
                    self.reference(path, attrs["href"], node.tag + "[href]", node.line,
                                   media=node.tag == "link", node=node)
            for attr in ("srcset", "imagesrcset"):
                for url in srcset_urls(attrs.get(attr) or ""):
                    self.reference(path, url, node.tag + "[" + attr + "]", node.line, media=True)
            if node.tag == "meta" and (attrs.get("property") == "og:image" or attrs.get("name") == "twitter:image"):
                self.reference(path, attrs.get("content") or "", "meta[" +
                               (attrs.get("property") or attrs.get("name")) + "]", node.line, media=True)
        if metadata:
            self.contract(path, "seo_metadata", metadata)
        if redirection:
            destination, node = redirection
            self.contract(path, "redirect_behavior", [node.opening, metadata])
            self.reference(path, destination, "meta[refresh]", node.line)
            if not destination:
                self.issue("invalid_redirect", path, node.attrs.get("content") or "", "meta[refresh]")
            self.exclusions.append({"source": path, "category": "intentional_redirect",
                                    "reason": "Redirect aliases are not independent sitemap articles."})
        for node in document.duplicate_attributes:
            self.issue("duplicate_html_attribute", path, node.tag, "attributes", node.line)
        ids = Counter(node.attrs["id"] for node in document.nodes if "id" in node.attrs)
        for value, count in sorted(ids.items()):
            if count > 1:
                self.issue("duplicate_html_id", path, value, "id", detail=f"Occurrences: {count}")
        if role == "empty":
            self.issue("empty_html_page", path, route(path), "document")
        if role != "content":
            return
        robots = [n for n in document.find("meta") if (n.attrs.get("name") or "").lower() == "robots"]
        noindex = any("noindex" in {d.strip() for d in (n.attrs.get("content") or "").lower().split(",")}
                      for n in robots)
        for node in robots:
            value = node.attrs.get("content") or ""
            for directive in value.lower().split(","):
                directive = directive.strip()
                flags = {"all", "none", "index", "noindex", "follow", "nofollow", "nosnippet",
                         "noarchive", "notranslate", "noimageindex", "indexifembedded", "nocache"}
                valid = directive in flags or bool(re.fullmatch(
                    r"(?:max-snippet|max-video-preview):(?:-1|\d+)|max-image-preview:(?:none|standard|large)|unavailable_after:.+", directive))
                if not valid:
                    self.issue("robots_syntax", path, directive, "meta[robots]", node.line)
        if noindex:
            self.exclusions.append({"source": path, "category": "noindex", "reason": "Explicit noindex page."})
            return
        for tag, nodes in (("title", document.find("title")),
                           ("description", [n for n in document.find("meta") if n.attrs.get("name") == "description"]),
                           ("canonical", [n for n in document.find("link") if n.attrs.get("rel") == "canonical"])):
            if len(nodes) != 1 or (tag == "title" and not nodes[0].text().strip()) or (
                    tag == "description" and not (nodes[0].attrs.get("content") or "").strip()):
                self.issue("seo_" + tag + "_count", path, len(nodes), tag)
        canonical = [n for n in document.find("link") if n.attrs.get("rel") == "canonical"]
        if len(canonical) == 1:
            value = canonical[0].attrs.get("href") or ""
            expected = self.origin + route(path)
            self.canonicals[path] = value
            try:
                parsed = urlsplit(value)
                valid = (parsed.scheme == "https" and parsed.netloc == self.host and
                         not parsed.query and not parsed.fragment and not re.search(r"\s", value)
                         and value.startswith(self.origin + "/") and not value.endswith("/index.html"))
            except ValueError:
                valid = False
            if not valid:
                self.issue("canonical_shape", path, value, "link[canonical]")
            elif value != expected:
                self.issue("canonical_route_review", path, value, "link[canonical]",
                           detail="Cross-route canonical requires editorial/localization review.")
                self.exclusions.append({"source": path, "category": "cross_route_canonical",
                                        "reason": "Current canonical targets another route; do not auto-correct."})
            state, _, _ = self.resolve(path, value)
            if state != "local":
                self.issue("canonical_destination", path, value, "link[canonical]")
        flat = []
        for value in schemas:
            flat.extend(value.get("@graph", [value]) if isinstance(value, dict) else value if isinstance(value, list) else [])
        article = any(isinstance(n, dict) and "Article" in (
            n.get("@type") if isinstance(n.get("@type"), list) else [n.get("@type")]) for n in flat)
        if article:
            self.article_paths.add(path)
        if article and len(document.find("h1")) != 1:
            self.issue("article_h1_count", path, len(document.find("h1")), "h1")

    def scan_sitemaps(self):
        seen = Counter()
        names = sorted(p for p in self.tree.files if PurePosixPath(p).name.startswith("sitemap") and p.endswith(".xml"))
        for path in names:
            try:
                tree = ET.fromstring(self.tree.files[path])
            except ET.ParseError as error:
                self.issue("invalid_sitemap_xml", path, str(error), "xml")
                continue
            if tree.tag not in {f"{{{NS}}}urlset", f"{{{NS}}}sitemapindex"}:
                self.issue("sitemap_namespace", path, tree.tag, "xml")
                continue
            index = tree.tag.endswith("sitemapindex")
            entry_tag = "sitemap" if index else "url"
            for entry in tree.findall(f"{{{NS}}}{entry_tag}"):
                locs = entry.findall(f"{{{NS}}}loc")
                if len(locs) != 1:
                    self.issue("sitemap_loc_count", path, len(locs), entry_tag)
                    continue
                value = locs[0].text or ""
                try:
                    u = urlsplit(value)
                    valid = (u.scheme == "https" and u.netloc == self.host and
                             not u.query and not u.fragment and not re.search(r"\s", value)
                             and value.startswith(self.origin + "/"))
                except ValueError:
                    valid = False
                if not valid:
                    self.issue("sitemap_url_shape", path, value, entry_tag + "/loc")
                state, target, _ = self.resolve(path, value)
                if state != "local":
                    self.issue("sitemap_destination", path, value, entry_tag + "/loc")
                elif index:
                    if target not in names:
                        self.issue("sitemap_index_target", path, value, "sitemap/loc")
                    self.sitemap_index.append(target)
                else:
                    self.sitemap_urls.append(value)
                    if self.roles.get(target) in {"empty", "redirect", "partial", "verification"}:
                        self.issue("sitemap_non_content", path, value, "url/loc",
                                   detail="Sitemap points to an empty/non-content/redirect file.")
                    elif self.canonicals.get(target) != value:
                        self.issue("sitemap_canonical_alignment", path, value, "url/loc")
                key = ("index" if index else "page", value)
                seen[key] += 1
                if seen[key] > 1:
                    self.issue("sitemap_duplicate", path, value, entry_tag + "/loc")
        for path in names:
            if path != "sitemap.xml" and path not in self.sitemap_index:
                self.issue("sitemap_unindexed", "sitemap.xml", path, "sitemapindex")
        for path, canonical in sorted(self.canonicals.items()):
            if canonical == self.origin + route(path) and canonical not in self.sitemap_urls:
                self.issue("sitemap_missing_canonical", path, canonical, "canonical coverage")

    def scan(self):
        for path, document in sorted(self.docs.items()):
            self.scan_html(path, document)
        for path, content in sorted(self.tree.files.items()):
            extension = PurePosixPath(path).suffix.lower()
            if "yacht-charter" in path.lower():
                self.issue("forbidden_yacht_charter", path, path, "path")
            if "searadar" in path.lower():
                self.issue("forbidden_searadar", path, path, "path")
            if extension in TEXT_EXT:
                text = content.decode("utf-8-sig", "replace")
                if re.search(r"searadar", text, re.I):
                    self.issue("forbidden_searadar", path, "SeaRadar", "integration")
                if re.search(r"yacht[ -]?charter", text, re.I):
                    self.issue("forbidden_yacht_charter", path, "Yacht Charter", "integration")
            if extension == ".css":
                text = re.sub(r"/\*.*?\*/", "", content.decode("utf-8-sig"), flags=re.S)
                for match in re.finditer(r"url\(\s*(['\"]?)(.*?)\1\s*\)|@import\s+(['\"])(.*?)\3", text, re.S):
                    value = match.group(2) if match.group(2) is not None else match.group(4)
                    if value and not value.startswith("#"):
                        self.reference(path, value, "css import/url", media=True)
            if extension in {".js", ".mjs"}:
                self.integration_scripts[path] = blob_hash(path, content)
                text = content.decode("utf-8-sig")
                patterns = [r"['\"](/(?:assets|partials)/[^'\"]+)['\"]",
                            r"\b(?:from|import)\s*['\"]((?:\./|\.\./|/(?!/))[^'\"]+)['\"]",
                            r"\b(?:import|fetch)\s*\(\s*['\"]((?:\./|\.\./|/(?!/))[^'\"]+)['\"]"]
                matches = set()
                for pattern in patterns:
                    matches.update((m.start(), m.group(1)) for m in re.finditer(pattern, text))
                for offset, value in sorted(matches):
                    urls = srcset_urls(value) if re.search(r"\s+\d+(?:w|x)(?:,|\s|$)", value) else [value]
                    for url in urls:
                        self.reference(path, url, "js literal import/asset", text[:offset].count("\n") + 1, media=True)
        self.scan_sitemaps()
        self.findings.sort(key=lambda item: item.identifier)

    def inventory(self):
        return {
            "html_files": len(self.docs), "html_roles": dict(sorted(Counter(self.roles.values()).items())),
            "affiliate_anchors": sum(map(len, self.affiliates.values())),
            "affiliate_providers": dict(sorted(Counter(n.attrs.get("data-aff") or
                urlsplit(n.attrs.get("href") or "").netloc for nodes in self.affiliates.values() for n in nodes).items())),
            "contract_counts": dict(sorted(self.contract_counts().items())),
            "missing_assets_by_extension": {k: len(v) for k, v in sorted(self.missing_assets.items())},
            "missing_asset_paths": len(set().union(*self.missing_assets.values())) if self.missing_assets else 0,
            "issues_by_category": dict(sorted(Counter(f.category for f in self.findings).items())),
            "reference_classifications": dict(sorted(self.references.items())),
            "sitemap_files": sum(p.endswith(".xml") and PurePosixPath(p).name.startswith("sitemap") for p in self.tree.files),
            "sitemap_locations": len(self.sitemap_urls), "sitemap_unique_locations": len(set(self.sitemap_urls)),
            "sitemap_index_entries": sorted(self.sitemap_index),
            "protected_cruise_files": self.protected(), "integration_scripts": self.integration_scripts,
            "inventory_exclusions": self.exclusions,
        }

    def contract_counts(self):
        counts = Counter()
        for groups in self.contracts.values():
            for kind, values in groups.items():
                counts[kind] += sum(values.values())
        return counts

    def protected(self):
        return {p: blob_hash(p, b) for p, b in sorted(self.tree.files.items()) if "cruise" in p.lower()}


def fixture_for(audit, recorded_on):
    reasons = {
        "runtime_fragment_review": "Existing JavaScript-owned consent control; requires browser review, not a static target.",
        "canonical_route_review": "Existing French canonical decision; retain pending localization review.",
        "sitemap_duplicate": "Existing redundant sitemap inventory; repair in a bounded sitemap PR.",
        "sitemap_missing_canonical": "Existing publication coverage gap; repair in a bounded sitemap PR.",
        "robots_syntax": "Existing robots directive syntax; repair in a reviewed SEO PR.",
    }
    return {
        "schema_version": 1, "source_revision": audit.tree.revision, "site_origin": audit.origin,
        "recorded_on": recorded_on, "inventory": audit.inventory(),
        "contracts": {p: {kind: dict(sorted(values.items())) for kind, values in sorted(groups.items())}
                      for p, groups in sorted(audit.contracts.items())},
        "exceptions": [{**finding.record(), "reason": reasons.get(finding.category,
            "Historical defect verified on the recorded main revision; repair separately without expanding its scope."),
            "recorded_on": recorded_on} for finding in audit.findings],
        "authorizations": [],
    }


def valid_authorization(entry):
    required = {"kind", "source", "before", "after", "reason", "reviewed_by", "recorded_on", "base_revision"}
    if not isinstance(entry, dict) or not required <= entry.keys():
        return False
    if not all(isinstance(entry[k], str) and entry[k].strip() for k in required - {"before", "after"}):
        return False
    try:
        date.fromisoformat(entry["recorded_on"])
    except ValueError:
        return False
    return all(entry[k] is None or (isinstance(entry[k], str) and
               bool(re.fullmatch(r"[a-f0-9]{64}", entry[k]))) for k in ("before", "after"))


def compare(current, base, fixture):
    errors, known, resolved, authorized = [], [], [], []
    base_ids = {f.identifier for f in base.findings}
    current_ids = {f.identifier for f in current.findings}
    exceptions = {item["id"]: item for item in fixture["exceptions"]}
    authorizations = fixture.get("authorizations", [])
    for entry in authorizations:
        if not valid_authorization(entry):
            errors.append({"category": "invalid_authorization", "source": FIXTURE, "detail": str(entry)})

    def permitted(kind, source, before, after):
        entry = next((a for a in authorizations if valid_authorization(a) and
                     a["base_revision"] == base.tree.revision and
                     (a["kind"], a["source"], a["before"], a["after"]) == (kind, source, before, after)), None)
        if entry:
            authorized.append({"kind": kind, "source": source, "reason": entry["reason"], "reviewed_by": entry["reviewed_by"]})
        return bool(entry)

    for finding in current.findings:
        if finding.identifier in exceptions and finding.identifier in base_ids:
            known.append(finding.record())
        else:
            record = finding.record()
            record["status"] = "reintroduced" if finding.identifier in exceptions else "new"
            errors.append(record)
    for identifier in sorted(set(exceptions) - current_ids):
        resolved.append({"id": identifier, "source": exceptions[identifier]["source"],
                         "category": exceptions[identifier]["category"]})
    for path, groups in sorted(base.contracts.items()):
        for kind, before in sorted(groups.items()):
            after = current.contracts.get(path, {}).get(kind, Counter())
            missing = before - after
            if missing and not permitted(kind, path, digest(dict(before)), digest(dict(after))):
                errors.append({"category": "contract_changed", "source": path, "kind": kind,
                               "before": digest(dict(before)), "after": digest(dict(after)),
                               "removed_or_modified": sum(missing.values())})
    for kind, protected in (("cruise_file", base.protected()), ("integration_script", base.integration_scripts)):
        for path, before in sorted(protected.items()):
            after = blob_hash(path, current.tree.files[path]) if path in current.tree.files else None
            if before != after and not permitted(kind, path, before, after):
                errors.append({"category": "protected_file_changed", "kind": kind, "source": path,
                               "before": before, "after": after})
    for path in sorted(base.docs):
        if path not in current.tree.files and not permitted("published_file", path,
                blob_hash(path, base.tree.files[path]), None):
            errors.append({"category": "published_file_deleted", "source": path})
    for path in sorted(base.article_paths - current.article_paths):
        if path in current.docs and len(current.docs[path].find("h1")) != 1:
            errors.append({"category": "article_h1_count", "source": path,
                           "detail": "Base article lost its H1 even though its schema type changed."})
    for path, nodes in current.affiliates.items():
        retained = Counter(base.contracts.get(path, {}).get("affiliate_anchor", {}))
        for node in nodes:
            sha = digest(node.opening)
            if retained[sha]:
                retained[sha] -= 1
                continue
            attrs = node.attrs
            program = attrs.get("data-aff") or ""
            u = urlsplit(attrs.get("href") or "")
            valid = (u.scheme == "https" and u.netloc in PARTNERS.get(program, set())
                     and attrs.get("target") == "_blank" and bool(attrs.get("data-subid"))
                     and "js-aff" in (attrs.get("class") or "").split()
                     and {"nofollow", "sponsored", "noopener"} <= set((attrs.get("rel") or "").split()))
            if not valid:
                errors.append({"category": "new_affiliate_needs_review", "source": path,
                               "line": node.line, "markup_sha256": sha, "href": attrs.get("href")})
    for path, document in current.docs.items():
        reusable_scripts = {sha for groups in base.contracts.values()
                            for sha in groups.get("integration_markup", {})}
        old_widgets = Counter(base.contracts.get(path, {}).get("widget", {}))
        for node in document.nodes:
            if node.tag == "script" and node.attrs.get("type") != "application/ld+json":
                sha = digest(node.markup())
                if sha not in reusable_scripts and not permitted("new_integration_markup", path, None, sha):
                    errors.append({"category": "new_integration_needs_review", "source": path,
                                   "line": node.line, "after": sha})
            if "tp-widget" in (node.attrs.get("class") or "").split():
                sha = digest(node.markup())
                if old_widgets[sha]:
                    old_widgets[sha] -= 1
                elif not permitted("new_widget", path, None, sha):
                    errors.append({"category": "new_widget_needs_review", "source": path, "after": sha})
        old = Counter(base.contracts.get(path, {}).get("affiliate_form", {}))
        for node in document.find("form"):
            if not (node.attrs.get("data-aff") or node.attrs.get("data-affiliate-base")):
                continue
            sha = digest(node.markup())
            if old[sha]:
                old[sha] -= 1
                continue
            a = node.attrs
            u = urlsplit(a.get("data-affiliate-base") or "")
            if not (u.scheme == "https" and u.netloc in PARTNERS.get(a.get("data-aff"), set())
                    and a.get("data-subid")):
                errors.append({"category": "new_affiliate_form_needs_review", "source": path})
    for path, sha in sorted(current.integration_scripts.items()):
        if path not in base.integration_scripts and not permitted("new_integration_script", path, None, sha):
            errors.append({"category": "new_integration_needs_review", "source": path, "after": sha})
    return {"passed": not errors, "base_revision": base.tree.revision,
            "known": known, "resolved": resolved, "errors": sorted(errors, key=lambda x: encoded(x)),
            "authorized": authorized, "inventory": current.inventory()}


def validate_fixture(fixture, recorded):
    if (not isinstance(fixture, dict) or not isinstance(fixture.get("exceptions"), list)
            or not isinstance(fixture.get("authorizations", []), list)):
        raise ValueError("Baseline must contain exception and authorization arrays.")
    if fixture.get("schema_version") != 1 or fixture.get("site_origin") != ORIGIN:
        raise ValueError("Unsupported baseline schema/origin; requires a separate reviewed policy migration.")
    expected = fixture_for(recorded, fixture["recorded_on"])
    date.fromisoformat(fixture["recorded_on"])
    for key in ("source_revision", "inventory", "contracts"):
        if fixture.get(key) != expected[key]:
            raise ValueError(f"Baseline {key} does not reproduce its recorded Git revision.")
    original = {item["id"]: item for item in expected["exceptions"]}
    seen = set()
    for entry in fixture["exceptions"]:
        if not isinstance(entry, dict):
            raise ValueError("Every exception must be an object.")
        identifier = entry.get("id")
        if identifier in seen or identifier not in original:
            raise ValueError("Duplicate/new exception not verified on the recorded Git revision: " + str(identifier))
        seen.add(identifier)
        for key in ("category", "source", "target", "locator", "occurrence"):
            if entry.get(key) != original[identifier][key]:
                raise ValueError("Exception identity was changed: " + identifier)
        if not isinstance(entry.get("reason"), str) or not entry["reason"].strip():
            raise ValueError("Exception needs a reason: " + identifier)
        date.fromisoformat(entry["recorded_on"])


def readable(result, verbose=False):
    inv = result["inventory"]
    lines = ["Site audit: " + ("PASS" if result["passed"] else "FAIL"),
             f"HTML files: {inv['html_files']}; affiliate anchors: {inv['affiliate_anchors']}; sitemap XML: {inv['sitemap_files']}",
             f"Known historical findings: {len(result['known'])}; resolved: {len(result['resolved'])}; regressions: {len(result['errors'])}",
             f"Distinct missing asset paths: {inv['missing_asset_paths']}; protected cruise files: {len(inv['protected_cruise_files'])}",
             "Historical categories: " + json.dumps(dict(sorted(Counter(f['category'] for f in result['known']).items())), sort_keys=True)]
    for record in result["errors"]:
        lines.append("ERROR " + json.dumps(record, sort_keys=True, ensure_ascii=False))
    for record in result["resolved"]:
        lines.append("RESOLVED " + json.dumps(record, sort_keys=True))
    for record in result["authorized"]:
        lines.append("AUTHORIZED " + json.dumps(record, sort_keys=True))
    if verbose:
        for record in result["known"]:
            lines.append("KNOWN " + json.dumps(record, sort_keys=True, ensure_ascii=False))
    return "\n".join(lines) + "\n"


def self_test(_base, _fixture):
    """Mutation tests run on dictionaries of immutable bytes, never on site files."""
    # A tiny independent site keeps tests valid as production defects are repaired.
    def content(path, body=""):
        url = ORIGIN + route(path)
        return ('<!doctype html><html lang="en"><head><title>Fixture</title>'
                '<meta name="description" content="Fixture"><meta name="robots" content="index,follow">'
                f'<link rel="canonical" href="{url}"><link rel="stylesheet" href="/assets/css/styles.css">'
                f'<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Article","url":"{url}"}}</script>'
                '</head><body><h1>Fixture</h1>' + body + '</body></html>\n').encode()

    missing_image = "/assets/images/attractions/disney/disneyland-paris-castle.webp"
    anchor = ('<a class="js-aff" data-aff="klook" data-subid="fixture" '
              'href="https://klook.tpk.ro/H4hEgxrx" target="_blank" rel="nofollow sponsored noopener">Probe</a>')
    paths = ["index.html", "about/index.html", "attractions/disneyland-paris-tickets/index.html",
             "cruises/caribbean/index.html"]
    files = {p: content(p) for p in paths}
    files["about/index.html"] = content("about/index.html", f'<img src="{missing_image}" alt="Probe">')
    files[paths[2]] = content(paths[2], '<h2 id="ticket-types">Types</h2>' + anchor)
    files.update({"assets/css/styles.css": b"body { color: black; }\n",
                  "assets/js/site.js": b"/* tracking fixture */\n",
                  "assets/images/tg-logo.png": b"fixture image",
                  "assets/images/hero/disneyland-tickets-castle-800x450.webp": b"fixture image"})
    files["sitemap-core.xml"] = (f'<urlset xmlns="{NS}">' + ''.join(
        f'<url><loc>{ORIGIN + route(p)}</loc></url>' for p in paths) + '</urlset>\n').encode()
    files["sitemap.xml"] = (f'<sitemapindex xmlns="{NS}"><sitemap><loc>{ORIGIN}/sitemap-core.xml</loc>'
                            '</sitemap></sitemapindex>\n').encode()
    base = Audit(Tree(files, "self-test"))
    fixture = fixture_for(base, "2026-10-08")
    outcomes = []

    def run(name, change, expected=None, base_audit=base, fixture_value=fixture):
        tree = base_audit.tree.copy()
        change(tree)
        result = compare(Audit(tree), base_audit, fixture_value)
        categories = {e["category"] for e in result["errors"]}
        okay = (expected in categories and not result["passed"]) if expected else result["passed"]
        outcomes.append({"test": name, "passed": okay, "expected": expected or "pass",
                         "actual_errors": sorted(categories), "resolved": len(result["resolved"])})
        return result

    def insert(tree, text, path="about/index.html"):
        tree.files[path] = tree.files[path].replace(b"</body>", text.encode() + b"\n</body>")

    run("unchanged baseline", lambda t: None)
    run("new broken internal link", lambda t: insert(t, '<a href="/regression-missing/">Probe</a>'), "missing_internal_page")
    run("new missing image", lambda t: insert(t, '<img src="/assets/images/regression-missing.webp" alt="Probe">'), "missing_asset")
    run("changed existing affiliate URL", lambda t: t.files.__setitem__(
        "attractions/disneyland-paris-tickets/index.html", t.files["attractions/disneyland-paris-tickets/index.html"].replace(
            b"https://klook.tpk.ro/H4hEgxrx", b"https://klook.tpk.ro/H4hEgxrZ")), "contract_changed")
    run("malformed sitemap", lambda t: t.files.__setitem__("sitemap-core.xml", b"<urlset>"), "invalid_sitemap_xml")
    run("invalid JSON-LD", lambda t: t.files.__setitem__("about/index.html", t.files["about/index.html"].replace(
        b'"@context"', b'INVALID "@context"', 1)), "invalid_jsonld")
    run("non-JSON NaN rejected", lambda t: insert(t, '<script type="application/ld+json">{"value":NaN}</script>'), "invalid_jsonld")
    run("cruise file removed", lambda t: t.files.pop("cruises/caribbean/index.html"), "protected_file_changed")
    run("missing stylesheet", lambda t: insert(t, '<link rel="stylesheet" href="/assets/css/regression-missing.css">'), "missing_asset")
    run("case-sensitive filename", lambda t: insert(t, '<img src="/assets/images/TG-LOGO.png" alt="Probe">'), "case_sensitive_reference")
    run("broken fragment", lambda t: insert(t, '<a href="/about/#regression-missing">Probe</a>'), "broken_fragment")
    run("bad srcset candidate", lambda t: insert(t, '<img src="/assets/images/tg-logo.png" srcset="/assets/images/tg-logo.png 1x, /assets/images/probe-missing.png 2x" alt="Probe">'), "missing_asset")
    run("missing CSS import", lambda t: t.files.__setitem__("assets/css/styles.css", t.files["assets/css/styles.css"] + b'\n@import "./probe-missing.css";\n'), "missing_asset")
    run("missing JS import", lambda t: t.files.__setitem__("assets/js/probe.js", b'import "./probe-missing.mjs";\n'), "missing_asset")
    run("invalid existing canonical", lambda t: t.files.__setitem__("about/index.html", t.files["about/index.html"].replace(
        b'rel="canonical" href="https://tripguidely.github.io/about/"', b'rel="canonical" href="https://invalid.example/about/"')), "canonical_shape")
    run("published page removed", lambda t: t.files.pop("about/index.html"), "published_file_deleted")
    run("new valid internal link", lambda t: insert(t, '<a href="../attractions/disneyland-paris-tickets/index.html?probe=1#ticket-types">Probe</a>'))

    def page(tree, aff=False):
        url = ORIGIN + "/regression-valid/"
        cta = ('<p class="aff-note">Affiliate disclosure: test fixture only.</p>'
               '<a class="btn js-aff" data-aff="klook" data-subid="regression_fixture" '
               'href="https://klook.tpk.ro/TestOnly" target="_blank" rel="nofollow sponsored noopener">Probe</a>') if aff else ""
        content = ('<!doctype html><html lang="en"><head><title>Fixture</title>'
                   '<meta name="description" content="Fixture"><meta name="robots" content="index,follow">'
                   f'<link rel="canonical" href="{url}"><link rel="stylesheet" href="/assets/css/styles.css">'
                   f'<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Article","url":"{url}"}}</script>'
                   '</head><body><main><h1>Fixture</h1>' + cta + '</main></body></html>\n')
        tree.files["regression-valid/index.html"] = content.encode()
        tree.files["sitemap-core.xml"] = tree.files["sitemap-core.xml"].replace(b"</urlset>", f"<url><loc>{url}</loc></url></urlset>".encode())

    run("new valid page and sitemap entry", page)
    run("new legitimate affiliate CTA", lambda t: page(t, True))
    run("malformed new affiliate CTA", lambda t: insert(t, anchor.replace('data-subid="fixture"', '')), "new_affiliate_needs_review")
    run("annotated affiliate cannot omit tracking tokens", lambda t: insert(t, anchor.replace(
        'class="js-aff"', '').replace('rel="nofollow sponsored noopener"', '').replace(
        'https://klook.tpk.ro/H4hEgxrx', 'https://www.klook.com/fixture')), "new_affiliate_needs_review")
    run("tracking script changed", lambda t: t.files.__setitem__("assets/js/site.js", b"/* changed */\n"), "protected_file_changed")
    run("new integration script requires review", lambda t: insert(t, '<script src="https://tp.media/new-widget.js"></script>'), "new_integration_needs_review")
    run("new widget requires review", lambda t: insert(t, '<div class="tp-widget" data-marker="fixture"></div>'), "new_widget_needs_review")
    run("missing sitemap coverage", lambda t: t.files.__setitem__("regression-valid/index.html", content("regression-valid/index.html")), "sitemap_missing_canonical")
    run("duplicate sitemap URL", lambda t: t.files.__setitem__("sitemap-core.xml", t.files["sitemap-core.xml"].replace(
        b"</urlset>", f"<url><loc>{ORIGIN}/about/</loc></url></urlset>".encode())), "sitemap_duplicate")
    run("missing article H1", lambda t: t.files.__setitem__("about/index.html", t.files["about/index.html"].replace(b"<h1>Fixture</h1>", b"")), "article_h1_count")
    run("article type removal cannot bypass H1", lambda t: t.files.__setitem__("about/index.html", t.files["about/index.html"].replace(b"<h1>Fixture</h1>", b"").replace(b'"Article"', b'"WebPage"')), "article_h1_count")
    run("new valid encoded link", lambda t: insert(t, '<a href="/%61bout/index.html?probe=1">Probe</a>'))
    run("multiline srcset first candidate", lambda t: insert(t, '<img src="/assets/images/tg-logo.png" srcset="\n /assets/images/first-missing.webp 1x,\n /assets/images/tg-logo.png 2x" alt="Probe">'), "missing_asset")
    run("new valid srcset", lambda t: insert(t, '<img src="/assets/images/tg-logo.png" srcset="\n /assets/images/tg-logo.png 1x,\n /assets/images/tg-logo.png 2x" alt="Probe">'))
    run("missing absolute JS import", lambda t: t.files.__setitem__("assets/js/probe.js", b'import "/probe-missing.mjs";\n'), "missing_asset")
    run("forbidden SeaRadar", lambda t: insert(t, "<p>SeaRadar integration</p>"), "forbidden_searadar")
    run("forbidden Yacht Charter", lambda t: t.files.__setitem__("yacht-charter/index.html", content("yacht-charter/index.html")), "forbidden_yacht_charter")
    approved_tree = base.tree.copy()
    approved_tree.files["assets/js/site.js"] = b"/* explicitly reviewed tracking update */\n"
    approval = {"kind": "integration_script", "source": "assets/js/site.js",
                "base_revision": base.tree.revision,
                "before": base.integration_scripts["assets/js/site.js"],
                "after": blob_hash("assets/js/site.js", approved_tree.files["assets/js/site.js"]),
                "reason": "Synthetic owner review", "reviewed_by": "fixture-owner", "recorded_on": "2026-10-08"}
    approved_fixture = dict(fixture, authorizations=[approval])
    run("narrow approved script change", lambda t: t.files.update(approved_tree.files), fixture_value=approved_fixture)
    wrong_fixture = dict(fixture, authorizations=[dict(approval, after="0" * 64)])
    run("approval cannot cover another hash", lambda t: t.files.update(approved_tree.files), "protected_file_changed", fixture_value=wrong_fixture)
    other_base_fixture = dict(fixture, authorizations=[dict(approval, base_revision="other-base")])
    run("approval cannot replay on another base", lambda t: t.files.update(approved_tree.files), "protected_file_changed", fixture_value=other_base_fixture)
    target = "assets/images/attractions/disney/disneyland-paris-castle.webp"
    image = base.tree.files["assets/images/hero/disneyland-tickets-castle-800x450.webp"]
    repaired = run("historical missing image repaired", lambda t: t.files.__setitem__(target, image))
    outcomes[-1]["passed"] &= bool(repaired["resolved"])
    fixed_tree = base.tree.copy()
    fixed_tree.files[target] = image
    fixed = Audit(fixed_tree)
    run("resolved issue cannot silently return", lambda t: t.files.pop(target), "missing_asset", base_audit=fixed)
    repeated = compare(Audit(base.tree.copy()), base, fixture)
    outcomes.append({"test": "deterministic result", "passed": encoded(repeated) == encoded(compare(Audit(base.tree.copy()), base, fixture))})
    outcomes.append({"test": "data URL srcset token", "passed": srcset_urls('data:image/png;base64,AAAA 1x, /assets/images/tg-logo.png 2x') == ['data:image/png;base64,AAAA', '/assets/images/tg-logo.png']})
    print(json.dumps({"self_tests": outcomes, "passed": all(t["passed"] for t in outcomes)}, indent=2))
    return all(t["passed"] for t in outcomes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--base-ref", default="origin/main")
    parser.add_argument("--baseline", default=FIXTURE)
    parser.add_argument("--record-baseline", action="store_true", help="Explicit initial fixture creation; refuses overwrite")
    parser.add_argument("--recorded-on", help="Required ISO date for explicit baseline recording")
    parser.add_argument("--json", action="store_true", help="Deterministic machine report, without wall-clock runtime")
    parser.add_argument("--verbose", action="store_true", help="Print every historical finding")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    started = time.perf_counter()
    try:
        root = args.root.resolve()
        base_tree = Tree.revision_tree(root, args.base_ref)
        base = Audit(base_tree)
        fixture_path = root / args.baseline
        if args.record_baseline:
            if fixture_path.exists():
                raise ValueError("Refusing to overwrite a baseline. Retire resolved entries manually; do not regenerate it.")
            if not args.recorded_on:
                raise ValueError("--record-baseline requires --recorded-on YYYY-MM-DD")
            date.fromisoformat(args.recorded_on)
            fixture_path.parent.mkdir(parents=True, exist_ok=True)
            fixture_path.write_text(json.dumps(fixture_for(base, args.recorded_on), indent=2,
                                               ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
            print("Recorded explicit baseline from " + base_tree.revision)
            return 0
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        recorded_tree = base_tree if fixture["source_revision"] == base_tree.revision else Tree.revision_tree(root, fixture["source_revision"])
        git(root, "merge-base", "--is-ancestor", fixture["source_revision"], base_tree.revision)
        recorded = base if recorded_tree is base_tree else Audit(recorded_tree)
        validate_fixture(fixture, recorded)
        # If the base already has a fixture, it supplies the trusted exception
        # ceiling. A PR may retire exceptions, never silently add new ones.
        exists = subprocess.run(["git", "-C", str(root), "cat-file", "-e", base_tree.revision + ":" + args.baseline], capture_output=True)
        if exists.returncode == 0:
            old_fixture = json.loads(git(root, "show", base_tree.revision + ":" + args.baseline))
            old_ids = {e["id"] for e in old_fixture["exceptions"]}
            if any(e["id"] not in old_ids for e in fixture["exceptions"]):
                raise ValueError("PR fixture adds exceptions. New defects must fail; use a separately reviewed policy PR.")
        if args.self_test:
            return 0 if self_test(base, fixture) else 1
        current = Audit(Tree.working(root))
        result = compare(current, base, fixture)
        if args.json:
            print(json.dumps(result, sort_keys=True, ensure_ascii=False, indent=2))
        else:
            print(readable(result, args.verbose), end="")
            print(f"Audit runtime: {time.perf_counter() - started:.3f}s")
        return 0 if result["passed"] else 1
    except (ValueError, OSError, KeyError, UnicodeError, json.JSONDecodeError) as error:
        print("AUDIT CONFIGURATION ERROR: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
