from pathlib import Path
import csv,hashlib,json,math,subprocess,sys
import numpy as np
from PIL import Image
import yaml
R=Path(__file__).resolve().parent;O=R/'analysis';O.mkdir(exist_ok=False)
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
def put(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def write(p,rs):
 if rs:
  with p.open('w',newline='',encoding='utf-8')as f:w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
summaries=[];updates=[];contexts=[];checks=[];readout_groups=[];failures=[]
for role in ['PF24_A2_Q01','PF24_A2_T01','PF24_A2_T02','PF24_B2_Q01']:
 D=R/'cases'/role;run=D/'RUN_RESULT.json'
 if not run.exists():continue
 result=json.loads(run.read_text());case=result['case'];runtime=D/'runtime';meta=json.loads((D/'CASE_META.json').read_text());truth=np.array(meta['source_xyz'][:2])
 if result.get('result')!='NATIVE_ACTION_RETURNED':
  failures.append(dict(role=role,case=case,native_goals=result.get('native_goal_count',0),classification='TECHNICAL_NOT_PMFS_PERFORMANCE',error=result.get('error'),retained=True));continue
 assert result.get('preflight')=='PASS'and result.get('native_goal_count')==1
 gate=json.loads((runtime/'BASELINE_PARAMETER_GATE.json').read_text());assert gate['status']=='PASS_ACTUAL_NODE_PARAMETER_VALUES'
 # Compare the actual Nav2 occupancy map byte-for-byte against the pinned official PGM.
 nav=json.loads((runtime/'NAVIGATION_MAP_METADATA.json').read_text());cfgroot=R/'official_exact/Environment_config/PMFS/scenarios'/case[0];cfg=yaml.safe_load((cfgroot/'_occupancy.yaml').read_text())
 im=np.array(Image.open(cfgroot/cfg['image']).convert('L'))
 occ=(255-im.astype(float))/255. if not cfg.get('negate',0)else im.astype(float)/255.
 expected=np.full(im.shape,-1,dtype='i1');expected[occ>float(cfg['occupied_thresh'])]=100;expected[occ<float(cfg['free_thresh'])]=0
 expected=np.flipud(expected).copy();actual=np.fromfile(runtime/'navigation_map.s8',dtype='i1').reshape(nav['height'],nav['width'])
 assert actual.shape==expected.shape and np.array_equal(actual,expected),('NAV_MAP_DIFFERS_FROM_PINNED_OFFICIAL_PGM',role)
 assert abs(nav['resolution']-cfg['resolution'])<1e-8
 assert np.max(abs(np.array([nav['origin_x'],nav['origin_y']])-cfg['origin'][:2]))<1e-6
 w=rows(runtime/'native_window_consumption.csv');consumed=[r for r in w if r['status']=='CONSUMED'];assert consumed
 assert all(int(r['gas_count'])>0 and int(r['wind_count'])>0 for r in consumed)
 wind=rows(runtime/'GMRF_consumed.csv');assert len(wind)>3
 clock=json.loads((runtime/'CLOCK_SENSOR_RATE_PREFLIGHT.json').read_text());assert 4.4<clock['real_time_factor']<5.6
 assert clock['gas_samples_per_wall_second']>7 and clock['wind_samples_per_wall_second']>14
 states={}
 for a in rows(runtime/'native_posterior_updates.csv'):states.setdefault(int(a['update']),[]).append(a)
 assert states
 for update,a in sorted(states.items()):
  q=np.array([float(t['source_probability'])for t in a]);omega=np.array([float(t['hit_omega'])for t in a]);alpha=np.array([float(t['hit_confidence'])for t in a]);xy=np.array([[float(t['x_m']),float(t['y_m'])]for t in a]);assert np.all(np.isfinite(q))and np.all(q>=0)and abs(q.sum()-1)<1e-9
  err=float(np.max(abs(alpha-(1-np.exp(-omega**2)))));assert err<2e-14,('ACTUAL_EQ6_MISMATCH',role,update,err)
  mean=(q[:,None]*xy).sum(axis=0);var=float(np.sum(q*np.sum((xy-mean)**2,axis=1)));cellsize=float(a[0]['cell_size_m']);width=int(nav['width']/25);height=int(nav['height']/25)
  # Match native float coordinate-to-index semantics. Support is reported, never modified.
  tx=int(np.float32(np.float32(truth[0])-np.float32(nav['origin_x']))/np.float32(cellsize));ty=int(np.float32(np.float32(truth[1])-np.float32(nav['origin_y']))/np.float32(cellsize))
  truth_row=next((i for i,t in enumerate(a)if int(t['col'])==tx and int(t['row'])==ty),None)
  info=dict(role=role,case=case,update=update,source_cells=len(a),probability_mass=float(q.sum()),max_Eq6_alpha_error=err,full_variance_m2=var,posterior_mean_error_m=float(np.linalg.norm(mean-truth)),truth_supported=truth_row is not None,truth_cell_probability=float(q[truth_row])if truth_row is not None else 0.,truth_strict_rank=int(1+np.sum(q>q[truth_row]))if truth_row is not None else None)
  updates.append(info);contexts.append(dict(role=role,update=update,truth=truth.tolist(),info=info));readout_groups.append((nav,cellsize,a,width,height))
 raw=(runtime/'native_results.csv').read_text().strip().split();failed=raw[0]=='FAILED';raw=raw[1:]if failed else raw;assert len(raw)==6,raw
 native=dict(navigation_time=float(raw[0]),search_s=float(raw[1]),mean_error_m=float(raw[2]),top5_error_m=float(raw[3]),iterations=int(raw[4]),variance_m2=float(raw[5]))
 assert failed== (not bool(result.get('localization_success')))
 if not failed:assert native['variance_m2']<1.
 assert abs(native['variance_m2']-updates[-1]['full_variance_m2'])<2e-5
 summary=dict(role=role,case=case,classification='DECLARED'if not failed else 'NATIVE_300S_CENSORED',native_declared=not failed,declared_top5_error_m=native['top5_error_m']if not failed else None,last_censored_top5_error_m=native['top5_error_m']if failed else None,search_s=native['search_s'],variance_m2=native['variance_m2'],source_updates=len(states),consumed_windows=len(consumed),empty_waits=len(w)-len(consumed),gas_count_min=min(int(t['gas_count'])for t in consumed),wind_count_min=min(int(t['wind_count'])for t in consumed),truth_supported=updates[-1]['truth_supported'],clock_real_time_factor=clock['real_time_factor'],actual_parameters_pass=True,map_bytes_match_official_PGM=True,Eq6_actual_snapshots_pass=True,binary_sha256=meta['actual_binary_sha256'])
 summaries.append(summary)
 checks.append(dict(role=role,nav_map='EXACT_OFFICIAL_PGM_BYTES',parameters='PASS',native_clock='PUBLIC_PROFILE_MEASURED_NOT_ORIGINAL_PAPER_PROOF',window_consumption='NONEMPTY',source_mass='UNIT_FINITE',confidence_formula='PAPER_EQ6',local_wind='GMRF_WITH_VALIDITY_GUARD_NO_FREE_TRUE_FIELD'))
write(O/'EPISODES.csv',summaries);write(O/'SOURCE_UPDATES.csv',updates);put(O/'TECHNICAL_TRIALS.json',failures);put(O/'CHECKS.json',checks);put(O/'CONTEXTS.json',contexts)
with (O/'native_readout_input.txt').open('w')as f:
 f.write(str(len(readout_groups))+'\n')
 for nav,size,a,width,height in readout_groups:
  f.write(f"{width} {height} {nav['origin_x']:.17g} {nav['origin_y']:.17g} {size:.17g} {len(a)}\n")
  for r in a:f.write(f"{r['col']} {r['row']} {r['source_probability']}\n")
put(O/'FIRST_STAGE_COMPLETE.json',dict(status='TWO_CASES_RECORDED'if len(summaries)==2 else 'PARTIAL',episodes=summaries,technical_trials=failures,new_gas_worlds=0,AIMMD=0))
print(json.dumps(dict(status='ANALYSIS_INPUT_GATES_PASS',episodes=len(summaries),updates=len(updates),technical_trials=len(failures))))
