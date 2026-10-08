"""Per-run frozen prerequisite gates. Reusable for live E3 and all40 review."""
from pathlib import Path
import csv,hashlib,json
import numpy as np
from scipy.special import ndtr
def rows(p,delimiter=','):
    with Path(p).open(encoding='utf-8') as f:return list(csv.DictReader(f,delimiter=delimiter))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def qualify(row,audit,result,reference,domain,source,windstat,noise,route_geometry):
    audit=Path(audit);result=Path(result);reference=Path(reference);frames=rows(audit/'native_frames.csv');base=rows(reference/'native_frames.csv');timeline=rows(result/'RECORD_TIMELINE.tsv','\t')
    state=np.fromfile(audit/'filament_states.f32',dtype='<f4').reshape(-1,4);baseline=np.fromfile(reference/'filament_states.f32',dtype='<f4').reshape(-1,4)
    lo=np.array(domain['effective_outlet_inner_planes_m']['min']);hi=np.array(domain['effective_outlet_inner_planes_m']['max']);band=domain['true_boundary_band_m'];Q=domain['qualification'];requested=source['clock']['score_times_s']
    t=np.float32(0);last=np.float32(-np.inf);dt=np.float32(source['clock']['time_step_s']);save=np.float32(source['clock']['results_time_step_s']);tick=0;sig=np.float32(10);age=[sig];expected=[]
    while t<np.float32(source['clock']['sim_time_s']):
        tick+=1;sig=np.float32(sig+np.float32(np.float32(15)/np.float32(2*sig)*dt));age.append(sig)
        if t>np.float32(last+save):expected.append((len(expected),t,tick));last=t
        t=np.float32(t+dt)
    terminal=float(t);ages=np.array(age,dtype=np.float32);frame_metrics=[];fail=[];same_clock=len(frames)==len(base)==len(timeline)==len(expected);same_sigma=True;age_match=True;release=True;seq=hashlib.sha256()
    for f,b,tm,exp in zip(frames,base,timeline,expected):
        n=int(f['n_filaments']);offset=int(f['offset_filaments']);a=state[offset:offset+n];ref=baseline[int(b['offset_filaments']):int(b['offset_filaments'])+int(b['n_filaments'])];assert np.isfinite(a).all() and (a[:,3]>0).all()
        same_clock=same_clock and all(f[k]==b[k] for k in ['record_index','time_s','wind_index','n_filaments','offset_filaments']) and int(f['record_index'])==exp[0] and np.float32(float(f['time_s']))==exp[1] and int(f['wind_index'])==0
        same_clock=same_clock and float(tm['internal_simulation_time_s'])==float(f['time_s']) and int(tm['record_index'])==int(f['record_index']) and int(tm['wind_index'])==0
        release=release and n==exp[2];same_sigma=same_sigma and np.array_equal(a[:,3],ref[:,3]);age_match=age_match and np.array_equal(a[:,3],ages[exp[2]:0:-1]);seq.update(a[:,3].tobytes())
        xyz=a[:,:3].astype(float);s=a[:,3,None].astype(float)/100;cent=xyz.mean(axis=0);margins=np.concatenate([xyz-lo-3*s,hi-xyz-3*s],axis=1)
        def box(bl,bh):return float(np.prod(ndtr((bh-xyz)/s)-ndtr((bl-xyz)/s),axis=1).mean())
        whole=box(lo,hi);inset=box(lo+band,hi-band);roi=box(np.array(domain['analysis_roi_m']['min']),np.array(domain['analysis_roi_m']['max']));on=box(np.array([0,-2,2]),np.array([12,2,8]));off=box(np.array([0,3.5,2]),np.array([12,7.5,8]));variance=((xyz-cent)**2).mean(axis=0)+np.mean(s*s)
        met={'run_id':row['run_id'],'record_index':int(f['record_index']),'time_s':float(f['time_s']),'filament_count':n,'expected_release':exp[2],'release_deficit':exp[2]-n,'min_3sigma_margin_m':float(margins.min()),'centroid_clearance_m':float(min(np.r_[cent-lo,hi-cent])),'all6_band_mass_fraction':max(0.,whole-inset)/whole,'whole_Gaussian_box_mass_fraction':whole,'outside_Gaussian_box_mass_fraction':1-whole,'ROI_mass_fraction':roi,'outside_ROI_mass_fraction':1-roi,'A_on_mass_fraction':on,'A_off_mass_fraction':off}
        for j,k in enumerate(['x','y','z']):met['centroid_'+k+'_m']=float(cent[j]);met['spread_'+k+'_m']=float(np.sqrt(variance[j]))
        for axis in range(3):
            for side in [0,1]:
                bl=lo.copy();bh=hi.copy()
                if side==0:bh[axis]=lo[axis]+band
                else:bl[axis]=hi[axis]-band
                name=['x','y','z'][axis]+['_min','_max'][side];met[name+'_band_fraction']=box(bl,bh)/whole;met[name+'_3sigma_margin_m']=float(margins[:,axis+3*side].min())
        frame_metrics.append(met)
    assert len(frame_metrics)>0;times=np.array([m['time_s'] for m in frame_metrics]);indices=np.searchsorted(times,requested,side='right')-1;assert (indices>=0).all();selected=[frame_metrics[k] for k in indices];lag=np.array(requested)-times[indices];bands=np.array([m['all6_band_mass_fraction'] for m in selected]);on=np.array([m['A_on_mass_fraction'] for m in selected]);off=np.array([m['A_off_mass_fraction'] for m in selected])
    gap=max(float(np.diff(times).max()),terminal-times[-1]);bound=(windstat['max_speed']+.1*noise['max_abs']+.012)*(gap+1e-6);margin=min(m['min_3sigma_margin_m'] for m in frame_metrics);clear=min(m['centroid_clearance_m'] for m in frame_metrics);src=np.array([float(row[k]) for k in ['x_m','y_m','z_m']]);source_clear=float(min(np.r_[src-lo,hi-src]));tail_safe=margin>bound and gap<=.610001
    log=(audit/'simulation.stdout.log').read_text(errors='replace');exception=any(v in log for v in ['Exception Updating Filaments','Could not spawn','SERIOUS','Requested wind vector at a point outside','Filament is outside environment'])
    support=margin>=Q['every_record_min_filament_3sigma_margin_to_outlet_m'] and clear>=Q['centroid_min_clearance_to_effective_outlet_m'] and source_clear>=Q['source_min_clearance_to_outlet_m'] and float(bands.mean())<=Q['band_mean_mass_fraction_max'] and float(np.quantile(bands,.95,method='linear'))<=Q['band_mass_fraction_q95_max'] and release and tail_safe and not exception
    crn=same_clock and same_sigma and age_match and release and not exception and support
    obs=rows(audit/'route.csv');refobs=rows(reference/'route.csv');route_ok=len(obs)==len(refobs)==51
    for o,b,g in zip(obs,refobs,route_geometry):route_ok=route_ok and all(o[k]==b[k] for k in ['time_s','record_index','x','y','z']) and np.allclose([float(o[k]) for k in ['x','y','z']],[float(g[k]) for k in ['x_m','y_m','z_m']],atol=1e-6,rtol=0)
    y=np.array([float(o['ppm']) for o in obs]);assert np.isfinite(y).all() and (y>=0).all();parity=rows(audit/'sampling_parity.csv');parity_ok=len(parity)>=51*25 and all(float(q['absolute_difference'])<=1e-5*(1+abs(float(q['native']))) for q in parity);relevance=row['wind_arm']!='U0' or (on.mean()>=.30 and off.mean()<=.01 and np.quantile(off,.95,method='linear')<=.05)
    for name,ok in [('SUPPORT',support),('RNG',crn),('ROUTE',route_ok),('SAMPLING_PARITY',parity_ok),('PAIR_A_RELEVANCE',relevance),('FRAME_ALIGNMENT',float(lag.max())<=.61)]:
        if not ok:fail.append('M0_'+name+'_HOLD')
    rep={'run_id':row['run_id'],'wind_arm':row['wind_arm'],'source_id':row['source_id'],'realization':int(row['realization']),'master_seed':int(row['master_seed']),'records':len(frames),'support_pass':bool(support),'CRN_pass':bool(crn),'route_pass':bool(route_ok),'sampling_parity_pass':bool(parity_ok),'Pair_A_baseline_relevance_pass':bool(relevance),'minimum_3sigma_margin_m':margin,'minimum_centroid_clearance_m':clear,'source_clearance_m':source_clear,'all6_band_mean':float(bands.mean()),'all6_band_q95':float(np.quantile(bands,.95,method='linear')),'zero_deletion_certified':0 if support else None,'native_exceptions':exception,'clock_identical_to_U0':bool(same_clock),'full_sigma_birth_order_identical_to_U0':bool(same_sigma),'sigma_age_recurrence_match':bool(age_match),'sigma_sequence_sha256':seq.hexdigest(),'noise_table_sequence_sha256':noise['table_sequence_sha256'],'total_native_ticks':tick,'total_RNG_draw_call_assignments':3*tick*(tick+1)//2,'terminal_clock_s':terminal,'last_saved_clock_s':float(times[-1]),'max_frame_lag_s':float(lag.max()),'max_gap_motion_bound_m':float(bound),'route_detectable_samples':int((y>=.1).sum()),'first_route_detection_request_s':next((float(o['time_s']) for o in obs if float(o['ppm'])>=.1),None),'native_parity_queries':len(parity),'native_parity_max_abs_diff':max(float(q['absolute_difference']) for q in parity),'A_on_baseline_overlap_mean':float(on.mean()),'A_off_baseline_overlap_mean':float(off.mean()),'A_off_baseline_overlap_q95':float(np.quantile(off,.95,method='linear')),'failures':fail,'qualified':not fail,'deletion_RNG_certificate_kind':'Pinned source and no-retry point emission; saved counts/sigma and interval+terminal bound, not instrumented per-tick events.'}
    return rep,frame_metrics
