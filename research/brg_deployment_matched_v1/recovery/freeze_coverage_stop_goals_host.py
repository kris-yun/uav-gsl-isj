"""Freeze source-blind stop-and-sample coverage goals from the V2 map path."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
ROUTES = Path(r'C:\Users\50176\Desktop\vm数据\BRG_V1_COVERAGE_ROUTES_20260928')
TARGET = ROOT / 'COVERAGE_STOP_GOALS_FREEZE_V3.json'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    v2_file = ROOT / 'COVERAGE_ROUTE_FREEZE_V2.json'
    v2 = json.loads(v2_file.read_text())
    if v2['status'] != 'SOURCE_BLIND_COVERAGE_ROUTE_FROZEN_V2':
        raise RuntimeError('V2 geometry freeze missing')
    indices = list(range(119, 1501, 119))
    if len(indices) != 12:
        raise RuntimeError('unexpected fixed coverage goal count')
    records = []
    for item in v2['records']:
        env = item['environment_index']
        route = ROUTES / f'env_{env}_coverage.npz'
        if sha(route) != item['route_file_sha256']:
            raise RuntimeError('V2 route bytes changed before stop-goal freeze')
        with np.load(route, allow_pickle=False) as saved:
            xy = saved['position_xy_m']
            times = saved['time_s']
        if len(xy) != 1501 or not np.array_equal(times, np.arange(1501) * .2):
            raise RuntimeError('V2 path time geometry changed')
        goals = [[float(v) for v in xy[index]] for index in indices]
        if len({(round(x, 6), round(y, 6)) for x, y in goals}) != 12:
            raise RuntimeError('coverage stop goals are not distinct')
        records.append({'environment_index': env, 'house': item['house'],
                        'route_file_sha256': sha(route), 'waypoint_indices': indices,
                        'goal_xy_m': goals})
    result = {'status': 'SOURCE_BLIND_STOP_AND_SAMPLE_GOALS_FROZEN_V3',
              'parent_v2_freeze_sha256': sha(v2_file),
              'selection_rule': 'every seventh 3.4s segment endpoint of frozen V2 legal-cell route',
              'goal_count_per_environment': 12,
              'pilot_v2_rejected_due_to_sensor_position_contract': True,
              'pilot_v2_archive_sha256':
                  'fd86348bbf9c9f7965ed3b0b8cb4e2f82704ed3a303411b2c632a319a0b1c911',
              'source_truth_used': False, 'plume_outcome_used': False,
              'records': records}
    payload = json.dumps(result, indent=2) + '\n'
    if TARGET.exists():
        if TARGET.read_text() != payload:
            raise RuntimeError('existing V3 goal freeze changed')
    else:
        TARGET.write_text(payload)
    print(json.dumps({'status': result['status'], 'sha256': sha(TARGET),
                      'goal_counts': [len(r['goal_xy_m']) for r in records]}))


if __name__ == '__main__':
    main()
