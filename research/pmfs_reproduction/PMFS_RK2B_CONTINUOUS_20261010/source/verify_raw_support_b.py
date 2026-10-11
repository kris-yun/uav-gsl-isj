"""Portable independent raw support checks, no producer or physical execution."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import csv,json,hashlib,importlib.util,numpy as np
def rows(p):
    with Path(p).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(core,support):
    core=Path(core);support=Path(support);p=core/'source/verify_raw_receiver_queries.py';s=importlib.util.spec_from_file_location('independent_locked_native_readout',p);raw=importlib.util.module_from_spec(s);s.loader.exec_module(raw)
    reg=json.loads((core/'experiment_registry.json').read_text(encoding='utf-8'));occ=raw.occupancy(support/'OccupancyGrid3D.csv');index=rows(support/'SELECTED_RAW_FRAME_INDEX.csv');maximum=0.;anchors=[]
    for row in index:
        f=support/row['support_path'];assert sha(f)==row['SHA256'];d=raw.snapshot(f);assert len(d['filaments'])==int(row['particle_records']);assert d['gas_type']==13 and d['wind_index']==10
        assert np.array_equal(d['dimensions'],occ['dimensions']) and np.array_equal(d['minimum'],occ['minimum'])
    for job in reg['jobs']:
        root=support/'realizations'/job['job_id'];line=rows(root/'QUERY_PHYSICAL_LINEAGE.csv')[0];frame=int(line['frame']);d=raw.snapshot(root/'snapshots'/f'iteration_{frame}');native={r['query_id']:r for r in rows(root/'QUERY_OUTPUT.csv')}
        assert np.allclose(d['source'],job['source_xyz'],atol=1e-6,rtol=0)
        for pi,xyz in enumerate(reg['all_receiver_xyz']):
            value,detail=raw.concentration(xyz,d,occ);target=np.float32(float(native[f'b0_p{pi}']['ppm_float32']));delta=abs(float(value)-float(target));assert delta<=3e-7+5e-6*abs(float(target)),(job['job_id'],pi,value,target)
            maximum=max(maximum,delta);anchors.append(dict(job_id=job['job_id'],pose=pi,absolute_ppm_difference=delta))
    # Reconstruct every saved query count and full-particle conditional prior.
    ci=json.loads((support/'reference_cache/CACHE_INDEX.json').read_text(encoding='utf-8'));cache={};exposures={};phi_checks=0;phi_positive_checks=0
    for ent in ci['entries']:
        pp=support/'reference_cache'/ent['file'];assert sha(pp)==ent['SHA256']
        with np.load(pp,allow_pickle=False) as z:cache[ent['job_id'],ent['frame']]=(z['filaments'].copy(),z['contributions'].copy())
        exposures[ent['job_id'],ent['frame']]=ent['exposure']
        f,phi=cache[ent['job_id'],ent['frame']]
        desc=raw.snapshot(support/'realizations'/ent['job_id']/'snapshots'/f"iteration_{ent['frame']}")
        assert np.array_equal(f,desc['filaments'])
        for particle in sorted({0,len(f)//2,len(f)-1}) if len(f) else []:
            single=desc.copy();single['filaments']=f[particle:particle+1]
            for pose in range(10):
                value,_=raw.concentration(reg['all_receiver_xyz'][pose],single,occ);want=phi[particle,pose]
                assert abs(float(value)-float(want))<=3e-7+5e-6*abs(float(value));phi_checks+=1;phi_positive_checks+=int(value>0)
    def features(f):
        grid=(f[:,:2]-np.array([-7.55,-7.88],np.float32))/np.float32(.25);cell=np.floor(grid).astype(np.int32)
        return cell,np.column_stack((grid-cell,f[:,2],f[:,3])).astype(float)
    def route(spec,x):
        if spec['kind']=='U':return np.zeros(len(x),np.int32)
        if spec['kind']=='S':return 2*(x[:,2]>=spec['z_cut']).astype(np.int32)+(x[:,3]>=spec['sigma_cut']).astype(np.int32)
        out=np.zeros(len(x),np.int32)
        def walk(node,ii):
            if isinstance(node,int):out[ii]=node;return
            test=x[ii,node['feature']]<node['cut'];walk(node['left'],ii[test]);walk(node['right'],ii[~test])
        walk(spec['tree'],np.arange(len(x)));return out
    reconstructions=[];forecast_checks=0;attribution_checks=0
    attribution={(int(r['M']),r['method'],r['job_id'],int(r['block'])):r for r in rows(core/'reference_transfer_error_attribution.csv')} if (core/'reference_transfer_error_attribution.csv').exists() else {}
    for M in [2,4]:
        jobs=[j for j in reg['jobs'] if j['role']=='reference' or (M==4 and j['role']=='extra_reference')]
        metadata=json.loads((core/f'M{M}/MODEL_METADATA.json').read_text(encoding='utf-8'))
        for name,m in metadata.items():
            with np.load(core/f'M{M}/models/{name}.npz',allow_pickle=False) as z:keys=z['keys'];X=z['train_counts'];prior=z['prior'];poses=z['train_pose_ids'];targets=z['train_native_ppm'];h=z['decoder']
            look={tuple(map(int,k)):i for i,k in enumerate(keys)};den=np.zeros(len(keys));num=np.zeros_like(prior);xx=[];pp=[];yy=[]
            for job in jobs:
                root=support/'realizations'/job['job_id'];lines=rows(root/'QUERY_PHYSICAL_LINEAGE.csv');native={r['query_id']:float(r['ppm_float32']) for r in rows(root/'QUERY_OUTPUT.csv')};fkeys={}
                entries=[e for e in ci['entries'] if e['job_id']==job['job_id']];total=sum(e['exposure']*e['particles'] for e in entries)
                for ent in entries:
                    f,phi=cache[job['job_id'],ent['frame']];cell,feat=features(f);cl=route(m['spec'],feat);kk=np.column_stack((cell,cl));idx=np.array([look[tuple(map(int,k))] for k in kk],int);fkeys[ent['frame']]=idx
                    w=ent['exposure']/total if total else 0.;np.add.at(den,idx,w)
                    for pose in range(10):np.add.at(num[:,pose],idx,w*phi[:,pose].astype(float))
                for l in lines:
                    bid=int(l['block_id']);xx.append(np.bincount(fkeys[int(l['frame'])],minlength=len(keys)));pp.append(bid//5);yy.append(native[f'b{bid}_p{bid//5}'])
            assert np.array_equal(xx,X) and np.array_equal(pp,poses);assert np.allclose(yy,targets,rtol=0,atol=1e-14)
            assert (den>0).all();pr=num/den[:,None];assert np.allclose(pr,prior,rtol=1e-10,atol=2e-12)
            reconstructions.append(dict(M=M,method=name,query_rows=len(xx),states=len(keys),maximum_prior_absolute_difference=float(np.max(np.abs(pr-prior),initial=0))))
            with np.load(core/f'M{M}/forecasts/{name}.npz',allow_pickle=False) as z:forecast=z['reference_response_ppm']
            for job in [j for j in reg['jobs'] if j['role'] in ['reference','extra_reference']]:
                root=support/'realizations'/job['job_id'];lines=rows(root/'QUERY_PHYSICAL_LINEAGE.csv');c=[s['future_candidate_id'] for s in reg['sources']].index(job['candidate_id']);ri=job['replicate']+(2 if job['role']=='extra_reference' else 0);frame_indices={}
                for l in lines:
                    frame=int(l['frame']);bid=int(l['block_id']);pose=bid//5;f,phi=cache[job['job_id'],frame]
                    if frame not in frame_indices:
                        cell,feat=features(f);kk=np.column_stack((cell,route(m['spec'],feat)));frame_indices[frame]=np.array([look.get(tuple(map(int,k)),-1) for k in kk],int)
                    idx=frame_indices[frame];known=idx>=0;cnt=np.bincount(idx[known],minlength=len(keys));fb=float(np.cumsum(phi[~known,pose],dtype=np.float32)[-1]) if (~known).any() else 0.;value=float(cnt@h[:,pose])+fb
                    assert abs(value-forecast[c,ri,bid])<=3e-7+5e-6*abs(value);forecast_checks+=1
                    if attribution:
                        r=attribution[M,name,job['job_id'],bid];fit=float(cnt@(h[:,pose]-prior[:,pose]));ps=float(cnt@prior[:,pose])-float(np.sum(phi[known,pose].astype(float)))
                        assert abs(float(r['fit_coefficient_adjustment_ppm'])-fit)<=1e-10*(1+abs(fit));assert abs(float(r['physical_conditional_prior_transfer_ppm'])-ps)<=1e-10*(1+abs(ps));assert abs(float(r['reconstructed_prediction_ppm'])-value)<=1e-10*(1+abs(value));attribution_checks+=1
                        if r['F_zero_model_positive']=='True':
                            assert (phi[:,pose]==0).all() and fb==0;zp=prior[:,pose]==0;zero_value=float(cnt[zp]@h[zp,pose]);assert abs(zero_value-float(r['known_decoder_ppm_from_zero_training_prior_states']))<=1e-10
                            q=np.array(reg['all_receiver_xyz'][pose],np.float32);delta=f[:,:3]-q;squared=np.zeros(len(f),np.float32)
                            for ax in range(3):squared=np.float32(squared+np.float32(delta[:,ax]*delta[:,ax]))
                            lim=np.float32(np.float32(f[:,3]*np.float32(3))/np.float32(100));ii=np.flatnonzero(squared<np.float32(lim*lim));assert len(ii)==int(r['cutoff_eligible_particles'])
                            desc=raw.snapshot(root/'snapshots'/f'iteration_{frame}');assert all(not raw.los(q,f[i,:3],desc,occ) for i in ii)
    result=dict(status='PASS_RAW_BYTE_TIME_GEOMETRY_NATIVE_ANCHORS_AND_TRAINING_LINEAGE',raw_frames=len(index),realizations=len(reg['jobs']),independent_native_concentration_anchors=len(anchors),maximum_absolute_ppm_difference=maximum,source_module_SHA256=sha(p),reference_cache_frames=len(cache),phi_fixed_first_middle_last_scalar_spot_checks=phi_checks,phi_positive_spot_checks=phi_positive_checks,model_training_reconstructions=reconstructions,frozen_reference_forecasts_reconstructed=forecast_checks,error_attribution_rows_independently_checked=attribution_checks,no_simulation=True,no_new_fit=True,producer_model_module_imported=False)
    print(json.dumps(result,indent=2));return result
if __name__=='__main__':main(sys.argv[1],sys.argv[2])
