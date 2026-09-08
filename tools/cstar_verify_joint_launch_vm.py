"""Read-only real-asset tests for the prospective PMFS launch binding."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from closed_loop.ctpi.cstar_launch_binding import validate_launch_binding


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--preflight', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    report = json.loads(args.preflight.read_text())
    geometry_path = Path(report['inputs']['geometry'])
    geometry = json.loads(geometry_path.read_text())
    rows = []
    for house, start in [('H01', (-3.17, -1.75)), ('H02', (-.5, -2.5)), ('H03', (2., 0.))]:
        g = geometry[house]
        realization = next(r['realization_path'] for r in report['entries'] if r['house'] == house)
        values = dict(cstar_environment_preflight=str(args.preflight.resolve()),
                      cstar_geometry_manifest=str(geometry_path), cstar_house=house,
                      raw_gas_results=realization, raw_query_executable=report['inputs']['helper'],
                      gmrf_map_yaml_file=g['map_yaml_path'], vgr_data_path=str(Path(g['occupancy_path']).parent),
                      flight_height='0.3', seed='12', deltaTime='0.2',
                      gaden_iteration_mode='seeded_time_replay', sensor_model_mode='dynamic',
                      start_x=str(start[0]), start_y=str(start[1]))
        accepted = validate_launch_binding(values.__getitem__)
        values['gmrf_map_yaml_file'] = str(Path(values['vgr_data_path']) / 'occupancy.yaml')
        try:
            validate_launch_binding(values.__getitem__)
        except ValueError as exc:
            if 'LAUNCH_GMRF_MAP_PATH' not in str(exc):
                raise
            rejected = str(exc)
        else:
            raise AssertionError('LEGACY_GMRF_MAP_NOT_REJECTED')
        rows.append(dict(house=house, corrected_map_pass=accepted, legacy_map_rejection=rejected))
    args.out.write_text(json.dumps(dict(pass_=True, tests=6, rows=rows,
                         closed_loop_ran=False, scope='launch input guard only'), indent=2) + '\n')
    print('JOINT_LAUNCH_BINDING: 3 corrected maps accepted, 3 legacy map paths rejected')


if __name__ == '__main__':
    main()
