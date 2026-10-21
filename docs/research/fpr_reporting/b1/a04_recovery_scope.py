"""Hash-only preservation audit of the recovery scope and historical artifacts."""
from __future__ import annotations
import json
import subprocess
from pathlib import Path
import a04_evidence as e
import a04_recovery_intake as r

BASELINE = '73744c0fcaabc6efd995bd534726bd741ce3c9eb'
PREFIX = 'docs/research/fpr_reporting/b1/'


def main() -> None:
    """Compare historical bytes without parsing historical research judgments."""
    head = e.clean_head()
    e.baseline(e.read(e.CONFIG))
    command = lambda *args: subprocess.run(['git', *args], capture_output=True, check=True).stdout
    paths = command('ls-tree', '-r', '--name-only', BASELINE, '--', PREFIX).decode().splitlines()
    historical = []
    changed = []
    # Read Git blobs only for byte hashing; no JSON or scientific content parsing.
    specs = ''.join(BASELINE + ':' + path + '\n' for path in paths).encode()
    process = subprocess.run(['git', 'cat-file', '--batch'], input=specs, capture_output=True, check=True)
    data = process.stdout
    position = 0
    for path in paths:
        end = data.index(b'\n', position)
        header = data[position:end].split()
        if len(header) != 3 or header[1] != b'blob':
            raise ValueError('SCOPE_EXPECTED_HISTORICAL_BLOB')
        size = int(header[2])
        raw = data[end+1:end+1+size]
        position = end+1+size+1
        actual = Path(path).read_bytes()
        same = raw == actual
        historical.append({'path': path, 'baseline_sha256':e.sha(raw), 'working_sha256':e.sha(actual), 'byte_identical':same})
        if not same:
            changed.append(path)
    delta = command('diff','--name-status',BASELINE,head).decode().splitlines()
    if changed or any(not line.startswith('A\t' + PREFIX) for line in delta):
        raise ValueError('HISTORICAL_BYTES_OR_RESEARCH_ONLY_ADDITION_SCOPE_CHANGED:' + json.dumps(changed))
    locks = {name:e.sha((e.BASE/name).read_bytes()) for name in ['PROTOCOL_LOCK.json','PROTOCOL_LOCK_A02.json','PROTOCOL_LOCK_A03.json','PROTOCOL_LOCK_A04.json']}
    result={'checked_utc':e.now(),'source_git_commit':head,'historical_baseline':BASELINE,
            'historical_files':len(paths),'historical_files_byte_identical':True,'historical_hashes':historical,
            'research_only_added_paths':len(delta),'protocol_lock_sha256':locks,
            'production_change':False,'frozen_artifacts_modified':False,'historical_decision_comparison':'NOT_PERFORMED',
            'selection_run':False,'b2_run':False,'independent_review_completed':False,'gate':'FRAME_BLOCKED'}
    e.write_new(e.BASE/r.RUN/'RECOVERY_SCOPE_CHECK.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='historical_hashes'},sort_keys=True))


if __name__=='__main__':
    main()
