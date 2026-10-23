"""Local durable generations. No Git execution, remote calls or cache dependency."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import timedelta
import os
from pathlib import Path
import re
import tempfile
from typing import Protocol

from .model import validate_event
from .validation import (MAX_STATE_BYTES, ValidationError, canonical, digest, instant,
                         keys, load_json, require, safe_external_directory, stamp)


class StoreError(ValueError):
    pass


class ConflictError(StoreError):
    pass


@dataclass(frozen=True)
class Snapshot:
    token: str | None
    generation: int
    data: dict


class StateStore(Protocol):
    def load(self, now) -> Snapshot: ...
    def commit(self, data: dict, expected_token: str | None, now) -> Snapshot: ...


def empty_state(registry):
    return {"schema_version": 3, "config_hash": registry.config_hash,
            "last_run_at": None, "events": [], "sources": {}}


def validate_state(data, registry, now):
    keys(data, {"schema_version", "config_hash", "last_run_at", "events", "sources"})
    require(type(data["schema_version"]) is int and data["schema_version"] == 3, "state_schema")
    require(data["config_hash"] == registry.config_hash, "state_configuration_mismatch")
    if data["last_run_at"] is not None:
        require(instant(data["last_run_at"]) <= now + timedelta(minutes=5), "future_state")
    require(type(data["events"]) is list and len(data["events"]) <= 1000, "state_event_limit")
    ids = set()
    for event in data["events"]:
        validate_event(event, registry, now)
        require(event["event_id"] not in ids, "state_duplicate_event")
        ids.add(event["event_id"])
        require(data["last_run_at"] is not None and
                instant(event["observed_at"]) <= instant(data["last_run_at"]), "state_event_clock")
    require(type(data["sources"]) is dict and set(data["sources"]) <= set(registry.sources), "state_sources")
    for s in data["sources"].values():
        keys(s, {"status", "last_attempt_at", "last_success_at", "source_generated_at", "error_code"})
        require(s["status"] in {"checked", "unavailable"}, "source_state_status")
        attempt = instant(s["last_attempt_at"])
        require(data["last_run_at"] is not None and attempt <= instant(data["last_run_at"]), "source_state_clock")
        if s["last_success_at"] is not None:
            require(instant(s["last_success_at"]) <= attempt, "source_success_clock")
        if s["source_generated_at"] is not None:
            require(s["last_success_at"] is not None and
                    instant(s["source_generated_at"]) <= instant(s["last_success_at"]) + timedelta(minutes=10),
                    "source_generated_clock")
        if s["status"] == "checked":
            require(s["error_code"] is None and s["last_success_at"] == s["last_attempt_at"]
                    and s["source_generated_at"] is not None, "checked_source_state")
        else:
            require(type(s["error_code"]) is str and re.fullmatch(r"[a-z0-9_]{1,80}", s["error_code"]),
                    "invalid_error_code")
    return data


def _sync_directory(path):
    # Windows has no portable directory fsync. Files are still fsynced before replace.
    if os.name != "nt":
        descriptor = os.open(path, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def atomic_json(path, data):
    raw = canonical(data) + b"\n"
    require(len(raw) <= MAX_STATE_BYTES, "state_size_limit")
    descriptor, temporary = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        _sync_directory(path.parent)
    finally:
        Path(temporary).unlink(missing_ok=True)


class LocalStateStore:
    """Immutable full JSON snapshots + atomic CURRENT, CAS and fail-fast lock.

    Recovery is explicit and only chooses a complete chain. A leftover lock is
    never deleted automatically: inspect the process before removing it offline.
    """
    def __init__(self, directory, registry, checkout):
        self.checkout = Path(checkout)
        self.directory = safe_external_directory(directory, self.checkout)
        self.registry = registry

    def _safe(self):
        safe_external_directory(self.directory, self.checkout)
        for name in ("CURRENT.json", ".writer.lock", "generations"):
            path = self.directory / name
            require(not path.is_symlink() and not path.is_junction(), "linked_state_path")

    @contextmanager
    def _lock(self):
        self._safe()
        self.directory.mkdir(parents=True, exist_ok=True)
        lock = self.directory / ".writer.lock"
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            raise ConflictError("state_writer_locked") from None
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(canonical({"pid": os.getpid(), "purpose": "gti-v3-local-writer"}))
                stream.flush()
                os.fsync(stream.fileno())
            yield
        finally:
            lock.unlink()

    def _read_generation(self, generation, token, now):
        require(type(generation) is int and 1 <= generation <= 1000, "generation_limit")
        require(type(token) is str and re.fullmatch(r"[a-f0-9]{64}", token), "generation_hash")
        path = self.directory / "generations" / f"{generation:08d}-{token}.json"
        require(not path.is_symlink() and not path.is_junction(), "linked_generation")
        envelope = load_json(path, MAX_STATE_BYTES)
        keys(envelope, {"schema_version", "generation", "previous_token", "created_at", "data"})
        require(digest(envelope) == token and type(envelope["schema_version"]) is int
                and envelope["schema_version"] == 3 and type(envelope["generation"]) is int
                and envelope["generation"] == generation, "generation_integrity")
        require(instant(envelope["created_at"]) <= now + timedelta(minutes=5), "future_generation")
        validate_state(envelope["data"], self.registry, now)
        require(envelope["data"]["last_run_at"] is not None and
                instant(envelope["created_at"]) == instant(envelope["data"]["last_run_at"]),
                "generation_state_clock")
        return envelope

    def _chain(self, generation, token, now):
        latest = self._read_generation(generation, token, now)
        current, current_token, number = latest, token, generation
        while number > 1:
            next_token = current["previous_token"]
            parent = self._read_generation(number - 1, next_token, now)
            require(instant(parent["created_at"]) <= instant(current["created_at"]), "generation_clock_rollback")
            current, current_token, number = parent, next_token, number - 1
        require(current["previous_token"] is None, "generation_root")
        return Snapshot(token, generation, latest["data"])

    def load(self, now):
        try:
            self._safe()
            pointer = self.directory / "CURRENT.json"
            if not pointer.exists():
                generations = self.directory / "generations"
                require(not generations.exists() or not any(generations.iterdir()), "state_pointer_missing")
                return Snapshot(None, 0, empty_state(self.registry))
            p = load_json(pointer, 1024)
            keys(p, {"schema_version", "generation", "token"})
            require(type(p["schema_version"]) is int and p["schema_version"] == 3, "pointer_schema")
            return self._chain(p["generation"], p["token"], now)
        except (OSError, ValueError, TypeError, KeyError, RecursionError):
            raise StoreError("state_invalid_recovery_required") from None

    def commit(self, data, expected_token, now):
        validate_state(data, self.registry, now)
        require(data["last_run_at"] == stamp(now), "commit_clock")
        with self._lock():
            old = self.load(now)
            if old.token != expected_token:
                raise ConflictError("state_generation_conflict")
            if old.data["last_run_at"] is not None:
                require(instant(old.data["last_run_at"]) <= now, "clock_rollback")
            generation = old.generation + 1
            require(generation <= 1000, "generation_limit")
            envelope = {"schema_version": 3, "generation": generation, "previous_token": old.token,
                        "created_at": stamp(now), "data": data}
            token = digest(envelope)
            generations = self.directory / "generations"
            generations.mkdir(exist_ok=True)
            target = generations / f"{generation:08d}-{token}.json"
            # An identical orphan from an interrupted commit can be reused safely.
            if target.exists():
                self._read_generation(generation, token, now)
            else:
                raw = canonical(envelope) + b"\n"
                require(len(raw) <= MAX_STATE_BYTES, "state_size_limit")
                with target.open("xb") as stream:
                    stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
                _sync_directory(generations)
            atomic_json(self.directory / "CURRENT.json", {"schema_version": 3, "generation": generation,
                                                        "token": token})
            return Snapshot(token, generation, data)

    def recover(self, now):
        """Restore greatest complete chain; preserve corrupt/orphaned evidence."""
        with self._lock():
            generations = self.directory / "generations"
            paths = list(generations.iterdir()) if generations.exists() else []
            require(len(paths) <= 1100, "recovery_file_limit")
            by_generation = {}
            for path in paths:
                match = re.fullmatch(r"(\d{8})-([a-f0-9]{64})\.json", path.name)
                if match:
                    by_generation.setdefault(int(match[1]), []).append(match[2])
            heads = []
            for number in sorted(by_generation, reverse=True):
                for token in by_generation[number]:
                    try:
                        heads.append(self._chain(number, token, now))
                    except (OSError, ValueError, TypeError, KeyError, RecursionError):
                        continue
                if heads:
                    break
            if not heads:
                raise StoreError("no_valid_recovery_generation")
            if len(heads) != 1:
                raise StoreError("ambiguous_recovery_generation")
            best = heads[0]
            pointer = self.directory / "CURRENT.json"
            # Keep damaged pointer evidence; generations already preserve history.
            if pointer.exists():
                with pointer.open("rb") as stream:
                    evidence = stream.read(1025)
                from hashlib import sha256
                archive = self.directory / ("recovery-pointer-" + sha256(evidence).hexdigest() + ".bin")
                if not archive.exists():
                    with archive.open("xb") as stream:
                        stream.write(evidence)
            atomic_json(pointer, {"schema_version": 3, "generation": best.generation, "token": best.token})
            return best
