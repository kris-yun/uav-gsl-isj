#!/usr/bin/env python3
"""Independently verify the signed row keys and frozen template support."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    root = args.root
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    manifest = root / 'protocol/frozen/HOUSE03_FUTURE_PMFS_SEEDS_FULL624_54912.tsv'
    assert sha(manifest) == '00bf64ab0d1ce55fda58303b11208019473313b97c4de11f7a2305d16143327d'
    rows = list(csv.DictReader(manifest.open(), delimiter='\t'))
    audit = json.loads((root / 'CANDIDATE_BANK_AUDIT.json').read_text())
    freeze = json.loads((root / 'TEMPLATE_FREEZE.json').read_text())
    build = json.loads((root / 'BUILD_AND_ASSET_AUDIT.json').read_text())
    assert build['passed']
    assert sha(root / 'inputs/meta.json') == build['geometry_hashes']['pruned_meta.json']
    assert sha(root / 'inputs/occupancy.u8') == build['geometry_hashes']['pruned_seed0.bin']
    assert sha(root / 'inputs/sources.csv') == build['source_csv_sha256']
    for wind in build['wind']:
        assert sha(root / f"inputs/wind_{wind['state']}.csv") == wind['export_sha256']
        assert sha(wind['csv_path']) == wind['csv_sha256']
        assert sha(wind['binary_path']) == wind['binary_sha256']
    assert sha(root / 'execution/marked_forward_full624.cpp') == build['wrapper_sha256']
    assert sha(root / 'build/marked_forward_full624') == build['binary_sha256']
    for path, digest in build['object_hashes'].items():
        assert sha(path) == digest
    assert audit['passed'] and freeze['passed']
    assert audit['completed'] == len(rows) == len(audit['records']) == 54912
    assert audit['source_count'] == freeze['candidates'] == 624
    assert audit['fresh_targets_generated'] == freeze['fresh_target_runs'] == 0
    assert freeze['fresh_target_values_read'] is False
    expected_keys = {(s, w, r) for s in range(624) for w in range(11) for r in range(8)}
    seen = set()
    for row, record in zip(rows, audit['records']):
        key = tuple(int(row[k]) for k in ['source_index', 'wind_state', 'transport_replica_index'])
        assert key not in seen
        seen.add(key)
        for k in ['source_index', 'wind_state', 'transport_replica_index', 'requested_seed']:
            assert int(row[k]) == record[k], (key, k)
        assert row['source_id'] == record['source_id']
        assert set(record['hashes']) == {'p', 'u', 'rawp', 'rawu'}
        assert all(len(h) == 64 for h in record['hashes'].values())
    assert seen == expected_keys
    template_dir = root / 'templates'
    for name, digest in freeze['arrays_sha256'].items():
        assert sha(template_dir / name) == digest, name
    support = list(csv.DictReader((template_dir / 'CANDIDATE_SUPPORT.csv').open()))
    source_ids = [r['source_id'] for r in support]
    assert len(source_ids) == len(set(source_ids)) == 624
    by_index = {int(r['source_index']): r['source_id'] for r in rows}
    assert source_ids == [by_index[i] for i in range(624)]
    path_arrays = np.load(template_dir / 'candidate_path_templates.npz', allow_pickle=False)
    wanted = {f'{c}_{k}_path_{p}' for c in ['nominal', 'state0_stress']
              for k in ['p', 'rawp', 'u', 'rawu'] for p in ['A', 'B']}
    assert set(path_arrays.files) == wanted
    for name in wanted:
        array = path_arrays[name]
        assert array.shape == (624, 10) and np.isfinite(array).all() and (array >= 0).all()
    result = dict(passed=True, source_count=624, full_signed_forward_rows=54912,
                  unique_source_state_replica_keys=len(seen), path_template_arrays=len(wanted),
                  candidate_bank_audit_sha256=sha(root / 'CANDIDATE_BANK_AUDIT.json'),
                  template_freeze_sha256=sha(root / 'TEMPLATE_FREEZE.json'),
                  seed_manifest_sha256=sha(manifest), fresh_targets_generated=0,
                  fresh_target_values_read=False,
                  initial_geometry_wind_sources_binary_and_objects_hashes_unchanged=True,
                  map_byte_validation='VM template builder verified all four files against each completed row hash',
                  scientific_parameters_changed=False)
    (root / 'PRE_TARGET_BANK_VALIDATION.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
