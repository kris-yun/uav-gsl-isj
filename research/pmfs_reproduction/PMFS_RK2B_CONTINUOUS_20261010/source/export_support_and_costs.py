"""Mechanical export of existing raw records, frozen routing coverage and cost ledgers.
No new score head, fitting, physical generation, source inference or selection.
"""
from common_b import *
import csv,shutil,collections,numpy as np
import rk2b_models as models
import verify_raw_receiver_queries as raw

def rows(p):
    with Path(p).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def write(p,a):
    if not a:return
    keys=list(dict.fromkeys(k for r in a for k in r))
    with Path(p).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys,lineterminator='\n');w.writeheader();w.writerows(a)
def main():
    begin=time.perf_counter();reg=load(CORE/'experiment_registry.json');physical=Path(reg['host_data_path']);gen=load(CORE/'GENERATION_LEDGER.json')
    assert load(CORE/'stage_status.json')['status']=='COMPLETE_ALL_REGISTERED_BRANCHES'
    # Requires the immutable blind prediction checkpoint before hidden-state metadata export.
    assert sha(CORE/'BLIND_PREDICTIONS.json')==load(CORE/'BLIND_PREDICTION_FREEZE.json')['SHA256']
    frozen={};lookup={};coverage=[];files=[];costs=[]
    for M in [2,4]:
        metadata=load(CORE/f'M{M}/MODEL_METADATA.json')
        for name,m in metadata.items():
            with np.load(CORE/f'M{M}/runtime_models/{name}.npz',allow_pickle=False) as z:keys=z['keys']
            frozen[M,name]=m['spec'];lookup[M,name]={tuple(map(int,k)) for k in keys}
    dest=RAW/'realizations';dest.mkdir(exist_ok=False);indices=CORE/'complete_bank_indices';indices.mkdir(exist_ok=False)
    for job in reg['jobs']:
        origin=physical/'realizations'/job['job_id'];d=dest/job['job_id'];d.mkdir();(d/'snapshots').mkdir()
        for p in origin.iterdir():
            if p.is_file():
                if p.name=='ALL_FRAME_SHA256_AND_TIME.csv':shutil.copyfile(p,indices/(job['job_id']+'.csv'))
                else:shutil.copyfile(p,d/p.name)
        lines=rows(origin/'QUERY_PHYSICAL_LINEAGE.csv');exposure=collections.Counter(int(r['frame']) for r in lines);knownsum=collections.Counter();particle_total=0;features=[]
        for frame,count in sorted(exposure.items()):
            src=origin/'bank'/f'iteration_{frame}';dd=d/'snapshots'/src.name;shutil.copyfile(src,dd)
            desc=raw.snapshot(src);f=desc['filaments'];cell,feature=models.physical_features(f);particle_total+=len(f)*count
            if len(f):features.append(feature)
            for key,spec in frozen.items():
                cl=models.route(feature,spec);kk=models.state_keys(cell,cl);n=sum(tuple(map(int,k)) in lookup[key] for k in kk);knownsum[key]+=n*count
            files.append(dict(job_id=job['job_id'],role=job['role'],frame=frame,exposure=count,source_path=str(src),support_path=dd.relative_to(RAW).as_posix(),SHA256=sha(dd),bytes=dd.stat().st_size,particle_records=len(f),physical_time_s=float(next(r['actual_s'] for r in lines if int(r['frame'])==frame))))
        ranges=np.concatenate(features) if features else np.empty((0,4))
        for key,spec in frozen.items():
            M,name=key;lo=np.min(ranges,axis=0).tolist() if len(ranges) else ['NA_EMPTY']*4;hi=np.max(ranges,axis=0).tolist() if len(ranges) else ['NA_EMPTY']*4
            coverage.append(dict(job_id=job['job_id'],role=job['role'],M=M,method=name,total_particle_exposure=particle_total,known_particle_exposure=knownsum[key],unknown_fraction=1-knownsum[key]/particle_total if particle_total else 'NA_EMPTY',feature_order='within_cell_x,within_cell_y,z_m,sigma_cm',feature_min=json.dumps(lo),feature_max=json.dumps(hi),hidden_states_used_for_source_inference=False,evaluation_only=True,stable_cross_frame_particle_ID=False))
        costs.append(dict(stage='generation_including_snapshot_save',job_id=job['job_id'],method='shared physical bank',wall_s=next(r['generation']['wall_s'] for r in gen['records'] if r['job_id']==job['job_id']),generated_frames=1803))
        costs.append(dict(stage='native_F_scalar_matrix_once_including_playback_and_IO',job_id=job['job_id'],method='F_shared',wall_s=next(r['native_response']['wall_s'] for r in gen['records'] if r['job_id']==job['job_id']),queries=701,F_charged_per_source_infer=False))
    write(CORE/'state_coverage_by_realization.csv',coverage);write(RAW/'SELECTED_RAW_FRAME_INDEX.csv',files)
    dump(CORE/'FULL_BANK_PRESERVATION.json',dict(complete_bank_root=str(physical),generated_realizations=24,complete_frames=24*1803,selected_raw_frames=len(files),all_unselected_files_preserved=True,complete_hash_time_indices_directory='complete_bank_indices',not_uploaded_to_Git=True,parent_banks_overwritten=False))
    for r in load(CORE/'LOCAL_RUNTIME_LEDGER.json'):costs.append(dict(stage='whole_'+r['stage'],method='shared or stage-specific',wall_s=r['wall_s'],peak_RSS_bytes=r['sampled_process_tree_peak_RSS_bytes'],includes_subrows_not_additive=True))
    for row in rows(CORE/'REFERENCE_CACHE_COSTS.csv'):costs.append(dict(stage=row['stage'],job_id=row['job_id'],method='shared native particle cache',wall_s=float(row['wall_s'])+float(row['parse_wall_s']),queries=row['queries'],includes_subrows_not_additive=True))
    methods=[]
    for M in [2,4]:
        meta=load(CORE/f'M{M}/MODEL_METADATA.json');read=rows(CORE/f'M{M}/READOUT_COSTS.csv');fit=load(CORE/f'M{M}/MODEL_STATUS.json')['fit_search_and_forecast_wall_s']
        for name in load(CORE/f'M{M}/MODEL_STATUS.json')['methods']:
            rr=[r for r in read if r['method']==name];cap=meta[name]['capacity'] if name in meta else {}
            costs.append(dict(stage='candidate_readout_on_own_reference_states',M=M,method=name,wall_s=sum(float(r['readout_wall_s']) for r in rr),fallback_wall_s=sum(float(r['fallback_wall_s']) for r in rr),route_wall_s=sum(float(r['route_wall_s']) for r in rr),decode_wall_s=sum(float(r['decode_wall_s']) for r in rr),queries=len(rr),F_charged_per_source_infer=False,includes_subrows_not_additive=True))
            methods.append(dict(M=M,method=name,reference_queries=len(rr),readout_wall_s=sum(float(r['readout_wall_s']) for r in rr),fallback_wall_s=sum(float(r['fallback_wall_s']) for r in rr),fallback_particles=sum(int(r['fallback_particles']) for r in rr),all_particles=sum(int(r['particles']) for r in rr),canonical_model_bytes=cap.get('canonical_total_bytes','NA_F_SCALAR_CACHE'),runtime_model_bytes=cap.get('runtime_NPZ_bytes','NA_F_SCALAR_CACHE'),actual_runtime_object_bytes=cap.get('actual_minimal_runtime_object_bytes','NA_F_SCALAR_CACHE'),shared_fit_search_and_forecast_wall_s=fit,native_Cpp_F_cost_shared_across_methods=True,Python_to_Cpp_speedup_claim=False))
    costs.extend(rows(CORE/'runtime_infer_costs.csv'));write(CORE/'runtime_costs.csv',costs);write(CORE/'METHOD_COST_AND_STORAGE.csv',methods)
    dump(CORE/'EXPORT_SUPPORT_LEDGER.json',dict(wall_s=time.perf_counter()-begin,selected_raw_bytes=sum(r['bytes'] for r in files),coverage_only_no_hidden_state_predictions=True,source_blind_result_reverified=True,generated_or_fitted_new_model=False,complete_bank_gas_bytes=sum(p.stat().st_size for p in physical.rglob('*') if p.is_file())))
    print(json.dumps(load(CORE/'EXPORT_SUPPORT_LEDGER.json'),indent=2))
if __name__=='__main__':main()
