"""One frozen retrospective spatial pilot; not a native active-flight test."""
from __future__ import annotations
from pathlib import Path
import json,hashlib,itertools
import numpy as np
from scipy.special import logsumexp
from ..data import OCBDataset
from ..m1_opponent import SamplingContract,OpponentBank,calibrate_source_contrast
from .metrics import source_metrics


def _gaussian_fit(x):
    x=np.asarray(x,dtype=float)
    if x.ndim==1:x=x[:,None]
    mu=x.mean(0);c=np.atleast_2d(np.cov(x,rowvar=False))
    ridge=max(float(np.trace(c)/len(mu))*0.03,1e-18)
    c=c+np.eye(len(mu))*ridge
    return mu,c


def _ll(x,fit):
    mu,c=fit;x=np.atleast_1d(x)
    d=x-mu
    return float(-.5*(d@np.linalg.solve(c,d)+np.linalg.slogdet(c)[1]+len(d)*np.log(2*np.pi)))


def run_static_pilot(root,output):
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    if (out/'STATIC_PILOT_RESULT.json').exists():
        raise ValueError("pilot output exists: use a new directory; do not overwrite evidence")
    ds=OCBDataset(root)
    protocol={"schema":"v7-static-pilot-1","scientific_level":"retrospective synchronous spatial diagnostic",
      "full_Level2":False,"no_dynamic_claim":True,"truth_uses":"training labels / evaluator only",
      "train_worlds":[w.run_id for w in ds.split('train')],"dev_worlds":[w.run_id for w in ds.split('dev')],
      "units_of_independence":"whole plume realization, NOT ten snapshot frames",
      "action_selection":"one source-pair contrast maximum on TRAIN ONLY over 435 original probe pairs; freeze before dev scoring",
      "fixed_test":"all ten original snapshots, one identical frozen paired probe for every scoring method",
      "geometry":"two original 3D release locations differ in z as well as xy; source occupancy HOLD",
      "baselines":["mean_only_gaussian","raw_joint_gaussian","even_odd_gaussian_equivalent","opponent_joint_histogram"],
      "tuning":"none after dev scoring; histogram alpha=.5; Gaussian ridge .03 times trace/dimension",
      "claim_limit":"open discovery only; does not establish paper novelty or >10% improvement"}
    proto=json.dumps(protocol,ensure_ascii=False,indent=2)
    (out/'STATIC_PILOT_PROTOCOL.json').write_text(proto,encoding='utf8')
    source_ids=sorted({w.source_id for w in ds.worlds})
    train={sid:np.concatenate([w.pooled for w in ds.split('train') if w.source_id==sid],axis=0) for sid in source_ids}
    all_pairs=list(itertools.combinations(range(30),2))
    # Only training arrays enter this action choice. Dev is evaluated below.
    pair_scores=[]
    for pair in all_pairs:
        z=[np.log1p(train[sid][:,pair]) for sid in source_ids]
        fits=[_gaussian_fit(v) for v in z]
        delta=fits[0][0]-fits[1][0];cov=(fits[0][1]+fits[1][1])/2
        pair_scores.append(float(delta@np.linalg.solve(cov,delta)))
    choice=int(np.argmax(pair_scores));pair=all_pairs[choice]
    freeze={"probe_indices_zero_based":pair,"original_probe_ranks":[ds.probe_ids[i] for i in pair],
            "training_contrast":pair_scores[choice],"selection_truth_scope":"TRAIN_ONLY",
            "positions_xyz":ds.probe_positions_m[list(pair)].tolist(),"n_probe_pairs_compared":len(all_pairs),
            "protocol_sha256":hashlib.sha256(proto.encode()).hexdigest()}
    (out/'PAIR_SELECTION_FREEZE.json').write_text(json.dumps(freeze,ensure_ascii=False,indent=2),encoding='utf8')
    x=np.stack([train[sid][:,pair] for sid in source_ids])
    xy=np.array([next(w.source_xyz[:2] for w in ds.worlds if w.source_id==sid) for sid in source_ids])
    t=[float(ds.worlds[0].times_s[0])]
    model=calibrate_source_contrast(x[None,:,None,:,None,:],t,
                SamplingContract(False,provenance="native OCB same-frame 2x2 pooled pair; no temporal window"),
                xy,['fixed_pair'],source_ids,[1.],OpponentBank(),variant='secondary',max_filters=1,
                alpha=.5,smoothing_mode='legacy_per_cell',
                calibration_world_ids=[w.run_id for w in ds.split('train')])
    model.save(out/'static_model')
    raw_fits=[_gaussian_fit(np.log1p(v)) for v in x]
    mean_fits=[_gaussian_fit(np.log1p(v).mean(1)) for v in x]
    transform=np.array([[.5,.5],[.5,-.5]])
    eo_fits=[(transform@m,transform@c@transform.T) for m,c in raw_fits]
    rows=[];max_equivalence_error=0.
    for world in ds.split('dev'):
        truth=source_ids.index(world.source_id)
        for frame in range(10):
            raw=ds.query_probes(world,frame,freeze['original_probe_ranks']);z=np.log1p(raw)
            symbol=model.encode(0,raw[None,:],times=[world.times_s[frame]])
            likelihoods={
              'mean_only_gaussian':np.array([_ll(z.mean(),f) for f in mean_fits]),
              'raw_joint_gaussian':np.array([_ll(z,f) for f in raw_fits]),
              'even_odd_gaussian_equivalent':np.array([_ll(transform@z,f) for f in eo_fits]),
              'opponent_joint_histogram':np.log(model.channel.probabilities[0,:,0,symbol])}
            post={key:np.exp(ll-logsumexp(ll)) for key,ll in likelihoods.items()}
            max_equivalence_error=max(max_equivalence_error,float(np.max(np.abs(post['raw_joint_gaussian']-post['even_odd_gaussian_equivalent']))))
            for key,p in post.items():
                rows.append({"world":world.run_id,"frame":frame,"physical_time_s":float(world.times_s[frame]),
                             "method":key,"probability":p.tolist(),**source_metrics(p,truth,xy)})
    summaries=[]
    for key in protocol['baselines']:
        rr=[row for row in rows if row['method']==key]
        world_stats=[]
        for w in ds.split('dev'):
            ww=[row for row in rr if row['world']==w.run_id]
            world_stats.append({"world":w.run_id,"top1_fraction":float(np.mean([r['top1'] for r in ww])),
                 "map_error_m":float(np.mean([r['map_error_m'] for r in ww])),
                 "log_margin":float(np.mean([r['log_margin'] for r in ww])),
                 "wrong_high_confidence_count":int(sum(r['wrong_high_confidence'] for r in ww)),
                 "tie_count":int(sum(r['top1_tie'] for r in ww))})
        summaries.append({"method":key,"independent_dev_worlds":4,"snapshots":40,
            "top1_correct_snapshots":int(sum(r['top1'] for r in rr)),
            "top1_fraction_descriptive":float(np.mean([r['top1'] for r in rr])),
            "mean_map_error_m_descriptive":float(np.mean([r['map_error_m'] for r in rr])),
            "mean_log_margin":float(np.mean([r['log_margin'] for r in rr])),"by_world":world_stats})
    result={"status":"PASS_RETROSPECTIVE_PIPELINE_NOT_FULL_LEVEL2", "qualification":ds.audit(),
            "protocol":protocol,"freeze":freeze,"summary":summaries,
            "raw_joint_vs_even_odd_max_posterior_error":max_equivalence_error,
            "static_operator_equivalence":"expected: invertible linear re-expression supplies no new information",
            "temporal_filter_claim":"NOT_TESTED: 50s snapshots cannot test temporal MNM",
            "native_PMFS_head_to_head":"NOT_RUN", "all_rows":rows}
    (out/'STATIC_PILOT_RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    return result

