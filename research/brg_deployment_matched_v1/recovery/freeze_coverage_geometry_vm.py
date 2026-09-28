"""Freeze source-blind, occupancy-legal OPEN coverage before any route run."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np

V0 = Path('/home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927')
VGR = Path('/home/zyc/brg_closedloop_20260927/vgr_execution_v2')
sys.path[:0] = [str(V0), str(VGR)]
from pmfs_brg.bank import TemplateBank
from vgr_bridge.mcos_motion_profiles import generate_profile, MotionLimits


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    records = []
    for env, house, start in ((0, 'House01', (-3.17, -1.75)),
                              (1, 'House02', (-.5, -2.5)),
                              (2, 'House02', (-.5, -2.5))):
        path = V0 / f'legal_support_v2/env_{env}_bank.npz'
        bank = TemplateBank.load(path)
        profile = generate_profile('reversal', duration_s=300., dt_s=.2,
                                   start_xy_m=start, heading_rad=0.)
        if not profile.satisfies(MotionLimits()):
            raise RuntimeError('fixed coverage exceeds registered VGR motion envelope')
        cells = set(bank.cells.tolist())
        indices = []
        for x, y in profile.position_xy_m:
            i = int((x - bank.ox) / bank.dx)
            j = int((y - bank.oy) / bank.dx)
            idx = i + bank.nx * j
            if not (0 <= i < bank.nx and 0 <= j < bank.ny and idx in cells):
                raise RuntimeError(f'{house} profile leaves Native legal support at {(x, y)}')
            indices.append(idx)
        records.append({'environment_index': env, 'house': house,
                        'start_xy_m': start, 'profile': 'reversal',
                        'amplitude_m': .5, 'heading_rad': 0., 'duration_s': 300.,
                        'dt_s': .2, 'samples': len(indices),
                        'all_samples_on_native_legal_support': True,
                        'distinct_cells_visited': len(set(indices)),
                        'path_length_m': float(np.linalg.norm(np.diff(profile.position_xy_m, axis=0), axis=1).sum()),
                        'motion_envelope': profile.envelope(),
                        'bank_fingerprint': bank.fingerprint,
                        'bank_file_sha256': sha(path),
                        'profile_positions_sha256': hashlib.sha256(
                            np.asarray(profile.position_xy_m, dtype='<f8').tobytes()).hexdigest()})
    result = {'status': 'SOURCE_BLIND_COVERAGE_GEOMETRY_FROZEN',
              'profile_module_sha256': sha(VGR / 'vgr_bridge/mcos_motion_profiles.py'),
              'records': records, 'source_truth_used': False,
              'plume_concentration_used': False}
    out = Path('/home/zyc/brg_v1_recovery_20260928/COVERAGE_GEOMETRY_FREEZE.json')
    if out.exists():
        if json.loads(out.read_text()) != result:
            raise RuntimeError('coverage geometry freeze drift')
    else:
        out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
