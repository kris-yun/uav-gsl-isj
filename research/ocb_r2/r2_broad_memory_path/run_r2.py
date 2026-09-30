#!/usr/bin/env python3
"""Frozen OCB-R2 R2 discovery-only memory and candidate path-factor gates."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import statistics
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'research/ocb_r2/mechanism_census_r0'))
sys.path.insert(0, str(ROOT/'research/ocb_r2/cross_time_anatomy_r1'))
sys.path.insert(0, str(ROOT/'research/ocb_r2/mz_memory_probe_20260930'))
import run_census as r0  # noqa: E402
import run_r1 as r1  # noqa: E402
import run_mz_exploratory_probe as exploratory  # noqa: E402

R0 = ROOT/'evidence/ocb_r2/mechanism_census_r0'
R1 = ROOT/'evidence/ocb_r2/cross_time_anatomy_r1'
PROTOCOL = ROOT/'research/ocb_r2/mz_memory_probe_20260930/R2_BROAD_MEMORY_PATH_PROTOCOL.md'
FREEZE = ROOT/'research/ocb_r2/r2_broad_memory_path/R2_PROTOCOL_FROZEN.md'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def med(xs):
    return float(statistics.median(float(x) for x in xs))


def mean(xs):
    return float(statistics.mean(float(x) for x in xs))


def preflight():
    assert PROTOCOL.is_file() and FREEZE.is_file()
    prior = r1.parity()
    repeat = json.loads((R1/'R1_DETERMINISTIC_REPEAT.json').read_text())
    assert repeat['byte_identical'] and repeat['scoring_passes'] == 2
    for name, digest in repeat['files_sha256'].items():
        assert sha(R1/name) == sha(R1/'pass1'/name) == sha(R1/'pass2'/name) == digest, name
    assert sha(R1/'R1_CONTEXTS.tsv') == repeat['canonical_context_sha256']
    result = dict(decision='OCB_R2_R2_INPUT_PARITY_PASS', r0=prior,
                  r1_repeat_sha256=sha(R1/'R1_DETERMINISTIC_REPEAT.json'),
                  r1_aggregate_sha256=sha(R1/'R1_AGGREGATES.json'),
                  exploratory_code_sha256=sha(ROOT/'research/ocb_r2/mz_memory_probe_20260930/run_mz_exploratory_probe.py'),
                  protocol_sha256=sha(PROTOCOL), operational_freeze_sha256=sha(FREEZE),
                  target_count=64, source_context_groups=16, contexts=8,
                  no_new_extraction=True, confirmation_and_house03_sealed=True)
    return result


def spearman(x, y):
    assert len(x) == len(y)
    def ranks(values):
        order = sorted(range(len(values)), key=lambda i: (values[i], i))
        out = [0.0]*len(values)
        k = 0
        while k < len(order):
            end = k+1
            while end < len(order) and values[order[end]] == values[order[k]]:
                end += 1
            rank = (k+1+end)/2
            for pos in range(k, end):
                out[order[pos]] = rank
            k = end
        return np.asarray(out, dtype=float)
    a, b = ranks(x), ranks(y)
    if np.std(a) == 0 or np.std(b) == 0:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def summarize_groups(groups, field):
    assert len(groups) == 16
    contexts = sorted({g['context'] for g in groups})
    assert len(contexts) == 8
    hmed = {h: med([g[field] for g in groups if g['house'] == h]) for h in ('House01', 'House02')}
    cmean = {c: mean([g[field] for g in groups if g['context'] == c]) for c in contexts}
    pooled = med([g[field] for g in groups])
    loo = {c: med([g[field] for g in groups if g['context'] != c]) for c in contexts}
    observed, p = exploratory.exact_context_signflip([cmean[c] for c in contexts])
    denom = sum(abs(v) for v in cmean.values())
    return dict(house_medians=hmed, pooled_group_median=pooled,
                positive_groups=sum(g[field] > 0 for g in groups),
                context_means=cmean, positive_contexts=sum(v > 0 for v in cmean.values()),
                leave_one_context_out=loo, context_mean=observed, exact_signflip=p,
                context_abs_contributions={c: abs(cmean[c])/denom for c in contexts} if denom > 0 else None,
                max_context_abs_contribution=max(abs(v)/denom for v in cmean.values()) if denom > 0 else None)


def direction_gate(s):
    return (all(v > 0 for v in s['house_medians'].values()) and
            s['positive_groups'] >= 12 and s['positive_contexts'] >= 6 and
            all(v > 0 for v in s['leave_one_context_out'].values()) and
            s['exact_signflip'] <= 0.05)


def calculate():
    runs, contexts = r0.metadata_preflight()
    tensors, _ = r0.verify_inputs(runs, contexts)
    banks = r0.references(runs, tensors, contexts)
    lookup = {(r['context'], r['source'], r['replica']): r for r in runs}
    baseline = {r['run_id']: r for r in r0.rows(R0/'R0_TARGET_EFFECTS.tsv') if r['primary_omission'] == '1'}
    assert len(baseline) == 64
    mz_targets, candidate_terms, path_targets = [], [], []
    audit = dict(lag_surrogate_views=0, lag_pair_preservation_assertions=0)
    for cidx, c in enumerate(contexts):
        source_ids = (c['source_a'], c['source_b'])
        for sidx, truth in enumerate(source_ids):
            alt_idx = 1-sidx
            for ridx in range(1, 5):
                run = lookup[(c['context'], truth, ridx)]
                y = banks[(c['context'], sidx)][ridx-1]
                truth_ref = np.delete(banks[(c['context'], sidx)], ridx-1, axis=0)
                hgain = {h: exploratory.predictive_gain(y, truth_ref, h) for h in (1, 3, 5)}
                mz_targets.append(dict(context=c['context'], house=c['house'], wind=c['wind'], gas=c['gas'],
                                       run_id=run['run_id'], truth_source=truth, target_replicate=ridx,
                                       M_truth_H1=hgain[1], M_truth_H3=hgain[3], M_truth_H5=hgain[5],
                                       D_MZ=hgain[3]-hgain[1], D_H5_H1=hgain[5]-hgain[1]))
                candidate_ebm = {}
                for cand_idx, candidate in enumerate(source_ids):
                    omissions = (ridx,) if cand_idx == sidx else range(1, 5)
                    for omitted in omissions:
                        ref = np.delete(banks[(c['context'], cand_idx)], omitted-1, axis=0)
                        terms = []
                        for lag in (1, 2, 3):
                            intact, shuffled = r1.lag_scores(ref, y, lag, cidx, cand_idx, ridx, omitted, audit)
                            q_median = med(shuffled)
                            term = q_median-intact
                            terms.append(term)
                            candidate_terms.append(dict(context=c['context'], house=c['house'], wind=c['wind'],
                                                        gas=c['gas'], run_id=run['run_id'],
                                                        truth_source=truth, candidate_source=candidate,
                                                        candidate_role='TRUTH' if cand_idx == sidx else 'ALTERNATIVE',
                                                        target_replicate=ridx, omitted_replicate=omitted,
                                                        lag=lag, ES_RAW=intact, ES_Q_median=q_median,
                                                        E_s_L=term))
                        candidate_ebm[(cand_idx, omitted)] = mean(terms)
                for omitted in range(1, 5):
                    et = candidate_ebm[(sidx, ridx)]
                    ea = candidate_ebm[(alt_idx, omitted)]
                    path_targets.append(dict(context=c['context'], house=c['house'], wind=c['wind'], gas=c['gas'],
                                             run_id=run['run_id'], truth_source=truth,
                                             alternative_source=source_ids[alt_idx], target_replicate=ridx,
                                             alternative_omitted_replicate=omitted,
                                             primary_omission=int(omitted == ridx),
                                             E_BM_truth=et, E_BM_alt=ea, Delta_BM=et-ea,
                                             G_M_FULL=float(baseline[run['run_id']]['G_M_FULL'])))
    assert len(mz_targets) == 64 and len(candidate_terms) == 64*5*3 and len(path_targets) == 64*4
    assert audit['lag_surrogate_views'] == 64*5*3*1000
    assert audit['lag_pair_preservation_assertions'] == 64*5*1000*(9+8+7)
    return mz_targets, candidate_terms, path_targets, contexts, audit


def aggregate(mz_targets, path_targets, contexts):
    mz_by_run = {r['run_id']: r for r in mz_targets}
    primary = [r for r in path_targets if r['primary_omission'] == 1]
    assert len(primary) == 64
    groups = []
    for c in contexts:
        for source in (c['source_a'], c['source_b']):
            sub = [r for r in primary if r['context'] == c['context'] and r['truth_source'] == source]
            assert len(sub) == 4
            mz = [mz_by_run[r['run_id']] for r in sub]
            groups.append(dict(context=c['context'], house=c['house'], wind=c['wind'], gas=c['gas'],
                               truth_source=source, targets=4,
                               mean_D_MZ=mean([r['D_MZ'] for r in mz]),
                               median_D_MZ=med([r['D_MZ'] for r in mz]),
                               mean_D_H5_H1=mean([r['D_H5_H1'] for r in mz]),
                               mean_Delta_BM=mean([r['Delta_BM'] for r in sub]),
                               median_Delta_BM=med([r['Delta_BM'] for r in sub]),
                               mean_G_M_FULL=mean([r['G_M_FULL'] for r in sub])))
    assert len(groups) == 16
    a = summarize_groups(groups, 'mean_D_MZ')
    b = summarize_groups(groups, 'mean_Delta_BM')
    gate_a = direction_gate(a)
    omissions = []
    omission_stats = {}
    for omitted in range(1, 5):
        view = [r for r in path_targets if r['alternative_omitted_replicate'] == omitted]
        assert len(view) == 64
        ogroups = []
        for c in contexts:
            for source in (c['source_a'], c['source_b']):
                sub = [r for r in view if r['context'] == c['context'] and r['truth_source'] == source]
                assert len(sub) == 4
                ogroups.append(dict(context=c['context'], house=c['house'],
                                    mean_Delta_BM=mean([r['Delta_BM'] for r in sub])))
        s = summarize_groups(ogroups, 'mean_Delta_BM')
        omission_stats[str(omitted)] = s
        omissions.append(dict(alternative_omitted_replicate=omitted,
                              House01_group_median=s['house_medians']['House01'],
                              House02_group_median=s['house_medians']['House02'],
                              pooled_group_median=s['pooled_group_median'],
                              positive_groups=s['positive_groups'], positive_contexts=s['positive_contexts'],
                              exact_signflip=s['exact_signflip']))
    omission_pass = all(all(v > 0 for v in s['house_medians'].values()) and
                        s['pooled_group_median'] > 0 for s in omission_stats.values())
    contribution_pass = b['max_context_abs_contribution'] is not None and b['max_context_abs_contribution'] <= 0.40
    gate_b = direction_gate(b) and omission_pass and contribution_pass
    context_rows = []
    for c in contexts:
        sub = [g for g in groups if g['context'] == c['context']]
        context_rows.append(dict(context=c['context'], house=c['house'], wind=c['wind'], gas=c['gas'],
                                 source_groups=2, mean_D_MZ=mean([g['mean_D_MZ'] for g in sub]),
                                 median_D_MZ=med([g['mean_D_MZ'] for g in sub]),
                                 mean_Delta_BM=mean([g['mean_Delta_BM'] for g in sub]),
                                 median_Delta_BM=med([g['mean_Delta_BM'] for g in sub]),
                                 abs_contribution_to_GateB=b['context_abs_contributions'][c['context']]
                                 if b['context_abs_contributions'] else ''))
    if gate_a and gate_b:
        label = 'OCB_R2_R2_MZ_PATH_FACTOR_DISCOVERY_ADVANCE'
    elif gate_b:
        label = 'OCB_R2_R2_PATH_FACTOR_ONLY_HOLD_MZ'
    elif gate_a:
        label = 'OCB_R2_R2_MZ_PHYSICS_ONLY_HOLD_INFERENCE'
    else:
        label = 'OCB_R2_R2_NO_GO'
    result = dict(decision=label, gate_a_pass=gate_a, gate_b_pass=gate_b,
                  gate_a=a, gate_b=b, gate_b_omission_pass=omission_pass,
                  gate_b_context_contribution_pass=contribution_pass,
                  omission_stats=omission_stats, no_new_data=True,
                  confirmation_and_house03_sealed=True)
    return result, groups, context_rows, omissions, primary


def complementarity(groups, primary):
    ordered = sorted(primary, key=lambda r: (r['G_M_FULL'], r['run_id']))
    bottom = ordered[:16]
    by_margin = sorted(groups, key=lambda g: (g['mean_G_M_FULL'], g['context'], g['truth_source']))
    out = dict(group_spearman_DeltaBM_vs_MFULL=spearman([g['mean_Delta_BM'] for g in groups],
                                                      [g['mean_G_M_FULL'] for g in groups]),
               bottom_quartile_MFULL=dict(n=16, run_ids=[r['run_id'] for r in bottom],
                                          mean_Delta_BM=mean([r['Delta_BM'] for r in bottom]),
                                          median_Delta_BM=med([r['Delta_BM'] for r in bottom]),
                                          positive_targets=sum(r['Delta_BM'] > 0 for r in bottom)),
               lower_group_half=dict(mean_Delta_BM=mean([g['mean_Delta_BM'] for g in by_margin[:8]]),
                                     positive_groups=sum(g['mean_Delta_BM'] > 0 for g in by_margin[:8])),
               upper_group_half=dict(mean_Delta_BM=mean([g['mean_Delta_BM'] for g in by_margin[8:]]),
                                     positive_groups=sum(g['mean_Delta_BM'] > 0 for g in by_margin[8:])))
    for kind, selector in (('house', lambda g: g['house']), ('speed', lambda g: 'fast' if 'fast' in g['wind'] else 'slow'),
                           ('gas', lambda g: str(g['gas'])), ('source', lambda g: g['truth_source'])):
        keys = sorted({selector(g) for g in groups})
        out[kind] = {key: dict(groups=sum(selector(g) == key for g in groups),
                              mean_Delta_BM=mean([g['mean_Delta_BM'] for g in groups if selector(g) == key]),
                              median_Delta_BM=med([g['mean_Delta_BM'] for g in groups if selector(g) == key]),
                              positive_groups=sum(g['mean_Delta_BM'] > 0 for g in groups if selector(g) == key))
                     for key in keys}
    return out


def run(outdir):
    outdir = Path(outdir)
    assert not outdir.exists()
    parity = preflight()
    mz, terms, paths, contexts, audit = calculate()
    result, groups, context_rows, omissions, primary = aggregate(mz, paths, contexts)
    comp = complementarity(groups, primary)
    outdir.mkdir(parents=True)
    r0.write_json(outdir/'R2_INPUT_PARITY.json', parity)
    r0.write_tsv(outdir/'R2_MZ_TARGETS.tsv', mz)
    r0.write_tsv(outdir/'R2_PATH_CANDIDATE_TERMS.tsv', terms)
    r0.write_tsv(outdir/'R2_PATH_TARGETS.tsv', paths)
    r0.write_tsv(outdir/'R2_GROUPS.tsv', groups)
    r0.write_tsv(outdir/'R2_CONTEXTS.tsv', context_rows)
    r0.write_tsv(outdir/'R2_OMISSION_ROBUSTNESS.tsv', omissions)
    r0.write_json(outdir/'R2_COMPLEMENTARITY.json', comp)
    r0.write_json(outdir/'R2_GATE_RESULTS.json', result)
    r0.write_json(outdir/'R2_QTIME_PRESERVATION_AUDIT.json', audit)
    print(json.dumps(dict(decision=result['decision'], gate_a_pass=result['gate_a_pass'],
                          gate_b_pass=result['gate_b_pass'],
                          gate_a_exact_signflip=result['gate_a']['exact_signflip'],
                          gate_b_exact_signflip=result['gate_b']['exact_signflip']), sort_keys=True))


def selftest():
    assert abs(spearman([1, 2, 3], [3, 2, 1])+1) < 1e-12
    assert abs(spearman([1, 2, 3], [1, 2, 3])-1) < 1e-12
    assert exploratory.predictive_gain(np.zeros((10, 30), dtype=bool),
                                       np.zeros((3, 10, 30), dtype=bool), 3) == 0
    assert exploratory.exact_context_signflip([1]*8)[1] == 1/256
    print('R2_SYNTHETIC_SELFTEST_PASS')


if __name__ == '__main__':
    assert len(sys.argv) in (2, 3)
    if sys.argv[1] == 'selftest':
        selftest()
    elif sys.argv[1] == 'preflight' and len(sys.argv) == 3:
        r0.write_json(sys.argv[2], preflight())
        print('OCB_R2_R2_INPUT_PARITY_PASS')
    elif sys.argv[1] == 'run' and len(sys.argv) == 3:
        run(sys.argv[2])
    else:
        raise SystemExit('Usage: run_r2.py selftest | preflight OUT.json | run OUTDIR')
