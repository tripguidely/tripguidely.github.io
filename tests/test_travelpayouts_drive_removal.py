"""Exact preservation and owner-approved authorization checks for Drive removal.
Run: python -B tests/test_travelpayouts_drive_removal.py
This suite never writes the baseline or a production file.
"""
import collections,hashlib,importlib.util,io,json,re,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='ee86ecbd38f68bad7e5647d1451c2ca497a9d3b7'
URL='https://tp-em.com/NDkyNzI0.js?t=492724'
PAT=re.compile(rb'<script\b(?=[^>]*\bsrc\s*=\s*["\x27]https://tp-em\.com/NDkyNzI0\.js\?t=492724["\x27])[^>]*>\s*</script>',re.I)
INVENTORY='docs/qa/travelpayouts-drive-removal-inventory.json'
DRAFT='docs/qa/travelpayouts-drive-removal-pending-authorizations.json'
REPORT='docs/travelpayouts-drive-removal.md'
EXTRA={INVENTORY,DRAFT,REPORT,'tests/test_travelpayouts_drive_removal.py','tests/test_paris_drive_initial_load.cjs'}
ADAPTED='tests/test_paris_family_affiliate_tracking.cjs'
APPROVED_DRAFT_SHA='8fd59853dace013f8af0be28a5bf263c2144829024c09f46ae37404275e00bb1'
REVIEW='Requesting project owner; explicit approval in this conversation on 2026-10-18; approved draft SHA-256 '+APPROVED_DRAFT_SHA
def git(*args,input=None):return subprocess.check_output(['git','--no-optional-locks','-C',str(ROOT),*args],input=input)
def norm(b):return b.replace(b'\r\n',b'\n')
def sha(b):return hashlib.sha256(norm(b)).hexdigest()
def remove_drive(blob):
 m=PAT.search(blob);assert m
 start=blob.rfind(b'\n',0,m.start())+1
 assert not blob[start:m.start()].strip(b' \t')
 return blob[:start]+blob[m.end():]
def committed_files():
 entries=[]
 for row in git('ls-tree','-r','-z',BASE).split(b'\0'):
  if row:
   metadata,name=row.split(b'\t',1);mode,kind,oid=metadata.split()
   assert kind==b'blob' and mode in (b'100644',b'100755')
   entries.append((name.decode(),oid))
 stream=io.BytesIO(git('cat-file','--batch',input=b''.join(oid+b'\n' for _,oid in entries)))
 result={}
 for p,oid in entries:
  header=stream.readline().split();assert header[:2]==[oid,b'blob']
  data=stream.read(int(header[2]));assert stream.read(1)==b'\n';result[p]=data
 assert stream.read()==b''
 return result
class DriveRemoval(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.old=committed_files()
  cls.targets={p for p,b in cls.old.items() if p.endswith('.html') and PAT.search(b)}
  cls.inventory=json.loads((ROOT/INVENTORY).read_text(encoding='utf8'))
  cls.entries=json.loads((ROOT/DRAFT).read_text(encoding='utf8'))['authorizations']
  spec=importlib.util.spec_from_file_location('drive_preservation_audit',ROOT/'scripts/audit-site.py')
  cls.a=importlib.util.module_from_spec(spec);sys.modules[spec.name]=cls.a;spec.loader.exec_module(cls.a)
  cls.base=cls.a.Audit(cls.a.Tree.revision_tree(ROOT,BASE))
  cls.current=cls.a.Audit(cls.a.Tree.working(ROOT))
  cls.fixture=json.loads(cls.old[cls.a.FIXTURE])
  cls.applied_fixture=json.loads((ROOT/cls.a.FIXTURE).read_bytes())
  cls.audit=cls.a.compare(cls.current,cls.base,cls.fixture)
 def test_clean_origin_and_empty_index(self):
  self.assertEqual(git('branch','--show-current').decode().strip(),'fix/travelpayouts-drive-removal-v1')
  self.assertEqual(git('rev-parse','HEAD').decode().strip(),BASE)
  self.assertEqual(git('diff','--cached','--name-only').strip(),b'')
 def test_inventory_is_derived_from_the_immutable_base(self):
  self.assertEqual(len(self.targets),112)
  self.assertEqual(self.inventory['base_revision'],BASE)
  self.assertEqual(self.inventory['drive_url'],URL)
  self.assertEqual(self.inventory['page_count'],112)
  self.assertEqual([e['source'] for e in self.inventory['pages']],sorted(self.targets))
  for e in self.inventory['pages']:
   p=e['source'];old=self.old[p];new=(ROOT/p).read_bytes();m=list(PAT.finditer(old))
   self.assertEqual(len(m),1,p);self.assertEqual(e['removed_count'],1)
   self.assertEqual(e['removed_script_markup'].encode(),m[0][0])
   self.assertEqual(e['before_file_sha256'],sha(old));self.assertEqual(e['after_file_sha256'],sha(new))
   self.assertEqual(e['removed_script_sha256'],sha(m[0][0]))
 def test_each_html_diff_is_exactly_one_script_tag(self):
  for p in sorted(self.targets):
   current=(ROOT/p).read_bytes()
   self.assertEqual(norm(current),norm(remove_drive(self.old[p])),p)
   self.assertFalse(PAT.search(current),p)
 def test_all_other_tracked_files_preserved(self):
  for p,old in self.old.items():
   if p in self.targets or p in {ADAPTED,self.a.FIXTURE}:continue
   actual=(ROOT/p).read_bytes()
   # LICENSE is text auto-converted by Git on Windows, like the existing preservation suites.
   if Path(p).suffix.lower() in self.a.TEXT_EXT | {'.py','.cjs'} or Path(p).name in {'.gitkeep','LICENSE'}:actual,old=norm(actual),norm(old)
   self.assertEqual(actual,old,p)
 def test_exact_changeset_without_unrelated_files(self):
  changed=set(git('diff','--name-only',BASE).decode().splitlines())
  untracked=set(git('ls-files','--others','--exclude-standard').decode().splitlines())
  self.assertEqual(changed,self.targets|{ADAPTED,self.a.FIXTURE})
  self.assertEqual(untracked,EXTRA)
 def test_manual_widgets_other_scripts_and_affiliate_opening_tags(self):
  widget_count=0
  for p,old in self.old.items():
   if not p.endswith('.html'):continue
   new=(ROOT/p).read_bytes()
   for pat in (rb'<a\b[^>]*>',rb'<form\b[^>]*>[\s\S]*?</form>',rb'<meta\b[^>]*>',rb'<link\b[^>]*>'):
    self.assertEqual(re.findall(pat,norm(old)),re.findall(pat,norm(new)),p)
   old_scripts=re.findall(rb'<script\b[^>]*>[\s\S]*?</script>',norm(old))
   new_scripts=re.findall(rb'<script\b[^>]*>[\s\S]*?</script>',norm(new))
   self.assertEqual([s for s in old_scripts if not PAT.fullmatch(s)],new_scripts,p)
   widget_count+=len(re.findall(rb'<script\b[^>]*src=["\x27]https://tpemb.com/content',old))
  self.assertEqual(widget_count,24)
 def test_approved_draft_is_immutable_and_exact(self):
  self.assertEqual(hashlib.sha256((ROOT/DRAFT).read_bytes()).hexdigest(),APPROVED_DRAFT_SHA)
  self.assertEqual(len(self.entries),116)
  fields=('kind','source','before','after')
  expected={tuple(e[f] for f in fields) for e in self.audit['errors']}
  actual={tuple(e[f] for f in fields) for e in self.entries}
  self.assertEqual(expected,actual);self.assertEqual(len(actual),116)
  self.assertEqual(collections.Counter(e['kind'] for e in self.entries),{'integration_markup':112,'cruise_file':4})
  for e in self.entries:
   self.assertEqual(e['base_revision'],BASE);self.assertIsNone(e['reviewed_by'])
   self.assertTrue(e['reason'].strip());self.assertEqual(e['recorded_on'],'2026-10-18')
 def test_original_baseline_detects_all_116_reviewed_changes(self):
  self.assertFalse(self.audit['passed'])
  self.assertEqual(collections.Counter((e['category'],e.get('kind')) for e in self.audit['errors']),{('contract_changed','integration_markup'):112,('protected_file_changed','cruise_file'):4})
 def test_baseline_only_appends_exact_owner_approved_entries(self):
  before=self.fixture;after=self.applied_fixture
  self.assertEqual(set(after),set(before))
  for key in before:
   if key!='authorizations':self.assertEqual(after[key],before[key],key)
  historic=before['authorizations'];applied=after['authorizations'][len(historic):]
  self.assertEqual(after['authorizations'][:len(historic)],historic)
  self.assertEqual(len(applied),116)
  pending='Exact completed diff awaits human review; do not apply this draft to the baseline.'
  approval='Exact completed diff approved by the requesting project owner in this conversation on 2026-10-18; approved draft SHA-256 '+APPROVED_DRAFT_SHA+'.'
  for draft,entry in zip(self.entries,applied):
   expected=dict(draft,reviewed_by=REVIEW,reason=draft['reason'].replace(pending,approval))
   self.assertEqual(entry,expected)
   self.assertTrue(self.a.valid_authorization(entry))
 def test_official_auditor_accepts_only_exact_approved_changes(self):
  result=self.a.compare(self.current,self.base,self.applied_fixture)
  self.assertTrue(result['passed'],result['errors'])
  self.assertEqual(result['errors'],[])
  self.assertEqual(len(result['authorized']),116)
  fields=('kind','source')
  self.assertEqual({tuple(e[f] for f in fields) for e in result['authorized']},
                   {tuple(e[f] for f in fields) for e in self.entries})
if __name__=='__main__':unittest.main()
