#!/usr/bin/env python3
"""Read-only verification of the attached Native support audit.
No ROS, training, gas observations, forward simulations or closed-loop scoring.
Usage: python verify_support.py --input INPUT.zip --out OUTPUT_DIRECTORY
Uses only the Python standard library.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import math
from collections import deque
from pathlib import Path
import zipfile

EXPECTED_SHA = '453ac894df2655b6dfe179df657c3cb0ce8b1664f7a7158796f7b78f505be500'

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def save_json(path: Path, obj: object) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')

def save_tsv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError('No rows to export')
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter='\t', lineterminator='\n')
        w.writeheader()
        w.writerows(rows)

def run(inp: Path, out: Path) -> None:
    payload = inp.read_bytes()
    if sha(payload) != EXPECTED_SHA:
        raise ValueError('Unexpected input SHA256; do not silently accept a different contract')
    out.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        checks = []
        for line in z.read('SHA256SUMS').decode().splitlines():
            expected, name = line.split(maxsplit=1)
            name = name.strip()
            actual = sha(z.read(name))
            checks.append({'path': name, 'sha256': actual, 'match': actual == expected})
        if not all(c['match'] for c in checks):
            raise ValueError('Manifest mismatch')
        report = json.loads(z.read('audit/RESULT.json'))
        belief = json.loads(z.read('audit/NATIVE_INITIALIZATION_AND_SOFTWARE_CHECK_BELIEFS.jsonl').splitlines()[0])
        # Later software-smoke belief records are not used as scientific outcomes.
        if belief['stage'] != 'initialized' or belief['time_s'] != 0:
            raise ValueError('Expected time-zero initialization')
        nx, ny = belief['width'], belief['height']
        cells = belief['free_cells']
        legal = set(cells)
        if len(cells) != len(legal) or cells != sorted(cells):
            raise ValueError('Noncanonical Native support ordering')
        metadata = {}
        values = []
        for line in z.read('inputs/OccupancyGrid3D.csv').decode().splitlines():
            parts = line.split()
            if not parts or parts == [';']:
                continue
            if parts[0].startswith('#'):
                metadata[parts[0]] = parts[1:]
            else:
                values.extend(int(p) for p in parts)
        fx, fy, fz = map(int, metadata['#num_cells'])
        fine_dx = float(metadata['#cell_size(m)'][0])
        origin = list(map(float, metadata['#env_min(m)']))
        zi = int((0.2 - origin[2]) / fine_dx)
        if len(values) != fx * fy * fz:
            raise ValueError('Occupancy dimensions do not match')
        def voxel(i: int, j: int) -> int:
            return values[(zi * fx + i) * fy + j]
        reduced = bytes(int(all(voxel(3*i+a, 3*j+b) == 0
                                for a in range(3) for b in range(3)))
                        for j in range(ny) for i in range(nx))
        if reduced != z.read('audit/native_fine_reduced_occupancy.u8'):
            raise ValueError('Independent coarse occupancy reduction differs')
        dx, ox, oy = belief['resolution'], belief['origin_x'], belief['origin_y']
        sx = int((2.0 - ox) / dx)
        sy = int((0.0 - oy) / dx)
        start = sx + sy*nx
        if reduced[start] != 1:
            raise ValueError('Native fixed start is not free')
        # Reachability only: the supplied Native code traverses all free 8-neighbours.
        seen = {start}
        queue = deque([start])
        while queue:
            cell = queue.popleft()
            i, j = cell % nx, cell // nx
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    ii, jj = i+di, j+dj
                    if not (0 <= ii < nx and 0 <= jj < ny):
                        continue
                    cc = ii+jj*nx
                    if reduced[cc] == 1 and cc not in seen:
                        seen.add(cc)
                        queue.append(cc)
        rebuilt = bytes(int(c in seen) for c in range(nx*ny))
        saved = z.read('audit/native_verified_legal_occupancy.u8')
        if rebuilt != saved or seen != legal:
            raise ValueError('Reachability mask disagrees with runtime initialization')
        stored_q = belief['source_map']
        if len(stored_q) != nx * ny:
            raise ValueError('Unexpected full-grid source map storage size')
        # Native initializes every storage slot; legality is defined by free_cells.
        initial_q = [stored_q[c] for c in cells]
        if not all(abs(p-1/len(cells)) < 1e-15 for p in initial_q):
            raise ValueError('Initial source prior not uniform on legal support')
        support_rows = []
        for c in cells:
            i, j = c % nx, c // nx
            support_rows.append({
                'source_id': f'pmfs_{i}_{j}', 'grid_index': c,
                'grid_i': i, 'grid_j': j,
                'x_from_runtime_metadata_m': ox+(i+0.5)*dx,
                'y_from_runtime_metadata_m': oy+(j+0.5)*dx,
                'initial_prior': 1/len(cells),
            })
        # No reported probability values, trajectories or scores are used below.
        truths = list(csv.DictReader(io.StringIO(z.read('audit/HOUSE03_F1_TRUTH_PANEL_12.tsv').decode()), delimiter='\t'))
        truth_rows = []
        near_rows = []
        for t in truths:
            x, y = float(t['x_m']), float(t['y_m'])
            cell = int(t['pmfs_i']) + nx * int(t['pmfs_j'])
            distances = [(math.hypot(r['x_from_runtime_metadata_m']-x,
                                    r['y_from_runtime_metadata_m']-y), r)
                         for r in support_rows]
            distances.sort(key=lambda pair: (pair[0], pair[1]['grid_index']))
            truth_rows.append({
                'pair_id': t['pair_id'], 'source_id': t['source_id'],
                'true_grid_index': cell, 'x_m': x, 'y_m': y, 'z_m': float(t['z_m']),
                'truth_in_native_support': cell in legal,
                'nearest_native_source': distances[0][1]['source_id'],
                'nearest_native_center_distance_m': distances[0][0],
                'native_centers_within_0p5m': sum(d <= 0.5 for d, _ in distances),
                'recommended_reporting_stratum': 'in_support' if cell in legal else 'support_misspecification',
            })
            if cell not in legal:
                for d, r in distances[:10]:
                    near_rows.append({'truth_id': t['source_id'], 'candidate_id': r['source_id'],
                                      'candidate_grid_index': r['grid_index'],
                                      'candidate_x_m': r['x_from_runtime_metadata_m'],
                                      'candidate_y_m': r['y_from_runtime_metadata_m'],
                                      'distance_m': d, 'within_existing_0p5m': d <= 0.5})
        removed_checks = []
        for r in report['removed_candidates']:
            i, j = r['grid_i'], r['grid_j']
            block = [[voxel(3*i+a, 3*j+b) for b in range(3)] for a in range(3)]
            counts = {str(v): sum(x==v for row in block for x in row) for v in (0,1,2)}
            if block != r['raw_3x3_values'] or counts != r['raw_3x3_counts']:
                raise ValueError('Removed candidate fine block mismatch')
            removed_checks.append({'source_id': r['source_id'], 'grid_index': r['grid_index'],
                                   'raw_block_matches': True, 'native_coarse_free': bool(reduced[r['grid_index']]),
                                   'fine_voxels_obstacle': counts['1'], 'fine_voxels_other_blocked': counts['2']})
        summary = {
            'input_sha256': sha(payload), 'input_size': len(payload),
            'original_decision_preserved': report['decision'],
            'manifest_entries_verified': len(checks),
            'coarse_occupancy_reduction_independently_rebuilt': True,
            'coarse_free_count': sum(reduced),
            'eight_neighbour_reachability_independently_rebuilt': True,
            'runtime_native_support_count': len(legal),
            'native_support_mask_sha256': sha(saved),
            'native_support_ordering': 'ascending full-grid index, matching initialized free_cells',
            'native_initial_prior_uniform_on_free_cells': True,
            'source_map_storage_count': len(stored_q),
            'blocked_initial_storage_values_are_not_legal_source_classes': True,
            'excluded_truth_ids': [r['source_id'] for r in truth_rows if not r['truth_in_native_support']],
            'all_twelve_have_native_center_within_existing_0p5m': all(r['native_centers_within_0p5m'] > 0 for r in truth_rows),
            'geometry_only_no_success_prediction': True,
            'native_cpp_binary_rerun': False, 'new_forward': 0, 'new_plume': 0,
            'gas_values_read': 0, 'models_trained': 0, 'scored_campaign_runs': 0,
            'contract_status': 'PROPOSED_AMENDMENT_REQUIRES_MAIN_THREAD_SIGNATURE',
            'attachment_does_not_include_complete_primary_endpoint_clause_06': True,
        }
        save_json(out/'VERIFY_RESULT.json', summary)
        save_json(out/'MANIFEST_CHECK.json', checks)
        save_json(out/'REMOVED_FINE_BLOCK_CHECK.json', removed_checks)
        save_tsv(out/'NATIVE_615_IDS.tsv', support_rows)
        save_tsv(out/'TRUTH_SUPPORT_GEOMETRY.tsv', truth_rows)
        save_tsv(out/'EXCLUDED_TRUTH_NEAREST_CANDIDATES.tsv', near_rows)
        (out/'NATIVE_615_MASK.u8').write_bytes(saved)
        print(json.dumps(summary, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--input',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    run(args.input,args.out)
