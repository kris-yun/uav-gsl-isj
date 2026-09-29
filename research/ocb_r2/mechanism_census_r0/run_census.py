#!/usr/bin/env python3
"""Discovery-only source-information mechanism census, frozen R0 contract."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import statistics
import sys

import numpy as np


REPO = Path(__file__).resolve().parents[3]
E = REPO/'evidence/ocb_r2'
O = E/'mechanism_census_r0'
I = O/'inputs'
S2 = E/'OCB_R2_S2_DISCOVERY_RUNLIST_32.tsv'
S2X = E/'s2x/OCB_R2_S2X_RUNLIST_32.tsv'
F0 = I/'AOD_R2_F0_TARGET_EXTRACTION.json'
R0 = REPO/'research/ocb_r2/OCB_R2_SOURCE_INFORMATION_MECHANISM_CENSUS_R0.md'
FROZEN = REPO/'research/ocb_r2/mechanism_census_r0/R0_PROTOCOL_FROZEN.md'
N_SURROGATE = 1000
N_NULL = 10000
K = 3


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def rows(path):
    with Path(path).open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False)+'\n')


def write_tsv(path, records):
    assert records
    with Path(path).open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]), delimiter='\t', lineterminator='\n')
        writer.writeheader()
        writer.writerows(records)


def median(values):
    return float(statistics.median(float(v) for v in values))


def mean(values):
    return float(statistics.mean(float(v) for v in values))


def metadata_preflight():
    """No concentration values are decoded in this step."""
    assert R0.is_file() and FROZEN.is_file()
    s2, s2x = rows(S2), rows(S2X)
    assert len(s2) == len(s2x) == 32
    runs = []
    for phase, source, folder in [('S2', s2, E/'s2_runs'), ('S2X', s2x, E/'s2x/runs')]:
        for r in source:
            context = int(r['config_index'] if phase == 'S2' else r['parent_s2_config_index'])
            run_id = r['run_id']
            manifest_path = folder/f'{run_id}.RUN_MANIFEST.json'
            qc_path = folder/f'{run_id}.QC.json'
            manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
            qc = json.loads(qc_path.read_text(encoding='utf-8-sig'))
            assert manifest['run_id'] == run_id
            assert manifest['house'] == r['house'] and manifest['source_id'] == r['source_id']
            assert manifest['wind_id'] == r['wind_id']
            assert manifest['master_seed'] == int(r['master_seed'])
            assert int(manifest['simulation_parameters']['gas_type']) == int(r['gas_type'])
            assert tuple(float(manifest['simulation_parameters'][f'source_position_{d}']) for d in 'xyz') == \
                tuple(float(r[f'source_{d}']) for d in 'xyz')
            assert qc['record_count'] == 1803 and qc['first_time_s'] == 0 and qc['last_time_s'] == 999.502991
            assert qc['binary_sha256'] == manifest['generator_binary_sha256'] == \
                'ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688'
            timeline = folder/f'{run_id}.RECORD_TIMELINE.tsv'
            assert sha(timeline) == qc['timeline_sha256']
            asset = manifest['asset_checks']
            key = (r['house'], r['wind_id'], int(r['gas_type']), asset['occupancy_sha256'],
                   asset['wind_bundle_sha256'], qc['binary_sha256'], qc['timeline_sha256'],
                   qc['wind_index_sequence_sha256'])
            replica = int(r['replicate_index']) if phase == 'S2' else int(run_id.rsplit('_r', 1)[1])
            assert 1 <= replica <= 4
            runs.append(dict(run_id=run_id, phase=phase, context=f'X{context:02d}',
                             house=r['house'], source=r['source_id'], replica=replica,
                             seed=int(r['master_seed']), key=key,
                             manifest_sha256=sha(manifest_path), qc_sha256=sha(qc_path)))
    assert len(runs) == 64 and len({r['run_id'] for r in runs}) == 64
    assert len({r['seed'] for r in runs}) == 64
    contexts = []
    for c in (f'X{i:02d}' for i in range(8)):
        subset = [r for r in runs if r['context'] == c]
        assert len(subset) == 8 and len({r['key'] for r in subset}) == 1
        assert {r['phase'] for r in subset} == {'S2', 'S2X'}
        sources = sorted({r['source'] for r in subset})
        assert len(sources) == 2
        for source in sources:
            this = [r for r in subset if r['source'] == source]
            assert len(this) == 4 and {r['replica'] for r in this} == {1, 2, 3, 4}
            assert len({r['seed'] for r in this}) == 4
        key = subset[0]['key']
        contexts.append(dict(context=c, house=key[0], wind=key[1], gas=key[2],
                             source_a=sources[0], source_b=sources[1],
                             occupancy_sha256=key[3], wind_bundle_sha256=key[4],
                             generator_sha256=key[5], timeline_sha256=key[6],
                             wind_index_sequence_sha256=key[7], run_count=8))
    assert sum(c['house'] == 'House01' for c in contexts) == 4
    assert sum(c['house'] == 'House02' for c in contexts) == 4
    assert all(sum('fast' in c['wind'] for c in contexts if c['house'] == h) == 2 for h in ('House01', 'House02'))
    return runs, contexts


def verify_inputs(runs, contexts):
    previous = json.loads((I/'AOD_R2_F0_D0A_COMPARABILITY.json').read_text())
    assert previous['decision'] == 'OCB_R2_D0A_SOURCE_COMPARABILITY_PASS'
    assert {(c['context'], c['house'], c['source_a'], c['source_b']) for c in contexts} == \
        {(c['context'], c['house'], c['source_a'], c['source_b']) for c in previous['contexts']}
    frozen = json.loads((I/'AOD_R2_F0_PRE_TARGET_FREEZE.json').read_text())
    assert frozen['decision'] == 'AOD_R2_F0_METADATA_FROZEN_NO_TARGET_READ'
    assert frozen['target_runs'] == 64 and frozen['time_mapping_rows'] == 640
    mapping = rows(I/'AOD_R2_F0_TIME_MAPPING.tsv')
    assert len(mapping) == 640 and {r['run_id'] for r in mapping} == {r['run_id'] for r in runs}
    for run in runs:
        slots = [r for r in mapping if r['run_id'] == run['run_id']]
        assert len(slots) == 10 and {int(r['slot']) for r in slots} == set(range(1, 11))
        assert {int(r['requested_time_s']) for r in slots} == set(range(50, 501, 50))
    extraction = json.loads(F0.read_text())
    assert extraction['decision'] == 'AOD_R2_F0_TARGETS_EXTRACTED'
    assert {r['run_id'] for r in extraction['runs']} == {r['run_id'] for r in runs}
    hashes = {}
    tensors = {}
    for record in extraction['runs']:
        path = I/f"{record['run_id']}.pooled.npy"
        digest = sha(path)
        assert digest == record['pooled_sha256']
        tensor = np.load(path, allow_pickle=False)
        assert tensor.shape == (10, 30) and np.isfinite(tensor).all() and (tensor >= 0).all()
        tensors[record['run_id']] = tensor > 0
        hashes[record['run_id']] = digest
    paths = [R0, FROZEN, S2, S2X, I/'AOD_R2_F0_D0A_COMPARABILITY.json',
             I/'AOD_R2_F0_PRE_TARGET_FREEZE.json', I/'AOD_R2_F0_TIME_MAPPING.tsv', F0,
             Path(__file__)]
    return tensors, dict(input_file_sha256={str(p.relative_to(REPO)).replace('\\', '/'): sha(p) for p in paths},
                         pooled_tensor_sha256=hashes, encounter_definition='concentration > 0',
                         target_count=64, tensor_shape=[10, 30], confirmation_and_house03_sealed=True)


def references(runs, tensors, contexts):
    lookup = {(r['context'], r['source'], r['replica']): tensors[r['run_id']] for r in runs}
    assert len(lookup) == 64
    result = {}
    for c in contexts:
        for sidx, source in enumerate((c['source_a'], c['source_b'])):
            result[(c['context'], sidx)] = np.stack([lookup[(c['context'], source, r)] for r in range(1, 5)])
    return result


def marginal_scores(ref, target):
    p = ref.mean(axis=0)
    y = target.astype(np.float64)
    return dict(M_TIME=float(np.square(p.mean(axis=1)-y.mean(axis=1)).mean()),
                M_SPACE=float(np.square(p.mean(axis=0)-y.mean(axis=0)).mean()),
                M_FULL=float(np.square(p-y).mean()))


def energy_batch(banks, target):
    """Fair-U Energy Score for a batch of K=3 binary 300D ensembles."""
    assert banks.ndim == 3 and banks.shape[1:] == (3, 300)
    assert target.shape == (300,)
    fit = np.sqrt(np.count_nonzero(banks != target[None, None, :], axis=2)).mean(axis=1)
    diversity = sum(np.sqrt(np.count_nonzero(banks[:, i] != banks[:, j], axis=1))
                    for i, j in ((0, 1), (0, 2), (1, 2))) / 6.0
    return fit-diversity


def surrogate_scores(ref, target, mode, cidx, sidx, ridx, omitted, audit):
    assert ref.shape == (3, 10, 30) and ref.dtype == np.bool_
    seed = 2026093001 if mode == 'C1' else 2026093002
    rng = np.random.default_rng(np.random.SeedSequence([seed, cidx, sidx, ridx, omitted]))
    if mode == 'C1':
        base = ref.reshape(3, 300).T
        perm = np.argsort(rng.random((N_SURROGATE, 300, 3)), axis=-1, kind='stable')
        banks = np.take_along_axis(np.broadcast_to(base, (N_SURROGATE, 300, 3)), perm,
                                   axis=2).transpose(0, 2, 1)
    else:
        base = ref.transpose(1, 0, 2)
        perm = np.argsort(rng.random((N_SURROGATE, 10, 3)), axis=-1, kind='stable')
        banks = np.take_along_axis(np.broadcast_to(base, (N_SURROGATE, 10, 3, 30)),
                                   perm[:, :, :, None], axis=2).transpose(0, 2, 1, 3).reshape(N_SURROGATE, 3, 300)
    assert banks.shape == (N_SURROGATE, 3, 300) and banks.dtype == np.bool_
    assert np.array_equal(banks.sum(axis=1), np.broadcast_to(ref.reshape(3, 300).sum(axis=0),
                                                            (N_SURROGATE, 300)))
    if mode == 'C2':
        powers = 1 << np.arange(30, dtype=np.int64)
        original_codes = (ref.astype(np.int64)*powers).sum(axis=2)
        new_codes = (banks.reshape(N_SURROGATE, 3, 10, 30).astype(np.int64)*powers).sum(axis=3)
        assert np.array_equal(np.sort(new_codes, axis=1),
                              np.broadcast_to(np.sort(original_codes, axis=0),
                                              (N_SURROGATE, 3, 10)))
    audit[mode]['banks'] += N_SURROGATE
    audit[mode]['binary'] += N_SURROGATE
    audit[mode]['marginals'] += N_SURROGATE
    if mode == 'C2':
        audit[mode]['snapshot_multiset'] += N_SURROGATE
    return energy_batch(banks, target.reshape(300))


def score_targets(runs, contexts, banks):
    target_rows, marginal_rows, omission_rows = [], [], []
    audit = {mode: dict(banks=0, binary=0, marginals=0, snapshot_multiset=0)
             for mode in ('C1', 'C2')}
    run_lookup = {(r['context'], r['source'], r['replica']): r for r in runs}
    for cidx, c in enumerate(contexts):
        context = c['context']
        for sidx, source in enumerate((c['source_a'], c['source_b'])):
            altidx = 1-sidx
            alt_source = (c['source_a'], c['source_b'])[altidx]
            for ridx in range(4):
                run = run_lookup[(context, source, ridx+1)]
                target = banks[(context, sidx)][ridx]
                truth_ref = np.delete(banks[(context, sidx)], ridx, axis=0)
                truth_m = marginal_scores(truth_ref, target)
                truth_raw = float(energy_batch(truth_ref.reshape(1, 3, 300), target.reshape(300))[0])
                truth_c1 = surrogate_scores(truth_ref, target, 'C1', cidx, sidx, ridx+1, ridx+1, audit)
                truth_c2 = surrogate_scores(truth_ref, target, 'C2', cidx, sidx, ridx+1, ridx+1, audit)
                for omit in range(4):
                    alt_ref = np.delete(banks[(context, altidx)], omit, axis=0)
                    alt_m = marginal_scores(alt_ref, target)
                    alt_raw = float(energy_batch(alt_ref.reshape(1, 3, 300), target.reshape(300))[0])
                    alt_c1 = surrogate_scores(alt_ref, target, 'C1', cidx, altidx, ridx+1, omit+1, audit)
                    alt_c2 = surrogate_scores(alt_ref, target, 'C2', cidx, altidx, ridx+1, omit+1, audit)
                    g_c1 = median(alt_c1-truth_c1)
                    g_c2 = median(alt_c2-truth_c2)
                    g_raw = alt_raw-truth_raw
                    row = dict(context=context, house=c['house'], wind=c['wind'], gas=c['gas'],
                               run_id=run['run_id'], truth_source=source, alternative_source=alt_source,
                               target_replicate=ridx+1, alternative_omitted_replicate=omit+1,
                               primary_omission=int(omit == ridx),
                               G_M_TIME=alt_m['M_TIME']-truth_m['M_TIME'],
                               G_M_SPACE=alt_m['M_SPACE']-truth_m['M_SPACE'],
                               G_M_FULL=alt_m['M_FULL']-truth_m['M_FULL'],
                               G_C1=g_c1, G_C2=g_c2, G_RAW=g_raw,
                               I_SPATIAL=g_c2-g_c1, I_CROSS=g_raw-g_c2,
                               I_TOTAL_DEP=g_raw-g_c1)
                    omission_rows.append(row)
                    if omit == ridx:
                        target_rows.append(row)
                        marginal_rows.append({k: row[k] for k in ('context', 'house', 'wind', 'gas', 'run_id',
                                                                    'truth_source', 'target_replicate',
                                                                    'G_M_TIME', 'G_M_SPACE', 'G_M_FULL')})
    assert len(target_rows) == len(marginal_rows) == 64 and len(omission_rows) == 256
    assert audit['C1']['banks'] == audit['C2']['banks'] == 320000
    return target_rows, marginal_rows, omission_rows, audit


MEASURES = ('G_M_TIME', 'G_M_SPACE', 'G_M_FULL', 'G_C1', 'G_C2', 'G_RAW',
            'I_SPATIAL', 'I_CROSS', 'I_TOTAL_DEP')


def aggregate(targets, contexts):
    groups = []
    for c in contexts:
        for source in (c['source_a'], c['source_b']):
            subset = [r for r in targets if r['context'] == c['context'] and r['truth_source'] == source]
            assert len(subset) == 4
            row = dict(context=c['context'], house=c['house'], wind=c['wind'], gas=c['gas'],
                       truth_source=source, target_count=4)
            for measure in MEASURES:
                row[measure+'_mean'] = mean([r[measure] for r in subset])
                row[measure+'_median'] = median([r[measure] for r in subset])
            groups.append(row)
    context_rows = []
    for c in contexts:
        subset = [g for g in groups if g['context'] == c['context']]
        assert len(subset) == 2
        row = dict(context=c['context'], house=c['house'], wind=c['wind'], gas=c['gas'], group_count=2)
        for measure in MEASURES:
            row[measure+'_mean'] = mean([g[measure+'_mean'] for g in subset])
            row[measure+'_median'] = median([g[measure+'_mean'] for g in subset])
        context_rows.append(row)
    return groups, context_rows


def stats_for(groups, contexts, measure):
    values = [g[measure+'_mean'] for g in groups]
    houses = {h: median([g[measure+'_mean'] for g in groups if g['house'] == h])
              for h in ('House01', 'House02')}
    context_values = {c['context']: c[measure+'_mean'] for c in contexts}
    leave_one = {c: median([g[measure+'_mean'] for g in groups if g['context'] != c])
                 for c in context_values}
    total_abs = sum(abs(v) for v in context_values.values())
    concentration = max(abs(v) for v in context_values.values())/total_abs if total_abs else 1.0
    return dict(pooled_median=median(values), pooled_mean=mean(values), house_medians=houses,
                positive_groups=sum(v > 0 for v in values),
                positive_contexts=sum(v > 0 for v in context_values.values()),
                context_means=context_values, leave_one_context_out=leave_one,
                max_context_absolute_share=concentration)


def label_null(groups, contexts, measure):
    observed = mean([g[measure+'_mean'] for g in groups])
    context_effects = np.array([next(c[measure+'_mean'] for c in contexts if c['context'] == f'X{i:02d}')
                                for i in range(8)], dtype=np.float64)
    rng = np.random.default_rng(2026093003)
    signs = rng.integers(0, 2, size=(N_NULL, 8), dtype=np.int8)*2-1
    null = (signs*context_effects).mean(axis=1)
    reference = float((1+np.count_nonzero(null >= observed))/(N_NULL+1))
    return dict(observed_group_mean=observed, one_sided_reference=reference,
                null_mean=float(null.mean()), null_q05=float(np.quantile(null, .05)),
                null_q95=float(np.quantile(null, .95)), draws=N_NULL,
                seed=2026093003, sign_unit='paired source groups within context')


def omission_summary(omissions, contexts):
    output = []
    for omitted in range(1, 5):
        selected = [r for r in omissions if r['alternative_omitted_replicate'] == omitted]
        assert len(selected) == 64
        groups, context_rows = aggregate(selected, contexts)
        for measure in ('G_M_FULL', 'I_SPATIAL', 'I_CROSS'):
            s = stats_for(groups, context_rows, measure)
            output.append(dict(alternative_omitted_replicate=omitted, measure=measure,
                               pooled_median=s['pooled_median'], House01_median=s['house_medians']['House01'],
                               House02_median=s['house_medians']['House02'],
                               positive_groups=s['positive_groups'], positive_contexts=s['positive_contexts']))
    return output


def gate(stats, null, omissions, measure):
    s = stats[measure]
    om = [r for r in omissions if r['measure'] == measure]
    return dict(house01_positive=s['house_medians']['House01'] > 0,
                house02_positive=s['house_medians']['House02'] > 0,
                at_least_12_groups=s['positive_groups'] >= 12,
                at_least_6_contexts=s['positive_contexts'] >= 6,
                all_leave_one_positive=all(v > 0 for v in s['leave_one_context_out'].values()),
                label_null_le_005=null[measure]['one_sided_reference'] <= .05,
                all_alt_omissions_positive=all(r['pooled_median'] > 0 and r['House01_median'] > 0
                                               and r['House02_median'] > 0 for r in om),
                max_context_share_le_040=s['max_context_absolute_share'] <= .4,
                preservation_assertions_pass=True)


def run(outdir):
    outdir = Path(outdir)
    assert not outdir.exists()
    runs, contexts = metadata_preflight()
    tensors, input_hashes = verify_inputs(runs, contexts)
    banks = references(runs, tensors, contexts)
    targets, marginals, omissions, preservation = score_targets(runs, contexts, banks)
    groups, context_rows = aggregate(targets, contexts)
    stats = {measure: stats_for(groups, context_rows, measure) for measure in MEASURES}
    null = {measure: label_null(groups, context_rows, measure) for measure in ('I_SPATIAL', 'I_CROSS')}
    omission = omission_summary(omissions, contexts)
    gates = {measure: gate(stats, null, omission, measure) for measure in ('I_SPATIAL', 'I_CROSS')}
    mfull = stats['G_M_FULL']
    mfull_stable = (all(v > 0 for v in mfull['house_medians'].values()) and
                    mfull['positive_groups'] >= 12 and mfull['positive_contexts'] >= 6)
    if all(gates['I_CROSS'].values()):
        decision = 'OCB_R2_MECH_CROSS_TIME_STABLE'
    elif all(gates['I_SPATIAL'].values()):
        decision = 'OCB_R2_MECH_SPATIAL_JOINT_STABLE'
    elif mfull_stable:
        decision = 'OCB_R2_MECH_MARGINAL_DOMINANT'
    elif all(v <= 0 for v in mfull['house_medians'].values()):
        decision = 'OCB_R2_MECH_OBSERVATION_INSUFFICIENT'
    else:
        decision = 'OCB_R2_MECH_INCONSISTENT_HOLD'
    all_mfull_correct = all(r['G_M_FULL'] > 0 for r in targets)
    ranked = sorted(targets, key=lambda r: r['G_M_FULL'])
    hard = ranked[:16]
    strata = {}
    for kind, predicate in [('fast', lambda r: 'fast' in r['wind']),
                            ('slow', lambda r: 'slow' in r['wind']),
                            ('gas10', lambda r: int(r['gas']) == 10),
                            ('gas13', lambda r: int(r['gas']) == 13)]:
        subset = [g for g in groups if predicate(g)]
        strata[kind] = {m: median([g[m+'_mean'] for g in subset]) for m in ('G_M_FULL', 'I_SPATIAL', 'I_CROSS')}
    summary = dict(decision=decision, source_context_groups=16, targets=64, contexts=8,
                   all_64_mfull_correct=all_mfull_correct,
                   mfull_positive_targets=sum(r['G_M_FULL'] > 0 for r in targets),
                   mfull_stable=mfull_stable, stats=stats, gates=gates, null=null,
                   strata=strata, hard_bottom_quartile=dict(count=len(hard),
                   max_G_M_FULL=max(r['G_M_FULL'] for r in hard),
                   median_I_SPATIAL=median([r['I_SPATIAL'] for r in hard]),
                   median_I_CROSS=median([r['I_CROSS'] for r in hard])),
                   no_new_gaden=True, no_new_pmfs=True,
                   confirmation_and_house03_sealed=True)
    outdir.mkdir(parents=True)
    write_tsv(outdir/'R0_MARGINAL_ANATOMY.tsv', marginals)
    write_tsv(outdir/'R0_TARGET_EFFECTS.tsv', targets)
    write_tsv(outdir/'R0_GROUP_EFFECTS.tsv', groups)
    write_tsv(outdir/'R0_CONTEXT_EFFECTS.tsv', context_rows)
    write_tsv(outdir/'R0_REFERENCE_OMISSION_ROBUSTNESS.tsv', omission)
    write_json(outdir/'R0_PRESERVATION_AUDIT.json', preservation)
    write_json(outdir/'R0_NULL_REFERENCE.json', null)
    write_json(outdir/'R0_INPUT_HASHES.json', input_hashes)
    write_json(outdir/'R0_MECHANISM_SUMMARY.json', summary)
    print(json.dumps(dict(decision=decision, mfull_positive_targets=summary['mfull_positive_targets'],
                          spatial_positive_groups=stats['I_SPATIAL']['positive_groups'],
                          cross_positive_groups=stats['I_CROSS']['positive_groups']), sort_keys=True))


def preflight(out):
    runs, contexts = metadata_preflight()
    output = dict(decision='OCB_R2_D0A_SOURCE_COMPARABILITY_PASS',
                  contexts=contexts, run_count=len(runs), source_positions_per_context=2,
                  independent_realizations_per_source=4, concentration_values_read=False,
                  new_gaden=0, confirmation_and_house03_sealed=True,
                  protocol_sha256=sha(R0), operational_freeze_sha256=sha(FROZEN),
                  runlist_sha256={str(p.relative_to(REPO)).replace('\\', '/'): sha(p) for p in (S2, S2X)})
    write_json(out, output)
    print(json.dumps(dict(decision=output['decision'], contexts=len(contexts), runs=len(runs))))


def selftest():
    x = np.array([[[1, 0, 1], [0, 1, 0]], [[0, 1, 0], [1, 0, 1]],
                  [[1, 1, 0], [0, 0, 1]]], dtype=bool)
    ref = np.zeros((3, 10, 30), dtype=bool)
    ref[:, :2, :3] = x
    target = ref[0].copy()
    audit = {mode: dict(banks=0, binary=0, marginals=0, snapshot_multiset=0)
             for mode in ('C1', 'C2')}
    c1 = surrogate_scores(ref, target, 'C1', 0, 0, 1, 1, audit)
    c2 = surrogate_scores(ref, target, 'C2', 0, 0, 1, 1, audit)
    assert c1.shape == c2.shape == (1000,)
    assert np.isfinite(c1).all() and np.isfinite(c2).all()
    assert audit['C1']['banks'] == audit['C2']['banks'] == 1000
    zero = np.zeros((1, 3, 300), dtype=bool)
    assert energy_batch(zero, zero[0, 0]).item() == 0
    print('R0_SYNTHETIC_SELFTEST_PASS')


if __name__ == '__main__':
    assert len(sys.argv) in (2, 3)
    if sys.argv[1] == 'selftest':
        selftest()
    elif sys.argv[1] == 'preflight' and len(sys.argv) == 3:
        preflight(sys.argv[2])
    elif sys.argv[1] == 'run' and len(sys.argv) == 3:
        run(sys.argv[2])
    else:
        raise SystemExit('Usage: run_census.py selftest | preflight OUT.json | run OUTDIR')
