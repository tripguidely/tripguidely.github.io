"""Local NWS snapshots: immutable envelope + atomic pointer, CAS and explicit recovery."""
from contextlib import contextmanager
from copy import deepcopy
import os
from pathlib import Path
import re

from .storage import atomic_json, ConflictError
from .validation import canonical, digest, keys, load_json, require, safe_external_directory


class NWSStore:
    def __init__(self, directory, checkout):
        self.checkout = Path(checkout)
        self.directory = safe_external_directory(directory, checkout)

    def safe(self):
        safe_external_directory(self.directory, self.checkout)
        for name in ('CURRENT.json','generations','.writer.lock'):
            path = self.directory / name
            require(not path.is_symlink() and not path.is_junction(), 'nws_linked_state')

    def generation(self, token):
        require(type(token) is str and re.fullmatch('[a-f0-9]{64}', token), 'nws_state_token')
        path = self.directory / 'generations' / (token + '.json')
        require(not path.is_symlink() and not path.is_junction(), 'nws_linked_generation')
        envelope = load_json(path)
        keys(envelope, {'schema','generation','previous','data'})
        require(type(envelope['schema']) is int and envelope['schema'] == 1 and type(envelope['generation']) is int and
                1 <= envelope['generation'] <= 10000 and digest(envelope) == token, 'nws_state_integrity')
        require(type(envelope['data']) is dict and set(envelope['data']) == {'feed','report','lastGoodFeed','history'}, 'nws_state_schema')
        require(type(envelope['data']['history']) is list and len(envelope['data']['history']) <= 1000, 'nws_history_limit')
        return envelope

    def load(self):
        self.safe()
        pointer = self.directory / 'CURRENT.json'
        if not pointer.exists():
            require(not (self.directory / 'generations').exists() or
                    not any((self.directory / 'generations').iterdir()), 'nws_orphan_requires_recovery')
            return None, 0, None
        data = load_json(pointer)
        keys(data, {'generation','token'})
        envelope = self.generation(data['token'])
        require(type(data['generation']) is int and envelope['generation'] == data['generation'], 'nws_pointer_mismatch')
        # Verify complete history, not an arbitrary newest orphan after a crash.
        current, count = envelope, envelope['generation']
        while count > 1:
            current = self.generation(current['previous'])
            count -= 1
            require(current['generation'] == count, 'nws_history_gap')
        require(current['previous'] is None, 'nws_history_root')
        return data['token'], envelope['generation'], deepcopy(envelope['data'])

    @contextmanager
    def lock(self):
        self.safe(); self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / '.writer.lock'
        try:
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            raise ConflictError('nws_writer_locked') from None
        try:
            with os.fdopen(descriptor, 'wb') as handle:
                handle.write(canonical({'pid':os.getpid(),'purpose':'nws-local-only'})); handle.flush(); os.fsync(handle.fileno())
            yield
        finally:
            path.unlink()

    def commit(self, data, expected_token):
        with self.lock():
            token, generation, _ = self.load()
            if token != expected_token:
                raise ConflictError('nws_generation_conflict')
            require(generation < 10000, 'nws_generation_limit')
            envelope = {'schema':1,'generation':generation + 1,'previous':token,'data':data}
            new_token = digest(envelope)
            folder = self.directory / 'generations'; folder.mkdir(exist_ok=True)
            target = folder / (new_token + '.json')
            require(not target.is_symlink() and not target.is_junction(), 'nws_linked_generation')
            if target.exists():
                require(self.generation(new_token) == envelope, 'nws_generation_exists')
            else:
                atomic_json(target, envelope)
            # A crash here leaves the last pointer intact. Orphans are never auto-promoted.
            atomic_json(self.directory / 'CURRENT.json', {'generation':generation + 1,'token':new_token})
            return new_token

    def recover(self, token):
        """Operator-selected known token only; no newest-file guessing or lock breaking."""
        with self.lock():
            envelope = self.generation(token)
            old = self.directory / 'CURRENT.json'
            # Validate chain before replacing a corrupt pointer by using envelope links.
            current = envelope
            for number in range(envelope['generation'] - 1, 0, -1):
                current = self.generation(current['previous'])
                require(current['generation'] == number, 'nws_history_gap')
            require(current['previous'] is None, 'nws_history_root')
            atomic_json(old, {'generation':envelope['generation'],'token':token})

    def export(self, directory):
        output = safe_external_directory(directory, self.checkout)
        # Prevent slow concurrent exporters from overwriting a newer projection with an old one.
        with self.lock():
            _, _, data = self.load()
            require(data is not None, 'nws_empty_state')
            output.mkdir(parents=True, exist_ok=True)
            for name, key in [('nws-nyc.json','feed'),('review.json','report')]:
                target = output / name
                require(not target.is_symlink() and not target.is_junction(), 'nws_linked_export')
                atomic_json(target, data[key])
