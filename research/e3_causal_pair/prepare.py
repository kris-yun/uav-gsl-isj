from pathlib import Path
import csv,json,hashlib,os,secrets,struct,itertools,shutil,datetime
import numpy as np
PROJECT=Path('D:/ZYC/A-gas');C=PROJECT/'workspace/METHOD_COMPARISON_O24_1M2_20261024';OLD=C/'outputs/E3_INFORMATION_SOURCE_20261025';OUT=C/'outputs/E3_CAUSAL_PAIR_20261025';CODE=C/'method_source/E3_CAUSAL_PAIR_20261025'
REPLAY=C/'V12_REVIEW_20261024/pro_handoff/physical_replay_bundle'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8-sig')))
def table(p,rs):
 with Path(p).open('w',newline='',encoding='utf8') as f:w=csv.DictWriter(f,fieldnames=rs[0]);w.writeheader();w.writerows(rs)
def main():
 OUT.mkdir(exist_ok=False);CODE.mkdir(exist_ok=True);(OUT/'provenance').mkdir();(OUT/'schedule').mkdir()
 runtime=OLD/'inputs/E3_R01/runtime';windows=[w for w in rows(runtime/'native_window_consumption.csv') if w['status']=='CONSUMED'];gas=[json.loads(l) for l in (runtime/'service_queries.jsonl').read_text().splitlines()];gas=[g for g in gas if g['kind']=='GasPosition']
 trace=rows(runtime/'physical_clock_trace.csv');bytime={int(r['receipt_ros_ns']):r for r in trace if r['reason']=='gas_service'}
 ss=[];membership=[];oldqueries=[]
 for g in gas:
  g['ppm']=struct.unpack_from('<d',bytes.fromhex(g['response_cdr_hex']),12)[0]
 for w in windows:
  start=int(w['window_start_node_ns']);end=int(w['node_clock_ns']);count=int(w['gas_count']);obs=float(w['concentration_mean_ppm']);cand=[g for g in gas if start<=g['response_ns']<=end]
  valid=[]
  for subset in itertools.combinations(cand,count):
   val=float(np.float32(np.mean([np.float32(g['ppm']) for g in subset])))
   if abs(val-obs)<max(1e-6,abs(obs)*1e-6):valid.append(subset)
  assert valid,('cannot recover equivalent native-window sample packet',w['event'])
  # Deterministic oldest matching packet; alternate packets are preserved as
  # an explicit callback-membership ambiguity, never claimed uniquely known.
  chosen=valid[0];stop=(int(w['event'])-1)//5+1
  membership.append(dict(event=int(w['event']),stop=stop,native_count=count,equivalent_packets=len(valid),candidate_serial_sets=json.dumps([[g['serial'] for g in sub] for sub in valid]),selected_serials=json.dumps([g['serial'] for g in chosen]),mean_reconstruction_error=abs(float(np.float32(np.mean([np.float32(g['ppm']) for g in chosen])))-obs),scope='offline equivalent-packet recovery from actual count and mean; no unique callback claim on ties'))
  for tick,g in enumerate(chosen):
   tr=bytime.get(g['request_ns']);assert tr is not None,('missing exact physical clock binding',g['serial'])
   row=dict(query_id=f"hist_e{int(w['event'])}_t{tick}",group='historical',stop=stop,window=int(w['event']),action='original_route',update=0,tick=tick,ros_s=g['request_ns']*1e-9,physical_s=float(tr['target_internal_s']),x=g['x'][0],y=g['y'][0],z=g['z'][0],original_ppm=g['ppm'],original_frame=int(tr['frame']))
   ss.append(row);oldqueries.append(dict(query_id=row['query_id'],frame=row['original_frame'],x=row['x'],y=row['y'],z=row['z']))
 for r in rows(OLD/'FIXED_QUERY_SCHEDULE.csv'):
  ss.append(dict(query_id='action_'+r['query_id'],group='action',stop=0,window=int(r['window']),action=r['action'],update=int(r['update']),tick=int(r['tick']),ros_s=float(r['ros_s']),physical_s=float(r['physical_s']),x=float(r['x']),y=float(r['y']),z=float(r['z']),original_ppm='',original_frame=''))
 assert max(r['physical_s'] for r in ss)<240
 table(OUT/'schedule/QUERIES.csv',ss);table(OUT/'schedule/ORIGINAL_NATIVE_QUERY_INPUT.csv',oldqueries);table(OUT/'schedule/WINDOW_MEMBERSHIP_RECOVERY.csv',membership)
 points=[];lookup={}
 for r in ss:
  p=tuple(float(r[k]) for k in ['x','y','z'])
  if p not in lookup:lookup[p]=len(points);points.append(dict(point_id=len(points),x=p[0],y=p[1],z=p[2]))
 table(OUT/'schedule/UNIQUE_POINTS.csv',points)
 for r in ss:r['point_id']=lookup[tuple(float(r[k]) for k in ['x','y','z'])]
 table(OUT/'schedule/QUERIES.csv',ss)
 streams=[]
 for source,xyz in [('true',[-4.,-1.9,.7]),('rival',[-2.375,-4.875,.7])]:
  for rep in range(2):
   streams.append(dict(id=f'{source}_r{rep}',source=source,replicate=rep,source_xyz=xyz,gaussian_seed_words=[int.from_bytes(secrets.token_bytes(4),'little') for _ in range(4)],uniform_seed_words=[int.from_bytes(secrets.token_bytes(4),'little') for _ in range(4)]))
 models=[dict(id=f'pred_r{k}',uniform_seed=187031+7919*k,cache_seed_words=[int.from_bytes(secrets.token_bytes(4),'little') for _ in range(4)]) for k in range(2)]
 plan=dict(identity='E3_CAUSAL_PAIR_NATIVE_PHYSICS_AND_EVENT_OPERATOR_20261025',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent_commit='01b2a9507590b770503e138151ede211c0a08b82',
  authorization='Explicit user instruction: paired two-source two-realization physics after generator/RNG/resource gate',
  worlds=streams,prediction_streams=models,source_positions_fixed=True,
  physical=dict(duration_s=240.,deltaTime=.1,gas_type=10,temperature_K=298.,pressure_atm=1.,filaments_per_s=10.,initial_center_ppm=10.,initial_sigma_cm=10.,growth_gamma_cm2_s=15.,filament_noise_std=.015,wind='original E3 single loaded3D field, evaluator/generator only',source_height_m=.7),
  source_shape='native PointSource; no jitter; same empty initial field and continuous release',
  independence='OS-entropy independent128bit initialization of separate MT19937 Gaussian/uniform streams; actual engine/distribution/cache initial/final states logged. Within-world1000Gaussian cyclic cache retained: not iid increments.',
  output='No full concentration grids; native-format complete filament snapshots only at predeclared query times plus endpoints; all propagation from0to240s.',
  clock='Native RunningSimulation pre-step snapshot timestamp after that step advection, with post-step timestamp also saved; preserves original convention, not interpolated.',
  caps=dict(total_execution_wall_s=900,per_process_CPU_s=120,new_output_bytes=134217728,parallel_processes=1),
  observations=dict(original_windows=65,critical_stops=list(range(8,14)),query_rows=len(ss),distinct_positions=len(points),all_legal_previous_actions=True,threshold_ppm=.1,sensor='PID30 uncorrected direct ppm; original physical response, no invented filtering/noise'),
  controls=dict(native_center='verbatim native2D simulation, source point diagnostic at the same two coordinates; frozen posterior1132cells remains separate',
   ordinary_PID='same2D native paths/GMRF/RNG/budget; ordinary GADEN Gaussian mass/spread/3DLOS plus window-mean threshold. Derive quadrature puff mass from physical10filaments/s divided by native5paths/step. No new wind reconstruction.',
   source_support='Both diagnostic response arms use the same two fixed point hypotheses. Never present two-source MAP as full-domain localization gain.',
   same_budget='Two prediction streams per source; center and PID readout run on same trajectories; extra readout CPU reported separately.',
   physical_observability='Predeclared source-labelled physical-reference diagnostic only: realization0 reference, realization1 test, and swap; all13stops and8to13 reported. No reference bank enters deployable action choice.',
   likelihood='Station-balanced continuous template MSE and ordinary nonnegative amplitude-fit reference diagnostic; native and PID event source ranking use identical stationwise compatibility and ordinary Beta(1,1) smoothing sensitivity, not calibrated Bayes claims.',
   planner='Only after response directional adequacy on held-out physical realizations; full original cache IG retained as negative control. No new active neural model.'),
  no_retuning=True,no_new_ROS=True,A2='all3previous normal runs preserved; any operator diagnostic must include normal reference or report missing inputs',
  permitted_verdicts=['真实物理可分，原生响应错序','真实物理可分，普通可靠模型已能解决','现有动作物理不可分，其他动作可能可分','当前数据仍不足以可靠归因'])
 put(OUT/'PREREGISTERED_CAUSAL_CONTRACT.json',plan)
 shutil.copy2(REPLAY/'gaden_core_actual_source/include/gaden/internal/MathUtils.hpp',OUT/'provenance/MathUtils.original.hpp');shutil.copy2(REPLAY/'gaden_core_actual_source/src/RunningSimulation.cpp',OUT/'provenance/RunningSimulation.original.cpp')
 put(OUT/'INPUT_IDENTITIES.json',dict(geometry_sha256=sha(REPLAY/'actual_runtime/OccupancyGrid3D.csv'),physical_source_code_sha256=sha(OUT/'provenance/RunningSimulation.original.cpp'),old_contract_sha256=sha(OLD/'MINIMUM_MISSING_DATA_CONTRACT_PROPOSAL.json'),schedule_sha256=sha(OUT/'schedule/QUERIES.csv'),old_worlds_unchanged=True,old_A2_preserved=True))
 for p in Path(__file__).parent.glob('*'):
  if p.is_file():shutil.copy2(p,CODE/p.name)
 print(json.dumps(dict(status='FROZEN_BEFORE_NEW_WORLD_GENERATION',worlds=4,queries=len(ss),positions=len(points),critical_windows=30,largest_physical_s=max(r['physical_s'] for r in ss)),indent=2))
if __name__=='__main__':main()
