#!/usr/bin/env python3
"""Import ONLY historical OPEN H01/H02 arrays and MODEL-generated templates.
House03 gas arrays are not read by this importer. No new plume/forward is run.
"""
import argparse,io,json,csv,zipfile,hashlib,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from pmfs_brg.bank import TemplateBank

def rows(z,name):return list(csv.DictReader(io.StringIO(z.read(name).decode()),delimiter='\t' if name.endswith('.tsv') else ','))
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return h.hexdigest()

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--marked-zip',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
 out=Path(a.out);out.mkdir(parents=True,exist_ok=True);z=zipfile.ZipFile(a.marked_zip)
 envs=json.loads(z.read('inputs/environment_manifest.json'))
 R=np.load(io.BytesIO(z.read('protocol/JTD_E2_REFERENCE_12x10x30.npy')),allow_pickle=False)
 Y=np.load(io.BytesIO(z.read('protocol/JTD_E2_FRESH_TARGET_10x30.npy')),allow_pickle=False)
 # These are historical exposed data. The variable/file name 'FRESH' does not
 # restore a fresh-evaluation status in this new method's development.
 allY=np.concatenate((R,Y),axis=2)
 if allY.shape!=(3,6,16,10,30):raise ValueError(f'unexpected shape {allY.shape}')
 outputs=[]
 for e,env in enumerate(envs):
  meta=json.loads(z.read(f'inputs/env_{e}/meta.json'));meta.update(environment_id=f'env_{e}',house=env['house'],wind=env['wind'],height_m=.2,footprint_x_m=.2,footprint_y_m=.2,unit='area_averaged_cell_count_proxy')
  ss=sorted(rows(z,f'inputs/env_{e}/sources.csv'),key=lambda v:int(v['source_index']))
  pp=sorted(rows(z,f'inputs/env_{e}/probes.csv'),key=lambda v:int(v['probe_rank']))
  ids=[v['source_id'] for v in ss];xy=np.array([[float(v['x']),float(v['y'])] for v in ss])
  cells=np.array([int(v.split('_')[1])+meta['width']*int(v.split('_')[2]) for v in ids])
  n=meta['width']*meta['height']; vals={}
  for kind in ['p','rawu']:
   means=[]
   for s in range(6):
    arr=[]
    for k in range(11):
     for r in range(1,9):
      key=f'forward/env_{e}/source_{s}/state_{k}_replica_{r}.{kind}.f32'
      x=np.frombuffer(z.read(key),dtype='<f4').astype('float64')
      if x.shape!=(n,):raise ValueError(key)
      arr.append(x)
    means.append(np.mean(arr,axis=0))
   vals[kind]=np.stack(means)
  # Validate without flooring amplitude. Boundary p roundoff only is rejected.
  bank=TemplateBank(meta,ids,xy,cells,vals['p'],vals['rawu']); bp=out/f'env_{e}_bank.npz';bank.save(bp)
  probes=np.array([[float(v['x']),float(v['y'])] for v in pp]);pr,ur=bank.project(probes)
  occ=np.frombuffer(z.read(f'inputs/env_{e}/occupancy.u8'),dtype='uint8')
  path=out/f'env_{e}_open.npz'
  np.savez_compressed(path,concentration=allY[e],probe_xy=probes,source_xy=xy,source_ids=np.array(ids),p=pr,rawu=ur,occupancy=occ,metadata=np.array(json.dumps(meta)))
  outputs.append(dict(env=e,house=env['house'],wind=env['wind'],source_count=6,trajectories=96,bank=str(bp.name),bank_sha256=sha(bp),bank_id=bank.fingerprint,data=str(path.name),data_sha256=sha(path)))
 manifest={'status':'OPEN_DEVELOPMENT_ONLY','input_sha256':sha(a.marked_zip),'new_plume':0,'new_forward':0,'environments':outputs,'truth_data_role':'training/development, never runtime context','source_support_warning':'six candidates per imported environment, not dense training coverage'}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
