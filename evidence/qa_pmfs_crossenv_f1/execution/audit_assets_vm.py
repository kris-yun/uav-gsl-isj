#!/usr/bin/env python3
"""Check historical assets by hashes; fresh target arrays remain unopened."""
import csv,hashlib,json,platform
from pathlib import Path
import numpy as np
import scipy
ROOT=Path('/home/zyc/qa_pmfs_crossenv_f1_20260926')
HIST=ROOT/'historical'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def rows(p):
    with p.open(newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
def dump(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True,allow_nan=False)+'\n')
def main():
    ROOT.joinpath('audit').mkdir(exist_ok=False)
    archive=Path('/home/zyc/JTD_E2_RAW_180_20260925.tar.gz')
    try:
        for line in (ROOT/'protocol/SHA256SUMS.txt').read_text().splitlines():
            expected,name=line.split('  ',1);assert sha(ROOT/'protocol'/name)==expected,name
        expected_files={}
        for name in ['JTD_E2_INPUT_SHA256.tsv','JTD_E2_OUTPUT_SHA256.tsv']:
            for r in rows(HIST/name):expected_files[Path(r['path'].replace('\\','/')).name]=r['sha256']
        for p in HIST.iterdir():
            if p.is_file() and p.name in expected_files:assert sha(p)==expected_files[p.name],p.name
        assert sha(archive)=='dbd85a3199c73619c6a93c4e39bf137359d0d38037c2b64e19be61a6315ef842'
        ref=rows(HIST/'JTD_E2_REFERENCE_12_MANIFEST.tsv');target=rows(HIST/'JTD_E2_FRESH_TARGET_MANIFEST.tsv')
        assert len(ref)==216 and len(target)==72
        assert len({(int(r['environment_index']),int(r['source_index']),int(r['reference_index'])) for r in ref})==216
        assert len({(int(r['environment_index']),int(r['source_index']),int(r['new_index'])) for r in target})==72
        R=np.load(HIST/'JTD_E2_REFERENCE_12x10x30.npy',allow_pickle=False)
        assert R.shape==(3,6,12,10,30) and R.dtype==np.float32 and np.isfinite(R).all() and (R>=0).all()
        probes=rows(HIST/'E1_HOUSE_PROBE_CONTRACTS.tsv');geo=rows(HIST/'E1_HOUSE_SOURCE_PANELS.tsv')
        envs=[('House01','1,3-2,4_fast'),('House02','3,5-1_slow'),('House02','4,5-3_slow')]
        inventory=[];support=[]
        for ei,(house,wind) in enumerate(envs):
            for si in range(6):
                group=[r for r in ref if int(r['environment_index'])==ei and int(r['source_index'])==si]
                assert len(group)==12 and {int(r['reference_index']) for r in group}==set(range(12))
                sid=group[0]['source_id'];g=next(g for g in geo if g['house']==house and g['source_id']==sid)
                support.append({'environment_index':ei,'house':house,'wind':wind,'source_index':si,'source_id':sid,'xy':[float(g['x_m']),float(g['y_m'])],'z':float(g['z_m'])})
        for role,records in [('reference',ref),('target',target)]:
            for r in records:
                ei=int(r['environment_index']);si=int(r['source_index'])
                assert (r['house'],r['wind'])==envs[ei]
                run=Path(r['run_dir']);assert run.is_relative_to('/home/zyc') and 'SEALED' not in str(run)
                cp=run/'concentration.npy';assert sha(cp)==r['cube_sha256'],str(cp)
                pp=run/'pooled.npy'
                if r.get('pooled_sha256'):assert sha(pp)==r['pooled_sha256'],str(pp)
                if role=='reference':
                    ri=int(r['reference_index']);pvec=R[ei,si,ri]
                    if r.get('pooled_value_sha256'):assert hashlib.sha256(pvec.tobytes()).hexdigest()==r['pooled_value_sha256']
                    cube=np.load(cp,allow_pickle=False)
                    ps=sorted([p for p in probes if p['house']==r['house']],key=lambda p:int(p['probe_rank']))
                    assert len(ps)==30
                    repool=np.stack([cube[:,int(p['native_x0']):int(p['native_x1_exclusive']),int(p['native_y0']):int(p['native_y1_exclusive'])].mean(axis=(1,2)) for p in ps],axis=1).astype(np.float32)
                    assert np.array_equal(repool,pvec)
                inventory.append({'role':role,'environment_index':ei,'source_index':si,'source_id':r['source_id'],'requested_seed':r['requested_seed'],'run_dir':str(run),'cube_sha256':r['cube_sha256'],'pooled_sha256':r.get('pooled_sha256','')})
        assert set((r['environment_index'],r['requested_seed']) for r in ref).isdisjoint(set((r['environment_index'],r['requested_seed']) for r in target))
        record={'status':'EXACT_EXISTING_CROSSENV_ASSETS_FOUND','source_units':18,'references_per_source':12,'targets_per_source':4,'reference_raw_cubes_verified':216,'target_raw_cubes_hash_verified':72,'reference_repool_exact':216,'fresh_target_values_read':False,'target_truth_ranks_read':False,'archive_sha256':sha(archive),'historical_file_hashes':{p.name:sha(p) for p in sorted(HIST.iterdir()) if p.is_file()},'source_support':support,'inventory':inventory,'environment':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__}}
        dump(ROOT/'audit/ASSET_AUDIT.json',record);print('QA_F1_ASSET_AUDIT_PASS reference=216 target=72 target_values_unopened')
    except Exception as e:
        dump(ROOT/'audit/ASSET_AUDIT.json',{'status':'QA_F1_HOLD_EXISTING_CROSSENV_ASSETS_NOT_FOUND','error':str(e),'fresh_target_values_read':False});raise
if __name__=='__main__':main()
