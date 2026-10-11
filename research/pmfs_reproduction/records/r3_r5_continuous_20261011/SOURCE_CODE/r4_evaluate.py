"""Independent evaluation: never imports transport, generator or inference functions."""
import csv,json,pathlib,hashlib,time
import numpy as np
from scipy.special import ndtr,logsumexp
BASE=pathlib.Path(__file__).resolve().parents[1];OUT=BASE/'outputs/PMFS_R3_R5_CONTINUOUS_20261011'
def write_csv(file,rows):
    with (OUT/file).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def A(x,sd):return 2*sd*np.exp(-.5*(x/sd)**2)/np.sqrt(2*np.pi)+x*(2*ndtr(x/sd)-1)
def crps(y,mu,w):
    m=mu.ravel();v=w.ravel();v=v/v.sum()
    # Proper Gaussian mixture CRPS for raw (uncensored) scalar; kept evaluation-only.
    return float(v@A(y-m,.02)-.5*(v@A(m[:,None]-m[None,:],np.sqrt(2)*.02)@v))
def metrics(split):
    d=json.loads((OUT/'R4_PREREGISTRATION_REV1.json').read_text(encoding='utf-8'));xy=np.array([[s['x_m'],s['y_m']] for s in d['inference']['source_support']]);dist=np.linalg.norm(xy[:,None]-xy[None,:],axis=2)
    rows=[]
    for task in d['tasks']:
        if task['split']!=split:continue
        truth=np.load(OUT/f"raw/evaluation_only/{task['task_id']}.npz");ts=int(truth['true_source_id']);rawsensor=truth['raw_sensor'];obs=np.load(OUT/f"raw/observations/{task['task_id']}.npz")
        for method in d['inference']['methods']:
            f=OUT/f"raw/inference/{task['task_id']}__{method}.npz";a=np.load(f);meta=json.loads(f.with_suffix('.json').read_text(encoding='utf-8'))
            assert hashlib.sha256(f.read_bytes()).hexdigest()==meta['file_sha256'];pall=a['source_posterior'];l=a['source_log_score'];assert np.allclose(pall.sum(axis=1),1,atol=1e-12)
            forecasts=a['forecast_particle_means'];pw=a['forecast_mixture_weights'];cr=np.array([crps(y,m,w) for y,m,w in zip(rawsensor,forecasts,pw)])
            predmean=(forecasts*pw).sum(axis=(1,2));winderr=np.sqrt(np.mean((a['wind_estimate']-truth['wind'])**2))
            for n in [20,35,50]:
                p=pall[n-1];risk=dist@p;medoid=int(np.argmin(risk));order=np.argsort(-p,kind='stable');cum=np.cumsum(p[order]);hp=order[:np.searchsorted(cum,.9)+1];mp=int(np.argmax(p));mean=p@xy;top=order[:2];toppos=(p[top]/p[top].sum())@xy[top];variance=np.sum(p*np.sum((xy-mean)**2,axis=1));onehot=np.eye(25)[ts]
                rows.append({'task_id':task['task_id'],'split':split,'true_source_id':ts,'regime':task['regime'],'realization':task['realization'],'method':method,'events':n,'main_distance_m':dist[medoid,ts],'action_source_id':medoid,'posterior_expected_distance_m':risk[medoid],'MAP_distance_m':dist[mp,ts],'mean_distance_m':np.linalg.norm(mean-xy[ts]),'Top5_aux_distance_m':np.linalg.norm(toppos-xy[ts]),'Top5_scope':'2/25 candidates; not native PMFS','source_NLL':float(logsumexp(l[n-1])-l[n-1,ts]),'source_Brier':np.sum((p-onehot)**2),'source_energy_score_m':p@dist[:,ts]-.5*p@dist@p,'coverage90':int(ts in hp),'coverage90_set_size':len(hp),'variance_m2':variance,'true_source_mass':p[ts],'true1m_mass':p[dist[:,ts]<=1.].sum(),'positive_detections':int((obs['y'][:n]>.05).sum()),'censored_zero_events':int((obs['y'][:n]==0).sum()),'gas_prequential_mean_NLL':-np.mean(a['gas_prequential_log_evidence'][:n]),'raw_predictive_CRPS':cr[:n].mean(),'raw_predictive_RMSE':np.sqrt(np.mean((predmean[:n]-rawsensor[:n])**2)),'wind_RMSE_m_s':winderr,'method_wall_s':meta['wall_s'],'wind_boundary_clips':meta['wind_boundary_clips'],'source_prior':'uniform atomic','evidence_level':'controlled matched-FV numerical task'})
    return rows
def evaluate(split):
    rows=metrics(split);write_csv('R4_'+split.upper()+'_METRICS.csv',rows)
    summary={m:{k:float(np.mean([r[k] for r in rows if r['method']==m and r['events']==50])) for k in ['main_distance_m','MAP_distance_m','mean_distance_m','source_NLL','source_Brier','coverage90','raw_predictive_CRPS','gas_prequential_mean_NLL','wind_RMSE_m_s','method_wall_s']} for m in ['B0_FIXED','B1_TRANSIENT','B2_JOINT_PF','WIND_ORACLE']}
    (OUT/f'R4_{split.upper()}_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    if split=='development':
        best=min(['B1_TRANSIENT','B2_JOINT_PF'],key=lambda m:summary[m]['main_distance_m'])
        selection={'selected_ordinary_method':best,'reason':'preregistered minimum development mean Euclidean source distance, ties B1 first','parameters_fitted':False,'test_metrics_read':False,'development_summary':summary}
        (OUT/'R4_ORDINARY_SELECTION_FROZEN.json').write_text(json.dumps(selection,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'evaluated':split,'summary':summary},ensure_ascii=False),flush=True)
if __name__=='__main__':
    import sys
    evaluate(sys.argv[1])
