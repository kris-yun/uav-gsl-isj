"""Verify the deployment-field and time boundary of the local information audit.

These are data-ingress checks, not causal or efficacy tests. Temporary copies
are confined to a Python-owned temporary directory; archived inputs are read-only.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

import numpy as np


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=repo)
    parser.add_argument('--output', type=Path, default=repo / 'evidence/m1r_causal_repair_20260912/WIND_INPUT_VERIFICATION.json')
    args = parser.parse_args()
    repo = args.repo.resolve()
    script = repo / 'tools/assess_local_wind_response_information.py'
    evidence_path = repo / 'evidence/m1r_causal_repair_20260912/WIND_RESPONSE_INFORMATION_GATE.json'
    spec = importlib.util.spec_from_file_location('wind_input_gate', script)
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    evidence = json.loads(evidence_path.read_text(encoding='utf-8'))
    assert evidence['script_sha256'] == digest(script)
    checks = {}
    for house in ('H01', 'H02', 'H03'):
        name = f'{house}_seed12_M1R'
        directory = repo / 'evidence/m1r_instrumented_20260912' / name
        run = evidence['runs'][name]
        independently_read = {}
        for filename, fields in gate.FIELDS.items():
            path = directory / filename
            assert run['input_sha256'][filename] == digest(path)
            # A separate CSV parser, projected explicitly before numeric conversion.
            with path.open(encoding='utf-8-sig', newline='') as handle:
                reader = csv.DictReader(handle)
                rows = []
                for row in reader:
                    if float(row['t_sim_s']) > 240:
                        break
                    rows.append([float(row[field]) for field in fields])
            independently_read[filename] = np.asarray(rows)
            actual = gate.read_projected_prefix(path, fields)
            assert list(actual.columns) == list(fields)
            np.testing.assert_array_equal(actual.to_numpy(), independently_read[filename])
        assert all(len(a) == 1200 for a in independently_read.values())
        assert run['aligned_samples'] == 1200
        # Poison unselected fields and post-budget values in isolated copies.
        with tempfile.TemporaryDirectory(prefix='m1r_wind_input_') as tmp_name:
            tmp = Path(tmp_name)
            for filename, fields in gate.FIELDS.items():
                with (directory / filename).open(encoding='utf-8-sig', newline='') as source:
                    reader = csv.DictReader(source)
                    header = reader.fieldnames
                    with (tmp / filename).open('w', encoding='utf-8', newline='') as dest:
                        writer = csv.DictWriter(dest, fieldnames=header, lineterminator='\n')
                        writer.writeheader()
                        for row in reader:
                            beyond_budget = float(row['t_sim_s']) > 240
                            for field in header:
                                if field not in fields or (beyond_budget and field != 't_sim_s'):
                                    row[field] = 'POISON_NOT_AN_OBSERVATION'
                            writer.writerow(row)
                actual = gate.read_projected_prefix(tmp / filename, fields)
                np.testing.assert_array_equal(actual.to_numpy(), independently_read[filename])
            poisoned = gate.assess_run(tmp)
            assert {k: v for k, v in poisoned.items() if k != 'input_sha256'} == {
                k: v for k, v in run.items() if k != 'input_sha256'
            }
            wind_path = tmp / 'wind_trace.csv'
            lines = wind_path.read_text(encoding='utf-8').splitlines()
            fields = lines[2].split(',')
            fields[0] = str(float(fields[0]) + 0.01)
            lines[2] = ','.join(fields)
            wind_path.write_bytes(('\n'.join(lines) + '\n').encode('utf-8'))
            try:
                gate.assess_run(tmp)
            except ValueError as error:
                assert str(error) == 'TIMESTAMP_OR_STEP_ALIGNMENT_FAILURE'
            else:
                raise AssertionError('misaligned sensor/wind timestamps were accepted')
        checks[name] = {
            'independent_csv_projection_equal': True,
            'archived_hashes_match': True,
            'oracle_and_unused_fields_poison_invariant': True,
            'post_240s_values_poison_invariant': True,
            'timestamp_misalignment_rejected': True,
            'original_input_hashes_still_match': all(
                digest(directory / f) == h for f, h in run['input_sha256'].items()
            ),
        }
        assert all(checks[name].values())
    result = {
        'status': 'PASS_INPUT_BOUNDARY_CHECKS_ONLY',
        'scientific_status': 'CAUSAL_ADMISSION_NOT_ESTABLISHED',
        'verifier_sha256': digest(Path(__file__)),
        'input_script_sha256': digest(script),
        'input_evidence_sha256': digest(evidence_path),
        'checks': checks,
        'does_not_establish': ['instrument validity', 'source discrimination', 'causal efficacy', 'cross-dataset improvement'],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes((json.dumps(result, indent=2, ensure_ascii=False) + '\n').encode('utf-8'))
    print(json.dumps({'status': result['status'], 'houses_checked': len(checks)}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
