"""Necessity gate: numerical target, rare path statistics and task direction.

No new simulations; no proposal is trained on the high-budget reference.
"""
from pathlib import Path
import csv,gzip,json,math,os
import numpy as np
R=Path(__file__).resolve().parent;O=Path(os.environ.get('AIMMD_ANALYSIS_OUT',str(R/'analysis')));O.mkdir(parents=True,exist_ok=True)
plan=json.loads((R/'FROZEN_PLAN.json').read_text(encoding='utf8'));assert (R/'PRIMARY_COMPLETE.json').exists()
def rows(p):return list(csv.DictReader(p.open(newline='')))
def write(n,a):
    if not a:return
    with (O/n).open('w',newline='',encoding='utf8') as f:w=csv.DictWriter(f,fieldnames=list(a[0]));w.writeheader();w.writerows(a)
def dump(n,a):(O/n).write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf8')
jobrows=rows(R/'inputs/jobs.csv');byjob={(x['key'],x['job_id'],x['phase'],int(x['replicate'])):x for x in jobrows}
commands=json.loads((R/'COMMANDS.json').read_text());cmd_by_tag={x['tag']:x for x in commands}
full_cost_by_job={(x['key'],x['job_id'],x['phase'],int(x['replicate'])):cmd_by_tag[f'sim_{i:04d}']['cpu_s'] for i,x in enumerate(jobrows)}
constructor_cost=cmd_by_tag['export_native_constructor_states']['cpu_s']/len(jobrows)
receptors=[];costs=[];checks=[];source_stats=[];batches=[];targets=[];gates=[];emission_checks=[];source_meta=[]
for c in plan['cases']:
    key=c['key'];rx=rows(R/'inputs'/key/'receivers.csv');m=rows(R/'inputs'/key/'metadata.csv')[0];w,h=int(m['width']),int(m['height']);cells=w*h
    inp=rows(R/'inputs'/key/'input.csv');free=np.array([x['occupancy']=='1' for x in inp]);conf=np.array([float(x['confidence']) for x in inp]);measured=1-1/(1+np.exp([float(x['logOdds']) for x in inp]));D=float(rows(R/'inputs'/key/'settings.csv')[0]['sourceDiscriminationPower'])
    def cellscore(p):
        out=np.zeros_like(p,dtype='f8');out[...,free]=np.log(1-D*conf[free]*np.abs(measured[free]-p[...,free]));return out
    def ell(p):return cellscore(p).sum(axis=-1)
    data={};ref_stats={};rare_masks={}
    for ident in [c['truth_job'],c['competitor_job']]:
        arrays={};source_receiver=[]
        for phase,n in [('reference',128),('evaluation',96)]:
            maps=[];raws=[];ls=[];cpu=[];moves=[];timing=[];visitors=[];recvis=[];emits=[];alive=[];recfreq=[];first=[]
            for k in range(n):
                p=R/'results'/phase/key/ident/str(k);sc=rows(p/'scores.csv');assert len(sc)==1;s=sc[0];p=p/ident
                raw=np.fromfile(p/'raw.f32','<f4');blur=np.fromfile(p/'blur.f32','<f4');assert len(raw)==len(blur)==cells
                error=abs(float(ell(blur))-float(s['source_logscore']));assert error<1e-12;checks.append(error)
                trace=np.frombuffer(gzip.decompress((p/'trace.u32.gz').read_bytes()),'<u4').reshape(-1,9+3*len(rx));assert len(trace)==2000
                assert int((trace[:,0]==0).sum())==1800 and int((trace[:,0]==1).sum())==200
                assert np.all(trace[:,5].astype('i8')-trace[:,6].astype('i8')==trace[:,3])
                assert int(trace[:,2].astype('u8').sum())==int(s['particle_moves'])
                assert (int(s['gaussian_before'])+2*int(s['particle_moves']))%2500==int(s['gaussian_after'])
                rec=trace[trace[:,0]==1];allvis=[];rvis=[];fr=[];ft=[]
                for ri,r in enumerate(rx):
                    q=9+3*ri;actual=float(np.mean(rec[:,q]>0));assert np.float32(actual)==raw[int(r['cell_index'])]
                    allvis.append(int(trace[:,q+1].sum()));rvis.append(int(rec[:,q+1].sum()));fr.append(actual)
                    hits=np.flatnonzero(trace[:,q]>0)
                    ft.append((float(trace[hits[0],1]-1)*(.2 if trace[hits[0],0]==0 else .1)+(0 if trace[hits[0],0]==0 else 360)) if len(hits) else math.nan)
                inclusive_cpu=full_cost_by_job[(key,ident,phase,k)]+constructor_cost
                maps.append(blur);raws.append(raw);ls.append(float(s['source_logscore']));cpu.append(inclusive_cpu);moves.append(int(s['particle_moves']));visitors.append(allvis);recvis.append(rvis);emits.append(int(s['emitted']));alive.append(int(s['final_survivors']));recfreq.append(fr);first.append(ft)
                costs.append(dict(key=key,source=ident,phase=phase,replicate=k,seed=s['seed'],cpu_s=inclusive_cpu,simulation_internal_cpu_s=float(s['cpu_s']),constructor_amortized_cpu_s=constructor_cost,moves=int(s['particle_moves']),emitted=int(s['emitted']),final_survivors=int(s['final_survivors'])))
            arrays[phase]=dict(maps=np.array(maps,dtype='f8'),raws=np.array(raws,dtype='f8'),ls=np.array(ls),cpu=np.array(cpu),moves=np.array(moves),visitors=np.array(visitors),record_new_visitors=np.array(recvis),emits=np.array(emits),alive=np.array(alive),freq=np.array(recfreq),first=np.array(first))
        data[ident]=arrays
        a=arrays['reference'];mean=a['maps'].mean(axis=0);a['reference_mean']=mean
        gradient=np.zeros(cells);gradient[free]=D*conf[free]*np.sign(measured[free]-mean[free])/(1-D*conf[free]*np.abs(measured[free]-mean[free]));linear=a['maps']@gradient
        ref_stats[ident]=dict(target_score=float(ell(mean)),mean_random_run_score=float(a['ls'].mean()),linearised_variance_of_mean=float(linear.var(ddof=1)/128),half_0=float(ell(a['maps'][:64].mean(axis=0))),half_1=float(ell(a['maps'][64:].mean(axis=0))))
        mask=np.zeros(cells,bool);diagnostic_stops=c['diagnostic_stops']
        for ri,r in enumerate(rx):
            frac=a['visitors'][:,ri]/a['emits'];meanfrac=float(frac.mean());meanvis=float(a['visitors'][:,ri].mean())
            allowed=(diagnostic_stops=='all consumed receptors' and r['consumed_by_this_update']=='1') or (isinstance(diagnostic_stops,list) and int(r['stop']) in diagnostic_stops)
            rare=bool(allowed and meanfrac<=.01 and a['visitors'][:,ri].sum()>=3)
            if rare:
                cell=int(r['cell_index']);x,y=cell%w,cell//w
                for yy in range(max(0,y-5),min(h,y+6)):
                    for xx in range(max(0,x-5),min(w,x+6)):mask[yy*w+xx]=True
            finite=a['first'][:,ri][np.isfinite(a['first'][:,ri])]
            receptors.append(dict(key=key,source=ident,stop=r['stop'],consumed=r['consumed_by_this_update'],diagnostic_stop_allowed=allowed,
              mean_lifetime_visitors=meanvis,mean_births_visiting_fraction=meanfrac,total_visitors_across_128_runs=int(a['visitors'][:,ri].sum()),
              descriptive_rare_path_screen=rare,run_fraction_any_visit=float(np.mean(a['visitors'][:,ri]>0)),run_fraction_any_record_hit=float(np.mean(a['freq'][:,ri]>0)),
              mean_record_occupancy=float(a['freq'][:,ri].mean()),first_arrival_median_s=float(np.median(finite)) if len(finite) else '',first_arrival_min_s=float(finite.min()) if len(finite) else '',first_arrival_max_s=float(finite.max()) if len(finite) else '',
              mean_record_new_lifetime_visitors=float(a['record_new_visitors'][:,ri].mean()),note='Descriptive native shared-cache counts; births and frames are correlated, not independent Bernoulli samples'))
        rare_masks[ident]=mask&free
        source_stats.append(dict(key=key,source=ident,**ref_stats[ident],reference_cpu_s=float(a['cpu'].sum()),evaluation_cpu_s=float(arrays['evaluation']['cpu'].sum()),source_RNG_coupling='Independent source-specific prediction states; ordinary common-random-number source pairing was not tested'))
    truth,comp=c['truth_job'],c['competitor_job'];refgap=ref_stats[truth]['target_score']-ref_stats[comp]['target_score'];se=math.sqrt(sum(ref_stats[i]['linearised_variance_of_mean'] for i in [truth,comp]));lo,hi=refgap-1.96*se,refgap+1.96*se
    half=[ref_stats[truth][f'half_{i}']-ref_stats[comp][f'half_{i}'] for i in [0,1]]
    target=dict(key=key,reference_true_minus_competitor_score=refgap,linearised_reference_SE=se,descriptive_linearised_95_low=lo,descriptive_linearised_95_high=hi,
      split_half_0_gap=half[0],split_half_1_gap=half[1],mean_random_run_score_gap=ref_stats[truth]['mean_random_run_score']-ref_stats[comp]['mean_random_run_score'],
      expectation_and_nonlinear_score_not_interchanged=True,target_favours_true_source=refgap>0,formal_physical_world_confidence=False)
    targets.append(target)
    for M in [1,4]:
        ee=[];rr=[];wr=[];cpu=[]
        for b in range(24):
            sl=slice(b*4,b*4+M);ts=data[truth]['evaluation']['maps'][sl].mean(axis=0);cs=data[comp]['evaluation']['maps'][sl].mean(axis=0)
            delta=float(ell(ts)-ell(cs));error=delta-refgap
            tdiff=cellscore(ts)-cellscore(data[truth]['reference']['reference_mean']);cdiff=cellscore(cs)-cellscore(data[comp]['reference']['reference_mean']);part=float(tdiff[rare_masks[truth]].sum()-cdiff[rare_masks[comp]].sum())
            ee.append(error);rr.append(part);wr.append(delta*refgap<0);cost=float(data[truth]['evaluation']['cpu'][sl].sum()+data[comp]['evaluation']['cpu'][sl].sum());cpu.append(cost)
            batches.append(dict(key=key,replicates_per_source=M,batch=b,estimated_gap=delta,reference_gap=refgap,error=error,rare_region_exact_error_component=part,reference_relative_wrong_order=delta*refgap<0,true_source_loses=delta<0,cpu_s=cost))
        ee,rr=np.array(ee),np.array(rr);rmse=float(np.sqrt(np.mean(ee*ee)));rareRMSE=float(np.sqrt(np.mean(rr*rr)))
        signed=float(np.cov(rr,ee,ddof=1)[0,1]/np.var(ee,ddof=1)) if np.var(ee)>0 else math.nan
        qualified=se<=.25*rmse and all(x*refgap>0 for x in half)
        material=rmse>2*se
        rarelink=rareRMSE>=.2*rmse and signed>0
        # This source-pair task gate is frozen and separate from the numerical
        # efficiency question. Negative target is not a sampler failure.
        taskblocked=qualified and hi<0
        gates.append(dict(key=key,replicates_per_source=M,MC_RMSE=rmse,MC_mean_error=float(ee.mean()),MC_rare_region_error_RMSE=rareRMSE,
          rare_error_RMSE_over_total=rareRMSE/rmse if rmse else '',signed_rare_region_covariance_fraction=signed,
          MC_reference_relative_wrong_orders=int(sum(wr)),batches=24,MC_true_source_loses=sum(x['true_source_loses'] for x in batches if x['key']==key and x['replicates_per_source']==M),
          mean_MC_cpu_s=float(np.mean(cpu)),reference_uncertainty_over_MC_RMSE=se/rmse if rmse else '',
          reference_provisionally_qualified=qualified,material_MC_pair_score_error=material,rare_region_error_link_screen=rarelink,
          task_direction_blocked_for_source_pair=taskblocked,
          gate2_necessity_screen=bool(qualified and material and rarelink and not taskblocked),
          exclusion='This is not MC-vs-WE-vs-AIMMD; no same-CPU 20% claim is made'))
write('REFERENCE_TARGETS.csv',targets);write('SOURCE_REFERENCE_STATS.csv',source_stats);write('MC_BATCH_RESULTS.csv',batches);write('NECESSITY_GATE.csv',gates);write('RECEPTOR_RARITY_AND_LATENCY.csv',receptors);write('FORWARD_COSTS.csv',costs)
dump('CHECKS.json',dict(completed_primary_source_calls=len(costs),parity_source_calls=4,maximum_exact_score_recompute_error=max(checks),native_population_event_and_trace_frequency_match=True,
  birth_exit_survivor_conservation=True,cyclic_cache_index_consumption_match=True,source_specific_prediction_states=True,particle_or_frame_independence_not_assumed=True,
  reference_for_evaluation_only=True,new_physical_worlds=0,new_ROS=0,new_closed_loop_gain=False))
eligible=[x for x in gates if x['replicates_per_source']==4 and x['gate2_necessity_screen']]
decision=dict(stage='BOUNDED_NUMERICAL_NECESSITY_PILOT',gate2_eligible_contexts=[x['key'] for x in eligible],
  status='PROCEED_ONLY_TO_ADMISSIBLE_STRONG_BASELINE_COMPARISON' if eligible else 'STOP_BEFORE_SAMPLER_DEVELOPMENT',
  numerical_sampling_error_present=any(x['material_MC_pair_score_error'] for x in gates),
  numerical_gate='NUMERICAL_ERROR_AND_LOW_COUNT_REGION_LINK_OBSERVED',
  task_link_gate='NOT_SUPPORTED_FOR_THESE_FROZEN_SOURCE_PAIRS' if not eligible else 'REQUIRES_NEXT_GATE',
  path_sampling_can_change_model_bias=False,
  sampler_independent_gain='NOT_TESTED',same_CPU_twenty_percent_gate='NOT_TESTED',AIMMD_implemented=False,weighted_ensemble_implemented=False,
  necessity_is_not_algorithm_effectiveness=True,
  source_pair_target_limit='Reference accuracy describes this frozen 360+20s target, not stationary truth, a full source posterior, or task gain. If this target prefers the competitor, better numerical integration alone does not restore this source pair.',
  no_automatic_horizon_seed_physics_or_score_search=True,targets=targets,gates=gates)
dump('DECISION.json',decision)
print(json.dumps(decision,ensure_ascii=False,indent=2))
