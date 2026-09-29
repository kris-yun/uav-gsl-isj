#!/usr/bin/env python3
"""Freeze OCB-R2 F0 comparability, time, truth neighborhoods, and PMFS row list.

Reads only runlists, provenance, QC, timelines, source geometry and model support.
It does not open native filament files, concentration arrays or PMFS map values.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
EVIDENCE = REPO / 'evidence/ocb_r2'
OUT = EVIDENCE / 'aod_r2_f0'
S2 = EVIDENCE / 'OCB_R2_S2_DISCOVERY_RUNLIST_32.tsv'
S2X = EVIDENCE / 's2x/OCB_R2_S2X_RUNLIST_32.tsv'
LEGAL = REPO / 'research/physical_cued_brg_v0/legal_training_banks/LEGAL_SUPPORT_COMPLETE.json'
ENVIRONMENTS = EVIDENCE.parent / 'marked_encounter_pmfs_d0/inputs/environment_manifest.json'
PROBES = REPO / 'research/marked_encounter_pmfs_d0/protocol/E1_HOUSE_PROBE_CONTRACTS.tsv'
STATIC = EVIDENCE / 'S1_STATIC_ASSET_AUDIT.json'
GENERATOR = 'ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688'
REQUESTED = tuple(range(50, 501, 50))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rows(path):
    with Path(path).open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def save_tsv(path, records, columns):
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=columns, delimiter='\t', lineterminator='\n')
        w.writeheader()
        w.writerows(records)


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def main():
    assert sha(S2) == 'f1d8604b49a74ba3ab698f445a2c1e381d84164c809e1bcf8b0f08beddf40974'
    assert sha(S2X) == 'f89dbd78e56f8d564947bc0af24ddd647a0c31994a86c670e2bf0d166917700c'
    s2, s2x = rows(S2), rows(S2X)
    assert len(s2) == len(s2x) == 32
    assert len({x['run_id'] for x in s2 + s2x}) == 64
    assert len({int(x['master_seed']) for x in s2 + s2x}) == 64
    probe_rows = rows(PROBES)
    for house in ('House01', 'House02'):
        this = [r for r in probe_rows if r['house'] == house]
        assert len(this) == 30 and sorted(int(r['probe_rank']) for r in this) == list(range(1, 31))
        assert all(float(r['z_m']) == .2 and int(r['native_cell_count']) == 4 for r in this)
    legal = json.loads(LEGAL.read_text(encoding='utf-8'))
    envs = json.loads(ENVIRONMENTS.read_text(encoding='utf-8'))
    static = json.loads(STATIC.read_text(encoding='utf-8'))
    legal_by_house = {'House01': legal['banks'][0], 'House02': legal['banks'][1]}
    meta_by_house = {'House01': envs[0]['metadata'], 'House02': envs[1]['metadata']}
    assert [(b['candidates']) for b in legal_by_house.values()] == [596, 630]
    source_xyz = {}
    for entry in static[:8]:
        key = (entry['house'], entry['source_id'])
        value = tuple(float(x) for x in entry['source_xyz'])
        assert key not in source_xyz or source_xyz[key] == value
        source_xyz[key] = value
    assert len(source_xyz) == 4

    allrows = []
    for phase, source, root in [('S2', s2, EVIDENCE / 's2_runs'),
                                ('S2X', s2x, EVIDENCE / 's2x/runs')]:
        for row in source:
            run_id = row['run_id']
            context = int(row['config_index'] if phase == 'S2' else row['parent_s2_config_index'])
            manifest_file = root / f'{run_id}.RUN_MANIFEST.json'
            qc_file = root / f'{run_id}.QC.json'
            timeline_file = root / f'{run_id}.RECORD_TIMELINE.tsv'
            manifest = json.loads(manifest_file.read_text(encoding='utf-8-sig'))
            qc = json.loads(qc_file.read_text(encoding='utf-8-sig'))
            assert manifest['generator_binary_sha256'] == qc['binary_sha256'] == GENERATOR
            assert manifest['master_seed'] == int(row['master_seed'])
            assert manifest['house'] == row['house'] and manifest['source_id'] == row['source_id']
            assert manifest['wind_id'] == row['wind_id']
            assert int(manifest['simulation_parameters']['gas_type']) == int(row['gas_type'])
            assert tuple(float(manifest['simulation_parameters'][f'source_position_{v}']) for v in 'xyz') == source_xyz[(row['house'], row['source_id'])]
            assert qc['record_count'] == 1803 and qc['first_time_s'] == 0 and qc['last_time_s'] == 999.502991
            assert sha(timeline_file) == qc['timeline_sha256']
            if phase == 'S2X':
                assert row['crossover_context'] == f'X{context:02d}'
                assert manifest['parent_s2_run_id'].startswith(f'ocb_r2_cfg{context:02d}_')
            asset = manifest['asset_checks']
            allrows.append(dict(run_id=run_id, phase=phase, context=context, house=row['house'],
                                source_id=row['source_id'], source_xyz=source_xyz[(row['house'], row['source_id'])],
                                seed=int(row['master_seed']), wind=row['wind_id'], gas=int(row['gas_type']),
                                key=(row['house'], row['wind_id'], int(row['gas_type']),
                                     asset['occupancy_sha256'], asset['wind_bundle_sha256'],
                                     qc['timeline_sha256'], qc['wind_index_sequence_sha256'], GENERATOR),
                                timeline=timeline_file, manifest_sha256=sha(manifest_file)))

    by_context = defaultdict(list)
    for record in allrows:
        by_context[record['context']].append(record)
    assert set(by_context) == set(range(8))
    summary = []
    for context, entries in sorted(by_context.items()):
        assert len(entries) == 8 and {e['phase'] for e in entries} == {'S2', 'S2X'}
        assert len({e['key'] for e in entries}) == 1
        ids = sorted({e['source_id'] for e in entries})
        assert len(ids) == 2
        assert all(sum(e['source_id'] == sid for e in entries) == 4 for sid in ids)
        summary.append(dict(context=f'X{context:02d}', house=entries[0]['house'],
                            wind=entries[0]['wind'], gas=entries[0]['gas'],
                            source_a=ids[0], source_b=ids[1], runs=8,
                            occupancy_sha256=entries[0]['key'][3], wind_bundle_sha256=entries[0]['key'][4],
                            timeline_sha256=entries[0]['key'][5]))

    mappings = []
    for entry in sorted(allrows, key=lambda x: (x['context'], x['source_id'], x['seed'])):
        timeline = rows(entry['timeline'])
        assert len(timeline) == 1803
        times = [float(r['internal_simulation_time_s']) for r in timeline]
        assert times[0] == 0 and times[-1] == 999.502991 and all(a < b for a, b in zip(times, times[1:]))
        for slot, requested in enumerate(REQUESTED, 1):
            selected = min(timeline, key=lambda r: (abs(float(r['internal_simulation_time_s']) - requested),
                                                    float(r['internal_simulation_time_s']), int(r['record_index'])))
            actual = float(selected['internal_simulation_time_s'])
            mappings.append(dict(run_id=entry['run_id'], slot=slot, requested_time_s=requested,
                                 record_index=int(selected['record_index']), actual_time_s=selected['internal_simulation_time_s'],
                                 abs_time_error_s=format(abs(actual-requested), '.9g'),
                                 wind_index=int(selected['wind_index'])))
    assert len(mappings) == 640

    neighborhoods = []
    for (house, sid), xyz in sorted(source_xyz.items()):
        support = legal_by_house[house]['source_ids']
        meta = meta_by_house[house]
        for full_index, cid in enumerate(support):
            _, i, j = cid.split('_')
            x = float(meta['origin_x']) + (int(i) + .5)*float(meta['resolution'])
            y = float(meta['origin_y']) + (int(j) + .5)*float(meta['resolution'])
            distance = math.hypot(x-xyz[0], y-xyz[1])
            if distance <= .30:
                neighborhoods.append(dict(house=house, truth_source=sid,
                                          truth_x_m=xyz[0], truth_y_m=xyz[1], truth_z_m=xyz[2],
                                          candidate_id=cid, full_legal_index=full_index,
                                          candidate_x_m=format(x, '.15g'), candidate_y_m=format(y, '.15g'),
                                          candidate_z_m=.2, distance_xy_m=format(distance, '.15g')))
    by_source = defaultdict(set)
    for n in neighborhoods:
        by_source[(n['house'], n['truth_source'])].add(n['candidate_id'])
    assert set(by_source) == set(source_xyz)
    for house in ('House01', 'House02'):
        pair = [by_source[k] for k in sorted(by_source) if k[0] == house]
        assert len(pair) == 2 and pair[0].isdisjoint(pair[1])

    forward = []
    for context, entries in sorted(by_context.items()):
        house = entries[0]['house']
        chosen = sorted((n for n in neighborhoods if n['house'] == house), key=lambda n: n['full_legal_index'])
        for n in chosen:
            for state in range(11):
                for key in range(1, 9):
                    forward.append(dict(context=f'X{context:02d}', house=house,
                                        wind=entries[0]['wind'], gas=entries[0]['gas'],
                                        source_id=n['candidate_id'], full_legal_index=n['full_legal_index'],
                                        source_x_m=n['candidate_x_m'], source_y_m=n['candidate_y_m'], source_z_m='.2',
                                        wind_state=state, pmfs_transport_key=key))

    OUT.mkdir(parents=True, exist_ok=True)
    save_json(OUT / 'AOD_R2_F0_D0A_COMPARABILITY.json',
              dict(decision='OCB_R2_D0A_SOURCE_COMPARABILITY_PASS', contexts=summary,
                   source='metadata_only', no_concentration_read=True, run_count=64))
    save_tsv(OUT / 'AOD_R2_F0_TIME_MAPPING.tsv', mappings, list(mappings[0]))
    save_tsv(OUT / 'AOD_R2_F0_SOURCE_NEIGHBORHOODS.tsv', neighborhoods, list(neighborhoods[0]))
    save_tsv(OUT / 'AOD_R2_F0_FORWARD_RUNLIST.tsv', forward, list(forward[0]))
    outputs = {p.name: sha(p) for p in sorted(OUT.iterdir()) if p.is_file()}
    inputs = {str(p.relative_to(REPO)): sha(p) for p in (S2, S2X, LEGAL, ENVIRONMENTS, PROBES, STATIC, Path(__file__),
                  REPO / 'research/aod_r2_transfer/AOD_R2_F0_PROTOCOL_20260929.md')}
    save_json(OUT / 'AOD_R2_F0_PRE_TARGET_FREEZE.json',
              dict(decision='AOD_R2_F0_METADATA_FROZEN_NO_TARGET_READ', input_sha256=inputs,
                   output_sha256=outputs, contexts=8, sources_per_context=2, realizations_per_source=4,
                   target_runs=64, time_mapping_rows=len(mappings), neighborhood_rows=len(neighborhoods),
                   selected_candidates_per_context={f'X{k:02d}': len([n for n in neighborhoods if n['house'] == v[0]['house']])
                                                    for k, v in sorted(by_context.items())},
                   pmfs_forward_rows=len(forward), new_gaden=0, target_values_read=False,
                   confirmation_and_house03_sealed=True))
    print(json.dumps(dict(decision='OCB_R2_D0A_SOURCE_COMPARABILITY_PASS',
                          forward_rows=len(forward), neighborhood_rows=len(neighborhoods),
                          time_rows=len(mappings)), sort_keys=True))


if __name__ == '__main__':
    main()
