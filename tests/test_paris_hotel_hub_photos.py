"""Preservation audit for the seven-photo Paris hub; run with python -B tests/test_paris_hotel_hub_photos.py."""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
BASE = '2549de3c4aae381e4117e3e659639962bc6429a4'
PAGE = 'hotels/paris/index.html'
CSS = 'assets/css/pages/paris-hotel-hub-photos.css'
MANIFEST = 'docs/qa/paris-hotel-hub-photos-v1-images.json'


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args]).decode('utf-8')


class Tags(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.tags = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


def run():
    checks = []
    def check(condition, message):
        assert condition, message
        checks.append(message)

    check(subprocess.run(['git', '-C', str(ROOT), 'merge-base', '--is-ancestor', BASE, 'HEAD'], check=False).returncode == 0,
          'Approved base is an ancestor of the checkout')
    before = git('show', BASE + ':' + PAGE).replace('\r\n', '\n')
    after = (ROOT / PAGE).read_text(encoding='utf-8')
    css_markup = '  <link rel="stylesheet" href="/' + CSS + '" />\n'
    check(after.count(css_markup) == 1, 'One hub-only stylesheet')
    pattern = r'\n            <figure class="tg-hotel-photo">[\s\S]*?</figure>'
    figures = re.findall(pattern, after)
    check(len(figures) == 7, 'Seven photos')
    restored = re.sub(pattern, '', after).replace(css_markup, '', 1)
    note = '              <span>Opens in a new tab</span>\n'
    check(before.count(note) == 7, 'Exactly seven original visual new-tab notes')
    check('Opens in a new tab' not in after, 'No visual new-tab notes remain')
    check(restored == before.replace(note, ''), 'Whole HTML exact except seven photos, one stylesheet and seven approved visual note removals')
    for card in re.findall(r'<article class="tg-card tg-hotel-card"[\s\S]*?</article>', after):
        links = [a for t,a in Tags(card).tags if t == 'a' and 'js-aff' in a.get('class', '').split()]
        check(len(links) == 1, 'One unchanged affiliate CTA per card')
        link = links[0]
        check(link.get('target') == '_blank' and set(link.get('rel', '').split()) == {'nofollow', 'sponsored', 'noopener'}, 'New-tab target and security rel retained')
        check(link.get('aria-label', '').endswith('(opens in a new tab)') and link['aria-label'].startswith('Check availability on Klook'), 'Accessible CTA name and new-tab warning retained')
    anchors = lambda text: re.findall(r'<a\b[\s\S]*?</a>', text)
    check(anchors(before) == anchors(after), 'All 97 complete anchors, CTA labels and attributes exact')
    check(len(anchors(after)) == 97, '97 anchors independently counted')
    old_tags, new_tags = Tags(before).tags, Tags(after).tags
    klook = lambda tags: [a for t, a in tags if t == 'a' and urlsplit(a.get('href', '')).hostname == 'klook.tpk.ro']
    check(klook(old_tags) == klook(new_tags) and len(klook(new_tags)) == 10, 'All 10 Klook destinations and affiliate attributes exact')
    subids = lambda tags: [a['data-subid'] for t, a in tags if 'data-subid' in a]
    check(subids(old_tags) == subids(new_tags) and len(subids(new_tags)) == 7, 'All 7 SubID exact')
    tracking = lambda tags: [(t, {k:v for k,v in a.items() if k.startswith('data-')}) for t,a in tags if any(k.startswith('data-') for k in a)]
    check(tracking(old_tags) == tracking(new_tags), 'All data/tracking attributes exact')
    scripts = lambda text: re.findall(r'<script\b[\s\S]*?</script>', text)
    check(scripts(before) == scripts(after), 'All scripts and JSON-LD exact')
    for block in re.findall(r'<script type="application/ld\+json">([\s\S]*?)</script>', after):
        json.loads(block)
    check(True, 'JSON-LD parses')
    ids = [a['id'] for _, a in new_tags if 'id' in a]
    check(len(ids) == len(set(ids)), 'No duplicate HTML IDs')
    for _, attr in new_tags:
        href = attr.get('href', '')
        if href.startswith('#'):
            check(href[1:] in ids, 'Local fragment resolves: ' + href)
    cards = re.findall(r'<article class="tg-card tg-hotel-card"[\s\S]*?</article>', after)
    check(len(cards) == 7, 'Seven distinct hotel cards; neighborhood cards excluded')
    manifest = json.loads((ROOT / MANIFEST).read_text(encoding='utf-8'))
    check(manifest['base'] == BASE, 'Manifest records exact base')
    for row in manifest['images']:
        data = (ROOT / row['file']).read_bytes()
        sha = row['sha256'] if row['existing'] else row['variants'][row['selected']]['sha256']
        size = row['bytes'] if row['existing'] else row['variants'][row['selected']]['bytes']
        check(hashlib.sha256(data).hexdigest() == sha and len(data) == size, 'Exact image bytes: ' + row['file'])
        if row['existing']:
            blob = subprocess.check_output(['git', '-C', str(ROOT), 'show', BASE + ':' + row['file']])
            check(data == blob, 'Existing image unchanged: ' + row['hotel_id'])
        card = next(c for c in cards if 'aria-labelledby="' + row['hotel_id'] + '"' in c)
        imgs = [a for t,a in Tags(card).tags if t == 'img']
        check(len(imgs) == 1, 'One image in ' + row['hotel_id'])
        img = imgs[0]
        check(img['src'] == '/' + row['file'] and img['alt'] == row['alt'], 'Exact src and reviewed ALT: ' + row['hotel_id'])
        check([int(img['width']), int(img['height'])] == row['display_dimensions'], 'Intrinsic dimensions: ' + row['hotel_id'])
        check(img['loading'] == 'lazy' and img['decoding'] == 'async', 'Lazy async decoding: ' + row['hotel_id'])
        check('<figcaption' not in card, 'No caption: ' + row['hotel_id'])
        if not row['existing']:
            ow, oh = row['dimensions']; w, h = row['display_dimensions']
            check(w <= ow and h <= oh and w <= 1200 and abs(h - oh*w/ow) <= 1, 'No upscale; original ratio within pixel rounding: ' + row['hotel_id'])
            check(not git('ls-files', '--', row['original']).strip(), 'Original JPEG absent from versioned files: ' + row['hotel_id'])
    # Asset references must exist, including all existing srcset candidates.
    assets = []
    for tag, attrs in new_tags:
        for key in ('src', 'href'):
            value = attrs.get(key, '')
            if value.startswith('/assets/'):
                assets.append(value)
        for key in ('srcset', 'imagesrcset'):
            assets.extend(part.strip().split()[0] for part in attrs.get(key, '').split(',') if part.strip())
    check(all((ROOT / x.lstrip('/')).is_file() for x in assets), 'Every local image/script/stylesheet/srcset path exists')
    allowed = {PAGE, CSS, MANIFEST, 'docs/paris-hotel-hub-photos-v1.md',
               'tests/test_paris_hotel_hub_photos.py', 'tests/test_paris_hotel_hub_photos_browser.py'}
    allowed.update(row['file'] for row in manifest['images'] if not row['existing'])
    changed = set(git('diff', '--name-only', BASE).splitlines())
    check(changed <= allowed, 'Only the nine approved files change; all other pages, JS, consent, filters, Leaflet and SEO files preserved')
    check(not git('diff', '--name-only', '--diff-filter=D', BASE).strip(), 'No deleted versioned files')
    js = (ROOT / 'assets/js/paris-neighborhood-map.js').read_text(encoding='utf-8')
    zones = json.loads(re.search(r'var data = (\[[\s\S]*?\n\]);', js)[1])
    check(len(zones) == 10, '10 neighborhood records retained')
    check('855cd16e_z.jpg' not in after and '2aa91068_z.jpg' in (ROOT / MANIFEST).read_text(encoding='utf-8'), 'Final Madrigal source used')
    return {'passed': True, 'base': BASE, 'checks': len(checks), 'results': checks,
            'klook_before': klook(old_tags), 'klook_after': klook(new_tags),
            'subids_before': subids(old_tags), 'subids_after': subids(new_tags),
            'anchors_sha256': hashlib.sha256('\n'.join(anchors(after)).encode()).hexdigest(),
            'neighborhoods': zones}


if __name__ == '__main__':
    print(json.dumps(run(), ensure_ascii=True, indent=2))
