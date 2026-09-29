#!/usr/bin/env python3
"""Read-only original-config runner audit and 96-row freeze; never runs GADEN."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

from audit_e2_timebase import reconstruct

ROOT = Path('/mnt/hgfs/workspace/GADEN_files/scenarios')
E1 = Path('/home/zyc/e2_repo_20260925/evidence/environment_level_benchmark_v0/e1')
BINARY = Path('/home/zyc/hcmc_gaden_seed_build_20260922/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator')
EXTRACTOR = Path('/home/zyc/rmfe_filament_extractor_omp')
WRITER = Path('/home/zyc/hcmc_gaden_seed_build_20260922/src/GADEN/gaden_common/third_party/gaden_core/src/RunningSimulation.cpp')
HOUSES = ('House01', 'House02', 'House03')
RECORDS = tuple(range(100, 551, 50))
EXPECTED_BINARY = '4127b9ba4f42186ba2d6d33c84fba8d4b92749da59b83750fa4847dbd9957ce1'
EXPECTED_EXTRACTOR = '206cc92384866dcb7d966c6f8f9ec87862e15c7fee460a43c04014b58e3cae91'
EXPECTED_PROBES = '364c7a2f0333c95845cfb7a10dbb96ee8c5f30a47282e508e3961d4eec575812'
SOURCE_ARGS = ('source_location_x', 'source_location_y', 'source_location_z', 'gas_type')
SEED_BASE = 2026900000


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def rows(path: Path, sep: str = '\t') -> list[dict[str, str]]:
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream, delimiter=sep))


def write_rows(path: Path, values: list[dict]) -> None:
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(values[0]), delimiter='\t', lineterminator='\n')
        writer.writeheader()
        writer.writerows(values)


def resolve(value: str, args: dict[str, str]) -> str:
    value = value.replace('$(find-pkg-share vgr_dataset)/scenarios', str(ROOT))
    for key, arg in args.items():
        value = value.replace('$(var ' + key + ')', arg)
    if '$(' in value:
        raise RuntimeError(f'unresolved launch substitution: {value}')
    return value


def parse_config(house: str, wind: str) -> tuple[dict, dict, Path]:
    path = ROOT / house / 'launch' / wind / 'GADEN_ros2.launch'
    tree = ET.parse(path)
    args = {node.attrib['name']: node.attrib['default'] for node in tree.findall('arg')}
    if args['scenario'] != house or args['simulation'] != wind:
        raise RuntimeError(f'launch default drift: {path}')
    simulator = next((n for n in tree.findall('node') if n.attrib.get('exec') == 'filament_simulator'), None)
    if simulator is None:
        raise RuntimeError(f'filament simulator node absent: {path}')
    params = {n.attrib['name']: resolve(n.attrib['value'], args) for n in simulator.findall('param')}
    for key, param in (('source_location_x', 'source_position_x'),
                       ('source_location_y', 'source_position_y'),
                       ('source_location_z', 'source_position_z'), ('gas_type', 'gas_type')):
        if params[param] != args[key]:
            raise RuntimeError(f'source/gas param differs from launch default: {path} {key}')
    if params['sim_time'] != '1000.0' or params['time_step'] != '0.1':
        raise RuntimeError(f'original 1000 s time contract drift: {path}')
    if params['results_time_step'] != '0.5' or params['wind_time_step'] != '1.0':
        raise RuntimeError(f'writer/wind time contract drift: {path}')
    if (params['allow_looping'], params['loop_from_step'], params['loop_to_step']) != ('true', '1', '10'):
        raise RuntimeError(f'wind loop drift: {path}')
    occupancy = ROOT / house / 'OccupancyGrid3D.csv'
    if params['occupancy3D_data'] != str(occupancy):
        raise RuntimeError(f'occupancy path drift: {path}')
    source_xyz = tuple(float(args[k]) for k in SOURCE_ARGS[:3])
    gas_dir = ROOT / house / 'gas_simulations' / wind / (
        f'FilamentSimulation_gasType_{args["gas_type"]}_sourcePosition_'
        f'{args["source_location_x"]}_{args["source_location_y"]}_{args["source_location_z"]}')
    if not gas_dir.is_dir() or len(list(gas_dir.glob('iteration_*'))) != 2000:
        raise RuntimeError(f'original gas directory/2000 records absent: {gas_dir}')
    if params['results_location'] != str(gas_dir):
        raise RuntimeError(f'original result path drift: {path}')
    prefix = ROOT / house / 'wind_simulations' / wind / wind
    if params['wind_data'] != str(prefix) + '_':
        raise RuntimeError(f'original wind prefix drift: {path}')
    return dict(house=house, wind_config=wind, source_xyz=source_xyz,
                source_x_text=args['source_location_x'], source_y_text=args['source_location_y'],
                source_z_text=args['source_location_z'], gas_type=args['gas_type'],
                original_launch=str(path), original_launch_sha256=sha(path),
                original_gas_dir=str(gas_dir), occupancy=str(occupancy),
                wind_prefix=str(prefix)), params, path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--timebase-map', type=Path, required=True)
    parser.add_argument('--timebase-provenance', type=Path, required=True)
    args = parser.parse_args()
    if sha(BINARY) != EXPECTED_BINARY or sha(EXTRACTOR) != EXPECTED_EXTRACTOR:
        raise RuntimeError('pinned binary or concentration extractor drift')
    provenance = json.loads(args.timebase_provenance.read_text(encoding='utf-8'))
    if provenance['original_e2_binary_sha256'] != EXPECTED_BINARY or sha(WRITER) != provenance['writer_source_sha256']:
        raise RuntimeError('writer implementation/timebase provenance drift')
    probe_file = E1 / 'E1_HOUSE_PROBE_CONTRACTS.tsv'
    if sha(probe_file) != EXPECTED_PROBES:
        raise RuntimeError('frozen E1 observation operator drift')
    probes = rows(probe_file)
    by_house = defaultdict(list)
    for p in probes:
        by_house[p['house']].append(p)
    for house in HOUSES:
        occupancy = ROOT / house / 'OccupancyGrid3D.csv'
        header = occupancy.read_text(encoding='utf-8').splitlines()[:4]
        nx, ny = (int(v) for v in header[2].split()[1:3])
        if len(by_house[house]) != 30:
            raise RuntimeError(f'not 30 source-blind probes in {house}')
        for p in by_house[house]:
            x0, x1, y0, y1 = (int(p[k]) for k in ('native_x0', 'native_x1_exclusive',
                                                'native_y0', 'native_y1_exclusive'))
            if not (0 <= x0 < x1 <= nx and 0 <= y0 < y1 <= ny and x1-x0 == y1-y0 == 2):
                raise RuntimeError(f'probe footprint out of bounds: {house} {p["probe_rank"]}')
            if float(p['z_m']) != 0.2 or int(p['native_cell_count']) != 4:
                raise RuntimeError(f'probe height or pooling contract drift: {house}')
    records = rows(args.timebase_map, ',')
    planned_time = reconstruct(1000.0)
    if len(records) != 10 or len(planned_time) <= max(RECORDS):
        raise RuntimeError('ten writer records unavailable')
    for r, record_id in zip(records, RECORDS):
        t = planned_time[record_id]
        if (int(r['save_record_id']), float(r['clock_before_s']), int(r['active_wind_index'])) != (
                record_id, t['clock_before_s'], t['active_wind_index']):
            raise RuntimeError(f'pinned-binary writer map drift at {record_id}')
    configs, parameter_maps, fingerprints, hashes, missing_wind, conflicting_wind = [], [], [], [], [], []
    def nested_copy(path: Path) -> Path:
        house = path.parts[len(ROOT.parts)]
        return ROOT / house / house / Path(*path.parts[len(ROOT.parts)+1:])
    def asset(kind: str, path: Path) -> None:
        if not path.is_file():
            if kind != 'original_wind':
                raise RuntimeError(f'missing {kind}: {path}')
            missing_wind.append(str(path))
            hashes.append(dict(asset_kind=kind, path=str(path), bytes='', sha256='', status='MISSING'))
            nested = nested_copy(path)
            if nested.is_file():
                hashes.append(dict(asset_kind='nested_copy_for_missing_wind', path=str(nested),
                                   bytes=nested.stat().st_size, sha256=sha(nested), status='BACKUP_ONLY'))
            return
        digest = sha(path)
        status = 'PRESENT'
        if kind == 'original_wind' and '/House02/' in str(path):
            nested = nested_copy(path)
            if nested.is_file() and sha(nested) != digest:
                conflicting_wind.append(str(path))
                status = 'PRESENT_BUT_DIFFERS_FROM_NESTED'
        hashes.append(dict(asset_kind=kind, path=str(path), bytes=path.stat().st_size,
                           sha256=digest, status=status))
    for house in HOUSES:
        wind_dirs = sorted(p.name for p in (ROOT / house / 'launch').iterdir() if p.is_dir())
        if len(wind_dirs) != 4:
            raise RuntimeError(f'expected four original launch wind configs: {house}')
        asset('occupancy', ROOT / house / 'OccupancyGrid3D.csv')
        for wind in wind_dirs:
            config, params, path = parse_config(house, wind)
            configs.append(config)
            parameter_maps.append(params)
            fingerprints.append({k: v for k, v in params.items() if k not in (
                'source_position_x', 'source_position_y', 'source_position_z',
                'gas_type', 'wind_data', 'occupancy3D_data', 'results_location')})
            asset('original_ros2_launch', path)
            asset('original_ros1_launch', path.with_name('GADEN_ros1.launch'))
            for i in range(11):
                for suffix in ('.csv', '.csv_U', '.csv_V', '.csv_W'):
                    asset('original_wind', Path(config['wind_prefix'] + f'_{i}' + suffix))
            if len(list((Path(config['original_gas_dir']) / 'wind').glob('wind_iteration_*'))) != 11:
                raise RuntimeError(f'original wind-state bank incomplete: {wind}')
    if len(configs) != 12 or any(p != fingerprints[0] for p in fingerprints[1:]):
        raise RuntimeError('12 configurations do not share the non-source launch parameters')
    asset('pinned_simulator_binary', BINARY)
    asset('pinned_extractor', EXTRACTOR)
    asset('e1_probe_contract', probe_file)
    asset('e2c_timebase_map', args.timebase_map)
    asset('e2c_timebase_provenance', args.timebase_provenance)
    asset('writer_source', WRITER)
    source_ids = {}
    for house in HOUSES:
        xyz = sorted({c['source_xyz'] for c in configs if c['house'] == house})
        if len(xyz) != 2:
            raise RuntimeError(f'expected two configured physical sources: {house}')
        source_ids.update({(house, x): f'{house}_configured_{i+1}' for i, x in enumerate(xyz)})
    catalog = []
    seed_rows = []
    split_rows = []
    command_rows = []
    for ci, c in enumerate(configs):
        sid = source_ids[(c['house'], c['source_xyz'])]
        catalog.append(dict(config_index=ci, house=c['house'], source_id=sid,
                            wind_config=c['wind_config'], x_m=c['source_xyz'][0],
                            y_m=c['source_xyz'][1], z_m=c['source_xyz'][2],
                            gas_type=c['gas_type'], launch_path=c['original_launch'],
                            launch_sha256=c['original_launch_sha256'],
                            wind_prefix=c['wind_prefix'], occupancy=c['occupancy'],
                            original_gas_dir=c['original_gas_dir']))
        for rep in range(1, 9):
            seed = SEED_BASE + ci*100 + rep
            role = ('SEALED_EXTERNAL_HOUSE_CONFIRMATION' if c['house'] == 'House03'
                    else 'DISCOVERY' if rep <= 4 else 'SEALED_STOCHASTIC_CONFIRMATION')
            relpath = f'{c["house"]}/{c["wind_config"]}/{sid}/r{rep}_seed{seed}'
            seed_rows.append(dict(config_index=ci, house=c['house'], source_id=sid,
                                  wind_config=c['wind_config'], x_m=c['source_xyz'][0],
                                  y_m=c['source_xyz'][1], z_m=c['source_xyz'][2],
                                  gas_type=c['gas_type'], replicate_index=rep,
                                  requested_seed=seed, role=role, output_relative_path=relpath))
            split_rows.append(dict(config_index=ci, house=c['house'], source_id=sid,
                                   wind_config=c['wind_config'], replicate_index=rep,
                                   requested_seed=seed, role=role))
            original_params = parameter_maps[ci]
            effective_params = dict(original_params)
            effective_params['results_location'] = '<APPROVED_OUTPUT_ROOT>/' + relpath
            changed = {k for k in original_params if original_params[k] != effective_params[k]}
            if changed != {'results_location'} or set(original_params) != set(effective_params):
                raise RuntimeError('runtime ROS parameter changes exceed output path')
            if tuple(float(effective_params['source_position_'+k]) for k in 'xyz') != c['source_xyz']:
                raise RuntimeError('command changes configured source coordinates')
            if effective_params['gas_type'] != c['gas_type'] or effective_params['wind_data'] != c['wind_prefix']+'_':
                raise RuntimeError('command changes gas or configured wind')
            argv = [str(BINARY), '--ros-args']
            for key, value in effective_params.items():
                argv.extend(('-p', f'{key}:={value}'))
            command_rows.append(dict(config_index=ci, requested_seed=seed,
                                     original_launch_sha256=c['original_launch_sha256'],
                                     original_parameter_map=original_params,
                                     effective_parameter_map=effective_params,
                                     changed_ros_parameters=sorted(changed),
                                     environment_override={'GADEN_RNG_SEED': str(seed)},
                                     argv=argv))
    if len(seed_rows) != 96 or len({r['requested_seed'] for r in seed_rows}) != 96:
        raise RuntimeError('seed count/collision')
    if Counter(r['role'] for r in seed_rows) != Counter(DISCOVERY=32,
                 SEALED_STOCHASTIC_CONFIRMATION=32, SEALED_EXTERNAL_HOUSE_CONFIRMATION=32):
        raise RuntimeError('split count drift')
    args.out.mkdir(parents=True, exist_ok=True)
    write_rows(args.out / 'ORIGINAL_CONFIG_CATALOG.tsv', catalog)
    write_rows(args.out / 'SEED_MANIFEST_96.tsv', seed_rows)
    write_rows(args.out / 'SPLIT_MANIFEST.tsv', split_rows)
    write_rows(args.out / 'PRE_RUN_SHA256.tsv', hashes)
    (args.out / 'RUNNER_COMMAND_CONTRACT.json').write_text(
        json.dumps(dict(common_non_source_launch_params=fingerprints[0],
                        intended_commands=command_rows,
                        no_simulator_invoked=True), indent=2, sort_keys=True) + '\n', encoding='utf-8')
    audit = dict(decision='OCB_R1_FOUNDATION_HOLD_WIND_ASSET_INTEGRITY'
                 if missing_wind or conflicting_wind else
                 'OCB_R1_FOUNDATION_AUDIT_COMPLETE_SIMULATION_NOT_AUTHORIZED',
                 source_count=6, config_count=12, planned_runs=96,
                 source_location_overrides=0, seeds_unique=96,
                 split_counts=dict(Counter(r['role'] for r in seed_rows)),
                 original_launch_sim_time_s=1000,
                 original_saved_iteration_count_per_config=2000,
                 pinned_binary_reconstructed_1000s_record_count=len(planned_time),
                 record_ids=list(RECORDS), record_time_map_matches_pinned_binary=True,
                 original_2000_record_time_map_certified=False,
                 e1_30probe_2x2_contract_valid_all_houses=True,
                 wind_files_hashed=sum(r['asset_kind']=='original_wind' and r['status']=='PRESENT' for r in hashes),
                 wind_files_missing=missing_wind,
                 wind_files_conflicting_with_nested_copy=conflicting_wind,
                 original_launch_wind_input_complete=not missing_wind and not conflicting_wind,
                 no_concentration_values_read=True, no_simulator_invoked=True)
    (args.out / 'FOUNDATION_AUDIT.json').write_text(
        json.dumps(audit, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(audit, sort_keys=True))


if __name__ == '__main__':
    main()
