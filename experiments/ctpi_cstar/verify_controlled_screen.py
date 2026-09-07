"""Independent artifact-level recomputation; does not train or edit results."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ASSETS = ROOT / 'evidence/cstar_controlled_assets_20260907_r2'


def read(path):
    return json.loads(path.read_text())


def jsonl(path):
    return [json.loads(s) for s in path.read_text().splitlines()]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--results', type=Path, required=True)
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    result = args.results.resolve()
    m1, m2 = read(result/'M1_SCREEN.json'), read(result/'M2_BASELINE_SCREEN.json')
    cfg_path = HERE/'CSTAR_CONTROLLED_SCREEN_CONFIG_20260907.json'
    cfg, start = read(result/'FROZEN_CONFIG.json'), read(result/'RUN_START.json')
    assert start['config_sha256'] == m1['config_sha256'] == sha(cfg_path)
    if 'effective_config_sha256' in start:
        assert start['effective_config_sha256'] == m1['effective_config_sha256'] == sha(result/'FROZEN_CONFIG.json')
        assert start['metric_coordinate_contract'] == m1['metric_coordinate_contract'] == 'raw_candidate_xy_m_v2'
        for path,digest in start['code_sha256'].items():
            snapshot=result/'source_snapshot'/path
            assert sha(snapshot if snapshot.is_file() else ROOT/path) == digest, 'PRODUCER_CODE_CHANGED'
    else:
        assert cfg == read(cfg_path), 'LEGACY_VARIANT_NEEDS_SEPARATE_RECOMPUTATION'
    records, candidates, label_candidates = {}, {}, {}
    for row in read(ASSETS/'manifests/H01.json')['m1_episodes']:
        records[row['realization_id']] = row
        path = ASSETS / row['candidate_domain_path']
        assert sha(path) == row['candidate_domain_sha256']
        with path.open() as f:
            xy = np.array([[float(r['x']),float(r['y'])] for r in csv.DictReader(f)],dtype=np.float32)
        candidates[row['house']] = xy if start.get('metric_coordinate_contract') == 'raw_candidate_xy_m_v2' else (xy / np.float32(10))*np.float32(10)
        label_candidates[row['house']] = xy
    verified_rows, fold_checks = 0, []
    for fold in m1['folds']:
        held, metrics = fold['heldout_house'], fold['metrics']
        assert read(result/held/'FOLD_RESULT.json') == fold
        for variant in cfg['variants']:
            assert sha(result/held/(variant+'.pt')) == metrics[variant]['checkpoint_sha256']
            log = read(result/held/(variant+'_training.json'))
            assert len(log) == 200 and [r['step'] for r in log] == list(range(1,201))
            assert all(r['house'] != held and r['prefix_s'] in range(4,61,4) for r in log)
        for rowpath in (result/held).glob('*_rows.json'):
            stem = rowpath.name[:-len('_rows.json')]
            rows = read(rowpath)
            values = np.load(result/held/(stem+'_predictions.npz'))
            p, z = values['posterior'], values['z_source']
            assert p.shape[0:2] == (15,4) and z.shape == (15,4,24)
            assert np.isfinite(p).all() and (p>=0).all() and np.allclose(p.sum(-1),1,atol=2e-6)
            assert len(rows) == 60
            for k,row in enumerate(rows):
                t, i = divmod(k,4)
                meta = records[row['rid']]
                xy = candidates[meta['house']]
                truth = np.array(meta['source_xyz_m'][:2],dtype=np.float32)
                label = int(((label_candidates[meta['house']]-truth)**2).sum(-1).argmin())
                prob = float(p[t,i,label])
                if prob > 1e-35:
                    assert abs(-math.log(prob)-row['nll']) < 2e-4, 'NLL_MISMATCH'
                else:
                    assert row['nll'] > 80, 'UNDERFLOW_NLL_CONTRADICTION'
                error = float(np.linalg.norm(xy[p[t,i].argmax()]-truth))
                assert abs(error-row['source_error_m']) < 2e-5, 'LOCALIZATION_MISMATCH'
                entropy = float(-(p[t,i]*np.log(np.maximum(p[t,i],1e-30))).sum()/math.log(p.shape[-1]))
                assert abs(entropy-row['normalized_entropy']) < 2e-6, 'ENTROPY_MISMATCH'
                same = float(np.linalg.norm(z[t,[0,2]]-z[t,[1,3]],axis=-1).mean())
                different = float(np.linalg.norm(z[t,[0,0,1,1]]-z[t,[2,3,2,3]],axis=-1).mean())
                assert abs(same-row['same_z']) < 2e-5 and abs(different-row['different_z']) < 2e-5
                assert row['prefix_s'] == 4*(t+1)
                verified_rows += 1
            if '_train_' in stem:
                variant, train_house = stem.split('_train_')
                summary = metrics[variant]['train_metrics'][train_house]
            else:
                summary = metrics[stem]
            assert sha(result/held/(stem+'_predictions.npz')) == summary['predictions_sha256']
            for key in ['nll','source_error_m','normalized_entropy','same_z','different_z','same_different_ratio']:
                assert abs(np.mean([r[key] for r in rows])-summary[key]) < 1e-7
        p = np.load(result/held/'picr_predictions.npz')['posterior']
        zero = np.load(result/held/'zs_zero_predictions.npz')['posterior']
        swap = np.load(result/held/'zs_swap_predictions.npz')['posterior']
        assert np.allclose(zero,1/zero.shape[-1],atol=1e-7)
        assert np.allclose(swap,p[:,[2,3,0,1]],atol=1e-7), 'ZS_SWAP_NOT_EXECUTED'
        c,b = metrics['picr'],metrics['unconstrained']
        checks = {'proper_score_better':c['nll'] < b['nll'],
            'localization_better':c['source_error_m'] < b['source_error_m'],
            'invariance_better':c['same_z'] < b['same_z'],
            'relative_invariance_better':c['same_different_ratio'] < b['same_different_ratio'],
            'separation_not_collapsed':c['different_z'] >= .9*b['different_z'],
            'context_only_beaten':c['nll'] < metrics['context_only']['nll'] and c['source_error_m'] < metrics['context_only']['source_error_m'],
            'label_permutation_destroyed_gain':metrics['label_permutation']['nll'] >= b['nll'] and metrics['label_permutation']['source_error_m'] >= b['source_error_m'],
            'zs_zero_destroys_gain':metrics['zs_zero']['nll'] > c['nll'],
            'zs_swap_destroys_gain':metrics['zs_swap']['nll'] > c['nll'] and metrics['zs_swap']['source_error_m'] > c['source_error_m'],
            'uninformative_uncertainty':metrics['uninformative']['min_normalized_entropy'] >= .95 or metrics['uninformative']['abstain_count'] == 60}
        assert checks == fold['checks'] and all(checks.values()) == fold['all_checks_pass']
        fold_checks.append({'house':held,'failed_checks':[k for k,v in checks.items() if not v],
                            'picr_worse_than_uniform_nll':c['nll'] > math.log(candidates[held].shape[0]),
                            'uninformative_mean_entropy':metrics['uninformative']['normalized_entropy']})
    assert m1['pass'] == (sum(f['all_checks_pass'] for f in m1['folds']) >= 2)
    for fold in m2['folds']:
        held = fold['heldout_house']
        manifest = read(ASSETS/'manifests'/(held+'.json'))
        assert start['asset_manifests'][held] == sha(ASSETS/'manifests'/(held+'.json'))
        histories = {r['episode_id']:jsonl(ASSETS/r['history_trace_path']) for r in manifest['m1_episodes']}
        table, all_counts = np.ones((2,21))/21, np.ones(21)/21
        dataset = {}
        for r in manifest['m2_route_cases']:
            gas = [f['gas_ppm'] for f in histories[r['episode_id']] if f['t_sim_s'] <= r['decision_time_s']][-1]
            target = next((i for i,f in enumerate(jsonl(ASSETS/r['outcome_trace_path'])) if f['gas_ppm']>.1),20)
            bucket = int(gas>.1)
            dataset[r['decision_id']] = (bucket,target,r['split'])
            if r['split'] == 'train': table[bucket,target] += 1; all_counts[target] += 1
        table /= table.sum(-1,keepdims=True)
        all_counts /= all_counts.sum()
        raw = read(result/('M2_'+held+'_raw.json'))
        assert len(raw) == 84
        for r in raw:
            bucket,target,split = dataset[r['decision_id']]
            assert split == 'heldout' and target == r['target']
            assert np.allclose(r['persistence_law'],table[bucket],atol=1e-12)
            assert np.allclose(r['unconditional_law'],all_counts,atol=1e-12)
            assert abs(-math.log(table[bucket,target])-r['nll']) < 1e-12
            assert abs(float(((table[bucket]-np.eye(21)[target])**2).sum())-r['brier']) < 1e-12
        for key,value in fold['metrics'].items():
            assert abs(np.mean([r[key] for r in raw])-value) < 1e-12
    report = {'contract':'CSTAR_CONTROLLED_SCREEN_RECOMPUTATION_V1','pass':True,
        'verified_m1_prediction_rows':verified_rows,'verified_m2_cases':252,
        'm1_result':m1['verdict'],'m1_diagnostics':fold_checks,
        'interpretation':'verification PASS is not scientific gate PASS; no closed-loop authorization'}
    if args.output:
        args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__ == '__main__': main()
