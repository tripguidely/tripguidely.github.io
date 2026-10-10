"""Optional providers. Importing this module never reads credentials or uses the network.

The CLI exposes offline planning/mock previews only. See docs/image-seo-agent-v2.md.
"""
from __future__ import annotations

import base64
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import http.client
import importlib.util
from io import BytesIO
import json
import math
import multiprocessing
from multiprocessing.connection import wait
from multiprocessing.shared_memory import SharedMemory
import os
from pathlib import Path, PurePosixPath
import re
import ssl
import struct
import threading
import time
from typing import Protocol
import warnings
import zlib

from PIL import Image, ImageDraw, ImageOps

MODEL = 'gpt-image-2.5-flare-2026-09-08'
HOST = 'api.openai.com'
ENDPOINT = '/v1/images/generations'
MAX_PROMPT_BYTES = 8000
MAX_JSON_BYTES = 24 * 1024 * 1024
MAX_IMAGE_BYTES = 16 * 1024 * 1024
MAX_PIXELS = 4_194_304
MAX_EDGE = 2560
MAX_OUTPUT_BYTES = 64 * 1024 * 1024
MAX_INPUT_BYTES = 2 * 1024 * 1024
FRAMEWORK_MAX_IMAGES = 3
APPROVED_RUN_LIMIT = 1
CONNECT_SECONDS = 10
REQUEST_SECONDS = 180
WORKER_SECONDS = 45
MAX_CONTAINER_PARTS = 4096
FRAME = struct.Struct('!4sBI32s')
FRAME_MAGIC = b'ISV2'
FRAME_ERROR, FRAME_BYTES, FRAME_JSON, FRAME_ARGS = 0, 1, 2, 3
PAID_CONFIRMATION = 'I AUTHORIZE ONE PAID IMAGE REQUEST'
_live_lock = threading.Lock()


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def strict_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Ambiguous duplicate JSON key')
            result[key] = value
        return result
    def constant(value):
        raise ValueError('Nonfinite JSON number forbidden')
    try:
        return json.loads(data, object_pairs_hook=pairs, parse_constant=constant)
    except (UnicodeError, RecursionError) as error:
        raise ValueError('Invalid JSON input') from error


def read_bounded(path, limit=MAX_INPUT_BYTES):
    with Path(path).open('rb') as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError('Input exceeds byte limit')
    return data


def local_page(root, name):
    if not isinstance(name, str) or '\\' in name or ':' in name:
        raise ValueError('A relative local page path is required')
    parts = PurePosixPath(name)
    if parts.is_absolute() or '..' in parts.parts or parts.suffix != '.html':
        raise ValueError('Page traversal or unsupported page path')
    path = root.resolve() / parts
    for parent in (path, *path.parents):
        if parent == root.resolve().parent:
            break
        if os.path.lexists(parent) and (parent.is_symlink() or getattr(parent.lstat(), 'st_file_attributes', 0) & 0x400):
            raise ValueError('Page aliases are forbidden')
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Page escapes repository')
    return path


def run_count(count):
    if type(count) is not int or not 1 <= count <= FRAMEWORK_MAX_IMAGES:
        raise ValueError('Framework image count must be 1..3')
    if count > APPROVED_RUN_LIMIT:
        raise ValueError('Initial approved run limit is one image')


@dataclass(frozen=True)
class GenerationRequest:
    brief_id: str
    page: str
    placement: str
    prompt: str
    width: int
    height: int
    base_revision: str
    context_sha256: str
    model: str = MODEL
    output_format: str = 'png'
    quality: str = 'medium'
    count: int = 1

    def validate(self):
        run_count(self.count)
        if type(self.width) is not int or type(self.height) is not int:
            raise ValueError('Integer dimensions required')
        if min(self.width, self.height) < 16 or max(self.width, self.height) > MAX_EDGE or self.width * self.height > MAX_PIXELS:
            raise ValueError('Requested dimensions exceed limits')
        if self.width % 16 or self.height % 16 or not 1/3 <= self.width / self.height <= 3:
            raise ValueError('Dimensions must be multiples of 16 with aspect ratio 1:3..3:1')
        if not isinstance(self.prompt, str) or not self.prompt.strip() or len(self.prompt.encode('utf-8')) > MAX_PROMPT_BYTES:
            raise ValueError('Prompt missing or too large')
        if self.output_format not in ('png', 'jpeg', 'webp') or self.quality not in ('low', 'medium', 'high'):
            raise ValueError('Unsupported format/quality')
        if not re.fullmatch('[0-9a-f]{40}', self.base_revision) or not re.fullmatch('[0-9a-f]{64}', self.context_sha256):
            raise ValueError('Exact base and context hashes required')
        if not re.fullmatch('[a-z0-9-]{1,100}', self.brief_id):
            raise ValueError('Invalid brief identifier')
        if not isinstance(self.page, str) or '\\' in self.page or ':' in self.page or PurePosixPath(self.page).is_absolute() or '..' in PurePosixPath(self.page).parts or not self.page.endswith('.html'):
            raise ValueError('Relative local HTML page required')
        if not isinstance(self.model, str) or len(self.model) > 100:
            raise ValueError('Model identifier missing or too large')
        if not isinstance(self.placement, str) or not self.placement or len(self.placement.encode('utf-8')) > 1000:
            raise ValueError('Placement missing or too large')

    def fingerprint(self):
        self.validate()
        return sha256(canonical(asdict(self)))


@dataclass(frozen=True)
class GenerationResult:
    image: bytes
    provider: str
    model: str | None
    generation_status: str


class Provider(Protocol):
    def capabilities(self) -> dict: ...
    def estimate(self, request: GenerationRequest) -> dict: ...
    def generate(self, request: GenerationRequest, **authorization) -> GenerationResult: ...


class MockProvider:
    """Deterministic synthetic shapes, not AI content or a simulation of provider quality."""
    def capabilities(self):
        return {'provider': 'offline-mock', 'network': False, 'max_images': 1, 'formats': ['png', 'jpeg', 'webp']}

    def estimate(self, request):
        request.validate()
        return {'usd': 0, 'advisory': True, 'network': False}

    def generate(self, request, **authorization):
        request.validate()
        seed = bytes.fromhex(request.fingerprint())
        image = Image.new('RGB', (request.width, request.height), tuple(seed[:3]))
        draw = ImageDraw.Draw(image)
        draw.rectangle((request.width//4, request.height//4, 3*request.width//4, 3*request.height//4), fill=tuple(seed[3:6]))
        encoded = BytesIO()
        image.save(encoded, {'png': 'PNG', 'jpeg': 'JPEG', 'webp': 'WEBP'}[request.output_format])
        return GenerationResult(encoded.getvalue(), 'offline-mock', None, 'MOCK_ONLY_NOT_AI_GENERATED')


def validate_paid(request, approval, confirmation):
    request.validate()
    if request.model != MODEL or request.width * request.height < 655_360 or request.width * request.height > 2560 * 1440:
        raise ValueError('Live adapter supports the documented snapshot and conservative standard dimensions only')
    if confirmation != PAID_CONFIRMATION or not isinstance(approval, dict):
        raise ValueError('Explicit paid-use approval and confirmation required')
    expected = {'operation': 'PAID_IMAGE_GENERATION', 'provider': 'openai', 'request_sha256': request.fingerprint(),
                'base_revision': request.base_revision, 'max_requests': 1, 'max_images': 1,
                'budget_is_advisory': True, 'status': 'APPROVED'}
    if any(approval.get(k) != v or type(approval.get(k)) is not type(v) for k, v in expected.items()):
        raise ValueError('Paid approval does not match this exact request')
    if not re.fullmatch('[0-9a-f]{32}', str(approval.get('approval_id', ''))):
        raise ValueError('Approval needs a unique 32-character hexadecimal ID')
    if not isinstance(approval.get('review_reference'), str) or not 1 <= len(approval['review_reference']) <= 200:
        raise ValueError('Owner review reference required')
    budget = approval.get('advisory_budget_usd')
    if type(budget) not in (int, float) or not math.isfinite(budget) or not 0 < budget <= 1000:
        raise ValueError('Positive advisory budget required; it is not a spend cap')
    try:
        start, end = (datetime.fromisoformat(approval[k]) for k in ('approved_at', 'expires_at'))
        now = datetime.now(timezone.utc)
        if start.utcoffset() is None or end.utcoffset() is None or not start <= now < end or not 0 < (end-start).total_seconds() <= 86400:
            raise ValueError('Paid approval expired or has invalid dates')
    except (KeyError, TypeError) as error:
        raise ValueError('Timezone-aware paid approval dates required') from error


def _post(payload, key):
    """One TLS POST; no proxy discovery, redirects, URL results, SDK retries or body logging."""
    started = time.monotonic()
    connection = http.client.HTTPSConnection(HOST, timeout=CONNECT_SECONDS, context=ssl.create_default_context())
    try:
        connection.connect()
        connection.sock.settimeout(max(0.01, REQUEST_SECONDS - (time.monotonic()-started)))
        connection.request('POST', ENDPOINT, body=payload,
                           headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
        response = connection.getresponse()
        if response.status != 200:
            raise ValueError('Provider returned HTTP ' + str(response.status) + '; no retry, billing unknown')
        if response.getheader('Content-Encoding', 'identity') != 'identity':
            raise ValueError('Compressed provider responses are unsupported')
        length = response.getheader('Content-Length')
        if length and (not length.isdecimal() or int(length) > MAX_JSON_BYTES):
            raise ValueError('Provider response exceeds byte limit')
        chunks, total = [], 0
        while True:
            remaining = REQUEST_SECONDS - (time.monotonic()-started)
            if remaining <= 0:
                raise TimeoutError('Provider deadline reached; billing unknown')
            if connection.sock is not None:
                connection.sock.settimeout(remaining)
            chunk = response.read1(min(65536, MAX_JSON_BYTES + 1 - total))
            total += len(chunk)
            if total > MAX_JSON_BYTES:
                raise ValueError('Provider response exceeds byte limit')
            if not chunk:
                break
            chunks.append(chunk)
        return b''.join(chunks)
    finally:
        connection.close()


def decode_response(body):
    if not isinstance(body, bytes) or len(body) > MAX_JSON_BYTES:
        raise ValueError('Provider response exceeds byte limit or has wrong type')
    try:
        response = json.loads(body)
        rows = response['data']
        if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict) or 'url' in rows[0]:
            raise ValueError('Exactly one base64 image required; URL outputs forbidden')
        encoded = rows[0]['b64_json']
        if not isinstance(encoded, str) or len(encoded) > 4 * ((MAX_IMAGE_BYTES + 2)//3):
            raise ValueError('Encoded image exceeds byte limit')
        image = base64.b64decode(encoded, validate=True)
        if not image or len(image) > MAX_IMAGE_BYTES:
            raise ValueError('Decoded image exceeds byte limit')
        return image
    except (KeyError, TypeError, UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError('Invalid provider response') from error


def _write_frame(buffer, limit, kind, payload):
    """Commit a bounded lock-free result only after all payload bytes are written."""
    if kind not in (FRAME_ERROR, FRAME_BYTES, FRAME_JSON, FRAME_ARGS) or not isinstance(payload, bytes) or len(payload) > limit:
        raise ValueError('Worker result exceeds frame limit')
    view = memoryview(buffer).cast('B')
    try:
        view[FRAME.size:FRAME.size+len(payload)] = payload
        view[:FRAME.size] = FRAME.pack(FRAME_MAGIC, kind, len(payload), hashlib.sha256(payload).digest())
    finally:
        view.release()


def _read_frame(buffer, limit, expected_kind, failure):
    # Called only after the producer has exited. No recv, unpickle, locks or stream framing.
    view = memoryview(buffer).cast('B')
    try:
        magic, kind, length, digest = FRAME.unpack(bytes(view[:FRAME.size]))
        if magic != FRAME_MAGIC or kind not in (FRAME_ERROR, expected_kind) or length > limit:
            raise ValueError('Invalid or incomplete worker frame')
        payload = bytes(view[FRAME.size:FRAME.size+length])
    finally:
        view.release()
    if hashlib.sha256(payload).digest() != digest:
        raise ValueError('Incomplete or corrupt worker frame')
    if kind == FRAME_ERROR:
        raise ValueError(failure)
    if kind == FRAME_JSON:
        try:
            return json.loads(payload)
        except (ValueError, UnicodeError, RecursionError):
            raise ValueError('Invalid worker JSON result') from None
    return payload


def _pack_args(args):
    binary = []
    def encode(value):
        if isinstance(value, bytes):
            if binary or len(value) > MAX_JSON_BYTES:
                raise ValueError('One bounded binary worker input required')
            binary.append(value)
            return {'binary': True}
        if isinstance(value, (tuple, list)):
            return [encode(item) for item in value]
        if value is None or type(value) in (str, int, float, bool):
            return value
        raise ValueError('Unsupported worker input type')
    metadata = canonical(encode(args))
    if len(metadata) > MAX_INPUT_BYTES:
        raise ValueError('Worker input metadata exceeds limit')
    return struct.pack('!I', len(metadata)) + metadata + (binary[0] if binary else b'')


def _unpack_args(payload):
    if len(payload) < 4:
        raise ValueError('Incomplete worker input frame')
    length = int.from_bytes(payload[:4], 'big')
    if length > MAX_INPUT_BYTES or 4 + length > len(payload) or len(payload) - 4 - length > MAX_JSON_BYTES:
        raise ValueError('Worker input frame exceeds limits')
    metadata = strict_json(payload[4:4+length])
    binary, used = payload[4+length:], False
    def decode(value):
        nonlocal used
        if isinstance(value, dict):
            if set(value) != {'binary'} or value['binary'] is not True or used:
                raise ValueError('Ambiguous worker binary input')
            used = True
            return binary
        if isinstance(value, list):
            return [decode(item) for item in value]
        if value is None or type(value) in (str, int, float, bool):
            return value
        raise ValueError('Unsupported worker input type')
    if not isinstance(metadata, list):
        raise ValueError('Worker argument list required')
    result = decode(metadata)
    if binary and not used:
        raise ValueError('Unexpected binary input bytes')
    return result


def _produce_frame(name, input_name, target, limit):
    source = SharedMemory(name=input_name)
    try:
        args = _unpack_args(_read_frame(source.buf, source.size - FRAME.size, FRAME_ARGS, 'Invalid worker inputs'))
    finally:
        source.close()
    area = SharedMemory(name=name)
    try:
        target(area.buf, limit, *args)
    finally:
        area.close()


def _supervised(target, args, *, limit, timeout, expected_kind, timeout_message, failure):
    """Fixed shared frame; accept only a fully exited worker within an elapsed deadline."""
    if type(limit) is not int or not 0 < limit <= MAX_JSON_BYTES or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('Invalid worker frame/deadline limits')
    deadline = time.monotonic() + timeout
    context = multiprocessing.get_context('spawn')
    area = source = process = None
    started = False
    def remaining():
        value = deadline - time.monotonic()
        if value <= 0:
            raise TimeoutError(timeout_message)
        return value
    try:
        inputs = _pack_args(args)
        remaining()
        area = SharedMemory(create=True, size=FRAME.size + limit)  # No producer-held synchronization lock.
        source = SharedMemory(create=True, size=FRAME.size + len(inputs))
        _write_frame(source.buf, len(inputs), FRAME_ARGS, inputs)
        # Spawn carries small control values only, never large images or credentials in bootstrap pipes.
        process = context.Process(target=_produce_frame, args=(area.name, source.name, target, limit))
        remaining()
        process.start()
        started = True
        if not wait([process.sentinel], timeout=remaining()):
            raise TimeoutError(timeout_message)
        remaining()
        process.join(timeout=0)  # The sentinel is signaled only on process exit.
        if process.exitcode != 0:
            raise ValueError(failure)
        value = _read_frame(area.buf, limit, expected_kind, failure)
        remaining()  # Copies/parsing are bounded; late results are never accepted.
        return value
    finally:
        try:
            if started:
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=1)
                    if process.is_alive():
                        process.kill()
                        process.join(timeout=1)
                else:
                    process.join(timeout=0)
                if process.is_alive():
                    raise RuntimeError('Unable to reap worker after bounded cleanup')
            if process is not None:
                process.close()  # Close the process/sentinel handle, including failed starts.
        finally:
            for mapping in (source, area):
                if mapping is not None:
                    mapping.close()
                    mapping.unlink()  # Windows removes it when its final handle closes.


def _transport_worker(buffer, limit, payload, key):
    try:
        _write_frame(buffer, limit, FRAME_BYTES, _post(payload, key))
    except Exception:
        _write_frame(buffer, limit, FRAME_ERROR, b'')


def network_request(payload, key):
    """Includes startup, request, transfer and result acceptance; no retry on termination."""
    return _supervised(_transport_worker, (payload, key), limit=MAX_JSON_BYTES,
                       timeout=REQUEST_SECONDS, expected_kind=FRAME_BYTES,
                       timeout_message='Provider deadline exceeded; billing unknown',
                       failure='Provider request failed; billing unknown')


class OpenAIProvider:
    """Optional adapter, not exposed as a live CLI command. No account access is assumed."""
    def capabilities(self):
        return {'provider': 'openai', 'model': MODEL, 'max_images': 1, 'formats': ['png', 'jpeg', 'webp'],
                'live_tested': False, 'endpoint': 'https://' + HOST + ENDPOINT}

    def estimate(self, request):
        request.validate()
        return {'usd': None, 'advisory': True, 'note': 'Image token use unknown; no guaranteed spend cap or account access verification'}

    def generate(self, request, *, approval=None, confirmation=None, root=None, ledger=None):
        validate_paid(request, approval, confirmation)  # Before reading credentials or touching a socket.
        if root is None or ledger is None:
            raise ValueError('A private external persistent approval ledger is required')
        if not _live_lock.acquire(blocking=False):
            raise ValueError('Only one concurrent live request is permitted')
        try:
            reservation = agent_module().ExclusiveOutput(Path(root), Path(ledger) / ('paid-' + approval['approval_id']))
            reservation.write('attempt.json', canonical({'request_sha256': request.fingerprint(),
                                                        'review_reference': approval['review_reference'], 'billing': 'UNKNOWN'}))
            # A failed/ambiguous attempt consumes the approval too. Never retry automatically.
            key = os.environ.get('OPENAI_API_KEY')
            if not key or not key.strip():
                raise ValueError('OPENAI_API_KEY required for an explicitly authorized live request')
            if any(ord(c) < 33 or ord(c) > 126 for c in key) or len(key) > 1024:
                raise ValueError('Invalid credential format')
            payload = canonical({'model': MODEL, 'prompt': request.prompt, 'n': 1,
                                 'size': f'{request.width}x{request.height}', 'quality': request.quality,
                                 'output_format': request.output_format, 'background': 'opaque'})
            try:
                image = bounded_worker('response', (network_request(payload, key),))
                bounded_worker('validate', (image, request.width, request.height,
                                           {'png': 'PNG', 'jpeg': 'JPEG', 'webp': 'WEBP'}[request.output_format]))
            except Exception:
                # Do not expose exception messages, HTTP bodies, prompts or credentials.
                raise ValueError('Provider attempt failed; approval consumed, billing unknown; no automatic retry') from None
            return GenerationResult(image, 'openai', MODEL, 'PROVIDER_RESPONSE_RECEIVED_UNREVIEWED')
        finally:
            _live_lock.release()


def _canvas(width, height):
    if min(width, height) < 1 or max(width, height) > MAX_EDGE or width * height > MAX_PIXELS:
        raise ValueError('Decoded image dimensions exceed limits (preflight)')
    return width, height


def _png_canvas(data):
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('Invalid PNG signature')
    position, count, dimensions, color = 8, 0, None, None
    palette, image_data, data_ended = False, False, False
    view = memoryview(data)
    while position < len(data):
        count += 1
        if count > MAX_CONTAINER_PARTS or position + 12 > len(data):
            raise ValueError('Invalid PNG chunk framing')
        size = int.from_bytes(data[position:position+4], 'big')
        kind = data[position+4:position+8]
        end = position + 12 + size
        if end > len(data) or not re.fullmatch(b'[A-Za-z]{4}', kind) or not 65 <= kind[2] <= 90:
            raise ValueError('Invalid PNG chunk/header')
        if zlib.crc32(view[position+4:end-4]) != int.from_bytes(data[end-4:end], 'big'):
            raise ValueError('Invalid PNG checksum')
        payload = view[position+8:end-4]
        if count == 1 and (kind != b'IHDR' or size != 13):
            raise ValueError('PNG requires one leading IHDR')
        if kind == b'IHDR':
            if dimensions is not None or size != 13:
                raise ValueError('Ambiguous PNG dimensions')
            width, height, depth, color, compression, filtering, interlace = struct.unpack('!IIBBBBB', payload)
            dimensions = _canvas(width, height)
            allowed = {0: (1,2,4,8,16), 2: (8,16), 3: (1,2,4,8), 4: (8,16), 6: (8,16)}
            if depth not in allowed.get(color, ()) or compression != 0 or filtering != 0 or interlace not in (0,1):
                raise ValueError('Unsupported PNG header')
        elif kind in (b'acTL', b'fcTL', b'fdAT'):
            raise ValueError('Animated PNG is forbidden before decoding')
        elif kind == b'PLTE':
            if palette or image_data or not 0 < size <= 768 or size % 3 or color in (0,4):
                raise ValueError('Invalid PNG palette')
            palette = True
        elif kind == b'IDAT':
            if data_ended or (color == 3 and not palette):
                raise ValueError('Invalid PNG image-data order')
            image_data = True
        elif kind == b'IEND':
            if size or not image_data or end != len(data):
                raise ValueError('Incomplete PNG or trailing data')
            return dimensions
        else:
            if 65 <= kind[0] <= 90:
                raise ValueError('Unknown critical PNG chunk')
            if image_data:
                data_ended = True
        position = end
    raise ValueError('Incomplete PNG container')


def _webp_canvas(data):
    if len(data) < 20 or data[:4] != b'RIFF' or data[8:12] != b'WEBP' or int.from_bytes(data[4:8], 'little') + 8 != len(data):
        raise ValueError('Invalid WebP RIFF framing')
    position, count, canvas, pixels, flags, alpha = 12, 0, None, None, 0, False
    seen = set()
    while position < len(data):
        count += 1
        if count > MAX_CONTAINER_PARTS or position + 8 > len(data):
            raise ValueError('Invalid WebP chunk framing')
        kind = data[position:position+4]
        size = int.from_bytes(data[position+4:position+8], 'little')
        start, end = position + 8, position + 8 + size
        padded = end + size % 2
        if padded > len(data) or (size % 2 and data[end] != 0) or kind in seen:
            raise ValueError('Invalid or ambiguous WebP chunks')
        seen.add(kind)
        payload = memoryview(data)[start:end]
        if kind in (b'ANIM', b'ANMF'):
            raise ValueError('Animated WebP is forbidden before native decoding')
        if kind == b'VP8X':
            if count != 1 or size != 10 or payload[0] & 0xc3 or any(payload[1:4]):
                raise ValueError('Invalid or animated extended WebP header')
            flags = payload[0]
            canvas = _canvas(1 + int.from_bytes(payload[4:7], 'little'), 1 + int.from_bytes(payload[7:10], 'little'))
        elif kind in (b'VP8 ', b'VP8L'):
            if pixels is not None or b'EXIF' in seen or b'XMP ' in seen:
                raise ValueError('Multiple or unordered WebP images')
            if kind == b'VP8L':
                if size < 5 or payload[0] != 0x2f:
                    raise ValueError('Invalid lossless WebP header')
                packed = int.from_bytes(payload[1:5], 'little')
                if packed >> 29 or b'ALPH' in seen:
                    raise ValueError('Unsupported lossless WebP header')
                pixels = _canvas(1 + (packed & 0x3fff), 1 + ((packed >> 14) & 0x3fff))
                alpha = bool(packed & (1 << 28))
            else:
                if size < 10 or bytes(payload[3:6]) != b'\x9d\x01\x2a':
                    raise ValueError('Invalid VP8 key-frame header')
                tag = int.from_bytes(payload[:3], 'little')
                width, height = struct.unpack('<HH', payload[6:10])
                if tag & 1 or ((tag >> 1) & 7) > 3 or not tag & 16 or width & 0xc000 or height & 0xc000 or tag >> 5 > size - 10:
                    raise ValueError('Unsupported VP8 frame header')
                pixels = _canvas(width, height)
                alpha = b'ALPH' in seen
        elif kind == b'ALPH':
            if canvas is None or pixels is not None or size < 1 or payload[0] & 0xc0 or (payload[0] & 3) > 1 or ((payload[0] >> 4) & 3) > 1:
                raise ValueError('Invalid WebP alpha header')
            if payload[0] & 3 == 0 and size != 1 + canvas[0] * canvas[1]:
                raise ValueError('Invalid uncompressed WebP alpha size')
        elif kind == b'ICCP':
            if canvas is None or pixels is not None or b'ALPH' in seen or not size:
                raise ValueError('Invalid WebP color-profile order')
        elif kind in (b'EXIF', b'XMP '):
            if canvas is None or pixels is None or not size:
                raise ValueError('Invalid WebP metadata order')
        else:
            raise ValueError('Unsupported WebP chunk; fail closed')
        position = padded
    if pixels is None or (canvas is not None and canvas != pixels):
        raise ValueError('Missing or inconsistent WebP canvas')
    if canvas is None and len(seen) != 1:
        raise ValueError('Extended WebP chunks require VP8X')
    if canvas is not None and (bool(flags & 0x10) != alpha or
            any(bool(flags & flag) != (kind in seen) for flag, kind in ((0x20,b'ICCP'),(0x08,b'EXIF'),(0x04,b'XMP ')))):
        raise ValueError('Inconsistent WebP feature flags')
    return pixels


def _jpeg_canvas(data):
    if data[:2] != b'\xff\xd8':
        raise ValueError('Invalid JPEG signature')
    position, count, dimensions, components, scans = 2, 0, None, set(), 0
    while position < len(data):
        count += 1
        if count > MAX_CONTAINER_PARTS or data[position] != 0xff:
            raise ValueError('Invalid JPEG marker framing')
        while position < len(data) and data[position] == 0xff:
            position += 1
        if position >= len(data):
            break
        kind = data[position]
        position += 1
        if kind == 0xd9:
            if dimensions is None or not scans or position != len(data):
                raise ValueError('Incomplete JPEG or trailing data')
            return dimensions
        if kind not in (0xc0, 0xc2, 0xc4, 0xdb, 0xdd, 0xda, 0xfe) and not 0xe0 <= kind <= 0xef:
            raise ValueError('Unsupported JPEG marker; fail closed')
        if position + 2 > len(data):
            raise ValueError('Truncated JPEG segment')
        size = int.from_bytes(data[position:position+2], 'big')
        end = position + size
        if size < 2 or end > len(data):
            raise ValueError('Invalid JPEG segment length')
        payload = memoryview(data)[position+2:end]
        if kind in (0xc0, 0xc2):
            if dimensions is not None or len(payload) < 6 or payload[0] != 8 or payload[5] not in (1,3) or len(payload) != 6 + 3*payload[5]:
                raise ValueError('Unsupported or ambiguous JPEG frame')
            height, width = struct.unpack('!HH', payload[1:5])
            dimensions = _canvas(width, height)
            for offset in range(6, len(payload), 3):
                identifier, sampling, table = payload[offset:offset+3]
                if identifier in components or not 1 <= sampling >> 4 <= 4 or not 1 <= sampling & 15 <= 4 or table > 3:
                    raise ValueError('Invalid JPEG component header')
                components.add(identifier)
        elif kind == 0xe2 and bytes(payload[:4]) == b'MPF\0':
            raise ValueError('Multiframe JPEG is forbidden before decoding')
        elif kind == 0xdd and len(payload) != 2:
            raise ValueError('Invalid JPEG restart interval')
        elif kind == 0xda:
            if dimensions is None or not payload or not 1 <= payload[0] <= len(components) or len(payload) != 4 + 2*payload[0]:
                raise ValueError('Invalid JPEG scan header')
            ids = [payload[index] for index in range(1, 1+2*payload[0], 2)]
            if len(set(ids)) != len(ids) or not set(ids) <= components:
                raise ValueError('Invalid JPEG scan components')
            scans += 1
            position = end
            while position < len(data):
                marker = data.find(b'\xff', position)
                if marker < 0 or marker + 1 >= len(data):
                    raise ValueError('Truncated JPEG entropy data')
                next_byte = data[marker+1]
                if next_byte == 0 or 0xd0 <= next_byte <= 0xd7:
                    position = marker + 2
                elif next_byte == 0xff:
                    position = marker + 1
                else:
                    position = marker
                    break
            continue
        position = end
    raise ValueError('Incomplete JPEG container')


def preflight_image(data, fmt):
    """Bound still-image canvas headers without constructing any Pillow/native image."""
    if not isinstance(data, bytes) or not data or len(data) > MAX_IMAGE_BYTES:
        raise ValueError('Image byte limit or type invalid')
    readers = {'PNG': _png_canvas, 'JPEG': _jpeg_canvas, 'WEBP': _webp_canvas}
    if fmt not in readers:
        raise ValueError('Unsupported image format; no safe preflight')
    return readers[fmt](data)


def validate_image(data, width, height, fmt):
    header_size = preflight_image(data, fmt)
    with warnings.catch_warnings():
        warnings.simplefilter('error', Image.DecompressionBombWarning)
        with Image.open(BytesIO(data), formats=[fmt]) as image:
            if image.format not in ('PNG', 'JPEG', 'WEBP') or image.format != fmt:
                raise ValueError('Actual image format mismatch or unsupported')
            if image.size != header_size:
                raise ValueError('Native image dimensions differ from checked container')
            _canvas(*image.size)
            if getattr(image, 'n_frames', 1) != 1 or image.mode not in ('RGB', 'RGBA', 'L', 'LA', 'P'):
                raise ValueError('Multiframe or unsupported image mode')
            image.load()  # Full decode, not just header inspection.
            image = ImageOps.exif_transpose(image)
            if image.size != (width, height):
                raise ValueError('Actual dimensions differ from requested dimensions')
            pixels = image.convert('RGBA').tobytes()
            pixel_digest = hashlib.sha256(canonical([width, height, 'RGBA']))
            pixel_digest.update(pixels)
            return {'width': width, 'height': height, 'format': fmt, 'bytes': len(data),
                    'sha256': sha256(data), 'pixel_sha256': pixel_digest.hexdigest(),
                    'alpha': 'A' in image.getbands() or 'transparency' in image.info}


def reject_duplicates(images):
    hashes, pixels = set(), set()
    for image in images:
        if image['sha256'] in hashes or image['pixel_sha256'] in pixels:
            raise ValueError('Duplicate image bytes or decoded pixels')
        hashes.add(image['sha256'])
        pixels.add(image['pixel_sha256'])


def agent_module():
    spec = importlib.util.spec_from_file_location('image_agent_worker', Path(__file__).with_name('image-seo-agent.py'))
    agent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(agent)
    return agent


def _worker(buffer, limit, operation, args):
    try:
        if operation == 'validate':
            value = validate_image(*args)
        elif operation == 'response':
            value = decode_response(*args)
        elif operation == 'optimize':
            root, source, output, widths, formats, quality, dimensions, fmt = args
            validate_image(read_bounded(Path(root) / source, MAX_IMAGE_BYTES), *dimensions, fmt)
            value = agent_module().optimize(Path(root), source, Path(output), widths, formats, quality,
                                             max_output_bytes=MAX_OUTPUT_BYTES)
        else:
            raise ValueError('Unknown worker operation')
        if operation == 'response':
            _write_frame(buffer, limit, FRAME_BYTES, value)
        else:
            _write_frame(buffer, limit, FRAME_JSON, canonical(value))
    except Exception:
        _write_frame(buffer, limit, FRAME_ERROR, b'')


def bounded_worker(operation, args, timeout=WORKER_SECONDS):
    """Sequential killable codec worker; bounded inputs, not an OS memory/network sandbox."""
    if operation not in ('validate', 'optimize', 'response') or not 0 < timeout <= WORKER_SECONDS:
        raise ValueError('Invalid worker operation/deadline')
    return _supervised(_worker, (operation, args),
                       limit=MAX_IMAGE_BYTES if operation == 'response' else MAX_INPUT_BYTES,
                       timeout=timeout, expected_kind=FRAME_BYTES if operation == 'response' else FRAME_JSON,
                       timeout_message='Image worker deadline exceeded; discard incomplete external output',
                       failure='Image validation/optimization failed')
