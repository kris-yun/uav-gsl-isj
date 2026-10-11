from common_n import *
import csv,io
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8',newline='')))
def cb(rs):
 s=io.StringIO();w=csv.DictWriter(s,fieldnames=list(rs[0]),lineterminator='\n');w.writeheader();w.writerows(rs);return s.getvalue().encode()
old=BASE/'outputs/PMFS_RK2B_CONTINUOUS_20261010_CORE';reg=load(old/'experiment_registry.json');banks=[]
for c in ['C7','K2']:
 for i in range(4):banks.append(dict(id=c+'_'+str(i),candidate=c,replicate=i,path=f'/home/zyc/pmfs_m2_process_observation_20261010/realizations/{c}_{i}'))
for j in reg['jobs']:
 if j['role'] not in ['reference','extra_reference']:continue
 ci=j['job_id'].split('_')[0];i=j['replicate']+(2 if j['role']=='extra_reference' else 0)
 banks.append(dict(id=ci+'_'+str(i),candidate=ci,replicate=i,path=reg['remote_data_path']+'/realizations/'+j['job_id']))
cov=rows(BASE/'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010/observation_lineage/MAP_REPLAY_EVENT_COVARIATES.csv')
lin=rows(BASE/'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010/native_reference_evidence/realizations/C7_0/QUERY_PHYSICAL_LINEAGE.csv')
lin={int(r['block_id']):r for r in lin if r['membership_branch']=='0'}
historical=[]
for i,e in enumerate(cov):historical.append(dict(block_id=i,stop_id=e['stop_id'],physical_target_s=lin[i]['target_physical_s'],x=e['x'],y=e['y'],z=-.2,wind_speed=e['wind_speed'],wind_direction_to=e['wind_direction_to'],event_hit=1,concentration_ppm=0))
plan=dict(entry_unix=load(WORK/'ENTRY_TIME.json')['start_unix'],banks=banks,schedules=[dict(id='B4',events='events/B4_plan.csv'),dict(id='PUBLIC_B',events='events/D00.csv')],
 query_executable='/home/zyc/pmfs_m2_process_observation_20261010/query_native',query_SHA256='52e282b03b7e109204c1b22b096ab41ca15e33a7cc24625b1b79feaa0b9789f5',environment='/home/zyc/pmfs_b4_native_validation_20261009/derived_B4',
 score='actual native sourceProbFromMaps, D=.4, same observed p/confidence, same447 support',O0='At least one centre per exact nativeXY cell per frame; no ppm semantics; mask prior to native blur',O1='Native Query at actual-.2m, PID threshold>.1ppm, original3sigma/LOS',
 A0='O1 instantaneous grid event frequency with native blur',A1='O1 receiver events through actual native EstimateHitProbabilities; no second blur',
 scope='fixed five original point-source GADEN hypotheses; not447-map treatment; all public exploratory',new_gas_calls=0)
dump(CORE/'READOUT_CONTRACT.json',plan)
files={'READOUT_CONTRACT.json':(CORE/'READOUT_CONTRACT.json').read_bytes(),'readout_worker.py':(WORK/'readout_worker.py').read_bytes(),
 'events/B4_plan.csv':cb(historical),'raw_decode.py':(BASE/'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010/independent_raw_query_verify/verify_raw_receiver_queries.py').read_bytes()}
code=r'''import subprocess,time
p=subprocess.Popen(['python3',str(t/'readout_worker.py')],stdout=(t/'readout_worker.stdout').open('w'),stderr=(t/'readout_worker.stderr').open('w'),start_new_session=True)
print(json.dumps({'pid':p.pid,'tasks':40,'new_gas':0}))
'''
r=json.loads(upload(files,code,'start_readout_native_existing_banks',45));dump(CORE/'READOUT_WORKER_STARTED.json',r);print(json.dumps(r))
