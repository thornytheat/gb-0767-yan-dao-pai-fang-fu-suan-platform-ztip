import json
from datetime import UTC, datetime
from hashlib import sha256
from time import perf_counter

from app.config import VERSION
from app.monitor.source import digests


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), default=str)


def batch_key(files):
    hashes = digests(files)
    return sha256(canonical([VERSION, hashes]).encode()).hexdigest(), hashes


def manifest(run_id, hashes, window, name, started):
    return {'run_id': run_id, 'source': name, 'rule': VERSION, 'sha256': hashes,
            'created_utc': datetime.now(UTC).isoformat(timespec='seconds'),
            'elapsed_ms': round((perf_counter() - started) * 1000), 'parameters': window}
