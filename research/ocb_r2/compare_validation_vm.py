#!/usr/bin/env python3
"""Exact A(S1), B(S2), C(S1) scientific payload qualification."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path('/home/zyc/ocb_r2_validation')


def load(arm: str):
    base = ROOT / f'RUN_{arm}'
    manifest = json.loads((base / 'RUN_MANIFEST.json').read_text())
    with (base / 'OUTPUT_SHA256SUMS.tsv').open(newline='') as fh:
        files = {row['name']: (int(row['size_bytes']), row['sha256']) for row in csv.DictReader(fh, delimiter='\t')}
    with (base / 'RECORD_TIMELINE.tsv').open(newline='') as fh:
        timeline = list(csv.DictReader(fh, delimiter='\t'))
    return manifest, files, timeline


def main():
    a, af, at = load('A')
    b, bf, bt = load('B')
    c, cf, ct = load('C')
    assert a['master_seed'] == c['master_seed'] != b['master_seed']
    excluded = {'arm', 'master_seed', 'stdout_sha256'}
    clean = lambda m: {k: v for k, v in m.items() if k not in excluded}
    metadata_ac = clean(a) == clean(c)
    metadata_ab = clean(a) == clean(b)
    same_names = set(af) == set(bf) == set(cf)
    assert same_names and len(af) > 100
    differing_ab = [name for name in sorted(af) if af[name] != bf[name]]
    differing_ac = [name for name in sorted(af) if af[name] != cf[name]]
    total_bytes = sum(size for size, _ in af.values())
    different_bytes = sum(af[name][0] for name in differing_ab)
    result = {
        'decision': 'OCB_R2_GENERATOR_REFOUNDATION_FAIL_STOP',
        'record_count_A_B_C': [a['record_count'], b['record_count'], c['record_count']],
        'timeline_exact_A_B': at == bt,
        'timeline_exact_A_C': at == ct,
        'wind_index_exact_A_B': [x['wind_index'] for x in at] == [x['wind_index'] for x in bt],
        'wind_index_exact_A_C': [x['wind_index'] for x in at] == [x['wind_index'] for x in ct],
        'deterministic_metadata_exact_A_B': metadata_ab,
        'deterministic_metadata_exact_A_C': metadata_ac,
        'scientific_payload_exact_A_C': not differing_ac,
        'scientific_payload_different_A_B': bool(differing_ab),
        'different_file_count_A_B': len(differing_ab),
        'different_file_count_A_C': len(differing_ac),
        'total_scientific_bytes_A': total_bytes,
        'bytes_in_files_with_seed_difference_A_B': different_bytes,
        'fraction_of_record_files_different_A_B': len(differing_ab) / len(af),
        'first_20_different_records_A_B': differing_ab[:20],
    }
    passed = all((
        len(af) == a['record_count'] == b['record_count'] == c['record_count'],
        result['timeline_exact_A_B'], result['timeline_exact_A_C'],
        result['wind_index_exact_A_B'], result['wind_index_exact_A_C'],
        metadata_ab, metadata_ac, not differing_ac, bool(differing_ab),
    ))
    if passed:
        result['decision'] = 'OCB_R2_GENERATOR_REFOUNDATION_PASS'
    out = ROOT / 'VALIDATION_RESULT.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if passed else 20


if __name__ == '__main__':
    raise SystemExit(main())
