"""Validate smoke and convert raw native queries into frozen observation contract."""
import pathlib,json,re,hashlib
import numpy as np,pandas as pd
ROOT=pathlib.Path(__file__).resolve().parents[3];OUT=ROOT/'evidence/lakeshore_observability_r0_r2'
def parse(p):
 m=re.fullmatch(r'(N0|L1|F1|F2)_x(\d+)_y(-?\d+)_r(\d+)_seed(\d+)',p.stem)
 if not m:return None
 return m[1],int(m[2]),int(m[3]),int(m[4]),int(m[5])
def main():
 files=[p for p in (OUT/'observations').glob('*.csv') if parse(p)]
 reference=None;rows=[]
 for p in sorted(files):
  d=pd.read_csv(p);meta=parse(p)
  assert len(d)==1200 and np.isfinite(d.to_numpy()).all() and (d.concentration>=0).all()
  assert sorted(d.z.unique())==[10,30,60,100]
  trajectory=d[['time','x','y','z']].to_numpy()
  if reference is None:reference=trajectory
  assert np.array_equal(reference,trajectory),'unequal XY-time trajectories'
  assert np.array_equal(d.time.unique(),np.arange(300))
  rows.append({'file':p.name,'environment':meta[0],'source_x':meta[1],'source_y':meta[2],'source_z':1,'release_filaments_s':meta[3],'plume_seed':meta[4],'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 pd.DataFrame(rows).to_csv(OUT/'observation_manifest.csv',index=False)
 (OUT/'fixed_path_contract.csv').write_text(pd.DataFrame(reference,columns=['time','x','y','z']).to_csv(index=False))
 if len(files)==12:
  r={'pass':True,'realizations':12,'rows':14400,'same_XY_time_all_conditions':True,'frequency_Hz':1,'duration_s':300,'heights_m':[10,30,60,100],'phase':'smoke_output_contract_only_no_gate_scoring'}
  (OUT/'smoke_matrix_validation.json').write_text(json.dumps(r,indent=2));print(r)
 else:print('validated',len(files),'realizations')
if __name__=='__main__':main()
