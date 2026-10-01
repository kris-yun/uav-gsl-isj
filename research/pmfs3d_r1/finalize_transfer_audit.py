"""Verify copied inputs and export compact, reviewable metadata (no R1 scores)."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--evidence', type=Path, required=True)
args = parser.parse_args()
root = args.evidence
audit = json.loads((root / 'ASSET_AND_NATIVE_PARITY.json').read_text())
inputs = []
summary = []
for case in audit['cases']:
    for entry in case['historical_manifest_verified_inputs']:
        relative = Path(entry['archive_relative']).relative_to('native')
        local = root / 'frozen_inputs' / relative
        actual = hashlib.sha256(local.read_bytes()).hexdigest()
        assert actual == entry['sha256'], str(local)
        assert local.stat().st_size == entry['bytes'], str(local)
        inputs.append(dict(case=case['case'], archive_relative=entry['archive_relative'],
                           bytes=entry['bytes'], sha256=actual))
    params = case['resolved_parameters']
    terminal = case['terminal']
    x, y = float(params['ground_truth_x']), float(params['ground_truth_y'])
    i = math.floor((x - float(terminal['origin_x'])) / float(terminal['cell_size']))
    j = math.floor((y - float(terminal['origin_y'])) / float(terminal['cell_size']))
    matched = [leaf for leaf in case['active_candidates']
               if int(leaf['origin_i']) <= i < int(leaf['origin_i']) + int(leaf['size_i'])
               and int(leaf['origin_j']) <= j < int(leaf['origin_j']) + int(leaf['size_j'])]
    assert len(matched) == 1, (case['case'], i, j)
    cells_path = root / 'frozen_inputs' / case['case'] / 'context_bank' / 'source_update_0005' / 'measured_hit_probability.csv'
    with cells_path.open(newline='', encoding='utf-8-sig') as handle:
        true_cells = [c for c in csv.DictReader(handle) if int(c['grid_i']) == i and int(c['grid_j']) == j]
    assert len(true_cells) == 1 and true_cells[0]['occupancy'] == 'Free'
    summary.append(dict(case=case['case'], source_update_id=terminal['source_update_id'],
                        sim_time=terminal['sim_time'], active_leaf_count=case['active_leaf_count'],
                        free_cell_count=case['free_cell_count'], useWindGroundTruth=params['useWindGroundTruth'],
                        source_z=params['ground_truth_z'], sensor_z=terminal['robot_z'],
                        truth_grid_i=i, truth_grid_j=j, truth_owner_leaf=matched[0]['candidate_id'],
                        native_parity_max_abs=case['native_posterior_parity']['max_abs']))
for filename, data in [('VERIFIED_INPUTS.tsv', inputs), ('CASE_AUDIT_SUMMARY.tsv', summary)]:
    with (root / filename).open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(data[0]), delimiter='\t', lineterminator='\n')
        writer.writeheader()
        writer.writerows(data)
print(json.dumps({'verified_input_count': len(inputs), 'cases': summary,
                  'scientific_scoring_executed': False}, indent=2))
