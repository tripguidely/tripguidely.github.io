"""Bounded untrusted JSON, plain text, URLs and time primitives."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

UTC = timezone.utc
MAX_INPUT_BYTES = 2_000_000
MAX_STATE_BYTES = 10_000_000


class ValidationError(ValueError):
    """A safe diagnostic code, never an external payload or credential."""


def require(condition, code):
    if not condition:
        raise ValidationError(code)


def keys(value, expected):
    require(type(value) is dict and set(value) == set(expected), "invalid_fields")


def plain(value, limit=800):
    require(type(value) is str and 0 < len(value) <= limit, "invalid_text")
    require(not any(unicodedata.category(c).startswith("C") and c not in "\n\r\t"
                    for c in value), "control_character")
    result = " ".join(unicodedata.normalize("NFC", value).split())
    require(bool(result) and "<" not in result and ">" not in result, "invalid_text")
    return result


def slug(value):
    require(type(value) is str and re.fullmatch(r"[a-z0-9-]{1,64}", value), "invalid_id")
    return value


def country(value):
    require(type(value) is str and re.fullmatch(r"[A-Z]{2}", value), "invalid_country")
    return value


def instant(value):
    require(type(value) is str and re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})", value),
        "timestamp_requires_offset")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        raise ValidationError("invalid_timestamp") from None


def stamp(value):
    require(isinstance(value, datetime) and value.utcoffset() is not None, "naive_clock")
    return value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def local_time(value, timezone_name):
    try:
        return instant(value).astimezone(ZoneInfo(timezone_name)).isoformat(timespec="seconds")
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        raise ValidationError("iana_timezone_unavailable") from None


def official_url(value, allowed_urls):
    require(type(value) is str and len(value) <= 2048, "invalid_url")
    try:
        u = urlsplit(value)
        valid = (u.scheme == "https" and u.hostname and not u.username and not u.password
                 and u.port in (None, 443) and not u.fragment and not u.query)
    except ValueError:
        valid = False
    require(valid and value in allowed_urls, "url_not_allowlisted")
    return value


def canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def _depth(value, level=0):
    require(level <= 32, "json_too_deep")
    if type(value) is dict:
        require(len(value) <= 5000, "json_too_many_keys")
        for item in value.values():
            _depth(item, level + 1)
    elif type(value) is list:
        require(len(value) <= 5000, "json_too_many_items")
        for item in value:
            _depth(item, level + 1)


def parse_json(raw, limit=MAX_INPUT_BYTES):
    require(type(raw) is bytes and len(raw) <= limit, "json_size_limit")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate_json_key")
            result[key] = value
        return result
    def no_constant(_):
        raise ValidationError("nonfinite_json_number")
    try:
        result = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=unique,
                            parse_constant=no_constant)
        _depth(result)
        # Also reject overflow such as 1e999 parsed as float infinity.
        canonical(result)
        return result
    except (UnicodeError, json.JSONDecodeError, RecursionError, OverflowError):
        raise ValidationError("malformed_json") from None
    except ValueError as exc:
        if isinstance(exc, ValidationError):
            raise
        raise ValidationError("nonfinite_json_number") from None


def load_json(path, limit=MAX_INPUT_BYTES):
    with Path(path).open("rb") as stream:
        return parse_json(stream.read(limit + 1), limit)


def safe_external_directory(path, checkout):
    """No writes to a checkout, another worktree, Git metadata or symlink path."""
    raw = Path(path).absolute()
    for parent in (raw, *raw.parents):
        require(not parent.is_symlink() and not parent.is_junction(), "linked_output_path")
        require(parent.name.lower() not in (".git", ".github"), "git_output_path")
        require(not (parent / ".git").exists(), "output_inside_git_checkout")
    target = raw.resolve()
    require(not target.is_relative_to(Path(checkout).resolve()), "output_inside_checkout")
    return target
