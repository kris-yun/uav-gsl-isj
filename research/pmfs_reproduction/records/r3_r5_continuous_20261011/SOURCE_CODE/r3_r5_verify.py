"""Standalone independent bundle verifier. No imports from production or evaluator."""
import argparse,csv,hashlib,json,pathlib
import numpy as np
from scipy.special import logsumexp
from scipy.stats import norm
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main(root):
    root=pathlib.Path(root);manifest=load(root/'MANIFEST_SHA256.json');bad=[]
    for path,digest in manifest.items():
        p=root/path
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:bad.append(path)
    assert not bad,bad
    tri=load(root/'R3_TRIAGE_RECOMPUTED.json');expected=load(root/'authorization/R2_FROZEN_READONLY_TRIAGE.json');assert tri==expected
    r3=root/'audit_R3';atomic=list(csv.DictReader((r3/'ATOMIC_SOURCE_CATALOG.csv').open(encoding='utf-8-sig')));cells=np.array([int(a['cell']) for a in atomic]);rxy=np.array([[float(a['x']),float(a['y'])] for a in atomic]);rdist=np.linalg.norm(rxy[:,None]-rxy[None,:],axis=2);rpost=np.load(r3/'FULL_SOURCE_POSTERIORS.npz');rtruth=load(r3/'FUTURE_TRUTH.json')
    risks=list(csv.DictReader((root/'R3_DECISION_RISK.csv').open(encoding='utf-8')));riskmap={(r['oid'],r['method'],r['decision']):r for r in risks};r3max=0.
    for oid,t in rtruth.items():
        for method in ['P3-O0','P3-O1']:
            p=rpost[f'{oid}__R01__{method}__50_posterior'][cells];p=p/p.sum();act=rxy[np.argmin(rdist@p)];error=np.linalg.norm(act-np.array(t['source_xyz'][:2]));r3max=max(r3max,abs(error-float(riskmap[(oid,method,'EUCLIDEAN_FEASIBLE_MEDOID')]['error_m'])))
    assert r3max<1e-12
    d=load(root/'R4_PREREGISTRATION_REV1.json');xy=np.array([[s['x_m'],s['y_m']] for s in d['inference']['source_support']]);dist=np.linalg.norm(xy[:,None]-xy[None,:],axis=2)
    seeds=[]
    for t in d['tasks']:
        seeds.extend([t[x] for x in ['release_seed','wind_truth_seed','gas_sensor_seed','wind_sensor_seed']]);seeds.extend([t['inference_seed']+i for i in [20,21,22]])
    assert len(seeds)==252==len(set(seeds))
    with (root/'R4_B0_B1_B2_SOURCE_OUTPUT.csv').open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    assert len(rows)==432
    rowmap={(r['task_id'],r['method'],int(r['events'])):r for r in rows};posmax=0.;probmax=0.;nllmax=0.;count=0
    for task in d['tasks']:
        for method in d['inference']['methods']:
            f=root/f"audit_slim/{task['task_id']}__{method}.npz";a=np.load(f);ps=a['source_posterior'];log=a['source_log_score'];truth=int(task['true_source_id'])
            assert ps.shape==(50,25) and np.min(ps)>=0 and np.allclose(ps.sum(axis=1),1,atol=1e-12)
            assert np.max(abs(np.exp(log-logsumexp(log,axis=1)[:,None])-ps))<1e-12
            for n in [20,35,50]:
                p=ps[n-1];r=rowmap[(task['task_id'],method,n)];decision=np.argmin(dist@p);error=dist[decision,truth];posmax=max(posmax,abs(error-float(r['main_distance_m'])));assert int(r['action_source_id'])==decision
                nn=float(logsumexp(log[n-1])-log[n-1,truth]);nllmax=max(nllmax,abs(nn-float(r['source_NLL'])));probmax=max(probmax,abs(p[truth]-float(r['true_source_mass'])));count+=1
    full=0;likemax=0.;mixmax=0.
    for f in sorted((root/'audit_full').glob('*.npz')):
        task,method=f.stem.split('__');a=np.load(f);obs=np.load(root/f'audit_observations/{task}.npz')
        for e,y in enumerate(obs['y']):
            mu=a['forecast_particle_means'][e];w=a['forecast_mixture_weights'][e]
            loglike=norm.logcdf(0,loc=mu,scale=.02) if y==0 else norm.logpdf(y,loc=mu,scale=.02)
            logw=np.full(w.shape,-np.inf);np.log(w,out=logw,where=w>0);ls=logsumexp(logw+loglike,axis=1);total=logsumexp(ls);posterior=np.exp(ls-total)
            likemax=max(likemax,abs(total-float(a['gas_prequential_log_evidence'][e])));mixmax=max(mixmax,float(np.max(abs(posterior-a['source_posterior'][e]))))
        full+=1
    assert posmax<1e-12 and probmax<1e-12 and nllmax<1e-11
    assert likemax<1e-10 and mixmax<1e-10,(likemax,mixmax)
    result={'status':'PASS','manifest_members':len(manifest),'R3_12_posterior_risk_decisions_verified':True,'R3_max_risk_error_difference_m':r3max,'source_endpoint_rows_verified':count,'full_prequential_sample_files':full,'sample_events_checked':full*50,'max_coordinate_error_difference_m':posmax,'max_source_NLL_difference':nllmax,'max_prequential_log_evidence_difference':likemax,'max_post_update_posterior_difference':mixmax,'unique_rng_streams':252,'no_production_imports':True,'limitations':'Finite PF convergence, real physics, 3D/lakeshore and native navigation not established.'}
    print(json.dumps(result,ensure_ascii=False,indent=2));return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',nargs='?',default=str(pathlib.Path(__file__).resolve().parent));args=p.parse_args();main(args.root)
