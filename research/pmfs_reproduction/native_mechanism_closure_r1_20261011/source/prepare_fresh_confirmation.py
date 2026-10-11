from common_n import *
import csv,shutil,math
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8',newline='')))
b=load(BASE/'outputs/PMFS_RK2B_CONTINUOUS_20261010_CORE/experiment_registry.json');m=rows(CORE/'MAP_OPERATOR_CONTRASTS.csv');p=rows(CORE/'RECEPTOR_READOUT_PREDICTION_METRICS.csv');improvements=[]
for rep in [0,1]:
 a=[r for r in m if r['oid']=='B4' and r['group']==f'R{rep}'];margin={r['method']:float(r['true_minus_bestwrong']) for r in a}
 met={r['method']:float(r['Brier']) for r in p if r['oid']=='B4' and int(r['replicate'])==rep}
 gain=margin['O1']-margin['O0'];assert gain>100*load(CORE/'B_NATIVE_SCORER_INDEPENDENT_VERIFY.json')['maximum_abs_log_difference']
 assert met['O1_PID']<met['O0_center_cell_proxy']
 improvements.append(dict(replicate=rep,margin_gain=gain,Brier_improvement=met['O0_center_cell_proxy']-met['O1_PID'],single_reference_sufficient=margin['O1']>0))
historical={s for j in b['jobs'] for s in [j['gaussian_seed'],j['uniform_seed']]}
oldm=load(BASE/'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010/frozen_contract.json');historical.update(s for j in oldm['jobs'] for s in j['seeds']);jobs=[];tags=[]
for cid in ['B000','B001','B002']:
 source=next(j['source_xyz'] for j in b['jobs'] if j['job_id'].startswith(cid))
 for rep in [0,1]:
  tag=f'NATIVE-MECHANISM-CLOSURE-R1|a5d93c9433f6a70ddbfba87329073fcf959018ea|FRESH|{cid}|{rep}'
  seeds=[int.from_bytes(hashlib.sha256((tag+'|'+s).encode()).digest()[:4],'big') for s in ['gaussian','uniform']]
  assert not historical.intersection(seeds);historical.update(seeds)
  jobs.append(dict(id=f'{cid}_fresh{rep}',oid=f'X{len(jobs):02d}',candidate=cid,source_xyz=source,seeds=seeds,tag=tag))
data=Path('D:/ZYC/A-gas/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011');freeze=data/'confirmation_reference_freeze';freeze.mkdir(exist_ok=False);refs=[]
for cid in ['C7','K2','B000','B001','B002']:
 for method in ['O0','O1']:
  src=data/'readout_scores'/f'PUBLIC_B_R01_{cid}_{method}.f32';dest=freeze/src.name;shutil.copy2(src,dest);refs.append(dict(candidate=cid,method=method,SHA256=sha(dest),path=DATA+'/confirmation_reference_freeze/'+dest.name))
plan=dict(status='FROZEN_BEFORE_FRESH_GAS_OUTPUT',entry_unix=load(WORK/'ENTRY_TIME.json')['start_unix'],intervention='O1 native PID readout; same-bank only; no fitted transform',control='O0 native-grid centre occupancy proxy with same native blur',
 selection='lowest complexity eligible registered factor; O1 priority over new propagation interventions; choice not changed by later C results',entry_evidence=improvements,
 negative_controls='Original O0 already correctly identifies all12 public B tasks; single-reference O1 remains wrong on B4 replicate0; A1 ties B4 original2 references',
 endpoint='Restricted five point candidates: native similarity at same447 measured cells/confidence; unique top1, true_minus_bestwrong, source weight; tie tolerance1e-12. N0 full447 history reported separately. No direct accuracy subtraction across supports.',
 stats_no_retuning='Report all six whole realizations; no inferential p-values or generalization beyond this geometry; no new selection from these outputs',
 jobs=jobs,references=refs,receiver_plan=b['receiver_plan'],all_receiver_xyz=b['all_receiver_xyz'],world_library='/home/zyc/pmfs_m2_process_observation_20261010/libgaden.so',world_library_SHA256='ed042a1c317a0350e3e1bd701c3ac1e1ab3df23a9807612fd6e91f9234be76c6',
 serial_wait_for_factorial=True,CFD_new=False,source_or_route_changes=False)
dump(CORE/'FRESH_CONFIRMATION_PREREGISTRATION.json',plan)
code=r'''from pathlib import Path
import subprocess,os,json,hashlib
t=Path(REMOTE);p=json.loads((t/'FRESH_CONFIRMATION_PREREGISTRATION.json').read_text());probe=Path('/home/zyc/ros2_ws/pmfs_rk2b_continuous_20261010/rng_probe')
assert probe.exists(),str(probe)
receipt={}
for j in p['jobs']:
 d=Path(DATA)/'fresh_rng_precommit'/j['id'];d.mkdir(parents=True,exist_ok=False);e=os.environ.copy();e.update(M2_GAUSSIAN_SEED=str(j['seeds'][0]),M2_UNIFORM_SEED=str(j['seeds'][1]),M2_RNG_TRACE=str(d/'RNG'))
 subprocess.run([str(probe)],env=e,check=True,timeout=10)
 receipt[j['id']]={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in d.iterdir() if '.initial.' in f.name or '.cache' in f.name}
(t/'FRESH_RNG_PRECOMMIT.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
'''.replace('REMOTE',repr(REMOTE)).replace('DATA',repr(DATA))
r=json.loads(upload({'FRESH_CONFIRMATION_PREREGISTRATION.json':(CORE/'FRESH_CONFIRMATION_PREREGISTRATION.json').read_bytes()},code,'fresh_seed_native_initial_state_precommit',45));dump(CORE/'FRESH_RNG_PRECOMMIT.json',r)
print(json.dumps({'selected':'O1','fresh_jobs_locked':6,'gas_generated':0,'entry_evidence':improvements}))
