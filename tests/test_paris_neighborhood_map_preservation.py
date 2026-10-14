"""Neighborhood map scope, geometry, affiliate and SEO preservation checks."""
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE="5f3c1d0db4ee88689352607e6adf4bc6b83407a5"
PAGE="hotels/paris/index.html"
CSS="assets/css/pages/paris-neighborhood-map.css"
JS="assets/js/paris-neighborhood-map.js"
FIXTURE="tests/fixtures/site-baseline.json"
ALLOWED={PAGE,CSS,JS,FIXTURE,"docs/paris-neighborhood-map.md","tests/test_paris_neighborhood_map.cjs","tests/test_paris_neighborhood_map_preservation.py"}
def git(*args,input=None):
 return subprocess.check_output(["git","-C",str(ROOT),*args],input=input)
def norm(b):return b.replace(b"\r\n",b"\n")
def run():
 checks=[]
 def check(name,value):
  assert value,name
  checks.append(name)
 check("requested branch contains the reviewed main base",git("branch","--show-current").decode().strip()=="feat/paris-neighborhood-mobile-ux" and subprocess.run(["git","-C",str(ROOT),"merge-base","--is-ancestor",BASE,"HEAD"],check=False).returncode==0)
 check("empty index",not git("diff","--cached","--name-only").strip())
 changed=set(git("diff","--name-only",BASE).decode().splitlines())|set(git("ls-files","--others","--exclude-standard").decode().splitlines())
 check("seven expected paths only",changed==ALLOWED)
 check("no deleted files",not git("diff","--name-only","--diff-filter=D",BASE).strip())
 before=git("show",BASE+":"+PAGE).decode()
 after=(ROOT/PAGE).read_text(encoding="utf-8")
 mapsection=lambda s:re.sub(r'      <!-- Neighborhood orientation only:[\s\S]*?      <!-- BEST AREAS -->',"      <!-- BEST AREAS -->",s,count=1)
 check("all HTML outside map section unchanged",norm(mapsection(before).encode())==norm(mapsection(after).encode()))
 anchors=lambda s:re.findall(r'<a\b[^>]*class="[^"]*js-aff[^>]*>[\s\S]*?</a>',s)
 check("ten complete affiliate anchors byte-identical including URLs, SubID, tracking and labels",anchors(before)==anchors(after) and len(anchors(after))==10)
 areas=lambda s:re.findall(r'<article class="tg-card tg-area-card"[\s\S]*?</article>',s)
 check("all ten source area cards and eleven PR40 routes exact",[norm(a.encode()) for a in areas(before)]==[norm(a.encode()) for a in areas(after)] and len(areas(after))==10)
 check("three editorial li per area card",all(len(re.findall(r"<li\b",a))==3 for a in areas(after)))
 metadata=lambda s:re.findall(r'<title>[\s\S]*?</title>|<meta\b[^>]*>|<link\b[^>]*(?:rel="canonical"|hreflang=")[^>]*>',s)
 check("all SEO metadata identical",metadata(before)==metadata(after))
 schema=lambda s:re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>[\s\S]*?</script>',s)
 check("all Schema identical",norm("".join(schema(before)).encode())==norm("".join(schema(after)).encode()))
 check("new visible external anchors none (attribution is created by Leaflet)",re.findall(r'<a\b[^>]*href="https?://[^"]+"[^>]*>',before)==re.findall(r'<a\b[^>]*href="https?://[^"]+"[^>]*>',after))
 old=json.loads(git("show",BASE+":"+FIXTURE));new=json.loads((ROOT/FIXTURE).read_text(encoding="utf-8"))
 check("baseline facts, exceptions and all previous authorizations unchanged",{k:v for k,v in old.items() if k!="authorizations"}=={k:v for k,v in new.items() if k!="authorizations"} and new["authorizations"][:-1]==old["authorizations"])
 records=new["authorizations"][-1:]
 markup='<script src="/'+JS+'" defer></script>'
 script_hash=hashlib.sha256(norm((ROOT/JS).read_bytes())).hexdigest()
 check("map controller included exactly once, Leaflet absent from initial markup",after.count(markup)==1 and "src=\"/assets/vendor/leaflet" not in after)
 check("one exact owner-requested controller hash authorization",[(r["kind"],r["source"],r["after"],r["before"],r["base_revision"]) for r in records]==[("integration_script",JS,script_hash,hashlib.sha256(norm(git("show",BASE+":"+JS))).hexdigest(),BASE)])
 entries=[]
 for row in git("ls-tree","-r","-z",BASE).split(b"\0"):
  if row:
   meta,name=row.split(b"\t",1);entries.append((name.decode(),meta.split()[2]))
 payload=git("cat-file","--batch",input=b"".join(oid+b"\n" for _,oid in entries))
 pos=0;verified=0
 for name,oid in entries:
  end=payload.index(b"\n",pos);size=int(payload[pos:end].split()[2]);pos=end+1
  b=payload[pos:pos+size];pos+=size+1
  if name in ALLOWED:continue
  current=(ROOT/name).read_bytes()
  text=Path(name).suffix in {".html",".css",".js",".mjs",".cjs",".py",".json",".md",".xml",".txt",".svg",".yml",".yaml"} or Path(name).name.startswith(".") or Path(name).name in {"LICENSE","NOTICE","CNAME"}
  assert (norm(current)==norm(b) if text else current==b),name
  verified+=1
 check("all other tracked files preserved including Disney, child guides, GA4/consent, images and Leaflet",verified>0)
 data=json.loads(re.search(r"var data = (\[[\s\S]*?\n\]);",(ROOT/JS).read_text(encoding="utf-8"))[1])
 expected=[("areas-first",48.863992,2.361532),("area-saint-germain",48.854148,2.333399),("area-latin",48.848614,2.342377),("area-first",48.863356,2.336069),("areas-family",48.85288,2.303337),("areas-romance",48.886518,2.340671),("areas-nightlife",48.853711,2.370213),("area-south-pigalle",48.879563,2.337431),("area-canal",48.873548,2.364072),("areas-budget",48.871044,2.332135)]
 check("ten reviewed IGN reference coordinates exact",[(z["id"],z["lat"],z["lon"]) for z in data]==expected)
 old_data=json.loads(re.search(r"var data = (\[[\s\S]*?\n\]);",git("show",BASE+":"+JS).decode())[1])
 for i,z in enumerate(old_data):
  if i in (0,6,7):z["profiles"].append("nightlife")
 check("all ten data records unchanged except Nightlife on original numbers 1,7,8",data==old_data)
 check("map runtime and loading contract exact",all(block in (ROOT/JS).read_text(encoding="utf-8") for block in ['loadAsset("link","/assets/vendor/leaflet-1.9.4/leaflet.css")','loadAsset("script","/assets/vendor/leaflet-1.9.4/leaflet.js")','{rootMargin:"250px 0px"}','scrollWheelZoom: false, minZoom: 11, maxZoom: 17','maxZoom: 17, updateWhenIdle: true, keepBuffer: 0, detectRetina: false']))
 check("no geocoder, geolocation or analytic handler added",all(s not in (ROOT/JS).read_text(encoding="utf-8") for s in ["navigator.geolocation","gtag(","affiliate_click","fetch("]))
 return {"passed":True,"checks":len(checks),"scenarios":checks,"other_tracked_files_verified":verified,"changed_paths":sorted(changed),"base_revision":BASE}
if __name__=="__main__":print(json.dumps(run(),indent=2))
