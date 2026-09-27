#!/usr/bin/env python3
"""Read MODEL templates ONLY from the now-OPEN F1 review, never gas targets.
Infer unique grid from exact source indices and full-map size, verify every row.
Any ambiguity fails; no guessed ROS metadata. This is a cached-model test bank,
not a demonstration that full wind truth is available in flight.
"""
import sys,argparse,zipfile,io,json,csv,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from pmfs_brg.bank import TemplateBank

def main():
 a=argparse.ArgumentParser();a.add_argument('--review',required=True);a.add_argument('--out',required=True);args=a.parse_args()
 z=zipfile.ZipFile(args.review);names=['templates/CANDIDATE_SUPPORT.csv','templates/nominal_p_full_maps.npy','templates/nominal_rawu_full_maps.npy']
 rows=list(csv.DictReader(io.StringIO(z.read(names[0]).decode())));rows.sort(key=lambda r:int(r['source_index']))
 p=np.load(io.BytesIO(z.read(names[1])),allow_pickle=False);u=np.load(io.BytesIO(z.read(names[2])),allow_pickle=False)
 ids=[r['source_id'] for r in rows];ij=np.array([[int(t) for t in s.split('_')[1:]] for s in ids]);xy=np.array([[float(r['x']),float(r['y'])] for r in rows]);heights={float(r['z']) for r in rows}
 n=p.shape[1];dims=[(w,n//w) for w in range(1,n+1) if n%w==0 and w>ij[:,0].max() and n//w>ij[:,1].max()]
 if len(dims)!=1 or len(heights)!=1:raise ValueError('ambiguous grid/height; explicit metadata required')
 coeff=[]
 for axis in range(2):coeff.append(np.linalg.lstsq(np.stack((ij[:,axis]+.5,np.ones(len(ij))),1),xy[:,axis],rcond=None)[0])
 if abs(coeff[0][0]-coeff[1][0])>1e-8:raise ValueError('unequal cell dimensions')
 meta=dict(width=dims[0][0],height=dims[0][1],resolution=float(coeff[0][0]),origin_x=float(coeff[0][1]),origin_y=float(coeff[1][1]),height_m=heights.pop(),footprint_x_m=.2,footprint_y_m=.2,house='House03',wind='1-2,5_fast',environment_id='H03_nominal_model_only',unit='area_averaged_cell_count_proxy')
 bank=TemplateBank(meta,ids,xy,ij[:,0]+meta['width']*ij[:,1],p,u);bank.save(args.out)
 report={'bank_id':bank.fingerprint,'metadata':meta,'sources':len(ids),'read_members':names,'read_gas_arrays':False,'read_training_labels':False,'purpose':'624-candidate interface/latency test using model-generated maps'}
 Path(str(args.out)+'.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
