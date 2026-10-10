#!/usr/bin/env python3
"""Read-only image audit and disposable optimization previews. Python 3.12 + Pillow.

No network calls, generation, repository edits, or publishing. See docs/image-seo-agent-v1.md.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
from html import escape
from html.parser import HTMLParser
import json
import math
import os
from pathlib import Path
import posixpath
import re
import sys
import unicodedata
from urllib.parse import unquote, urljoin, urlsplit
import xml.etree.ElementTree as ET

from PIL import Image, ImageChops, ImageOps, ImageStat, features

EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.avif', '.gif', '.svg', '.ico', '.bmp', '.tif', '.tiff'}
WIDTHS = (320, 480, 640, 768, 960, 1200, 1600, 1920)
SKIP = {'.git', 'node_modules', '__pycache__', '.venv', 'venv'}
CSS_URL = re.compile(r'url\(\s*(?:"([^"]*)"|\x27([^\x27]*)\x27|([^)]*))\s*\)', re.I)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files(root):
    """Do not follow directory symlinks, dependencies, or nested worktrees."""
    import os
    for parent, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in SKIP and
                         not (Path(parent) / d).is_symlink() and
                         not (Path(parent) / d / '.git').exists())
        for name in sorted(names):
            path = Path(parent) / name
            if not path.is_symlink():
                yield path


def safe_output(root, output):
    """Reject output in ANY git checkout, including other worktrees, and ancestor paths."""
    output = Path(os.path.abspath(output))
    for parent in (output, *output.parents):
        if os.path.lexists(parent):
            info = parent.lstat()
            if parent.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400:
                raise ValueError('Symlink/reparse output ancestry forbidden')
    root, output = root.resolve(), output.resolve()
    if output == root or output.is_relative_to(root) or root.is_relative_to(output):
        raise ValueError('Output must be outside the source repository, not its ancestor')
    for parent in (output, *output.parents):
        if os.path.lexists(parent / '.git'):
            raise ValueError('Output inside a Git worktree is forbidden')
    return output


class ExclusiveOutput:
    """Reserve a fresh private directory; never replace an existing inode or remove outputs."""
    def __init__(self, root, output):
        self.root = root
        self.path = safe_output(root, output)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        safe_output(root, self.path)
        try:
            self.path.mkdir(mode=0o700)  # Atomic reservation; even an empty existing directory fails.
        except FileExistsError as error:
            raise ValueError('Use a fresh output directory; existing outputs are never replaced') from error
        self.identity = self.path.stat()

    def write(self, name, content):
        if Path(name).name != name or name in ('', '.', '..'):
            raise ValueError('Output name must be a single filename')
        safe_output(self.root, self.path)
        if not os.path.samestat(self.identity, self.path.stat()):
            raise ValueError('Output directory identity changed')
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_BINARY', 0)
        # O_EXCL rejects regular files, hardlinks and dangling symlinks, including races.
        fd = os.open(self.path / name, flags, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            if os.fstat(stream.fileno()).st_nlink != 1:
                raise ValueError('Output file alias detected')
            if not os.path.samestat(self.identity, self.path.stat()):
                raise ValueError('Output directory identity changed')
            stream.write(content.encode('utf-8') if isinstance(content, str) else content)
        return self.path / name


def write_reports(root, output, report):
    destination = ExclusiveOutput(root, output)
    destination.write('audit.json', json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    destination.write('audit.md', markdown(report))


def resolve(root, source, url, origin, base=None):
    """Resolve URL paths using HTML/CSS document semantics; never escape source root."""
    if not url or url.startswith('#'):
        return {'status': 'non-file', 'path': None}
    absolute = urljoin(base or origin.rstrip('/') + '/' + source, url)
    parts, site = urlsplit(absolute), urlsplit(origin)
    if parts.scheme not in ('http', 'https'):
        return {'status': 'embedded-or-unsupported', 'path': None}
    if (parts.hostname or '').lower() != (site.hostname or '').lower() or parts.port != site.port:
        return {'status': 'external-unverified', 'path': None}
    path = unquote(parts.path).lstrip('/')
    target = (root / path).resolve()
    if not target.is_relative_to(root.resolve()):
        return {'status': 'unsafe-path', 'path': path}
    # Preserve URL spelling: Windows resolve() may silently correct filename case.
    return {'status': 'exists' if target.is_file() else 'missing', 'path': posixpath.normpath(path)}


def srcset(value):
    """Parse common w/x srcsets, including commas in data URLs; reject bad descriptors."""
    result = []
    for match in re.finditer(r'(?:^|\s|,)(data:[^\s]+|[^\s,]+)\s*(\d+(?:\.\d+)?[wx])?\s*(?=,|$)', value):
        result.append((match[1].rstrip(','), match[2]))
    return result


def css_refs(text, source, start_line=1):
    # Preserve comment line counts; URL tokens are inventory, not a CSS cascade evaluator.
    text = re.sub(r'/\*.*?\*/', lambda m: '\n' * m[0].count('\n'), text, flags=re.S)
    for match in CSS_URL.finditer(text):
        url = next((s for s in match.groups() if s is not None), '').strip()
        if Path(urlsplit(url).path).suffix.lower() in EXTENSIONS or url.startswith('data:image/'):
            yield {'source': source, 'line': start_line + text[:match.start()].count('\n'),
                   'role': 'css-image', 'url': url, 'attrs': {}}


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.source, self.refs, self.images, self.errors = source, [], [], []
        self.capture = None
        self.buffer = ''
        self.base = None
        self.picture_depth = 0
        self.context = []
        self.title, self.h1 = '', ''

    def add(self, role, url, attrs=None, **extra):
        if url:
            self.refs.append({'source': self.source, 'line': self.getpos()[0], 'role': role,
                              'url': url, 'attrs': attrs or {}, **extra})

    def handle_starttag(self, tag, values):
        attrs = dict(values)
        hero_context = any('hero' in css_class for css_class in attrs.get('class', '').split()) or any(h for _, h in self.context)
        if tag == 'base' and self.base is None:
            self.base = attrs.get('href')
        if tag == 'picture':
            self.picture_depth += 1
        if tag == 'img':
            index = len(self.images)
            self.images.append({'source': self.source, 'line': self.getpos()[0], 'index': index,
                                'attrs': attrs, 'picture': bool(self.picture_depth), 'hero': hero_context})
            self.add('img', attrs.get('src'), attrs, index=index)
            for url, descriptor in srcset(attrs.get('srcset', '')):
                self.add('img-srcset', url, attrs, index=index, descriptor=descriptor)
        if tag == 'source' and self.picture_depth:
            self.add('picture-source', attrs.get('src'), attrs)
            for url, descriptor in srcset(attrs.get('srcset', '')):
                self.add('picture-srcset', url, attrs, descriptor=descriptor)
        if tag == 'meta' and (attrs.get('property') or attrs.get('name')) in ('og:image', 'og:image:url', 'og:image:secure_url', 'twitter:image'):
            self.add(attrs.get('property') or attrs.get('name'), attrs.get('content'), attrs)
        if tag == 'video':
            self.add('video-poster', attrs.get('poster'), attrs)
        if tag == 'link':
            rel = attrs.get('rel', '').lower().split()
            if 'preload' in rel and attrs.get('as') == 'image':
                self.add('preload', attrs.get('href'), attrs)
                for url, descriptor in srcset(attrs.get('imagesrcset', '')):
                    self.add('preload-srcset', url, attrs, descriptor=descriptor)
            if any('icon' in r for r in rel):
                self.add('icon', attrs.get('href'), attrs)
        if attrs.get('style'):
            self.refs.extend(css_refs(attrs['style'], self.source, self.getpos()[0]))
        self.add('interactive-preview', attrs.get('data-preview-image'), attrs)
        if tag in ('style', 'title', 'h1') or (tag == 'script' and attrs.get('type') == 'application/ld+json'):
            self.capture = tag
            self.buffer = ''
            self.capture_line = self.getpos()[0]
        if tag not in ('area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'):
            self.context.append((tag, hero_context))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_data(self, value):
        if self.capture:
            self.buffer += value

    def handle_endtag(self, tag):
        for index in range(len(self.context) - 1, -1, -1):
            if self.context[index][0] == tag:
                del self.context[index:]
                break
        if tag == 'picture':
            self.picture_depth = max(0, self.picture_depth - 1)
        if tag != self.capture:
            return
        if tag in ('title', 'h1'):
            setattr(self, tag, self.buffer.strip())
        if tag == 'style':
            self.refs.extend(css_refs(self.buffer, self.source, self.capture_line))
        if tag == 'script':
            try:
                self.schema(json.loads(self.buffer))
            except json.JSONDecodeError as error:
                self.errors.append({'source': self.source, 'line': self.capture_line, 'error': str(error)})
        self.capture = None

    def schema(self, node, image_context=False):
        if isinstance(node, str) and image_context:
            if not node.startswith('#') and not urlsplit(node).fragment:
                self.refs.append({'source': self.source, 'line': self.capture_line, 'role': 'jsonld-image', 'url': node, 'attrs': {}})
        elif isinstance(node, list):
            for value in node:
                self.schema(value, image_context)
        elif isinstance(node, dict):
            types = node.get('@type', [])
            is_image = types == 'ImageObject' or (isinstance(types, list) and 'ImageObject' in types)
            for key, value in node.items():
                if key in ('image', 'logo', 'thumbnailUrl') or (key in ('url', 'contentUrl') and (is_image or image_context)):
                    self.schema(value, True)
                elif isinstance(value, (dict, list)):
                    self.schema(value)


def metadata(path):
    data = {'bytes': path.stat().st_size, 'sha256': digest(path)}
    try:
        if path.suffix.lower() == '.svg':
            node = ET.fromstring(path.read_bytes())
            if node.tag.split('}')[-1] != 'svg':
                raise ValueError('Not an SVG document')
            box = [float(n) for n in node.get('viewBox', '').replace(',', ' ').split()]
            valid_box = len(box) == 4 and all(math.isfinite(n) for n in box) and box[2] > 0 and box[3] > 0
            def size(key, index):
                value = node.get(key, '')
                numeric = float(value.removesuffix('px')) if re.fullmatch(r'(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?(?:px)?', value) else None
                return numeric if numeric is not None and math.isfinite(numeric) and numeric > 0 else (box[index] if valid_box else None)
            data.update(format='SVG', width=size('width', 2), height=size('height', 3), alpha=True, frames=1)
            data['dimension_status'] = 'intrinsic-or-viewBox' if data['width'] and data['height'] else 'unknown'
            data['dimension_basis'] = 'SVG intrinsic dimensions/viewBox coordinates; not decoded raster pixels'
        else:
            with Image.open(path) as im:
                im.load()  # Decode pixels, do not trust extension or header only.
                upright = ImageOps.exif_transpose(im)
                data.update(format=im.format, width=upright.width, height=upright.height,
                            encoded_width=im.width, encoded_height=im.height, frames=getattr(im, 'n_frames', 1),
                            alpha='A' in im.getbands() or 'transparency' in im.info,
                            icc_profile=bool(im.info.get('icc_profile')))
                data['pixel_sha256'] = hashlib.sha256(str(upright.size).encode() + upright.convert('RGBA').tobytes()).hexdigest()
        data['status'] = 'valid'
    except (OSError, ValueError, ET.ParseError, Image.DecompressionBombError) as error:
        data.update(status='invalid', error=str(error))
    return data


def filename(subject):
    ascii_text = unicodedata.normalize('NFKD', subject).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', ascii_text).strip('-') or 'editorial-image'


def variants(original_width, rendered_widths, dprs=(1, 2)):
    """Select smallest sufficient bucket for each measured slot/DPR, cap at native width."""
    selected = set()
    for slot in rendered_widths:
        if not math.isfinite(slot) or slot <= 0:
            continue
        for dpr in dprs:
            needed = min(original_width, math.ceil(slot * dpr))
            selected.add(next((w for w in WIDTHS if w >= needed and w <= original_width), min(original_width, 1920)))
    return sorted(selected)


def finding(kind, source, line, evidence, severity='review', score=30, **extra):
    return dict(kind=kind, source=source, line=line, evidence=evidence, severity=severity, score=score, **extra)


def scan(root, page=None, origin='https://tripguidely.github.io', renders=None, traffic=None):
    root = root.resolve()
    all_files = list(files(root))
    html = [p for p in all_files if p.suffix.lower() in ('.html', '.htm')]
    if page:
        target = (root / page).resolve()
        if not target.is_relative_to(root) or not target.is_file() or target not in html:
            raise ValueError('Single page must be an existing HTML file inside the repository')
        html = [target]
    assets = {p.relative_to(root).as_posix(): metadata(p) for p in all_files if p.suffix.lower() in EXTENSIONS}
    refs, images, pages, errors = [], [], [], []
    for path in html:
        source = path.relative_to(root).as_posix()
        parsed = Page(source)
        parsed.feed(path.read_text(encoding='utf-8'))
        base = urljoin(origin.rstrip('/') + '/' + source, parsed.base) if parsed.base else None
        for ref in parsed.refs:
            ref.update(resolve(root, source, ref['url'], origin, base))
        refs.extend(parsed.refs)
        images.extend(parsed.images)
        errors.extend(parsed.errors)
        pages.append({'path': source, 'title': parsed.title, 'h1': parsed.h1, 'image_elements': len(parsed.images)})
    # CSS is a separate global inventory, not counted once for every linked page.
    if not page:
        for path in all_files:
            if path.suffix.lower() == '.css':
                source = path.relative_to(root).as_posix()
                for ref in css_refs(path.read_text(encoding='utf-8'), source):
                    ref.update(resolve(root, source, ref['url'], origin))
                    refs.append(ref)
    findings = []
    canonical_paths = {path.casefold(): path for path in assets}
    for ref in refs:
        if ref.get('path') and ref['path'] not in assets and ref['path'].casefold() in canonical_paths:
            ref['status'] = 'case-mismatch'
            findings.append(finding('case-mismatch', ref['source'], ref['line'], f"{ref['path']} differs from {canonical_paths[ref['path'].casefold()]}", 'error', 98, path=ref['path']))
        if ref['status'] in ('missing', 'unsafe-path'):
            visible = ref['role'] in ('img', 'picture-srcset', 'preload', 'preload-srcset')
            critical = visible and (('/hero/' in (ref['path'] or '')) or 'hero' in (ref['path'] or ''))
            # Structural hub/landing-page priority is a heuristic, not traffic data.
            hub = len(Path(ref['source']).parts) <= 2
            score = 100 + (20 if critical else 5 if visible else 0) + (5 if hub else 0)
            findings.append(finding('broken-reference', ref['source'], ref['line'], ref['url'], 'error', score, path=ref['path'], role=ref['role']))
        elif ref['status'] == 'exists' and (ref.get('descriptor') or '').endswith('w'):
            asset = assets.get(ref['path'], {})
            if asset.get('format') != 'SVG' and asset.get('width') and int(ref['descriptor'][:-1]) != asset['width']:
                findings.append(finding('srcset-width-mismatch', ref['source'], ref['line'], f"{ref['descriptor']} vs decoded {asset['width']}px", 'warning', 75, path=ref['path']))
    for path, asset in assets.items():
        if asset['status'] == 'invalid':
            findings.append(finding('invalid-image', path, 1, asset['error'], 'error', 95, path=path))
        elif asset.get('dimension_status') == 'unknown':
            findings.append(finding('unknown-image-dimensions', path, 1, 'Valid SVG; intrinsic dimensions cannot be established', path=path))
        if asset['bytes'] > 250_000:
            findings.append(finding('heavy-asset', path, 1, f"{asset['bytes']} bytes; policy threshold 250000, not proof of poor compression", 'review', 45, path=path))
        if asset.get('format') != 'SVG' and asset.get('width', 0) and asset['width'] > 1920:
            findings.append(finding('large-dimensions', path, 1, f"{asset['width']}x{asset['height']}; review actual slot/DPR before reducing", path=path))
        named = re.search(r'(\d{2,5})x(\d{2,5})(?:\.[^.]+)$', path)
        if named and asset.get('format') != 'SVG' and asset.get('width') and asset.get('height') and (int(named[1]), int(named[2])) != (asset['width'], asset['height']):
            findings.append(finding('filename-dimension-mismatch', path, 1, f"Name {named[1]}x{named[2]}, pixels {asset['width']}x{asset['height']}", 'warning', 65, path=path))
        expected = {'.jpg': 'JPEG', '.jpeg': 'JPEG', '.webp': 'WEBP', '.png': 'PNG', '.avif': 'AVIF', '.svg': 'SVG'}.get(Path(path).suffix.lower())
        if expected and asset.get('format') and expected != asset['format']:
            findings.append(finding('extension-format-mismatch', path, 1, f"Extension expects {expected}, decoded {asset['format']}", 'warning', 70, path=path))
        if asset.get('format') in ('PNG', 'JPEG') and asset['bytes'] > 100_000 and '/og/' not in path and asset.get('width', 0) > 640:
            findings.append(finding('modern-format-review', path, 1, 'Benchmark WebP/AVIF against the actual source; retain alpha and justified fallback', score=40, path=path))
    measurements = defaultdict(list)
    for run in (renders or []):
        # Old manifests may carry only actualUrl. Never trust an arbitrary loopback URL
        # in currentSrc itself as proof that it belongs to this sampler session.
        actual = urlsplit(run.get('actualUrl', ''))
        render_origin = run.get('origin') or (f'{actual.scheme}://{actual.netloc}' if actual.netloc else None)
        parsed_origin = urlsplit(render_origin or '')
        if parsed_origin.scheme not in ('http', 'https') or parsed_origin.hostname not in ('127.0.0.1', 'localhost', '::1'):
            render_origin = None
        for im in run.get('images', []):
            measurements[(run['page'], im['index'])].append({**im, 'viewport': run['viewport'], 'dpr': run.get('dpr', 1), 'render_origin': render_origin})
    plans = []
    for image in images:
        attrs, source, line = image['attrs'], image['source'], image['line']
        linked = next((r for r in refs if r['source'] == source and r.get('index') == image['index'] and r['role'] == 'img'), None)
        path = linked['path'] if linked else None
        asset = assets.get(path, {})
        hero = image['hero']
        if 'alt' not in attrs:
            findings.append(finding('missing-alt', source, line, attrs.get('src', 'no src'), 'warning', 55, path=path))
        elif attrs['alt'] and (len(attrs['alt']) > 180 or re.search(r'\.(?:jpg|png|webp)$', attrs['alt'], re.I)):
            findings.append(finding('alt-review', source, line, attrs['alt'], path=path))
        elif attrs.get('alt') == '' and attrs.get('role') not in ('presentation', 'none') and attrs.get('aria-hidden') != 'true':
            findings.append(finding('decorative-intent-review', source, line, 'Empty alt: confirm this image is decorative, not informative', path=path))
        if not (str(attrs.get('width', '')).isdigit() and str(attrs.get('height', '')).isdigit() and int(attrs['width']) > 0 and int(attrs['height']) > 0):
            findings.append(finding('dimension-reservation-review', source, line, 'Missing positive width/height; CSS may reserve space. CLS not established.', score=50, path=path))
        elif asset.get('width') and asset.get('height') and abs(int(attrs['width']) / int(attrs['height']) - asset['width'] / asset['height']) > 0.03:
            findings.append(finding('aspect-ratio-review', source, line, 'HTML ratio differs from decoded pixels; deliberate CSS crop may be valid', score=50, path=path))
        if hero and attrs.get('loading') == 'lazy':
            findings.append(finding('potential-lcp-lazy', source, line, 'Hero candidate lazy-loaded; confirm actual LCP element', 'warning', 80, path=path))
        if not attrs.get('srcset') and not image['picture'] and asset.get('format') != 'SVG' and (asset.get('width') or 0) > 640:
            findings.append(finding('responsive-opportunity', source, line, 'Large single raster source without picture/srcset', score=45, path=path))
        measured = measurements.get((source, image['index']), [])
        if measured:
            image['rendered'] = measured
        for measurement in measured:
            current = measurement.get('currentSrc', '')
            selected_asset = {}
            measurement['selected_source_status'] = 'unverified'
            if current:
                parts = urlsplit(current)
                for allowed in (origin, measurement['render_origin']):
                    if not allowed:
                        continue
                    site = urlsplit(allowed)
                    if (parts.scheme, parts.hostname, parts.port) == (site.scheme, site.hostname, site.port):
                        resolved = resolve(root, source, current, allowed)
                        if resolved['status'] == 'exists':
                            selected_asset = assets.get(resolved['path'], {})
                        break
                if parts.scheme in ('http', 'https') and not selected_asset:
                    measurement['selected_source_status'] = 'external-or-unmapped-unverified'
            verified = selected_asset.get('status') == 'valid' and selected_asset.get('format') != 'SVG'
            measurement['selected_pixel_width'] = selected_asset.get('width') if verified else None
            if verified:
                measurement['selected_source_status'] = 'local-decoded'
        slots = [m['width'] for m in measured if m['width'] > 0]
        if slots and asset.get('width') and asset.get('height') and asset.get('format') != 'SVG':
            plan = {'source': source, 'line': line, 'path': path, 'rendered': measured,
                    'widths': variants(asset['width'], slots), 'aspect_ratio': [asset['width'], asset['height']],
                    'formats': ['AVIF', 'WebP', 'PNG' if asset.get('alpha') else 'JPEG'],
                    'width': asset['width'], 'height': asset['height'], 'decoding': 'async',
                    'loading': 'eager' if hero else 'review: lazy only below fold',
                    'fetchpriority': 'high only if measured critical LCP; otherwise auto',
                    'sizes': 'derive from measured slots and CSS breakpoints; see rendered samples'}
            subject = filename(re.sub(r'-\d{2,5}(?:x\d{2,5})?$', '', Path(path).stem))
            plan['proposed_srcset'] = {fmt: ', '.join(f'{subject}-{width}w.{fmt} {width}w' for width in plan['widths']) for fmt in ('webp', 'avif')}
            plan['publication_status'] = 'Names and markup proposals only; files not installed or published'
            plans.append(plan)
            for m in measured:
                selected = m['selected_pixel_width'] if m.get('naturalWidth') else None
                if selected and selected > max(640, m['width'] * m['dpr'] * 1.6):
                    findings.append(finding('overdelivery-measured', source, line, f"viewport {m['viewport']}, slot {m['width']:.1f}px at DPR {m['dpr']}, selected decoded {selected}px", score=60, path=path))
                if selected and selected < m['width'] * m['dpr'] * 0.8:
                    findings.append(finding('underdelivery-measured', source, line, f"viewport {m['viewport']}, slot {m['width']:.1f}px at DPR {m['dpr']}, selected decoded {selected}px", score=60, path=path))
                if m.get('objectFit') == 'cover' and m.get('height', 0) > 0:
                    ratio = m['width'] / m['height'] / (asset['width'] / asset['height'])
                    retained = min(ratio, 1 / ratio)
                    if retained < 0.5:
                        findings.append(finding('cover-crop-review', source, line, f"viewport {m['viewport']}: roughly {retained:.0%} of source area retained by cover; inspect subject placement", score=40, path=path))
    hashes = defaultdict(list)
    pixels = defaultdict(list)
    for path, asset in assets.items():
        hashes[asset['sha256']].append(path)
        if asset.get('pixel_sha256'):
            pixels[asset['pixel_sha256']].append(path)
    duplicates = [paths for paths in hashes.values() if len(paths) > 1]
    pixel_duplicates = [paths for paths in pixels.values() if len(paths) > 1]
    traffic_by_page = defaultdict(lambda: {'web_impressions': 0, 'image_impressions': 0, 'clicks': 0})
    for row in (traffic or {}).get('rows', []):
        parts = urlsplit(row['page'])
        if parts.hostname != urlsplit(origin).hostname:
            continue
        route = unquote(parts.path).lstrip('/')
        source = route + 'index.html' if route.endswith('/') or not route else route
        key = row.get('search_type', 'web') + '_impressions'
        if key in ('web_impressions', 'image_impressions'):
            traffic_by_page[source][key] += row['impressions']
        traffic_by_page[source]['clicks'] += row['clicks']
    for item in findings:
        metrics = traffic_by_page.get(item['source'])
        if metrics:
            item['observed_traffic'] = dict(metrics)
            # Tie-break within defect severity, never a forecast of future gains.
            item['score'] += min(20, round(math.log1p(metrics['web_impressions'] + metrics['image_impressions']) * 2))
    findings.sort(key=lambda f: (-f['score'], f['source'], f['line'], f['kind']))
    # Group references to the same problem to avoid ten copies of one missing hero.
    grouped = {}
    for item in findings:
        family = re.sub(r'-\d{2,5}(?:x\d{2,5})?(?=\.[^.]+$)', '', item.get('path') or item['source'])
        key = (item['kind'], family)
        grouped.setdefault(key, {**item, 'occurrences': 0, 'pages': []})
        grouped[key]['occurrences'] += 1
        if item['source'] not in grouped[key]['pages']:
            grouped[key]['pages'].append(item['source'])
    return {'version': 1, 'mode': 'dry-run', 'root': str(root), 'origin': origin,
            'counts': {'html_files': len(html), 'documents': sum(bool(p['title']) for p in pages),
                       'image_elements': len(images), 'references': len(refs), 'image_files': len(assets),
                       'referenced_local_files': len({r['path'] for r in refs if r['status'] == 'exists'}),
                       'missing_paths': len({r['path'] for r in refs if r['status'] == 'missing'}),
                       'missing_references': sum(r['status'] == 'missing' for r in refs),
                       'external_references': sum(r['status'] == 'external-unverified' for r in refs),
                       'case_mismatches': sum(r['status'] == 'case-mismatch' for r in refs),
                       'heavy_assets': sum(a['bytes'] > 250_000 for a in assets.values()),
                       'missing_alt': sum(f['kind'] == 'missing-alt' for f in findings),
                       'duplicate_groups': len(duplicates), 'pixel_duplicate_groups': len(pixel_duplicates),
                       'responsive_opportunities': sum(f['kind'] == 'responsive-opportunity' for f in findings)},
            'pages': pages, 'assets': assets, 'references': refs, 'images': images, 'findings': findings,
            'priorities': list(grouped.values())[:10], 'duplicates': duplicates, 'pixel_duplicates': pixel_duplicates, 'dimension_plans': plans,
            'traffic_evidence': traffic, 'parse_errors': errors, 'limits': ['No licensing/provenance determination', 'No external URL validation',
            'Traffic evidence only if supplied; no conversion data or forecasts', 'No field LCP/CLS/INP measurements',
            'Visual relevance and empty-alt intent require human review', 'Shared CSS refs are global, not per-page usage',
            'Single-page mode inventories its markup and all assets; external stylesheet inventory requires full scan']}


def markdown(report):
    lines = ['# Image SEO dry-run audit', '', 'No production changes or publishing.', '', '## Counts', '']
    lines.extend(f'- {key}: {value}' for key, value in report['counts'].items())
    lines.extend(['', '## Top technical priorities', '', '| Kind | Location | Evidence | Occurrences |', '|---|---|---|---|'])
    for item in report['priorities']:
        cells = [item['kind'], f"{item['source']}:{item['line']}", item['evidence'], str(item['occurrences'])]
        lines.append('| ' + ' | '.join(str(s).replace('|', '\\|').replace('\n', ' ') for s in cells) + ' |')
    lines.extend(['', '## Limits', '', *('- ' + limit for limit in report['limits'])])
    return '\n'.join(lines) + '\n'


def brief(page, purpose, subject, width, height):
    if width <= 0 or height <= 0:
        raise ValueError('Brief dimensions must be positive')
    return {'target_page': page, 'purpose': purpose, 'subject': subject,
            'composition': 'Subject readable at mobile crop; leave safe space for overlay only if required by template',
            'travel_editorial_style': 'Clear, natural color; no fabricated factual details',
            'aspect_ratio': [width, height], 'output_dimensions': [width, height],
            'formats': ['AVIF', 'WebP', 'JPEG fallback; PNG if alpha needed'],
            'suggested_filename': filename(subject), 'alt_text': 'OWNER REVIEW: describe only the verified visible content in page context',
            'restrictions': ['Prefer licensed real photography for named hotels, landmarks and attractions',
            'Record source, rights, permitted derivatives and attribution before use',
            'Do not present AI hotel rooms/exteriors or attractions as documentary photography',
            'Label material illustrative imagery; no logos, invented facilities or misleading geography'],
            'status': 'brief only; human sourcing/generation and publication approval required'}


def optimize(root, source, output, widths, formats=('WEBP', 'AVIF'), quality=80):
    root = root.resolve()
    source = (root / source).resolve()
    if not source.is_relative_to(root) or not source.is_file():
        raise ValueError('Source image must be inside the repository')
    output = safe_output(root, output)
    if not widths or any(w <= 0 for w in widths) or not 1 <= quality <= 100:
        raise ValueError('Positive widths and quality 1..100 required')
    allowed = {'WEBP', 'AVIF', 'JPEG', 'PNG'}
    if not formats or any(f not in allowed for f in formats):
        raise ValueError('Unsupported output format')
    with Image.open(source) as raw:
        raw.load()
        if getattr(raw, 'n_frames', 1) != 1:
            raise ValueError('Animated/multiframe images require separate reviewed processing')
        image = ImageOps.exif_transpose(raw)
        alpha = 'A' in image.getbands() or 'transparency' in image.info
        if alpha and 'JPEG' in formats:
            raise ValueError('JPEG would discard transparency')
        if any(w > image.width for w in widths):
            raise ValueError('Upscaling is forbidden')
        if raw.mode == 'CMYK':
            raise ValueError('CMYK requires reviewed color management')
        subject = re.sub(r'-\d{2,5}(?:x\d{2,5})?$', '', source.stem)
        targets = [(w, fmt, output / f'{filename(subject)}-{w}w.{dict(WEBP="webp", AVIF="avif", JPEG="jpg", PNG="png")[fmt]}')
                   for w in sorted(set(widths)) for fmt in dict.fromkeys(formats)]
        destination = ExclusiveOutput(root, output)
        results = []
        for width, fmt, path in targets:
            height = max(1, round(image.height * width / image.width))
            resized = image.convert('RGBA' if alpha else 'RGB').resize((width, height), Image.Resampling.LANCZOS)
            options = {'icc_profile': raw.info['icc_profile']} if raw.info.get('icc_profile') else {}
            if fmt == 'PNG':
                options['optimize'] = True
            else:
                options['quality'] = quality
            if fmt == 'WEBP':
                options['method'] = 6
            # Encode to memory first; the encoder never receives a filesystem path.
            from io import BytesIO
            encoded = BytesIO()
            resized.save(encoded, fmt, **options)
            with Image.open(BytesIO(encoded.getvalue())) as decoded:
                decoded.load()
                if decoded.size != resized.size or decoded.format != fmt:
                    raise ValueError('Output dimension/format validation failed')
                if alpha and ('A' not in decoded.getbands() or decoded.getchannel('A').tobytes() != resized.getchannel('A').tobytes()):
                    raise ValueError('Output changed alpha channel; use lossless PNG/WebP alpha')
            destination.write(path.name, encoded.getvalue())
            with Image.open(path) as decoded:
                decoded.load()
                if decoded.size != resized.size or decoded.format != fmt:
                    raise ValueError('Output dimension/format validation failed')
                if alpha and ('A' not in decoded.getbands() or decoded.getchannel('A').tobytes() != resized.getchannel('A').tobytes()):
                    # AVIF can quantize alpha; reject changes rather than silently lose transparency.
                    raise ValueError('Output changed alpha channel; use lossless PNG/WebP alpha')
                diff = ImageChops.difference(decoded.convert('RGB'), resized.convert('RGB'))
                mse = sum(n * n for n in ImageStat.Stat(diff).rms) / 3
                psnr = 10 * math.log10(255 * 255 / mse) if mse else None
                accepted = mse == 0 or psnr >= 30
                results.append({'file': path.name, 'width': width, 'height': height, 'format': fmt,
                                'bytes': path.stat().st_size, 'source_bytes': source.stat().st_size,
                                'psnr_db': psnr, 'lossless_pixels': mse == 0, 'quality_gate_passed': accepted,
                                'status': 'human visual review required' if accepted else 'REJECT: quality below 30 dB',
                                'sha256': digest(path)})
        destination.write('optimization.json', json.dumps(results, indent=2) + '\n')
        tiles = ''.join(f'<figure><img src="{escape(r["file"], quote=True)}" width="{r["width"]}" height="{r["height"]}" alt="Optimization preview {escape(r["file"], quote=True)}"><figcaption>{escape(json.dumps(r))}</figcaption></figure>' for r in results)
        destination.write('preview.html', '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Disposable image previews</title><style>body{font:16px sans-serif;margin:24px}img{max-width:100%;height:auto}figcaption{overflow-wrap:anywhere}</style><h1>Unpublished previews — human review required</h1>' + tiles + '</html>')
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    commands = parser.add_subparsers(dest='command', required=True)
    audit = commands.add_parser('audit', help='Read-only full-site or single-page scan')
    audit.add_argument('--page')
    audit.add_argument('--origin', default='https://tripguidely.github.io')
    audit.add_argument('--render-manifest', type=Path)
    audit.add_argument('--traffic-manifest', type=Path, help='Optional exported real page/clicks/impressions/search_type rows with provenance')
    audit.add_argument('--output', type=Path, help='Optional report directory outside every repository')
    plan = commands.add_parser('brief', help='Produce an approval-ready brief, never an image')
    for arg in ('page', 'purpose', 'subject'):
        plan.add_argument('--' + arg, required=True)
    plan.add_argument('--width', type=int, required=True)
    plan.add_argument('--height', type=int, required=True)
    opt = commands.add_parser('optimize', help='Explicit disposable outputs; no source changes')
    opt.add_argument('--source', required=True)
    opt.add_argument('--output', type=Path, required=True)
    opt.add_argument('--widths', type=int, nargs='+', required=True)
    opt.add_argument('--formats', nargs='+', choices=('WEBP', 'AVIF', 'JPEG', 'PNG'), default=['WEBP', 'AVIF'])
    opt.add_argument('--quality', type=int, default=80)
    args = parser.parse_args()
    try:
        if args.command == 'audit':
            renders = json.loads(args.render_manifest.read_text(encoding='utf-8')) if args.render_manifest else []
            traffic = json.loads(args.traffic_manifest.read_text(encoding='utf-8')) if args.traffic_manifest else None
            report = scan(args.root, args.page, args.origin, renders, traffic)
            if args.output:
                write_reports(args.root, args.output, report)
                print(json.dumps(report['counts'], indent=2))
            else:
                print(json.dumps(report, indent=2, ensure_ascii=False))
        elif args.command == 'brief':
            print(json.dumps(brief(args.page, args.purpose, args.subject, args.width, args.height), indent=2))
        else:
            results = optimize(args.root, args.source, args.output, args.widths, args.formats, args.quality)
            print(json.dumps(results, indent=2))
            if any(not result['quality_gate_passed'] for result in results):
                return 1
        return 0
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as error:
        print('IMAGE AGENT ERROR: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
