#!/usr/bin/env python3
"""Frozen discovery-only OCB-R2 R1 cross-time memory anatomy."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import statistics
import sys

import numpy as np


REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO/'research/ocb_r2/mechanism_census_r0'))
import run_census as r0  # noqa: E402

E = REPO/'evidence/ocb_r2/cross_time_anatomy_r1'
R0 = REPO/'evidence/ocb_r2/mechanism_census_r0'
PROTOCOL = REPO/'research/ocb_r2/OCB_R2_CROSS_TIME_MEMORY_ANATOMY_R1.md'
FROZEN = REPO/'research/ocb_r2/cross_time_anatomy_r1/R1_PROTOCOL_FROZEN.md'
N = 1000


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def med(values):
    return float(statistics.median(float(v) for v in values))


def avg(values):
    return float(statistics.mean(float(v) for v in values))


def parity():
    assert PROTOCOL.is_file() and FROZEN.is_file()
    freeze = json.loads((R0/'R0_INPUT_HASHES.json').read_text())
    files = freeze['input_file_sha256']
    tensors = freeze['pooled_tensor_sha256']
    assert len(files) == 9 and len(tensors) == 64
    for name, digest in files.items():
        assert sha(REPO/name) == digest, name
    for run_id, digest in tensors.items():
        assert sha(R0/'inputs'/f'{run_id}.pooled.npy') == digest, run_id
    repeat = json.loads((R0/'R0_DETERMINISTIC_REPEAT.json').read_text())
    assert repeat['byte_identical'] and repeat['scoring_passes'] == 2
    for name, digest in repeat['files_sha256'].items():
        assert sha(R0/name) == digest
        assert sha(R0/'pass1'/name) == sha(R0/'pass2'/name) == digest
    summary = json.loads((R0/'R0_MECHANISM_SUMMARY.json').read_text())
    assert summary['decision'] == 'OCB_R2_MECH_CROSS_TIME_STABLE'
    runs, contexts = r0.metadata_preflight()
    assert len(runs) == 64 and len(contexts) == 8
    return dict(decision='OCB_R2_R1_INPUT_PARITY_PASS', r0_commit='c7b52bb969f8d48ffdbf87016574c00f1dd0cdae',
                protocol_source_commit='a715dd2f198a0f55e2cef78c3b017ef97319a733',
                file_hashes=files, tensor_hashes=tensors, r0_repeat_hashes=repeat['files_sha256'],
                r0_summary_sha256=sha(R0/'R0_MECHANISM_SUMMARY.json'),
                r1_protocol_sha256=sha(PROTOCOL), operational_freeze_sha256=sha(FROZEN),
                contexts=8, target_tensors=64, concentration_reextracted=False,
                confirmation_and_house03_sealed=True)


def fair_batch(ensembles, target):
    """Fair-U Energy Score; arbitrary dimensional binary pair/path ensembles."""
    assert ensembles.ndim == 3 and ensembles.shape[1] == 3
    assert target.shape == (ensembles.shape[2],)
    fit = np.sqrt(np.count_nonzero(ensembles != target[None, None, :], axis=2)).mean(axis=1)
    diversity = (np.sqrt(np.count_nonzero(ensembles[:, 0] != ensembles[:, 1], axis=1))+
                 np.sqrt(np.count_nonzero(ensembles[:, 0] != ensembles[:, 2], axis=1))+
                 np.sqrt(np.count_nonzero(ensembles[:, 1] != ensembles[:, 2], axis=1)))/6.0
    return fit-diversity


def lag_scores(ref, target, lag, cidx, sidx, ridx, omit, audit):
    """Average intact and second-snapshot-shuffled 60D scores over valid pairs."""
    assert ref.shape == (3, 10, 30) and target.shape == (10, 30)
    pairs = 10-lag
    rng = np.random.default_rng(np.random.SeedSequence([2026093100+lag, cidx, sidx, ridx, omit]))
    perm = np.argsort(rng.random((N, pairs, 3)), axis=-1, kind='stable')
    assert np.array_equal(np.sort(perm, axis=2), np.broadcast_to(np.arange(3), (N, pairs, 3)))
    shuffled = np.zeros(N, dtype=np.float64)
    intact = 0.0
    weights = 1 << np.arange(30, dtype=np.int64)
    for t in range(pairs):
        pair_target = np.concatenate((target[t], target[t+lag]))
        pair_ref = np.concatenate((ref[:, t], ref[:, t+lag]), axis=1)
        intact += float(fair_batch(pair_ref[None, :, :], pair_target)[0])/pairs
        second = ref[:, t+lag][perm[:, t]]
        first = np.broadcast_to(ref[:, t], second.shape)
        first_codes = (first.astype(np.int64)*weights).sum(axis=2)
        second_codes = (second.astype(np.int64)*weights).sum(axis=2)
        assert np.array_equal(first_codes, np.broadcast_to((ref[:, t].astype(np.int64)*weights).sum(axis=1),
                                                             (N, 3)))
        assert np.array_equal(np.sort(second_codes, axis=1),
                              np.broadcast_to(np.sort((ref[:, t+lag].astype(np.int64)*weights).sum(axis=1)),
                                              (N, 3)))
        surrogate = np.concatenate((first, second), axis=2)
        assert surrogate.shape == (N, 3, 60) and surrogate.dtype == np.bool_
        shuffled += fair_batch(surrogate, pair_target)/pairs
    audit['lag_surrogate_views'] += N
    audit['lag_pair_preservation_assertions'] += N*pairs
    return intact, shuffled


def block_scores(ref, target, length, cidx, sidx, ridx, omit, audit):
    """Permute complete contiguous blocks, preserving all within-block paths."""
    assert length in (2, 5) and ref.shape == (3, 10, 30)
    seed = 2026093120 if length == 2 else 2026093150
    nblocks = 10//length
    rng = np.random.default_rng(np.random.SeedSequence([seed, cidx, sidx, ridx, omit]))
    perm = np.argsort(rng.random((N, nblocks, 3)), axis=-1, kind='stable')
    assert np.array_equal(np.sort(perm, axis=2), np.broadcast_to(np.arange(3), (N, nblocks, 3)))
    bank = np.empty((N, 3, 10, 30), dtype=bool)
    for b in range(nblocks):
        lo, hi = b*length, (b+1)*length
        segment = ref[:, lo:hi, :]
        bank[:, :, lo:hi, :] = segment[perm[:, b, :]]
        assert np.array_equal(bank[:, :, lo:hi, :].sum(axis=1),
                              np.broadcast_to(segment.sum(axis=0), (N, length, 30)))
    assert bank.dtype == np.bool_ and bank.shape == (N, 3, 10, 30)
    assert np.array_equal(bank.sum(axis=1), np.broadcast_to(ref.sum(axis=0), (N, 10, 30)))
    audit[f'block_{length}_surrogate_views'] += N
    audit[f'block_{length}_block_preservation_assertions'] += N*nblocks
    return fair_batch(bank.reshape(N, 3, 300), target.reshape(300))


def score_all(runs, contexts, banks):
    lookup = {(r['context'], r['source'], r['replica']): r for r in runs}
    r0_targets = {r['run_id']: r for r in r0.rows(R0/'R0_TARGET_EFFECTS.tsv')}
    assert len(r0_targets) == 64
    lag_primary, block_primary, lag_all, block_all = [], [], [], []
    audit = dict(lag_surrogate_views=0, lag_pair_preservation_assertions=0,
                 block_2_surrogate_views=0, block_2_block_preservation_assertions=0,
                 block_5_surrogate_views=0, block_5_block_preservation_assertions=0,
                 r0_c2_views=0, r0_c2_snapshot_multiset_assertions=0,
                 max_r0_primary_G_B1_abs_diff=0.0, max_r0_primary_G_B10_abs_diff=0.0)
    old_audit = {mode: dict(banks=0, binary=0, marginals=0, snapshot_multiset=0)
                 for mode in ('C1', 'C2')}
    for cidx, c in enumerate(contexts):
        context = c['context']
        sources = (c['source_a'], c['source_b'])
        for sidx, source in enumerate(sources):
            aidx = 1-sidx
            alt_source = sources[aidx]
            for ridx in range(1, 5):
                run = lookup[(context, source, ridx)]
                target = banks[(context, sidx)][ridx-1]
                truth_ref = np.delete(banks[(context, sidx)], ridx-1, axis=0)
                truth_lag = {lag: lag_scores(truth_ref, target, lag, cidx, sidx, ridx, ridx, audit)
                             for lag in range(1, 10)}
                truth_b2 = block_scores(truth_ref, target, 2, cidx, sidx, ridx, ridx, audit)
                truth_b5 = block_scores(truth_ref, target, 5, cidx, sidx, ridx, ridx, audit)
                truth_b1 = r0.surrogate_scores(truth_ref, target, 'C2', cidx, sidx, ridx, ridx, old_audit)
                truth_b10 = float(fair_batch(truth_ref.reshape(1, 3, 300), target.reshape(300))[0])
                for omit in range(1, 5):
                    alt_ref = np.delete(banks[(context, aidx)], omit-1, axis=0)
                    alt_lag = {lag: lag_scores(alt_ref, target, lag, cidx, aidx, ridx, omit, audit)
                               for lag in range(1, 10)}
                    alt_b2 = block_scores(alt_ref, target, 2, cidx, aidx, ridx, omit, audit)
                    alt_b5 = block_scores(alt_ref, target, 5, cidx, aidx, ridx, omit, audit)
                    alt_b1 = r0.surrogate_scores(alt_ref, target, 'C2', cidx, aidx, ridx, omit, old_audit)
                    alt_b10 = float(fair_batch(alt_ref.reshape(1, 3, 300), target.reshape(300))[0])
                    g_b1 = med(alt_b1-truth_b1)
                    g_b2 = med(alt_b2-truth_b2)
                    g_b5 = med(alt_b5-truth_b5)
                    g_b10 = alt_b10-truth_b10
                    denominator = g_b10-g_b1
                    block = dict(context=context, house=c['house'], wind=c['wind'], gas=c['gas'],
                                 run_id=run['run_id'], truth_source=source, alternative_source=alt_source,
                                 target_replicate=ridx, alternative_omitted_replicate=omit,
                                 primary_omission=int(omit == ridx), G_B1=g_b1, G_B2=g_b2,
                                 G_B5=g_b5, G_B10=g_b10, I_R0_CROSS=denominator,
                                 R_B2=(g_b2-g_b1)/denominator if denominator > 0 else '',
                                 R_B5=(g_b5-g_b1)/denominator if denominator > 0 else '')
                    block_all.append(block)
                    if omit == ridx:
                        expected = r0_targets[run['run_id']]
                        d1 = abs(g_b1-float(expected['G_C2']))
                        d10 = abs(g_b10-float(expected['G_RAW']))
                        audit['max_r0_primary_G_B1_abs_diff'] = max(audit['max_r0_primary_G_B1_abs_diff'], d1)
                        audit['max_r0_primary_G_B10_abs_diff'] = max(audit['max_r0_primary_G_B10_abs_diff'], d10)
                        assert d1 < 1e-12 and d10 < 1e-12, (run['run_id'], d1, d10)
                        block_primary.append(block)
                    for lag in range(1, 10):
                        traw, tshuffle = truth_lag[lag]
                        araw, ashuffle = alt_lag[lag]
                        graw = araw-traw
                        gshuffle = med(ashuffle-tshuffle)
                        lagrow = dict(context=context, house=c['house'], wind=c['wind'], gas=c['gas'],
                                      run_id=run['run_id'], truth_source=source, alternative_source=alt_source,
                                      target_replicate=ridx, alternative_omitted_replicate=omit,
                                      primary_omission=int(omit == ridx), lag=lag, valid_pairs=10-lag,
                                      G_RAW_L=graw, G_SHUFFLED_L=gshuffle, I_LAG=graw-gshuffle)
                        lag_all.append(lagrow)
                        if omit == ridx:
                            lag_primary.append(lagrow)
    assert len(block_primary) == 64 and len(block_all) == 256
    assert len(lag_primary) == 64*9 and len(lag_all) == 256*9
    assert old_audit['C2']['banks'] == 320000 and old_audit['C2']['snapshot_multiset'] == 320000
    audit['r0_c2_views'] = old_audit['C2']['banks']
    audit['r0_c2_snapshot_multiset_assertions'] = old_audit['C2']['snapshot_multiset']
    assert audit['lag_surrogate_views'] == 320*9*1000
    assert audit['block_2_surrogate_views'] == audit['block_5_surrogate_views'] == 320000
    return lag_primary, block_primary, lag_all, block_all, audit


def group_lag(records, contexts, lag):
    groups = []
    for c in contexts:
        for source in (c['source_a'], c['source_b']):
            cases = [r for r in records if r['lag'] == lag and r['context'] == c['context']
                     and r['truth_source'] == source]
            assert len(cases) == 4
            groups.append(dict(lag=lag, context=c['context'], house=c['house'], wind=c['wind'],
                               gas=c['gas'], truth_source=source, targets=4,
                               mean_I_LAG=avg([r['I_LAG'] for r in cases]),
                               median_I_LAG=med([r['I_LAG'] for r in cases]),
                               mean_G_RAW_L=avg([r['G_RAW_L'] for r in cases]),
                               mean_G_SHUFFLED_L=avg([r['G_SHUFFLED_L'] for r in cases])))
    return groups


def group_block(records, contexts):
    groups = []
    for c in contexts:
        for source in (c['source_a'], c['source_b']):
            cases = [r for r in records if r['context'] == c['context'] and r['truth_source'] == source]
            assert len(cases) == 4
            row = dict(context=c['context'], house=c['house'], wind=c['wind'], gas=c['gas'],
                       truth_source=source, targets=4)
            for key in ('G_B1', 'G_B2', 'G_B5', 'G_B10', 'I_R0_CROSS'):
                row['mean_'+key] = avg([r[key] for r in cases])
                row['median_'+key] = med([r[key] for r in cases])
            denominator = row['mean_I_R0_CROSS']
            row['R_B2_group'] = (row['mean_G_B2']-row['mean_G_B1'])/denominator if denominator > 0 else ''
            row['R_B5_group'] = (row['mean_G_B5']-row['mean_G_B1'])/denominator if denominator > 0 else ''
            groups.append(row)
    return groups


def summary_lag(groups, contexts):
    assert len(groups) == 16
    context_means = {c['context']: avg([g['mean_I_LAG'] for g in groups if g['context'] == c['context']])
                     for c in contexts}
    return dict(House01_median=med([g['mean_I_LAG'] for g in groups if g['house'] == 'House01']),
                House02_median=med([g['mean_I_LAG'] for g in groups if g['house'] == 'House02']),
                pooled_group_median=med([g['mean_I_LAG'] for g in groups]),
                positive_groups=sum(g['mean_I_LAG'] > 0 for g in groups),
                positive_contexts=sum(v > 0 for v in context_means.values()),
                context_means=context_means,
                leave_one_context_out={c: med([g['mean_I_LAG'] for g in groups if g['context'] != c])
                                       for c in context_means})


def summary_block(groups):
    assert len(groups) == 16
    recovery = {}
    for house in ('House01', 'House02'):
        house_groups = [g for g in groups if g['house'] == house]
        recovery[house] = {}
        for length in (2, 5):
            values = [g[f'R_B{length}_group'] for g in house_groups]
            recovery[house][f'B{length}'] = med(values) if all(v != '' for v in values) else None
    return dict(House_recovery=recovery,
                House_r0_cross_median={house: med([g['mean_I_R0_CROSS'] for g in groups if g['house'] == house])
                                       for house in ('House01', 'House02')},
                positive_r0_cross_groups=sum(g['mean_I_R0_CROSS'] > 0 for g in groups),
                group_mean_denominator_min=min(g['mean_I_R0_CROSS'] for g in groups),
                pooled_B2_recovery=med([g['R_B2_group'] for g in groups])
                    if all(g['R_B2_group'] != '' for g in groups) else None,
                pooled_B5_recovery=med([g['R_B5_group'] for g in groups])
                    if all(g['R_B5_group'] != '' for g in groups) else None)


def stable_lag(s):
    return s['House01_median'] > 0 and s['House02_median'] > 0 and s['positive_groups'] >= 12


def recovery_at_least(b, length, value=2/3):
    return all(b['House_recovery'][h][f'B{length}'] is not None and
               b['House_recovery'][h][f'B{length}'] >= value for h in ('House01', 'House02'))


def recovery_below_both(b, length, value=2/3):
    return all(b['House_recovery'][h][f'B{length}'] is not None and
               b['House_recovery'][h][f'B{length}'] < value for h in ('House01', 'House02'))


def recovery_below_either(b, length, value=2/3):
    return any(b['House_recovery'][h][f'B{length}'] is not None and
               b['House_recovery'][h][f'B{length}'] < value for h in ('House01', 'House02'))


def run(outdir):
    outdir = Path(outdir)
    assert not outdir.exists()
    parity_record = parity()
    runs, contexts = r0.metadata_preflight()
    tensors, _ = r0.verify_inputs(runs, contexts)
    banks = r0.references(runs, tensors, contexts)
    lag_primary, block_primary, lag_all, block_all, audit = score_all(runs, contexts, banks)
    lag_groups = [g for lag in range(1, 10) for g in group_lag(lag_primary, contexts, lag)]
    block_groups = group_block(block_primary, contexts)
    lag_stats = {str(lag): summary_lag([g for g in lag_groups if g['lag'] == lag], contexts)
                 for lag in range(1, 10)}
    block_stats = summary_block(block_groups)
    omission = []
    omit_lag_stats = {}
    omit_block_stats = {}
    for omitted in range(1, 5):
        ls = [r for r in lag_all if r['alternative_omitted_replicate'] == omitted]
        bs = [r for r in block_all if r['alternative_omitted_replicate'] == omitted]
        assert len(ls) == 64*9 and len(bs) == 64
        omit_lag_stats[omitted] = {lag: summary_lag(group_lag(ls, contexts, lag), contexts)
                                   for lag in range(1, 10)}
        omit_block_stats[omitted] = summary_block(group_block(bs, contexts))
        for lag in range(1, 10):
            s = omit_lag_stats[omitted][lag]
            omission.append(dict(alternative_omitted_replicate=omitted, kind='LAG', lag=lag,
                                 House01_median=s['House01_median'], House02_median=s['House02_median'],
                                 positive_groups=s['positive_groups'], positive_contexts=s['positive_contexts'],
                                 B2_recovery_House01='', B2_recovery_House02='',
                                 B5_recovery_House01='', B5_recovery_House02=''))
        b = omit_block_stats[omitted]
        omission.append(dict(alternative_omitted_replicate=omitted, kind='BLOCK', lag='',
                             House01_median='', House02_median='', positive_groups='', positive_contexts='',
                             B2_recovery_House01=b['House_recovery']['House01']['B2'],
                             B2_recovery_House02=b['House_recovery']['House02']['B2'],
                             B5_recovery_House01=b['House_recovery']['House01']['B5'],
                             B5_recovery_House02=b['House_recovery']['House02']['B5']))
    short_primary = stable_lag(lag_stats['1']) and recovery_at_least(block_stats, 2)
    short_omissions = all(stable_lag(omit_lag_stats[o][1]) and recovery_at_least(omit_block_stats[o], 2)
                          for o in range(1, 5))
    short = short_primary and short_omissions
    broad_lags = [lag for lag in range(3, 10) if stable_lag(lag_stats[str(lag)]) and
                  all(stable_lag(omit_lag_stats[o][lag]) for o in range(1, 5))]
    broad_blocks = (recovery_below_both(block_stats, 2) and recovery_at_least(block_stats, 5) and
                    all(recovery_below_both(omit_block_stats[o], 2) and
                        recovery_at_least(omit_block_stats[o], 5) for o in range(1, 5)))
    broad = bool(broad_lags) or broad_blocks
    r0_stats = json.loads((R0/'R0_MECHANISM_SUMMARY.json').read_text())['stats']['I_CROSS']
    whole = (recovery_below_either(block_stats, 5) and
             all(recovery_below_either(omit_block_stats[o], 5) and
                 omit_block_stats[o]['House_recovery']['House01']['B5'] is not None and
                 omit_block_stats[o]['House_recovery']['House02']['B5'] is not None and
                 omit_block_stats[o]['House_r0_cross_median']['House01'] > 0 and
                 omit_block_stats[o]['House_r0_cross_median']['House02'] > 0 and
                 omit_block_stats[o]['positive_r0_cross_groups'] >= 12
                 for o in range(1, 5)) and
             r0_stats['house_medians']['House01'] > 0 and r0_stats['house_medians']['House02'] > 0)
    if short:
        decision = 'OCB_R2_R1_SHORT_MEMORY_DOMINANT'
    elif broad:
        decision = 'OCB_R2_R1_BROAD_MEMORY_REQUIRED'
    elif whole:
        decision = 'OCB_R2_R1_WHOLE_PATH_REQUIRED'
    else:
        decision = 'OCB_R2_R1_MEMORY_ANATOMY_HOLD'
    result = dict(decision=decision, short_primary=short_primary, short_all_omissions=short_omissions,
                  broad_lags_robust=broad_lags, broad_block_recovery_robust=broad_blocks,
                  whole_path_condition=whole, lag_stats=lag_stats, block_stats=block_stats,
                  omission_lag_stats=omit_lag_stats, omission_block_stats=omit_block_stats,
                  no_new_gaden=True, no_new_pmfs=True, no_training=True,
                  confirmation_and_house03_sealed=True)
    outdir.mkdir(parents=True)
    r0.write_tsv(outdir/'R1_LAG_TARGETS.tsv', lag_primary)
    r0.write_tsv(outdir/'R1_LAG_GROUPS.tsv', lag_groups)
    r0.write_tsv(outdir/'R1_BLOCK_TARGETS.tsv', block_primary)
    r0.write_tsv(outdir/'R1_BLOCK_GROUPS.tsv', block_groups)
    r0.write_tsv(outdir/'R1_REFERENCE_OMISSION.tsv', omission)
    r0.write_json(outdir/'R1_AGGREGATES.json', result)
    r0.write_json(outdir/'R1_PRESERVATION_AUDIT.json', audit)
    r0.write_json(outdir/'R1_INPUT_PARITY.json', parity_record)
    print(json.dumps(dict(decision=decision, lag1_groups=lag_stats['1']['positive_groups'],
                          B2_House_recovery={h: block_stats['House_recovery'][h]['B2']
                                             for h in ('House01', 'House02')},
                          B5_House_recovery={h: block_stats['House_recovery'][h]['B5']
                                             for h in ('House01', 'House02')}), sort_keys=True))


def selftest():
    ref = np.zeros((3, 10, 30), dtype=bool)
    ref[0, :, 0] = True
    ref[1, 0::2, 1] = True
    ref[2, 1::2, 2] = True
    target = ref[0].copy()
    audit = dict(lag_surrogate_views=0, lag_pair_preservation_assertions=0,
                 block_2_surrogate_views=0, block_2_block_preservation_assertions=0,
                 block_5_surrogate_views=0, block_5_block_preservation_assertions=0)
    for lag in (1, 5, 9):
        raw, surrogates = lag_scores(ref, target, lag, 0, 0, 1, 1, audit)
        assert np.isfinite(raw) and surrogates.shape == (N,) and np.isfinite(surrogates).all()
    for length in (2, 5):
        surrogates = block_scores(ref, target, length, 0, 0, 1, 1, audit)
        assert surrogates.shape == (N,) and np.isfinite(surrogates).all()
    assert fair_batch(np.zeros((1, 3, 60), dtype=bool), np.zeros(60, dtype=bool))[0] == 0
    print('R1_SYNTHETIC_SELFTEST_PASS')


if __name__ == '__main__':
    assert len(sys.argv) in (2, 3)
    if sys.argv[1] == 'selftest':
        selftest()
    elif sys.argv[1] == 'preflight' and len(sys.argv) == 3:
        r0.write_json(sys.argv[2], parity())
        print('OCB_R2_R1_INPUT_PARITY_PASS')
    elif sys.argv[1] == 'run' and len(sys.argv) == 3:
        run(sys.argv[2])
    else:
        raise SystemExit('Usage: run_r1.py selftest | preflight OUT.json | run OUTDIR')
