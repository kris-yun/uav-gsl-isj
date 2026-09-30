#!/usr/bin/env python3
"""Frozen common-window H1/H3 predictive-memory audit on 64 discovery tensors."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import statistics
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'research/ocb_r2/mechanism_census_r0'))
sys.path.insert(0, str(ROOT/'research/ocb_r2/r2_broad_memory_path'))
sys.path.insert(0, str(ROOT/'research/ocb_r2/mz_memory_probe_20260930'))
import run_census as r0  # noqa: E402
import run_r2 as r2  # noqa: E402
import run_mz_exploratory_probe as exploratory  # noqa: E402

R2 = ROOT/'evidence/ocb_r2/r2_broad_memory_path'
PROTOCOL = ROOT/'research/ocb_r2/R2A_MATCHED_WINDOW_MEMORY_AUDIT_20260930.md'
FREEZE = ROOT/'research/ocb_r2/r2a_matched_memory/R2A_PROTOCOL_FROZEN.md'
ANCHORS = tuple(range(2, 9))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mean(xs):
    return float(statistics.mean(float(x) for x in xs))


def med(xs):
    return float(statistics.median(float(x) for x in xs))


def preflight():
    assert PROTOCOL.is_file() and FREEZE.is_file()
    prior = r2.preflight()
    repeat = json.loads((R2/'R2_DETERMINISTIC_REPEAT.json').read_text())
    assert repeat['byte_identical'] and repeat['scoring_passes'] == 2
    for name, digest in repeat['files_sha256'].items():
        assert sha(R2/name) == sha(R2/'pass1'/name) == sha(R2/'pass2'/name) == digest, name
    assert repeat['decision_verified'] == 'OCB_R2_R2_MZ_PATH_FACTOR_DISCOVERY_ADVANCE'
    assert sha(R2/'R2_FORMULA_AUDIT.json')
    return dict(decision='OCB_R2_R2A_INPUT_PARITY_PASS', r2=prior,
                r2_repeat_sha256=sha(R2/'R2_DETERMINISTIC_REPEAT.json'),
                r2_gate_results_sha256=sha(R2/'R2_GATE_RESULTS.json'),
                protocol_sha256=sha(PROTOCOL), operational_freeze_sha256=sha(FREEZE),
                tensor_count=64, common_anchors=list(ANCHORS), future_slots=[t+1 for t in ANCHORS],
                confirmation_and_house03_sealed=True, no_new_extraction=True)


def anchor_gain(target, refs, h, t):
    assert target.shape == (10, 30) and refs.shape == (3, 10, 30)
    assert target.dtype == refs.dtype == np.bool_
    assert h in (1, 2, 3) and t in ANCHORS and t-h+1 >= 0
    distances = np.mean(refs[:, t-h+1:t+1, :] != target[None, t-h+1:t+1, :], axis=(1, 2))
    nearest = np.flatnonzero(np.isclose(distances, distances.min(), atol=1e-12, rtol=0))
    future_errors = np.mean(refs[:, t+1, :] != target[None, t+1, :], axis=1)
    intact_error = float(np.mean(future_errors[nearest]))
    shuffled_error = float(np.mean(future_errors))
    return dict(gain=shuffled_error-intact_error, intact_error=intact_error,
                shuffled_error=shuffled_error, nearest_count=len(nearest),
                minimum_history_distance=float(distances.min()))


def calculate():
    runs, contexts = r0.metadata_preflight()
    tensors, _ = r0.verify_inputs(runs, contexts)
    banks = r0.references(runs, tensors, contexts)
    lookup = {(r['context'], r['source'], r['replica']): r for r in runs}
    targets, anchors = [], []
    for c in contexts:
        for sidx, source in enumerate((c['source_a'], c['source_b'])):
            for ridx in range(1, 5):
                run = lookup[(c['context'], source, ridx)]
                target = banks[(c['context'], sidx)][ridx-1]
                refs = np.delete(banks[(c['context'], sidx)], ridx-1, axis=0)
                local = []
                for t in ANCHORS:
                    h1, h2, h3 = (anchor_gain(target, refs, h, t) for h in (1, 2, 3))
                    assert h1['shuffled_error'] == h2['shuffled_error'] == h3['shuffled_error']
                    row = dict(context=c['context'], house=c['house'], wind=c['wind'], gas=c['gas'],
                               run_id=run['run_id'], truth_source=source, target_replicate=ridx,
                               anchor_t=t, future_slot=t+1,
                               M_H1=h1['gain'], M_H2=h2['gain'], M_H3=h3['gain'],
                               D_H3_H1=h3['gain']-h1['gain'],
                               H1_nearest_count=h1['nearest_count'],
                               H2_nearest_count=h2['nearest_count'],
                               H3_nearest_count=h3['nearest_count'])
                    local.append(row)
                    anchors.append(row)
                assert len(local) == 7 and [r['anchor_t'] for r in local] == list(ANCHORS)
                m1, m2, m3 = (mean([r[f'M_H{h}'] for r in local]) for h in (1, 2, 3))
                targets.append(dict(context=c['context'], house=c['house'], wind=c['wind'], gas=c['gas'],
                                    run_id=run['run_id'], truth_source=source, target_replicate=ridx,
                                    anchors=7, M_H1_COMMON=m1, M_H2_COMMON=m2, M_H3_COMMON=m3,
                                    D_MZ_COMMON=m3-m1, D_H2_H1_COMMON=m2-m1,
                                    D_H3_H2_COMMON=m3-m2))
    assert len(targets) == 64 and len(anchors) == 64*7
    return targets, anchors, contexts


def aggregate(targets, anchors, contexts):
    groups = []
    for c in contexts:
        for source in (c['source_a'], c['source_b']):
            subset = [r for r in targets if r['context'] == c['context'] and r['truth_source'] == source]
            assert len(subset) == 4
            groups.append(dict(context=c['context'], house=c['house'], wind=c['wind'], gas=c['gas'],
                               truth_source=source, targets=4,
                               mean_D_MZ_COMMON=mean([r['D_MZ_COMMON'] for r in subset]),
                               median_D_MZ_COMMON=med([r['D_MZ_COMMON'] for r in subset]),
                               mean_M_H1_COMMON=mean([r['M_H1_COMMON'] for r in subset]),
                               mean_M_H2_COMMON=mean([r['M_H2_COMMON'] for r in subset]),
                               mean_M_H3_COMMON=mean([r['M_H3_COMMON'] for r in subset])))
    assert len(groups) == 16
    contexts_out = []
    for c in contexts:
        sub = [g for g in groups if g['context'] == c['context']]
        assert len(sub) == 2
        contexts_out.append(dict(context=c['context'], house=c['house'], wind=c['wind'], gas=c['gas'],
                                 source_groups=2,
                                 mean_D_MZ_COMMON=mean([g['mean_D_MZ_COMMON'] for g in sub]),
                                 median_D_MZ_COMMON=med([g['mean_D_MZ_COMMON'] for g in sub])))
    stats = r2.summarize_groups(groups, 'mean_D_MZ_COMMON')
    gate = r2.direction_gate(stats)
    if gate:
        decision = 'OCB_R2_R2A_MZ_MATCHED_WINDOW_PASS'
    elif stats['pooled_group_median'] <= 0 or any(v <= 0 for v in stats['house_medians'].values()):
        decision = 'OCB_R2_R2A_MZ_MATCHED_WINDOW_NO_SIGNAL'
    else:
        decision = 'OCB_R2_R2A_MZ_MATCHED_WINDOW_HOLD'
    per_anchor = []
    for t in ANCHORS:
        subset = [r for r in anchors if r['anchor_t'] == t]
        per_anchor.append(dict(anchor_t=t, future_slot=t+1, targets=64,
                               mean_D_MZ_COMMON=mean([r['D_H3_H1'] for r in subset]),
                               median_D_MZ_COMMON=med([r['D_H3_H1'] for r in subset]),
                               positive_targets=sum(r['D_H3_H1'] > 0 for r in subset),
                               House01_mean=mean([r['D_H3_H1'] for r in subset if r['house'] == 'House01']),
                               House02_mean=mean([r['D_H3_H1'] for r in subset if r['house'] == 'House02'])))
    descriptive = dict(House_H1_H2_H3_group_medians={h: {f'H{k}': med([g[f'mean_M_H{k}_COMMON'] for g in groups if g['house'] == h])
                                                       for k in (1, 2, 3)} for h in ('House01', 'House02')},
                       pooled_H1_H2_H3_group_medians={f'H{k}': med([g[f'mean_M_H{k}_COMMON'] for g in groups])
                                                       for k in (1, 2, 3)},
                       strata={})
    for kind, selector in (('speed', lambda g: 'fast' if 'fast' in g['wind'] else 'slow'),
                           ('gas', lambda g: str(g['gas']))):
        descriptive['strata'][kind] = {key: dict(groups=sum(selector(g) == key for g in groups),
                                                  mean_D_MZ_COMMON=mean([g['mean_D_MZ_COMMON'] for g in groups if selector(g) == key]),
                                                  median_D_MZ_COMMON=med([g['mean_D_MZ_COMMON'] for g in groups if selector(g) == key]),
                                                  positive_groups=sum(g['mean_D_MZ_COMMON'] > 0 for g in groups if selector(g) == key))
                                         for key in sorted({selector(g) for g in groups})}
    result = dict(decision=decision, gate_pass=gate, stats=stats, descriptive=descriptive,
                  anchors=list(ANCHORS), future_slots=[t+1 for t in ANCHORS],
                  no_new_data=True, confirmation_and_house03_sealed=True)
    return result, groups, contexts_out, per_anchor


def run(outdir):
    outdir = Path(outdir)
    assert not outdir.exists()
    parity = preflight()
    targets, anchors, contexts = calculate()
    result, groups, context_rows, per_anchor = aggregate(targets, anchors, contexts)
    outdir.mkdir(parents=True)
    r0.write_json(outdir/'R2A_INPUT_PARITY.json', parity)
    r0.write_tsv(outdir/'R2A_TARGETS.tsv', targets)
    r0.write_tsv(outdir/'R2A_GROUPS.tsv', groups)
    r0.write_tsv(outdir/'R2A_CONTEXTS.tsv', context_rows)
    r0.write_tsv(outdir/'R2A_ANCHOR_EFFECTS.tsv', anchors)
    r0.write_tsv(outdir/'R2A_ANCHOR_SUMMARY.tsv', per_anchor)
    r0.write_json(outdir/'R2A_GATE_RESULTS.json', result)
    print(json.dumps(dict(decision=result['decision'], gate_pass=result['gate_pass'],
                          house_medians=result['stats']['house_medians'],
                          positive_groups=result['stats']['positive_groups'],
                          positive_contexts=result['stats']['positive_contexts'],
                          exact_signflip=result['stats']['exact_signflip']), sort_keys=True))


def selftest():
    y = np.zeros((10, 30), dtype=bool)
    refs = np.zeros((3, 10, 30), dtype=bool)
    for t in ANCHORS:
        for h in (1, 2, 3):
            assert anchor_gain(y, refs, h, t)['gain'] == 0
    refs[0, 3, 0] = True
    gains = [anchor_gain(y, refs, h, 2) for h in (1, 2, 3)]
    assert all(g['shuffled_error'] == 1/90 for g in gains)
    assert exploratory.exact_context_signflip([1]*8)[1] == 1/256
    print('R2A_SYNTHETIC_SELFTEST_PASS')


if __name__ == '__main__':
    assert len(sys.argv) in (2, 3)
    if sys.argv[1] == 'selftest':
        selftest()
    elif sys.argv[1] == 'preflight' and len(sys.argv) == 3:
        r0.write_json(sys.argv[2], preflight())
        print('OCB_R2_R2A_INPUT_PARITY_PASS')
    elif sys.argv[1] == 'run' and len(sys.argv) == 3:
        run(sys.argv[2])
    else:
        raise SystemExit('Usage: run_r2a.py selftest | preflight OUT.json | run OUTDIR')
