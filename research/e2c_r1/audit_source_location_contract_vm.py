#!/usr/bin/env python3
"""Read-only audit of configured VGR/GADEN source locations in House01/02/03."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path('/mnt/hgfs/workspace/GADEN_files/scenarios')
HOUSES = ('House01', 'House02', 'House03')
ARGS = ('source_location_x', 'source_location_y', 'source_location_z', 'gas_type')


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def launch_defaults(path: Path) -> dict[str, str]:
    content = path.read_text(encoding='utf-8')
    values = {}
    for key in ARGS:
        match = re.search(r'<arg\s+name="' + key + r'"\s+default="([^"]+)"', content)
        if not match:
            raise RuntimeError(f'missing {key} in {path}')
        values[key] = match.group(1)
    return values


def configured_rows() -> list[dict]:
    rows = []
    for house in HOUSES:
        launch_root = ROOT / house / 'launch'
        winds = sorted(p for p in launch_root.iterdir() if p.is_dir())
        if len(winds) != 4:
            raise RuntimeError(f'expected four wind configs: {house}: {len(winds)}')
        for wind_dir in winds:
            ros1 = wind_dir / 'GADEN_ros1.launch'
            ros2 = wind_dir / 'GADEN_ros2.launch'
            one, two = launch_defaults(ros1), launch_defaults(ros2)
            if one != two:
                raise RuntimeError(f'ROS1/ROS2 source defaults disagree: {wind_dir}')
            x, y, z = (float(two[k]) for k in ARGS[:3])
            gas_root = ROOT / house / 'gas_simulations' / wind_dir.name
            gas_dirs = sorted(p for p in gas_root.iterdir() if p.is_dir())
            expected_name = (f'FilamentSimulation_gasType_{two["gas_type"]}'
                             f'_sourcePosition_{two["source_location_x"]}'
                             f'_{two["source_location_y"]}_{two["source_location_z"]}')
            if len(gas_dirs) != 1 or gas_dirs[0].name != expected_name:
                raise RuntimeError(f'gas simulation dir/default mismatch: {gas_root}')
            gas = gas_dirs[0]
            plume = list(gas.glob('iteration_*'))
            wind = list((gas / 'wind').glob('wind_iteration_*'))
            rows.append(dict(house=house, wind_config=wind_dir.name,
                             configured_source_x_m=x, configured_source_y_m=y,
                             configured_source_z_m=z, configured_gas_type=two['gas_type'],
                             ros1_launch=str(ros1), ros1_sha256=sha(ros1),
                             ros2_launch=str(ros2), ros2_sha256=sha(ros2),
                             gas_simulation_dir=str(gas),
                             existing_plume_iteration_files=len(plume),
                             existing_wind_iteration_files=len(wind),
                             source_coordinates_are_launch_args=True))
    if len(rows) != 12:
        raise RuntimeError(f'expected 12 House/wind configs, found {len(rows)}')
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--panel', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    rows = configured_rows()
    with args.panel.open(encoding='utf-8', newline='') as stream:
        panel = list(csv.DictReader(stream, delimiter='\t'))
    if len(panel) != 24:
        raise RuntimeError('frozen panel row count drift')
    by_house = defaultdict(set)
    for row in rows:
        by_house[row['house']].add((row['configured_source_x_m'],
                                  row['configured_source_y_m'],
                                  row['configured_source_z_m']))
    comparisons = []
    for source in panel:
        xyz = tuple(float(source[k]) for k in ('x_m', 'y_m', 'z_m'))
        comparisons.append(dict(house=source['house'], source_id=source['source_id'],
                                panel_role=source['panel_role'], x_m=xyz[0], y_m=xyz[1],
                                z_m=xyz[2], matches_original_configured_source=xyz in by_house[source['house']]))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, values in [('ORIGINAL_CONFIGURED_SOURCE_CATALOG.tsv', rows),
                         ('FROZEN_PANEL_VS_ORIGINAL_SOURCE_CATALOG.tsv', comparisons)]:
        with (args.output_dir / name).open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(values[0]), delimiter='\t', lineterminator='\n')
            writer.writeheader()
            writer.writerows(values)
    summary = dict(decision='E2C_R1_HOLD_SOURCE_LOCATION_CONTRACT',
                   configured_house_wind_combinations=len(rows),
                   unique_configured_sources_per_house={h: len(by_house[h]) for h in HOUSES},
                   frozen_panel_sources=len(comparisons),
                   frozen_panel_matches_original_configured=sum(x['matches_original_configured_source'] for x in comparisons),
                   original_source_catalog_expansion_found=False,
                   runtime_source_args_exist=True,
                   runtime_editability_is_not_dataset_catalog_membership=True,
                   no_concentration_files_opened=True,
                   panel_sha256=sha(args.panel))
    (args.output_dir / 'SOURCE_LOCATION_CONTRACT_AUDIT.json').write_text(
        json.dumps(summary, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(summary, sort_keys=True))


if __name__ == '__main__':
    main()
