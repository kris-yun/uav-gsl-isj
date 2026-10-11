#!/usr/bin/env python3
"""Read-only RK2-B arithmetic review; no optimizer, simulator, or producer import.

Input is an unpacked CORE. All output is written to a NEW external directory.
Counterfactuals are post-hoc diagnostics, NOT new localization performance.
"""
from __future__ import annotations
import argparse, csv, hashlib, json
from pathlib import Path
import numpy as np


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def load(p: Path):
    return json.loads(p.read_text(encoding='utf-8'))


def write_csv(p: Path, rows: list[dict]) -> None:
    if not rows: return
    with p.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def main(core: Path, output: Path) -> None:
    core, output = core.resolve(), output.resolve()
    if output == core or core in output.parents:
        raise ValueError('Output must be outside the frozen CORE')
    output.mkdir(parents=True, exist_ok=False)
    manifest = load(core/'MANIFEST_SHA256.json')
    failures = [str(p) for p, h in manifest.items() if sha(core/p) != h]
    if failures: raise ValueError(f'Frozen hashes differ: {failures[:5]}')
    with (core/'reference_transfer_error_attribution.csv').open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    selected = [r for r in rows if r['M']=='2' and r['method']=='L' and r['reference_role']=='extra_reference']
    if len(selected) != 300: raise ValueError('Expected 300 frozen M2 extra-reference queries')
    def col(k): return np.array([float(r[k]) for r in selected], dtype=np.float64)
    native, pred = col('F_ppm'), col('frozen_prediction_ppm')
    prior = pred-col('fit_coefficient_adjustment_ppm')
    empirical_zero = pred-col('known_decoder_ppm_from_zero_training_prior_states')
    diagnostic = []
    arms = {
        'frozen_L': (pred, 'original frozen forecast'),
        'prior_only': (prior, 'known-state h replaced by prior; no refit; post-hoc'),
        'empirical_zero_coefficient_reset': (empirical_zero, 'h=0 where TRAINING prior=0; not universally physical'),
        'exact_zero_query_oracle': (np.where(native==0, 0.0, pred), 'uses exact F zero label; NOT a deployable method'),
    }
    for name, (x, scope) in arms.items():
        diagnostic.append(dict(arm=name, queries=len(x), MSE=float(np.mean((x-native)**2)),
            MAE=float(np.mean(abs(x-native))),
            threshold_disagreements=int(np.count_nonzero((x.astype(np.float32)>np.float32(.1)) != (native.astype(np.float32)>np.float32(.1)))),
            strict_zero_false_positive=int(np.count_nonzero((native==0)&(x>float(np.float32(.1))))),
            scope=scope))
    write_csv(output/'readout_counterfactuals_descriptive.csv', diagnostic)
    with np.load(core/'M2/forecasts/F.npz', allow_pickle=False) as z:
        ref = z['reference_response_ppm'][:,:2].astype(np.float32)
    mismatches=[]
    for m in ['U_query','S_query','L']:
        with np.load(core/f'M2/forecasts/{m}.npz', allow_pickle=False) as z:
            a = z['reference_response_ppm'][:,:2].astype(np.float32)
        for c, r, t in np.argwhere((a>np.float32(.1))!=(ref>np.float32(.1))):
            mismatches.append(dict(method=m,candidate_index=int(c),reference_index=int(r),block=int(t),F_ppm=float(ref[c,r,t]),model_ppm=float(a[c,r,t])))
    write_csv(output/'primary_reference_event_differences.csv',mismatches)
    # Numerical toy: soft-prior nonnegative ridge need not preserve a known zero.
    lam=.01; h0=np.array([0.,.5]); d=.5/(2+lam); h=h0+d
    grad=2*((h.sum()-1)+lam*(h-h0))
    assert np.allclose(grad,0,atol=1e-14) and h[0]>.1
    toy={'scope':'constructed optimization counterexample, not measured PMFS or RK2 data',
         'X_train':[[1.,1.]],'y_train':[1.], 'h_prior':h0.tolist(),'lambda':lam,
         'h_fitted':h.tolist(),'train_prediction':float(h.sum()),
         'X_test':[[1.,0.]],'physical_test_y':0.,'test_prediction':float(h[0]),
         'KKT_gradient_max':float(np.max(abs(grad)))}
    (output/'soft_prior_counterexample.json').write_text(json.dumps(toy,ensure_ascii=False,indent=2),encoding='utf-8')
    summary={'status':'PASS_READONLY_DESCRIPTIVE_REVIEW','CORE_hashes_checked':len(manifest),
        'source_generation_calls':0,'model_fit_calls':0,'new_localization_runs':0,
        'counterfactuals_are_posthoc':True,'source_effect_claim':'NOT_TESTED',
        'reference_event_difference_count':len(mismatches)}
    (output/'REVIEW_SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('core',type=Path);p.add_argument('output',type=Path);a=p.parse_args();main(a.core,a.output)
