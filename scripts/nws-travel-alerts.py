"""Collect NWS locally. No default live fetch, Git operation or public-site writer."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

from travel_intelligence import nws
from travel_intelligence.nws_storage import NWSStore
from travel_intelligence.validation import ValidationError, canonical, instant, load_json, safe_external_directory, stamp

ROOT = Path(__file__).resolve().parents[1]


def run(store, reader, now, synthetic, clock=None):
    token, _, previous = store.load()
    if previous and previous['feed']['synthetic'] != synthetic:
        raise ValidationError('nws_state_mode_mismatch')
    if previous:
        require_clock = instant(previous['feed']['generatedAt'])
        if now < require_clock:
            raise ValidationError('nws_clock_rollback')
    try:
        raw = reader()
        now = clock() if clock else now
        feed, report = nws.collect(raw, now, synthetic=synthetic)
    except (ValidationError, OSError, TimeoutError) as error:
        code = str(error) if isinstance(error, ValidationError) else 'nws_source_unavailable'
        feed = nws.empty_feed(now, synthetic, 'unavailable')
        report = {'status':'unavailable','verifiedAt':stamp(now),'error':code,'safetyConclusion':None}
    old_feed = previous['lastGoodFeed'] if previous else nws.empty_feed(now, synthetic)
    updates = nws.changes(old_feed, feed, now)
    report['changes'] = updates
    history = (previous['history'] if previous else []) + [{'at':stamp(now),**item} for item in updates]
    data = {'feed':feed,'report':report,
            'lastGoodFeed':feed if feed['status'] == 'checked' else old_feed,'history':history[-1000:]}
    store.commit(data, token)
    return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--fixture', type=Path, help='Always marks output synthetic; never publish this output')
    group.add_argument('--live', action='store_true', help='One read-only NWS request, no automatic retry')
    group.add_argument('--recover-token', help='Explicit local snapshot restoration; no collection')
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='External directory; checkout paths are refused')
    parser.add_argument('--now', help='Fixture clock only; live clock override is refused')
    args = parser.parse_args()
    try:
        safe_external_directory(args.output, ROOT)
        store = NWSStore(args.state, ROOT)
        if args.recover_token:
            store.recover(args.recover_token)
        else:
            if args.live and args.now:
                raise ValidationError('nws_live_clock_override')
            now = instant(args.now) if args.now else datetime.now(timezone.utc)
            reader = args.fixture.read_bytes if args.fixture else nws.fetch
            result = run(store, reader, now, synthetic=bool(args.fixture),
                         clock=(lambda: datetime.now(timezone.utc)) if args.live else None)
        store.export(args.output)
        print(canonical({'status':'local_outputs_only','directory':str(args.output)}).decode())
    except (ValueError, OSError) as error:
        print('NWS local operation refused: ' + (str(error) if isinstance(error,ValidationError) else type(error).__name__), file=sys.stderr)
        raise SystemExit(1)
