#!/usr/bin/env python3
"""Replace only model cues/support. Keep all original gas, routes and splits."""
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from pmfs_brg.bank import TemplateBank

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data',required=True); ap.add_argument('--banks',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    src=Path(a.data); banks=Path(a.banks); out=Path(a.out); out.mkdir(parents=True,exist_ok=False)
    reports=[]
    for e in range(3):
        b=TemplateBank.load(banks/f'env_{e}_bank.npz')
        with np.load(src/f'env_{e}_open.npz',allow_pickle=False) as old:
            truth_ids=old['source_ids']; truth_indices=np.array([b.ids.index(str(i)) for i in truth_ids],dtype=np.int64)
            p,u=b.project(old['probe_xy'],(.2,.2))
            occ=old['occupancy']; assert b.meta.get('support_rule')
            # Preserve original geometry-only route graph; source support uses Native legal mask.
            legal=np.zeros(b.n,dtype=np.uint8);legal[b.cells]=1
            np.savez_compressed(out/f'env_{e}_open.npz',concentration=old['concentration'],probe_xy=old['probe_xy'],source_xy=b.xy,
                source_ids=np.array(b.ids),p=p,rawu=u,occupancy=occ,metadata=np.array(json.dumps(b.meta)),truth_candidate_indices=truth_indices,native_legal_occupancy=legal)
        with np.load(out/f'env_{e}_open.npz') as new, np.load(src/f'env_{e}_open.npz') as old:
            assert np.array_equal(new['concentration'],old['concentration'])
            assert np.array_equal(new['probe_xy'],old['probe_xy'])
        reports.append({'environment':e,'candidates':len(b.ids),'truth_candidate_indices':truth_indices.tolist(),
            'bank_id':b.fingerprint,'bank_sha256':sha(banks/f'env_{e}_bank.npz'),'data_sha256':sha(out/f'env_{e}_open.npz'),
            'original_data_sha256':sha(src/f'env_{e}_open.npz')})
    manifest={'role':'NATIVE_LEGAL_FULL_SUPPORT_OPEN_TRAINING','original_manifest_sha256':sha(src/'manifest.json'),
        'environments':reports,'route_geometry_unchanged':True,'candidate_legality':'actual fine z0.20 slice -> Native scale3 reduction -> Native prune','new_plumes':0,'house03_training_observations':0,
        'train_groups':'e/s/r, r=0..11 unchanged','dev_groups':'e/s/r, r=12..15 unchanged',
        'independent_train_plumes':216,'independent_dev_plumes':72}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n'); print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
