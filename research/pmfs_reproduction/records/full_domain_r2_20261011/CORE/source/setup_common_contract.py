from common_r2 import *
import csv,shutil,math,numpy as np
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8',newline='')))
def wc(p,rs):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]),lineterminator='\n');w.writeheader();w.writerows(rs)
for group in ['R0','R1']:
 source=Path('D:/ZYC/A-gas/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011/point_corrected_inputs')/group;dest=CORE/'predictor_inputs'/group;dest.mkdir(parents=True)
 for n in ['metadata.csv','settings.csv','gaussian_cache.f32','rng.csv']:shutil.copy2(source/n,dest/n)
 rr=rows(source/'input.csv')
 for r in rr:r.update(logOdds=str(math.log(.3/.7)),omega='0',confidence='0',probability='.3',prior_posterior=str(1/447 if r['occupancy']=='1' else 0))
 wc(dest/'input.csv',rr)
plans={}
for k,n in [('B4','B4_plan.csv'),('PUBLIC_B','D00.csv')]:
 rs=rows(CORE/'registered_covariates'/n);allowed=['block_id','stop_id','physical_target_s','x','y','z','wind_speed','wind_direction_to'];plans[k]=[{f:r[f] for f in allowed} for r in rs]
 wc(CORE/'predictor_covariates'/(k+'.csv'),plans[k])
bankreg=load(BASE/'outputs/PMFS_RK2B_CONTINUOUS_20261010_CORE/experiment_registry.json');aux=bankreg['all_receiver_xyz'][10:]
assert len(aux)==4
worldlib='/home/zyc/pmfs_m2_process_observation_20261010/libgaden.so'
common=dict(parent_commit='984cab0356872db354c909b1d534a510827ddbd2',upstream_PMFS_commit='4e141e162551e674f2f30ddb8859136c72139aac',native_binary=load(CORE/'NATIVE_BATCH_PROVENANCE.json'),world_library=worldlib,world_SHA256=load(CORE/'ENTRY_VM_PREFLIGHT.json')['world_library_SHA256'],geometry_SHA256=load(CORE/'geometry/CANDIDATE_MODES_PRECHECK.json')['geometry_SHA256'],source_mode=load(CORE/'MODE_AND_BUDGET_FREEZE.json')['mode'],source_catalog_SHA256=sha(CORE/'SOURCE_CATALOG_AND_COVERAGE.json'),source_prior='Uniform area per legal fine source cell; region weight proportional legalcell count',source_height=-.5,source_xyz_from_geometry_only=True,source_processes=dict(N_POINT_ALL='Native2D5centres/step, dt.1, sigma absent, no ppm units; cannot equate50/s toGADEN',P3='Official B4 gas13,7filaments/s, sigma10cm growth15, std.02, dt.1, full1000s, native3D moles/LOS'),wind_information=dict(allowed='Same immutable11 CFD assets',N_POINT_ALL='Captured CFD10 XY sampledat-.2; verticalcomponent unused',P3='All native3D components/heights and original0..10 startup; observed times use10 static',N0='Frozen captured groundtruth flow and adaptive tree; no newAction'),receiver_plans=plans,auxiliary_receivers=aux,aux_scope='Reference input diagnostic only, not newroute or inference endpoint',PID='Instantaneous nativeppm; corrections disabled',threshold='Strict float32ppm > float32(.1)',updates=[20,35,50],fixed_terminal=50,future_observed_data='Never read before prefix',N0_first_convergence='Frozen native rule only, not newAction',score_heads=dict(P3_O0_O1_NPOINT='Actual nativeblur and product similarity D.4, same observedp/confidence/mask447',E_event='Jeffreys .5 marginal meanBernoulli score, temperature1; composite, notjoint likelihood',A1_map='Mean negative squaredprobability distance across shared447 mask, temperature1; confidence notchanged orreused as anotherindependence weight'),RNG=dict(N_POINT='Two recorded ready states; each candidate reset same cache/LCG; not independentworld realizations',P3='Two preregistered seedstreams pernewcandidate; no collisions with allknownparent registers',future='Precommitted6seed andgeometry-basedsource choices, activated onlyatdevelopment gate'),groups=['R0','R1','R01'],factors_allowed_to_change={'P3-O0_vs_P3-O1':['readout_definition_only'],'NPOINT_vs_P3':['Forwardmodel combination; sourcearea/score/support equal'],'A1_vs_P3/Eevent':['Evidence head and observation representation']},no_new_CFD=True,no_navigation=True,no_training=True,allow_source_truth_in_inference=False)
dump(CORE/'COMMON_TASK_CONTRACT.json',common)
files={}
for p in (CORE/'predictor_inputs').rglob('*'):
 if p.is_file():files['inputs/'+p.relative_to(CORE/'predictor_inputs').as_posix()]=p.read_bytes()
files['COMMON_TASK_CONTRACT.json']=(CORE/'COMMON_TASK_CONTRACT.json').read_bytes();files['REFERENCE_JOBS_PREREGISTRATION.json']=(CORE/'REFERENCE_JOBS_PREREGISTRATION.json').read_bytes();files['MODE_AND_BUDGET_FREEZE.json']=(CORE/'MODE_AND_BUDGET_FREEZE.json').read_bytes();files['SOURCE_CATALOG_AND_COVERAGE.json']=(CORE/'SOURCE_CATALOG_AND_COVERAGE.json').read_bytes()
code=r'''import shutil,json,subprocess,os,hashlib,time
ram=Path('/dev/shm/pmfs_r2');env=ram/'environment';env.mkdir()
old=Path('/home/zyc/pmfs_b4_native_validation_20261009/derived_B4')
shutil.copy2(old/'OccupancyGrid3D.csv',env/'OccupancyGrid3D.csv');shutil.copytree(old/'wind',env/'wind')
wind={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (env/'wind').iterdir() if p.is_file()}
(t/'WIND_INPUT_HASHES.json').write_text(json.dumps(wind,indent=2))
assert len(wind)==11
e=os.environ.copy();e.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',LD_LIBRARY_PATH=json.loads(Path('/home/zyc/ros2_ws/pmfs_native_mechanism_closure_r1_20261011/ACTUAL_BINARY_PROVENANCE.json').read_text())['LD_LIBRARY_PATH'])
job=Path('/mnt/hgfs/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011/point_corrected_inputs/R0/point_C7.csv')
# Actual job file names are read from the qualified point directory, not guessed.
import csv
oldjobs=list(Path('/mnt/hgfs/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011/point_corrected_inputs/R0').glob('*.csv'))
selected=[]
for p in oldjobs:
 rows=list(csv.DictReader(p.open()))
 if rows and 'point_x' in rows[0] and abs(float(rows[0]['point_x'])+3.2)<1e-5 and abs(float(rows[0]['point_y'])+3.3)<1e-5:selected.append(p)
assert len(selected)==1
start=time.monotonic();out=ram/'SHORT_NATIVE_POINT_ANCHOR';p=subprocess.run([str(ram/'native_build/native_batch_entry'),'point_forward',str(t/'inputs/R0'),str(selected[0]),str(out)],env=e,capture_output=True,text=True,timeout=60);assert p.returncode==0,p.stderr
a=list(csv.DictReader((out/'forward/candidates.csv').open()))[0];oldpoint=Path('/mnt/hgfs/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011/point_corrected_results/C7_R0/forward');b=list(csv.DictReader((oldpoint/'candidates.csv').open()))[0]
assert (out/'forward'/a['map_file']).read_bytes()==(oldpoint/b['map_file']).read_bytes()
assert a['rng_after']==b['rng_after'] and a['gaussian_index_after']==b['gaussian_index_after']
print(json.dumps({'status':'PASS_NATIVE_BATCH_SHORT_POINT_CONNECTION','map_exact':True,'RNG_phase_exact':True,'wall_s':time.monotonic()-start,'wind_hashes':wind,'source_observation_values_not_in_predictor_input':True}))
'''
r=json.loads(upload(files,code,'common_contract_inputs_and_native_short_connection',90));dump(CORE/'NATIVE_SHORT_CONNECTION.json',r);print(json.dumps({k:v for k,v in r.items() if k!='wind_hashes'}))
