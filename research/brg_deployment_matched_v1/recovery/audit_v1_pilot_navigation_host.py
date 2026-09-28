"""Read archived VGR pilot traces to verify event and navigation behavior."""
from __future__ import annotations

from collections import Counter
import csv
import io
import json
from pathlib import Path
import subprocess

from collect_native_host import ROOT, ZSTD, sha
from evaluate_v1_pilot_host import ARCHIVE, RECEIPTS, ARMS


def extract(archive: Path, member: str) -> bytes:
    decoder = subprocess.Popen([str(ZSTD), '-dc', str(archive)], stdout=subprocess.PIPE)
    assert decoder.stdout is not None
    result = subprocess.run(['tar', '-xOf', '-', member], stdin=decoder.stdout,
                            capture_output=True)
    decoder.stdout.close()
    if decoder.wait() or result.returncode:
        raise RuntimeError(f'archive member read failure: {archive.name} {member}')
    return result.stdout


def main() -> None:
    freeze = json.loads((ROOT / 'PILOT_EVAL_FREEZE.json').read_text())
    rows = []
    for case in freeze['cases']:
        for arm in ARMS:
            prefix = 'pilot' if arm == 'native_pmfs' else 'pilot_fix1'
            stem = f'{prefix}_{arm}_{case["ordinal"]:03d}_{case["case_id"]}'
            archive = ARCHIVE / f'{stem}.tar.zst'
            receipt = json.loads((RECEIPTS / f'{stem}.json').read_text())
            if sha(archive) != receipt['archive_sha256']:
                raise RuntimeError(f'pilot archive drift: {stem}')
            base = f'{stem}_raw/'
            binding = json.loads(extract(archive, base + 'runtime_binding.json'))
            navigation = list(csv.DictReader(io.StringIO(extract(archive, base + 'navigation_trace.csv').decode())))
            sent = [r for r in navigation if r['event'] == 'SENT']
            succeeded = [r for r in navigation if r['event'] == 'RESULT' and r['outcome'] == 'SUCCEEDED']
            goals = sorted({(float(r['goal_x']), float(r['goal_y'])) for r in sent})
            if binding['training_collection'] or binding['fixed_source_blind_coverage']:
                raise RuntimeError(f'training or fixed-route mode leaked into pilot: {stem}')
            if arm == 'native_pmfs':
                sidecar = None
            else:
                events = [json.loads(x) for x in extract(archive, base + 'sidecar_events.jsonl').splitlines()]
                sidecar = dict(Counter(e['status'] for e in events))
                if sidecar.get('RESET') != 1 or sidecar.get('OK', 0) == 0 or sidecar.get('ERROR', 0):
                    raise RuntimeError(f'pilot sidecar event protocol failed: {stem}')
            rows.append({'ordinal': case['ordinal'], 'arm': arm,
                         'navigation_goal_sent': len(sent),
                         'navigation_goal_succeeded': len(succeeded),
                         'unique_sent_goal_xy': goals,
                         'sidecar_protocol_counts': sidecar,
                         'training_collection': binding['training_collection'],
                         'fixed_source_blind_coverage': binding['fixed_source_blind_coverage'],
                         'brg_run_token': binding.get('brg_run_token'),
                         'archive_sha256': receipt['archive_sha256']})
    result = {'status': 'BRG_V1_PILOT_NAVIGATION_AND_SIDECAR_LOG_AUDIT',
              'run_count': len(rows), 'rows': rows}
    output = ARCHIVE / 'summary' / 'BRG_V1_PILOT_NAVIGATION_AUDIT.json'
    if output.exists():
        raise RuntimeError('refuse to overwrite navigation audit')
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'run_count': len(rows),
                      'goals_by_run': [(x['ordinal'], x['arm'], x['unique_sent_goal_xy']) for x in rows],
                      'sha256': sha(output)}))


if __name__ == '__main__':
    main()
