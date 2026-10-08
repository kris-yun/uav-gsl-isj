"""E2 qualification only. Frozen gates; no posterior/material-effect verdict."""
from pathlib import Path
import csv,hashlib,json,math
import numpy as np
from scipy.special import ndtr
R=Path(__file__).resolve().parent;F=R.parent/'m0_clean_support_r0_20261007';DATA=R/'evidence'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def rows(p,delimiter=','):
    with Path(p).open(encoding='utf-8') as f:return list(csv.DictReader(f,delimiter=delimiter))
def write(n,x):(R/n).write_bytes((json.dumps(x,indent=2)+'\n').encode())
def csvout(n,data):
    with (R/n).open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]),lineterminator='\n');w.writeheader();w.writerows(data)
def verify_inputs():
    for q in rows(F/'M0_R0_FILES_SHA256.csv'):assert sha(F/q['path'])==q['sha256']
    seal=read(R/'E2_EXECUTION_SEAL.json')
    for name,h in seal['scripts_sha256'].items():assert sha(R/name)==sha(DATA/name)==h,(name,'sealed code')
    for q in rows(DATA/'E1_REFERENCE_HASHES.csv'):assert sha(DATA/q['archived_path'])==q['sha256']
    if (DATA/'NATIVE_ALL_FILES_SHA256.csv').exists():
        for q in rows(DATA/'NATIVE_ALL_FILES_SHA256.csv'):assert sha(DATA/q['path'])==q['sha256']
    A=read(R/'M0_E2_AUTHORIZATION.json');assert A['allowed_run_ids']==[q['run_id'] for q in read(DATA/'E2_COMPLETED_RUNS.json')]
    assert not A['E3_authorized'] and read(DATA/'E2_PROGRESS.json')['completed']==4 and read(DATA/'E2_PROGRESS.json')['E3_runs']==0
verify_inputs();D=read(F/'M0_DOMAIN_ROI_GUARD_CONTRACT.json');S=read(F/'M0_SOURCE_CONTRACT.json');P=read(F/'M0_PERTURBATION_CONTRACT.json');Q=D['qualification'];PRE=read(DATA/'E2_PREQUALIFICATION.json');M=read(DATA/'E2_ASSET_MANIFEST.json');RUNS=read(DATA/'E2_COMPLETED_RUNS.json')
lo=np.array(D['effective_outlet_inner_planes_m']['min']);hi=np.array(D['effective_outlet_inner_planes_m']['max']);requests=np.array(S['clock']['score_times_s']);band=D['true_boundary_band_m'];ref=DATA/'reference/audit'
ref_frames=rows(ref/'native_frames.csv');ref_states=np.fromfile(ref/'filament_states.f32',dtype='<f4').reshape(-1,4);ref_route=rows(ref/'route.csv');route_geom=rows(F/'M0_UAV_ROUTE_POINTS.csv')
t=np.float32(0);last=np.float32(-np.inf);dt=np.float32(S['clock']['time_step_s']);save=np.float32(S['clock']['results_time_step_s']);tick=0;expected=[];sigma=np.float32(S['release']['filament_initial_std_cm']);age=[sigma]
while t<np.float32(S['clock']['sim_time_s']):
    tick+=1;sigma=np.float32(sigma+np.float32(np.float32(15)/np.float32(2*sigma)*dt));age.append(sigma)
    if t>np.float32(last+save):expected.append([len(expected),float(t),tick,0]);last=t
    t=np.float32(t+dt)
terminal=float(t);ages=np.array(age,dtype=np.float32);reports=[];all_records=[];certificates=[];failures=[];descriptive=[]
for run in RUNS:
    rid=run['run_id'];arm=run['wind_arm'];folder=DATA/'audit'/rid;result=DATA/'projects'/arm/'simulations'/rid/'result';frames=rows(folder/'native_frames.csv');states=np.fromfile(folder/'filament_states.f32',dtype='<f4').reshape(-1,4);timeline=rows(result/'RECORD_TIMELINE.tsv','\t');clock=[];metrics=[];sigmahash=hashlib.sha256();same_sigma=True;age_ok=True;count_ok=True
    assert len(frames)==len(ref_frames)==len(expected)==len(timeline)==246
    for fr,b,tm,exp in zip(frames,ref_frames,timeline,expected):
        idx=int(fr['record_index']);ts=float(fr['time_s']);n=int(fr['n_filaments']);offset=int(fr['offset_filaments']);a=states[offset:offset+n];rb=ref_states[int(b['offset_filaments']):int(b['offset_filaments'])+int(b['n_filaments'])]
        assert np.isfinite(a).all() and (a[:,3]>0).all();clock.append([idx,ts,n,int(fr['wind_index'])]);count_ok=count_ok and n==exp[2]
        same_sigma=same_sigma and np.array_equal(a[:,3],rb[:,3]);age_ok=age_ok and np.array_equal(a[:,3],ages[exp[2]:0:-1]);sigmahash.update(a[:,3].tobytes())
        assert idx==int(tm['record_index']) and ts==float(tm['internal_simulation_time_s']) and int(tm['wind_index'])==0
        xyz=a[:,:3].astype(float);sd=a[:,3,None].astype(float)/100;dist=np.concatenate([xyz-lo,hi-xyz],axis=1);margins=dist-3*np.concatenate([sd]*6,axis=1);centroid=xyz.mean(axis=0)
        def box(bl,bh):return np.prod(ndtr((bh-xyz)/sd)-ndtr((bl-xyz)/sd),axis=1).mean()
        whole=box(lo,hi);inner=box(lo+band,hi-band);facefr=[]
        for axis in range(3):
            fl=lo.copy();fh=hi.copy();fh[axis]=lo[axis]+band;facefr.append(float(box(fl,fh)/whole))
            fl=lo.copy();fh=hi.copy();fl[axis]=hi[axis]-band;facefr.append(float(box(fl,fh)/whole))
        record={'run_id':rid,'record_index':idx,'time_s':ts,'filament_count':n,'expected_released':exp[2],'release_deficit':exp[2]-n,'min_3sigma_outlet_margin_m':float(margins.min()),'centroid_clearance_m':float(min(np.r_[centroid-lo,hi-centroid])),'all6_band_mass_fraction':float(max(0,whole-inner)/whole),'outside_Gaussian_mass_fraction':float(1-whole),'ROI_mass_fraction':float(box(np.array(D['analysis_roi_m']['min']),np.array(D['analysis_roi_m']['max']))),'centroid_x':float(centroid[0]),'centroid_y':float(centroid[1]),'centroid_z':float(centroid[2])}
        for k,v in zip(['x_min','x_max','y_min','y_max','z_min','z_max'],facefr):record[k+'_1m_band_mass_fraction']=v
        for j,k in enumerate(['x_min','y_min','z_min','x_max','y_max','z_max']):record[k+'_3sigma_margin_m']=float(margins[:,j].min())
        metrics.append(record);all_records.append(record)
    ref_clock=[[int(f['record_index']),float(f['time_s']),int(f['n_filaments']),int(f['wind_index'])] for f in ref_frames]
    clock_same=clock==ref_clock==expected;times=np.array([f['time_s'] for f in metrics]);indices=np.searchsorted(times,requests,side='right')-1;selected=[metrics[j] for j in indices];lags=requests-times[indices]
    assert (indices>=0).all() and max(lags)<=.61
    gap=max(float(np.diff(times).max()),terminal-times[-1]);gmax=PRE['noise_table'][arm]['max_abs'];maxwind=PRE['wind_readback'][arm]['max_speed']
    # Actual cyclic Gaussian table, actual wind maximum, conservative native CO buoyancy bound.
    bound=float((maxwind+.1*gmax+.012)*(gap+1e-6));margin=min(f['min_3sigma_outlet_margin_m'] for f in metrics);tail_safe=gap<=.610001 and margin>bound
    source=np.array([0.,-1.,5.]);source_clearance=float(min(np.r_[source-lo,hi-source]));bands=np.array([f['all6_band_mass_fraction'] for f in selected]);centclear=min(f['centroid_clearance_m'] for f in metrics)
    log=(folder/'simulation.stdout.log').read_text(errors='replace');exceptions=any(s in log for s in ['Exception Updating Filaments','Could not spawn','SERIOUS','Requested wind vector at a point outside','Filament is outside environment'])
    table_hash=sha(DATA/'noise'/arm);table_same=table_hash==read(R/'PARENT_E0_QUALIFICATION.json')['native_noise_table_bounds']['2026100701']['table_sequence_sha256']
    support=margin>=Q['every_record_min_filament_3sigma_margin_to_outlet_m'] and centclear>=Q['centroid_min_clearance_to_effective_outlet_m'] and source_clearance>=Q['source_min_clearance_to_outlet_m'] and bands.mean()<=Q['band_mean_mass_fraction_max'] and np.quantile(bands,.95,method='linear')<=Q['band_mass_fraction_q95_max'] and count_ok and tail_safe and not exceptions
    crn=clock_same and same_sigma and age_ok and count_ok and table_same and support and not exceptions
    obs=rows(folder/'route.csv');assert len(obs)==51
    route_same=all(float(o['time_s'])==int(tm) and int(o['record_index'])==int(ref_route[j]['record_index']) and np.allclose([float(o[k]) for k in ['x','y','z']],[float(route_geom[j][k]) for k in ['x_m','y_m','z_m']],atol=1e-6,rtol=0) for j,(o,tm) in enumerate(zip(obs,requests)))
    concentration=np.array([float(o['ppm']) for o in obs]);assert np.isfinite(concentration).all() and (concentration>=0).all()
    parity=rows(folder/'sampling_parity.csv');parity_ok=len(parity)>=51*25 and all(float(q['absolute_difference'])<=1e-5*(1+abs(float(q['native']))) for q in parity);maxdiff=max(float(q['absolute_difference']) for q in parity)
    wind_same=sha(DATA/'projects'/arm/'wind/wind_iteration_0')==sha(DATA/'native_readback'/arm/'native_readback.wind')==P['expected_modern_wind_sha256'][arm]==run['wind_sha256']
    rep={'run_id':rid,'arm':arm,'records':len(frames),'clock_bit_identical_to_U0':clock_same,'release_count_identical_to_U0':count_ok,'birth_order_sigma_bit_identical_to_U0':same_sigma,'sigma_age_recurrence_bit_identity':age_ok,'sigma_sequence_sha256':sigmahash.hexdigest(),'noise_table_sha256':table_hash,'RNG_table_identical_to_U0':table_same,'RNG_draws_per_live_filament_per_tick':3,'RNG_total_draw_assignment_count':3*tick*(tick+1)//2,'deletion_count_certified':0 if count_ok and tail_safe and not exceptions else None,'native_position_exceptions':exceptions,'all_record_min_3sigma_margin_m':margin,'all_record_min_centroid_clearance_m':centclear,'source_clearance_m':source_clearance,'all6_band_mean':float(bands.mean()),'all6_band_q95':float(np.quantile(bands,.95,method='linear')),'max_between_save_or_terminal_gap_s':gap,'max_axis_gap_displacement_bound_m':bound,'last_saved_time_s':float(times[-1]),'terminal_native_time_s':terminal,'max_alignment_lag_s':float(lags.max()),'route_coordinate_and_record_identity':route_same,'route_detectable_samples_descriptive_only':int((concentration>=.1).sum()),'native_parity_checks':len(parity),'native_parity_max_abs_difference':maxdiff,'wind_hash_matches_E0':wind_same,'support_pass':bool(support),'CRN_pass':bool(crn),'sampling_parity_pass':bool(parity_ok)}
    for k in ['x_min','x_max','y_min','y_max','z_min','z_max']:
        vals=np.array([f[k+'_1m_band_mass_fraction'] for f in selected]);rep[k+'_band_mean']=float(vals.mean());rep[k+'_band_q95']=float(np.quantile(vals,.95,method='linear'));rep[k+'_all_record_3sigma_margin_m']=min(f[k+'_3sigma_margin_m'] for f in metrics)
    reports.append(rep);certificates.append({'run_id':rid,'clock':clock,'paired_U0_clock_identical':clock_same,'sigma_birth_order_matched':same_sigma,'full_sigma_age_arrays_matched':age_ok,'draw_call_assignment_control_flow':crn,'no_retry_or_deletion_branch':support,'certificate_type':'Pinned native source and runtime, fixed point emissions, every-saved-record count/sigma, all interval and terminal-tail displacement bound; not an instrumented per-tick RNG/deletion trace.'})
    for name,ok in [('SUPPORT',support),('RNG',crn),('SAMPLING_PARITY',parity_ok),('ROUTE',route_same),('WIND_HASH',wind_same)]:
        if not ok:failures.append(rid+':M0_'+name+'_HOLD')
    y0=np.array([float(q['ppm']) for q in ref_route]);f0=np.stack([np.fromfile(ref/('roi_column_t'+str(int(tm))+'.f32'),dtype='<f4') for tm in requests]).astype(float);fm=np.stack([np.fromfile(folder/('roi_column_t'+str(int(tm))+'.f32'),dtype='<f4') for tm in requests]).astype(float);den=.5*(np.linalg.norm(f0)+np.linalg.norm(fm));df=float(np.linalg.norm(fm-f0)/den) if den>0 else 0
    descriptive.append({'run_id':rid,'D_F_descriptive':df,'D_Y_descriptive':float(np.sqrt(np.mean((np.log1p(concentration)-np.log1p(y0))**2))),'true_observation_U0_route_sha256':sha(ref/'route.csv'),'posterior_damage':'NOT_COMPUTED_E2_LIBRARY_INCOMPLETE','interpretation':'Paired forward QC only; no material effect, direction selection, M0_PASS or algorithm claim.'})
elapsed=read(DATA/'E2_PROGRESS.json')['wall_s'];rss=max(max(r['sim_peak_RSS_bytes'],r['extraction_peak_RSS_bytes']) for r in RUNS);allbytes=sum(p.stat().st_size for p in DATA.rglob('*') if p.is_file());q95=float(np.quantile([r['sim_wall_s']+r['extraction_wall_s'] for r in RUNS],.95,method='linear'));projection=1800+3*q95*28+elapsed+read(R/'PARENT_E1_DECISION.json')['resources']['wall_all8_s'];bytes_projection=allbytes+read(R/'PARENT_E1_DECISION.json')['resources']['current_evidence_input_output_bytes']+28*max(r['output_bytes'] for r in RUNS)
resource_ok=rss<=2*1024**3 and projection<=10800 and bytes_projection<=5*1024**3
if not resource_ok:failures.append('M0_RESOURCE_HOLD')
resource={'E2_campaign_wall_s':elapsed,'max_RSS_bytes':rss,'E2_input_output_bytes':allbytes,'remaining_28_projected_total_wall_s_with_safety':projection,'projected_total_bytes':bytes_projection,'resource_gate_pass':resource_ok}
csvout('E2_ALL_RECORD_SUPPORT.csv',all_records);csvout('E2_SENTINEL_SUMMARY.csv',reports);write('E2_CRN_CERTIFICATE.json',{'native_total_ticks':tick,'terminal_clock_s':terminal,'total_draw_call_assignments_per_run':3*tick*(tick+1)//2,'reference_id':'m0r0_U0_S0_r01','records_per_run':246,'paired_runs':certificates,'claimed_instrumented_rng_trace':False,'unrun_28_alignment_not_yet_tested':True})
write('E2_DESCRIPTIVE_FORWARD_QC.json',descriptive);write('E2_RESOURCE_AUDIT.json',resource)
decision={'verdict':'M0_E2_CRN_SENTINEL_QUALIFIED' if not failures else 'M0_E2_PREREQUISITE_HOLD','failures':failures,'stage':'E2_ONLY','new_U0_runs':0,'new_wrong_wind_runs':4,'total_M0_runs_completed':12,'remaining_wrong_wind_runs':28,'remaining_28_authorized':False,'remaining_28_launched':False,'R0_unchanged':True,'E1_unchanged':True,'scientific_M0_verdict':'NOT_TESTED','posterior_material_effect':'NOT_TESTED','no_threshold_or_design_adjustment':True,'STOP_now':True,'resources':resource}
write('E2_DECISION.json',decision);print(json.dumps(decision,indent=2))
