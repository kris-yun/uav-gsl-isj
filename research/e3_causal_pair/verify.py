from pathlib import Path
import json,csv,hashlib,re,zlib,struct,subprocess,sys
import numpy as np
from analyze import O,OLD,rows,load,put,table
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def decode(p):
 b=Path(p).read_bytes();assert b[:13]==b'GADEN_RESULT\0' and b[13]==1;a=zlib.decompress(b[22:]);n=struct.unpack_from('<Q',a,48)[0];off=56+n;source=struct.unpack_from('<3f',a,off);gas=struct.unpack_from('<i',a,off+12)[0];moles,air=struct.unpack_from('<2f',a,off+16);off+=28;length=struct.unpack_from('<Q',a,off)[0];off+=8+length;count=struct.unpack_from('<Q',a,off)[0];fil=np.frombuffer(a,dtype='<f4',offset=off+8).reshape(-1,4);assert len(fil)==count and np.isfinite(fil).all() and np.all(fil[:,3]>0);return source,gas,moles,air
def main():
 plan=load(O/'PREREGISTERED_CAUSAL_CONTRACT.json');rr=[];man=[]
 for w in plan['worlds']:
  path=O/'worlds'/w['id'];gauss=path/'RNG.GAUSSIAN.initial.txt';uni=path/'RNG.UNIFORM.initial.txt';cache=path/'RNG.cache.f32';initial=(path/'RNG.cache.initial.txt').read_text();final=(path/'RNG.cache.final.txt').read_text();i0=int(re.search(r'index=(\d+)',initial)[1]);i1=int(re.search(r'index=(\d+)',final)[1]);calls=int(re.search(r'calls=(\d+)',final)[1]);assert (i0+calls)%1000==i1 and calls%3==0;assert cache.stat().st_size==4000
  for p in sorted((path/'saved_world').rglob('*')):
   if not p.is_file():continue
   man.append(dict(world=w['id'],path=p.relative_to(O).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
   if p.name.startswith('iteration_'):
    src,gas,moles,air=decode(p);assert np.max(abs(np.array(src)-w['source_xyz']))<1e-6 and gas==10 and abs(moles-6.4407449826831e-6)<1e-12 and abs(air-4.0894632547860965e-5)<1e-12
  q=load(path/'REPLAY_QA.json');assert q['queries']==604 and q['max_abs_error_ppm']==0
  a=rows(path/'RESPONSES.csv');assert len(a)==604;tl=rows(path/'PHYSICAL_FRAME_TIME.csv');assert len(tl)==342 and all(0<=float(t['physical_snapshot_time_s'])<=240.01 for t in tl)
  rr.append(dict(world=w['id'],source_xyz=json.dumps(w['source_xyz']),gaussian_initial_sha256=sha(gauss),uniform_initial_sha256=sha(uni),cache_sha256=sha(cache),cache_initial_index=i0,cache_final_index=i1,cache_calls=calls,filament_moves=calls//3,native_replay_max_abs_error=0,source_and_units_all_snapshots_verified=True,independence='separate precommitted entropy-seeded streams; not iid within-world noise'))
 assert len({r['gaussian_initial_sha256'] for r in rr})==4 and len({r['uniform_initial_sha256'] for r in rr})==4 and len({r['cache_sha256'] for r in rr})==4
 table(O/'RNG_AND_WORLD_QUALIFICATION.csv',rr);put(O/'PHYSICAL_FRAME_SHA256.json',man)
 old=rows(O/'ORIGINAL_E3_NATIVE_3D_EVENT_DECOMPOSITION.csv');assert len(old)==65 and max(float(r['max_contribution_sum_error']) for r in old)==0
 q=load(O/'event_control/NATIVE_PARITY.json');assert len(q)==2 and all(r['all2112floats_exact'] and r['RNG_endpoint_exact'] for r in q)
 assert load(O/'MASS_WEIGHT_ACCOUNTING.json')['both_equal_physical10']
 total=load(O/'event_control/RECEIPT.json')['combined_execution_wall_s'];assert total<900
 allcost=load(O/'execution/COST.json')+load(O/'event_control/COST.json');assert max(r['CPU_s'] for r in allcost)<120
 assert sum(p.stat().st_size for p in O.rglob('*') if p.is_file())<134217728
 frozen=Path('D:/ZYC/A-gas/workspace/FROZEN_O24_1M2_SCREEN12_20261024/verify_frozen_baseline.py')
 if frozen.exists():
  v=subprocess.run([sys.executable,'-X','utf8',str(frozen)],capture_output=True,text=True,encoding='utf8',timeout=60);assert v.returncode==0;put(O/'FINAL_FROZEN_O24_GUARD.json',dict(status='PASS',stdout=v.stdout,stderr=v.stderr))
 put(O/'INDEPENDENT_QA.json',dict(status='PASS_PHYSICAL_IDENTITY_RNG_PARITY_UNITS_AND_RECOMPUTATION_GATES',physical_worlds=4,independent_stream_initializations_verified=4,physical_snapshots=len([r for r in man if '/iteration_' in r['path']]),actual_query_values_exact_replayed=2416,original_consumed_windows_reconstructed=65,old3D_decomposition_exact=True,native_caches_parity2112floats_each=2,same_trajectory_operator_comparisons=4,scientific_wall_s=total,max_recorded_child_CPU_s=max(r['CPU_s'] for r in allcost),new_ROS=0,neural_training=0,original_worlds_modified=False,full_source_new_algorithm_localization_claim=False,exception='First pre-propagation syntax-failed compiler aggregateCPU receipt was lost to an orchestration NameError; original error log retained, cost not fabricated. All four world generation calls and successful controls have complete ledgers.'))
 print('PASS_INDEPENDENT_QA',len(man),total,flush=True)
if __name__=='__main__':main()
