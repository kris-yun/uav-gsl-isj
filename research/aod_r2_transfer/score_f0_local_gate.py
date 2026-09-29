#!/usr/bin/env python3
"""Frozen AOD-R2 F0 u-ABS/rawu-ABS neighborhood B2 comparison."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import statistics
import sys

import numpy as np


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO/'research/amplitude_operator_decoupling_v0'))
from amplitude_readout import AmplitudeTemplates, Arm, ObservationOperator, rectangular_weights, EPS  # noqa: E402

F0 = REPO/'evidence/ocb_r2/aod_r2_f0'
S2 = REPO/'evidence/ocb_r2/OCB_R2_S2_DISCOVERY_RUNLIST_32.tsv'
S2X = REPO/'evidence/ocb_r2/s2x/OCB_R2_S2X_RUNLIST_32.tsv'
PROBES = REPO/'research/marked_encounter_pmfs_d0/protocol/E1_HOUSE_PROBE_CONTRACTS.tsv'
ENVS = REPO/'evidence/marked_encounter_pmfs_d0/inputs/environment_manifest.json'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def rows(path):
    with Path(path).open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def tsv(path, records):
    assert records
    with Path(path).open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(records[0]), delimiter='\t', lineterminator='\n')
        w.writeheader()
        w.writerows(records)


def median(values):
    return float(statistics.median(values))


def mean(values):
    return float(statistics.mean(values))


def main(outdir):
    outdir = Path(outdir)
    assert not outdir.exists()
    freeze = json.loads((F0/'AOD_R2_F0_PRE_TARGET_FREEZE.json').read_text())
    assert freeze['decision'] == 'AOD_R2_F0_METADATA_FROZEN_NO_TARGET_READ'
    complete = json.loads((F0/'AOD_R2_F0_FORWARD_COMPLETE.json').read_text())
    assert complete['decision'] == 'AOD_R2_F0_LOCAL_PMFS_BANK_COMPLETE' and complete['rows'] == 3168
    extracted = json.loads((F0/'targets/AOD_R2_F0_TARGET_EXTRACTION.json').read_text())
    assert extracted['decision'] == 'AOD_R2_F0_TARGETS_EXTRACTED' and len(extracted['runs']) == 64
    for r in extracted['runs']:
        assert sha(F0/'targets'/f"{r['run_id']}.pooled.npy") == r['pooled_sha256']
        assert sha(F0/'targets'/f"{r['run_id']}.cube.npy") == r['cube_sha256']
    runmap = {r['run_id']: dict(context=f"X{int(r['config_index']):02d}", house=r['house'],
                                    truth=r['source_id'], seed=int(r['master_seed'])) for r in rows(S2)}
    runmap.update({r['run_id']: dict(context=f"X{int(r['parent_s2_config_index']):02d}", house=r['house'],
                                         truth=r['source_id'], seed=int(r['master_seed'])) for r in rows(S2X)})
    assert len(runmap) == 64
    neighborhoods = rows(F0/'AOD_R2_F0_SOURCE_NEIGHBORHOODS.tsv')
    by_truth = {}
    for r in neighborhoods:
        by_truth.setdefault((r['house'], r['truth_source']), []).append(r['candidate_id'])
    envs = {e['house']: e['metadata'] for e in json.loads(ENVS.read_text()) if e['house'] in {'House01', 'House02'}}
    probes = rows(PROBES)
    operators = {}
    for house in ('House01', 'House02'):
        this = sorted((p for p in probes if p['house'] == house), key=lambda p: int(p['probe_rank']))
        assert len(this) == 30 and [int(p['probe_rank']) for p in this] == list(range(1, 31))
        assert all(int(p['native_x1_exclusive'])-int(p['native_x0']) == 2 and
                   int(p['native_y1_exclusive'])-int(p['native_y0']) == 2 for p in this)
        centers = np.array([[float(p['center_x_m']), float(p['center_y_m'])] for p in this])
        sizes = np.full((30, 2), .2, dtype=np.float64)
        operators[house] = {'footprint': ObservationOperator('footprint',
                                                            rectangular_weights(envs[house], centers, sizes))}
    by_context = {c['context']: c for c in json.loads((F0/'AOD_R2_F0_D0A_COMPARABILITY.json').read_text())['contexts']}
    assert len(by_context) == 8
    templates = {}
    ids = {}
    for context, info in sorted(by_context.items()):
        bank = F0/f'{context}_NEIGHBORHOOD_BANK.npz'
        assert sha(bank) == complete['bank_sha256'][context]
        with np.load(bank, allow_pickle=False) as z:
            ids[context] = [str(x) for x in z['source_ids']]
            maps = {'u': z['u'], 'rawu': z['rawu']}
            assert maps['u'].shape == maps['rawu'].shape == (len(ids[context]),
                                                              int(envs[info['house']]['width'])*int(envs[info['house']]['height']))
            assert len(ids[context]) in (4, 5)
            templates[context] = {kind: AmplitudeTemplates.prepare(maps, operators[info['house']], arm)
                                  for kind, arm in [('u', Arm.U_FOOTPRINT),
                                                    ('rawu', Arm.RAWU_FOOTPRINT)]}
        assert set(ids[context]) == (set(by_truth[(info['house'], info['source_a'])]) |
                                     set(by_truth[(info['house'], info['source_b'])]))
    targets = []
    for run_id, r in sorted(runmap.items(), key=lambda pair: (pair[1]['context'], pair[1]['truth'], pair[1]['seed'])):
        context, house, truth = r['context'], r['house'], r['truth']
        info = by_context[context]
        assert house == info['house'] and truth in {info['source_a'], info['source_b']}
        alt = info['source_b'] if truth == info['source_a'] else info['source_a']
        truth_idx = [ids[context].index(x) for x in by_truth[(house, truth)]]
        alt_idx = [ids[context].index(x) for x in by_truth[(house, alt)]]
        assert set(truth_idx).isdisjoint(alt_idx)
        y = np.load(F0/'targets'/f'{run_id}.pooled.npy', allow_pickle=False)
        assert y.shape == (10, 30) and np.isfinite(y).all() and (y >= 0).all()
        norm = float(np.square(y).sum())
        arm_scores = {}
        for kind in ('u', 'rawu'):
            sse, gains = templates[context][kind].score(y)
            assert np.isfinite(sse).all() and np.isfinite(gains).all()
            arm_scores[kind] = dict(truth_sse=float(np.min(sse[truth_idx])),
                                    alt_sse=float(np.min(sse[alt_idx])))
            arm_scores[kind]['D'] = (arm_scores[kind]['alt_sse'] - arm_scores[kind]['truth_sse']) / max(norm, EPS) if norm > 0 else 0.0
        du, dr = arm_scores['u']['D'], arm_scores['rawu']['D']
        targets.append(dict(context=context, house=house, wind=info['wind'], gas=info['gas'],
                            run_id=run_id, truth_source=truth, alt_source=alt, seed=r['seed'],
                            observation_norm2=norm, zero_observation=int(norm == 0),
                            u_truth_sse=arm_scores['u']['truth_sse'], u_alt_sse=arm_scores['u']['alt_sse'],
                            rawu_truth_sse=arm_scores['rawu']['truth_sse'], rawu_alt_sse=arm_scores['rawu']['alt_sse'],
                            D_u=du, D_rawu=dr, delta_D=dr-du, u_win=int(du > 0), rawu_win=int(dr > 0),
                            rescue=int(du <= 0 and dr > 0), harm=int(du > 0 and dr <= 0)))
    assert len(targets) == 64
    groups = []
    for context, info in sorted(by_context.items()):
        for truth in (info['source_a'], info['source_b']):
            cases = [t for t in targets if t['context'] == context and t['truth_source'] == truth]
            assert len(cases) == 4
            groups.append(dict(context=context, house=info['house'], truth_source=truth,
                               mean_delta_D=mean([t['delta_D'] for t in cases]),
                               median_delta_D=median([t['delta_D'] for t in cases]),
                               positive_realizations=sum(t['delta_D'] > 0 for t in cases),
                               u_wins=sum(t['u_win'] for t in cases), rawu_wins=sum(t['rawu_win'] for t in cases),
                               rescues=sum(t['rescue'] for t in cases), harms=sum(t['harm'] for t in cases)))
    assert len(groups) == 16
    contexts = []
    for c, info in sorted(by_context.items()):
        gs = [g for g in groups if g['context'] == c]
        ts = [t for t in targets if t['context'] == c]
        contexts.append(dict(context=c, house=info['house'], wind=info['wind'], gas=info['gas'],
                             mean_group_delta_D=mean([g['mean_delta_D'] for g in gs]),
                             median_group_delta_D=median([g['mean_delta_D'] for g in gs]),
                             positive_groups=sum(g['mean_delta_D'] > 0 for g in gs),
                             rescues=sum(t['rescue'] for t in ts), harms=sum(t['harm'] for t in ts)))
    houses = []
    for house in ('House01', 'House02'):
        gs = [g for g in groups if g['house'] == house]
        ts = [t for t in targets if t['house'] == house]
        houses.append(dict(house=house, median_group_mean_delta_D=median([g['mean_delta_D'] for g in gs]),
                           positive_groups=sum(g['mean_delta_D'] > 0 for g in gs),
                           u_wins=sum(t['u_win'] for t in ts), rawu_wins=sum(t['rawu_win'] for t in ts),
                           rescues=sum(t['rescue'] for t in ts), harms=sum(t['harm'] for t in ts)))
    overall_median = median([g['mean_delta_D'] for g in groups])
    rescues = sum(t['rescue'] for t in targets)
    harms = sum(t['harm'] for t in targets)
    leave_one = {c: median([g['mean_delta_D'] for g in groups if g['context'] != c]) for c in sorted(by_context)}
    conditions = dict(overall_median_positive=overall_median > 0,
                      both_house_medians_positive=all(h['median_group_mean_delta_D'] > 0 for h in houses),
                      at_least_10_positive_groups=sum(g['mean_delta_D'] > 0 for g in groups) >= 10,
                      rescues_exceed_harms=rescues > harms,
                      all_leave_one_context_medians_positive=all(v > 0 for v in leave_one.values()))
    if all(conditions.values()):
        decision = 'AOD_R2_F0_LOCAL_SIGNAL_POSITIVE'
    elif overall_median <= 0 and rescues <= harms:
        decision = 'AOD_R2_F0_NO_SIGNAL'
    else:
        decision = 'AOD_R2_F0_HETEROGENEOUS_HOLD'
    result = dict(decision=decision, conditions=conditions, overall_median_group_mean_delta_D=overall_median,
                  positive_groups=sum(g['mean_delta_D'] > 0 for g in groups),
                  rescues=rescues, harms=harms, leave_one_context_out_median=leave_one,
                  contexts=contexts, houses=houses, groups=groups, target_count=64,
                  candidate_count_per_context={c: len(ids[c]) for c in sorted(ids)},
                  source='OCB_R2_S2_S2X_DISCOVERY_ONLY', no_new_gaden=True,
                  confirmation_and_house03_sealed=True, full_support_not_evaluated=True,
                  forward_completion_sha256=sha(F0/'AOD_R2_F0_FORWARD_COMPLETE.json'),
                  target_extraction_sha256=sha(F0/'targets/AOD_R2_F0_TARGET_EXTRACTION.json'),
                  scorer_sha256=sha(__file__))
    outdir.mkdir()
    tsv(outdir/'TARGET_RESULTS.tsv', targets)
    tsv(outdir/'GROUP_RESULTS.tsv', groups)
    tsv(outdir/'CONTEXT_RESULTS.tsv', contexts)
    tsv(outdir/'HOUSE_RESULTS.tsv', houses)
    (outdir/'AOD_R2_F0_RESULT.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps(dict(decision=decision, positive_groups=result['positive_groups'], rescues=rescues,
                          harms=harms, median=overall_median), sort_keys=True))


if __name__ == '__main__':
    assert len(sys.argv) == 2
    main(sys.argv[1])
