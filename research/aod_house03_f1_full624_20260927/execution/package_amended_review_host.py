#!/usr/bin/env python3
"""Independent review data; raw simulations remain separately archived on C."""
import hashlib,json,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
C=Path(r'C:\Users\50176\Downloads')
O=C/'AOD_F1_AMENDED_EXECUTION_20260927'
RAW=C/'AOD_F1_AMENDED_RAW_ARCHIVE_20260927'
SHARED=Path(r'D:\ZYC\A-gas\workspace\_staging\AOD_F1_AMENDED_TARGETS_20260927')
OUT=C/'AOD_HOUSE03_F1_FULL624_AMENDED_REVIEW_20260927.zip'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def main():
    assert not OUT.exists()
    state=json.loads((O/'AMENDED_FINAL_EXECUTION_STATE.json').read_text())
    assert state['completed_targets']==96 and state['deterministic_scientific_repeat']
    registries=[json.loads(p.read_text()) for p in sorted(RAW.glob('*.archive.json'))]
    assert len(registries)==96 and all(r['verified'] for r in registries)
    for rec in registries:assert sha(Path(rec['archive_path']))==rec['sha256']
    files={}
    for folder in ['protocol','amplitude_implementation','templates','f0','execution','timebase_amendment']:
        for p in (R/folder).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:files[str(p.relative_to(R)).replace('\\','/')]=p
    for p in O.rglob('*'):
        if p.is_file():files['amended_execution/'+str(p.relative_to(O)).replace('\\','/')]=p
    original=C/'AOD_HOUSE03_F1_FULL624_REVIEW_20260927.zip'
    assert sha(original)=='de4fe418b9c4cf4b9377349436516bb77be0952bac1708be23f0308ea775d0b7'
    files['historical/'+original.name]=original
    for meta in sorted((O/'metadata').glob('*.json')):
        rec=json.loads(meta.read_text());name=meta.stem
        src=RAW/'source_0_replica_0' if rec['first_reused'] else SHARED/name
        for n in ['RESULT_TIME_MAP.tsv','RELEASE_TIME_METADATA.tsv','RUN_CONFIGURATION.json','generation.log']:
            assert sha(src/n)==rec['files_sha256'][n]
            files['raw_metadata/'+name+'/'+n]=src/n
    for p in RAW.glob('*.archive.json'):files['raw_archive_registry/'+p.name]=p
    inventory=[]
    with zipfile.ZipFile(OUT,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for n,p in sorted(files.items()):
            z.write(p,n);inventory.append(sha(p)+'  '+n+'\n')
        readme=('Historical HOLD is unchanged. This package contains the signed native-state amendment, '
          'all 96 full concentration cubes and exact path observations, full624 templates, candidate scores, '
          'unchanged B2/evaluator, scientific repeated output, raw clock metadata and all hashes. '
          '96 complete raw simulator directories are separately archived and verified on C drive; '
          'their locations, bytes and hashes are in raw_archive_registry. Raw data and original candidate bank were not deleted.\n')
        z.writestr('README_REVIEW.txt',readme)
        inventory.append(hashlib.sha256(readme.encode()).hexdigest()+'  README_REVIEW.txt\n')
        z.writestr('SHA256SUMS',''.join(inventory))
    with zipfile.ZipFile(OUT) as z:
        assert z.testzip() is None
        for line in z.read('SHA256SUMS').decode().splitlines():
            h,n=line.split('  ',1);assert hashlib.sha256(z.read(n)).hexdigest()==h,n
    report=dict(path=str(OUT),bytes=OUT.stat().st_size,sha256=sha(OUT),
        verified_inventory_entries=len(inventory),raw_archives=96,full_cubes=96)
    (C/'AOD_HOUSE03_F1_FULL624_AMENDED_REVIEW_20260927_METADATA.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
