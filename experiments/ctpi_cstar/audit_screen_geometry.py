"""Recompute physical localization from archived posteriors; never retrain.

Original files stay immutable. Outputs bind each report and posterior file
and replace only the erroneous normalized-to-metre localization metric.
"""
import argparse
import copy
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / 'evidence/cstar_controlled_assets_20260907_r2'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def checks(m):
    c, b = m['picr'], m['unconstrained']
    return dict(
        proper_score_better=c['nll'] < b['nll'],
        localization_better=c['source_error_m'] < b['source_error_m'],
        invariance_better=c['same_z'] < b['same_z'],
        relative_invariance_better=c['same_different_ratio'] < b['same_different_ratio'],
        separation_not_collapsed=c['different_z'] >= .9*b['different_z'],
        context_only_beaten=c['nll'] < m['context_only']['nll'] and c['source_error_m'] < m['context_only']['source_error_m'],
        label_permutation_destroyed_gain=m['label_permutation']['nll'] >= b['nll'] and m['label_permutation']['source_error_m'] >= b['source_error_m'],
        zs_zero_destroys_gain=m['zs_zero']['nll'] > c['nll'],
        zs_swap_destroys_gain=m['zs_swap']['nll'] > c['nll'] and m['zs_swap']['source_error_m'] > c['source_error_m'],
        uninformative_uncertainty=m['uninformative']['min_normalized_entropy'] >= .95 or m['uninformative']['abstain_count'] == 60,
    )


def audit(directory):
    report_path = directory/'M1_SCREEN.json'
    report = copy.deepcopy(json.loads(report_path.read_text()))
    manifest = json.loads((ASSETS/'manifests/H01.json').read_text())
    records = {r['realization_id']:r for r in manifest['m1_episodes']}
    candidates = {}
    for r in records.values():
        path = ASSETS/r['candidate_domain_path']
        assert sha(path) == r['candidate_domain_sha256']
        with path.open() as f:
            candidates[r['house']] = np.array([[float(x['x']),float(x['y'])] for x in csv.DictReader(f)])
    bindings, differences = {}, []
    for fold in report['folds']:
        h = fold['heldout_house']
        for rp in sorted((directory/h).glob('*_rows.json')):
            stem = rp.name[:-10]
            rows = json.loads(rp.read_text())
            pp = rp.with_name(stem+'_predictions.npz')
            p = np.load(pp)['posterior']
            assert p.shape[:2] == (15,4) and len(rows) == 60
            assert np.isfinite(p).all() and (p >= 0).all() and np.allclose(p.sum(-1),1,atol=2e-6)
            if '_train_' in stem:
                v, th = stem.split('_train_')
                summary = fold['metrics'][v]['train_metrics'][th]
            else:
                summary = fold['metrics'][stem]
            assert sha(pp) == summary['predictions_sha256']
            errors = []
            for k,row in enumerate(rows):
                t,i = divmod(k,4)
                meta = records[row['rid']]
                xy = candidates[meta['house']]
                errors.append(float(np.linalg.norm(xy[p[t,i].argmax()]-meta['source_xyz_m'][:2])))
            before = summary['source_error_m']
            summary['source_error_m'] = float(np.mean(errors))
            bindings[str(pp.relative_to(directory))] = sha(pp)
            bindings[str(rp.relative_to(directory))] = sha(rp)
            if '_train_' not in stem:
                differences.append(dict(house=h,variant=stem,old_error_m=before,
                                        corrected_error_m=summary['source_error_m']))
        fold['checks'] = checks(fold['metrics'])
        fold['all_checks_pass'] = all(fold['checks'].values())
    report['pass'] = sum(f['all_checks_pass'] for f in report['folds']) >= 2
    report['verdict'] = 'M1_SCREEN_GO_TO_FULL_CAUSAL_GATE' if report['pass'] else 'M1_CONTROLLED_SCREEN_NO_GO'
    return dict(original_result=str(directory.relative_to(ROOT)), original_report_sha256=sha(report_path),
                recomputed=report, differences=differences, raw_bindings=bindings,
                scope='localization metric recomputation only; no model replay or independent causality certification')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--results',type=Path,nargs='+',required=True)
    ap.add_argument('--output',type=Path,required=True)
    args = ap.parse_args()
    results = [audit(p.resolve()) for p in args.results]
    output = dict(contract='CSTAR_SCREEN_METRIC_AUDIT_V2',results=results,formal_gate_authority=False)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    for r in results:
        print(r['original_result'],r['recomputed']['verdict'])


if __name__ == '__main__': main()
