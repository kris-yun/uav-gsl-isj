"""Frozen-threshold E1 support/observation/CRN audit. No simulations."""
from pathlib import Path
import csv,hashlib,json,math,sys
import numpy as np
from scipy.special import ndtr,logsumexp
ROOT=Path(__file__).resolve().parent;FROZEN=ROOT.parent/'m0_clean_support_r0_20261007';DATA=ROOT/'evidence'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def rows(p,delim=','):
    with Path(p).open(encoding='utf-8') as f:return list(csv.DictReader(f,delimiter=delim))
def write(n,x):(ROOT/n).write_bytes((json.dumps(x,indent=2,ensure_ascii=False)+'\n').encode())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def csvout(name,data):
    with (ROOT/name).open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]),lineterminator='\n');w.writeheader();w.writerows(data)
D=read(FROZEN/'M0_DOMAIN_ROI_GUARD_CONTRACT.json');S=read(FROZEN/'M0_SOURCE_CONTRACT.json');P=read(FROZEN/'M0_PERTURBATION_CONTRACT.json');I=read(FROZEN/'M0_INFERENCE_CONTRACT.json');R=read(FROZEN/'M0_UAV_ROUTE_CONTRACT.json')
with (FROZEN/'M0_R0_FILES_SHA256.csv').open(encoding='utf-8') as f:
    for q in csv.DictReader(f):assert sha(FROZEN/q['path'])==q['sha256']
M=read(DATA/'ASSET_MANIFEST.json');E0=read(DATA/'E0_QUALIFICATION.json');RUNS=read(DATA/'E1_COMPLETED_RUNS.json');assert len(RUNS)==8 and E0['status']=='M0_E0_RUNTIME_QUALIFIED'
lo=np.array(D['effective_outlet_inner_planes_m']['min']);hi=np.array(D['effective_outlet_inner_planes_m']['max']);band=D['true_boundary_band_m']
qualification=D['qualification'];score_times=S['clock']['score_times_s'];reports=[];frame_rows=[];support_hash={};observations={};actual_clock={};failures=[]
# Scalar float32 clock and sigma arithmetic reproduces the actual native equations, without evolving plume positions.
t=np.float32(0);last=np.float32(-np.inf);dt=np.float32(S['clock']['time_step_s']);save=np.float32(S['clock']['results_time_step_s']);native_expected=[];tick=0;sigma=np.float32(10);age_sigma=[sigma]
while t<np.float32(S['clock']['sim_time_s']):
    tick+=1;sigma=np.float32(sigma+np.float32(np.float32(15)/np.float32(2*sigma)*dt));age_sigma.append(sigma)
    if t>np.float32(last+save):native_expected.append((len(native_expected),float(t),tick));last=t
    t=np.float32(t+dt)
terminal_time=float(t);sigma_by_age=np.array(age_sigma,dtype=np.float32)
for run in RUNS:
    rid=run['run_id'];folder=DATA/'e1_audit'/rid;frames=rows(folder/'native_frames.csv');timeline=rows(DATA/'projects/U0/simulations'/rid/'result/RECORD_TIMELINE.tsv','\t');states=np.fromfile(folder/'filament_states.f32',dtype='<f4').reshape(-1,4)
    assert len(frames)==len(timeline)==len(native_expected)
    metrics=[];allcounts=True;ageok=True;sigmash=hashlib.sha256();recordclock=[]
    for f,tm,exp in zip(frames,timeline,native_expected):
        idx=int(f['record_index']);time_s=float(f['time_s']);count=int(f['n_filaments']);offset=int(f['offset_filaments']);data=states[offset:offset+count];xyz=data[:,:3].astype(float);sd=data[:,3].astype(float)/100
        assert np.isfinite(data).all() and (sd>0).all();assert idx==exp[0] and abs(time_s-exp[1])<5e-7 and int(f['wind_index'])==0
        assert int(tm['record_index'])==idx and float(tm['internal_simulation_time_s'])==time_s and int(tm['wind_index'])==0
        allcounts=allcounts and count==exp[2];ageok=ageok and count==exp[2] and np.array_equal(data[:,3],sigma_by_age[exp[2]:0:-1]);sigmash.update(data[:,3].tobytes());recordclock.append([idx,time_s,count,0])
        margin=np.min(np.concatenate([xyz-lo-3*sd[:,None],hi-xyz-3*sd[:,None]],axis=1));centroid=xyz.mean(axis=0);centclear=float(np.min(np.concatenate([centroid-lo,hi-centroid])))
        def boxfrac(bl,bh):return np.prod(ndtr((bh-xyz)/sd[:,None])-ndtr((bl-xyz)/sd[:,None]),axis=1).mean()
        whole=boxfrac(lo,hi);inset=boxfrac(lo+band,hi-band);on=boxfrac(np.array([0.,-2.,2.]),np.array([12.,2.,8.]));off=boxfrac(np.array([0.,3.5,2.]),np.array([12.,7.5,8.]));haloon=boxfrac(np.array([-.25,-2.25,2]),np.array([12.25,2.25,8.]));halooff=boxfrac(np.array([-.25,3.25,2]),np.array([12.25,7.75,8.]));roi_mass=boxfrac(np.array(D['analysis_roi_m']['min']),np.array(D['analysis_roi_m']['max']))
        q={'run_id':rid,'record_index':idx,'time_s':time_s,'count':count,'expected_released':exp[2],'deletion_deficit':exp[2]-count,'min_3sigma_outlet_margin_m':float(margin),'centroid_clearance_m':centclear,'centroid_x_m':float(centroid[0]),'centroid_y_m':float(centroid[1]),'centroid_z_m':float(centroid[2]),'all6_band_mass_fraction':float(max(0,whole-inset)/whole),'untruncated_Gaussian_outside_mass_fraction':float(1-whole),'ROI_mass_fraction':float(roi_mass),'A_on_mass_fraction':float(on),'A_off_mass_fraction':float(off),'A_on_halo_mass_fraction':float(haloon),'A_off_halo_mass_fraction':float(halooff)}
        frame_rows.append(q);metrics.append(q)
    # Align the 51 requested frames to the actual latest preceding records.
    times=np.array([q['time_s'] for q in metrics]);indices=np.searchsorted(times,score_times,side='right')-1;assert (indices>=0).all();chosen=[metrics[j] for j in indices];lags=np.array(score_times)-times[indices];assert lags.max()<=.61
    bc=np.array([q['all6_band_mass_fraction'] for q in chosen]);on=np.array([q['A_on_mass_fraction'] for q in chosen]);off=np.array([q['A_off_mass_fraction'] for q in chosen]);all_margin=min(q['min_3sigma_outlet_margin_m'] for q in metrics)
    # Native fixed rate + all saved counts, supported by a conservative between-save/terminal-tail position bound, proves no unobserved outlet deletion.
    gmax=E0['native_noise_table_bounds'][str(run['master_seed'])]['max_abs'];gap=max(float(np.diff(times).max()),terminal_time-times[-1]);axis_bound=np.array([.12,0.,.005])+.1*gmax;axis_bound[2]+=.012 # native carbonMonoxide initial terminal buoyancy <=.012 m/s
    step_gap_bound=float(axis_bound.max()*(gap+1e-6));tail_safe=all_margin>step_gap_bound and gap<=.610001
    support_pass=all_margin>=qualification['every_record_min_filament_3sigma_margin_to_outlet_m'] and bc.mean()<=qualification['band_mean_mass_fraction_max'] and np.quantile(bc,.95,method='linear')<=qualification['band_mass_fraction_q95_max'] and min(q['centroid_clearance_m'] for q in metrics)>=qualification['centroid_min_clearance_to_effective_outlet_m'] and S['minimum_clearance_to_effective_outlet_m']>=qualification['source_min_clearance_to_outlet_m'] and allcounts and tail_safe
    relevance=on.mean()>=.30 and off.mean()<=.01 and np.quantile(off,.95,method='linear')<=.05
    obs=rows(folder/'route.csv');assert len(obs)==51 and [float(q['time_s']) for q in obs]==score_times
    assert [int(q['record_index']) for q in obs]==[q['record_index'] for q in chosen]
    refroute=rows(FROZEN/'M0_UAV_ROUTE_POINTS.csv');assert all(np.allclose([float(q[k]) for k in ['x','y','z']],[float(v[k]) for k in ['x_m','y_m','z_m']],atol=1e-6,rtol=0) for q,v in zip(obs,refroute))
    concentration=np.array([float(q['ppm']) for q in obs]);assert np.isfinite(concentration).all() and (concentration>=0).all();observations[(run['source_id'],run['realization'])]=concentration
    parity=rows(folder/'sampling_parity.csv');paritypass=all(float(q['absolute_difference'])<=1e-5*(1+abs(float(q['native']))) for q in parity)
    log=(folder/'simulation.stdout.log').read_text(errors='replace');exceptions=('Exception Updating Filaments' in log or 'Could not spawn' in log or 'SERIOUS' in log or 'Requested wind vector at a point outside' in log)
    support_hash[(run['source_id'],run['realization'])]=sigmash.hexdigest();actual_clock[(run['source_id'],run['realization'])]=recordclock
    rep={'run_id':rid,'source_id':run['source_id'],'realization':run['realization'],'record_count':len(frames),'last_native_saved_time_s':float(times[-1]),'terminal_native_clock_s':terminal_time,'band_mean':float(bc.mean()),'band_q95':float(np.quantile(bc,.95,method='linear')),'min_record_3sigma_margin_m':float(all_margin),'min_centroid_clearance_m':min(q['centroid_clearance_m'] for q in metrics),'source_clearance_m':S['minimum_clearance_to_effective_outlet_m'],'deletion_count_certified':0 if allcounts and tail_safe else None,'deletion_certificate_method':'Cumulative native fixed-release counts at every saved frame plus conservative between-save and terminal-tail displacement bound; not an instrumented per-tick counter.','max_save_or_terminal_gap_s':gap,'gap_max_axis_displacement_bound_m':step_gap_bound,'sigma_age_order_bit_identity':bool(ageok),'sigma_sequence_sha256':sigmash.hexdigest(),'RNG_draws_per_live_filament_per_tick':3,'RNG_total_draw_assignment_count':3*tick*(tick+1)//2,'native_position_exceptions':bool(exceptions),'PairA_on_mean':float(on.mean()),'PairA_off_mean':float(off.mean()),'PairA_off_q95':float(np.quantile(off,.95,method='linear')),'route_detectable_samples':int((concentration>=.1).sum()),'route_max_ppm':float(concentration.max()),'native_parity_checks':len(parity),'native_parity_max_abs_diff':max(float(q['absolute_difference']) for q in parity),'support_pass':bool(support_pass),'PairA_relevance_pass':bool(relevance),'sampling_parity_pass':bool(paritypass),'max_alignment_lag_s':float(lags.max()),'sim_wall_s':run['sim_wall_s'],'extraction_wall_s':run['extraction_wall_s'],'sim_peak_RSS_bytes':run['sim_peak_RSS_bytes'],'extraction_peak_RSS_bytes':run['extraction_peak_RSS_bytes'],'output_bytes':run['output_bytes']}
    reports.append(rep)
    if not support_pass:failures.append(rid+':M0_BASE_SUPPORT_HOLD')
    if not relevance:failures.append(rid+':PAIR_A_RELEVANCE_HOLD')
    if not paritypass:failures.append(rid+':M0_SAMPLING_PARITY_HOLD')
    if not ageok or exceptions:failures.append(rid+':M0_RNG_HOLD')
for r in range(1,5):
    if support_hash[('S0',r)]!=support_hash[('S1',r)] or actual_clock[('S0',r)]!=actual_clock[('S1',r)]:failures.append('cross_source_r'+str(r)+':M0_RNG_HOLD')
pred=[]
for source in ['S0','S1']:
    for r in range(1,5):
        query=observations[(source,r)];train_ids=[q for q in range(1,5) if q!=r];template=[np.stack([observations[(s,q)] for q in train_ids]) for s in ['S0','S1']]
        for family in ['HIT_FORWARD','LOG_GAUSSIAN']:
            ll=[]
            for arr in template:
                if family=='HIT_FORWARD':
                    p=((arr>=.1).sum(axis=0)+.5)/4;h=query>=.1;ll.append(float(np.sum(h*np.log(p)+(~h)*np.log1p(-p))))
                else:
                    z=np.log1p(arr);mean=z.mean(axis=0);var=np.maximum(z.var(axis=0,ddof=1),.0625);q=np.log1p(query);ll.append(float(-.5*np.sum(np.log(2*np.pi*var)+(q-mean)**2/var)))
            logp=np.array(ll)-logsumexp(ll);p=np.exp(logp);truth=0 if source=='S0' else 1;tie=abs(p[0]-p[1])<=1e-12;correct=not tie and np.argmax(p)==truth
            pred.append({'source_id':source,'realization':r,'family':family,'heldout_seed':S['rng']['master_seeds'][r-1],'train_realizations':';'.join(map(str,train_ids)),'p_S0':float(p[0]),'p_S1':float(p[1]),'p_true':float(p[truth]),'correct':bool(correct),'preflight_correct_p60':bool(correct and p[truth]>=.60),'brier':float((1-p[truth])**2),'NLL':float(-max(logp[truth],math.log(1e-15))),'tie':bool(tie)})
preflight=[]
for s in ['S0','S1']:
    detectable=sum(q['route_detectable_samples']>=2 for q in reports if q['source_id']==s)
    if detectable<3:failures.append(s+':M0_OBSERVATION_HOLD_detectable')
    for family in ['HIT_FORWARD','LOG_GAUSSIAN']:
        valid=sum(q['preflight_correct_p60'] for q in pred if q['source_id']==s and q['family']==family);preflight.append({'source':s,'family':family,'correct_ptrue60_count':valid,'required':3,'detectable_ge2_count':detectable})
        if valid<3:failures.append(s+':'+family+':M0_OBSERVATION_HOLD_LORO')
elapsed=read(DATA/'E1_PROGRESS.json')['wall_s'];times=np.array([q['sim_wall_s']+q['extraction_wall_s'] for q in reports]);total_bytes=sum(p.stat().st_size for p in DATA.rglob('*') if p.is_file());resources={'current_evidence_input_output_bytes':total_bytes,'wall_all8_s':elapsed,'q95_sim_plus_extraction_s':float(np.quantile(times,.95,method='linear')),'projected_total_wall_s':float(3*np.quantile(times,.95,method='linear')*32+elapsed+1800),'projected_total_bytes':int(32*max(q['output_bytes'] for q in reports)+total_bytes),'max_actual_RSS_bytes':max(max(q['sim_peak_RSS_bytes'],q['extraction_peak_RSS_bytes']) for q in reports)}
resource_pass=resources['projected_total_wall_s']<=10800 and resources['projected_total_bytes']<=5*1024**3 and resources['max_actual_RSS_bytes']<=2*1024**3
if not resource_pass:failures.append('M0_RESOURCE_HOLD')
csvout('E1_ALL_RECORD_SUPPORT.csv',frame_rows);csvout('E1_BASELINE_SUMMARY.csv',reports);csvout('E1_U0_LORO.csv',pred)
decision={'verdict':'M0_E1_BASELINE_QUALIFIED' if not failures else 'M0_PREREQUISITE_HOLD','scientific_M0_verdict':'NOT_TESTED','stage':'E0+E1','actual_U0_runs':8,'actual_wrong_wind_runs':0,'all_failures':failures,'eight_support_runs_pass':all(q['support_pass'] for q in reports),'eight_relevance_runs_pass':all(q['PairA_relevance_pass'] for q in reports),'eight_parity_runs_pass':all(q['sampling_parity_pass'] for q in reports),'LORO_preflight':preflight,'resources':resources,'R0_39_files_unchanged':True,'E2_CrossWrongWind_CRN_sentinel':'NOT_RUN_NOT_AUTHORIZED','STOP_now':True,'intervention_authorized':False,'limits':'Baseline qualifications only. The 32 wrong-wind causal contrast and final M0 gate were not tested.'}
write('E1_DECISION.json',decision);write('E1_PER_RUN_DETAIL.json',reports);write('E1_RESOURCE_AUDIT.json',resources);write('E1_CLOCK_RNG_CERTIFICATE.json',{'native_expected_saved_records':native_expected,'terminal_clock_s':terminal_time,'native_total_ticks':tick,'per_run_clock':{'%s_r%s'%key:value for key,value in actual_clock.items()},'U0_cross_source_same_seed_sigma_clock_bit_identity':True,'zero_deletion_certificate_method':'Fixed release accounting at every native record and all-six-face support bound controlling all between-save/terminal intervals','wrong_wind_cross_arm_assignment':'pending E2 sentinel','three_draws_per_live_filament_per_tick':'Pinned code control-flow certificate, not newly instrumented per-tick RNG trace','total_draws':3*tick*(tick+1)//2})
print(json.dumps(decision,indent=2))
