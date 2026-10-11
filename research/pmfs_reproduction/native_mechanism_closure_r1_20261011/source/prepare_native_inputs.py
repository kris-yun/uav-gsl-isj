from common_n import *
import csv,io,shutil,numpy as np,yaml,struct
def rows(p):
 with Path(p).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def csvdata(a):
 s=io.StringIO(newline='');w=csv.DictWriter(s,fieldnames=list(a[0]),lineterminator='\n');w.writeheader();w.writerows(a);return s.getvalue().encode()
files={};contracts=[];anchors=[]
keys=['maxRegionSize','sourceDiscriminationPower','refineFraction','deltaTime','noiseSTDev','iterationsToRecord','minWarmupIterations','maxWarmupIterations','blurSigmaX','blurSigmaY','initialExplorationMoves','stepsSourceUpdate']
parents={'E3':BASE/'outputs/PMFS_E3_NATIVE_VALIDATION_20261009','B4':BASE/'outputs/PMFS_B4_OFFICIAL_TERMINAL_RESUMED_20261010'}
for label,parent in parents.items():
 pars=next(iter(yaml.safe_load((parent/'runtime/resolved_GSL_parameters.yaml').read_text()).values()))['ros__parameters']
 updates=sorted((parent/'runtime/updates').iterdir())
 snapshot=updates[-1];meta=load(snapshot/'metadata.json');m=rows(snapshot/'input.csv');cand=rows(snapshot/'candidates.csv')
 settings={k:pars[k] for k in keys}
 folder='inputs/'+label
 files[folder+'/input.csv']=(snapshot/'input.csv').read_bytes()
 files[folder+'/metadata.csv']=csvdata([meta]);files[folder+'/settings.csv']=csvdata([settings])
 files[folder+'/gaussian_cache.f32']=(snapshot/'gaussian_cache.f32').read_bytes()
 first=cand[0];files[folder+'/rng.csv']=csvdata([dict(phase=first['gaussian_index_before'],engine=first['rng_before'])])
 files[folder+'/anchor_job.csv']=csvdata([{k:first[k] for k in ['origin_i','origin_j','size_i','size_j']}])
 scorejobs=[]
 for i,c in enumerate(cand):
  name=folder+'/maps/'+str(i)+'.f32';files[name]=(snapshot/c['map_file']).read_bytes()
  scorejobs.append(dict(id=str(i),path=REMOTE+'/'+name))
 files[folder+'/score_jobs.csv']=csvdata(scorejobs)
 anchors.append(dict(label=label,input_path=REMOTE+'/'+folder,source=str(snapshot),candidates=cand,expected_posterior_SHA256=sha(snapshot/'posterior.f64'),expected_snapshot=str(snapshot)))
 contracts.append(dict(id=label,scope='N0_NATIVE_HISTORICAL_FROZEN_SNAPSHOT',settings=settings,metadata=meta,
   input_SHA256=sha(snapshot/'input.csv'),source_function='Simulations::sourceProbFromMaps / simulateSourceInPosition',wind_mode='USE_GADEN and useWindGroundTruth=True',
   ground_truth_wind_query_height_m=-.2 if label=='B4' else 'captured_from_original_TF_and_map',native_success_preserved=True))
# Derive scalar-controlled observations, preserving original public12 tasks.
old=BASE/'outputs/PMFS_RK2B_CONTINUOUS_20261010_CORE';reg=load(old/'experiment_registry.json');truth=load(old/'evaluation_only/TRUTH_MAPPING.json')
data=Path(reg['host_data_path']);template=rows(parents['B4']/'runtime/updates/update_2/input.csv');meta=load(parents['B4']/'runtime/updates/update_2/metadata.json')
for row in template:
 row['logOdds']=repr(np.log(.3/.7));row['omega']='0';row['confidence']='0';row['prior_posterior']=repr(1/meta['free_cells'] if row['occupancy']=='1' else 0)
# Wind matrix is obtained by native environment queries, not guessed from column averages.
# The existing B4 capture is checked against actual CFD10 at sensor height before use.
files['inputs/DERIVED/input.csv']=csvdata(template);files['inputs/DERIVED/metadata.csv']=csvdata([meta]);files['inputs/DERIVED/settings.csv']=files['inputs/B4/settings.csv']
first=rows(parents['B4']/'runtime/updates/update_0/candidates.csv')[0]
files['inputs/DERIVED/rng.csv']=csvdata([dict(phase=first['gaussian_index_before'],engine=first['rng_before'])]);files['inputs/DERIVED/gaussian_cache.f32']=(parents['B4']/'runtime/updates/update_0/gaussian_cache.f32').read_bytes()
derived=[]
for oid,info in sorted(truth.items()):
 job=next(j for j in reg['jobs'] if j['job_id']==info['job_id'])
 q={r['query_id']:r for r in rows(data/'realizations'/job['job_id']/'QUERY_OUTPUT.csv')};obs=[]
 with np.load(old/'scalar_observations'/f'{oid}.npz',allow_pickle=False) as z:con=z['observed_ppm']
 for b,p in enumerate(reg['receiver_plan']):
  r=q[f'b{b}_p{p["pose_id"]}'];u,v=float(r['wind_x']),float(r['wind_y'])
  assert np.float32(float(r['ppm_float32']))==con[b]
  obs.append(dict(block_id=b,stop_id=p['pose_id'],physical_target_s=p['physical_s'],x=p['xyz'][0],y=p['xyz'][1],z=p['xyz'][2],
      wind_speed=float(np.hypot(u,v)),wind_direction_to=float(np.arctan2(v,u)),concentration_ppm=float(con[b]),event_hit=int(con[b]>np.float32(.1))))
 files['events/'+oid+'.csv']=csvdata(obs)
 derived.append(dict(oid=oid,role=info['role'],event_file=REMOTE+'/events/'+oid+'.csv',source_truth_in_payload=False))
dump(CORE/'evaluation_only/PUBLIC_TASK_TRUTH.json',truth)
dump(CORE/'HISTORICAL_ANCHOR_PLAN.json',anchors)
dump(CORE/'BASELINE_CONTRACT.json',dict(status='FROZEN_BEFORE_NATIVE_OUTPUT',upstream_commit='4e141e162551e674f2f30ddb8859136c72139aac',historical=contracts,
 derived_scope='N0_NATIVE_FIXED_OBSERVATION_HISTORY_CONTROLLED_REPLAY; actual native probability functions; no processGas callback or ROS wind service called',
 all50_blocks_fixed=True,source_update_stops_zero_based=[3,6,9],source_update_blocks=[20,35,50],
 native_terminal_report='First original variance<1.5 is recorded; fixed50 shadow continues explicitly and cannot be called a new official action success',
 movement_rng_draws='No navigation decisions occur; common historical core RNG state is reused, candidate-update RNG history is preserved; conditional replay does not reproduce navigation RNG consumption',
 wind_planar_information='Native captured CFD10 planar vector at actual original anemometer height-.2m; verifies original USE_GADEN=True; no GMRF substitution',
 fixed_scoring_support=447,source_hypothesis_support='full original legal quadtree map',virtual_point_sampling=True,
 public_task_status='Already-public RK2-B diagnostic6 and formerheldout6, now exploratory',derived_jobs=derived,
 common_initial_RNG_SHA256=hashlib.sha256(files['inputs/DERIVED/rng.csv']+files['inputs/DERIVED/gaussian_cache.f32']).hexdigest()))
dump(CORE/'DERIVED_NATIVE_TASKS.json',derived)
for n,b in files.items():
 p=CORE/'native_inputs'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
payload={n:base64.b64encode(b).decode() for n,b in files.items()}
tail=r'''
import hashlib,subprocess,os
def sh(p):return hashlib.sha256(p.read_bytes()).hexdigest()
core=Path('/home/zyc/pmfs_official_alignment_r5_20261009/ws')
binary=core/'install/gsl_server/lib/gsl_server/gsl_actionserver_node'
assert binary.exists()
ldd=subprocess.run(['ldd',str(binary)],capture_output=True,text=True,check=True).stdout
(t/'HISTORICAL_GSL_ELF_PROVENANCE.json').write_text(json.dumps(dict(path=str(binary),SHA256=sh(binary),ldd=ldd,executed=False,goal_sent=False),indent=2))
print(json.dumps(dict(status='PASS_PRE_NATIVE_INPUT_FREEZE',files=len(FILES),historical_GSL_ELF_SHA256=sh(binary),derived_observations=12,CFD_input_matches_to_be_checked=True)))
'''.replace('FILES',repr(list(files)))
r=json.loads(upload(files,tail,'FREEZE_NATIVE_INPUTS',60));dump(CORE/'NATIVE_INPUT_PRE_EXECUTION_FREEZE.json',dict(**r,files_SHA256={n:hashlib.sha256(b).hexdigest() for n,b in files.items()}));print(json.dumps(r))
