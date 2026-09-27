#!/usr/bin/env python3
"""Independent signed gate verification from timestamps and release metadata."""
import argparse
import csv
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('metadata', type=Path)
    parser.add_argument('audit', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    times_path = args.metadata / 'RESULT_TIME_MAP.tsv'
    release_path = args.metadata / 'RELEASE_TIME_METADATA.tsv'
    times = list(csv.DictReader(times_path.open(), delimiter='\t'))
    release = list(csv.DictReader(release_path.open(), delimiter='\t'))
    primary = json.loads(args.audit.read_text())
    assert [int(row['save_record_id']) for row in times] == list(range(len(times)))
    values = [float(row['physical_sim_time_s']) for row in times]
    assert all(b > a for a, b in zip(values, values[1:]))
    assert all(0 <= int(row['wind_index']) <= 10 for row in times)
    enabled = next(row for row in release if row['event'] == 'release_enabled_first_step')
    emitted = next(row for row in release if row['event'] == 'first_nonzero_filament_count')
    enable_zero = abs(float(enabled['physical_sim_time_s'])) <= 1e-9
    actual_zero = abs(float(emitted['physical_sim_time_s'])) <= 1e-9
    counts = [sum(abs(t - requested) <= 1e-9 for t in values) for requested in range(50, 501, 50)]
    passed = enable_zero and actual_zero and all(count == 1 for count in counts)
    decision = 'TIMEBASE_METADATA_VALID' if passed else 'AOD_F1_HOLD_TIMEBASE'
    assert primary['passed'] == passed and primary['decision'] == decision
    assert primary['writer_record_count'] == len(times)
    assert counts == [entry['exact_match_count'] for entry in primary['slot_checks']]
    hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in [
        ('result_time_map', times_path), ('release_metadata', release_path)]}
    assert hashes['result_time_map'] == primary['result_time_map_sha256']
    assert hashes['release_metadata'] == primary['release_metadata_sha256']
    result = dict(independent_verification_passed=True, decision=decision,
                  signed_tolerance_s=1e-9, configured_release_enabled_at_zero=enable_zero,
                  first_actual_emission_s=float(emitted['physical_sim_time_s']),
                  actual_emission_at_zero=actual_zero, exact_match_counts=counts,
                  writer_record_count=len(times), input_sha256=hashes,
                  concentration_values_read=False, scoring_or_bootstrap_executed=False)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(decision, 'INDEPENDENT_METADATA_VERIFICATION_MATCHED')


if __name__ == '__main__':
    main()
