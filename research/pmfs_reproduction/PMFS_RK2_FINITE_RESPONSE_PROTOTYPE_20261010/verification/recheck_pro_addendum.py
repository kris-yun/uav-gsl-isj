"""Independent saved-prediction arithmetic; never imports a producer or queries physics."""
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent
HANDOFF = BASE / 'pro_handoff'
PARENT = BASE.parents[1] / 'outputs' / 'PMFS_RK1_PRO_REVIEW_BUNDLE_20261010'


def read_csv(p):
    with p.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def close(a, b, atol=5e-13):
    assert math.isclose(float(a), float(b), rel_tol=5e-12, abs_tol=atol), (a, b)


def mean(values):
    return math.fsum(values) / len(values)


def write_csv(name, rows):
    with (BASE / name).open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    manifest = json.loads((HANDOFF / 'SHA256_MANIFEST.json').read_text(encoding='utf-8'))
    assert len(manifest) == 12
    for name, expected in manifest.items():
        assert sha(HANDOFF / name) == expected, name
    prediction_path = PARENT / 'RK1_NEW' / 'PREDICTIONS_BLIND.csv'
    prediction_sha = sha(prediction_path)
    groups = defaultdict(list)
    for r in read_csv(prediction_path):
        if r['role'] == 'test' and int(r['membership_branch']) == 0:
            groups[(r['fold'], r['bank'])].append(r)
    assert len(groups) == 4
    mapping = json.loads((PARENT / 'RK1_NEW' / 'POST_FREEZE_GENERATOR_MAPPING.json').read_text(encoding='utf-8'))
    metrics = []
    directions = []
    tail_error_identity_max = 0.
    expected_counts = {'C7_1': 23, 'K2_1': 26, 'C7_0': 19, 'K2_0': 31}
    for (fold, bank), rows in sorted(groups.items()):
        assert len(rows) == 50
        errors = {}
        for arm in ('U', 'S', 'C_C7', 'C_K2', 'C_ORACLE'):
            col = 'C_' + mapping[bank] if arm == 'C_ORACLE' else arm
            e = [float(r[col + '_prediction_ppm']) - float(r['target_phi64_ppm']) for r in rows]
            bias = mean(e)
            mse = mean([v * v for v in e])
            centered = mean([(v - bias) ** 2 for v in e])
            close(mse, bias * bias + centered)
            for r, v in zip(rows, e):
                qerror = float(r[col + '_Q_prediction_ppm']) - float(r['target_Q64_ppm'])
                tail_error_identity_max = max(tail_error_identity_max, abs(v - qerror))
            errors[arm] = e
            metrics.append(dict(fold=fold, bank=bank, arm=arm, MSE_ppm2=mse,
                                bias_ppm=bias, squared_bias_ppm2=bias * bias,
                                centered_error_ppm2=centered, MAE_ppm=mean([abs(v) for v in e]),
                                event_disagreements=sum(int(r[col + '_event']) != int(r['native_F32_event']) for r in rows)))
        gains = [a * a - b * b for a, b in zip(errors['S'], errors['C_ORACLE'])]
        improve = sum(v > 1e-12 for v in gains)
        worsen = sum(v < -1e-12 for v in gains)
        assert improve == expected_counts[bank]
        directions.append(dict(fold=fold, bank=bank, exposures=50,
                               C_lower_squared_error_blocks=improve,
                               C_higher_squared_error_blocks=worsen,
                               median_S_minus_C_squared_error=mean(sorted(gains)[24:26]),
                               tail_alone_positive_blocks=sum(int(r['tail_alone_event']) for r in rows),
                               not_independent_trials=True))
    supplied = {(r['fold'], r['bank'], r['arm']): r for r in read_csv(HANDOFF / 'verification' / 'independent_test_metrics.csv')}
    for r in metrics:
        s = supplied[(r['fold'], r['bank'], r['arm'])]
        for k in ('MSE_ppm2', 'bias_ppm', 'squared_bias_ppm2', 'centered_error_ppm2', 'MAE_ppm'):
            close(r[k], s[k])
        assert r['event_disagreements'] == int(s['event_disagreements'])
    equal = {}
    for arm in ('U', 'S', 'C_ORACLE'):
        rr = [r for r in metrics if r['arm'] == arm]
        equal[arm] = {key: mean([r[key] for r in rr]) for key in ('MSE_ppm2', 'squared_bias_ppm2', 'centered_error_ppm2')}
    delta = {key: equal['S'][key] - equal['C_ORACLE'][key]
             for key in ('MSE_ppm2', 'squared_bias_ppm2', 'centered_error_ppm2')}
    close(delta['MSE_ppm2'], delta['squared_bias_ppm2'] + delta['centered_error_ppm2'])
    pro = json.loads((HANDOFF / 'verification' / 'INDEPENDENT_REVIEW_RESULT.json').read_text(encoding='utf-8'))
    for arm, r in equal.items():
        close(r['MSE_ppm2'], pro['equal_bank_MSE'][arm])
    for ours, theirs in [('MSE_ppm2', 'S_to_C_MSE_reduction'),
                        ('squared_bias_ppm2', 'S_to_C_squared_bias_reduction'),
                        ('centered_error_ppm2', 'S_to_C_centered_error_reduction')]:
        close(delta[ours], pro[theirs])
    close(tail_error_identity_max, pro['tail_error_identity_max_abs'])
    rmse_s = math.sqrt(equal['S']['MSE_ppm2'])
    rmse_c = math.sqrt(equal['C_ORACLE']['MSE_ppm2'])
    rmse_reduction = 1. - rmse_c / rmse_s
    assert abs(rmse_reduction * 100 - 20.32) < .005
    # Closed-form sanity case only. Not a fitted method and not new RK1 data.
    # Particle averaging and total-query least squares optimize different weights.
    n = [1., 10.]
    y = [10., 10.]
    h_pool = math.fsum(y) / math.fsum(n)
    h_query = math.fsum(a * b for a, b in zip(n, y)) / math.fsum(a * a for a in n)
    toy_pool_loss = math.fsum((a * h_pool - b) ** 2 for a, b in zip(n, y))
    toy_query_loss = math.fsum((a * h_query - b) ** 2 for a, b in zip(n, y))
    assert toy_query_loss < toy_pool_loss
    write_csv('PRO_ADDENDUM_RECOMPUTED_METRICS.csv', metrics)
    write_csv('PRO_ADDENDUM_RECOMPUTED_BLOCK_DIRECTIONS.csv', directions)
    result = dict(status='PASS_INDEPENDENT_SAVED_PREDICTION_RECOMPUTATION',
                  handoff_hash_count=len(manifest), prediction_SHA256=prediction_sha,
                  banks=4, main_test_exposures=200, mean_identity='MSE = per-bank bias squared + centered mean squared error',
                  equal_bank_metrics=equal, S_to_C_difference=delta,
                  RMSE_S_ppm=rmse_s, RMSE_C_ORACLE_ppm=rmse_c,
                  RMSE_reduction_fraction=rmse_reduction, block_directions=directions,
                  tail_error_identity_max_abs_ppm=tail_error_identity_max,
                  read_only_PRO_script_review=dict(no_import_or_execution=True, declared_boundary_correct=True,
                    actual_reads='196 immutable NPZ caches, 8 frozen kernels, saved predictions and source mapping',
                    actual_writes='fresh external output directory only',
                    new_phi_queries=0, new_physics=0, prototype_construction=0,
                    caveat='Reconstructs existing estimators; this is numerical replay, not prototype fitting search.'),
                  query_loss_math=dict(correct=True, scalar_h_query_formula='sum(w_t N_t Y_t) / sum(w_t N_t^2)',
                    pooled_h_formula='sum(w_t Y_t) / sum(w_t N_t)',
                    nonnegative_scalar_case='For nonnegative N,Y, unconstrained scalar optimum is nonnegative.',
                    multivariate_case='Nonnegative regularized least squares requires candidate-count design matrix including cross-cell covariation; it is not independent per-cell particle averaging.',
                    toy_counterexample=dict(N=n,Y=y,h_pool=h_pool,h_query=h_query,
                                             pool_loss=toy_pool_loss,query_loss=toy_query_loss),
                    scope='Toy algebra verification only; no new model or physics.'),
                  inference_prohibitions=['test hidden particle table', 'test Q classes or counts', 'test phi or exact tail',
                    'test generating-source identity or filename routing', 'test response signatures used to construct L',
                    'test observations used to select lambda/cutpoints/temperature'],
                  legitimate_forecast_inputs='Every candidate may read its own reference realization state; exact fallback may use only that candidate state and must be cost-accounted.',
                  no_new_model_or_phi=True)
    (BASE / 'PRO_ADDENDUM_INDEPENDENT_REVIEW.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    assert sha(prediction_path) == prediction_sha
    for name, expected in manifest.items():
        assert sha(HANDOFF / name) == expected
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
