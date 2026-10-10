"""Read-only numerical verification of frozen M0; newline/float formatting independent.

SHA256 still checks ORIGINAL bytes. Derived CSV comparisons parse values using
rtol=5e-12, atol=5e-15, except source-score columns use atol=1e-300. Integers,
booleans, strings, row order and column names must match exactly. No ROS or writes.
"""
import sys
sys.dont_write_bytecode = True
import argparse
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path


def load_m0(package):
    spec = importlib.util.spec_from_file_location('frozen_m0_calculation', package / 'verify_m0.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def same_number(actual, expected, label, score=False):
    actual = float(actual)
    assert math.isfinite(actual) and math.isfinite(expected), label
    absolute = 1e-300 if score else 5e-15
    assert math.isclose(actual, expected, rel_tol=5e-12, abs_tol=absolute), (label, actual, expected)
    return abs(actual-expected)


def compare_json(actual, expected, label='result'):
    if isinstance(expected, dict):
        assert actual.keys() == expected.keys(), label
        return max((compare_json(actual[k], expected[k], label+'.'+k) for k in expected), default=0.)
    if isinstance(expected, list):
        assert len(actual) == len(expected), label
        return max((compare_json(a, e, label) for a, e in zip(actual, expected)), default=0.)
    if isinstance(expected, float):
        assert isinstance(actual, (float, int)) and not isinstance(actual, bool), label
        return same_number(actual, expected, label, score=label.endswith('_score'))
    assert type(actual) is type(expected), label
    assert actual == expected, label
    return 0.


def compare_csv(path, expected):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == list(expected[0]), path
        actual = list(reader)
    assert len(actual) == len(expected), path
    maximum = 0.
    numeric_fields = 0
    for index, (row, target) in enumerate(zip(actual, expected)):
        for key, value in target.items():
            label = f'{path.name}:{index+2}:{key}'
            if isinstance(value, bool):
                assert row[key] == str(value), label
            elif isinstance(value, int):
                assert row[key].strip() == str(value), label
            elif isinstance(value, float):
                maximum = max(maximum, same_number(row[key], value, label, score=key.endswith('_score')))
                numeric_fields += 1
            else:
                assert row[key] == str(value), label
    return dict(file=path.name, rows=len(actual), numeric_fields=numeric_fields, maximum_abs_difference=maximum)


def verify(package):
    frozen = json.loads((package/'SHA256_MANIFEST.json').read_text(encoding='utf-8'))
    for name, digest in frozen.items():
        assert hashlib.sha256((package/name).read_bytes()).hexdigest() == digest, name
    module = load_m0(package)
    result, cells, regions, cross, chains = module.analyse(package/'evidence')
    saved = json.loads((package/'derived/B4_M0_RESULT.json').read_text(encoding='utf-8'))
    json_error = compare_json(saved, result)
    checks = []
    for key, records in cells.items():
        checks.append(compare_csv(package/'derived'/(key+'_CELL_ATTRIBUTION.csv'), records))
    for key, records in regions.items():
        checks.append(compare_csv(package/'derived'/(key+'_REGION_ATTRIBUTION.csv'), records))
    for name, records in [('FIXED_REGION_CROSS_MAP_SCORING.csv', cross),
                          ('SOURCE_LEAF_AND_REFINEMENT_TRACE.csv', chains),
                          ('DIRECT_STOPS_AND_COVERAGE.csv', result['observation']['stops'])]:
        checks.append(compare_csv(package/'derived'/name, records))
    assert len(checks) == 15
    return dict(verdict='PASS_M0_FROZEN_HASH_AND_PORTABLE_NUMERICAL_COMPARISON',
                original_hashes=len(frozen), derived_CSVs=len(checks), CSV_checks=checks,
                JSON_maximum_abs_difference=json_error, rtol=5e-12, atol=5e-15,
                score_atol=1e-300, original_files_changed=0, writes=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--m0', type=Path, default=Path(__file__).resolve().parent/'frozen_M0')
    args = parser.parse_args()
    print(json.dumps(verify(args.m0.resolve()), indent=2))
