from pathlib import Path
import csv,json,hashlib,math,itertools,os
import numpy as np
B=Path('D:/ZYC/A-gas/workspace/METHOD_COMPARISON_O24_1M2_20261024');O=Path(os.environ.get('E3_PAIR_OUTPUT',str(B/'outputs/E3_CAUSAL_PAIR_20261025')));OLD=Path(os.environ.get('E3_PARENT_OUTPUT',str(B/'outputs/E3_INFORMATION_SOURCE_20261025')))
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8-sig')))
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def put(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+'\n',encoding='utf8')
def table(p,rs):
 with Path(p).open('w',newline='',encoding='utf8') as f:w=csv.DictWriter(f,fieldnames=rs[0]);w.writeheader();w.writerows(rs)
def main():
 assert (O/'event_control/RECEIPT.json').exists();schedule=rows(O/'schedule/QUERIES.csv');points=rows(O/'schedule/UNIQUE_POINTS.csv');group={}
 for r in schedule:group.setdefault((r['group'],int(r['stop']),int(r['update']),r['action'],int(r['window'])),[]).append(r)
 plan=load(O/'PREREGISTERED_CAUSAL_CONTRACT.json');physical={};window=[];station=[];decomp=rows(O/'original_E3_decomposition/DECOMPOSED_QUERIES.csv');decompbyid={r['query_id']:r for r in decomp}
 native_original=[]
 for w in plan['worlds']:
  ident=w['id'];dat={r['query_id']:r for r in rows(O/'worlds'/ident/'RESPONSES.csv')};physical[ident]={}
  for key,qs in group.items():
   pp=np.array([float(dat[r['query_id']]['raw_gas_ppm']) for r in qs]);mean=float(np.float32(pp.mean()));frames={dat[r['query_id']]['frame'] for r in qs}
   record=dict(world=ident,source=w['source'],replicate=w['replicate'],group=key[0],stop=key[1],update=key[2],action=key[3],window=key[4],point_id=int(qs[0]['point_id']),samples=len(qs),unique_physical_frames=len(frames),mean_ppm=mean,hit=int(mean>.1),first_physical_s=float(qs[0]['physical_s']),last_physical_s=float(qs[-1]['physical_s']))
   physical[ident][key]=record;window.append(record)
  for stop in range(1,14):
   rr=[r for r in physical[ident].values() if r['group']=='historical' and r['stop']==stop]
   station.append(dict(world=ident,source=w['source'],replicate=w['replicate'],stop=stop,mean_ppm=float(np.mean([r['mean_ppm'] for r in rr])),hit_frequency=float(np.mean([r['hit'] for r in rr])),n_windows=len(rr)))
 for event in range(1,66):
  qs=group[('historical',(event-1)//5+1,0,'original_route',event)];actual=next(r for r in rows(OLD/'WINDOW_RESPONSE_COMPARISON.csv') if r['role']=='E3_R01' and int(r['event'])==event)
  dd=[decompbyid[r['query_id']] for r in qs];mean=float(np.float32(np.mean([float(r['native_ppm']) for r in dd])));assert abs(mean-float(actual['concentration_ppm']))<max(1e-6,1e-6*abs(mean))
  native_original.append(dict(event=event,stop=(event-1)//5+1,actual_window_mean_ppm=float(actual['concentration_ppm']),reconstructed_native_ppm=mean,max_contribution_sum_error=max(abs(float(r['native_ppm'])-float(r['sum_contributions_ppm'])) for r in dd),gas_samples=len(dd),positive_samples=sum(float(r['native_ppm'])>.1 for r in dd),positive_samples_without_same_xy_cell_center=sum(float(r['native_ppm'])>.1 and int(r['center_occupants_same_xy_cell'])==0 for r in dd),mean_positive_contributors=float(np.mean([int(r['positive_contributors']) for r in dd])),mean_ppm_from_outside_sensor_xy_cell=float(np.mean([float(r['ppm_from_centers_outside_xy_cell']) for r in dd])),mean_nearest_center_distance_m=float(np.mean([float(r['nearest_center_m']) for r in dd])),mean_nearest_sigma_cm=float(np.mean([float(r['nearest_sigma_cm']) for r in dd]))))
 table(O/'PHYSICAL_WINDOWS.csv',window);table(O/'PHYSICAL_STATION_SUMMARY.csv',station);table(O/'ORIGINAL_E3_NATIVE_3D_EVENT_DECOMPOSITION.csv',native_original)
 # Physical response comparison preserves independent realizations as units;
 # five correlated windows are never called five independent trials.
 direction=[]
 oldst=[r for r in rows(OLD/'STOP_RESPONSE_COMPARISON.csv') if r['role']=='E3_R01']
 for stop in range(1,14):
  rr=[r for r in station if r['stop']==stop];delta=[next(r['hit_frequency'] for r in rr if r['world']==f'true_r{k}')-next(r['hit_frequency'] for r in rr if r['world']==f'rival_r{k}') for k in [0,1]]
  ppm_delta=[next(r['mean_ppm'] for r in rr if r['world']==f'true_r{k}')-next(r['mean_ppm'] for r in rr if r['world']==f'rival_r{k}') for k in [0,1]];old=oldst[stop-1]
  direction.append(dict(stop=stop,physical_hit_delta_r0=delta[0],physical_hit_delta_r1=delta[1],physical_mean_ppm_delta_r0=ppm_delta[0],physical_mean_ppm_delta_r1=ppm_delta[1],both_physical_sources_all5hit_in_both_replicates=all(r['hit_frequency']==1 for r in rr),original_region_frequency_true=float(old['true_native_frequency']),original_region_frequency_rival=float(old['wrong_native_frequency']),old_false_event_contrast=all(r['hit_frequency']==1 for r in rr) and float(old['true_native_frequency'])==0 and float(old['wrong_native_frequency'])>.9))
 table(O/'PHYSICAL_VS_ORIGINAL_RESPONSE_DIRECTION.csv',direction)
 # Source-labelled actual-world templates are a NONDEPLOYABLE observability
 # diagnostic. Reference and evaluation propagation realizations are disjoint.
 controls=[]
 for label,stops in [('whole13',list(range(1,14))),('critical8to13',list(range(8,14)))]:
  keys=sorted(k for k in group if k[0]=='historical' and k[1] in stops)
  for trainrep,testrep in [(0,1),(1,0)]:
   for source in ['true','rival']:
    y=np.array([physical[f'{source}_r{testrep}'][k]['mean_ppm'] for k in keys]);hits=np.array([physical[f'{source}_r{testrep}'][k]['hit'] for k in keys],float)
    for arm in ['continuous_template_MSE','unknown_nonnegative_amplitude','binary_template_Brier']:
     score={}
     for h in ['true','rival']:
      x=np.array([physical[f'{h}_r{trainrep}'][k]['mean_ppm'] for k in keys]);gain=max(0,float(x@y)/max(float(x@x),1e-30)) if arm=='unknown_nonnegative_amplitude' else 1.
      if arm=='binary_template_Brier':x=np.array([physical[f'{h}_r{trainrep}'][k]['hit'] for k in keys],float);score[h]=float(np.mean((hits-x)**2))
      else:score[h]=float(np.mean((y-gain*x)**2))
     wrong='rival' if source=='true' else 'true';tol=1e-12*max(1,abs(score['true']),abs(score['rival']));win=.5 if abs(score[source]-score[wrong])<=tol else float(score[source]<score[wrong]);controls.append(dict(scope=label,reference_rep=trainrep,evaluation_rep=testrep,evaluation_source=source,arm=arm,true_hypothesis_loss=score['true'],rival_hypothesis_loss=score['rival'],evaluation_source_rank_best=1 if win else 2,evaluation_source_rank_worst=2 if win==.5 else 1 if win else 2,correct_tie_aware=win,hypothesis_only_MAP_error_m=0 if win==1 else float(np.linalg.norm(np.array([-4.,-1.9])-[-2.375,-4.875])) if win==0 else None,deployment_qualified=False,full_source_localization_metric=False))
 table(O/'ACTUAL_WORLD_HELDOUT_OBSERVABILITY.csv',controls)
 # Four common native trajectories: center frequency, ordinary any-center
 # window, and native Gaussian PID-window event. No fitting or retuning.
 eventpred={};rates=[];pathvalid=[];E=O/'event_control';scene=load(E/'scene.json');nx=scene['nx'];origin=np.array(scene['origin']);cs=scene['cell_size']
 for h in ['true','rival']:
  for pred in plan['prediction_streams']:
   ident=h+'_'+pred['id'];rs=rows(E/(ident+'.timeseries.csv'));yy=np.array([float(r['ppm']) for r in rs]).reshape(200,len(points));cc=np.array([int(r['center_hit']) for r in rs]).reshape(200,len(points));freq=np.fromfile(E/(ident+'.f32'),dtype='<f4');pathvalid.append(dict(source=h,prediction=pred['id'],mean_active=float(np.mean([int(r['active_filaments']) for r in rs])),mean_3D_rejected_centers=float(np.mean([int(r['physical3D_rejected_centers']) for r in rs]))))
   for pid,p in enumerate(points):
    xy=np.array([float(p['x']),float(p['y'])]);ij=((xy.astype(np.float32)-origin.astype(np.float32))/np.float32(cs)).astype(int);native=float(freq[ij[0]+nx*ij[1]]);assert abs(native-cc[:,pid].mean())<1e-6,(ident,pid,native,cc[:,pid].mean())
    for n in [3,4,5]:
     windows=yy[:200//n*n,pid].reshape(-1,n).mean(1);center=cc[:200//n*n,pid].reshape(-1,n).max(1)
     for arm,q,count in [('native_center_frequency',native,200),('center_any_window',float(center.mean()),len(center)),('ordinary_PID_window',float(np.mean(windows>.1)),len(windows))]:
      eventpred[h,pred['id'],pid,n,arm]=q;rates.append(dict(source=h,prediction=pred['id'],point_id=pid,samples_per_window=n,arm=arm,predicted_event_rate=q,n_model_windows=count,mean_ppm=float(yy[:,pid].mean()),max_ppm=float(yy[:,pid].max()),calibration='uncalibrated stationary native path/readout diagnostic; temporal correlation not ignored in independent-world count'))
 table(O/'NATIVE_AND_EVENT_MATCHED_RESPONSE_RATES.csv',rates);table(O/'NATIVE_PATH_3D_VALIDITY_DIAGNOSTIC.csv',pathvalid)
 comparison=[]
 for w in plan['worlds']:
  for pred in plan['prediction_streams']:
   for label,stops in [('whole13',list(range(1,14))),('critical8to13',list(range(8,14)))]:
    ks=[k for k in group if k[0]=='historical' and k[1] in stops]
    for arm in ['native_center_frequency','center_any_window','ordinary_PID_window','native_center_frequency_beta11','center_any_window_beta11','ordinary_PID_window_beta11']:
     score={h:0. for h in ['true','rival']};brier={h:0. for h in ['true','rival']}
     for key in ks:
      z=physical[w['id']][key]
      for h in score:
       basearm=arm.replace('_beta11','');q=eventpred[h,pred['id'],z['point_id'],z['samples'],basearm]
       if arm.endswith('_beta11'):
        count=200 if basearm=='native_center_frequency' else 200//z['samples'];q=(q*count+1)/(count+2)
       score[h]+=math.log(1-.2*abs(z['hit']-q))/5;brier[h]+=(z['hit']-q)**2/len(ks)
     delta=score['true']-score['rival'];p=1/(1+math.exp(-delta));predh='true' if delta>1e-12 else 'rival' if delta< -1e-12 else 'tie';actual=w['source'];rank=1 if predh==actual else 2
     comparison.append(dict(world=w['id'],actual_source=actual,prediction=pred['id'],scope=label,arm=arm,true_minus_rival_log_compatibility=delta,true_over_rival_compatibility_ratio=math.exp(delta),normalized_pair_true_weight=p,pair_MAP=predh,pair_actual_rank=rank,pair_only_error_m=0 if rank==1 else 3.3898746289501624,true_source_proxy_Brier=brier[actual],competing_source_proxy_Brier=brier['rival' if actual=='true' else 'true'],full1132cell_localization=False,working_weights_not_calibrated_posterior=True))
 table(O/'MATCHED_EVENT_SOURCE_PAIR_RESULTS.csv',comparison)
 # Full legal support diagnostic on the original bank. Does not pretend to be
 # a new native tree, re-run posterior, or full-domain PID forward library.
 import sys
 sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'e3_information_audit'))
 import audit
 audit.OUT=OLD
 d=audit.case_data('E3_R01');s=audit.snapshot(d,4);banks=s['maps'][s['owner'][s['idx']]];full=[]
 for w in plan['worlds']:
  score=np.zeros(len(s['idx']))
  for key in group:
   if key[0]!='historical':continue
   z=physical[w['id']][key];qrow=group[key][0];xy=np.array([float(qrow['x']),float(qrow['y'])]);ij=np.floor((xy-[d['nav']['origin_x'],d['nav']['origin_y']])/d['cs']).astype(int);flat=int(ij[0]+d['nx']*ij[1]);score+=np.log(1-.2*abs(z['hit']-banks[:,flat]))
  p=np.exp(score-score.max());p/=p.sum();dd=dict(d,truth=np.array(w['source_xyz'][:2]));tc=np.floor((dd['truth']-[d['nav']['origin_x'],d['nav']['origin_y']])/d['cs']).astype(int);dd['tf']=int(tc[0]+d['nx']*tc[1]);full.append(dict(world=w['id'],mode='fixed_original1132cell_bank_raw_window_compatibility_NOT_NATIVE_REEXECUTION',**audit.metrics(p,s,dd)))
 table(O/'FULL_SUPPORT_FIXED_BANK_DIAGNOSTIC.csv',full)
 # Explicitly stop model-based planning when the candidate event models remain
 # wrong at the queried critical stations under the new independent worlds.
 reliability=[]
 for arm in ['native_center_frequency','center_any_window','ordinary_PID_window']:
  rr=[r for r in comparison if r['arm']==arm and r['scope']=='whole13'];true=[r for r in rr if r['actual_source']=='true'];reliability.append(dict(arm=arm,paired_world_seed_evaluations=len(rr),correct_pairs=sum(r['pair_actual_rank']==1 for r in rr),true_world_correct=sum(r['pair_actual_rank']==1 for r in true),reliable_model_gate_pass=all(r['pair_actual_rank']==1 for r in rr)))
 put(O/'ORDINARY_RESPONSE_RELIABILITY_GATE.json',dict(rows=reliability,continue_planner=any(r['reliable_model_gate_pass'] for r in reliability if r['arm']=='ordinary_PID_window'),scope='Prerequisite directional/model consistency only, not general calibration; failure stops any new planner performance claim'))
 def summary(group,arm):
  rs=[r for r in controls if r['scope']==group and r['arm']==arm];return sum(r['correct_tie_aware'] for r in rs)
 summary_result=dict(physical_template_whole13={a:summary('whole13',a) for a in ['continuous_template_MSE','unknown_nonnegative_amplitude','binary_template_Brier']},physical_template_critical8to13={a:summary('critical8to13',a) for a in ['continuous_template_MSE','unknown_nonnegative_amplitude','binary_template_Brier']},template_evaluations_per_arm=4,critical_stops_all_four_worlds_hit=[r['stop'] for r in direction if r['stop']>=8 and r['both_physical_sources_all5hit_in_both_replicates']],ordinary_reliability=reliability,original_positive_samples_no_xy_center=sum(r['positive_samples_without_same_xy_cell_center'] for r in native_original if r['stop']>=8),original_critical_samples=sum(r['gas_samples'] for r in native_original if r['stop']>=8),full_bank_results=full)
 put(O/'ANALYSIS_SUMMARY.json',summary_result);print(json.dumps(summary_result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
