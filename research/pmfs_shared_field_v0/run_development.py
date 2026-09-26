"""One signed OPEN comparison. No new plumes, networks or sealed data."""
from __future__ import annotations
import argparse,csv,hashlib,json,os,time
from pathlib import Path
import numpy as np
from solver import fit

MODELS=['NOMINAL','INDEPENDENT_DRO','TEMPERATURE','SHARED_FIELD','SHUFFLED_SHARED']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(path,obj):path.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def alphabet(training):
    positive=training[training>0]
    thresholds=np.unique(np.quantile(positive,[1/3,2/3])).tolist() if positive.size else []
    return {'positive_thresholds':thresholds,'bins':len(thresholds)+2 if positive.size else 1}
def encode(raw,abc):
    if abc['bins']==1:return np.zeros(raw.shape[:-1],dtype=np.int16)
    bins=np.where(raw==0,0,1+np.searchsorted(abc['positive_thresholds'],raw,side='left'))
    return (bins[...,0]*abc['bins']+bins[...,1]).astype(np.int16)
def truth_scores(Q,codes):
    S,R,M=codes.shape;ss=np.arange(S)[:,None,None];mm=np.arange(M)[None,None,:]
    return np.log(Q[ss,mm,codes])
def temperature(Q,T):
    logq=np.log(Q)/T;logq-=logq.max(0,keepdims=True)
    q=np.exp(logq);return q/q.sum(0,keepdims=True)
def pick(scores,kind):
    best=max(scores.values());eligible=[k for k,v in scores.items() if best-v<=1e-12]
    return min(eligible) if kind=='rho' else min(eligible,key=lambda t:(abs(t-1),t))
def detail(f):
    return {'entropy':f.entropy,'worst_risk':f.worst_risk,'gap':f.gap,'constraint_violation':f.constraint_violation,
            'iterations':f.iterations,'seconds':f.seconds,'max_protocol_gap':f.protocol_max_gap}
def shuffle_codes(codes,refs,source_ids,run_ids,outer):
    S,R,M=codes.shape;perms=np.empty((S,M,R),dtype=np.int16);out=np.empty_like(codes)
    for s in range(S):
        for m in range(M):
            order=list(range(R)) if m==0 else sorted(range(R),key=lambda j:hashlib.sha256(
                f'PMFS_SHARED_FIELD_IDENTITY_ABLATION_V0|{outer}|{source_ids[s]}|{m}|{run_ids[s,refs[j]]}'.encode()).digest())
            perms[s,m]=order;out[s,:,m]=codes[s,order,m]
            assert np.array_equal(np.sort(out[s,:,m]),np.sort(codes[s,:,m]))
    return out,perms

def main(a):
    started=time.perf_counter();e=a.root/'evidence/pmfs_shared_field_v0';c=json.loads((e/'NUMERICAL_CONTRACT.json').read_text())
    assert c['status']=='SIGNED_BEFORE_OUTER_SCORING'
    assert json.loads((e/'SOLVER_CONFORMANCE.json').read_text())['status']=='SCALABLE_SOLVER_CONFORMANCE_PASS'
    arrays=[]
    for item in c['inputs']:
        path=Path(item['path']);assert sha(path)==item['sha256'];arrays.append(np.load(path,allow_pickle=False))
    # Only one probe, two times per task. No 30-probe simultaneous trajectory.
    raw=np.concatenate([x[:,:,[0,9],:].transpose(0,1,3,2) for x in arrays],axis=2)
    S,R,M,_=raw.shape;assert (S,R,M)==(168,16,60)
    panel=list(csv.DictReader((e/'central_panel.tsv').open(),delimiter='\t'))
    ids=[v['source_id'] for v in panel];xyz=np.asarray([[float(v[k]) for k in ('x_m','y_m','z_m')] for v in panel])
    distance=np.linalg.norm(xyz[:,None,:]-xyz[None,:,:],axis=-1)
    joins=list(csv.DictReader((e/'RUN_ID_JOIN.csv').open()))
    runids=np.empty((S,R),dtype=object)
    for row in joins:runids[int(row['source_index']),int(row['replicate_index'])]=row['run_id']
    fold_reports=[];predictions={};codes_archive={};weights={};fit_records=[]
    for fold,held in enumerate(c['folds']):
        held=np.asarray(held);refs=np.asarray([r for r in range(R) if r not in held])
        select_shared={rho:[] for rho in c['selection']['rho_grid']};select_ind={rho:[] for rho in select_shared}
        select_t={t:[] for t in c['selection']['temperature_grid']}
        for inner in range(3):
            val=refs[np.arange(12)%3==inner];train=refs[np.arange(12)%3!=inner]
            abc=alphabet(raw[:,train]);K=abc['bins']**2;codes=encode(raw,abc)
            nominal=fit(codes[:,train],K,0)
            for T in select_t:select_t[T].append(float(truth_scores(temperature(nominal.posterior,T),codes[:,val]).mean()))
            for rho in select_shared:
                for arm,selection,ind in [('SHARED',select_shared,False),('INDEPENDENT',select_ind,True)]:
                    f=nominal if rho==0 else fit(codes[:,train],K,rho,independent=ind)
                    selection[rho].append(float(truth_scores(f.posterior,codes[:,val]).mean()))
                    fit_records.append({'outer':fold,'inner':inner,'phase':'reference_selection','arm':arm,'rho':rho,'alphabet':abc,**detail(f)})
                    print(f'outer={fold} inner={inner} {arm} rho={rho} certified it={f.iterations} gap={f.gap:.2g}',flush=True)
            dump(e/'PROGRESS.json',{'phase':'inner_reference_selection','outer':fold,'inner':inner,'elapsed_seconds':time.perf_counter()-started})
        shared_rho=pick({k:float(np.mean(v)) for k,v in select_shared.items()},'rho')
        ind_rho=pick({k:float(np.mean(v)) for k,v in select_ind.items()},'rho')
        T=pick({k:float(np.mean(v)) for k,v in select_t.items()},'temperature')
        abc=alphabet(raw[:,refs]);K=abc['bins']**2;codes=encode(raw,abc)
        nominal=fit(codes[:,refs],K,0)
        sf=fit(codes[:,refs],K,shared_rho);ind=fit(codes[:,refs],K,ind_rho,independent=True)
        shuffled,perms=shuffle_codes(codes[:,refs],refs,ids,runids,fold)
        shuffled_fit=fit(shuffled,K,shared_rho)
        # Nominal must be exactly invariant under protocol-wise identity shuffle.
        shuffled_nominal=fit(shuffled,K,0)
        assert np.allclose(shuffled_nominal.posterior,nominal.posterior,atol=1e-14,rtol=0)
        tables=[nominal.posterior,ind.posterior,temperature(nominal.posterior,T),sf.posterior,shuffled_fit.posterior]
        for name,Q in zip(MODELS,tables):
            assert np.isfinite(Q).all() and (Q>0).all() and np.allclose(Q.sum(0),1,atol=1e-12)
            predictions[f'fold_{fold}_{name}']=Q
        codes_archive[f'fold_{fold}_all_codes']=codes;codes_archive[f'fold_{fold}_refs']=refs;codes_archive[f'fold_{fold}_held']=held
        codes_archive[f'fold_{fold}_shuffle_permutation']=perms
        weights[f'fold_{fold}_SHARED']=sf.weights;weights[f'fold_{fold}_INDEPENDENT']=ind.weights;weights[f'fold_{fold}_SHUFFLED']=shuffled_fit.weights
        for name,f,rho in [('SHARED_FIELD',sf,shared_rho),('INDEPENDENT_DRO',ind,ind_rho),('SHUFFLED_SHARED',shuffled_fit,shared_rho)]:
            fit_records.append({'outer':fold,'phase':'outer_fit','arm':name,'rho':rho,**detail(f)})
        fold_reports.append({'fold':fold,'refs':refs.tolist(),'held':held.tolist(),'alphabet':abc,'shared_rho':shared_rho,
            'independent_rho':ind_rho,'temperature':T,'selection_shared':select_shared,'selection_independent':select_ind,
            'selection_temperature':select_t,'nominal_shuffle_max_error':float(np.max(abs(shuffled_nominal.posterior-nominal.posterior)))})
        # Save fitted tables and symbols BEFORE computing external target metrics.
        np.savez_compressed(e/'PROBABILITY_MAP_TABLES.npz',**predictions)
        np.savez_compressed(e/'OBSERVATION_CODES.npz',**codes_archive)
        np.savez_compressed(e/'REALIZATION_WEIGHTS.npz',**weights)
        dump(e/'FIT_RECORDS.json',fit_records);dump(e/'FOLD_MODELS.json',fold_reports)
        print(f'outer={fold} models locked; shared rho={shared_rho}, independent rho={ind_rho}, T={T}',flush=True)
    # All outer models and choices exist before aggregate heldout scoring.
    metric_names=['log2_truth_probability','brier','truth_rank','map_distance_m','expected_distance_m','mass_05m','mass_1m']
    values=np.zeros((len(MODELS),S,R,M,len(metric_names)),dtype=np.float64)
    for fold,held in enumerate(c['folds']):
        codes=codes_archive[f'fold_{fold}_all_codes']
        for mi,name in enumerate(MODELS):
            Q=predictions[f'fold_{fold}_{name}']
            # Protocol table representation is lossless: each full posterior
            # is Q[:,protocol,encoded_observation]. No giant duplicate array.
            for m in range(M):
                selected=Q[:,m,codes[:,held,m]].transpose(1,2,0)  # truth source,held,candidate
                truth=selected[np.arange(S)[:,None],np.arange(len(held))[None,:],np.arange(S)[:,None]]
                order=np.argsort(-selected,axis=-1,kind='stable')
                rank=np.argmax(order==np.arange(S)[:,None,None],axis=-1)+1
                mapid=order[...,0]
                batch=np.stack([np.log2(truth),np.sum(selected**2,axis=-1)-2*truth+1,rank,
                    distance[np.arange(S)[:,None],mapid],np.sum(selected*distance[:,None,:],axis=-1),
                    np.sum(selected*(distance[:,None,:]<=.5),axis=-1),np.sum(selected*(distance[:,None,:]<=1),axis=-1)],axis=-1)
                values[mi,:,held,m,:]=batch.transpose(1,0,2)
    np.savez_compressed(e/'TARGET_METRICS.npz',values=values,metric_names=np.asarray(metric_names),model_names=np.asarray(MODELS))
    with (e/'TARGET_METRICS.csv').open('w',newline='',encoding='utf-8') as stream:
        fields=['model','source_id','replicate_index','run_id','protocol','layout','probe']+metric_names
        writer=csv.writer(stream);writer.writerow(fields)
        for mi,name in enumerate(MODELS):
            for s in range(S):
                for r in range(R):
                    for m in range(M):writer.writerow([name,ids[s],r,runids[s,r],m,'P_G1A' if m<30 else 'P_E2',m%30]+values[mi,s,r,m].tolist())
    summary=[]
    for mi,name in enumerate(MODELS):
        v=values[mi];nll=-v[...,0]
        report={'model':name,**{key:float(v[...,j].mean()) for j,key in enumerate(metric_names)},
                'nll_bits_mean':float(nll.mean()),'nll_bits_q95':float(np.quantile(nll,.95)),
                'nll_bits_max':float(nll.max()),'top1':float((v[...,2]<=1).mean()),
                'top3':float((v[...,2]<=3).mean()),'top5':float((v[...,2]<=5).mean())}
        summary.append(report)
    rng=np.random.default_rng(c['bootstrap']['seed']);ix=rng.integers(0,S,size=(10000,S))
    comparisons=[]
    for mi,name in enumerate(MODELS):
        if name=='SHARED_FIELD':continue
        delta=values[3,...,0]-values[mi,...,0];source=delta.mean(axis=(1,2));boot=source[ix].mean(1);flat=np.sort(delta.ravel())
        trim=len(flat)//5;keep=len(flat)-int(np.ceil(.05*len(flat)))
        comp={'control':name,'mean_gain_bits':float(source.mean()),'source_panel_95pct_sensitivity':np.quantile(boot,[.025,.975]).tolist(),
              'positive_sources':int((source>0).sum()),'source_effects_bits':source.tolist(),
              'trimmed20_mean_bits':float(flat[trim:-trim].mean()),'drop_top5pct_positive_mean_bits':float(flat[:keep].mean()),
              'gain_bits_q01_q50_q99':np.quantile(flat,[.01,.5,.99]).tolist(),
              'per_layout_mean_bits':[float(delta[:,:,:30].mean()),float(delta[:,:,30:].mean())]}
        comparisons.append(comp)
    good=all(v['mean_gain_bits']>0 and v['source_panel_95pct_sensitivity'][0]>0 for v in comparisons)
    decision='DEVELOPMENT_RETAIN_SHARED_FIELD_CANDIDATE' if good else 'DEVELOPMENT_STOP_NO_INCREMENT_BEYOND_CONTROLS'
    result={'DEVELOPMENT_DECISION':decision,'scientific_confirmation':False,'scope':c['scope'],
            'models':summary,'comparisons_shared_minus_control':comparisons,'fold_selection':fold_reports,
            'optimization_all_certified':True,'optimization_fit_count':len(fit_records),
            'maximum_gap_nats':max(v['gap'] for v in fit_records),'maximum_constraint_violation':max(v['constraint_violation'] for v in fit_records),
            'compute_seconds_total':time.perf_counter()-started,'protocols_per_run':60,
            'posterior_output':'exact model/fold/protocol/symbol tables plus per-run symbols; get Q[:,m,z]',
            'raw_original_tensors_preserved':True,'further_experiment_started':False,
            'failure_attribution':'No shared-field innovation claim unless gains exceed nominal, independent DRO, temperature and identity shuffle simultaneously; not a statement that all robust estimators fail.'}
    dump(e/'DEVELOPMENT_RESULT.json',result)
    dump(e/'PROGRESS.json',{'phase':'complete','decision':decision,'elapsed_seconds':time.perf_counter()-started})
    print(decision,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();a.root=a.root.resolve()
    try:main(a)
    except Exception as exc:
        e=a.root/'evidence/pmfs_shared_field_v0';dump(e/'IMPLEMENTATION_STOP.json',{'decision':'DEVELOPMENT_IMPLEMENTATION_BLOCKED','scientific_decision':None,'exception':repr(exc)})
        raise
