"""Frozen small controlled-data screen. Not a production gate producer.

Metadata/targets live outside the model-input constructor. Only measured causal
prefixes and geometry enter PICR. No raw field or evaluator future is queried.
"""
import argparse
import copy
import csv
import hashlib
import json
import math
from pathlib import Path
import random
import subprocess
import sys
import time

import numpy as np
import torch
import torch.nn.functional as F

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from m1_picr.model import PICRModel

CONFIG = HERE / 'CSTAR_CONTROLLED_SCREEN_CONFIG_20260907.json'
ASSETS = ROOT / 'evidence/cstar_controlled_assets_20260907_r2'
HORIZON_S = 60


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True)+'\n', encoding='utf-8')


def lines(path):
    return [json.loads(s) for s in Path(path).read_text().splitlines()]


def inputs(measured, end_s, context_only=False, null=False, geometry_bounds=None):
    # No metadata parameter and no future columns. EMA only uses earlier gas.
    ema, result = 0.0, []
    for r in measured:
        if r['t_sim_s'] > end_s:
            break
        gas = r['gas_ppm']
        ema = math.exp(-0.2/1.2)*ema+(1-math.exp(-0.2/1.2))*gas
        if geometry_bounds is None:
            pose_xy = (r['pose_xy'][0] / 10, r['pose_xy'][1] / 10)
        else:
            ox, oy, sx, sy = geometry_bounds
            pose_xy = ((r['pose_xy'][0] - ox) / sx,
                       (r['pose_xy'][1] - oy) / sy)
        result.append([0.0 if context_only or null else math.log1p(gas),
                       0.0 if context_only or null else ema,
                       *(0.0 if null else v for v in r['wind_uv']),
                       pose_xy[0], pose_xy[1], r['t_sim_s']/60, 1.0])
    assert len(result) == round(end_s*5) and len(result[0]) == 8
    return torch.tensor(result, dtype=torch.float32)


def load_data(geometry_normalized=False):
    rows = []
    for house_id in ('H01', 'H02', 'H03'):
        manifest = json.loads((ASSETS / 'manifests' / f'{house_id}.json').read_text())
        rows.extend(manifest['m1_episodes'])
    by = {}
    geometry_manifest = json.loads(
        (ROOT / 'evidence/cstar_environment_20260906/maps_v1/geometry_manifest.json').read_text())
    for row in rows:
        house = row['house']
        candidates_path = (ASSETS / row['candidate_domain_path']).resolve()
        assert sha(candidates_path) == row['candidate_domain_sha256']
        with candidates_path.open() as f:
            c = torch.tensor([[float(r['x']),float(r['y'])] for r in csv.DictReader(f)], dtype=torch.float32)
        path = ASSETS / row['history_trace_path']
        assert sha(path) == row['history_trace_sha256']
        source = row['source_xyz_m'][:2]
        if geometry_normalized:
            gm = geometry_manifest[house]
            ox, oy = map(float, gm['origin_xy_m'])
            sx = float(gm['expected_width_px']) * float(gm['resolution_m'])
            sy = float(gm['expected_height_px']) * float(gm['resolution_m'])
            c_model = torch.stack(((c[:, 0] - ox) / sx, (c[:, 1] - oy) / sy), dim=1)
            geometry_bounds = (ox, oy, sx, sy)
        else:
            c_model = c / 10
            geometry_bounds = None
        target = int(((c-torch.tensor(source))**2).sum(-1).argmin())
        by.setdefault(house, []).append({'row': row, 'measured': lines(path), 'candidates': c_model,
            'geometry_bounds': geometry_bounds, 'candidates_m': c,
            'source_xy': source, 'target': target, 'source_quantization_m': float(torch.linalg.vector_norm(c[target]-torch.tensor(source)))})
    for house, records in by.items():
        records.sort(key=lambda r: (r['row']['source_xyz_m'], r['row']['realization_id']))
        assert len(records) == 4
        assert records[0]['row']['source_xyz_m'] == records[1]['row']['source_xyz_m']
        assert records[2]['row']['source_xyz_m'] == records[3]['row']['source_xyz_m']
        assert records[0]['row']['source_xyz_m'] != records[2]['row']['source_xyz_m']
        assert all(torch.equal(r['candidates'], records[0]['candidates']) for r in records)
    return by


def tensors(records, end, variant='picr', null=False):
    H = torch.stack([inputs(r['measured'], end, variant == 'context_only', null,
                             r.get('geometry_bounds')) for r in records])
    C = torch.stack([r['candidates'] for r in records])
    V = torch.ones(H.shape[:2], dtype=torch.bool)
    targets = [r['target'] for r in records]
    if variant == 'label_permutation':
        targets = targets[2:]+targets[:2]
    return H, C, V, torch.tensor(targets, dtype=torch.long)


def train(by, held, variant, cfg, out):
    torch.manual_seed(cfg['seed'])
    rng = random.Random(cfg['seed'])
    model = PICRModel(**cfg['model'])
    opt = torch.optim.AdamW(model.parameters(), lr=cfg['learning_rate'], weight_decay=cfg['weight_decay'])
    houses = sorted(set(by)-{held})
    losses = []
    start = time.monotonic()
    for step in range(cfg['steps']):
        house, end = rng.choice(houses), rng.choice(list(range(4, HORIZON_S + 1, 4)))
        H,C,V,Y = tensors(by[house], end, variant)
        pred = model(H,C,V)
        ce = F.cross_entropy(pred.source_logits, Y)
        z = pred.source_representation
        inv = ((z[[0,2]]-z[[1,3]])**2).mean()
        diff = torch.linalg.vector_norm(z[[0,0,1,1]]-z[[2,3,2,3]], dim=-1)
        sep = F.relu(1-diff).square().mean()
        posterior_inv = torch.zeros((), dtype=ce.dtype)
        if cfg.get('paired_posterior_consistency', False):
            # Exact-source transport pairs are the same physical source under
            # different transport realizations.  Match the final posterior,
            # not just zS, so a nonlinear candidate head cannot reintroduce
            # transport-specific variation after the latent invariance loss.
            p = pred.source_posterior.clamp_min(1.0e-8)
            p_same = p[[0, 2]]
            p_pair = p[[1, 3]].clamp_min(1.0e-8)
            posterior_inv = 0.5 * (
                (p_same * (p_same.log() - p_pair.log())).sum(dim=-1)
                + (p_pair * (p_pair.log() - p_same.log())).sum(dim=-1)
            ).mean()
        loss = ce
        if variant != 'unconstrained':
            loss = loss + cfg['invariance_weight']*inv + cfg['separation_weight']*sep
            if cfg.get('paired_posterior_consistency', False):
                loss = loss + cfg['posterior_invariance_weight'] * posterior_inv
        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        opt.step()
        losses.append({'step':step+1, 'house':house, 'prefix_s':end, 'ce':float(ce.detach()),
                       'invariance':float(inv.detach()), 'separation_penalty':float(sep.detach()),
                       'posterior_invariance':float(posterior_inv.detach())})
        if (step+1) % 50 == 0:
            print(json.dumps({'stage':'M1_TRAIN', 'held':held, 'variant':variant, 'step':step+1,
                              'seconds':round(time.monotonic()-start,2), 'ce':losses[-1]['ce']}),flush=True)
    checkpoint = out / held / (variant+'.pt')
    checkpoint.parent.mkdir(parents=True,exist_ok=True)
    torch.save({'state_dict':model.state_dict(), 'config_sha256':sha(CONFIG), 'heldout_house':held,
                'effective_config_sha256':sha(out/'FROZEN_CONFIG.json'),
                'train_parent_ids':[r['row']['realization_id'] for h in houses for r in by[h]],
                'variant':variant, 'steps':cfg['steps']}, checkpoint)
    dump(out / held / (variant+'_training.json'), losses)
    return model.eval(), checkpoint


@torch.no_grad()
def evaluate(model, records, variant, out, stem):
    result = []
    posts, representations = [], []
    for end in range(4, HORIZON_S + 1, 4):
        H,C,V,Y = tensors(records, end, variant if variant == 'context_only' else 'picr')
        normal = model(H,C,V)
        hook = None
        if variant == 'zs_zero':
            hook = model.source_proj.register_forward_hook(lambda mod, inp, value: torch.zeros_like(value))
        elif variant == 'zs_swap':
            hook = model.source_proj.register_forward_hook(lambda mod, inp, value: value[[2,3,0,1]])
        if hook is not None:
            pred = model(H,C,V)
            hook.remove()
        elif variant == 'uninformative':
            H,C,V,Y = tensors(records,end,null=True)
            pred = model(H,C,V)
        else:
            pred = normal
        p = pred.source_posterior
        z = pred.source_representation
        same = torch.linalg.vector_norm(z[[0,2]]-z[[1,3]], dim=-1).mean()
        different = torch.linalg.vector_norm(z[[0,0,1,1]]-z[[2,3,2,3]], dim=-1).mean()
        for i,record in enumerate(records):
            # Score against physical coordinates, independent of model units.
            point = record['candidates_m'][int(p[i].argmax())]
            error = float(torch.linalg.vector_norm(point-torch.tensor(record['source_xy'])))
            prob = float(p[i,Y[i]])
            entropy = float(-(p[i]*p[i].clamp_min(1e-30).log()).sum()/math.log(p.shape[1]))
            nll = float(-F.log_softmax(pred.source_logits[i],dim=-1)[Y[i]])
            result.append({'rid':record['row']['realization_id'], 'prefix_s':end, 'nll':nll,
                'source_error_m':error, 'true_cell_mass':prob, 'normalized_entropy':entropy,
                'abstain':bool(pred.abstain[i]), 'same_z':float(same), 'different_z':float(different),
                'same_different_ratio':float(same/different.clamp_min(1e-12)),
                'source_quantization_m':record['source_quantization_m']})
        posts.append(p.cpu().numpy())
        representations.append(z.cpu().numpy())
    path = out / (stem+'_predictions.npz')
    np.savez_compressed(path, posterior=np.stack(posts), z_source=np.stack(representations))
    dump(out / (stem+'_rows.json'), result)
    summary = {k:sum(r[k] for r in result)/len(result) for k in
               ('nll','source_error_m','normalized_entropy','same_z','different_z','same_different_ratio')}
    summary.update({'rows':len(result), 'min_normalized_entropy':min(r['normalized_entropy'] for r in result),
                    'abstain_count':sum(r['abstain'] for r in result), 'predictions_sha256':sha(path)})
    return summary


def m1_screen(by, cfg, out):
    folds = []
    for held in sorted(by):
        summaries = {}
        for variant in cfg['variants']:
            model, path = train(by, held, variant, cfg, out)
            metrics = evaluate(model, by[held], variant, out / held, variant)
            metrics['checkpoint_sha256'] = sha(path)
            summaries[variant] = metrics
            if variant == 'picr':
                for control in ('zs_zero','zs_swap','uninformative'):
                    summaries[control] = evaluate(model,by[held],control,out / held,control)
            # Also expose train fit. It cannot choose steps/checkpoints or the gate.
            summaries[variant]['train_metrics'] = {h:evaluate(model,by[h],variant,out / held,variant+'_train_'+h)
                                                   for h in sorted(by) if h != held}
            print(json.dumps({'stage':'M1_EVALUATED','held':held,'variant':variant,
                              'nll':metrics['nll'],'error_m':metrics['source_error_m']}),flush=True)
        c,b = summaries['picr'], summaries['unconstrained']
        tests = {'proper_score_better': c['nll'] < b['nll'], 'localization_better':c['source_error_m'] < b['source_error_m'],
            'invariance_better':c['same_z'] < b['same_z'],
            'relative_invariance_better':c['same_different_ratio'] < b['same_different_ratio'],
            'separation_not_collapsed':c['different_z'] >= 0.9*b['different_z'],
            'context_only_beaten':c['nll'] < summaries['context_only']['nll'] and c['source_error_m'] < summaries['context_only']['source_error_m'],
            'label_permutation_destroyed_gain':summaries['label_permutation']['nll'] >= b['nll'] and summaries['label_permutation']['source_error_m'] >= b['source_error_m'],
            'zs_zero_destroys_gain':summaries['zs_zero']['nll'] > c['nll'],
            'zs_swap_destroys_gain':summaries['zs_swap']['nll'] > c['nll'] and summaries['zs_swap']['source_error_m'] > c['source_error_m'],
            'uninformative_uncertainty':summaries['uninformative']['min_normalized_entropy'] >= .95
                                      or summaries['uninformative']['abstain_count'] == 60}
        fold = {'heldout_house':held,'metrics':summaries,'checks':tests,'all_checks_pass':all(tests.values())}
        folds.append(fold)
        dump(out / held / 'FOLD_RESULT.json',fold)
    passed = sum(f['all_checks_pass'] for f in folds) >= 2
    report = {'contract':'CSTAR_M1_BOUNDED_CONTROLLED_SCREEN_V1','pass':passed,
        'formal_gate_authority':False,'config_sha256':sha(CONFIG),'folds':folds,
        'verdict':'M1_SCREEN_GO_TO_FULL_CAUSAL_GATE' if passed else 'M1_CONTROLLED_SCREEN_NO_GO',
        'limitations':['development LOHO, not virgin confirmation','fixed small budget, not asymptotic impossibility',
                       'labels are nearest navigation-height XY cell; exact XYZ only pairs physical sources',
                       'release random draws not matched; source-group transport settings can remain confounded',
                       'these checkpoints do not authorize closed loop']}
    dump(out / 'M1_SCREEN.json',report)
    return report


def m2_baselines(out):
    probe = json.loads((ASSETS / 'manifests' / 'H01.json').read_text())
    if 'm2_route_cases' not in probe:
        report = {
            'contract': 'CSTAR_M2_CAUSAL_PERSISTENCE_BASELINE_SCREEN_V1',
            'status': 'NOT_RUN', 'formal_gate_authority': False,
            'reason': 'current-runtime asset bundle contains M1 crossed source/transport cases only; no route-outcome cases were supplied',
            'interpretation': 'M2 is intentionally not inferred from an M1 source screen'
        }
        dump(out / 'M2_BASELINE_SCREEN.json', report)
        print(json.dumps({'stage': 'M2_BASELINES_SKIPPED', 'reason': report['reason']}), flush=True)
        return
    folds = []
    for held in ['H01','H02','H03']:
        manifest = json.loads((ASSETS / 'manifests' / (held+'.json')).read_text())
        episodes = {r['episode_id']:lines(ASSETS / r['history_trace_path']) for r in manifest['m1_episodes']}
        rows = []
        for r in manifest['m2_route_cases']:
            history = [f for f in episodes[r['episode_id']] if f['t_sim_s'] <= r['decision_time_s']]
            future = lines(ASSETS / r['outcome_trace_path'])
            target = next((i for i,f in enumerate(future) if f['gas_ppm'] > .1),20)
            rows.append({'decision_id':r['decision_id'],'split':r['split'],
                         'current_hit':int(history[-1]['gas_ppm']>.1),'target':target})
        conditional = np.ones((2,21))/21
        unconditional = np.ones(21)/21
        for r in rows:
            if r['split'] == 'train':
                conditional[r['current_hit'],r['target']] += 1
                unconditional[r['target']] += 1
        conditional /= conditional.sum(axis=1,keepdims=True)
        unconditional /= unconditional.sum()
        predictions = []
        for r in rows:
            if r['split'] != 'heldout': continue
            p = conditional[r['current_hit']]
            y = np.eye(21)[r['target']]
            predictions.append({**r,'persistence_law':p.tolist(),'unconditional_law':unconditional.tolist(),
                'nll':-math.log(p[r['target']]),'brier':float(((p-y)**2).sum()),
                'unconditional_nll':-math.log(unconditional[r['target']]),
                'unconditional_brier':float(((unconditional-y)**2).sum()),
                'exact':int(np.argmax(p)==r['target']), 'committor':float(1-p[-1]), 'observed_hit':int(r['target']<20)})
        metrics = {k:float(np.mean([r[k] for r in predictions])) for k in
                   ('nll','brier','unconditional_nll','unconditional_brier','exact','committor','observed_hit')}
        folds.append({'heldout_house':held,'metrics':metrics, 'train_conditional_law':conditional.tolist()})
        dump(out / ('M2_'+held+'_raw.json'), predictions)
    report = {'contract':'CSTAR_M2_CAUSAL_PERSISTENCE_BASELINE_SCREEN_V1','folds':folds,
        'inputs':['current measured gas threshold indicator'], 'route_or_source_inputs':False,
        'fit':'training parents only, conditional categorical histogram; total Dirichlet pseudocount1',
        'formal_gate_authority':False,'learned_cpo_trained':False,
        'missing_for_formal_gate':['causal_plume_fopdt deployable prior binding','verified_physics_prior deployable prior binding','learned CPO comparison'],
        'interpretation':'strong null; high label accuracy without source or route is not evidence of intervention skill'}
    dump(out / 'M2_BASELINE_SCREEN.json',report)
    print(json.dumps({'stage':'M2_BASELINES_COMPLETE','folds':folds}),flush=True)


def main():
    global ASSETS, HORIZON_S
    ap = argparse.ArgumentParser()
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--assets', type=Path, default=ASSETS,
                    help='controlled asset bundle; default is the frozen bundle')
    ap.add_argument('--horizon-s', type=int, default=60,
                    help='causal history horizon; must match the asset bundle')
    ap.add_argument('--selftest',action='store_true')
    ap.add_argument('--geometry-normalized', action='store_true',
                    help='normalize pose/candidate coordinates by the frozen map extent')
    ap.add_argument('--coordinate-equivariant', action='store_true',
                    help='use the fixed radial source-coordinate scorer')
    ap.add_argument('--paired-posterior-consistency', action='store_true',
                    help='match posteriors for exact-source transport pairs')
    ap.add_argument('--event-weighted-source-pool', action='store_true',
                    help='weight source pooling by causal measured plume events')
    ap.add_argument('--radial-source-score', action='store_true',
                    help='retain radial curvature with zero-zS precision gating')
    ap.add_argument('--strict-source-stream', action='store_true',
                    help='form zS from measured response plus pose only; exclude wind/time nuisance')
    args = ap.parse_args()
    ASSETS = args.assets.resolve()
    HORIZON_S = args.horizon_s
    if HORIZON_S < 4 or HORIZON_S % 4:
        ap.error('--horizon-s must be a positive multiple of 4')
    if args.coordinate_equivariant and not args.geometry_normalized:
        ap.error('--coordinate-equivariant requires --geometry-normalized')
    if args.radial_source_score and not args.coordinate_equivariant:
        ap.error('--radial-source-score requires --coordinate-equivariant')
    cfg = json.loads(CONFIG.read_text())
    if args.coordinate_equivariant:
        cfg['model'] = dict(cfg['model'])
        cfg['model']['coordinate_equivariant'] = True
        cfg['model']['coordinate_sigma'] = 0.15
    if args.paired_posterior_consistency:
        cfg['paired_posterior_consistency'] = True
        cfg['posterior_invariance_weight'] = 0.25
    if args.event_weighted_source_pool:
        cfg['model'] = dict(cfg['model'])
        cfg['model']['event_weighted_source_pool'] = True
    if args.radial_source_score:
        cfg['model']['radial_source_score'] = True
    if args.strict_source_stream:
        cfg['model'] = dict(cfg['model'])
        cfg['model']['strict_source_stream'] = True
    if args.geometry_normalized:
        cfg['feature_schema'] = 'causal measured gas/EMA/wind/time; pose XY normalized by frozen map extent'
        cfg['candidate_schema'] = 'free-cell XY normalized by frozen map extent; metrics use physical XY'
        cfg['normalization'] = 'map origin and extent only; no heldout fitted moments'
    torch.set_num_threads(1)
    if args.selftest:
        measured = [{'t_sim_s':(i+1)*.2,'gas_ppm':i*.01,'wind_uv':[.1,.2],'pose_xy':[1.,2.]} for i in range(300)]
        h = inputs(measured,4)
        changed = copy.deepcopy(measured)
        for r in changed[20:]: r.update(gas_ppm=999,wind_uv=[-100,100],pose_xy=[100,100])
        assert torch.equal(h, inputs(changed,4))
        assert torch.all(inputs(measured,4,context_only=True)[:,:2] == 0)
        by = load_data(args.geometry_normalized)
        for records in by.values():
            H,C,V,Y = tensors(records,4)
            assert torch.equal(tensors(records,4,'label_permutation')[-1],Y[[2,3,0,1]])
            model = PICRModel(**cfg['model'])
            pred = model(H,C,V)
            hook = model.source_proj.register_forward_hook(lambda m,i,v: torch.zeros_like(v))
            zero = model(H,C,V)
            hook.remove()
            assert torch.allclose(zero.source_posterior,torch.full_like(zero.source_posterior,1/C.shape[1]),atol=1e-7)
            (F.cross_entropy(pred.source_logits,Y)).backward()
        print('CSTAR_CONTROLLED_SCREEN_INPUT_PAIR_DESTRUCTIVE_SELFTEST=PASS')
        return
    args.out.mkdir(parents=True,exist_ok=False)
    dump(args.out / 'FROZEN_CONFIG.json',cfg)
    dump(args.out / 'RUN_START.json', {'git_sha':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'torch':torch.__version__,'python':sys.version,'config_sha256':sha(CONFIG),
        'geometry_normalized': bool(args.geometry_normalized),
        'coordinate_equivariant': bool(args.coordinate_equivariant),
        'paired_posterior_consistency': bool(args.paired_posterior_consistency),
        'event_weighted_source_pool': bool(args.event_weighted_source_pool),
        'radial_source_score': bool(args.radial_source_score),
        'strict_source_stream': bool(args.strict_source_stream),
        'effective_config_sha256': sha(args.out / 'FROZEN_CONFIG.json'),
        'metric_coordinate_contract': 'raw_candidate_xy_m_v2',
        'code_sha256': {str(p.relative_to(ROOT)):sha(p) for p in (Path(__file__), HERE/'m1_picr/model.py')},
        'asset_manifests':{h:sha(ASSETS/'manifests'/(h+'.json')) for h in ['H01','H02','H03']},
        'no_online_or_raw_queries':True})
    m2_baselines(args.out)
    report = m1_screen(load_data(args.geometry_normalized),cfg,args.out)
    report['geometry_normalized'] = bool(args.geometry_normalized)
    report['effective_config_sha256'] = sha(args.out/'FROZEN_CONFIG.json')
    report['metric_coordinate_contract'] = 'raw_candidate_xy_m_v2'
    dump(args.out / 'M1_SCREEN.json', report)
    print(report['verdict'],flush=True)


if __name__ == '__main__': main()
