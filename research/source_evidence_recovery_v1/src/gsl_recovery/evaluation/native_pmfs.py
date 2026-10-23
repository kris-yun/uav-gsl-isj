"""Frozen native PMFS score replay, not a simulator substitute.

Formula anchored in MAPIR Simulations.cpp probabilityFromSingleCell and
sourceProbFromMaps. Scores are compatibility products, NOT calibrated likelihoods.
"""
from pathlib import Path
import csv,numpy as np
from ..io import read_json,write_json,sha256
from ..types import Action,Observation,observation_to_dict

def compatibility_scores(measured,confidence,predictions,free,discrimination=.4):
    measured=np.asarray(measured,float);confidence=np.asarray(confidence,float)
    pred=np.atleast_2d(np.asarray(predictions,float));free=np.asarray(free,bool)
    if pred.shape[1]!=len(measured) or not (0<=discrimination<=1):raise ValueError('PMFS shape/discrimination')
    conf=np.where(np.isnan(confidence)|(confidence<0),0,np.minimum(confidence,1))
    factors=1-conf[None,:]*discrimination*np.abs(measured[None,:]-pred)
    return np.prod(factors[:,free].astype(np.longdouble),axis=1)

def replay_native_b4(root,out_dir):
    root=Path(root);out=Path(out_dir);u=root/'runtime/updates/update_2'
    provenance=read_json(root/'PROVENANCE.json')
    for a in provenance['assets']:
        if sha256(root/a['path'])!=a['sha256']:raise ValueError('B4 frozen fixture modified: '+a['path'])
    data=np.genfromtxt(u/'input.csv',delimiter=',',names=True,dtype=None,encoding='utf-8')
    meta=read_json(u/'metadata.json');N=meta['width']*meta['height']
    if len(data)!=N:raise ValueError('grid geometry mismatch')
    free=data['occupancy']==1
    if int(free.sum())!=meta['free_cells']:raise ValueError('free-cell mismatch')
    p=1.-1./(1.+np.exp(data['logOdds']))
    with open(u/'candidates.csv',newline='') as f:rows=list(csv.DictReader(f))
    values={};errors=[]
    for r in rows:
        hit=np.fromfile(u/r['map_file'],dtype='<f4')
        if len(hit)!=N or not np.isfinite(hit).all():raise ValueError('prediction map shape')
        v=compatibility_scores(p,data['confidence'],hit,free)[0];values[r['candidate_id']]=v
        expected=np.longdouble(r['score']);errors.append(float(abs(v-expected)/max(abs(expected),np.longdouble(1e-300))))
    reconstructed=np.zeros(N,dtype=np.longdouble);covered=np.zeros(N,int)
    with open(u/'final_tree.csv',newline='') as f:tree=list(csv.DictReader(f))
    for r in tree:
        if int(r['has_children']) or int(r['value'])!=1:continue
        val=values[r['node_id']]
        for j in range(int(r['origin_j']),int(r['origin_j'])+int(r['size_j'])):
            for i in range(int(r['origin_i']),int(r['origin_i'])+int(r['size_i'])):
                k=j*meta['width']+i;reconstructed[k]=val;covered[k]+=1
    if np.any(covered[free]!=1):raise ValueError('terminal candidate support gap/overlap')
    reconstructed[free]/=reconstructed[free].sum();reconstructed[~free]=0
    saved=np.fromfile(u/'posterior.f64',dtype='<f8');difference=float(np.max(np.abs(reconstructed-saved)))
    # Only source logscore; no source truth is needed for reconstruction.
    source_ratio=float(values['quadtree_23_37_1_1']/values['quadtree_17_18_5_1'])
    measurements=np.loadtxt(root/'runtime/measurement_events.csv',delimiter=',')
    if measurements.shape!=(50,8) or not np.all(np.diff(measurements[:,0])>0):raise ValueError('measurement event schema')
    # Preserve native detected labels from saved audit, not a tuned threshold.
    with open(root/'B4_OBSERVATION_AND_POSTERIOR_AUDIT.csv',newline='',encoding='utf-8-sig') as f:
        audit=[r for r in csv.DictReader(f) if r['event']=='measurement_block']
    obs=[]
    for n,(r,a) in enumerate(zip(measurements,audit)):
        t,gas,speed,angle,x,y,stop,within=r
        if abs(float(a['gas_ppm'])-gas)>1e-6 or abs(float(a['ROS_s'])-t/1e9)>1e-6:raise ValueError('native event alignment mismatch')
        obs.append(Observation(f'b4-{n+1}',Action(float(x),float(y),.5,float(t/1e9),1.),(float(speed*np.cos(angle)),float(speed*np.sin(angle))),float(a['detected']=='True')))
    xs=meta['origin_x']+(data['grid_i']+.5)*meta['cell_size'];ys=meta['origin_y']+(data['grid_j']+.5)*meta['cell_size']
    record={'schema_version':1,'metadata':{'scene':'B4','source_group':'frozen-B4','wind_group':'static-frame-10','realization_id':'original-single-realization','split':'legacy_evaluation','frame':'map','units':{'position':'m','wind':'m/s','gas':'binary native hit'},'readout':'binary_hit','propagation_qualified':False,'geometry_qualified':True,'candidate_support_qualified':True,'wind_scope':'native block local wind only','sensor_height_scope':'0.5m adapter convention; raw event contains XY only; not used for native score replay','historical_exposure':True},'candidates':np.column_stack((xs[free],ys[free])).tolist(),'observations':[observation_to_dict(o) for o in obs]}
    write_json(out/'b4_episode.json',record)
    np.savez_compressed(out/'native_posterior.npz',source_xy=np.column_stack((xs[free],ys[free])),posterior=np.asarray(reconstructed[free],float))
    receipt={'status':'PASS' if max(errors)<1e-10 and difference<1e-10 else 'FAIL','scope':'REAL_FROZEN_PMFS_B4_OFFLINE_REPLAY','new_localization_gain':False,'new_ROS_runs':0,'new_training':0,'candidate_scores_replayed':len(rows),'max_relative_score_error':max(errors),'max_posterior_abs_error':difference,'measurement_blocks':len(obs),'stops':int(len(np.unique(measurements[:,6]))),'positive_hits':int(sum(o.gas for o in obs)),'wrong_over_true_nearby_compatibility_score':source_ratio,'ratio_is_physical_likelihood':False,'geometry_support':'447 free cells covered exactly once by terminal leaves','native_float_top5_endpoint':'BLOCKED_REQUIRES_LINKED_CXX_RUNTIME','house_01_02_03':'BLOCKED_DATA_NOT_PRESENT','fixture_commit':provenance['commit']}
    write_json(out/'receipt.json',receipt);return receipt
