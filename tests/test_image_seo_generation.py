"""Offline V2 tests. All provider transports are mocked; no paid API calls."""
import base64
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
from io import BytesIO
import json
import os
import multiprocessing
import struct
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch
import zlib

from PIL import Image

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import image_seo_providers as providers

spec = importlib.util.spec_from_file_location('generation_agent', SCRIPTS / 'image-seo-agent.py')
agent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent)
BASE = 'a' * 40
OVERSIZE_WEBP = base64.b64decode('UklGRroCAABXRUJQVlA4TK0CAAAv/8//AwfQ//73v/9hLCFBgv+32yMi0VtMmqx/ey8hov8TACTJ//9BiIiQ//7z33///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff//9999///3333///ffff/8BAA==')  # Actual 706-byte 4096-square review fixture.


def frame_fixture(buffer, limit, mode, marker=None):
    """Real spawned, offline producers for deadline/framing regression tests."""
    if mode.startswith('partial'):
        buffer[:providers.FRAME.size] = providers.FRAME.pack(
            providers.FRAME_MAGIC, providers.FRAME_BYTES, 8, hashlib.sha256(b'complete').digest())
        buffer[providers.FRAME.size:providers.FRAME.size+1] = b'c'
    if marker is not None:
        Path(marker).write_text('SYNTHETIC PRODUCER STARTED')
    if mode in ('stall', 'partial-stall'):
        while True:
            time.sleep(.05)
    if mode == 'committed-stall':
        providers._write_frame(buffer, limit, providers.FRAME_BYTES, b'complete')
        while True:
            time.sleep(.05)
    if mode == 'late':
        time.sleep(2)
    if mode == 'crash':
        os._exit(23)
    if mode == 'partial-exit':
        return
    if mode == 'oversize':
        buffer[:providers.FRAME.size] = providers.FRAME.pack(providers.FRAME_MAGIC, providers.FRAME_BYTES, limit+1, b'\0'*32)
        return
    if mode == 'json':
        providers._write_frame(buffer, limit, providers.FRAME_JSON, b'{"complete":true}')
    else:
        providers._write_frame(buffer, limit, providers.FRAME_BYTES, b'complete')


class GenerationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.root = self.directory / 'repo'
        self.root.mkdir()
        (self.root / '.git').mkdir()
        (self.root / 'page.html').write_text('<title>Disposable</title><h1>Test fixture</h1>')
        self.brief = self.directory / 'brief.json'
        self.document = {'base_revision': BASE, 'generation_enabled': False, 'briefs': [
            {'id': 'fixture', 'operation': 'optional_illustration', 'page': 'page.html', 'placement': '#fixture',
             'master_dimensions': [64, 32], 'prompt': 'Synthetic shapes only', 'generation_enabled': False}]}
        self.save_brief()
        self.request = agent.generation_request(self.root, self.brief, 'fixture', BASE)
        self.output = self.directory / 'output'
        self.ledger = self.directory / 'ledger'
        # Test failures cannot accidentally fall through to an external provider.
        for target in ('socket.create_connection', 'http.client.HTTPSConnection.connect',
                       'image_seo_providers.network_request'):
            guard = patch(target, side_effect=AssertionError('Network forbidden in offline tests'))
            guard.start()
            self.addCleanup(guard.stop)

    def save_brief(self):
        self.brief.write_text(json.dumps(self.document), encoding='utf-8')

    def live_request(self):
        return replace(self.request, width=1536, height=864)

    def approval(self, request=None):
        request = request or self.live_request()
        now = datetime.now(timezone.utc)
        return {'operation': 'PAID_IMAGE_GENERATION', 'provider': 'openai', 'status': 'APPROVED',
                'approval_id': '1' * 32, 'request_sha256': request.fingerprint(), 'base_revision': BASE,
                'max_requests': 1, 'max_images': 1, 'budget_is_advisory': True, 'advisory_budget_usd': 1,
                'review_reference': 'OFFLINE TEST ONLY NOT OWNER AUTHORIZATION',
                'approved_at': (now-timedelta(minutes=1)).isoformat(), 'expires_at': (now+timedelta(minutes=1)).isoformat()}

    def invoke_live(self, request=None, **changes):
        request = request or self.live_request()
        options = {'approval': self.approval(request), 'confirmation': providers.PAID_CONFIRMATION,
                   'root': self.root, 'ledger': self.ledger}
        options.update(changes)
        return providers.OpenAIProvider().generate(request, **options)

    def preview(self, **options):
        return agent.generate_preview(self.root, self.request, self.output, mock=True, **options)

    def receipt(self, manifest):
        return {'schema_version': 3, 'status': 'APPROVED', 'manifest_sha256': agent.digest(self.output / 'review-manifest.json'),
                'request_sha256': manifest['request_sha256'], 'artifacts': manifest['artifacts'],
                'layout_evidence_state': manifest['layout_evidence']['state'],
                'layout_evidence_sha256': manifest['layout_evidence']['sha256'],
                'rights_reviewed': True, 'visual_reviewed': True, 'layout_reviewed': True,
                'review_reference': 'SYNTHETIC TEST RECEIPT ONLY'}

    def test_mock_is_deterministic_and_truthful(self):
        provider = providers.MockProvider()
        a, b = provider.generate(self.request), provider.generate(self.request)
        self.assertEqual(a.image, b.image)
        self.assertEqual(a.generation_status, 'MOCK_ONLY_NOT_AI_GENERATED')
        self.assertIsNone(a.model)
        self.assertFalse(provider.capabilities()['network'])

    def test_mock_changes_with_bound_context(self):
        provider = providers.MockProvider()
        self.assertNotEqual(provider.generate(self.request).image,
                            provider.generate(replace(self.request, context_sha256='b'*64)).image)

    def test_import_has_no_network_or_credentials(self):
        with patch('os.environ.get', side_effect=AssertionError('No credentials at import')):
            spec = importlib.util.spec_from_file_location('isolated_provider', SCRIPTS / 'image_seo_providers.py')
            module = importlib.util.module_from_spec(spec)
            sys.modules['isolated_provider'] = module
            try:
                spec.loader.exec_module(module)
            finally:
                del sys.modules['isolated_provider']

    def test_default_dry_run_has_no_writes_or_credentials(self):
        with patch('os.environ.get', side_effect=AssertionError('Offline must not read credentials')):
            plan = agent.generate_preview(self.root, self.request, self.output)
        self.assertEqual(plan['mode'], 'OFFLINE_DRY_RUN')
        self.assertEqual(plan['paid_calls'], 0)
        self.assertFalse(self.output.exists())

    def test_missing_paid_approval_gates_before_credentials(self):
        with patch('os.environ.get', side_effect=AssertionError('Approval must gate credential read')):
            with self.assertRaises(ValueError):
                providers.OpenAIProvider().generate(self.live_request())
        self.assertFalse(self.ledger.exists())

    def test_missing_confirmation_gates_before_credentials(self):
        with patch('os.environ.get', side_effect=AssertionError('No credentials before confirmation')):
            with self.assertRaises(ValueError):
                self.invoke_live(confirmation=None)

    def test_missing_credentials_consumes_attempt_without_network(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, 'OPENAI_API_KEY required'):
                self.invoke_live()
        self.assertTrue((self.ledger / ('paid-'+'1'*32) / 'attempt.json').exists())

    def test_live_transport_is_called_only_with_exact_mocked_authorization(self):
        request = self.live_request()
        image = providers.MockProvider().generate(request).image
        body = json.dumps({'data': [{'b64_json': base64.b64encode(image).decode()}]}).encode()
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'OFFLINE_TEST_SECRET'}), patch.object(providers, 'network_request', return_value=body) as transport:
            result = self.invoke_live(request)
        self.assertEqual(result.provider, 'openai')
        payload, key = transport.call_args.args
        data = json.loads(payload)
        self.assertEqual(data['model'], providers.MODEL)
        self.assertEqual(data['size'], '1536x864')
        self.assertEqual(data['n'], 1)
        self.assertNotIn('response_format', data)
        self.assertEqual(key, 'OFFLINE_TEST_SECRET')
        self.assertNotIn(key, (self.ledger / ('paid-'+'1'*32) / 'attempt.json').read_text())

    def test_consumed_approval_cannot_be_replayed(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                self.invoke_live()
        with patch('os.environ.get', side_effect=AssertionError('Replay must gate secrets')):
            with self.assertRaisesRegex(ValueError, 'fresh output'):
                self.invoke_live()

    def test_ambiguous_timeout_is_not_retried_and_does_not_leak_secret(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'DO_NOT_LOG'}), patch.object(providers, 'network_request', side_effect=TimeoutError('DO_NOT_LOG')) as transport:
            with self.assertRaisesRegex(ValueError, 'billing unknown') as error:
                self.invoke_live()
        self.assertEqual(transport.call_count, 1)
        self.assertNotIn('DO_NOT_LOG', str(error.exception))

    def test_live_concurrency_fails_closed(self):
        providers._live_lock.acquire()
        try:
            with self.assertRaisesRegex(ValueError, 'concurrent'):
                self.invoke_live()
        finally:
            providers._live_lock.release()

    def test_paid_approval_binds_all_request_fields(self):
        request = self.live_request()
        approval = self.approval(request)
        for changed in (replace(request, prompt='Changed'), replace(request, quality='high'),
                        replace(request, context_sha256='b'*64), replace(request, width=1280)):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                self.invoke_live(changed, approval=approval)

    def test_expired_naive_and_future_approvals_rejected(self):
        for changes in ({'expires_at': '2020-01-01T00:00:00+00:00'}, {'approved_at': '2026-01-01T00:00:00'},
                        {'approved_at': '2099-01-01T00:00:00+00:00'}, {'review_reference': ''},
                        {'advisory_budget_usd': float('nan')}, {'budget_is_advisory': False}, {'approval_id': '../escape'}):
            approval = self.approval()
            approval.update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.invoke_live(approval=approval)

    def test_counts_are_bounded_and_initial_limit_is_one(self):
        for count in (0, 2, 3, 4, True, -1):
            with self.subTest(count=count), self.assertRaises(ValueError):
                providers.MockProvider().generate(replace(self.request, count=count))
        self.assertEqual(providers.FRAMEWORK_MAX_IMAGES, 3)

    def test_unknown_model_or_destination_rejected_before_secrets(self):
        for model in ('https://attacker.invalid/v1/images', 'invented-model'):
            with self.subTest(model=model), patch('os.environ.get', side_effect=AssertionError('No secrets')):
                with self.assertRaises(ValueError):
                    self.invoke_live(replace(self.live_request(), model=model))

    def test_request_input_and_dimensions_limits(self):
        for changes in ({'prompt': 'é'*5000}, {'width': 4096}, {'width': 64.0}, {'width': 0},
                        {'height': 8192}, {'width': 65}, {'width': 2560, 'height': 2560},
                        {'width': 16, 'height': 64}, {'output_format': 'svg'}, {'quality': 'invalid'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                providers.MockProvider().generate(replace(self.request, **changes))

    def test_base_and_context_hashes_required(self):
        for changes in ({'base_revision': 'main'}, {'context_sha256': ''}):
            with self.assertRaises(ValueError):
                replace(self.request, **changes).validate()

    def test_bounded_input_read(self):
        path = self.directory / 'large'
        path.write_bytes(b'x'*11)
        with self.assertRaises(ValueError):
            providers.read_bounded(path, 10)

    def test_invalid_json_and_response_schema(self):
        for value in (b'bad', b'null', b'[]', b'{}', b'{"data":[]}', b'{"data":[{},{}]}',
                      b'{"data":[null]}', b'{"data":[{"b64_json":7}]}', b'{"data":[{"b64_json":"%%"}]}'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                providers.decode_response(value)

    def test_url_response_never_fetched(self):
        with self.assertRaisesRegex(ValueError, 'URL outputs forbidden'):
            providers.decode_response(b'{"data":[{"url":"https://attacker.invalid/image.png","b64_json":"YQ=="}]}')

    def test_oversized_response_and_base64(self):
        with patch.object(providers, 'MAX_JSON_BYTES', 20), self.assertRaises(ValueError):
            providers.decode_response(b' '*21)
        with patch.object(providers, 'MAX_IMAGE_BYTES', 2), self.assertRaises(ValueError):
            providers.decode_response(b'{"data":[{"b64_json":"YWJj"}]}')

    def test_transport_rejects_redirect_and_oversized_length_without_reading(self):
        for status, length in ((302, '1'), (200, str(providers.MAX_JSON_BYTES+1)), (200, 'bad')):
            response = Mock(status=status)
            response.getheader.side_effect = lambda key, default=None: length if key == 'Content-Length' else default
            connection = Mock()
            connection.getresponse.return_value = response
            with patch('http.client.HTTPSConnection', return_value=connection) as constructor:
                with self.assertRaises(ValueError):
                    providers._post(b'{}', 'OFFLINE_TEST_ONLY')
                response.read1.assert_not_called()
                self.assertEqual(constructor.call_args.args[0], 'api.openai.com')
                self.assertEqual(connection.request.call_args.args[:2], ('POST', '/v1/images/generations'))

    def test_streamed_response_byte_limit(self):
        response = Mock(status=200)
        response.getheader.side_effect = lambda key, default=None: default
        response.read1.return_value = b'x'*11
        connection = Mock()
        connection.getresponse.return_value = response
        with patch('http.client.HTTPSConnection', return_value=connection), patch.object(providers, 'MAX_JSON_BYTES', 10):
            with self.assertRaises(ValueError):
                providers._post(b'{}', 'OFFLINE_TEST_ONLY')

    def test_valid_full_image_decode(self):
        data = providers.MockProvider().generate(self.request).image
        metadata = providers.validate_image(data, 64, 32, 'PNG')
        self.assertEqual(metadata['sha256'], hashlib.sha256(data).hexdigest())
        self.assertEqual((metadata['width'], metadata['height']), (64, 32))

    def test_invalid_and_truncated_image_bytes(self):
        valid = providers.MockProvider().generate(self.request).image
        for image in (b'invalid', valid[:40]):
            with self.assertRaises((ValueError, OSError)):
                providers.validate_image(image, 64, 32, 'PNG')

    def test_decoded_pixel_and_file_limits(self):
        data = providers.MockProvider().generate(self.request).image
        with patch.object(providers, 'MAX_PIXELS', 100), self.assertRaises(ValueError):
            providers.validate_image(data, 64, 32, 'PNG')
        with patch.object(providers, 'MAX_EDGE', 32), self.assertRaises(ValueError):
            providers.validate_image(data, 64, 32, 'PNG')
        with patch.object(providers, 'MAX_IMAGE_BYTES', 10), self.assertRaises(ValueError):
            providers.validate_image(data, 64, 32, 'PNG')

    def test_actual_format_and_dimensions_required(self):
        data = providers.MockProvider().generate(self.request).image
        with self.assertRaises(ValueError):
            providers.validate_image(data, 64, 32, 'JPEG')
        with self.assertRaises(ValueError):
            providers.validate_image(data, 32, 16, 'PNG')

    def test_unsupported_format_and_animation(self):
        stream = BytesIO()
        Image.new('RGB', (64, 32)).save(stream, 'BMP')
        with self.assertRaises(ValueError):
            providers.validate_image(stream.getvalue(), 64, 32, 'BMP')
        stream = BytesIO()
        Image.new('RGB', (64, 32), 'blue').save(stream, 'PNG', save_all=True,
                                              append_images=[Image.new('RGB', (64, 32), 'red')])
        with self.assertRaises(ValueError):
            providers.validate_image(stream.getvalue(), 64, 32, 'PNG')

    def test_duplicate_bytes_and_pixels_rejected(self):
        image = Image.new('RGB', (64, 32), 'blue')
        a, b = BytesIO(), BytesIO()
        image.save(a, 'PNG', compress_level=1)
        image.save(b, 'PNG', compress_level=9)
        ma = providers.validate_image(a.getvalue(), 64, 32, 'PNG')
        mb = providers.validate_image(b.getvalue(), 64, 32, 'PNG')
        self.assertNotEqual(ma['sha256'], mb['sha256'])
        for images in ([ma, ma], [ma, mb]):
            with self.assertRaises(ValueError):
                providers.reject_duplicates(images)

    def test_worker_timeout_and_failure(self):
        data = providers.MockProvider().generate(self.request).image
        with self.assertRaises(TimeoutError):
            providers.bounded_worker('validate', (data, 64, 32, 'PNG'), timeout=0.001)
        with self.assertRaises(ValueError):
            providers.bounded_worker('validate', (b'bad', 64, 32, 'PNG'))

    def test_optimizer_converts_all_four_formats_without_upscaling(self):
        manifest = self.preview(formats=('WEBP', 'AVIF', 'JPEG', 'PNG'), quality=100)
        self.assertEqual({item['format'] for item in manifest['optimization_outputs']}, {'WEBP', 'AVIF', 'JPEG', 'PNG'})
        for result in manifest['optimization_outputs']:
            with Image.open(self.output / 'variants' / result['file']) as decoded:
                decoded.load()
                self.assertEqual(decoded.size, (64, 32))
                self.assertEqual(decoded.format, result['format'])
        selected = set(manifest['smallest_quality_passing_files'])
        self.assertTrue(all(result['quality_gate_passed'] for result in manifest['optimization_outputs'] if result['file'] in selected))

    def test_transparency_preserved_and_jpeg_rejected(self):
        source = self.directory / 'transparent'
        source.mkdir()
        Image.new('RGBA', (64, 32), (50, 100, 150, 0)).save(source / 'source.png')
        result = providers.bounded_worker('optimize', (str(source), 'source.png', str(self.output), [32], ['PNG', 'WEBP'], 100, (64, 32), 'PNG'))
        for item in result:
            with Image.open(self.output / item['file']) as image:
                self.assertEqual(image.getchannel('A').getextrema(), (0, 0))
        with self.assertRaises(ValueError):
            providers.bounded_worker('optimize', (str(source), 'source.png', str(self.directory/'bad'), [32], ['JPEG'], 100, (64, 32), 'PNG'))

    def test_quality_failure_cannot_produce_completed_manifest(self):
        original = providers.bounded_worker
        def worker(operation, args):
            if operation == 'optimize':
                return [{'quality_gate_passed': False}]
            return original(operation, args)
        with patch.object(providers, 'bounded_worker', side_effect=worker), self.assertRaises(ValueError):
            self.preview()
        self.assertFalse((self.output/'review-manifest.json').exists())

    def test_worker_failure_cannot_produce_manifest(self):
        with patch.object(providers, 'bounded_worker', side_effect=TimeoutError('fixture')), self.assertRaises(TimeoutError):
            self.preview()
        self.assertFalse((self.output/'review-manifest.json').exists())

    def test_fresh_output_required_no_asset_overwrites(self):
        original = (self.root/'page.html').read_bytes()
        self.output.mkdir()
        os.link(self.root/'page.html', self.output/'plan.json')
        with self.assertRaises(ValueError):
            self.preview()
        self.assertEqual((self.root/'page.html').read_bytes(), original)

    def test_production_and_other_worktree_outputs_rejected(self):
        other = self.directory/'other-worktree'
        other.mkdir()
        (other/'.git').write_text('gitdir: synthetic')
        for output in (self.root/'assets/generated', other/'assets/generated', self.root.parent):
            with self.subTest(output=output), self.assertRaises(ValueError):
                agent.generate_preview(self.root, self.request, output, mock=True)
        self.assertFalse((self.root/'assets').exists())

    def test_late_file_alias_is_never_overwritten(self):
        destination = agent.ExclusiveOutput(self.root, self.output)
        original = (self.root/'page.html').read_bytes()
        os.link(self.root/'page.html', self.output/'candidate.png')
        with self.assertRaises(FileExistsError):
            destination.write('candidate.png', b'MUST NOT OVERWRITE')
        self.assertEqual((self.root/'page.html').read_bytes(), original)

    def test_output_filename_traversal_rejected(self):
        destination = agent.ExclusiveOutput(self.root, self.output)
        for name in ('../escape.png', '../../repo/page.html', '/absolute.png'):
            with self.assertRaises(ValueError):
                destination.write(name, b'unsafe')

    def test_brief_page_traversal_and_external_url_rejected(self):
        for page in ('../page.html', 'https://attacker.invalid/x.html', '/page.html', 'C:\\page.html'):
            self.document['briefs'][0]['page'] = page
            self.save_brief()
            with self.assertRaises(ValueError):
                agent.generation_request(self.root, self.brief, 'fixture', BASE)

    def test_delivery_hero_generation_rejected(self):
        self.document['briefs'][0]['operation'] = 'delivery_optimization_only'
        self.save_brief()
        with self.assertRaises(ValueError):
            agent.generation_request(self.root, self.brief, 'fixture', BASE)

    def test_layout_is_not_invented_from_proposed_brief_sizes(self):
        manifest = self.preview()
        self.assertEqual(manifest['layout_status'], 'MASTER_ONLY_LAYOUT_UNVERIFIED')
        self.assertEqual({item['width'] for item in manifest['optimization_outputs']}, {64})

    def test_measured_layout_variants_use_width_and_dpr(self):
        layout = self.directory/'layout.json'
        layout.write_text(json.dumps({'page': 'page.html', 'placement': '#fixture', 'evidence_reference': 'SYNTHETIC MEASUREMENT',
                                     'context_sha256': self.request.context_sha256,
                                     'samples': [{'width': 16, 'dpr': 1}, {'width': 16, 'dpr': 2}]}))
        manifest = self.preview(layout_file=layout)
        self.assertEqual({item['width'] for item in manifest['optimization_outputs']}, {16, 32})
        self.assertEqual({(item['width'],item['height']) for item in manifest['optimization_outputs']}, {(16,8), (32,16)})

    def test_layout_staleness_and_resource_limits(self):
        layout = self.directory/'layout.json'
        valid = {'page': 'page.html', 'placement': '#fixture', 'evidence_reference': 'fixture',
                 'context_sha256': self.request.context_sha256, 'samples': [{'width': 16, 'dpr': 1}]}
        for changes in ({'context_sha256': 'b'*64}, {'samples': [{'width': float('nan'), 'dpr': 1}]},
                        {'samples': [{'width': 1, 'dpr': 4}]}, {'samples': [{'width': w, 'dpr': 1} for w in (16,32,48,64)]}):
            layout.write_text(json.dumps({**valid, **changes}))
            with self.assertRaises(ValueError):
                agent.measured_widths(self.root, self.request, layout)

    def test_manifest_is_complete_pending_and_truthful(self):
        manifest = self.preview()
        self.assertEqual(manifest['approval_status'], 'PENDING')
        self.assertEqual(manifest['generation_status'], 'MOCK_ONLY_NOT_AI_GENERATED')
        self.assertIsNone(manifest['model'])
        for field in ('target_page', 'placement', 'brief_id', 'requested_dimensions', 'actual_image',
                      'rights_status', 'authenticity_status', 'optimization_outputs', 'artifacts'):
            self.assertIn(field, manifest)
        for name, digest in manifest['artifacts'].items():
            self.assertEqual(agent.digest(self.output/name), digest)
        self.assertTrue((self.output/'variants/preview.html').exists())

    def test_explicit_human_receipt_validation_does_not_publish(self):
        manifest = self.preview()
        receipt = self.receipt(manifest)
        result = agent.verify_generation_review(self.root, self.output, self.brief, receipt)
        self.assertEqual(result['publication'], 'NOT_AUTHORIZED')
        self.assertEqual(json.loads((self.output/'review-manifest.json').read_text())['approval_status'], 'PENDING')

    def test_missing_human_receipt_rejected(self):
        manifest = self.preview()
        for change in ({'status': 'PENDING'}, {'rights_reviewed': False}, {'review_reference': ''}):
            receipt = self.receipt(manifest)
            receipt.update(change)
            with self.assertRaises(ValueError):
                agent.verify_generation_review(self.root, self.output, self.brief, receipt)

    def test_stale_approval_after_page_or_brief_changes(self):
        manifest = self.preview()
        receipt = self.receipt(manifest)
        (self.root/'page.html').write_text('changed page')
        with self.assertRaisesRegex(ValueError, 'Stale approval'):
            agent.verify_generation_review(self.root, self.output, self.brief, receipt)

    def test_stale_approval_after_image_or_manifest_changes(self):
        manifest = self.preview()
        receipt = self.receipt(manifest)
        (self.output/'source/candidate.png').write_bytes(b'changed fixture')
        with self.assertRaisesRegex(ValueError, 'Stale approval'):
            agent.verify_generation_review(self.root, self.output, self.brief, receipt)
        (self.output/'review-manifest.json').write_text(json.dumps({**manifest, 'provider': 'forged'}))
        with self.assertRaisesRegex(ValueError, 'Stale approval'):
            agent.verify_generation_review(self.root, self.output, self.brief, receipt)

    def test_review_manifest_traversal_cannot_read_production(self):
        manifest = self.preview()
        manifest['artifacts'] = {'../../repo/page.html': agent.digest(self.root/'page.html')}
        (self.output/'review-manifest.json').write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, 'traversal'):
            agent.verify_generation_review(self.root, self.output, self.brief, self.receipt(manifest))

    def test_approval_rejects_hardlinked_artifact(self):
        manifest = self.preview()
        os.link(self.output/'source/candidate.png', self.directory/'alias.png')
        with self.assertRaisesRegex(ValueError, 'aliased'):
            agent.verify_generation_review(self.root, self.output, self.brief, self.receipt(manifest))

    def test_budget_estimate_does_not_claim_spend_cap(self):
        estimate = providers.OpenAIProvider().estimate(self.live_request())
        self.assertIsNone(estimate['usd'])
        self.assertTrue(estimate['advisory'])
        self.assertIn('no guaranteed spend cap', estimate['note'])

    def test_vendor_neutral_candidate_pipeline_preserves_unverified_provenance(self):
        mock = providers.MockProvider().generate(self.request)
        # An imported fixture has no actual API generation history.
        imported = providers.GenerationResult(mock.image, 'local-fixture-import', None, 'LOCAL_TEST_FIXTURE_NOT_AI_GENERATED')
        manifest = agent.prepare_generation_candidate(self.root, self.request, imported, self.output)
        self.assertEqual(manifest['provider'], 'local-fixture-import')
        self.assertEqual(manifest['generation_status'], imported.generation_status)
        self.assertEqual(manifest['authenticity_status'], 'UNVERIFIED_NEVER_TREAT_AS_DOCUMENTARY_PHOTOGRAPHY')
        self.assertEqual(manifest['approval_status'], 'PENDING')

    def test_duplicate_candidate_rejected_before_source_write(self):
        mock = providers.MockProvider().generate(self.request)
        inspected = providers.validate_image(mock.image, 64, 32, 'PNG')
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            agent.prepare_generation_candidate(self.root, self.request, mock, self.output, seen_images=[inspected])
        self.assertFalse((self.output/'source').exists())

    def test_changed_brief_invalidates_receipt(self):
        manifest = self.preview()
        receipt = self.receipt(manifest)
        self.document['briefs'][0]['prompt'] = 'Changed fixture prompt'
        self.save_brief()
        with self.assertRaisesRegex(ValueError, 'Stale approval'):
            agent.verify_generation_review(self.root, self.output, self.brief, receipt)

    def test_encoder_byte_budget_applies_to_cumulative_outputs(self):
        source = self.directory/'input'
        source.mkdir()
        Image.new('RGB', (64, 32), 'blue').save(source/'image.png')
        with self.assertRaisesRegex(ValueError, 'byte limit'):
            agent.optimize(source, 'image.png', self.output, [32,64], ['PNG'], max_output_bytes=1)
        self.assertFalse(list(self.output.glob('*.png')))

    def test_output_reparse_ancestry_rejected(self):
        original = Path.lstat
        def status(path, *args, **kwargs):
            value = original(path, *args, **kwargs)
            if path == self.directory:
                # Simulate Windows junction attributes without requiring symlink privileges.
                return Mock(st_file_attributes=0x400, st_mode=value.st_mode)
            return value
        with patch.object(Path, 'lstat', status), self.assertRaisesRegex(ValueError, 'reparse'):
            self.preview()
        self.assertFalse(self.output.exists())

    def test_hardlinked_review_manifest_rejected(self):
        manifest = self.preview()
        os.link(self.output/'review-manifest.json', self.directory/'manifest-alias.json')
        with self.assertRaisesRegex(ValueError, 'alias'):
            agent.verify_generation_review(self.root, self.output, self.brief, self.receipt(manifest))

    def test_provider_validation_failure_consumes_approval(self):
        body = b'{"data":[{"b64_json":"bm90IGltYWdl"}]}'
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'OFFLINE_TEST_SECRET'}), patch.object(providers, 'network_request', return_value=body) as transport:
            with self.assertRaisesRegex(ValueError, 'approval consumed'):
                self.invoke_live()
        self.assertEqual(transport.call_count, 1)

    def test_dry_run_rejects_production_output_plan(self):
        with self.assertRaises(ValueError):
            agent.generate_preview(self.root, self.request, self.root/'assets/generated')
        self.assertFalse((self.root/'assets').exists())

    def test_review_can_bind_nondefault_provider_settings(self):
        request = replace(self.request, quality='high', model='fixture-model')
        result = providers.MockProvider().generate(request)
        manifest = agent.prepare_generation_candidate(self.root, request, result, self.output)
        validated = agent.verify_generation_review(self.root, self.output, self.brief, self.receipt(manifest))
        self.assertEqual(validated['status'], 'REVIEW_RECEIPT_VALID')

    def test_pixel_duplicate_hash_includes_actual_geometry(self):
        metadata = []
        for width, height in ((64,32), (32,64)):
            stream = BytesIO()
            Image.new('RGB', (width,height), 'blue').save(stream, 'PNG')
            metadata.append(providers.validate_image(stream.getvalue(), width, height, 'PNG'))
        providers.reject_duplicates(metadata)
        self.assertNotEqual(metadata[0]['pixel_sha256'], metadata[1]['pixel_sha256'])

    def test_review_706_byte_webp_rejected_before_any_pillow_open(self):
        self.assertEqual(len(OVERSIZE_WEBP), 706)
        with patch.object(providers.Image, 'open', side_effect=AssertionError('Native canvas must not be allocated')) as opened:
            with self.assertRaisesRegex(ValueError, 'preflight'):
                providers.validate_image(OVERSIZE_WEBP, 64, 32, 'WEBP')
        opened.assert_not_called()

    def test_webp_extended_canvas_budget_and_consistency_before_open(self):
        stream = BytesIO(); Image.new('RGB', (64,32), 'white').save(stream, 'WEBP', lossless=True)
        chunks = stream.getvalue()[12:]
        for width, height in ((4096,4096), (32,32)):
            header = b'\0'*4 + (width-1).to_bytes(3,'little') + (height-1).to_bytes(3,'little')
            body = b'WEBPVP8X' + struct.pack('<I',10) + header + chunks
            data = b'RIFF' + struct.pack('<I',len(body)) + body
            with patch.object(providers.Image,'open',side_effect=AssertionError('No native open')), self.assertRaises(ValueError):
                providers.validate_image(data,64,32,'WEBP')

    def test_webp_lossy_frame_budget_before_open(self):
        stream = BytesIO(); Image.new('RGB',(64,32),'white').save(stream,'WEBP')
        data = bytearray(stream.getvalue())
        self.assertEqual(data[12:16],b'VP8 ')
        data[26:30] = struct.pack('<HH',4096,4096)
        with patch.object(providers.Image,'open',side_effect=AssertionError('No native open')), self.assertRaisesRegex(ValueError,'preflight'):
            providers.validate_image(bytes(data),64,32,'WEBP')

    def test_webp_invalid_lengths_duplicates_flags_and_version_before_open(self):
        stream=BytesIO(); Image.new('RGB',(64,32),'white').save(stream,'WEBP',lossless=True)
        valid=stream.getvalue()
        version=bytearray(valid); version[24] |= 0xe0
        duplicated=b'RIFF'+struct.pack('<I',len(valid[12:])*2+4)+b'WEBP'+valid[12:]*2
        animated_header=b'\x02\0\0\0'+(63).to_bytes(3,'little')+(31).to_bytes(3,'little')
        body=b'WEBPVP8X'+struct.pack('<I',10)+animated_header+valid[12:]
        animated=b'RIFF'+struct.pack('<I',len(body))+body
        for damaged in (valid[:-1],valid+b'x',bytes(version),duplicated,animated):
            with self.subTest(data=damaged[:30]), patch.object(providers.Image,'open',side_effect=AssertionError('No native open')),self.assertRaises(ValueError):
                providers.validate_image(damaged,64,32,'WEBP')

    def test_png_dimensions_checksum_and_animation_rejected_before_open(self):
        stream=BytesIO(); Image.new('RGB',(64,32),'white').save(stream,'PNG')
        oversized=bytearray(stream.getvalue());oversized[16:24]=struct.pack('!II',4096,4096)
        bad_crc=bytes(oversized)
        oversized[29:33]=struct.pack('!I',zlib.crc32(oversized[12:29]))
        animated=BytesIO();Image.new('RGB',(64,32),'red').save(animated,'PNG',save_all=True,append_images=[Image.new('RGB',(64,32),'blue')])
        for data in (bad_crc,bytes(oversized),animated.getvalue()):
            with patch.object(providers.Image,'open',side_effect=AssertionError('No image open')),self.assertRaises(ValueError):
                providers.validate_image(data,64,32,'PNG')

    def test_jpeg_baseline_and_progressive_preflight_then_actual_decode(self):
        for progressive in (False,True):
            stream=BytesIO();Image.new('RGB',(64,32),'blue').save(stream,'JPEG',progressive=progressive)
            self.assertEqual(providers.preflight_image(stream.getvalue(),'JPEG'),(64,32))
            self.assertEqual(providers.validate_image(stream.getvalue(),64,32,'JPEG')['format'],'JPEG')

    def test_jpeg_oversized_ambiguous_and_multipicture_headers_before_open(self):
        stream=BytesIO();Image.new('RGB',(64,32),'blue').save(stream,'JPEG')
        valid=stream.getvalue();offset=valid.index(b'\xff\xc0')
        oversized=bytearray(valid);oversized[offset+5:offset+9]=struct.pack('!HH',4096,4096)
        size=int.from_bytes(valid[offset+2:offset+4],'big')
        duplicate=valid[:offset]+valid[offset:offset+size+2]+valid[offset:]
        multipicture=valid[:2]+b'\xff\xe2\0\x06MPF\0'+valid[2:]
        for data in (bytes(oversized),duplicate,multipicture,valid[:-2]):
            with patch.object(providers.Image,'open',side_effect=AssertionError('No decoder open')),self.assertRaises(ValueError):
                providers.validate_image(data,64,32,'JPEG')

    def test_unknown_format_cannot_load_an_unchecked_plugin(self):
        with patch.object(providers.Image,'open',side_effect=AssertionError('No unchecked plugin')),self.assertRaises(ValueError):
            providers.validate_image(b'GIF89a'+b'\0'*100,64,32,'GIF')

    def run_frame(self, mode, timeout=2):
        return providers._supervised(frame_fixture,(mode,),limit=64,timeout=timeout,
                                    expected_kind=providers.FRAME_JSON if mode=='json' else providers.FRAME_BYTES,
                                    timeout_message='Synthetic elapsed deadline',failure='Synthetic worker failed')

    def test_supervised_normal_bytes_and_json_complete(self):
        self.assertEqual(self.run_frame('normal'),b'complete')
        self.assertEqual(self.run_frame('json'),{'complete':True})

    def test_supervised_stall_partial_and_committed_stall_deadlines(self):
        for mode in ('stall','partial-stall','committed-stall'):
            marker=self.directory/(mode+'.marker')
            started=time.monotonic()
            with self.assertRaises(TimeoutError):
                providers._supervised(frame_fixture,(mode,str(marker)),limit=64,timeout=1,
                    expected_kind=providers.FRAME_BYTES,timeout_message='Synthetic elapsed deadline',failure='Synthetic worker failed')
            self.assertTrue(marker.exists(),'Actual child must enter the tested stalled state')
            self.assertLess(time.monotonic()-started,3.5)  # Includes bounded termination/reaping grace.

    def test_supervised_late_response_never_accepted(self):
        with self.assertRaises(TimeoutError):
            self.run_frame('late',timeout=.5)

    def test_supervised_partial_exit_and_oversized_frame_rejected(self):
        for mode in ('partial-exit','oversize'):
            with self.subTest(mode=mode),self.assertRaisesRegex(ValueError,'frame'):
                self.run_frame(mode)

    def test_supervised_worker_crash_rejected(self):
        with self.assertRaisesRegex(ValueError,'worker failed'):
            self.run_frame('crash')

    def test_supervised_timeout_reaps_child_and_closes_mapping(self):
        original=providers.SharedMemory;names=[]
        def mapping(*args,**kwargs):
            area=original(*args,**kwargs);names.append(area.name);return area
        before={child.pid for child in multiprocessing.active_children()}
        with patch.object(providers,'SharedMemory',side_effect=mapping),self.assertRaises(TimeoutError):
            self.run_frame('stall',timeout=.5)
        self.assertEqual({child.pid for child in multiprocessing.active_children()},before)
        self.assertEqual(len(names),2)
        for name in names:
            with self.assertRaises(FileNotFoundError):original(name=name)

    def test_supervised_success_closes_mapping(self):
        original=providers.SharedMemory;names=[]
        def mapping(*args,**kwargs):
            area=original(*args,**kwargs);names.append(area.name);return area
        with patch.object(providers,'SharedMemory',side_effect=mapping):self.assertEqual(self.run_frame('normal'),b'complete')
        for name in names:
            with self.assertRaises(FileNotFoundError):original(name=name)

    def test_supervised_failed_start_closes_mapping_and_process(self):
        context=Mock();process=context.Process.return_value
        process.start.side_effect=OSError('Synthetic failed start')
        original=providers.SharedMemory;names=[]
        def mapping(*args,**kwargs):
            area=original(*args,**kwargs);names.append(area.name);return area
        with patch.object(providers.multiprocessing,'get_context',return_value=context),patch.object(providers,'SharedMemory',side_effect=mapping),self.assertRaises(OSError):
            self.run_frame('normal')
        process.close.assert_called_once()
        for name in names:
            with self.assertRaises(FileNotFoundError):original(name=name)

    def test_worker_inputs_use_bounded_frames_not_bulk_spawn_arguments(self):
        values=(b'opaque fixture bytes',16,[32,64],None,'fixture')
        self.assertEqual(providers._unpack_args(providers._pack_args(values)),[b'opaque fixture bytes',16,[32,64],None,'fixture'])
        for args in ((b'a',b'b'),({'arbitrary':True},)):
            with self.assertRaises(ValueError):providers._pack_args(args)
        with patch.object(providers,'MAX_JSON_BYTES',1),self.assertRaises(ValueError):providers._pack_args((b'large',))

    def test_frame_checksum_and_kind_cannot_be_forged(self):
        for kind,digest in ((providers.FRAME_BYTES,b'\0'*32),(99,hashlib.sha256(b'complete').digest())):
            buffer=bytearray(providers.FRAME.size+64)
            buffer[:providers.FRAME.size]=providers.FRAME.pack(providers.FRAME_MAGIC,kind,8,digest)
            buffer[providers.FRAME.size:providers.FRAME.size+8]=b'complete'
            with self.assertRaises(ValueError):providers._read_frame(buffer,64,providers.FRAME_BYTES,'failure')

    def save_layout(self, changes=None):
        self.layout_document={'page':self.request.page,'placement':self.request.placement,
            'context_sha256':self.request.context_sha256,'evidence_reference':'SYNTHETIC CURRENT SLOT',
            'samples':[{'width':16,'dpr':1},{'width':16,'dpr':2}]}
        self.layout_document.update(changes or {})
        self.layout=self.directory/'layout.json'
        self.layout.write_text(json.dumps(self.layout_document))
        return self.layout

    def test_layout_unchanged_evidence_and_receipt_fingerprint_validate(self):
        manifest=self.preview(layout_file=self.save_layout());receipt=self.receipt(manifest)
        expected=providers.sha256(providers.canonical(self.layout_document))
        self.assertEqual(manifest['layout_evidence']['sha256'],expected)
        self.assertEqual(manifest['layout_evidence']['document'],self.layout_document)
        self.assertEqual(receipt['layout_evidence_sha256'],expected)
        result=agent.verify_generation_review(self.root,self.output,self.brief,receipt,layout_file=self.layout)
        self.assertEqual(result['publication'],'NOT_AUTHORIZED')

    def test_layout_changed_measurements_invalidate_receipt(self):
        manifest=self.preview(layout_file=self.save_layout());receipt=self.receipt(manifest)
        self.layout_document['samples']=[{'width':32,'dpr':1}]
        self.layout.write_text(json.dumps(self.layout_document))
        with self.assertRaisesRegex(ValueError,'layout evidence'):
            agent.verify_generation_review(self.root,self.output,self.brief,receipt,layout_file=self.layout)

    def test_layout_changed_source_reference_invalidate_receipt(self):
        manifest=self.preview(layout_file=self.save_layout());receipt=self.receipt(manifest)
        self.layout_document['evidence_reference']='CHANGED SYNTHETIC SOURCE'
        self.layout.write_text(json.dumps(self.layout_document))
        with self.assertRaisesRegex(ValueError,'layout evidence'):
            agent.verify_generation_review(self.root,self.output,self.brief,receipt,layout_file=self.layout)

    def test_layout_missing_current_evidence_rejected(self):
        manifest=self.preview(layout_file=self.save_layout());receipt=self.receipt(manifest)
        with self.assertRaisesRegex(ValueError,'layout evidence'):
            agent.verify_generation_review(self.root,self.output,self.brief,receipt)
        self.layout.unlink()
        with self.assertRaises(OSError):
            agent.verify_generation_review(self.root,self.output,self.brief,receipt,layout_file=self.layout)

    def test_layout_reordered_json_keys_remain_equivalent(self):
        manifest=self.preview(layout_file=self.save_layout());receipt=self.receipt(manifest)
        reordered=dict(reversed(list(self.layout_document.items())))
        reordered['samples']=[dict(reversed(list(sample.items()))) for sample in reordered['samples']]
        self.layout.write_text(json.dumps(reordered,indent=4))
        self.assertEqual(agent.verify_generation_review(self.root,self.output,self.brief,receipt,layout_file=self.layout)['status'],'REVIEW_RECEIPT_VALID')

    def test_layout_absence_is_explicit_and_old_receipts_rejected(self):
        manifest=self.preview();receipt=self.receipt(manifest)
        self.assertEqual(manifest['layout_evidence'],{'state':'ABSENT','sha256':None,'document':None})
        for key in ('schema_version','layout_evidence_state','layout_evidence_sha256'):
            stale={name:value for name,value in receipt.items() if name!=key}
            with self.subTest(missing=key),self.assertRaisesRegex(ValueError,'Stale'):
                agent.verify_generation_review(self.root,self.output,self.brief,stale)

    def test_layout_added_after_absent_review_rejected(self):
        manifest=self.preview();receipt=self.receipt(manifest);self.save_layout()
        with self.assertRaisesRegex(ValueError,'layout evidence'):
            agent.verify_generation_review(self.root,self.output,self.brief,receipt,layout_file=self.layout)

    def test_layout_changed_artifact_hash_still_rejected(self):
        manifest=self.preview(layout_file=self.save_layout());receipt=self.receipt(manifest)
        (self.output/'source/candidate.png').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'artifact changed'):
            agent.verify_generation_review(self.root,self.output,self.brief,receipt,layout_file=self.layout)

    def test_layout_malformed_duplicate_and_unknown_fields_rejected(self):
        self.save_layout()
        invalid=[{**self.layout_document,'evidence_reference':False},
                 {**self.layout_document,'samples':[{'width':True,'dpr':1}]},
                 {**self.layout_document,'samples':[{'width':16,'dpr':1,'unknown':0}]},
                 {**self.layout_document,'unknown':0},
                 {**self.layout_document,'samples':[None]}]
        for document in invalid:
            self.layout.write_text(json.dumps(document))
            with self.assertRaises(ValueError):agent.layout_evidence(self.request,self.layout)
        self.layout.write_text(json.dumps(self.layout_document)[:-1]+',"evidence_reference":"DUPLICATE"}')
        with self.assertRaisesRegex(ValueError,'duplicate'):agent.layout_evidence(self.request,self.layout)

    def test_layout_inconsistent_manifest_fingerprint_and_old_schema_rejected(self):
        manifest=self.preview(layout_file=self.save_layout())
        for change in ('fingerprint','old_schema'):
            modified=json.loads(json.dumps(manifest))
            if change=='fingerprint':modified['layout_evidence']['sha256']='0'*64
            else:modified['schema_version']=2
            (self.output/'review-manifest.json').write_text(json.dumps(modified))
            with self.assertRaises(ValueError):
                agent.verify_generation_review(self.root,self.output,self.brief,self.receipt(modified),layout_file=self.layout)

    def test_layout_changed_between_plan_and_preparation_fails_closed(self):
        self.save_layout()
        plan=agent.generate_preview(self.root,self.request,self.output,layout_file=self.layout)
        self.layout_document['evidence_reference']='CHANGED BETWEEN READS'
        self.layout.write_text(json.dumps(self.layout_document))
        with self.assertRaisesRegex(ValueError,'changed before preparation'):
            agent.prepare_generation_candidate(self.root,self.request,providers.MockProvider().generate(self.request),self.output,layout_file=self.layout,plan=plan)
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
