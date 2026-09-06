"""Small truth-blind controlled design. Reads geometry, never source or gas.

The output is an offline kinematic intervention, not a Nav2 tracking claim.
Commit this output before running the outcome extractor.
"""
import argparse
from collections import deque
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / 'evidence/cstar_environment_20260906'
DT = 0.2
SPEED = 0.5
DURATION = 60.0
DECISIONS = list(range(8, 57, 8))
HORIZON = 4.0
STARTS = {'H01': (-3.17, -1.75), 'H02': (-0.5, -2.5), 'H03': (2.0, 0.0)}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


class Grid:
    def __init__(self, house):
        self.meta = json.loads((ENV / 'maps_v1/geometry_manifest.json').read_text())[house]
        self.origin = self.meta['origin_xy_m']
        self.res = self.meta['resolution_m']
        candidate = ENV / 'maps_v1' / house / 'candidate.csv'
        assert sha(candidate) == self.meta['free_space_probe_csvs'][0]['sha256']
        with candidate.open() as f:
            self.free = {self.cell((float(r['x']), float(r['y']))) for r in csv.DictReader(f)}
        # One fine cell of clearance on all sides; never shrink source support.
        self.safe = {p for p in self.free if all((p[0]+dx, p[1]+dy) in self.free
                     for dx in (-1, 0, 1) for dy in (-1, 0, 1))}

    def cell(self, xy):
        return tuple(math.floor((xy[k]-self.origin[k])/self.res + 1e-9) for k in (0, 1))

    def xy(self, cell):
        return tuple(self.origin[k]+(cell[k]+0.5)*self.res for k in (0, 1))

    def bfs(self, starts):
        dist = {p: 0 for p in sorted(starts)}
        parent = {p: None for p in dist}
        queue = deque(dist)
        while queue:
            x, y = queue.popleft()
            for q in ((x-1, y), (x, y-1), (x, y+1), (x+1, y)):
                if q in self.safe and q not in dist:
                    dist[q] = dist[(x, y)]+1
                    parent[q] = (x, y)
                    queue.append(q)
        return dist, parent

    @staticmethod
    def path(parent, end):
        path = []
        while end is not None:
            path.append(end)
            end = parent[end]
        return path[::-1]

    def audit(self, points):
        for a, b in zip(points, points[1:]):
            distance = math.dist(a, b)
            assert distance <= SPEED*DT+1e-8, ('speed', distance)
            # Check full connecting segment every <= 1 cm, not endpoints alone.
            n = max(1, math.ceil(distance/0.01))
            for i in range(n+1):
                p = tuple(a[k]+(b[k]-a[k])*i/n for k in (0, 1))
                assert self.cell(p) in self.safe, ('collision', p)


def sample(polyline, duration):
    points, index, current = [tuple(polyline[0])], 1, tuple(polyline[0])
    for _ in range(round(duration/DT)):
        budget = SPEED*DT
        while index < len(polyline):
            target = tuple(polyline[index])
            distance = math.dist(current, target)
            if distance <= budget+1e-12:
                current, budget, index = target, max(0.0, budget-distance), index+1
            else:
                current = tuple(current[k]+(target[k]-current[k])*budget/distance for k in (0, 1))
                break
        points.append(current)
    return points


def coverage(grid, start):
    origin_cell = grid.cell(start)
    assert origin_cell in grid.safe, 'START_REQUIRES_CLEARANCE'
    visited, current = {origin_cell}, origin_cell
    polyline = [start, grid.xy(origin_cell)]
    length = math.dist(*polyline)
    while length < SPEED*DURATION+1:
        remoteness, _ = grid.bfs(visited)
        target = min(remoteness, key=lambda p: (-remoteness[p], p))
        if remoteness[target] == 0:
            break
        _, parent = grid.bfs({current})
        path = grid.path(parent, target)
        polyline.extend(grid.xy(p) for p in path[1:])
        length += (len(path)-1)*grid.res
        visited.update(path)
        current = target
    return sample(polyline, DURATION)


def alternatives(grid, start):
    cell = grid.cell(start)
    distance, parent = grid.bfs({cell})
    initial = math.dist(start, grid.xy(cell))
    reachable = [p for p in distance if distance[p]*grid.res+initial <= SPEED*HORIZON+1e-9]
    chosen, result = set(), []
    for k in range(3):
        heading = 2*math.pi*k/3
        def score(p):
            x, y = grid.xy(p)
            return ((x-start[0])*math.cos(heading)+(y-start[1])*math.sin(heading), distance[p])
        target = min((p for p in reachable if p not in chosen), key=lambda p: (-score(p)[0], -score(p)[1], p))
        chosen.add(target)
        result.append(sample([start]+[grid.xy(p) for p in grid.path(parent, target)], HORIZON))
    return result


def write_route(root, rel, points, offset):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['t_sim_s', 'x', 'y', 'z'])
        for i, p in enumerate(points):
            w.writerow([round(offset+i*DT, 9), *p, 0.3])
    return {'path': rel, 'sha256': sha(path), 'frame_count': len(points)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    result = {'contract': 'CSTAR_TRUTH_BLIND_ROUTE_FREEZE_V1',
        'generator_git_sha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'generator_sha256': sha(__file__), 'seed': 12, 'dt_s': DT,
        'history_duration_s': DURATION, 'prediction_horizon_s': HORIZON,
        'decision_times_s': DECISIONS, 'm1_prefix_times_s': list(range(4, 61, 4)),
        'first_hit_threshold_ppm': 0.1, 'first_hit_rule': 'strictly greater than threshold; future frames only',
        'speed_m_s': SPEED, 'geometry_clearance_cells': 1,
        'route_construction': 'farthest-from-visited graph tour; three fixed 120-degree endpoint projections at each context',
        'outcome_read_before_route_freeze': False, 'source_truth_used': False,
        'execution_kind': 'offline fixed-route GADEN replay; point kinematics, not Nav2 tracking or acceleration qualification',
        'timebase': 'unchanged VGR seeded_time_replay; one stored 0.5s iteration per 0.2s sensor step (2.5x field replay)',
        'sensor_manifest_sha256': sha(ENV / 'probes_v1/H01/sensor_manifest.json'),
        'sensor_state_model_input': 'absent; simulator delay queue and raw gas are evaluator-only',
        'sampling_policy': 'retain every frozen case including all-zero, saturated and duplicate-outcome cases',
        'houses': {}}
    for house in STARTS:
        grid = Grid(house)
        points = coverage(grid, STARTS[house])
        grid.audit(points)
        row = {'geometry_identity': grid.meta['geometry_identity'],
               'history': write_route(args.out, f'{house}/history_route.csv', points, 0), 'routes': []}
        for decision in DECISIONS:
            for index, future in enumerate(alternatives(grid, points[round(decision/DT)])):
                grid.audit(future)
                route = write_route(args.out, f'{house}/t{decision:02d}_a{index}.csv', future, decision)
                route.update({'decision_time_s': decision, 'action_index': index})
                row['routes'].append(route)
        result['houses'][house] = row
    dump(args.out / 'ROUTE_FREEZE.json', result)
    print(json.dumps({'verdict': 'TRUTH_BLIND_GEOMETRY_ROUTES_FROZEN', 'houses': 3,
                      'history_routes': 3, 'future_routes': 63, 'sha256': sha(args.out / 'ROUTE_FREEZE.json')}))


if __name__ == '__main__':
    main()
