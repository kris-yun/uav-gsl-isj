#!/usr/bin/env python3
"""Select source-unseen E2C confirmation pairs from frozen E1 geometry."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

E1_SCRIPT = Path('/home/zyc/e2_repo_20260925/research/environment_level_benchmark_v0/build_e1_cross_house_contract_vm.py')
E1_PANEL = Path('/home/zyc/e2_repo_20260925/evidence/environment_level_benchmark_v0/e1/E1_HOUSE_SOURCE_PANELS.tsv')
EXPECTED_E1_PANEL_SHA = 'e38bee4467fb9d98ab5ee48a6115eb1b3306df63cd3da409b9412b3032c4b06e'
EXPECTED_EXPOSURE_UNION_SHA = '9b6995bdcdffbdc99f593982b77a4b966ae84d33c45dfa45734a203131053527'
SCENARIOS = Path('/mnt/hgfs/workspace/GADEN_files/scenarios')


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_e1():
    spec = importlib.util.spec_from_file_location('e1_geometry_for_e2c', E1_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--exposure-union', type=Path, required=True)
    args = ap.parse_args()
    if sha(E1_PANEL) != EXPECTED_E1_PANEL_SHA:
        raise RuntimeError('E1 source panel hash drift')
    if sha(args.exposure_union) != EXPECTED_EXPOSURE_UNION_SHA:
        raise RuntimeError('prior source-exposure union drift')
    e1 = load_e1()
    with E1_PANEL.open(newline='') as f:
        old_rows = list(csv.DictReader(f, delimiter='\t'))
    with args.exposure_union.open(newline='', encoding='utf-8') as f:
        excluded = {(r['house'], r['source_id']) for r in csv.DictReader(f, delimiter='\t')}
    all_rows = []
    audit = {'e1_script_sha256': sha(E1_SCRIPT), 'e1_panel_sha256': sha(E1_PANEL),
             'exposure_union_sha256': sha(args.exposure_union),
             'geometry_and_frozen_exposure_only': True, 'houses': {}}
    for house in ('House01', 'House02', 'House03'):
        headers, occ = e1.GATE.read_occ(SCENARIOS / house / 'OccupancyGrid3D.csv')
        env_min = np.asarray(headers['env_min(m)'], dtype=float)
        cell = float(headers['cell_size(m)'][0])
        nav_free, nav_meta, nav_paths = e1.nav_for(house, env_min)
        original, _ = e1.sources_for(house, occ, env_min, cell, nav_free, nav_meta, .20)
        expected = [r for r in old_rows if r['house'] == house]
        for a, b in zip(original, expected, strict=True):
            if (a['source_id'] != b['source_id'] or a['role'] != b['role'] or
                int(a['pair_id']) != int(b['pair_id']) or
                any(abs(float(a[k]) - float(b[k])) > 1e-12 for k in ('x_m', 'y_m', 'z_m'))):
                raise RuntimeError(f'E1 first-three-pair replay mismatch: {house}')
        iz = e1.GATE.fine_index(.20, float(env_min[2]), cell)
        valid = np.zeros_like(nav_free, dtype=bool)
        index3d = {}
        for i in range(nav_free.shape[0]):
            for j in range(nav_free.shape[1]):
                if not nav_free[i, j]:
                    continue
                x, y = float(env_min[0] + (i + .5) * .30), float(env_min[1] + (j + .5) * .30)
                fi = e1.GATE.fine_index(x, float(env_min[0]), cell)
                fj = e1.GATE.fine_index(y, float(env_min[1]), cell)
                if 0 <= fi < occ.shape[1] and 0 <= fj < occ.shape[2] and occ[iz, fi, fj] == 0:
                    valid[i, j] = True
                    index3d[(i, j)] = (fi, fj)
        eligible = valid.copy()
        for i, j in np.argwhere(valid):
            if (house, f'pmfs_{int(i)}_{int(j)}') in excluded:
                eligible[i, j] = False
        ij = np.argwhere(eligible).astype(np.int64)
        clearance = distance_transform_edt(np.pad(valid, 1, constant_values=False))[1:-1, 1:-1]
        anchors = [(int(r['pmfs_i']), int(r['pmfs_j'])) for r in original if r['role'] == 'anchor']
        used = {(int(r['pmfs_i']), int(r['pmfs_j'])) for r in original}
        offsets = ((1, 0), (0, 1), (-1, 0), (0, -1))
        pair_count = 4 if house == 'House03' else 1
        selected = []
        for pair_number in range(pair_count):
            min_d2 = np.stack([np.sum((ij - np.asarray(a)) ** 2, axis=1)
                               for a in anchors], axis=0).min(axis=0)
            order = sorted(range(len(ij)), key=lambda k: (-int(min_d2[k]), int(ij[k, 0]), int(ij[k, 1])))
            choice = None
            choice_d2 = None
            for k in order:
                anchor = (int(ij[k, 0]), int(ij[k, 1]))
                if anchor in used:
                    continue
                options = []
                for rank, (di, dj) in enumerate(offsets):
                    neighbor = (anchor[0] + di, anchor[1] + dj)
                    if (0 <= neighbor[0] < eligible.shape[0] and 0 <= neighbor[1] < eligible.shape[1] and
                        eligible[neighbor] and neighbor not in used):
                        options.append((-float(clearance[neighbor]), rank, neighbor))
                if options:
                    choice = (anchor, min(options)[2])
                    choice_d2 = int(min_d2[k])
                    break
            if choice is None:
                raise RuntimeError(f'unexposed E1-style pair unavailable: {house} pair {pair_number + 1}')
            if math.dist(choice[0], choice[1]) != 1:
                raise RuntimeError('new pair is not adjacent')
            for point in choice:
                sid = f'pmfs_{point[0]}_{point[1]}'
                if (house, sid) in excluded:
                    raise RuntimeError(f'exposed source selected: {house} {sid}')
                used.add(point)
            anchors.append(choice[0])
            selected.append((choice, choice_d2))
        audit['houses'][house] = dict(occupancy_sha256=sha(SCENARIOS / house / 'OccupancyGrid3D.csv'),
                                     nav_mask_sha256=sha(nav_paths[1]), eligible_source_cells=len(ij),
                                     original_first_three_pairs_match=True,
                                     selected_pairs=[dict(anchor=list(pair[0]), partner=list(pair[1]),
                                                          anchor_min_squared_distance_to_previous_anchors=d2)
                                                     for pair, d2 in selected])
        if house != 'House03':
            for source_index, row in enumerate(original):
                all_rows.append(dict(row, source_index=source_index,
                                     panel_role='DISCOVERY', panel_origin='E1_EXISTING'))
        for pair_offset, (choice, _) in enumerate(selected):
            for point_offset, (role, (i, j)) in enumerate(zip(('anchor', 'partner'), choice)):
                fi, fj = index3d[(i, j)]
                all_rows.append(dict(house=house, pair_id=4 + pair_offset, role=role,
                                     source_id=f'pmfs_{i}_{j}', pmfs_i=i, pmfs_j=j,
                                     x_m=float(env_min[0] + (i + .5) * .30),
                                     y_m=float(env_min[1] + (j + .5) * .30), z_m=.20,
                                     gaden_ix=fi, gaden_iy=fj, gaden_iz=iz,
                                     clearance_m=float(clearance[i, j] * .30),
                                     source_index=(6 + point_offset if house != 'House03'
                                                   else 2 * pair_offset + point_offset),
                                     panel_role=('SEALED_WITHIN_HOUSE_CONFIRMATION' if house != 'House03'
                                                 else 'SEALED_H03_SOURCE_UNSEEN_CONFIRMATION'),
                                     panel_origin='E2C_NEW_GEOMETRY_EXPOSURE_EXCLUSION'))
    if len(all_rows) != 24:
        raise RuntimeError('expected exactly 8 source rows per House')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(all_rows[0]), delimiter='\t', lineterminator='\n')
        writer.writeheader()
        writer.writerows(all_rows)
    args.out.with_suffix('.audit.json').write_text(json.dumps(audit, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(audit, sort_keys=True))


if __name__ == '__main__':
    main()
