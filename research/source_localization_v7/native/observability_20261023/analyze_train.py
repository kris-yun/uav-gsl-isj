"""Finite TRAIN-only observability diagnostics, not an M1 performance search."""
import itertools,json,time
import numpy as np
from common import PROJECT,OUT,PROTOCOL,sha,write,csvout,dataset,probes
from gsl_discrimination.m1_opponent.operator import time_weights

METHODS=['single_L_full','single_R_full','single_L_mean','single_R_mean',
 'single_L_hitfraction','single_R_hitfraction','pair_means','pair_means_equal_scalar_budget',
 'pair_hitfractions','pair_ordered_full','pair_unordered_joint','pair_sorted_marginals',
 'pair_ordered_equal_scalar_budget']
SINGLE=range(6)
TRUTH=np.array([0,0,1,1])

def make_features(values,times,pairs,known):
    # values [source, repeat, native time, probe]. No labels used in features.
    i=pairs[:,0];j=pairs[:,1]
    raw=np.stack((values[...,i],values[...,j]),axis=-1).transpose(0,1,3,2,4)
    z=np.log1p(raw) if known else raw.copy()
    w=time_weights(times);n=len(times);dec=np.arange(0,2*(n//2),2)
    sub=z[...,dec,:];subw=time_weights(times[dec])
    means=np.einsum('srptc,t->srpc',z,w)
    submeans=np.einsum('srptc,t->srpc',sub,subw)
    hit=np.einsum('srptc,t->srpc',(raw>=.1).astype(float),w)
    order=np.lexsort((z[...,1],z[...,0]),axis=-1)
    unordered=np.take_along_axis(z,order[...,None],axis=-2)
    flatten=lambda a:a.reshape(a.shape[:3]+(-1,))
    features=[z[...,0],z[...,1],means[...,0,None],means[...,1,None],
        hit[...,0,None],hit[...,1,None],means,submeans,hit,flatten(z),flatten(unordered),
        flatten(np.sort(z,axis=-2)),flatten(sub)]
    return dict(zip(METHODS,features))

def score(y,mu,unknown_gain):
    if unknown_gain:
        e=np.sum(mu*mu,axis=-1)
        gain=np.divide(np.sum(y*mu,axis=-1),e,out=np.zeros_like(e),where=e>0)
        gain=np.maximum(gain,0)
        residual=np.sum((y-gain[...,None]*mu)**2,axis=-1)
        energy=np.sum(y*y,axis=-1)
        return np.divide(residual,energy,out=np.zeros_like(residual),where=energy>0)
    return np.mean((y-mu)**2,axis=-1)

def cross_world(features,unknown):
    outcomes=[];margins=[];distances=[]
    for source in range(2):
        for repeat in range(2):
            y=features[source,repeat]
            d=np.stack([score(y,features[s,1-repeat],unknown) for s in range(2)],axis=-1)
            difference=d[...,1]-d[...,0]
            ties=np.abs(difference)<=1e-12*np.maximum(1,np.max(np.abs(d),axis=-1))
            pred=np.argmin(d,axis=-1).astype(np.int8);pred[ties]=-1
            denom=np.maximum(np.sum(d,axis=-1),1e-12)
            margin=(d[...,1-source]-d[...,source])/denom
            outcomes.append(pred);margins.append(margin);distances.append(d)
    return np.array(outcomes),np.array(margins),np.array(distances)

def summarize_raw(values,times,receipt):
    rows=[]
    for s in range(2):
        for r in range(2):
            for p in range(30):
                x=values[s,r,:,p]
                fields={'world_id':receipt['worlds'][s*2+r]['run_id'],'source':('A','B')[s],
                        'probe_rank':p+1,'frames':len(x),'zero_count':int(np.sum(x==0)),
                        'positive_count':int(np.sum(x>0)),'minimum_positive_ppm':float(x[x>0].min()) if np.any(x>0) else None,
                        'maximum_ppm':float(x.max()),'time_mean_ppm':float(np.dot(x,time_weights(times)))}
                for threshold in (0.,.1):
                    b=x>0 if threshold==0 else x>=threshold
                    key='exact_positive' if threshold==0 else 'hit_0p1ppm'
                    fields[key+'_fraction']=float(b.mean());fields[key+'_switches']=int(np.sum(b[1:]!=b[:-1]))
                    fields[key+'_always_zero']=bool(not b.any());fields[key+'_always_one']=bool(b.all())
                rows.append(fields)
    csvout('PER_WORLD_PROBE_FULL_HISTORY.csv',rows)
    return rows

def main():
    start=time.perf_counter()
    if (OUT/'TRAIN_ANALYSIS_RESULT.json').exists():raise RuntimeError('TRAIN diagnostic already frozen')
    config=json.loads(PROTOCOL.read_text());values,times,receipt=dataset()
    assert len(receipt['worlds'])==4 and receipt['DEV_raw_frames_read']==0
    rawrows=summarize_raw(values,times,receipt)
    pp=probes();pos=np.array([[float(p['center_x_m']),float(p['center_y_m']),float(p['z_m'])] for p in pp])
    pairs=np.array(list(itertools.combinations(range(30),2)))
    separation=np.linalg.norm(pos[pairs[:,0]]-pos[pairs[:,1]],axis=-1)
    eligible=(separation>=config['selected_pair_minimum_separation_m'])&(separation<=config['selected_pair_maximum_separation_m'])
    pairrows=[];windowrows=[];all_outcomes=[];all_margins=[];windows=[];candidates=[]
    for anchor in range(50,951,50):
        keep=np.flatnonzero((times>=anchor)&(times<=anchor+20));t=times[keep];x=values[:,:,keep,:]
        assert len(t)>=3 and np.diff(t).max()<=.61
        per_model=[];margin_model=[]
        for known in (True,False):
            feature=make_features(x,t,pairs,known)
            outcomes=[];margins=[]
            for method in METHODS:
                if not known and 'hitfraction' in method:
                    # Concentration gain does not act linearly on an already
                    # thresholded hit fraction. Do not label that operation
                    # a physical source-strength control.
                    pred=np.full((4,len(pairs)),-2,dtype=np.int8)
                    margin=np.full((4,len(pairs)),np.nan)
                else:
                    pred,margin,distance=cross_world(feature[method],not known)
                outcomes.append(pred);margins.append(margin)
            per_model.append(np.array(outcomes));margin_model.append(np.array(margins))
        pred=np.array(per_model) # amplitude,method,world,pair
        margin=np.array(margin_model)
        strict=np.sum(pred==TRUTH[None,None,:,None],axis=2)
        ties=np.sum(pred<0,axis=2)
        single_best=np.max(strict[0,list(SINGLE)],axis=0)
        static_best=np.max(strict[0,[6,7,8]],axis=0)
        dynamic=(single_best<=3)&(static_best<=3)&(strict[0,10]<=3)&(strict[0,9]==4)&(strict[0,12]==4)
        spatial=(single_best<=3)&(strict[0,6]==4)&(strict[0,7]==4)
        for k,(i,j) in enumerate(pairs):
            row={'anchor_s':anchor,'probe_L':int(i+1),'probe_R':int(j+1),'distance_m':float(separation[k]),
                 'selection_geometry_eligible':bool(eligible[k]),'samples_per_sensor':len(t),
                 'known_best_single_strict_correct':int(single_best[k]),'known_best_static_pair_strict_correct':int(static_best[k]),
                 'dynamic_opportunity':bool(dynamic[k]),'spatial_opportunity':bool(spatial[k])}
            for a,prefix in enumerate(('known','unknown_gain')):
                for m,method in enumerate(METHODS):
                    row[prefix+'_'+method+'_strict']=int(strict[a,m,k]);row[prefix+'_'+method+'_ties']=int(ties[a,m,k])
            pairrows.append(row)
            for kind,mask,mi in [('dynamic',dynamic,9),('spatial',spatial,6)]:
                if mask[k] and eligible[k]:
                    candidates.append({'kind':kind,'anchor_s':anchor,'probe_L':int(i+1),'probe_R':int(j+1),
                        'distance_m':float(separation[k]),'minimum_train_margin':float(margin[0,mi,:,k].min()),
                        'unknown_gain_full_successes':int(strict[1,9,k]),'window_indices':keep.tolist()})
        for s in range(2):
            for r in range(2):
                for p in range(30):
                    y=x[s,r,:,p];b=y>=.1
                    windowrows.append({'anchor_s':anchor,'world_id':receipt['worlds'][s*2+r]['run_id'],
                        'source':('A','B')[s],'probe_rank':p+1,'samples':len(y),'exact_zero_count':int(np.sum(y==0)),
                        'positive_count':int(np.sum(y>0)),'hit_0p1ppm_count':int(b.sum()),
                        'hit_switches':int(np.sum(b[1:]!=b[:-1])),'time_mean_ppm':float(np.dot(y,time_weights(t)))})
        all_outcomes.append(pred);all_margins.append(margin)
        windows.append({'anchor_s':anchor,'indices':keep.tolist(),'times_s':t.tolist(),'samples':len(t),
            'equal_budget_scalar_samples':2*(len(t)//2),'single_scalar_samples':len(t),
            'single_last_s':float(t[-1]),'pair_decimated_last_s':float(t[np.arange(0,2*(len(t)//2),2)[-1]])})
        print('TRAIN_WINDOW',anchor,'dynamic',int(dynamic.sum()),'spatial',int(spatial.sum()),flush=True)
    csvout('PER_PAIR_WINDOW_TRAIN.csv',pairrows);csvout('PER_WORLD_PROBE_WINDOWS.csv',windowrows)
    np.savez_compressed(OUT/'TRAIN_PAIR_WORLD_OUTCOMES.npz',prediction=np.array(all_outcomes),
           signed_margin=np.array(all_margins),pairs=pairs,truth=TRUTH,method_names=np.array(METHODS),
           amplitudes=np.array(['known','unknown_gain']),anchors=np.arange(50,951,50))
    candidates.sort(key=lambda c:(0 if c['kind']=='dynamic' else 1,-c['minimum_train_margin'],c['distance_m'],c['anchor_s'],c['probe_L'],c['probe_R']))
    selected=candidates[0] if candidates else None
    write('TRAIN_ANALYSIS_RESULT.json',{'status':'FINITE_TRAIN_DIAGNOSTIC_COMPLETE','window_count':len(windows),
       'pairs_per_window':len(pairs),'total_pair_windows':len(pairrows),'eligible_probe_pairs':int(eligible.sum()),
       'dynamic_opportunity_pair_windows':sum(r['dynamic_opportunity'] for r in pairrows),
       'spatial_opportunity_pair_windows':sum(r['spatial_opportunity'] for r in pairrows),
       'eligible_candidate_count':len(candidates),'selected_candidate':selected,'candidates':candidates,
       'windows':windows,'worlds':receipt['worlds'],'DEV_responses_read':0,'M1_used_for_selection':False,
       'uncertainty':'only two TRAIN realizations per source; no population or information-theoretic sufficiency certificate',
       'unknown_gain_hitfraction_control':'NOT_APPLICABLE; concentration scaling is not linear on thresholded events',
       'diagnostic_not_active_UAV':True,'wall_s':time.perf_counter()-start})
    write('SELECTION_FREEZE.json',{'status':'ONE_DEVELOPMENT_CHECK_FROZEN' if selected else 'NO_ELIGIBLE_CANDIDATE_NO_DEV_QUERY',
       'selected':selected,'protocol_sha256':sha(PROTOCOL),'all_methods':METHODS,
       'TRAIN_arrays_sha256':{w['file']:w['sha256'] for w in receipt['worlds']},
       'analysis_code_sha256':sha(__file__),'results_sha256':sha(OUT/'TRAIN_PAIR_WORLD_OUTCOMES.npz'),
       'old_DEV_is_not_new_blind_test':True,'maximum_selected_pair_window':1,
       'next_model':'two TRAIN source prototype means, fixed ordinary features and distance rules, no hyperparameter search'})

if __name__=='__main__':main()
