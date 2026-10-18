"""Bind existing service requests to their recorded physical frames; no simulations."""
from pathlib import Path
import csv,json,struct,zlib,hashlib,subprocess,base64,shutil,bisect
import numpy as np
R=Path(__file__).resolve().parents[1];P=R.parent/'NATIVE_PMFS_WIND_RECOVERY_20261014'
N=P/'PORTABLE_DATA/cases/C4/native_execution';W=P/'cases/C4'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,v):p=R/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
def write(n,a):
    p=R/n;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(a[0]));w.writeheader();w.writerows(a)
# The original execution used this isolated R6 build, not the main workspace build.
remote='''from pathlib import Path
import json,base64,hashlib
r=Path('/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws')
c=r/'src/gaden_common/third_party/gaden_core'
files=[r/'src/gaden_player/src/simulation_player.cpp',r/'src/gaden_player/src/simulation_player.h']
files += [c/'src'/n for n in ['Simulation.cpp','PlaybackSimulation.cpp','RunningSimulation.cpp','Environment.cpp','GasSource.cpp']]
files += [c/'include/gaden'/n for n in ['Simulation.hpp','Environment.hpp','EnvironmentConfiguration.hpp','datatypes/Filament.hpp','datatypes/SimulationMetadata.hpp','internal/Serialization.hpp','core/Vectors.hpp']]
files += [r/'build/gaden_common/third_party/gaden_core/CMakeFiles/gaden.dir/flags.make']
out={str(p.relative_to(r)):base64.b64encode(p.read_bytes()).decode() for p in files if p.exists()}
out['_binary_sha256']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [r/'install/gaden_common/lib/libgaden.so',r/'install/gaden_player/lib/gaden_player/player'] if p.exists()}
print(json.dumps(out))
'''
q=subprocess.run(['ssh','-o','BatchMode=yes','zyc@192.168.111.128','python3','-'],input=remote.encode(),capture_output=True)
(R/'logs/runtime_source_snapshot.stderr').write_bytes(q.stderr);assert q.returncode==0
data=json.loads(q.stdout);binary=data.pop('_binary_sha256')
for name,b64 in data.items():p=R/'source_runtime'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(b64))
dump('lineage/RUNTIME_BUILD_IDENTITY.json',dict(root='/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws',binaries=binary,source_hashes={n:sha(R/'source_runtime'/n) for n in data},current_main_workspace_is_not_assumed_runtime=True))
for name in ['consumer_messages.csv','measurement_events.csv','physical_clock_trace.csv','service_queries.jsonl','preflight_PioneerP3DX_PID_parameters.yaml','PREFLIGHT.json','resolved_player_parameters.yaml','resolved_GSL_parameters.yaml','raw_ros_cdr.jsonl']:
    shutil.copy2(N/'runtime'/name,R/'inputs'/name)
for name in ['CASE_META.json','generation.yaml','PHYSICAL_FRAME_TIME.csv','ALL_FRAME_SHA256_AND_TIME.csv','generation.receipt.json','WORLD_QA.json']:
    shutil.copy2(W/name,R/'inputs'/name)
grid=R.parent/'NATIVE_PMFS_FULL20_20261014/derived/c5f5c47a61f0/OccupancyGrid3D.csv'
shutil.copy2(grid,R/'inputs/OccupancyGrid3D.csv')
queries=[json.loads(x) for x in (N/'runtime/service_queries.jsonl').read_text().splitlines()]
queries=[x for x in queries if x['kind']=='GasPosition']
clocks=[x for x in csv.DictReader((N/'runtime/physical_clock_trace.csv').open()) if x['reason']=='gas_service']
events=list(csv.reader((N/'runtime/measurement_events.csv').open()))
consumers=[(i,x) for i,x in enumerate(csv.DictReader((N/'runtime/consumer_messages.csv').open())) if x['kind']=='gas']
by_stamp={int(x['stamp_ns']):x for _,x in consumers}
event_bindings=[]
for e in events:
    a=by_stamp.get(int(e[0]));exact=a is not None and float(a['value'])==float(e[1])
    event_bindings.append(dict(stamp_ns=int(e[0]),stop=int(e[6]),window=int(e[7]),window_mean_ppm=float(e[1]),
      same_stamp_raw_exists=a is not None,same_stamp_raw_ppm=float(a['value']) if a else '',single_raw_value_exact_match=exact,
      ownership='same stamp and identical raw value' if exact else 'consumption window mean; exact callback membership not saved'))
write('lineage/CONSUMED_WINDOW_PID_BINDING.csv',event_bindings)
def gas_response(h):
    b=bytes.fromhex(h);assert b[:4]==b'\0\1\0\0'
    n,ng=struct.unpack_from('<II',b,4);assert n==ng==1
    v=struct.unpack_from('<d',b,12)[0]
    assert struct.unpack_from('<I',b,20)[0]==1
    length=struct.unpack_from('<I',b,24)[0];name=b[28:28+length].rstrip(b'\0').decode();assert 28+length==len(b)
    assert name=='butane';return v
out=[];ambiguous=[]
for x in queries:
    # The server advances and records its loaded frame at entry to this callback.
    # Require exactly one corresponding gas_service row in the proxy request interval.
    c=[r for r in clocks if int(x['request_ns'])<=int(r['receipt_ros_ns'])<=int(x['response_ns'])]
    if len(c)!=1:
        ambiguous.append(dict(serial=x['serial'],matching_service_clock_rows=len(c)));continue
    c=c[0];assert len(x['x'])==len(x['y'])==len(x['z'])==1
    ppm=gas_response(x['response_cdr_hex'])
    # Binding to consumed readings is separate: same exact value and publication
    # stamp after service response, before the next service call; no nearest-pose claim.
    readings=[(i,r) for i,r in consumers if int(x['response_ns'])<=int(r['stamp_ns'])<=int(x['response_ns'])+250000000 and float(r['value'])==ppm]
    row=dict(serial=x['serial'],request_ns=x['request_ns'],response_ns=x['response_ns'],
      service_clock_ns=int(c['receipt_ros_ns']),frame=int(c['frame']),physical_s=float(c['frame_internal_s']),
      x=x['x'][0],y=x['y'][0],z=x['z'][0],recorded_service_ppm=ppm,
      consumer_matches=len(readings),consumer_row=readings[0][0] if len(readings)==1 else '',
      consumer_stamp_ns=readings[0][1]['stamp_ns'] if len(readings)==1 else '',consumed_stop='',consumed_window='')
    if len(readings)==1:
        ev=[e for e in events if e[0]==row['consumer_stamp_ns']]
        if ev:
            assert len(ev)==1;row['consumed_stop']=int(ev[0][6]);row['consumed_window']=int(ev[0][7])
    out.append(row)
write('inputs/physical_queries.csv',out)
dump('lineage/TIME_BINDING.json',dict(gas_queries=len(queries),gas_service_clock_rows=len(clocks),unique_interval_bindings=len(out),ambiguous=ambiguous,
  consumers=len(consumers),consumed_events_exact_single_PID_match=sum(r['single_raw_value_exact_match'] for r in event_bindings),consumed_events=len(events),
  query_bound_consumed_events=sum(r['consumed_stop']!='' for r in out),
  matching_rule='One gas_service clock row inside recorded request/response interval; exact response value plus <=250 ms following PID stamp for consumer association',
  limits='No independent samples claimed; consumer association is timestamp/value supported, no shared message ID. Exact event stamp/value match is checked separately.'))
frames=sorted({r['frame'] for r in out});manifest={int(x['frame']):x for x in csv.DictReader((W/'ALL_FRAME_SHA256_AND_TIME.csv').open())}
meta=[];dest=R/'inputs/physical_frames';dest.mkdir(exist_ok=True)
for f in frames:
    p=W/f'one_realization/iteration_{f}';b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==manifest[f]['sha256']
    assert b[:13]==b'GADEN_RESULT\0' and b[13]==1
    raw=zlib.decompress(b[22:]);assert len(raw)==struct.unpack_from('<Q',b,14)[0]
    assert struct.unpack_from('<II',raw)==(3,0)
    L=struct.unpack_from('<Q',raw,48)[0];off=56+L
    assert raw[56:off]==b'point'
    xyz=struct.unpack_from('<3f',raw,off);gas=struct.unpack_from('<i',raw,off+12)[0]
    moles,air=struct.unpack_from('<2f',raw,off+16);wind=struct.unpack_from('<i',raw,off+24)[0]
    L=struct.unpack_from('<Q',raw,off+28)[0];off2=off+36+L
    assert raw[off+36:off2]==b'filaments'
    n=struct.unpack_from('<Q',raw,off2)[0];start=off2+8
    assert len(raw)==start+n*16
    fs=np.frombuffer(raw,'<f4',offset=start).reshape(n,4);assert np.isfinite(fs).all() and (fs[:,3]>0).all()
    assert gas==10 and abs(xyz[0]+.77)<1e-6 and abs(xyz[1]-2.2)<1e-6
    shutil.copy2(p,dest/p.name)
    meta.append(dict(frame=f,sha256=sha(p),filaments=n,total_moles_per_filament=moles,moles_air_per_cm3=air,sigma_cm_min=float(fs[:,3].min()),sigma_cm_max=float(fs[:,3].max()),source_z=xyz[2],wind_index=wind,format='GADEN 3.0 point/filaments; little endian float32 xyz+sigma_cm'))
write('lineage/PHYSICAL_FRAME_FIELDS.csv',meta)
dump('lineage/PHYSICAL_ASSET_AVAILABILITY.json',dict(matched_frames=len(frames),positions=True,sigma_cm=True,shared_moles_per_filament=True,air_moles_per_cm3=True,
  source_position=True,frame_times=True,release_config=True,filament_ID=False,per_filament_age=False,
  missing_effect='Frame snapshot supports exact instantaneous concentration and centre events, but not unique filament trajectory/age or counterfactual other-source response.',
  truth_fields_online_allowed=False))
print(json.dumps(json.loads((R/'lineage/TIME_BINDING.json').read_text()),indent=2))
print('physical frames',len(frames),'bytes',sum(p.stat().st_size for p in dest.iterdir()))
