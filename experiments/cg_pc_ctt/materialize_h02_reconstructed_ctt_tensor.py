#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
from ctt_bank_io import load_bank_first_hits

def sha256(path:Path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def rows(path):
    with path.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('bank_root',type=Path); ap.add_argument('analysis_manifest',type=Path)
    ap.add_argument('--out-dir',type=Path,required=True); a=ap.parse_args()
    rr=rows(a.analysis_manifest); a.out_dir.mkdir(parents=True,exist_ok=True)
    summary=[]
    for r in rr:
        case=r['case_id']; matches=sorted((a.bank_root/'banks').glob(f'{case}_*'))
        if len(matches)!=1: raise SystemExit(f'{case}: bank dir count {len(matches)}')
        phi,cxy,qxy,free_idx,contract=load_bank_first_hits(matches[0])
        out=a.out_dir/f'{case}.npz'
        np.savez_compressed(out, first_hit=phi, candidate_xy=cxy, query_xy=qxy, query_cell_index=free_idx,
            case_id=np.asarray(case), cluster_id=np.asarray(r['cluster_id']), seed=np.asarray(r['seed']),
            run_uuid=np.asarray(r['run_uuid']), source_update_id=np.asarray(int(r['source_update_id'])))
        summary.append({'case_id':case,'cluster_id':r['cluster_id'],'shape':list(phi.shape),'npz':str(out),'sha256':sha256(out)})
    payload={'contract':'H02_RECONSTRUCTED_CTT_TENSOR_V1','truth_used':False,'cases':len(summary),'items':summary}
    (a.out_dir/'MANIFEST.json').write_text(json.dumps(payload,indent=2),encoding='utf-8')
    print(json.dumps({'contract':payload['contract'],'cases':len(summary),'shapes':sorted({tuple(x['shape']) for x in summary})},indent=2))
if __name__=='__main__': main()
