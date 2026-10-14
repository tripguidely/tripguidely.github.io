"""Exact preservation checks for the approved Paris hotel photo integration.

python -B tests/test_paris_hotel_photos_preservation.py BASE_REF [OUTPUT_JSON]
The older Cheap/Luxury project-stage checks keep their original contracts.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
APPROVED_BASE = "04f83bc14e02150387d0f2b7b8e3a1351a69fcac"
PHOTO_CSS = '<link rel="stylesheet" href="/assets/css/pages/paris-hotel-photos.css" />\n'
REVIEW = json.loads(r'''{
  "pages": {
    "family": {
      "path": "hotels/paris/family-hotels/index.html",
      "figures": [
        {
          "sha256": "a51523cb90851da40388076ff3beb131560fa2fb5eefe4aa9061c4b4834f0cd8",
          "article": "hotel-citadines-halles"
        },
        {
          "sha256": "eb21386917c8659ceb1403c024889d37b9eee3df19cc865f72854d3a3a2ed0fb",
          "article": "hotel-pullman-montparnasse"
        },
        {
          "sha256": "a7b53eccf5e5be107cf576fd3df966a13ff77158a8af08be8943bd5565eb72d2",
          "article": "hotel-regence-etoile"
        },
        {
          "sha256": "b149d6b5fac086a30217e53bffd1bde50eb3cc32351a9274bc6ea64ca6a19d00",
          "article": "hotel-bb-batignolles"
        }
      ]
    },
    "cheap": {
      "path": "hotels/paris/cheap-hotels/index.html",
      "figures": [
        {
          "sha256": "7c2d234c9fa5d7a8cbf542ca0a623396458a4ea35b0c89fad44d9af32d9389d6",
          "article": "hotel-ibis-cambronne"
        },
        {
          "sha256": "b149d6b5fac086a30217e53bffd1bde50eb3cc32351a9274bc6ea64ca6a19d00",
          "article": "hotel-bb-batignolles"
        },
        {
          "sha256": "7092cca455335d2f1773d2623dbd256d42465d9c2668419115ddad5978669630",
          "article": "hotel-generator"
        }
      ]
    },
    "luxury": {
      "path": "hotels/paris/luxury-hotels/index.html",
      "figures": [
        {
          "sha256": "3e08d99e45724200607fbe589d6a257a6b1f9461ab08b1421f84bacd61056b99",
          "article": "hotel-le-meurice"
        },
        {
          "sha256": "baf2cb6e9ac15ba13f8fc9c878df5f8d33533b83311546e1625bf6a9bbe2f51d",
          "article": "hotel-lutetia"
        },
        {
          "sha256": "aa9494df935d9718d8ce41c72401b0ebf5fd9420895cc28e7ea91ecb5ea795ee",
          "article": "hotel-shangrila"
        },
        {
          "sha256": "2032265757a76b48bf02573458120a04708f50973a94e061eb68e834a4d8c34d",
          "article": "hotel-pullman-eiffel"
        }
      ]
    }
  },
  "assets": [
    {
      "path": "assets/images/hotels/paris/citadines-les-halles-paris-chambre-coin-repas.avif",
      "sha256": "afcd769ccdd2f693b7b65ffa1ba2be9297075e454c2c017a2d6287ce4073f349",
      "bytes": 57663
    },
    {
      "path": "assets/images/hotels/paris/pullman-paris-montparnasse-facade.avif",
      "sha256": "a761373c17b4580b2169f4a0c08703f76c4172c33e2824d43efc50389a926e9e",
      "bytes": 161253
    },
    {
      "path": "assets/images/hotels/paris/hotel-regence-etoile-paris-entree-facade.avif",
      "sha256": "adbce70e9ab03d63a07b3b120bcc1f17f9cad07617983f0c1cd8257125620944",
      "bytes": 103624
    },
    {
      "path": "assets/images/hotels/paris/bb-hotel-paris-17-batignolles-facade.avif",
      "sha256": "e14c89953147235b24e0d2512d61297d439be2a03186fab500b8a72866019b1d",
      "bytes": 90978
    },
    {
      "path": "assets/images/hotels/paris/ibis-paris-tour-eiffel-cambronne-15eme-entree.webp",
      "sha256": "df207a158a9e57aa82408e2c1658e4e3374ee5a9ad1923222cd57db2d2452c7b",
      "bytes": 155676
    },
    {
      "path": "assets/images/hotels/paris/generator-paris-hostel-facade.webp",
      "sha256": "c507bb7dd1049ed2db09dcd37d832b6b7704797c254c99cce4470f17277103b4",
      "bytes": 327138
    },
    {
      "path": "assets/images/hotels/paris/le-meurice-paris-exterior-garden-view.webp",
      "sha256": "c83686f95e985bef1ffc45cb2e0d90ff3b07a53d740180d398642dc4ce1ca041",
      "bytes": 163952
    },
    {
      "path": "assets/images/hotels/paris/mandarin-oriental-lutetia-paris-facade.avif",
      "sha256": "7078842f2d4beeffe76868d163d6559e51e31a393256e0537bfc2656fa315f75",
      "bytes": 152611
    },
    {
      "path": "assets/images/hotels/paris/shangri-la-paris-hotel-entrance.webp",
      "sha256": "b0c20e37fe881aa27b8bcc7082dbd0d74c71933ef043a5aa54e266a9e00f9c60",
      "bytes": 166790
    },
    {
      "path": "assets/images/hotels/paris/pullman-paris-tour-eiffel-facade.avif",
      "sha256": "45a3b295d146416eb6a612275253acc94700e04bb17e00f66e1bc81e7fdd41d3",
      "bytes": 94735
    }
  ],
  "cssSha256": "da9ce8bede547c8f1357c003f3f9f09962ea9049f6aac4e147ad1fd38058f617"
}''')


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def normalized(data):
    return data.replace(b"\r\n", b"\n")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def head(value):
    matches = re.findall(r"(?m)^<head>\n([\s\S]*?)^</head>$", value)
    assert len(matches) == 1, "One complete head element"
    return matches[0]


def check_page(name, before, after):
    """Allow only the reviewed stylesheet and exact, correctly placed figures."""
    checks = []

    def check(condition, label):
        assert condition, name + ": " + label
        checks.append(name + ": " + label)

    check(PHOTO_CSS not in before, "photo CSS absent from approved base")
    check(head(after).count(PHOTO_CSS) == 1 and after.count(PHOTO_CSS) == 1,
          "exactly one reviewed stylesheet in head")
    check(head(after).replace(PHOTO_CSS, "", 1) == head(before),
          "entire head exact except the one reviewed photo stylesheet")
    scripts = lambda s: re.findall(r'<script\b[\s\S]*?</script>', s)
    check(scripts(before) == scripts(after), "all scripts, Schema and consent markup exact")
    for schema in re.findall(r'<script type="application/ld\+json">([\s\S]*?)</script>', after):
        json.loads(schema)
    checks.append(name + ": JSON-LD valid")
    anchors = lambda s: re.findall(r'<a\b[\s\S]*?</a>', s)
    check(anchors(before) == anchors(after), "all anchors, Klook URLs/SubID and tracking exact")
    figures = list(re.finditer(r'\n<figure class="tg-hotel-photo">[\s\S]*?</figure>\n', after))
    review = REVIEW["pages"][name]["figures"]
    check(len(figures) == len(review) and after.count('<figure class="tg-hotel-photo">') == len(review),
          "exact reviewed photo count")
    restored = after.replace(PHOTO_CSS, "", 1)
    for figure, expected in zip(figures, review):
        markup = figure[0]
        check(digest(markup.encode()) == expected["sha256"],
              "exact approved src/ALT/dimensions/loading/caption: " + expected["article"])
        prefix = after[:figure.start()]
        article = prefix[prefix.rfind("<article"):]
        check(re.fullmatch(r'<article class="tg-card tg-hotel-card" aria-labelledby="' +
                           re.escape(expected["article"]) + r'">', article) is not None,
              "photo at exact opening of approved hotel article: " + expected["article"])
        check(restored.count(markup) == 1, "one exact figure occurrence: " + expected["article"])
        restored = restored.replace(markup, "", 1)
    check(restored == before, "whole page exact after removing only reviewed additions")
    return checks


def run(base_ref):
    resolved = git("rev-parse", base_ref + "^{commit}").decode().strip()
    assert resolved == APPROVED_BASE, "Use the exact reviewed photo-integration base"
    checks = []
    for name, review in REVIEW["pages"].items():
        before = normalized(git("show", resolved + ":" + review["path"])).decode()
        after = normalized((ROOT / review["path"]).read_bytes()).decode()
        checks.extend(check_page(name, before, after))
    for asset in REVIEW["assets"]:
        data = (ROOT / asset["path"]).read_bytes()
        assert digest(data) == asset["sha256"] and len(data) == asset["bytes"], asset["path"]
        checks.append("Exact approved photo bytes: " + asset["path"])
    photo_dir = ROOT / "assets/images/hotels/paris"
    actual = {p.relative_to(ROOT).as_posix() for p in photo_dir.rglob("*") if p.is_file()}
    assert actual == {a["path"] for a in REVIEW["assets"]}, "Exactly ten selected files, no variants"
    checks.append("10 exact files / 11 reviewed placements / one shared B&B URL")
    css = normalized((ROOT / "assets/css/pages/paris-hotel-photos.css").read_bytes())
    assert digest(css) == REVIEW["cssSha256"], "Approved photo CSS exact"
    checks.append("Photo design CSS exact")
    protected = git("ls-tree", "-r", "--name-only", resolved, "assets/js", "assets/css", "partials",
                    "tests/fixtures", "robots.txt", "sitemap.xml", "sitemap-paris.xml").decode().splitlines()
    for item in protected:
        assert normalized((ROOT / item).read_bytes()) == normalized(git("show", resolved + ":" + item)), item
    checks.append("All existing JS, consent/partials, CSS, baseline fixtures and SEO routing exact")
    return {"passed": True, "base": resolved, "checks": len(checks), "results": checks}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_ref")
    parser.add_argument("output", nargs="?", type=Path)
    args = parser.parse_args(argv)
    report = run(args.base_ref)
    if args.output:
        output = args.output.resolve()
        assert output != ROOT and ROOT not in output.parents, "QA report outside worktree"
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
