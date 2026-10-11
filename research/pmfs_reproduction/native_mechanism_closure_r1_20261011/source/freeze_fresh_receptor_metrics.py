from common_n import *
import numpy as np,csv
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8',newline='')))
D=Path('D:/ZYC/A-gas/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011');freeze=D/'confirmation_reference_freeze';candidates=['C7','K2','B000','B001','B002'];o0=[];o1=[];ppm=[]
for c in candidates:
 a=[];b=[];d=[]
 for i in [0,1]:
  folder=D/f'readout/PUBLIC_B_{c}_{i}';ev=rows(folder/'EVENTS_O1.csv');qm={r['query_id']:r for r in rows(folder/'QUERY_OUTPUT.csv')}
  indices=[int(np.floor((float(e['x'])-float(np.float32(-7.55)))/.25))+34*int(np.floor((float(e['y'])-float(np.float32(-7.88)))/.25)) for e in ev]
  with np.load(folder/'READOUT_FIELDS.npz',allow_pickle=False) as z:a.append([float(z['O0'][n,k]) for n,k in enumerate(indices)])
  b.append([int(e['event_hit']) for e in ev]);d.append([float(qm['r'+str(n)]['ppm_float32']) for n in range(50)])
 o0.append(np.mean(a,axis=0));o1.append(np.mean(b,axis=0));ppm.append(np.mean(d,axis=0))
p=freeze/'FIXED_RECEPTOR_PREDICTIONS.npz';assert not p.exists();np.savez_compressed(p,O0=np.array(o0),O1=np.array(o1),O1_ppm=np.array(ppm),candidate_order=np.array(candidates))
dump(CORE/'FRESH_RECEPTOR_METRIC_FREEZE.json',dict(status='FROZEN_BEFORE_FRESH_PHYSICS',SHA256=sha(p),field_path=DATA+'/confirmation_reference_freeze/'+p.name,
 metrics='Per-realization Brier on50 fixed time-indexed receiver predictions, blocks grouped into10 stops; O0 native-cell raw centre occupancy, O1 native PID event. O1 only ppm MAE/RMSE, O0 never ppm.',
 note='These direct receiver predictions differ from stationary full-grid frequency fields used for native map similarity; report separate meanings; no tuning on fresh outputs',candidate_order=candidates))
assert not (D/'fresh/CAMPAIGN_STARTED.json').exists(),'Fresh physics already began before metric freeze'
print('PASS_PRE_FRESH_RECEPTOR_PREDICTION_FREEZE')
