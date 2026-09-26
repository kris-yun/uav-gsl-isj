"""Independent histogram/table/heldout-metric recomputation, no fitting."""
from pathlib import Path
import csv,json
import numpy as np

root=Path(__file__).resolve().parents[2];e=root/'evidence/pmfs_shared_field_v0'
c=json.loads((e/'NUMERICAL_CONTRACT.json').read_text());result=json.loads((e/'DEVELOPMENT_RESULT.json').read_text())
tables=np.load(e/'PROBABILITY_MAP_TABLES.npz');coded=np.load(e/'OBSERVATION_CODES.npz')
metrics=np.load(e/'TARGET_METRICS.npz');saved=metrics['values'];names=metrics['model_names'].tolist()
folds=json.loads((e/'FOLD_MODELS.json').read_text());fits=json.loads((e/'FIT_RECORDS.json').read_text())
panel=list(csv.DictReader((e/'central_panel.tsv').open(),delimiter='\t'))
xyz=np.asarray([[float(v[k]) for k in ('x_m','y_m','z_m')] for v in panel]);d=np.linalg.norm(xyz[:,None]-xyz[None,:],axis=-1)
raw=np.concatenate([np.load(v['path'])[:,:,[0,9],:].transpose(0,1,3,2) for v in c['inputs']],axis=2)
max_table_error=max_metric_error=0.;selection_verified=True
recomputed=np.empty_like(saved)
for fold,model in enumerate(folds):
    codes=coded[f'fold_{fold}_all_codes'];refs=coded[f'fold_{fold}_refs'];held=coded[f'fold_{fold}_held']
    positive=raw[:,refs][raw[:,refs]>0];thresholds=np.unique(np.quantile(positive,[1/3,2/3])).tolist() if positive.size else []
    assert thresholds==model['alphabet']['positive_thresholds']
    B=model['alphabet']['bins'];K=B*B
    bins=np.where(raw==0,0,1+np.searchsorted(thresholds,raw,side='left')) if B>1 else np.zeros_like(raw,dtype=int)
    assert np.array_equal(codes,bins[...,0]*B+bins[...,1])
    counts=(codes[:,refs,:,None]==np.arange(K)).sum(axis=1)
    likelihood=(counts+1/K)/(len(refs)+1)
    nominal=likelihood/likelihood.sum(axis=0,keepdims=True)
    max_table_error=max(max_table_error,float(np.max(abs(nominal-tables[f'fold_{fold}_NOMINAL']))))
    # Verify hyperparameter decisions solely from stored reference-CV scores.
    for field,chosen in [('selection_shared','shared_rho'),('selection_independent','independent_rho')]:
        means={float(k):float(np.mean(v)) for k,v in model[field].items()};best=max(means.values())
        pick=min(k for k,v in means.items() if best-v<=1e-12)
        assert pick==model[chosen]
    means={float(k):float(np.mean(v)) for k,v in model['selection_temperature'].items()};best=max(means.values())
    pick=min((k for k,v in means.items() if best-v<=1e-12),key=lambda t:(abs(t-1),t))
    assert pick==model['temperature']
    assert model['shared_rho']==0 and model['independent_rho']==0 and model['temperature']==1
    perms=coded[f'fold_{fold}_shuffle_permutation']
    for s in range(168):
        for m in range(60):assert np.array_equal(np.sort(codes[s,refs,m]),np.sort(codes[s,refs,m][perms[s,m]]))
    for mi,name in enumerate(names):
        Q=tables[f'fold_{fold}_{name}'];assert np.isfinite(Q).all() and (Q>0).all()
        assert np.allclose(Q.sum(0),1,atol=1e-12)
        # Selected rho0/T1 imply same table, independently check this identity.
        max_table_error=max(max_table_error,float(np.max(abs(Q-nominal))))
        for m in range(60):
            for r in held:
                prob=Q[:,m,codes[:,r,m]].T
                truth=prob[np.arange(168),np.arange(168)]
                rank=1+(prob>truth[:,None]).sum(1)+((prob==truth[:,None])&(np.arange(168)[None,:]<np.arange(168)[:,None])).sum(1)
                mapid=np.argmax(prob,axis=1)
                v=np.column_stack([np.log2(truth),(prob*prob).sum(1)-2*truth+1,rank,d[np.arange(168),mapid],
                    (prob*d).sum(1),(prob*(d<=.5)).sum(1),(prob*(d<=1)).sum(1)])
                recomputed[mi,:,r,m]=v
                max_metric_error=max(max_metric_error,float(np.max(abs(v-saved[mi,:,r,m]))))
assert max_table_error<1e-13 and max_metric_error<1e-12
assert all(v['gap']<=2e-6 and v['constraint_violation']<=2e-8 and v['max_protocol_gap']<=2e-6 for v in fits)
rng=np.random.default_rng(2026092607);ix=rng.integers(0,168,(10000,168))
for comp in result['comparisons_shared_minus_control']:
    control=names.index(comp['control']);delta=recomputed[3,...,0]-recomputed[control,...,0]
    source=delta.mean((1,2));interval=np.quantile(source[ix].mean(1),[.025,.975])
    assert abs(source.mean()-comp['mean_gain_bits'])<1e-14
    assert np.allclose(interval,comp['source_panel_95pct_sensitivity'],atol=1e-14)
assert result['DEVELOPMENT_DECISION']=='DEVELOPMENT_STOP_NO_INCREMENT_BEYOND_CONTROLS'
out={'status':'INDEPENDENT_RECOMPUTATION_PASS','fit_count':len(fits),'probability_table_max_error':max_table_error,
     'heldout_metric_max_error':max_metric_error,'recomputed_tasks_per_model':168*16*60,
     'reference_thresholds_selection_verified':True,'source_bootstrap_verified':True,
     'note':'No optimization rerun; tables and complete metrics verified using independently reconstructed histograms and rank formula.'}
(e/'INDEPENDENT_RECOMPUTATION.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\n')
print(out)
