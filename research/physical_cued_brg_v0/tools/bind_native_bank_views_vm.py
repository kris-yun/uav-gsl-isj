"""Filter cached forward bank; no simulation and no test concentration read."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
ROOT=Path('/home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927');sys.path.insert(0,str(ROOT))
from pmfs_brg.bank import TemplateBank
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    out=ROOT/'legal_support_v2';cache=ROOT/'full_support'
    complete=json.loads((cache/'BANK_COMPLETE.json').read_text());masks=json.loads((out/'LEGAL_MASKS_COMPLETE.json').read_text())
    if (out/'LEGAL_SUPPORT_COMPLETE.json').exists():
        old=json.loads((out/'LEGAL_SUPPORT_COMPLETE.json').read_text())
        assert old['original_complete_sha256']==sha(cache/'BANK_COMPLETE.json')
        for row in old['banks']:assert sha(out/f'env_{row["environment"]}_bank.npz')==row['bank_sha256']
        print('EXISTING_NATIVE_LEGAL_VIEWS_HASH_VERIFIED');return
    reports=[]
    for e in range(3):
        source=(ROOT/'h01_native_rebuild/env_0_bank.npz') if e==0 else cache/f'env_{e}_bank.npz';b=TemplateBank.load(source)
        row=json.loads((ROOT/'h01_native_rebuild/BANK_COMPLETE.json').read_text()) if e==0 else next(x for x in complete['banks'] if x['environment']==e);assert sha(source)==row['bank_sha256']
        cells=np.flatnonzero(np.fromfile(out/f'env_{e}_occupancy.u8',np.uint8)==1)
        assert set(cells.tolist())<=set(b.cells.tolist())
        take=[b.ids.index(f'pmfs_{int(c)%b.nx}_{int(c)//b.nx}') for c in cells]
        meta={**b.meta,'support_rule':masks['rule'],'original_model_bank_sha256':sha(source),'legal_mask_sha256':sha(out/f'env_{e}_occupancy.u8')}
        filtered=TemplateBank(meta,np.array(b.ids)[take],b.xy[take],b.cells[take],b.p[take],b.u[take]);filtered.save(out/f'env_{e}_bank.npz')
        with np.load(ROOT/f'data/open/env_{e}_open.npz',allow_pickle=False) as z:
            labels=z['source_ids'];indices=[filtered.ids.index(str(x)) for x in labels]
        reports.append({'environment':e,'original_cached_candidates':len(b.ids),'candidates':len(filtered.ids),'source_ids':list(filtered.ids),'truth_indices':indices,'bank_id':filtered.fingerprint,'bank_sha256':sha(out/f'env_{e}_bank.npz'),'original_bank_sha256':sha(source)})
    report={'banks':reports,'original_complete_sha256':sha(cache/'BANK_COMPLETE.json'),'mask_manifest_sha256':sha(out/'LEGAL_MASKS_COMPLETE.json'),'rule':masks['rule'],'new_forward':'user-authorized H01 only:596x11x8; H02 and H03 reused','no_new_plume':True,'test_truth_not_network_input':True}
    (out/'LEGAL_SUPPORT_COMPLETE.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
