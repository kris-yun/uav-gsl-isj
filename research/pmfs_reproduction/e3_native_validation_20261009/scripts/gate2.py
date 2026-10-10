from common import *
print(remote(r'''
from pathlib import Path
import json,csv,zlib,struct,hashlib,statistics,numpy as np
t=Path('/home/zyc/pmfs_e3_native_validation_20261009')
g=json.loads((t/'GATE1.json').read_text());e=json.loads((t/'GENERATION_RESULT.json').read_text());assert e['exit_code']==0 and e['generation_executions']==1
bank=t/'one_realization_E3';frames=sorted(bank.glob('iteration_*'),key=lambda p:int(p.name.split('_')[1]));time=list(csv.DictReader((t/'PHYSICAL_FRAME_TIME.csv').open()))
assert len(frames)==len(time)>1100
records=[];maxfil=0
for k,(f,r) in enumerate(zip(frames,time)):
 b=f.read_bytes();assert int(f.name.split('_')[1])==int(r['frame'])==k and b.startswith(b'GADEN_RESULT\0') and b[13]==1
 a=zlib.decompress(b[22:]);assert len(a)==struct.unpack_from('<Q',b,14)[0] and struct.unpack_from('<II',a)==(3,0)
 assert list(struct.unpack_from('<3i',a,8))==g['grid_dimensions']
 assert np.allclose(struct.unpack_from('<3f',a,20),g['grid_minimum'],atol=1e-6,rtol=0)
 assert np.allclose(struct.unpack_from('<3f',a,32),g['grid_maximum'],atol=1e-6,rtol=0)
 assert abs(struct.unpack_from('<f',a,44)[0]-.1)<1e-7
 off=56+struct.unpack_from('<Q',a,48)[0]
 assert np.allclose(struct.unpack_from('<3f',a,off),[-4,-1.9,.7],atol=1e-6,rtol=0)
 assert struct.unpack_from('<i',a,off+12)[0]==10 and struct.unpack_from('<i',a,off+24)[0]==int(r['wind_index_at_save'])==0
 mode_n=struct.unpack_from('<Q',a,off+28)[0];mode=a[off+36:off+36+mode_n];assert mode==b'filaments'
 ptr=off+36+mode_n;num=struct.unpack_from('<Q',a,ptr)[0];ptr+=8
 assert num==int(r['filaments_after_step']) and len(a)-ptr==16*num
 fil=np.frombuffer(a,dtype='<f4',offset=ptr).reshape(num,4);assert np.isfinite(fil).all() and (fil[:,3]>0).all()
 maxfil=max(maxfil,num);tm=float(r['physical_snapshot_time_s']);post=float(r['post_step_time_s']);assert abs(post-tm-.1)<.00005
 records.append(dict(frame=k,physical_snapshot_time_s=tm,post_step_time_s=post,wind_index=0,filaments=num,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
ts=[r['physical_snapshot_time_s'] for r in records];d=np.diff(ts);assert (d>0).all() and ts[0]==0 and ts[-1]>999
assert ts[-1]-ts[200]>500
assert maxfil>100 and (t/'PHYSICAL_FRAME_TIME.csv.default_mt19937_state.txt').stat().st_size>1000
for n,h in json.loads((t/'OFFICIAL_ASSETS_BEFORE.json').read_text()).items():assert hashlib.sha256((t/n).read_bytes()).hexdigest()==h
wind=(bank/'wind/wind_iteration_0').read_bytes();assert wind==(t/'derived_E3/wind/wind_iteration_0').read_bytes()
with (t/'ALL_FRAME_SHA256_AND_TIME.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=records[0]);w.writeheader();w.writerows(records)
q=dict(verdict='PASS_CONTROLLED_SIMULATION_GENERATION_CONTRACT',generation_executions=1,frames=len(frames),source_xyz=[-4,-1.9,.7],gas_type=10,concentration_unit='ppm',sensor_input='Native PID model30 with default correction factors disabled returns sum of ppm; must verify at runtime',all_header_and_filament_values_verified=True,max_active_filaments=maxfil,wind_indices=[0],time_first_s=ts[0],time_last_s=ts[-1],start_frame=200,start_frame_actual_time_s=ts[200],saved_interval_min_s=float(d.min()),saved_interval_max_s=float(d.max()),saved_interval_median_s=float(np.median(d)),nominal_time_step_s=.1,physical_time_basis='Save-call currentTime before AdvanceTimestep; movement has already occurred in this step. post_step_time also captured; no index*0.5 assumption',default_rng_state_captured=True,seed_override=False,official_assets_unchanged=True,bank_bytes=sum(p.stat().st_size for p in bank.rglob('*') if p.is_file()),wind_sha256=hashlib.sha256(wind).hexdigest(),execution=e,independent_realizations=1,independent_experimental_physics_validation=False)
(t/'GATE2.json').write_text(json.dumps(q,indent=2));print(json.dumps(q))
''','GATE2',60))
