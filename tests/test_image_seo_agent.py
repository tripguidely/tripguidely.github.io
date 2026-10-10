"""Synthetic fixtures; never modify the real site or baseline."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

spec = importlib.util.spec_from_file_location('image_agent', Path(__file__).resolve().parents[1] / 'scripts/image-seo-agent.py')
agent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent)


class ImageAgentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'repo'
        self.root.mkdir()
        (self.root / '.git').mkdir()
        (self.root / 'assets').mkdir()
        (self.root / 'guide').mkdir()
        Image.new('RGB', (1000, 500), '#4c8192').save(self.root / 'assets/photo.jpg')
        (self.root / 'guide/index.html').write_text('<title>Guide</title><h1>Guide</h1><img src="../assets/photo.jpg" alt="View" width="1000" height="500">', encoding='utf-8')

    def report(self, **kwargs):
        return agent.scan(self.root, **kwargs)

    def test_relative_and_absolute_paths(self):
        for url in ('../assets/photo.jpg', '/assets/photo.jpg', 'https://tripguidely.github.io/assets/photo.jpg?v=1#crop', '//tripguidely.github.io/assets/photo.jpg'):
            self.assertEqual(agent.resolve(self.root,'guide/index.html',url,'https://tripguidely.github.io')['status'],'exists')

    def test_missing_paths(self):
        (self.root/'guide/index.html').write_text('<img src="missing.png"><img src="/gone.png"><img src="https://tripguidely.github.io/gone.png">',encoding='utf-8')
        report=self.report()
        self.assertEqual(report['counts']['missing_paths'],2)
        self.assertEqual(report['counts']['missing_references'],3)
        self.assertEqual(report['counts']['missing_alt'],3)

    def test_case_sensitive_deployment_paths(self):
        (self.root/'guide/index.html').write_text('<img src="/ASSETS/PHOTO.JPG" alt="View">',encoding='utf-8')
        self.assertEqual(self.report()['counts']['case_mismatches'],1)

    def test_external_and_embedded_not_missing(self):
        self.assertEqual(agent.resolve(self.root,'guide/index.html','https://other.test/x.jpg','https://tripguidely.github.io')['status'],'external-unverified')
        self.assertEqual(agent.resolve(self.root,'guide/index.html','data:image/png;base64,AAAA','https://tripguidely.github.io')['status'],'embedded-or-unsupported')

    def test_decoded_dimensions_and_format(self):
        data=self.report()['assets']['assets/photo.jpg']
        self.assertEqual((data['width'],data['height'],data['format'],data['status']),(1000,500,'JPEG','valid'))

    def test_corruption_and_misnamed_format(self):
        (self.root/'assets/fake.webp').write_bytes((self.root/'assets/photo.jpg').read_bytes())
        (self.root/'assets/bad.png').write_bytes(b'not image')
        kinds={f['kind'] for f in self.report()['findings']}
        self.assertTrue({'invalid-image','extension-format-mismatch'} <= kinds)

    def test_exact_duplicates(self):
        (self.root/'assets/copy.jpg').write_bytes((self.root/'assets/photo.jpg').read_bytes())
        self.assertEqual(self.report()['duplicates'],[['assets/copy.jpg','assets/photo.jpg']])

    def test_pixel_duplicates_with_different_bytes(self):
        Image.new('RGB',(50,25),'blue').save(self.root/'assets/a.png',compress_level=1)
        Image.new('RGB',(50,25),'blue').save(self.root/'assets/b.png',compress_level=9)
        self.assertEqual(self.report()['pixel_duplicates'],[['assets/a.png','assets/b.png']])
        self.assertEqual(self.report()['duplicates'],[])

    def test_filename(self):
        self.assertEqual(agent.filename('Éiffel Tower / Paris!'),'eiffel-tower-paris')
        self.assertEqual(agent.filename('!!!'),'editorial-image')

    def test_responsive_widths(self):
        self.assertEqual(agent.variants(1600,[300,600]),[320,640,1200])
        self.assertEqual(agent.variants(500,[700]),[500])
        self.assertEqual(agent.variants(1600,[]),[])
        self.assertEqual(agent.variants(1600,[0,-1,float('nan')]),[])

    def test_picture_preload_css_schema(self):
        (self.root/'guide/index.html').write_text('''<title>Guide</title>
<link rel="preload" as="image" href="/assets/photo.jpg" imagesrcset="/assets/photo.jpg 1000w">
<picture><source srcset="/assets/photo.jpg 1000w"><img src="/assets/photo.jpg" alt="View"></picture>
<meta property="og:image" content="/assets/photo.jpg">
<style>.x{background-image:url('/assets/photo.jpg')}</style>
<script type="application/ld+json">{"@type":"ImageObject","url":"/assets/photo.jpg","width":1000}</script>''',encoding='utf-8')
        report=self.report()
        self.assertEqual(report['counts']['references'],7)
        self.assertFalse(any(f['kind']=='responsive-opportunity' for f in report['findings']))
        self.assertFalse(report['parse_errors'])

    def test_base_href(self):
        (self.root/'guide/index.html').write_text('<base href="/assets/"><img src="photo.jpg" alt="View">',encoding='utf-8')
        self.assertEqual(self.report()['references'][0]['path'],'assets/photo.jpg')

    def test_svg_metadata(self):
        (self.root/'assets/icon.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 20"></svg>',encoding='utf-8')
        data=agent.metadata(self.root/'assets/icon.svg')
        self.assertEqual((data['width'],data['height'],data['format']),(40,20,'SVG'))

    def test_srcset_width_evidence(self):
        (self.root/'guide/index.html').write_text('<img src="/assets/photo.jpg" srcset="/assets/photo.jpg 800w" alt="View">',encoding='utf-8')
        self.assertIn('srcset-width-mismatch',{f['kind'] for f in self.report()['findings']})

    def test_density_and_data_srcset(self):
        self.assertEqual(agent.srcset('/a.jpg 1x, /b.jpg 2x'),[('/a.jpg','1x'),('/b.jpg','2x')])
        self.assertEqual(agent.srcset('data:image/png;base64,AAAA 1x, /b.jpg 2x')[0],('data:image/png;base64,AAAA','1x'))

    def test_measurements_plan(self):
        report=self.report(renders=[{'page':'guide/index.html','viewport':390,'dpr':2,'images':[{'index':0,'width':300,'height':150,'naturalWidth':1000}]}])
        self.assertEqual(report['dimension_plans'][0]['widths'],[320,640])
        self.assertEqual(report['dimension_plans'][0]['proposed_srcset']['webp'],'photo-320w.webp 320w, photo-640w.webp 640w')

    def test_real_traffic_export_ranking_and_provenance(self):
        traffic={'source':'Test fixture, not real GSC','rows':[{'page':'https://tripguidely.github.io/guide/','clicks':2,'impressions':100,'search_type':'web'}]}
        report=self.report(traffic=traffic)
        self.assertEqual(report['traffic_evidence'],traffic)
        observed=[f['observed_traffic'] for f in report['findings'] if f['source']=='guide/index.html']
        self.assertEqual(observed[0]['web_impressions'],100)
        self.assertEqual(observed[0]['clicks'],2)

    def test_selected_pixels_not_density_corrected_natural_width(self):
        report=self.report(renders=[{'page':'guide/index.html','origin':'http://localhost:9000','viewport':1440,'dpr':1,'images':[{'index':0,'width':300,'height':150,'naturalWidth':300,'currentSrc':'http://localhost:9000/assets/photo.jpg'}]}])
        self.assertEqual(report['dimension_plans'][0]['rendered'][0]['selected_pixel_width'],1000)
        self.assertIn('overdelivery-measured',{f['kind'] for f in report['findings']})

    def test_interactive_preview_missing(self):
        (self.root/'guide/index.html').write_text('<button data-preview-image="/absent.webp">Preview</button>',encoding='utf-8')
        self.assertEqual(self.report()['counts']['missing_paths'],1)

    def test_lcp_candidate_uses_context_not_asset_directory(self):
        (self.root/'guide/index.html').write_text('<section class="hero"><img src="/assets/photo.jpg" loading="lazy" alt="View"></section><section><img src="/assets/photo.jpg" loading="lazy" alt="Detail"></section>',encoding='utf-8')
        self.assertEqual(sum(f['kind']=='potential-lcp-lazy' for f in self.report()['findings']),1)

    def test_report_accuracy_and_single_page(self):
        report=self.report(page='guide/index.html')
        self.assertEqual(report['counts']['html_files'],1)
        self.assertEqual(report['counts']['image_files'],1)
        self.assertEqual(report['counts']['references'],1)
        self.assertIn('responsive-opportunity',agent.markdown(report))
        self.assertEqual(json.loads(json.dumps(report)),report)

    def test_dry_run_leaves_every_byte_and_filename_unchanged(self):
        before={p.relative_to(self.root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in agent.files(self.root)}
        self.report()
        after={p.relative_to(self.root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in agent.files(self.root)}
        self.assertEqual(before,after)

    def test_output_rejects_source_other_worktrees_and_ancestors(self):
        other=Path(self.temp.name)/'other'
        other.mkdir()
        (other/'.git').write_text('gitdir: elsewhere',encoding='utf-8')
        for output in (self.root/'assets/new',other/'previews',self.root.parent):
            with self.assertRaises(ValueError):agent.safe_output(self.root,output)

    def test_optimization_validates_output_and_preserves_source(self):
        source=self.root/'assets/photo.jpg'
        before=source.read_bytes()
        output=Path(self.temp.name)/'previews'
        results=agent.optimize(self.root,'assets/photo.jpg',output,[320],['WEBP','AVIF'])
        self.assertEqual(len(results),2)
        for result in results:
            data=agent.metadata(output/result['file'])
            self.assertEqual((data['width'],data['height']),(320,160))
            self.assertTrue(result['quality_gate_passed'])
        self.assertTrue((output/'preview.html').exists())
        self.assertEqual(source.read_bytes(),before)
        with self.assertRaises(ValueError):agent.optimize(self.root,'assets/photo.jpg',output,[320],['WEBP'])

    def test_no_upscale_or_alpha_loss(self):
        output=Path(self.temp.name)/'previews'
        with self.assertRaises(ValueError):agent.optimize(self.root,'assets/photo.jpg',output,[1200])
        Image.new('RGBA',(20,10),(30,40,50,90)).save(self.root/'assets/alpha.png')
        with self.assertRaises(ValueError):agent.optimize(self.root,'assets/alpha.png',output,[20],['JPEG'])
        results=agent.optimize(self.root,'assets/alpha.png',output,[20],['PNG','WEBP'])
        self.assertTrue(all(r['quality_gate_passed'] for r in results))

    def test_new_filename_does_not_keep_old_dimensions(self):
        (self.root/'assets/view-1000x500.jpg').write_bytes((self.root/'assets/photo.jpg').read_bytes())
        result=agent.optimize(self.root,'assets/view-1000x500.jpg',Path(self.temp.name)/'previews',[320],['WEBP'])[0]
        self.assertEqual(result['file'],'view-320w.webp')

    def test_compression_quality_rejection(self):
        Image.effect_noise((128,128),100).convert('RGB').save(self.root/'assets/noise.png')
        result=agent.optimize(self.root,'assets/noise.png',Path(self.temp.name)/'previews',[128],['WEBP'],1)[0]
        self.assertFalse(result['quality_gate_passed'])

    def test_bad_schema_reported(self):
        (self.root/'guide/index.html').write_text('<script type="application/ld+json">broken</script>',encoding='utf-8')
        self.assertEqual(len(self.report()['parse_errors']),1)

    def test_brief_authenticity(self):
        data=agent.brief('hotels/paris/index.html','hero','Paris rooftops',1600,900)
        self.assertEqual(data['suggested_filename'],'paris-rooftops')
        self.assertIn('brief only',data['status'])
        self.assertIn('licensed',data['restrictions'][0])

    def test_report_hardlink_cannot_overwrite_source(self):
        output = Path(self.temp.name) / 'reports'
        output.mkdir()
        source = self.root / 'guide/index.html'
        before = source.read_bytes()
        os.link(source, output / 'audit.json')
        with self.assertRaises(ValueError):
            agent.write_reports(self.root, output, self.report())
        self.assertEqual(source.read_bytes(), before)
        self.assertFalse((output / 'audit.md').exists())

    def test_reports_require_fresh_directory_and_parse(self):
        output = Path(self.temp.name) / 'reports'
        report = self.report()
        agent.write_reports(self.root, output, report)
        self.assertEqual(json.loads((output / 'audit.json').read_text()), report)
        self.assertIn('html_files: 1', (output / 'audit.md').read_text())
        with self.assertRaises(ValueError):
            agent.write_reports(self.root, output, report)
        empty = Path(self.temp.name) / 'empty'
        empty.mkdir()
        with self.assertRaises(ValueError):
            agent.ExclusiveOutput(self.root, empty)
        if os.name != 'nt':
            self.assertEqual(output.stat().st_mode & 0o777, 0o700)
            self.assertEqual((output / 'audit.json').stat().st_mode & 0o777, 0o600)

    def test_exclusive_creation_blocks_alias_inserted_at_open(self):
        output = agent.ExclusiveOutput(self.root, Path(self.temp.name) / 'reports')
        source = self.root / 'assets/photo.jpg'
        before = source.read_bytes()
        original = os.open
        def raced_open(path, flags, mode=0o777, **kwargs):
            os.link(source, path)
            return original(path, flags, mode, **kwargs)
        with patch.object(agent.os, 'open', side_effect=raced_open):
            with self.assertRaises(FileExistsError):
                output.write('new.bin', b'never overwrite')
        self.assertEqual(source.read_bytes(), before)

    def test_output_directory_identity_change_is_rejected(self):
        output = agent.ExclusiveOutput(self.root, Path(self.temp.name) / 'reports')
        moved = Path(self.temp.name) / 'moved'
        self.assertTrue(output.path.resolve().is_relative_to(Path(self.temp.name).resolve()))
        self.assertTrue(moved.resolve().is_relative_to(Path(self.temp.name).resolve()))
        output.path.rename(moved)
        output.path.mkdir()
        with self.assertRaisesRegex(ValueError, 'identity changed'):
            output.write('audit.json', '{}')
        self.assertFalse((output.path / 'audit.json').exists())

    def test_optimization_existing_alias_cannot_overwrite_source(self):
        output = Path(self.temp.name) / 'previews'
        output.mkdir()
        source = self.root / 'assets/photo.jpg'
        before = source.read_bytes()
        os.link(source, output / 'photo-320w.webp')
        with self.assertRaises(ValueError):
            agent.optimize(self.root, 'assets/photo.jpg', output, [320], ['WEBP'])
        self.assertEqual(source.read_bytes(), before)

    def test_svg_explicit_dimensions(self):
        path = self.root / 'assets/icon.svg'
        path.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="40px" height="20"/>')
        data = agent.metadata(path)
        self.assertEqual((data['width'], data['height'], data['status']), (40, 20, 'valid'))

    def test_svg_unknown_dimensions_continue_scan(self):
        for attributes in ('', 'width="100%" height="100%"', 'width="40"'):
            with self.subTest(attributes=attributes):
                (self.root / 'assets/icon.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" {attributes}/>')
                (self.root / 'guide/index.html').write_text('<img src="/assets/icon.svg" width="40" height="20" alt="Icon"><img src="/assets/photo.jpg" alt="View">')
                report = self.report()
                self.assertEqual(report['assets']['assets/icon.svg']['status'], 'valid')
                self.assertIsNone(report['assets']['assets/icon.svg']['height'])
                self.assertIn('unknown-image-dimensions', {f['kind'] for f in report['findings']})
                self.assertEqual(report['counts']['responsive_opportunities'], 1)
                self.assertEqual(json.loads(json.dumps(report)), report)

    def test_svg_malformed_is_reported(self):
        (self.root / 'assets/icon.svg').write_text('<svg><broken></svg>')
        report = self.report()
        self.assertEqual(report['assets']['assets/icon.svg']['status'], 'invalid')
        self.assertIn('invalid-image', {f['kind'] for f in report['findings']})

    def test_external_current_src_collision_is_unverified(self):
        for current in ('https://external.example/assets/photo.jpg', 'http://localhost:9001/assets/photo.jpg'):
            with self.subTest(current=current):
                report = self.report(renders=[{'page':'guide/index.html','origin':'http://localhost:9000','viewport':1440,'dpr':1,'images':[{'index':0,'width':400,'height':200,'naturalWidth':200,'currentSrc':current}]}])
                measured = report['images'][0]['rendered'][0]
                self.assertIsNone(measured['selected_pixel_width'])
                self.assertIn('unverified', measured['selected_source_status'])
                self.assertEqual(measured['naturalWidth'], 200)
                self.assertFalse(any(f['kind'] in ('overdelivery-measured', 'underdelivery-measured') for f in report['findings']))

    def test_current_src_without_sampler_origin_is_unverified(self):
        report = self.report(renders=[{'page':'guide/index.html','viewport':1440,'images':[{'index':0,'width':400,'height':200,'naturalWidth':200,'currentSrc':'http://localhost:9000/assets/photo.jpg'}]}])
        self.assertIsNone(report['images'][0]['rendered'][0]['selected_pixel_width'])

    def test_legacy_actual_url_establishes_sampler_origin(self):
        report = self.report(renders=[{'page':'guide/index.html','actualUrl':'http://127.0.0.1:9000/guide/index.html','viewport':1440,'images':[{'index':0,'width':400,'height':200,'naturalWidth':1000,'currentSrc':'http://127.0.0.1:9000/assets/photo.jpg'}]}])
        self.assertEqual(report['images'][0]['rendered'][0]['selected_pixel_width'], 1000)

    def test_external_primary_image_has_unverified_measurement(self):
        (self.root / 'guide/index.html').write_text('<img src="https://external.example/assets/photo.jpg" alt="External">')
        report = self.report(renders=[{'page':'guide/index.html','viewport':1440,'images':[{'index':0,'width':400,'height':200,'naturalWidth':200,'currentSrc':'https://external.example/assets/photo.jpg'}]}])
        self.assertEqual(report['counts']['external_references'], 1)
        self.assertEqual(report['counts']['missing_paths'], 0)
        self.assertIsNone(report['images'][0]['rendered'][0]['selected_pixel_width'])
        self.assertEqual(report['dimension_plans'], [])

    def sampler(self, output, module, opt_in=True):
        node = shutil.which('node')
        if not node:
            self.skipTest('Node is required for sampler tests')
        script = Path(__file__).resolve().parents[1] / 'scripts/image-seo-render.cjs'
        command = [node, str(script), str(self.root), str(output), str(module), os.environ.get('IMAGE_SEO_CHROME', '')]
        if opt_in:
            command.append('--allow-browser-sampling')
        return subprocess.run(command, capture_output=True, text=True, timeout=60)

    def test_sampler_is_disabled_by_default(self):
        output = Path(self.temp.name) / 'render'
        run = self.sampler(output, 'uninstalled-module', opt_in=False)
        self.assertEqual(run.returncode, 2)
        self.assertIn('disabled by default', run.stderr)
        self.assertFalse(output.exists())

    def test_sampler_screenshot_hardlink_cannot_overwrite_source(self):
        output = Path(self.temp.name) / 'render'
        output.mkdir()
        source = self.root / 'assets/photo.jpg'
        before = source.read_bytes()
        os.link(source, output / 'index.html-390.png')
        stub = Path(self.temp.name) / 'stub.cjs'
        stub.write_text("module.exports={chromium:{launch:async()=>{throw Error('BROWSER MUST NOT LAUNCH')}}};")
        run = self.sampler(output, stub)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('EEXIST', run.stderr)
        self.assertNotIn('BROWSER MUST NOT LAUNCH', run.stderr)
        self.assertEqual(source.read_bytes(), before)
        self.assertFalse((output / 'render.json').exists())

    def test_sampler_exclusive_write_blocks_late_screenshot_alias(self):
        output = Path(self.temp.name) / 'render'
        source = self.root / 'assets/photo.jpg'
        before = source.read_bytes()
        (self.root / 'index.html').write_text('<title>Synthetic</title>')
        stub = Path(self.temp.name) / 'stub.cjs'
        stub.write_text(r'''
const fs=require('node:fs'),path=require('node:path');
module.exports={chromium:{launch:async()=>{
 fs.linkSync(path.join(process.argv[2],'assets/photo.jpg'),path.join(process.argv[3],'index.html-390.png'));
 const tab={goto:async()=>{},waitForLoadState:async()=>{},waitForTimeout:async()=>{},url:()=>'',evaluate:async()=>({images:[]}),screenshot:async()=>Buffer.from('MUST NOT OVERWRITE')};
 const context={routeWebSocket:async()=>{},route:async()=>{},addInitScript:async()=>{},newPage:async()=>tab,close:async()=>{}};
 return {newContext:async()=>context,close:async()=>{}};
}}};''')
        run = self.sampler(output, stub)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('EEXIST', run.stderr)
        self.assertEqual(source.read_bytes(), before)
        self.assertFalse((output / 'render.json').exists())

    def test_sampler_missing_websocket_api_fails_closed(self):
        output = Path(self.temp.name) / 'render'
        stub = Path(self.temp.name) / 'stub.cjs'
        stub.write_text('module.exports={chromium:{launch:async()=>({newContext:async()=>({}),close:async()=>{}})}};')
        run = self.sampler(output, stub)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('lacks required WebSocket interception', run.stderr)
        self.assertFalse((output / 'render.json').exists())

    def test_chrome_blocks_original_websocket_and_http_fixture(self):
        module = os.environ.get('IMAGE_SEO_PLAYWRIGHT_MODULE')
        chrome = os.environ.get('IMAGE_SEO_CHROME')
        node = shutil.which('node')
        if not module or not chrome or not node:
            self.skipTest('Set IMAGE_SEO_PLAYWRIGHT_MODULE and IMAGE_SEO_CHROME for real Chrome verification')
        # Only disposable loopback servers; local SVG is a synthetic test fixture.
        fixture = r'''
const fs=require('node:fs'), http=require('node:http'), cp=require('node:child_process'), path=require('node:path');
const [script,root,out,module,chrome]=process.argv.slice(1);
let httpCount=0, socketCount=0;
const server=http.createServer((req,res)=>{httpCount++;res.end('test');});
server.on('upgrade',(req,socket)=>{socketCount++;socket.on('error',()=>{});socket.destroy();});
server.listen(0,'127.0.0.1',()=>{
 const port=server.address().port;
 fs.writeFileSync(path.join(root,'assets/test.svg'),'<svg xmlns="http://www.w3.org/2000/svg" width="200" height="100"/>');
 fs.writeFileSync(path.join(root,'index.html'),`<title>Transport test</title><img src="/assets/test.svg" alt="Synthetic"><script>fetch('http://127.0.0.1:${port}/http').catch(()=>{});new WebSocket('ws://127.0.0.1:${port}/socket');document.querySelector('img').style.width='123px';try{new RTCPeerConnection();document.querySelector('img').style.width='999px';}catch{}try{new WebTransport('https://127.0.0.1:${port}');document.querySelector('img').style.width='998px';}catch{}</script>`);
 cp.execFile(process.execPath,[script,root,out,module,chrome,'--allow-browser-sampling'],{timeout:45000},(error,stdout,stderr)=>{
  server.close();
  if(error){console.error(stderr);process.exitCode=1;return;}
  const runs=JSON.parse(fs.readFileSync(path.join(out,'render.json')));
  const widths=runs.filter(r=>r.page==='index.html').map(r=>r.images[0].width);
  console.log(JSON.stringify({httpCount,socketCount,widths}));
 });
});'''
        script = Path(__file__).resolve().parents[1] / 'scripts/image-seo-render.cjs'
        output = Path(self.temp.name) / 'render'
        run = subprocess.run([node, '-e', fixture, str(script), str(self.root), str(output), module, chrome], capture_output=True, text=True, timeout=60)
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout)
        self.assertEqual(result['httpCount'], 0)
        self.assertEqual(result['socketCount'], 0)
        self.assertEqual(result['widths'], [123] * 5)  # Fixture JS actually executed; unsupported APIs rejected.


if __name__=='__main__':
    unittest.main()
