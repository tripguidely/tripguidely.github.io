"""New York content/attribution preservation. Standard library only; no network."""
import json
import hashlib
import re
import subprocess
import sys
import unittest
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = "ee86ecbd38f68bad7e5647d1451c2ca497a9d3b7"
GOLDEN = json.loads(r'''[{"category":"luxury","key":"plaza","url":"https://klook.tpk.ro/Db6zKcox","subid":"nyc_luxury_plaza","lat":40.7644602,"lon":-73.9744924,"image":"https://res.klook.com/klook-hotel/image/upload/w_1680,c_fill,q_85/travelapi/1000000/30000/28100/28044/288a78f6_z.webp"},{"category":"luxury","key":"langham","url":"https://klook.tpk.ro/5FZWWQAg","subid":"nyc_luxury_langham","lat":40.7501109,"lon":-73.9838132,"image":"https://i.travelapi.com/lodging/4000000/3630000/3630000/3629903/c21195be_z.jpg?impolicy=resizecrop&rw=1920&ra=fit"},{"category":"luxury","key":"conrad","url":"https://klook.tpk.ro/xDOjrZN1","subid":"nyc_luxury_conrad","lat":40.7149558,"lon":-74.015694,"image":"https://i.travelapi.com/lodging/1000000/430000/423500/423480/a018670a_z.jpg?impolicy=resizecrop&rw=1920&ra=fit"},{"category":"family","key":"homewood","url":"https://klook.tpk.ro/agdSdmLP","subid":"nyc_family_homewood","lat":40.7542669,"lon":-73.9930832,"image":"https://i.travelapi.com/lodging/7000000/6840000/6830200/6830159/479978d2_z.jpg?impolicy=resizecrop&rw=1920&ra=fit"},{"category":"family","key":"residence_central","url":"https://klook.tpk.ro/RyWmUW9H","subid":"nyc_family_residence_central","lat":40.7643419,"lon":-73.9826989,"image":"https://i.travelapi.com/lodging/7000000/6440000/6434900/6434849/9372fbf5_z.jpg?impolicy=resizecrop&rw=1920&ra=fit"},{"category":"family","key":"residence_times","url":"https://klook.tpk.ro/IBNZ3wsi","subid":"nyc_family_residence_times","lat":40.7528306,"lon":-73.9858447,"image":"https://i.travelapi.com/lodging/2000000/1310000/1301500/1301443/f04c448b_z.jpg?impolicy=resizecrop&rw=1920&ra=fit"},{"category":"cheap","key":"pod39","url":"https://klook.tpk.ro/ppL59r2m","subid":"nyc_cheap_pod39","lat":40.7494052,"lon":-73.976574,"image":"https://i.travelapi.com/lodging/6000000/5330000/5321600/5321579/4bcea295_z.jpg?impolicy=resizecrop&rw=1920&ra=fit"},{"category":"cheap","key":"pod_times","url":"https://klook.tpk.ro/8rtgpfkY","subid":"nyc_cheap_pod_times","lat":40.7584977,"lon":-73.9932281,"image":"https://i.travelapi.com/lodging/20000000/19690000/19681400/19681371/d9e98b9f_z.jpg?impolicy=resizecrop&rw=750&ra=fit"},{"category":"cheap","key":"citizenm","url":"https://klook.tpk.ro/o6d6V2Wi","subid":"nyc_cheap_citizenm","lat":40.7615806,"lon":-73.9849656,"image":"https://i.travelapi.com/lodging/9000000/8360000/8357000/8356903/a2079c0b_z.jpg?impolicy=resizecrop&rw=1920&ra=fit"}]''')
CATEGORIES = ("luxury", "family", "cheap")

# Exact original-reference bytes acquired privately on 2026-10-19; not public assets.
PHOTO_SOURCE_EVIDENCE = {
    "plaza": ("288a78f6", 1680, 1121, "29b40d2ef5ad50cd42923e45974e9717a8f40e5f9badba028dccb511551d3e13"),
    "langham": ("c21195be", 1920, 1281, "6eb95869afdf63aac56a10c63609d85cf5671843dcc450734c8caed155696f77"),
    "conrad": ("a018670a", 1920, 1280, "d56e0abee699ef072e52a567d6aeb61d0466f3a4709c6f1bd14b8e8fca0260df"),
    "homewood": ("479978d2", 1920, 1282, "d8ed387d8760571a090fb07bda8cb3be289a989568ea6554368a304793047de6"),
    "residence_central": ("9372fbf5", 1920, 1280, "5e122fdd751f9f0a7a789b3f1634cb68f07977e48b6e0f5453e90762f48af83d"),
    "residence_times": ("f04c448b", 1920, 1280, "bf94acfe3a4390406494cd1cea382ac3a1bc0fd820f4de499b1950a64cee019b"),
    "pod39": ("4bcea295", 1920, 1595, "7955e2ab4219c4a5e87d134b87e765ce849202cef6d4438599c1b7ee3ca08002"),
    "pod_times": ("d9e98b9f", 750, 808, "8aaeefe1f334e2546168630650dcd43206748b0e15fa98e1ee2ecc23fbc88f44"),
    "citizenm": ("a2079c0b", 1920, 1280, "14a41408ab4113b8e73126d5605910a2270615e5e00719a3444f0744116f10f6"),
}



# Exact hashes of the existing, owner-selected optimization outputs; no re-encoding.
SITE_PHOTO_EVIDENCE = json.loads(r'''{"plaza":[{"file":"assets/images/hotels/new-york/the-plaza-new-york-exterior-288a78f6-1680x1121.webp","format":"WEBP","width":1680,"height":1121,"bytes":237090,"sha256":"2930787879792ff95c6029976d807729876dd9d7e03e48e275d199e9743a208a"},{"file":"assets/images/hotels/new-york/the-plaza-new-york-exterior-288a78f6-1680x1121.avif","format":"AVIF","width":1680,"height":1121,"bytes":183054,"sha256":"1318496fc3e46418c7289d2dd3fe6fe551ccc669acb8941bf2e9fc6f2c040e0f"}],"langham":[{"file":"assets/images/hotels/new-york/the-langham-new-york-entrance-c21195be-640x427.webp","format":"WEBP","width":640,"height":427,"bytes":64718,"sha256":"25a4eac62da50ed280ce580b01ba00f1160b57d6c6475376b78f84f61c07f5a0"},{"file":"assets/images/hotels/new-york/the-langham-new-york-entrance-c21195be-640x427.avif","format":"AVIF","width":640,"height":427,"bytes":47735,"sha256":"fe0a649ede32a4dfbeaaf7b6522408e346296345fdd2ef9d33254efffd8924b6"},{"file":"assets/images/hotels/new-york/the-langham-new-york-entrance-c21195be-1280x854.webp","format":"WEBP","width":1280,"height":854,"bytes":190112,"sha256":"c47ac39389021a78994e065443fcf8a629a1b068dc0757937cc14b45576d8b59"},{"file":"assets/images/hotels/new-york/the-langham-new-york-entrance-c21195be-1280x854.avif","format":"AVIF","width":1280,"height":854,"bytes":142263,"sha256":"e9be8706028e312abecf1e76cffeb226488dc28dc03e7e5efe322eb9ab96fafc"}],"conrad":[{"file":"assets/images/hotels/new-york/conrad-new-york-downtown-exterior-a018670a-480x320.webp","format":"WEBP","width":480,"height":320,"bytes":49536,"sha256":"b53ba6f4220f0a04cbfff45279b7e5c1d6d63cdfae5cb664de208b685cd16f83"},{"file":"assets/images/hotels/new-york/conrad-new-york-downtown-exterior-a018670a-480x320.avif","format":"AVIF","width":480,"height":320,"bytes":36602,"sha256":"b5b2778ec8d3be833beb4142c9bd1f2f8ee9d5f7f4c392fea04b1c893f1817f4"},{"file":"assets/images/hotels/new-york/conrad-new-york-downtown-exterior-a018670a-960x640.webp","format":"WEBP","width":960,"height":640,"bytes":164996,"sha256":"8d5d62e597ee3ec22f15c8566d390b0e30035ff871fed342867bd1f31ec9213d"},{"file":"assets/images/hotels/new-york/conrad-new-york-downtown-exterior-a018670a-960x640.avif","format":"AVIF","width":960,"height":640,"bytes":123260,"sha256":"de9a6f7f1af79c27882f9bb9d5ec522cf101072995c39fc256deac9560204fac"}],"homewood":[{"file":"assets/images/hotels/new-york/homewood-suites-new-york-times-square-exterior-479978d2-960x641.webp","format":"WEBP","width":960,"height":641,"bytes":111278,"sha256":"1f6a58043efb29094d47671e11f797bb0e49742044bb9d4cf29c39c9b34717cd"},{"file":"assets/images/hotels/new-york/homewood-suites-new-york-times-square-exterior-479978d2-960x641.avif","format":"AVIF","width":960,"height":641,"bytes":83562,"sha256":"b6572c9028990367147e13da07bb87bfdeb40173dfe8a28c294d604f5d9e9109"}],"residence_central":[{"file":"assets/images/hotels/new-york/residence-inn-new-york-central-park-entrance-9372fbf5-480x320.webp","format":"WEBP","width":480,"height":320,"bytes":47500,"sha256":"d391e6301cc1cecc972320f531de849a9b5135b2e1f3ca77ac21deddf802283d"},{"file":"assets/images/hotels/new-york/residence-inn-new-york-central-park-entrance-9372fbf5-480x320.avif","format":"AVIF","width":480,"height":320,"bytes":33095,"sha256":"f5ab713244dedbd08d8f67226e4684b86d6a7b38cb09a4a6a12c27348bcdedd6"},{"file":"assets/images/hotels/new-york/residence-inn-new-york-central-park-entrance-9372fbf5-960x640.webp","format":"WEBP","width":960,"height":640,"bytes":135818,"sha256":"b83a06549a4beffd684c9a08be63c0fd1bb3d33fa228777a86e1498fc0da4162"},{"file":"assets/images/hotels/new-york/residence-inn-new-york-central-park-entrance-9372fbf5-960x640.avif","format":"AVIF","width":960,"height":640,"bytes":99628,"sha256":"eeab333e60351bea4ccc12cbcb0a294c73cb90c7374bb1354fa1e21dfb891ff3"}],"residence_times":[{"file":"assets/images/hotels/new-york/residence-inn-new-york-times-square-exterior-f04c448b-480x320.webp","format":"WEBP","width":480,"height":320,"bytes":52806,"sha256":"38dccebcccc8dd3ed59512405fa8b2db5f3f842d44e51aa0cdfb016792892307"},{"file":"assets/images/hotels/new-york/residence-inn-new-york-times-square-exterior-f04c448b-480x320.avif","format":"AVIF","width":480,"height":320,"bytes":36590,"sha256":"72a288fdc040499557e801421a885112397f779757d3c31fc7c0abe3693572d6"},{"file":"assets/images/hotels/new-york/residence-inn-new-york-times-square-exterior-f04c448b-960x640.webp","format":"WEBP","width":960,"height":640,"bytes":180178,"sha256":"09867a2b257f99b19deca7bb8066d83768f2f1f7f6cb8b8c4b68609a69cd970c"},{"file":"assets/images/hotels/new-york/residence-inn-new-york-times-square-exterior-f04c448b-960x640.avif","format":"AVIF","width":960,"height":640,"bytes":121069,"sha256":"41491ac59b4cac8eb4bdc125a6f3077abc4dd138a73d32089e0869ce9ecfd47e"}],"pod39":[{"file":"assets/images/hotels/new-york/pod-39-new-york-room-4bcea295-384x319.webp","format":"WEBP","width":384,"height":319,"bytes":15830,"sha256":"c1f8ca028f73474a7018326f7a5f5c493a31b6199b70d9f0945b57963968d356"},{"file":"assets/images/hotels/new-york/pod-39-new-york-room-4bcea295-384x319.avif","format":"AVIF","width":384,"height":319,"bytes":12066,"sha256":"c6e899574cc1ea18cf3091a2e205bcb5bf778dc183a94858ed4a0239a1aadc7b"},{"file":"assets/images/hotels/new-york/pod-39-new-york-room-4bcea295-768x638.webp","format":"WEBP","width":768,"height":638,"bytes":44920,"sha256":"8a7e5674827d4fee5f7f4abd6deeb35d93ec879f491a8751dbc8bd4fd4e12fce"},{"file":"assets/images/hotels/new-york/pod-39-new-york-room-4bcea295-768x638.avif","format":"AVIF","width":768,"height":638,"bytes":34902,"sha256":"f29dc6149376d24e1b03e3eb703de4c0805c1e29291f2b2d5477ff6c37485637"}],"pod_times":[{"file":"assets/images/hotels/new-york/pod-times-square-new-york-room-d9e98b9f-375x404.webp","format":"WEBP","width":375,"height":404,"bytes":18716,"sha256":"7ee31d2ff46557083584b06ff55b4e54e471ac3f94cac47131b73915c313b81a"},{"file":"assets/images/hotels/new-york/pod-times-square-new-york-room-d9e98b9f-375x404.avif","format":"AVIF","width":375,"height":404,"bytes":14219,"sha256":"12d5289ab7717c834086b9d86caaab282f567ae5e2b7cb057b7ab0b282475a31"},{"file":"assets/images/hotels/new-york/pod-times-square-new-york-room-d9e98b9f-750x808.webp","format":"WEBP","width":750,"height":808,"bytes":56800,"sha256":"60753bfbb6da191bc1f6749d241e9285b8269c056cf7b63a0b9107f58f92aae1"},{"file":"assets/images/hotels/new-york/pod-times-square-new-york-room-d9e98b9f-750x808.avif","format":"AVIF","width":750,"height":808,"bytes":45550,"sha256":"7d27e575dd97f649900ee8b25554a60c8fef74276a15c4a02327a2d3ad198e30"}],"citizenm":[{"file":"assets/images/hotels/new-york/citizenm-new-york-times-square-exterior-a2079c0b-480x320.webp","format":"WEBP","width":480,"height":320,"bytes":31406,"sha256":"2b808cee3754d45070e1598bc57fe18e49d0627a0f846954316e7ad528803d73"},{"file":"assets/images/hotels/new-york/citizenm-new-york-times-square-exterior-a2079c0b-480x320.avif","format":"AVIF","width":480,"height":320,"bytes":23176,"sha256":"1f64e761cf036e42cb4d561f3e9cd5154fb68641542218aacef2b63cd902b6cf"},{"file":"assets/images/hotels/new-york/citizenm-new-york-times-square-exterior-a2079c0b-960x640.webp","format":"WEBP","width":960,"height":640,"bytes":101832,"sha256":"46bf04beae550310e6e388bc3c61dd88b37600576c71d605fd60aaec3174bc57"},{"file":"assets/images/hotels/new-york/citizenm-new-york-times-square-exterior-a2079c0b-960x640.avif","format":"AVIF","width":960,"height":640,"bytes":69300,"sha256":"8f6c7ae80e1998e7ff08b5fd45582eb53001cd2c3d71dbe51bc669b4aa292a18"}]}''')


# Exact owner-approved entries; historic baseline content is still compared in full.
APPROVED_NEW_YORK_AUTHORIZATIONS = json.loads(r'''[{"kind":"new_integration_markup","source":"hotels/new-york/cheap-hotels/index.html","base_revision":"ee86ecbd38f68bad7e5647d1451c2ca497a9d3b7","before":null,"after":"181b9012d558bee407343891db0550a23853a4403e7a10dc671c0e0129898bea","reason":"Owner explicitly approved these exact New York hotel guides V1 integration hashes in APPROBATION FINALE AUDIT NEW YORK: three local lazy Leaflet map script inclusions and the new map controller. Nine photographs and current design validated; no authorization for any additional path, hash or later change.","reviewed_by":"owner instruction: TRIPGUIDELY — APPROBATION FINALE AUDIT NEW YORK (Codex conversation, 2026-10-19)","recorded_on":"2026-10-19"},{"kind":"new_integration_markup","source":"hotels/new-york/family-hotels/index.html","base_revision":"ee86ecbd38f68bad7e5647d1451c2ca497a9d3b7","before":null,"after":"181b9012d558bee407343891db0550a23853a4403e7a10dc671c0e0129898bea","reason":"Owner explicitly approved these exact New York hotel guides V1 integration hashes in APPROBATION FINALE AUDIT NEW YORK: three local lazy Leaflet map script inclusions and the new map controller. Nine photographs and current design validated; no authorization for any additional path, hash or later change.","reviewed_by":"owner instruction: TRIPGUIDELY — APPROBATION FINALE AUDIT NEW YORK (Codex conversation, 2026-10-19)","recorded_on":"2026-10-19"},{"kind":"new_integration_markup","source":"hotels/new-york/luxury-hotels/index.html","base_revision":"ee86ecbd38f68bad7e5647d1451c2ca497a9d3b7","before":null,"after":"181b9012d558bee407343891db0550a23853a4403e7a10dc671c0e0129898bea","reason":"Owner explicitly approved these exact New York hotel guides V1 integration hashes in APPROBATION FINALE AUDIT NEW YORK: three local lazy Leaflet map script inclusions and the new map controller. Nine photographs and current design validated; no authorization for any additional path, hash or later change.","reviewed_by":"owner instruction: TRIPGUIDELY — APPROBATION FINALE AUDIT NEW YORK (Codex conversation, 2026-10-19)","recorded_on":"2026-10-19"},{"kind":"new_integration_script","source":"assets/js/new-york-hotel-map.js","base_revision":"ee86ecbd38f68bad7e5647d1451c2ca497a9d3b7","before":null,"after":"aa671c34035b10f4ea027dddd6089c5a3db4504be99112cd0fad02132aebc33a","reason":"Owner explicitly approved these exact New York hotel guides V1 integration hashes in APPROBATION FINALE AUDIT NEW YORK: three local lazy Leaflet map script inclusions and the new map controller. Nine photographs and current design validated; no authorization for any additional path, hash or later change.","reviewed_by":"owner instruction: TRIPGUIDELY — APPROBATION FINALE AUDIT NEW YORK (Codex conversation, 2026-10-19)","recorded_on":"2026-10-19"}]''')

class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.tags = []
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))
    def find(self, tag, **attrs):
        return [a for t, a in self.tags if t == tag and all(a.get(k) == v for k, v in attrs.items())]

def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)

class NewYorkPreservation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads((ROOT / "docs/qa/new-york-hotels-sources.json").read_text(encoding="utf-8"))
        cls.texts = {c: (ROOT / f"hotels/new-york/{c}-hotels/index.html").read_text(encoding="utf-8") for c in CATEGORIES}
        cls.pages = {c: Page(t) for c, t in cls.texts.items()}

    def test_exact_nine_affiliate_mappings(self):
        self.assertEqual(len(self.registry["hotels"]), 9)
        for expected, actual in zip(GOLDEN, self.registry["hotels"]):
            with self.subTest(hotel=expected["key"]):
                self.assertEqual((actual["key"],actual["category"],actual["affiliate_url"],actual["subid"]), (expected["key"],expected["category"],expected["url"],expected["subid"]))
                anchors = [a for a in self.pages[expected["category"]].find("a") if a.get("data-offer-id") == expected["subid"]]
                self.assertEqual(len(anchors), 2)
                self.assertEqual({a["data-cta-location"] for a in anchors}, {"comparison", "hotel_card"})
                for a in anchors:
                    self.assertEqual(a["href"], expected["url"])
                    self.assertEqual(a["data-subid"], expected["subid"])
                    self.assertEqual(a["data-cta-id"], expected["subid"] + "_" + a["data-cta-location"])
                    self.assertEqual(a["rel"], "nofollow sponsored noopener")
                    self.assertEqual(a["target"], "_blank")
                    self.assertIn("opens in a new tab", a["aria-label"])

    def test_integrated_original_photos_and_exact_existing_variants(self):
        for expected, actual in zip(GOLDEN, self.registry["hotels"]):
            image = actual["image_reference"]
            self.assertEqual(image["url"], expected["image"])
            self.assertTrue(image["integrated"])
            self.assertTrue(image["downloaded"])
            source = actual["klook_photo_status"]["owner_reference_file"]
            self.assertEqual((source["asset_id"], source["width"], source["height"], source["sha256"]), PHOTO_SOURCE_EVIDENCE[expected["key"]])
            self.assertFalse(source["public_repository_copy"], "Original source stays outside Git")
            self.assertEqual(actual["site_photo"]["source_sha256"], source["sha256"])
            assets = SITE_PHOTO_EVIDENCE[expected["key"]]
            self.assertEqual(actual["site_photo"]["variants"], assets)
            self.assertFalse(actual["site_photo"]["published"])
            self.assertTrue(actual["site_photo"]["copied_existing_variants_without_reencoding"])
            for asset in assets:
                data = (ROOT / asset["file"]).read_bytes()
                self.assertEqual((len(data), hashlib.sha256(data).hexdigest()), (asset["bytes"], asset["sha256"]))
                self.assertEqual(asset["width"] * source["height"], asset["height"] * source["width"])
                self.assertLessEqual(asset["width"], source["width"])
                self.assertTrue(asset["file"].startswith("assets/images/hotels/new-york/"))
            page = self.pages[expected["category"]]
            webp = [a for a in assets if a["format"] == "WEBP"]
            avif = [a for a in assets if a["format"] == "AVIF"]
            img = page.find("img", src="/" + webp[0]["file"])[0]
            self.assertEqual((img["width"], img["height"]), (str(webp[0]["width"]), str(webp[0]["height"])))
            self.assertEqual((img["loading"], img["decoding"], img["fetchpriority"]), ("lazy", "async", "low"))
            self.assertGreater(len(img["alt"]), 35)
            self.assertEqual(img["alt"], actual["site_photo"]["alt"])
            self.assertEqual(img["srcset"], ", ".join("/" + a["file"] + " " + str(a["width"]) + "w" for a in webp))
            avif_set = ", ".join("/" + a["file"] + " " + str(a["width"]) + "w" for a in avif)
            self.assertEqual(len(page.find("source", type="image/avif", srcset=avif_set, sizes=img["sizes"])), 1)
            self.assertEqual(len(page.find("picture", **{"data-hotel-photo-id":source["asset_id"]})), 1)
            if expected["key"].startswith("pod"):
                self.assertEqual(image["reference_version"], "new-user-approved-reference")
            self.assertNotIn(expected["image"], self.texts[expected["category"]])
        for category, page in self.pages.items():
            self.assertEqual(len(page.find("figure", **{"class":"ny-photo-placeholder"})), 0)
            self.assertEqual(len(page.find("figure", **{"class":"ny-hotel-photo"})), 3)
            self.assertEqual(len(page.find("div", **{"class":"ny-photo-layout-reserve", "aria-hidden":"true"})), 3)
            self.assertNotIn("Property photograph not available", self.texts[category])
            hero = page.find("img", src="/assets/images/illustrations/new-york-hotel-guides.svg")[0]
            self.assertEqual((hero["loading"], hero["fetchpriority"]), ("eager", "high"))
            self.assertEqual(len(page.find("img")), 4)

    def test_geo_matches_registry_and_structured_data(self):
        for category, text in self.texts.items():
            graph = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>',text,re.S)[1])["@graph"]
            records = [x for x in graph if x["@type"] == "Hotel"]
            expected = [h for h in GOLDEN if h["category"] == category]
            self.assertEqual(len(records),3)
            for hotel, point in zip(records,expected):
                self.assertEqual((hotel["geo"]["latitude"],hotel["geo"]["longitude"]),(point["lat"],point["lon"]))
                card = self.pages[category].find("article", **{"data-offer-id":point["subid"]})[0]
                self.assertEqual((float(card["data-latitude"]),float(card["data-longitude"])),(point["lat"],point["lon"]))
                for key in ("aggregateRating","starRating","priceRange","offers","amenityFeature"):
                    self.assertNotIn(key,hotel)
        for hotel in self.registry["hotels"]:
            self.assertEqual((hotel["geo"]["latitude"],hotel["geo"]["longitude"]),(hotel["lat"],hotel["lon"]))
            self.assertEqual(len(hotel["sources"]),3 if hotel["key"] in ("residence_central","residence_times") else 2)
            self.assertTrue(all(s["url"].startswith("https://") and s["purpose"] and s["checked_on"] for s in hotel["sources"]))
            self.assertTrue(hotel["geo"]["source"].startswith("https://www.openstreetmap.org/"))

    def test_seo_and_accessible_static_fallback(self):
        titles, descriptions = [], []
        for category, text in self.texts.items():
            page = self.pages[category]
            canonical = "https://tripguidely.github.io/hotels/new-york/" + category + "-hotels/"
            self.assertEqual(len(re.findall(r"<h1\b",text)),1)
            self.assertEqual(len(re.findall(r"<title>",text)),1)
            titles.append(re.search(r"<title>(.*?)</title>",text)[1])
            descriptions.append(page.find("meta",name="description")[0]["content"])
            self.assertEqual(page.find("link",rel="canonical"),[{"rel":"canonical","href":canonical}])
            self.assertEqual(page.find("meta",**{"property":"og:url"})[0]["content"],canonical)
            ids=[attrs["id"] for _,attrs in page.tags if "id" in attrs]
            self.assertEqual(len(ids),len(set(ids)))
            self.assertEqual(page.find("a",**{"class":"skip-link"})[0]["href"],"#content")
            self.assertIn("<noscript>",text)
            self.assertTrue(all("hidden" in a for a in page.find("button",**{"class":"ny-show-map"})))
            self.assertEqual(len(page.find("script",src="/assets/js/site.js")),1)
            self.assertEqual(len(page.find("script",src="/assets/js/new-york-hotel-map.js")),1)
            self.assertEqual(len(page.find("a",**{"data-aff":"klook"})),6)
            self.assertNotRegex(text,r"(?:\$|€)\s*\d|AggregateRating|ratingValue|lowPrice|highPrice|availability\s*:")
            self.assertNotIn("tp-em.com",text)
        self.assertEqual(len(set(titles)),3)
        self.assertEqual(len(set(descriptions)),3)


    def test_comparison_instructions_and_local_landmarks(self):
        for category,page in self.pages.items():
            region=page.find("div", **{"class":"tg-hotel-table-region"})[0]
            self.assertEqual(region["aria-describedby"],"comparison-help")
            self.assertEqual(region["tabindex"],"0")
            self.assertEqual(len(page.find("p", id="comparison-help")),1)
            self.assertIn("swipe inside the table",self.texts[category])
            self.assertIn("left and right arrow keys",self.texts[category])
            self.assertEqual(len(page.find("aside", **{"class":"ny-location-aside"})),0)
            self.assertEqual(len(page.find("nav", **{"class":"ny-location-aside","aria-label":"Plan the wider trip"})),1)

    def test_family_category_evidence_is_specific_and_official(self):
        # These are independently pinned expected facts, not generic booking-form limits.
        expected={
            "residence_central":("Doubles Partial Park View","STDD",4),
            "residence_times":("Double Studio Suite","DDST",4),
        }
        family=self.texts["family"]
        for key,(name,code,maximum) in expected.items():
            hotel=next(h for h in self.registry["hotels"] if h["key"]==key)
            evidence=hotel["room_evidence"]
            self.assertEqual((evidence["title"],evidence["room_code"],evidence["max_occupancy"]),(name,code,maximum))
            self.assertEqual(evidence["beds"],"Two double beds")
            self.assertEqual(evidence["status"],"verified_official_category")
            self.assertEqual(evidence["kitchen"],["refrigerator","microwave","dishwasher"])
            self.assertTrue(evidence["source"].startswith("https://www.marriott.com/en-us/hotels/"))
            self.assertTrue(evidence["source"].endswith("/rooms/"))
            # Official provenance stays in the registry; the guide no longer links to hotel booking sites.
            self.assertIn(evidence["source"], [source["url"] for source in hotel["sources"]])
            self.assertNotIn(evidence["source"], [anchor.get("href") for anchor in self.pages["family"].find("a")])
            self.assertIn(name,family)
            self.assertIn("maximum occupancy of four guests",family)
        homewood=next(h for h in self.registry["hotels"] if h["key"]=="homewood")["room_evidence"]
        self.assertEqual(homewood["status"],"category_capacity_unconfirmed")
        self.assertNotIn("max_occupancy",homewood)
        self.assertTrue(homewood["source"].startswith("https://www.hilton.com/"))
        self.assertIn("Room capacity remains to be confirmed.",family)
        self.assertIn("connecting rooms and cribs",family)
        self.assertNotIn("maximum occupancy of eight",family)
        self.assertEqual(len(self.pages["family"].find("div", **{"class":"ny-room-example"})),3)

    def test_explicit_guide_identity_partner_labels_and_verified_details(self):
        expected = {
            "plaza": ("Deluxe 2 Queens", "Terrace Room 1 King"),
            "langham": ("Superior Room", "Deluxe City View with Kitchen", "two guests"),
            "conrad": ("separate sleeping and living areas", "ATRIO", "Leonessa"),
            "pod39": ("Single Pod sleeps one", "private bathrooms", "twin beds arranged vertically"),
            "pod_times": ("Full, Bunk and Queen Pods list two guests", "Pod Pad", "not be assumed"),
            "citizenm": ("two adults", "XL king bed", "blackout blinds"),
        }
        for category, text in self.texts.items():
            heading = re.search(r'<h1[^>]*>(.*?)</h1>', text, re.S)[1].replace("<br>", " ")
            self.assertIn(category.capitalize() + " hotels", heading)
            self.assertIn("New York", heading)
            self.assertEqual(text.count("<dt>Room format</dt>"), 3)
            for anchor in re.findall(r'<a\b[^>]*class="[^"]*js-aff[^>]*>(.*?)</a>', text, re.S):
                self.assertIn("Check availability on Klook", anchor)
        for key, facts in expected.items():
            hotel = next(h for h in self.registry["hotels"] if h["key"] == key)
            detail = hotel["published_detail"]
            self.assertEqual(detail["status"], "verified_official_property_text")
            self.assertIs(detail["not_a_live_offer"], True)
            self.assertTrue(detail["source"].startswith(("https://www.fairmont.com/", "https://www.langhamhotels.com/", "https://www.hilton.com/", "https://www.thepodhotel.com/", "https://www.marriott.com/")))
            for fact in facts:
                self.assertIn(fact, detail["text"])
                self.assertIn(fact, self.texts[hotel["category"]])
        for hotel in self.registry["hotels"]:
            plan = hotel["photo_publication_plan"]
            self.assertEqual(plan["decision"], "integrated_locally_on_explicit_owner_instruction")

    def test_hub_five_links_and_nine_destinations_unchanged(self):
        rel="hotels/new-york/index.html"
        content=(ROOT/rel).read_bytes()
        self.assertEqual(content.replace(b"\r\n", b"\n"),git("show",BASE+":"+rel).replace(b"\r\n", b"\n"))
        page=Page(content.decode())
        links=[a for a in page.find("a") if "klook.tpk.ro" in a.get("href","")]
        self.assertEqual(len(links),5)
        self.assertEqual({a["href"] for a in links},{"https://klook.tpk.ro/"+s for s in ("xCnQd8kp","IvUOCdN9","4Lp9yahU","MPOV73jx","PXCXZ1h8")})
        for c in CATEGORIES:
            self.assertEqual(len(page.find("a",href=f"/hotels/new-york/{c}-hotels/")),3)
            self.assertTrue((ROOT/f"hotels/new-york/{c}-hotels/index.html").is_file())

    def test_existing_tracked_files_preserved(self):
        changed=git("diff","--name-only",BASE).decode().splitlines()
        # Normalize only Git checkout line endings in text; preserve binary asset bytes exactly.
        paths=git("ls-tree","-r","--name-only",BASE).decode().splitlines()
        self.assertEqual(set(changed) & set(paths),{"sitemap-new-york.xml","tests/fixtures/site-baseline.json"})
        untracked=set(git("ls-files","--others","--exclude-standard").decode().splitlines())
        additions=(set(changed)-set(paths)) | untracked
        allowed_new=set(json.loads(r'''["assets/css/pages/new-york-hotels.css","assets/images/illustrations/new-york-hotel-guides.svg","assets/images/og/new-york-hotel-guides-illustration.png","assets/js/new-york-hotel-map.js","docs/new-york-hotel-guides-v1.md","docs/qa/new-york-hotels-pending-authorizations.json","docs/qa/new-york-hotels-sources.json","hotels/new-york/cheap-hotels/index.html","hotels/new-york/family-hotels/index.html","hotels/new-york/luxury-hotels/index.html","tests/test_new_york_hotel_maps.cjs","tests/test_new_york_hotels_preservation.py"]'''))
        allowed_new.update(a["file"] for assets in SITE_PHOTO_EVIDENCE.values() for a in assets)
        self.assertEqual(additions,allowed_new,"Only the original twelve additions and 32 exact owner-selected photo variants are permitted")
        protected=[p for p in paths if p=="assets/js/site.js" or any(s in p.lower() for s in ("paris","disney","universal"))]
        for rel in protected:
            actual, original = (ROOT/rel).read_bytes(), git("show",BASE+":"+rel)
            if Path(rel).name == ".gitkeep" or Path(rel).suffix in (".html", ".css", ".js", ".cjs", ".py", ".yml", ".yaml", ".json", ".xml", ".md", ".svg", ".txt"):
                actual, original = actual.replace(b"\r\n", b"\n"), original.replace(b"\r\n", b"\n")
            self.assertEqual(actual,original,rel)

    def test_sitemap_only_three_new_canonicals(self):
        rel="sitemap-new-york.xml"
        old=ET.fromstring(git("show",BASE+":"+rel))
        new=ET.parse(ROOT/rel).getroot()
        ns={"s":"http://www.sitemaps.org/schemas/sitemap/0.9"}
        before=[e.text for e in old.findall("s:url/s:loc",ns)]
        after=[e.text for e in new.findall("s:url/s:loc",ns)]
        self.assertEqual(after[:len(before)],before)
        self.assertEqual(set(after)-set(before),{"https://tripguidely.github.io/hotels/new-york/"+c+"-hotels/" for c in CATEGORIES})
        self.assertEqual(len(after),len(set(after)))

    def test_baseline_only_approved_authorizations_and_resolved_exceptions(self):
        rel="tests/fixtures/site-baseline.json"
        before=json.loads(git("show",BASE+":"+rel))
        after=json.loads((ROOT/rel).read_text(encoding="utf-8"))
        retired=[e for e in before["exceptions"] if e["category"]=="missing_internal_page" and e["source"]=="hotels/new-york/index.html" and re.fullmatch(r"/hotels/new-york/(luxury|family|cheap)-hotels/",e["target"])]
        self.assertEqual(len(retired),9)
        expected=dict(before)
        expected["exceptions"]=[e for e in before["exceptions"] if e not in retired]
        expected["authorizations"] = before["authorizations"] + APPROVED_NEW_YORK_AUTHORIZATIONS
        self.assertEqual(after,expected,"Only the four exact owner-approved entries and nine previously repaired exceptions may differ; historic records, inventory and auditor policy remain exact")

if __name__ == "__main__":
    unittest.main()
