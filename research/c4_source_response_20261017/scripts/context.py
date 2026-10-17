"""Qualification of source support, receiver support and actual wind input, selected histories only."""
from pathlib import Path
import json,csv,sys,hashlib
import numpy as np
R=Path(__file__).resolve().parents[1];P=R.parent/'NATIVE_PMFS_WIND_RECOVERY_20261014/PORTABLE_DATA';sys.path.insert(0,str(P.parent))
from cdr_wind import decode_response
plan=json.loads((R/'FROZEN_PLAN.json').read_text());index=json.loads((P/'CASE_INDEX.json').read_text())
out=[];receivers=[];hashes={}
for case in ['C4','C3']:
 e=next(x for x in index['cases'] if x['case']==case);g=next(x for x in index['field_groups'] if x['group']==e['group'])
 grid=P/g['grid_path'];text=grid.read_text().splitlines();minimum=np.array([float(x) for x in text[0].split()[1:]]);dims=np.array([int(x) for x in text[2].split()[1:]]);step=float(text[3].split()[1]);cells=np.array([[int(x) for x in row.split()] for row in text[4:] if row!=';'],np.int8).reshape(dims[2],dims[0],dims[1]);hashes[g['grid_path']]=hashlib.sha256(grid.read_bytes()).hexdigest()
 def support(xyz):
  ijk=np.floor((np.array(xyz)-minimum)/step).astype(int);inside=np.all(ijk>=0) and np.all(ijk<dims)
  return dict(inside=bool(inside),ijk=ijk.tolist(),value=int(cells[ijk[2],ijk[0],ijk[1]]) if inside else None,gas_free=bool(inside and cells[ijk[2],ijk[0],ijk[1]]==0))
 native=P/e['native_path'];queries=[json.loads(x) for x in (native/'runtime/service_queries.jsonl').read_text().splitlines()]
 events=np.loadtxt(native/'runtime/measurement_events.csv',delimiter=',',ndmin=2)
 for stop in np.unique(events[:,6]).astype(int):
  a=events[events[:,6]==stop];xyz=[*a[-1,4:6],e['metadata']['sensor_xyz'][2]];s=support(xyz)
  receivers.append(dict(case=case,stop=int(stop),receiver_x=float(xyz[0]),receiver_y=float(xyz[1]),nominal_sensor_z=float(xyz[2]),sensor_3d_point_free=s['gas_free'],occupancy_value=s['value'],rule='Static last consumed stop pose plus captured constant sensor height; does not assert complete moving acquisition support'))
 for item in [x for x in plan['cases'] if x['case']==case]:
  ep=item['epoch'];native_up=native/f'runtime/updates/update_{ep}';m=item['metadata'];inp=list(csv.DictReader((native_up/'input.csv').open()));free=[r for r in inp if r['occupancy']=='1'];uv=np.array([[float(r['u']),float(r['v'])] for r in free])
  q=max([q for q in queries if q['kind']=='WindPosition' and len(q['x'])==len(free) and q['response_ns']<=m['stamp_ns']+150000000],key=lambda q:q['response_ns'])
  service=decode_response(bytes.fromhex(q['response_cdr_hex']));assert np.array_equal(uv,service[:,:2])
  trace=list(csv.DictReader((native/'runtime/physical_clock_trace.csv').open()));near=[a for a in trace if a['reason']=='wind_service' and q['request_ns']-150000000<=int(a['receipt_ros_ns'])<=q['response_ns']+150000000];wi=sorted({int(a['wind_index']) for a in near});assert len(wi)==1
  field=next(x for x in g['fields'] if x['frame']==wi[0]);b=(P/field['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==field['sha256'];hashes[field['path']]=field['sha256']
  values=np.frombuffer(b[8:],'<f4').reshape(-1,3);xyz=np.asarray(np.c_[q['x'],q['y'],q['z']],np.float32);ijk=np.trunc((xyz-minimum.astype('f4'))/np.float32(step)).astype(int);flat=ijk[:,0]+dims[0]*(ijk[:,1]+dims[1]*ijk[:,2]);assert np.array_equal(service,values[flat])
  out.append(dict(case=case,epoch=ep,true_source_support=support(e['metadata']['source_xyz']),actual_native_input_equals_captured_wind_service=True,service_equals_actual_3d_field=True,wind_frame=wi[0],forward_wind_query_z_unique=np.unique(xyz[:,2]).tolist(),horizontal_speed_mean=float(np.mean(np.linalg.norm(service[:,:2],axis=1))),vertical_abs_mean=float(np.mean(np.abs(service[:,2]))),vertical_abs_max=float(np.max(np.abs(service[:,2]))),native_uses_components='u,v only',new_worlds=0))
(R/'results/QUALIFIED_CONTEXT.json').write_text(json.dumps(out,indent=2))
(R/'lineage/PHYSICAL_CONTEXT_ASSETS_SHA256.json').write_text(json.dumps(hashes,indent=2))
with (R/'results/RECEIVER_3D_POINT_SUPPORT.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(receivers[0]));w.writeheader();w.writerows(receivers)
semantics=dict(status='HOLD_EVENT_OPERATOR_NOT_IDENTIFIED',native_prediction_event='At least one massless 2D filament centre occupies a cell in a recorded timestep, then fixed spatial blur',actual_event='Consumed PID concentration mean exceeds 0.1 ppm',native_filament_fields=['position.x','position.y'],source_point_files='2D source release positions only, not trajectories',missing_native_fields=['3D filament positions and vertical motion','filament age and radius/sigma','filament gas amount/mass or source strength mapping','sensor concentration superposition and response operator'],not_performed='No arbitrary occupancy-to-ppm factor, no threshold fit, no 3D model, no new physical world',distinction='World generation parameters and actual 3D fields exist, but do not turn the captured 2D model output into a calibrated PID event by themselves.')
(R/'results/EVENT_SEMANTICS.json').write_text(json.dumps(semantics,indent=2))
print(json.dumps(out,indent=2))

# Describe a still-uncontrolled ordinary explanation: finite propagation warmup.
# These are clocks and release counts, not evidence that longer warmup would help.
import bisect
timeline=[];horizons=[]
for item in plan['cases']:
 case,ep=item['case'],item['epoch'];m=item['metadata'];e=next(x for x in index['cases'] if x['case']==case);native=P/e['native_path'];params=plan['parameters_by_case'][case]
 ti=int((np.float32(item['truth'][0])-np.float32(m['origin_x']))/np.float32(m['cell_size']));tj=int((np.float32(item['truth'][1])-np.float32(m['origin_y']))/np.float32(m['cell_size']))
 up=native/f'runtime/updates/update_{ep}';tree=list(csv.DictReader((up/'final_tree.csv').open()))
 leaf=next(x for x in tree if x['has_children']=='0' and int(x['origin_i'])<=ti<int(x['origin_i'])+int(x['size_i']) and int(x['origin_j'])<=tj<int(x['origin_j'])+int(x['size_j']))
 cand=next(x for x in csv.DictReader((up/'candidates.csv').open()) if x['candidate_id']==leaf['node_id']);count=int(cand['point_count']);assert count%5==0
 steps=count//5-params['iterationsToRecord'];horizons.append(dict(case=case,epoch=ep,truth_parent=leaf['node_id'],captured_source_releases=count,warmup_steps=steps,warmup_seconds=steps*params['deltaTime']*2,record_seconds=params['iterationsToRecord']*params['deltaTime'],early_stability_rule='First simulated filament outside the domain, after minimum warmup; not a receiver-wise response convergence test'))
 trace=sorted(csv.DictReader((native/'runtime/physical_clock_trace.csv').open()),key=lambda x:int(x['receipt_ros_ns']));times=[int(x['receipt_ros_ns']) for x in trace]
 ev=np.loadtxt(native/'runtime/measurement_events.csv',delimiter=',',ndmin=2);ev=ev[ev[:,0]<=m['stamp_ns']]
 for stop in [2,4,5]:
  a=ev[ev[:,6]==stop]
  if not len(a):continue
  near=[trace[max(0,bisect.bisect_right(times,int(t))-1)] for t in a[:,0]]
  timeline.append(dict(case=case,epoch=ep,stop=stop,latest_loaded_snapshot_physical_age_min_s=min(float(x['frame_internal_s']) for x in near),latest_loaded_snapshot_physical_age_max_s=max(float(x['frame_internal_s']) for x in near),maximum_trace_age_s=max((int(t)-int(x['receipt_ros_ns']))/1e9 for t,x in zip(a[:,0],near)),interpretation='Latest logged loaded snapshot at each consumption timestamp; not exact per-PID acquisition ownership. A longer-lived real plume alone does not prove the short stationary approximation invalid.'))
for name,data in [('NATIVE_TRUE_SOURCE_FORWARD_HORIZON.csv',horizons),('OBSERVATION_PHYSICAL_AGE.csv',timeline)]:
 with (R/'results'/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
