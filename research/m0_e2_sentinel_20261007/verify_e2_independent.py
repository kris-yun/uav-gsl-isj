"""Independent E2 raw/hash and stable-tail verification, no simulation."""
from pathlib import Path
import csv,hashlib,json,math
import numpy as np
from scipy.special import erfc
R=Path(__file__).resolve().parent;F=R.parent/'m0_clean_support_r0_20261007';D=R/'evidence'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def rows(p,delimiter=','):
    with Path(p).open(encoding='utf-8') as f:return list(csv.DictReader(f,delimiter=delimiter))
for q in rows(F/'M0_R0_FILES_SHA256.csv'):assert sha(F/q['path'])==q['sha256']
allhash=rows(D/'NATIVE_ALL_FILES_SHA256.csv')
for q in allhash:assert sha(D/q['path'])==q['sha256'] and (D/q['path']).stat().st_size==int(q['bytes']),q['path']
for q in rows(D/'E1_REFERENCE_HASHES.csv'):assert sha(D/q['archived_path'])==q['sha256']
seal=read(R/'E2_EXECUTION_SEAL.json')
for name,h in seal['scripts_sha256'].items():assert sha(R/name)==sha(D/name)==h
A=read(R/'M0_E2_AUTHORIZATION.json');PRE=read(D/'E2_PREQUALIFICATION.json');DEC=read(R/'E2_DECISION.json');RUNS=read(D/'E2_COMPLETED_RUNS.json');summary=rows(R/'E2_SENTINEL_SUMMARY.csv');domain=read(F/'M0_DOMAIN_ROI_GUARD_CONTRACT.json');P=read(F/'M0_PERTURBATION_CONTRACT.json');PARENT=read(R/'PARENT_ASSET_MANIFEST.json');E0=read(R/'PARENT_E0_QUALIFICATION.json')
assert [q['run_id'] for q in RUNS]==A['allowed_run_ids'] and len(RUNS)==4 and not A['E3_authorized']
assert read(D/'E2_PROGRESS.json')['completed']==4 and read(D/'E2_PROGRESS.json')['E3_runs']==0
assert PRE['status']=='E2_RUNTIME_PREREQUISITES_PASS' and PRE['original_E1_native_files_verified']==2551
lo=np.array(domain['effective_outlet_inner_planes_m']['min']);hi=np.array(domain['effective_outlet_inner_planes_m']['max']);ref=D/'reference/audit';refframes=rows(ref/'native_frames.csv');refdata=np.fromfile(ref/'filament_states.f32',dtype='<f4').reshape(-1,4)
ref_obs=rows(ref/'route.csv');request=list(range(20,121,2));refcolumns=np.array([np.fromfile(ref/('roi_column_t'+str(tm)+'.f32'),dtype='<f4') for tm in request],dtype=float);y0=np.array([float(q['ppm']) for q in ref_obs]);proof=[];maxmargin=0.;qc_diff=0.;descriptive=read(R/'E2_DESCRIPTIVE_FORWARD_QC.json');parity_count=0;fail=[]
simcfgsha=next(q['sha256'] for q in PARENT['asset_files'] if q['path']=='projects/U0/simulations/m0r0_U0_S0_r01/sim.yaml')
for run,q in zip(RUNS,summary):
    rid=run['run_id'];arm=run['wind_arm'];folder=D/'audit'/rid;fr=rows(folder/'native_frames.csv');data=np.fromfile(folder/'filament_states.f32',dtype='<f4').reshape(-1,4);result=D/'projects'/arm/'simulations'/rid/'result';native_time=rows(result/'RECORD_TIMELINE.tsv','\t')
    assert len(fr)==len(native_time)==len(refframes)==246
    assert sha(D/'projects'/arm/'simulations'/rid/'sim.yaml')==simcfgsha
    assert sha(D/'projects'/arm/'wind/wind_iteration_0')==sha(D/'native_readback'/arm/'native_readback.wind')==P['expected_modern_wind_sha256'][arm]
    assert run['generator_sha256']==E0['generator_sha256'] and run['libgaden_sha256']==E0['libgaden_sha256']
    assert run['native_helper_sha256']==read(R/'PARENT_E1_HELPER_BUILD.json')['binary_sha256']
    assert run['runtime_env']['GADEN_RNG_SEED']=='2026100701' and run['runtime_env']['OMP_NUM_THREADS']=='1'
    assert run['master_seed']==2026100701 and run['source_id']=='S0' and run['realization']==1
    for h in rows(folder/'RAW_OUTPUT_SHA256.csv'):assert sha(D/h['path'])==h['sha256']
    sigma_hash=hashlib.sha256();low=math.inf;tail=[];times=[];counts=[]
    for row,baseline,tm in zip(fr,refframes,native_time):
        assert [row[k] for k in ['record_index','time_s','wind_index','n_filaments','offset_filaments']]==[baseline[k] for k in ['record_index','time_s','wind_index','n_filaments','offset_filaments']]
        assert float(tm['internal_simulation_time_s'])==float(row['time_s']) and int(tm['record_index'])==int(row['record_index']) and int(tm['wind_index'])==0
        off=int(row['offset_filaments']);n=int(row['n_filaments']);a=data[off:off+n];b=refdata[off:off+n];assert np.array_equal(a[:,3],b[:,3]);sigma_hash.update(a[:,3].tobytes());counts.append(n)
        xyz=a[:,:3].astype(float);s=a[:,3,None].astype(float)/100;distance=np.minimum(xyz-lo,hi-xyz)-3*s;low=min(low,float(distance.min()));times.append(float(row['time_s']))
        outer=.5*erfc((xyz-lo)/(s*math.sqrt(2)))+.5*erfc((hi-xyz)/(s*math.sqrt(2)))
        inset=.5*erfc((xyz-(lo+1))/(s*math.sqrt(2)))+.5*erfc(((hi-1)-xyz)/(s*math.sqrt(2)))
        tail.append(float(inset.sum(axis=1).mean()/(1-outer.sum(axis=1).mean())))
    chosen=[max(i for i,t in enumerate(times) if t<=tm) for tm in request];bounds=np.array(tail)[chosen];maxmargin=max(maxmargin,abs(low-float(q['all_record_min_3sigma_margin_m'])));assert low>=1 and bounds.mean()<=.05 and np.quantile(bounds,.95,method='linear')<=.10
    assert sigma_hash.hexdigest()==q['sigma_sequence_sha256'];assert sha(D/'noise'/arm)==E0['native_noise_table_bounds']['2026100701']['table_sequence_sha256']
    actual_max=float(abs(np.fromfile(D/'noise'/arm,dtype='<f4')).max());gap=max(max(times[i+1]-times[i] for i in range(len(times)-1)),140.09934997558594-times[-1]);motion=(PRE['wind_readback'][arm]['max_speed']+.1*actual_max+.012)*(gap+1e-6);assert low>motion
    assert int(q['deletion_count_certified'])==0 and q['native_position_exceptions']=='False' and q['CRN_pass']=='True' and q['support_pass']=='True'
    log=(folder/'simulation.stdout.log').read_text(errors='replace');assert not any(s in log for s in ['Exception Updating Filaments','Could not spawn','SERIOUS','Filament is outside environment'])
    obs=rows(folder/'route.csv');assert len(obs)==51
    for row,b in zip(obs,ref_obs):assert all(row[k]==b[k] for k in ['time_s','record_index','x','y','z'])
    parity=rows(folder/'sampling_parity.csv');assert len(parity)>=1275 and all(float(a['absolute_difference'])<=1e-5*(1+abs(float(a['native']))) for a in parity);parity_count+=len(parity)
    col=np.array([np.fromfile(folder/('roi_column_t'+str(tm)+'.f32'),dtype='<f4') for tm in request],dtype=float);difference=col.ravel()-refcolumns.ravel();norm=lambda x:math.sqrt(float(np.dot(x.ravel(),x.ravel())));df=norm(difference)/(.5*(norm(col)+norm(refcolumns)));ym=np.array([float(a['ppm']) for a in obs]);dy=math.sqrt(sum((math.log1p(float(a))-math.log1p(float(b)))**2 for a,b in zip(ym,y0))/51);v=next(d for d in descriptive if d['run_id']==rid);qc_diff=max(qc_diff,abs(df-v['D_F_descriptive']),abs(dy-v['D_Y_descriptive']))
    proof.append({'run_id':rid,'matched_clock_release_sigma_and_noise_table':True,'minimum_3sigma_margin_m':low,'stable_all6_band_mean_upper_bound':float(bounds.mean()),'stable_all6_band_q95_upper_bound':float(np.quantile(bounds,.95,method='linear')),'max_all_saved_record_band_upper_bound':max(tail),'between_save_terminal_motion_bound_m':motion,'deletion_count_certified':0,'native_parity_checks':len(parity)})
assert maxmargin<1e-12 and qc_diff<1e-12
for a,b in [('A_on','A_off'),('B_shear','B_speed')]:
    for key in ['global_vector_RMSE','ROI_vector_RMSE']:
        x,y=PRE['wind_readback'][a][key],PRE['wind_readback'][b][key];assert x>0 and y>0 and abs(x-y)<=1e-7 and abs(x-y)/max(x,y)<=1e-4
assert DEC['verdict']=='M0_E2_CRN_SENTINEL_QUALIFIED' and DEC['failures']==[] and not DEC['remaining_28_launched'] and DEC['scientific_M0_verdict']=='NOT_TESTED'
out={'status':'INDEPENDENT_E2_VERIFICATION_PASS','native_files_verified':len(allhash),'frozen_R0_files_verified':39,'four_sentinel_runs_verified':4,'new_baseline_runs':0,'remaining_28_runs':0,'margin_max_difference_m':maxmargin,'descriptive_forward_QC_max_difference':qc_diff,'native_sampling_queries_verified':parity_count,'all_cross_wind_CRN_prerequisites':True,'per_arm':proof,'zero_deletion_is_invariant_certificate_not_tick_counter':True,'material_effect_or_M0_PASS':'NOT_TESTED','STOP':True}
(R/'INDEPENDENT_E2_VERIFICATION.json').write_bytes((json.dumps(out,indent=2)+'\n').encode());print(json.dumps(out,indent=2))
