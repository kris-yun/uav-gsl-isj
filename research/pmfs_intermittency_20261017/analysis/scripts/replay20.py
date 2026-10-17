from pathlib import Path
import json,csv,sys,time,subprocess
import numpy as np,yaml
from parameters import read_parameters
R=Path(__file__).resolve().parents[1];P=R.parent/'NATIVE_PMFS_WIND_RECOVERY_20261014/PORTABLE_DATA'
rows=[];O=R/'results/replay20';O.mkdir(exist_ok=True)
entries=json.loads((P/'CASE_INDEX.json').read_text())['cases']
if len(sys.argv)>1:entries=[e for e in entries if e['case'] in sys.argv[1:]]
for e in entries:
 c=e['case'];root=P/e['native_path'];ev=np.loadtxt(root/'runtime/measurement_events.csv',delimiter=',',ndmin=2);updates=sorted((root/'runtime/updates').glob('*/COMPLETE.txt'),key=lambda p:int(p.parent.name.split('_')[-1]));first=updates[0].parent;m=json.loads((first/'metadata.json').read_text());inp=list(csv.DictReader((first/'input.csv').open()));free=np.array([i for i,a in enumerate(inp) if a['occupancy']=='1']);par,parameter_origin=read_parameters(root);settings=[par.get('hitPriorProbability',.3),par['kernelSigma'],par['kernelStretchConstant'],par['confidenceSigmaSpatial'],par['confidenceMeasurementWeight'],par['localEstimationWindowSize']]
 lines=[' '.join(map(str,[m['width'],m['height'],m['origin_x'],m['origin_y'],m['cell_size'],len(free),len(ev)])),' '.join(map(str,settings)),' '.join(map(str,free))]
 for a in ev:lines.append(' '.join(map(str,[a[4],a[5],int(a[1]>par['th_gas_present']),a[2],a[3]])))
 (O/(c+'.txt')).write_text('\n'.join(lines)+'\n');start=time.time();q=subprocess.run([str(R/'build/replay2026'),str(O/(c+'.txt')),str(O/(c+'.f64'))],capture_output=True,text=True)
 (R/'logs'/('replay_'+c+'.json')).write_text(json.dumps(dict(command=q.args,returncode=q.returncode,elapsed_s=time.time()-start,stderr=q.stderr),indent=2))
 if q.returncode:
  rows.append(dict(case=c,status='CPP_REPLAY_FAILED',returncode=q.returncode));continue
 data=np.fromfile(O/(c+'.f64'),dtype='<f8').reshape(len(ev),len(free),4)
 for marker in updates:
  u=marker.parent;m=json.loads((u/'metadata.json').read_text());n=int(np.searchsorted(ev[:,0],m['stamp_ns'],side='right'));b=list(csv.DictReader((u/'input.csv').open()));log=np.array([float(b[i]['logOdds']) for i in free]);conf=np.array([float(b[i]['confidence']) for i in free]);le=float(abs(log-data[n-1,:,0]).max());ce=float(abs(conf-data[n-1,:,1]).max());rows.append(dict(case=c,update=u.name,windows=n,free_cells=len(free),log_odds_max_error=le,confidence_max_error=ce,status='PASS' if le<1e-10 and ce<1e-12 else 'HOLD_HISTORY_BINDING'))
 for row in rows:
  if row['case']==c:row['parameter_origin']=parameter_origin
 (R/'results/REPLAY20_QA.json').write_text(json.dumps(rows,indent=2));print(c,rows[-1],flush=True)
