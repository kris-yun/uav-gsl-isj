"""Freeze a source-blind 300 s coverage path on each Native legal map.

The route uses only occupancy/legal support and the fixed start. It never
reads plume, source labels, scores, or House03. Four-neighbor grid travel
uses minimum-jerk 3.4 s segments, respecting the VGR motion envelope.
"""
from __future__ import annotations

from collections import deque
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

V0 = Path('/home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927')
VGR = Path('/home/zyc/brg_closedloop_20260927/vgr_execution_v2')
OUT = Path('/home/zyc/brg_v1_recovery_20260928/coverage_routes')
sys.path[:0] = [str(V0), str(VGR)]
from pmfs_brg.bank import TemplateBank
from vgr_bridge.mcos_motion_profiles import MotionProfile, MotionLimits


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def neighbors(cell: int, cells: set[int], nx: int, ny: int) -> list[int]:
    i, j = cell % nx, cell // nx
    result = []
    for di, dj in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        ni, nj = i + di, j + dj
        other = ni + nx * nj
        if 0 <= ni < nx and 0 <= nj < ny and other in cells:
            result.append(other)
    return sorted(result)


def bfs(start: int, cells: set[int], nx: int, ny: int) -> dict[int, int | None]:
    parent = {start: None}
    pending = deque([start])
    while pending:
        current = pending.popleft()
        for other in neighbors(current, cells, nx, ny):
            if other not in parent:
                parent[other] = current
                pending.append(other)
    return parent


def route(bank: TemplateBank, start_xy: tuple[float, float], segments: int) -> list[int]:
    i = int((start_xy[0] - bank.ox) / bank.dx)
    j = int((start_xy[1] - bank.oy) / bank.dx)
    current = i + bank.nx * j
    legal = set(bank.cells.tolist())
    if current not in legal:
        raise RuntimeError('fixed start outside Native legal support')
    reachable = set(bfs(current, legal, bank.nx, bank.ny))
    visited = {current}
    path = [current]
    while len(path) < segments + 1:
        parent = bfs(current, reachable, bank.nx, bank.ny)
        unvisited = reachable - visited
        if not unvisited:
            visited = {current}
            unvisited = reachable - visited
        # Maximize graph distance, with stable cell-index tie breaking.
        def distance(cell):
            n, v = 0, cell
            while parent[v] is not None:
                n += 1
                v = parent[v]
            return n
        target = sorted(unvisited, key=lambda c: (-distance(c), c))[0]
        reverse = [target]
        while reverse[-1] != current:
            reverse.append(parent[reverse[-1]])
        forward = list(reversed(reverse))[1:]
        for cell in forward:
            path.append(cell)
            visited.add(cell)
            if len(path) >= segments + 1:
                break
        current = path[-1]
    return path


def generate(bank: TemplateBank, start_xy: tuple[float, float]) -> tuple[MotionProfile, list[int]]:
    dt = .2
    segment_s = 3.4
    points_per_segment = int(round(segment_s / dt))
    total_steps = int(round(300 / dt))
    segments = (total_steps + points_per_segment - 1) // points_per_segment
    cells = route(bank, start_xy, segments)
    center = lambda c: np.array([bank.ox + (c % bank.nx + .5) * bank.dx,
                                 bank.oy + (c // bank.nx + .5) * bank.dx])
    anchors = [np.asarray(start_xy, dtype=np.float64), center(cells[0])]
    anchors.extend(center(c) for c in cells[1:])
    position, velocity, acceleration, jerk = [], [], [], []
    for a, b in zip(anchors, anchors[1:]):
        delta = b - a
        for k in range(points_per_segment):
            u = k / points_per_segment
            h = 10 * u**3 - 15 * u**4 + 6 * u**5
            hp = 30 * u**2 - 60 * u**3 + 30 * u**4
            hpp = 60 * u - 180 * u**2 + 120 * u**3
            hppp = 60 - 360 * u + 360 * u**2
            position.append(a + delta * h)
            velocity.append(delta * hp / segment_s)
            acceleration.append(delta * hpp / segment_s**2)
            jerk.append(delta * hppp / segment_s**3)
    position.append(anchors[-1])
    velocity.append(np.zeros(2))
    acceleration.append(np.zeros(2))
    jerk.append(np.zeros(2))
    count = total_steps + 1
    profile = MotionProfile('brg_v1_source_blind_coverage',
            np.arange(count, dtype=np.float64) * dt,
            np.asarray(position[:count]), np.asarray(velocity[:count]),
            np.asarray(acceleration[:count]), np.asarray(jerk[:count]))
    if not profile.satisfies(MotionLimits()):
        raise RuntimeError('route exceeds VGR motion limits')
    legal = set(bank.cells.tolist())
    for x, y in profile.position_xy_m:
        i = int((x - bank.ox) / bank.dx)
        j = int((y - bank.oy) / bank.dx)
        if i + bank.nx * j not in legal:
            raise RuntimeError('source-blind route leaves Native legal map')
    return profile, cells


def main() -> None:
    OUT.mkdir(exist_ok=True)
    records = []
    for env, house, start in ((0, 'House01', (-3.17, -1.75)),
                              (1, 'House02', (-.5, -2.5)),
                              (2, 'House02', (-.5, -2.5))):
        bank_path = V0 / f'legal_support_v2/env_{env}_bank.npz'
        bank = TemplateBank.load(bank_path)
        profile, cells = generate(bank, start)
        path = OUT / f'env_{env}_coverage.npz'
        if not path.exists():
            np.savez_compressed(path, name=np.array(profile.name),
                                time_s=profile.time_s,
                                position_xy_m=profile.position_xy_m,
                                velocity_xy_m_s=profile.velocity_xy_m_s,
                                acceleration_xy_m_s2=profile.acceleration_xy_m_s2,
                                jerk_xy_m_s3=profile.jerk_xy_m_s3)
        with np.load(path) as frozen:
            if not np.array_equal(frozen['position_xy_m'], profile.position_xy_m):
                raise RuntimeError('existing source-blind coverage route drift')
        records.append({'environment_index': env, 'house': house, 'start_xy_m': start,
                        'bank_fingerprint': bank.fingerprint,
                        'bank_file_sha256': sha(bank_path),
                        'route_file': str(path), 'route_file_sha256': sha(path),
                        'waypoint_steps': len(cells), 'distinct_legal_cells_visited': len(set(cells)),
                        'sample_count': len(profile.time_s),
                        'path_length_m': float(np.linalg.norm(np.diff(profile.position_xy_m, axis=0), axis=1).sum()),
                        'motion_envelope': profile.envelope()})
    result = {'status': 'SOURCE_BLIND_COVERAGE_ROUTE_FROZEN_V2',
              'selection_inputs': 'Native legal occupancy cells and fixed start only',
              'source_truth_used': False, 'plume_concentration_used': False,
              'target_results_used': False, 'records': records}
    target = OUT / 'COVERAGE_ROUTE_FREEZE_V2.json'
    if target.exists():
        if json.loads(target.read_text()) != result:
            raise RuntimeError('source-blind route freeze drift')
    else:
        target.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
