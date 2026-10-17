from pathlib import Path
import json,csv,collections,math,hashlib
import numpy as np
from parameters import read_parameters
R=Path(__file__).resolve().parents[1];W=R.parent;P=W/'NATIVE_PMFS_WIND_RECOVERY_20261014/PORTABLE_DATA';O=R/'results';index=json.loads((P/'CASE_INDEX.json').read_text());entries=index['cases'];groups={g['group']:g for g in index['field_groups']};cache={};rows=[];windows=[];sources={r['case']:r for r in json.loads((O/'geometry20.json').read_text())['cases']}
def write(name,data):
 keys=list(dict.fromkeys(k for r in data for k in r))
 with (O/name).open('w',newline='') as f:w=csv.DictWriter(f,keys);w.writeheader();w.writerows(data)
def stats(ppm,ts,threshold):
 y=np.asarray(ppm)>threshold;x=np.asarray(ppm,float);n=len(x);rho=None
 if n>=3 and np.std(y[:-1])>0 and np.std(y[1:])>0:rho=float(np.corrcoef(y[:-1],y[1:])[0,1])
 return dict(windows=n,hits=int(y.sum()),hit_fraction=float(y.mean()),mixed=bool(0<y.sum()<n),ppm_mean=float(x.mean()),ppm_min=float(x.min()),ppm_max=float(x.max()),ppm_variance=float(x.var()),transitions=int((y[1:]!=y[:-1]).sum()),lag1_binary_descriptive=rho,correlation_time_s=None,correlation_status='ABSTAIN_TOO_FEW_STOP_WINDOWS',first_stamp_ns=int(min(ts)),last_stamp_ns=int(max(ts)),stop_duration_s=float((max(ts)-min(ts))/1e9),consumed_window_ppm=json.dumps(x.tolist()))
for e in entries:
 c=e['case'];root=P/e['native_path'];ev=np.loadtxt(root/'runtime/measurement_events.csv',delimiter=',',ndmin=2);par,porig=read_parameters(root);g=e['group']
 if g not in cache:
  text=(P/groups[g]['grid_path']).read_text().splitlines();minimum=np.array([float(a) for a in text[0].split()[1:]]);dims=np.array([int(a) for a in text[2].split()[1:]]);cell=float(text[3].split()[1]);cells=np.array([[int(a) for a in l.split()] for l in text[4:] if l!=';'],np.int8).reshape(dims[2],dims[0],dims[1]);cache[g]=minimum,dims,cell,cells
 minimum,dims,cell,cells=cache[g];qp=[]
 for line in (root/'runtime/service_queries.jsonl').open():
  a=json.loads(line)
  if a['kind']=='GasPosition':qp.extend(zip(a['x'],a['y'],a['z']))
 qp=np.unique(np.array(qp),axis=0);assert len(qp)>0
 for stop in np.unique(ev[:,6]):
  a=ev[ev[:,6]==stop];pos=np.mean(a[:,4:6],axis=0);d=np.linalg.norm(qp[:,:2]-pos,axis=1);near=qp[d<=max(float(d.min())+1e-6,.02)];z=float(np.median(near[:,2]));ijk=np.floor((near-minimum)/cell).astype(int);inside=np.all((ijk>=0)&(ijk<dims),axis=1);valid=[]
  for ij,ok in zip(ijk,inside):valid.append(bool(ok and cells[ij[2],ij[0],ij[1]]==0))
  sensor='ALL_MATCHED_QUERY_POSITIONS_GAS_FREE' if all(valid) else 'INVALID_OR_AMBIGUOUS_3D_QUERY_POSITION';status=json.loads((root/'RUN_RESULT.json').read_text());native=json.loads((O/'native20_recomputed'/(c+'.json')).read_text());last=native['updates'][-1];row=dict(stratum='2026_corrected20',run=c,case=c,stop=int(stop),**stats(a[:,1],a[:,0],par['th_gas_present']),x=float(pos[0]),y=float(pos[1]),z=z,minimum_actual_query_xy_distance_m=float(d.min()),sensor_support=sensor,source_supported=sources[c]['native_source_supported'],source_exclusion_stage=sources[c]['exclusion_stage'],wind_speed_mean=float(a[:,2].mean()),wind_direction_circular_mean=float(np.angle(np.exp(1j*a[:,3]).mean())),wind_direction_resultant=float(abs(np.exp(1j*a[:,3]).mean())),original_outcome=native['status'],last_truth_rank=last['truth_strict_rank'],last_truth_mass=last['truth_cell_mass'],forward_matching='CAPTURED_FULL_MAPS_AND_FINAL_OWNERS',parameter_origin=porig);rows.append(row)
  for t in a:windows.append(dict(stratum='2026_corrected20',run=c,case=c,stop=int(stop),stamp_ns=int(t[0]),window_mean_ppm=float(t[1]),hit=bool(t[1]>par['th_gas_present']),wind_speed=float(t[2]),wind_direction=float(t[3]),x=float(t[4]),y=float(t[5]),z=z,sensor_support=sensor))
 # Preserve all actual unthresholded messages, not just the consumed window means.
 raw=0
 for line in (root/'runtime/raw_ros_cdr.jsonl').open():
  v=json.loads(line)
  if 'PID/Sensor_reading' in v['topic']:raw+=1
 (O/'RAW_PID_COUNTS.jsonl').open('a').write(json.dumps(dict(case=c,raw_pid_messages=raw,consumed_windows=len(ev)))+'\n')
write('OBSERVABLE_STOPS.csv',rows);write('OBSERVATION_WINDOWS.csv',windows)
# Supplementary 2024 historical repetitions: do not double-count B4 copied into EXT5.
E=W/'PMFS_OFFICIAL_REPRO_AUDIT_20261016/EXT5_3H_20261016_112419/observations';seen=set();extra=[]
extra_folders=list(sorted(E.iterdir()))
extra_folders += sorted((W/'PMFS_OFFICIAL_REPRO_AUDIT_20261016/PRO_NATIVE_PMFS_EXPORT').glob('P24_*_WALL5_VALID_V2_R0*'))
for folder in extra_folders:
 p=folder/'native_window_consumption.csv';v=folder/'native_events.csv'
 if not p.exists() or not v.exists():continue
 content=p.read_bytes();sha=hashlib.sha256(content).hexdigest()
 if sha in seen:continue
 seen.add(sha);tt=list(csv.DictReader(content.decode().splitlines()));tt=[a for a in tt if a['status']=='CONSUMED'];events=list(csv.DictReader(v.open()));goals=[(float(a['native_log_wall_unix_s']),a['message']) for a in events if 'Moving to' in a['message']]
 if not tt:continue
 pp=json.loads((folder/'resolved_GSL_parameters.json').read_text());threshold=.1
 for stop in sorted(set(sum(t<=float(a['node_clock_ns'])/1e9 for t,_ in goals) for a in tt)):
  aa=[a for a in tt if sum(t<=float(a['node_clock_ns'])/1e9 for t,_ in goals)==stop];case=folder.name.split('_')[1];extra.append(dict(stratum='2024_historical_EXT5',run=folder.name,case=case,stop=stop,**stats([float(a['concentration_mean_ppm']) for a in aa],[int(a['node_clock_ns']) for a in aa],threshold),sensor_support='SEE_GEOMETRY_AND_NAV_AUDITS_NOT_INFERRED_FROM_ZERO',forward_matching='NO_MATCHED_FINEST_FORWARD_MAPS',threshold=threshold))
write('SUPPLEMENTARY_HISTORICAL_STOPS.csv',extra)
write('02_ALL_STOPS_CONDITION_LEDGER.csv',rows+extra)
summary=dict(native20_stops=len(rows),native20_windows=len(windows),native20_mixed_stops=sum(a['mixed'] for a in rows),native20_mixed_cases=sorted({a['case'] for a in rows if a['mixed']}),source_supported_mixed_cases=sorted({a['case'] for a in rows if a['mixed'] and a['source_supported']}),invalid_or_ambiguous_sensor_stops=sum(a['sensor_support']!='ALL_MATCHED_QUERY_POSITIONS_GAS_FREE' for a in rows),historical_supplementary_runs=len({a['run'] for a in extra}),historical_mixed_cases=sorted({a['case'] for a in extra if a['mixed']}),scope='Stop windows are dependent; twenty configurations use one realized world each. No significance test treating stops as worlds.')
(O/'SCREEN_SUMMARY.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
