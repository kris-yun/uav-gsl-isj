"""No gas payloads: route geometry, timing, and causal sensor branch tests."""
import copy
import json
import math
from cstar_extract_controlled_assets import ROUTES, Grid, route_points, new_sensor, iteration


def main():
    design = json.loads((ROUTES / 'ROUTE_FREEZE.json').read_text())
    for house, data in design['houses'].items():
        grid = Grid(house)
        history = route_points(data['history'])
        assert len(history) == 301
        for route in data['routes']:
            p = route_points(route)
            assert len(p) == 21
            assert p[0] == history[round(route['decision_time_s']/0.2)]
            assert math.isclose(p[-1]['t_sim_s']-p[0]['t_sim_s'], 4.0)
            grid.audit([(r['x'], r['y']) for r in p])
        # Deliberate wall traversal must fail the segment audit.
        try:
            grid.audit([(1e5, 1e5), (1e5, 1e5)])
        except AssertionError:
            pass
        else:
            raise AssertionError('DESTRUCTIVE_COLLISION_NOT_REJECTED')
    sensor = new_sensor()
    for _ in range(40):
        sensor.process(1.0, 0.2)
    a, b, reset = copy.deepcopy(sensor), copy.deepcopy(sensor), new_sensor()
    assert a.process(0.0, 0.2) == b.process(0.0, 0.2)
    assert a.state_ppm != reset.process(0.0, 0.2), 'RESET_BRANCH_FALSE_EQUIVALENCE'
    a.process(10.0, 0.2)
    assert a.time_s != b.time_s and sensor.time_s < b.time_s
    assert iteration(1) == 1050 and iteration(300) == 1349
    print('CSTAR_CONTROLLED_GEOMETRY_TIMING_BRANCH_SELFTEST=PASS')


if __name__ == '__main__':
    main()
