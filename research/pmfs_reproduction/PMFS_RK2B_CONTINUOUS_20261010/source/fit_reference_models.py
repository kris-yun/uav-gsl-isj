"""Fit one frozen U/S/L per reference budget; reference states only."""
from common_b import *
import csv,collections,time,importlib.util,numpy as np,math
import rk2b_models as models
def csvrows(p):
    with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def module(n,p):
    s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def main(M):
    reg=load(CORE/'experiment_registry.json');out=CORE/f'M{M}';out.mkdir(exist_ok=False);started=time.perf_counter();physical=Path(reg['host_data_path'])
    raw=module('raw_model_prediction',CORE/'source/verify_raw_receiver_queries.py');prim=module('model_fallback_primitive',CORE/'source/cache_native.py').cutoff_and_contributions;occ=raw.occupancy(RAW/'OccupancyGrid3D.csv')
    all_refs=[j for j in reg['jobs'] if j['role'] in ('reference','extra_reference')]
    train=[j for j in all_refs if M==4 or j['role']=='reference'];ci=load(RAW/'reference_cache/CACHE_INDEX.json');entries={(e['job_id'],e['frame']):e for e in ci['entries']}
    ff=[];phis=[];weights=[];slices={};queries=[];offset=0;zero=[]
    for job in train:
        lin=csvrows(physical/'realizations'/job['job_id']/'QUERY_PHYSICAL_LINEAGE.csv');native={r['query_id']:r for r in csvrows(physical/'realizations'/job['job_id']/'QUERY_OUTPUT.csv')}
        frames=sorted({int(q['frame']) for q in lin});total=sum(entries[job['job_id'],frame]['exposure']*entries[job['job_id'],frame]['particles'] for frame in frames)
        if total==0:zero.append(job['job_id'])
        for frame in frames:
            ent=entries[job['job_id'],frame]
            with np.load(RAW/'reference_cache'/ent['file'],allow_pickle=False) as z:f=z['filaments'].copy();phi=z['contributions'].copy()
            slices[job['job_id'],frame]=(offset,offset+len(f));offset+=len(f);ff.append(f);phis.append(phi)
            weights.append(np.full(len(f),ent['exposure']/total if total else 0.))
        for row in lin:
            bid=int(row['block_id']);queries.append(dict(reference_id=job['job_id'],frame=int(row['frame']),block_id=bid,pose_id=bid//5,native_ppm=float(native[f'b{bid}_p{bid//5}']['ppm_float32'])))
    assert len(queries)==3*M*50
    f=np.concatenate(ff);phi=np.concatenate(phis);w=np.concatenate(weights)
    dump(out/'ZERO_PARTICLE_REFERENCE_JOBS.json',dict(jobs=zero,note='Zero-particle realizations remain zero query rows, not ghost states; nonempty reference priors retain whole-realization weight1.'))
    if not len(f):
        dump(out/'MODEL_STATUS.json',dict(status='NOT_RUN_ZERO_REFERENCE_STATES',methods=['F'],U_S_L='No particle support; no physical/score retuning'));return
    cells,features=models.physical_features(f);targets=np.array([q['native_ppm'] for q in queries]);poses=np.array([q['pose_id'] for q in queries])
    data=dict(f=f,phi=phi,weights=w,cells=cells,features=features,queries=queries,slices=slices,targets=targets,poses=poses)
    common=reg['model_rules']|dict(training_rows_per_pose=15*M)
    progress_events=[]
    def progress(phase,**kw):
        value=dict(phase=phase,M=M,wall_s=time.perf_counter()-started,**kw);progress_events.append(value)
        with (out/'progress.jsonl').open('a',encoding='utf-8') as s:s.write(json.dumps(value)+'\n')
        dump(CORE/'progress.json',value)
    fits={};errors={}
    for name,spec in [('U_query',dict(kind='U')),('S_query',dict(kind='S',z_cut=models.weighted_quantile(features[:,2],w,.5),sigma_cut=models.weighted_quantile(features[:,3],w,.5)))]:
        try:fits[name]=models.build_model(data,spec,common);progress('ORDINARY_FITTED',method=name,train_MSE=fits[name]['train_MSE'])
        except Exception as error:errors[name]=repr(error);dump(out/(name+'_FIT_FAILURE.json'),dict(error=repr(error),scientific_result=False,same_objective_polish_already_applied=True))
    if all(n in fits for n in ['U_query','S_query']):
        try:fits['L'],proposal=models.learn_one_tree(data,common,fits['S_query'],fits['U_query'],progress);dump(out/'TREE_PROPOSALS.json',proposal)
        except Exception as error:errors['L']=repr(error);dump(out/'L_FIT_FAILURE.json',dict(error=repr(error),scientific_result=False,do_not_retune=True))
    meta={};(out/'models').mkdir();(out/'runtime_models').mkdir()
    for n,m in fits.items():
        np.savez_compressed(out/'models'/f'{n}.npz',keys=m['keys'],decoder=m['h'],prior=m['prior'],train_counts=m['X'],train_native_ppm=targets,train_pose_ids=poses,routing_spec=np.array(json.dumps(m['spec'],sort_keys=True)))
        np.savez(out/'runtime_models'/f'{n}.npz',keys=m['keys'],decoder=m['h'],routing_spec=np.array(json.dumps(m['spec'],sort_keys=True)))
        meta[n]={k:m[k] for k in ['spec','capacity','fit_logs','train_MSE']};meta[n]['capacity'].update(nonzero_coefficients=int(np.count_nonzero(m['h'])),runtime_NPZ_bytes=(out/'runtime_models'/f'{n}.npz').stat().st_size)
    dump(out/'MODEL_METADATA.json',meta);dump(out/'MODEL_HASHES_BEFORE_TEST.json',{p.name:sha(p) for p in (out/'models').iterdir()})
    # All own-candidate references are forecast; M2 primary extracts original pair only.
    candidate_ids=[s['future_candidate_id'] for s in reg['sources']];R=4 if reg['mode']==24 else 2
    responses={n:np.zeros((3,R,50),dtype=float) for n in ['F',*fits]};matrices=np.zeros((3,R,50,len(reg['all_receiver_xyz'])),dtype=np.float32);costs=[]
    for cid in candidate_ids:
        jobs=[j for j in all_refs if j['candidate_id']==cid];ciidx=candidate_ids.index(cid)
        assert len(jobs)==R
        for ri,job in enumerate(jobs):
            root=physical/'realizations'/job['job_id'];lineage=csvrows(root/'QUERY_PHYSICAL_LINEAGE.csv');native={r['query_id']:r for r in csvrows(root/'QUERY_OUTPUT.csv')};desc_cache={}
            for line in lineage:
                bid=int(line['block_id']);pose=bid//5;frame=int(line['frame']);t=time.perf_counter()
                if frame not in desc_cache:desc_cache[frame]=raw.snapshot(root/'bank'/f'iteration_{frame}')
                desc=desc_cache[frame];parse=time.perf_counter()-t
                matrices[ciidx,ri,bid]=[float(native[f'b{bid}_p{p}']['ppm_float32']) for p in range(matrices.shape[-1])]
                responses['F'][ciidx,ri,bid]=matrices[ciidx,ri,bid,pose]
                for name,m in fits.items():
                    snapshot=models.CompressionSnapshot(desc,np.array(reg['all_receiver_xyz'][pose],dtype=np.float32),pose)
                    value,detail=models.compress(snapshot,m,raw,prim,occ);responses[name][ciidx,ri,bid]=value
                    costs.append(dict(M=M,method=name,job_id=job['job_id'],block_id=bid,parse_wall_s=parse,readout_wall_s=detail['total_compression_wall_s'],route_wall_s=detail['state_assignment_wall_s'],decode_wall_s=detail['decode_wall_s'],fallback_wall_s=detail['fallback_wall_s'],fallback_particles=detail['fallback_particles'],particles=detail['particles'],LOS_calls=detail['LOS_calls']))
            progress('REFERENCE_FORECAST_COMPLETE',job=job['job_id'])
    (out/'forecasts').mkdir()
    for n,a in responses.items():np.savez_compressed(out/'forecasts'/f'{n}.npz',candidate_ids=np.array(candidate_ids),source_xyz=np.array([s['xyz_m'] for s in reg['sources']]),reference_response_ppm=a,receiver_plan_id=np.array(reg['receiver_plan_id']))
    np.savez_compressed(out/'F_REFERENCE_ALL_POSES.npz',response_ppm=matrices,candidate_ids=np.array(candidate_ids))
    used=responses['F'][:,:M];z=np.log1p(used.astype(np.float32).astype(float));iqr=float(np.quantile(z,.75)-np.quantile(z,.25))
    dump(out/'HEAD_SCALE_FROZEN.json',dict(F_reference_z_IQR=iqr,H1_scale=iqr if iqr>1e-12 else 1.,fallback=iqr<=1e-12,M=M))
    if costs:
        with (out/'READOUT_COSTS.csv').open('w',encoding='utf-8',newline='') as s:wri=csv.DictWriter(s,fieldnames=list(costs[0]));wri.writeheader();wri.writerows(costs)
    dump(out/'PRE_TEST_PREDICTION_FREEZE.json',{p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file() and p.name not in ('progress.jsonl','PRE_TEST_PREDICTION_FREEZE.json')})
    dump(out/'MODEL_STATUS.json',dict(status='PASS_REFERENCE_MODELS_AND_FORECASTS_FROZEN' if not errors else 'PARTIAL_MODEL_ARMS_FROZEN',methods=list(responses),errors=errors,M=M,fit_search_and_forecast_wall_s=time.perf_counter()-started,test_observations_opened=False))
    print(json.dumps(load(out/'MODEL_STATUS.json'),indent=2))
if __name__=='__main__':main(int(sys.argv[1]))
