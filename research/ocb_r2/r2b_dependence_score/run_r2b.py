#!/usr/bin/env python3
"""Execute the preregistered binary, exact-Q R2B score and nothing else."""
from __future__ import annotations

import hashlib
import itertools
import json
import math
from pathlib import Path
import shutil
import statistics
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'research/ocb_r2/mechanism_census_r0'))
import run_census as r0

OUT = ROOT / 'evidence/ocb_r2/r2b_dependence_score'
CODE = Path(__file__)
PROTOCOL = ROOT / 'research/ocb_r2/R2B_DEPENDENCE_SENSITIVE_SCORE_PROTOCOL_20260930.md'
FREEZE = CODE.with_name('R2B_PROTOCOL_FROZEN.md')
R2 = ROOT / 'evidence/ocb_r2/r2_broad_memory_path'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, obj):
    Path(path).write_bytes((json.dumps(obj, sort_keys=True, indent=2, allow_nan=False) + '\n').encode())


def mean(values):
    return float(statistics.mean(float(v) for v in values))


def med(values):
    return float(statistics.median(float(v) for v in values))


def spearman(x, y):
    from scipy.stats import spearmanr
    if len(set(x)) < 2 or len(set(y)) < 2:
        return None
    return float(spearmanr(x, y).statistic)


def signflip(values):
    values = np.asarray(values, dtype=float)
    obs = float(values.mean())
    outcomes = [float((values * np.asarray(signs)).mean())
                for signs in itertools.product((-1, 1), repeat=8)]
    return sum(v >= obs - 1e-15 for v in outcomes) / 256


def summarize(groups, field='mean_Delta_VS'):
    cs = sorted({g['context'] for g in groups})
    assert len(groups) == 16 and len(cs) == 8
    cv = {c: mean([g[field] for g in groups if g['context'] == c]) for c in cs}
    return dict(house_medians={h: med([g[field] for g in groups if g['house'] == h])
                              for h in ('House01', 'House02')},
                pooled_group_median=med([g[field] for g in groups]),
                positive_groups=sum(g[field] > 0 for g in groups),
                context_means=cv, positive_contexts=sum(v > 0 for v in cv.values()),
                leave_one_context_out={c: med([g[field] for g in groups if g['context'] != c]) for c in cs},
                exact_signflip=signflip(list(cv.values())))


def scores(ref, target):
    """All time/probe pairs receive equal weight; no fair correction is added."""
    assert ref.shape == (3, 10, 30) and ref.dtype == np.bool_
    assert target.shape == (10, 30) and target.dtype == np.bool_
    lag_terms = []
    for lag in range(1, 10):
        raw_sums, q_sums = [], []
        for t in range(10 - lag):
            a, b = ref[:, t, :], ref[:, t + lag, :]
            raw = (a[:, :, None] != b[:, None, :]).mean(axis=0)
            pa, pb = a.mean(axis=0), b.mean(axis=0)
            q = pa[:, None] + pb[None, :] - 2 * pa[:, None] * pb[None, :]
            # Independent exact empirical-product constructor: all K^2 pairs.
            q_cross = (a[:, None, :, None] != b[None, :, None, :]).mean(axis=(0, 1))
            assert np.allclose(q, q_cross, rtol=0, atol=3e-16)
            observed = target[t, :, None] != target[t + lag, None, :]
            raw_sums.append(float(np.square(observed.astype(float) - raw).sum()))
            q_sums.append(float(np.square(observed.astype(float) - q).sum()))
        n = (10 - lag) * 900
        vs_raw, vs_q = math.fsum(raw_sums) / n, math.fsum(q_sums) / n
        lag_terms.append(dict(lag=lag, pairs=n, VS_RAW=vs_raw, VS_Q=vs_q, D_VS=vs_q - vs_raw))
    def pooled(lags):
        sub = [r for r in lag_terms if r['lag'] in lags]
        n = sum(r['pairs'] for r in sub)
        raw = math.fsum(r['VS_RAW'] * r['pairs'] for r in sub) / n
        q = math.fsum(r['VS_Q'] * r['pairs'] for r in sub) / n
        return dict(VS_RAW=raw, VS_Q=q, D_VS=q - raw)
    return pooled((1, 2, 3)), pooled(range(1, 10)), lag_terms


def input_parity():
    runs, contexts = r0.metadata_preflight()
    tensors, hashes = r0.verify_inputs(runs, contexts)
    prior = json.loads((ROOT / 'evidence/ocb_r2/mechanism_census_r0/R0_INPUT_HASHES.json').read_text())
    assert hashes['pooled_tensor_sha256'] == prior['pooled_tensor_sha256']
    for name, digest in prior['input_file_sha256'].items():
        assert sha(ROOT / name) == digest, name
    repeat = json.loads((R2 / 'R2_DETERMINISTIC_REPEAT.json').read_text())
    assert repeat['byte_identical']
    comparator_path = R2 / 'R2_PATH_TARGETS.tsv'
    assert sha(comparator_path) == repeat['files_sha256']['R2_PATH_TARGETS.tsv']
    comparator = r0.rows(comparator_path)
    primary = [r for r in comparator if r['primary_omission'] == '1']
    assert len(primary) == 64 and sum(float(r['Delta_BM']) > 0 for r in primary) == 53
    parity = dict(decision='R2B_INPUT_PARITY_PASS', target_count=64, contexts=8, groups=16,
                  input_hashes=hashes, r0_hash_manifest_sha256=sha(ROOT / 'evidence/ocb_r2/mechanism_census_r0/R0_INPUT_HASHES.json'),
                  comparator_sha256=sha(comparator_path), comparator_positive_targets=53,
                  scorer_sha256=sha(CODE), protocol_sha256=sha(PROTOCOL), freeze_sha256=sha(FREEZE),
                  representation='binary concentration > 0', no_reextraction=True,
                  confirmation_and_house03_sealed=True)
    return runs, contexts, tensors, comparator, parity


def calculate(runs, contexts, tensors, comparator):
    banks = r0.references(runs, tensors, contexts)
    lookup = {(r['context'], r['source'], r['replica']): r for r in runs}
    baseline = {(r['run_id'], int(r['alternative_omitted_replicate'])): r for r in comparator}
    targets, candidates = [], []
    for c in contexts:
        sources = (c['source_a'], c['source_b'])
        for truth_idx, truth in enumerate(sources):
            for rep in range(1, 5):
                run = lookup[(c['context'], truth, rep)]
                y = banks[(c['context'], truth_idx)][rep - 1]
                computed = {}
                for candidate_idx, candidate in enumerate(sources):
                    omissions = (rep,) if candidate_idx == truth_idx else range(1, 5)
                    for omit in omissions:
                        ref = np.delete(banks[(c['context'], candidate_idx)], omit - 1, axis=0)
                        primary, full, lags = scores(ref, y)
                        computed[(candidate_idx, omit)] = (primary, full, lags)
                        for lag in lags:
                            candidates.append(dict(run_id=run['run_id'], context=c['context'], candidate_source=candidate,
                                candidate_role='TRUTH' if candidate_idx == truth_idx else 'ALTERNATIVE',
                                target_replicate=rep, omitted_replicate=omit, **lag))
                for omit in range(1, 5):
                    tr, tf, tl = computed[(truth_idx, rep)]
                    ar, af, al = computed[(1 - truth_idx, omit)]
                    old = baseline[(run['run_id'], omit)]
                    targets.append(dict(context=c['context'], house=c['house'], wind=c['wind'], gas=c['gas'],
                        run_id=run['run_id'], truth_source=truth, alternative_source=sources[1 - truth_idx],
                        target_replicate=rep, alternative_omitted_replicate=omit, primary_omission=int(omit == rep),
                        VS_RAW_truth=tr['VS_RAW'], VS_Q_truth=tr['VS_Q'], D_VS_truth=tr['D_VS'],
                        VS_RAW_alt=ar['VS_RAW'], VS_Q_alt=ar['VS_Q'], D_VS_alt=ar['D_VS'],
                        Delta_VS=tr['D_VS'] - ar['D_VS'], Delta_ES=float(old['Delta_BM']),
                        VS_correct=int(tr['D_VS'] > ar['D_VS']), ES_correct=int(float(old['Delta_BM']) > 0),
                        Delta_VS_lag1=tl[0]['D_VS'] - al[0]['D_VS'],
                        Delta_VS_lag2=tl[1]['D_VS'] - al[1]['D_VS'],
                        Delta_VS_lag3=tl[2]['D_VS'] - al[2]['D_VS'],
                        Delta_VS_full_lag1_9=tf['D_VS'] - af['D_VS'], G_M_FULL=float(old['G_M_FULL'])))
    assert len(targets) == 256 and len(candidates) == 64 * 5 * 9
    return targets, candidates


def group_rows(targets, contexts):
    groups = []
    for c in contexts:
        for source in (c['source_a'], c['source_b']):
            sub = [r for r in targets if r['context'] == c['context'] and r['truth_source'] == source]
            assert len(sub) == 4
            groups.append(dict(context=c['context'], house=c['house'], wind=c['wind'], gas=c['gas'], truth_source=source,
                targets=4, VS_correct=sum(r['VS_correct'] for r in sub), ES_correct=sum(r['ES_correct'] for r in sub),
                mean_Delta_VS=mean([r['Delta_VS'] for r in sub]), mean_Delta_ES=mean([r['Delta_ES'] for r in sub]),
                median_Delta_VS=med([r['Delta_VS'] for r in sub])))
    return groups


def aggregate(targets, contexts):
    primary = [r for r in targets if r['primary_omission'] == 1]
    groups = group_rows(primary, contexts)
    summary = summarize(groups)
    houses = {h: dict(VS_correct=sum(r['VS_correct'] for r in primary if r['house'] == h),
                     ES_correct=sum(r['ES_correct'] for r in primary if r['house'] == h), targets=32)
              for h in ('House01', 'House02')}
    rescues = sum(r['VS_correct'] and not r['ES_correct'] for r in primary)
    harms = sum(r['ES_correct'] and not r['VS_correct'] for r in primary)
    discordant = rescues + harms
    paired_p = sum(math.comb(discordant, k) for k in range(rescues, discordant + 1)) / 2 ** discordant if discordant else 1.0
    omissions = []
    for omit in range(1, 5):
        view = [r for r in targets if r['alternative_omitted_replicate'] == omit]
        st = summarize(group_rows(view, contexts))
        omissions.append(dict(alternative_omitted_replicate=omit, VS_correct=sum(r['VS_correct'] for r in view),
            House01_group_median=st['house_medians']['House01'], House02_group_median=st['house_medians']['House02'],
            pooled_group_median=st['pooled_group_median'], positive_groups=st['positive_groups'],
            positive_contexts=st['positive_contexts'], exact_signflip=st['exact_signflip']))
    conditions = dict(accuracy_ge_58=sum(r['VS_correct'] for r in primary) >= 58,
        House01_nonregression=houses['House01']['VS_correct'] >= houses['House01']['ES_correct'],
        House02_nonregression=houses['House02']['VS_correct'] >= houses['House02']['ES_correct'],
        positive_groups_ge_15=summary['positive_groups'] >= 15, all_contexts_positive=summary['positive_contexts'] == 8,
        all_looco_positive=all(v > 0 for v in summary['leave_one_context_out'].values()),
        exact_signflip_le_0p05=summary['exact_signflip'] <= .05,
        omission_positive=all(min(r['House01_group_median'], r['House02_group_median'], r['pooled_group_median']) > 0 for r in omissions),
        paired_improvement=rescues > harms and paired_p <= .05)
    stable = (min(summary['house_medians'].values()) > 0 and summary['positive_groups'] >= 12
              and summary['positive_contexts'] >= 6 and summary['exact_signflip'] <= .05)
    decision = ('OCB_R2_R2B_DEPENDENCE_SCORE_AMPLIFIES' if all(conditions.values()) else
                'OCB_R2_R2B_DEPENDENCE_SCORE_STABLE_NOT_AMPLIFIED' if stable else
                'OCB_R2_R2B_DEPENDENCE_SCORE_NO_GO')
    result = dict(decision_provisional_before_repeat=decision, conditions=conditions, stable=stable,
                  VS_correct=sum(r['VS_correct'] for r in primary), ES_correct=53, targets=64,
                  houses=houses, rescues=rescues, harms=harms, discordant_exact_binomial_p=paired_p,
                  summary=summary, confirmation_and_house03_sealed=True)
    contexts_out = []
    for c in contexts:
        sub = [r for r in primary if r['context'] == c['context']]
        contexts_out.append(dict(context=c['context'], house=c['house'], wind=c['wind'], gas=c['gas'], targets=8,
            VS_correct=sum(r['VS_correct'] for r in sub), ES_correct=sum(r['ES_correct'] for r in sub),
            mean_Delta_VS=mean([r['Delta_VS'] for r in sub]), mean_Delta_ES=mean([r['Delta_ES'] for r in sub])))
    paired = [dict(run_id=r['run_id'], house=r['house'], context=r['context'], truth_source=r['truth_source'],
        Delta_ES=r['Delta_ES'], Delta_VS=r['Delta_VS'], ES_correct=r['ES_correct'], VS_correct=r['VS_correct'],
        outcome='RESCUE' if r['VS_correct'] and not r['ES_correct'] else 'HARM' if r['ES_correct'] and not r['VS_correct'] else 'UNCHANGED') for r in primary]
    diag = dict(target_spearman_VS_ES=spearman([r['Delta_VS'] for r in primary], [r['Delta_ES'] for r in primary]),
                full_lag1_9_correct=sum(r['Delta_VS_full_lag1_9'] > 0 for r in primary),
                lag_correct={str(l): sum(r[f'Delta_VS_lag{l}'] > 0 for r in primary) for l in (1, 2, 3)})
    for category, key in (('house', 'house'), ('gas', 'gas'), ('source', 'truth_source')):
        diag[category] = {str(v): dict(targets=len(sub), VS_correct=sum(r['VS_correct'] for r in sub),
            ES_correct=sum(r['ES_correct'] for r in sub), mean_Delta_VS=mean([r['Delta_VS'] for r in sub]))
            for v in sorted({r[key] for r in primary}) if (sub := [r for r in primary if r[key] == v])}
    diag['speed'] = {v: dict(targets=len(sub), VS_correct=sum(r['VS_correct'] for r in sub),
        ES_correct=sum(r['ES_correct'] for r in sub), mean_Delta_VS=mean([r['Delta_VS'] for r in sub]))
        for v in ('fast', 'slow') if (sub := [r for r in primary if v in r['wind']])}
    bottom = sorted(primary, key=lambda r: (r['G_M_FULL'], r['run_id']))[:16]
    diag['M_FULL_bottom_quartile'] = dict(run_ids=[r['run_id'] for r in bottom],
        VS_correct=sum(r['VS_correct'] for r in bottom), ES_correct=sum(r['ES_correct'] for r in bottom),
        mean_Delta_VS=mean([r['Delta_VS'] for r in bottom]))
    return result, groups, contexts_out, omissions, paired, diag


def main():
    assert FREEZE.is_file()
    runs, contexts, tensors, comparator, parity = input_parity()
    OUT.mkdir(parents=True, exist_ok=True)
    files = ['R2B_INPUT_PARITY.json', 'R2B_TARGETS.tsv', 'R2B_CANDIDATES.tsv', 'R2B_GROUPS.tsv',
             'R2B_CONTEXTS.tsv', 'R2B_OMISSION.tsv', 'R2B_RESCUE_HARM.tsv', 'R2B_GATES.json', 'R2B_DIAGNOSTICS.json']
    for pass_idx in (1, 2):
        dest = OUT / f'pass{pass_idx}'
        dest.mkdir(exist_ok=True)
        targets, candidates = calculate(runs, contexts, tensors, comparator)
        result, groups, context_rows, omissions, paired, diagnostics = aggregate(targets, contexts)
        write_json(dest / 'R2B_INPUT_PARITY.json', parity)
        for name, records in [('R2B_TARGETS.tsv', targets), ('R2B_CANDIDATES.tsv', candidates),
                              ('R2B_GROUPS.tsv', groups), ('R2B_CONTEXTS.tsv', context_rows),
                              ('R2B_OMISSION.tsv', omissions), ('R2B_RESCUE_HARM.tsv', paired)]:
            r0.write_tsv(dest / name, records)
        write_json(dest / 'R2B_GATES.json', result)
        write_json(dest / 'R2B_DIAGNOSTICS.json', diagnostics)
    assert all((OUT / 'pass1' / name).read_bytes() == (OUT / 'pass2' / name).read_bytes() for name in files)
    for name in files:
        shutil.copyfile(OUT / 'pass1' / name, OUT / name)
    repeat = dict(byte_identical=True, scoring_passes=2, files_sha256={n: sha(OUT / n) for n in files})
    write_json(OUT / 'R2B_REPEAT.json', repeat)
    result['decision'] = result.pop('decision_provisional_before_repeat')
    result['conditions']['deterministic_repeat'] = True
    write_json(OUT / 'R2B_RESULT.json', result)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
