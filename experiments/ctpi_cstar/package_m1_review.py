"""Package this M1 work only; preserve raw bytes and exclude unrelated work."""
import argparse,gzip,hashlib,json,shutil,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PACK=ROOT/'evidence/m1_review_upload_20260912'
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--restore',action='store_true');args=parser.parse_args()
    if args.restore:
        manifest=json.loads((PACK/'manifest.json').read_text())
        for entry in manifest['files']:
            if entry['encoding']!='gzip': continue
            target=(ROOT/entry['original']).resolve()
            if not target.is_relative_to(ROOT): raise ValueError('unsafe restore path')
            if target.exists():
                if digest(target)!=entry['sha256']: raise ValueError(f'existing different file: {target}')
                continue
            packed=ROOT/entry['stored']
            if digest(packed)!=entry['stored_sha256']: raise ValueError('packed hash mismatch')
            target.parent.mkdir(parents=True,exist_ok=True)
            with gzip.open(packed,'rb') as src,target.open('xb') as dst: shutil.copyfileobj(src,dst)
            if digest(target)!=entry['sha256']: raise ValueError('restored hash mismatch')
        print('M1_RESTORE_HASH_VERIFIED');return
    PACK.mkdir(exist_ok=False)
    names=subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z','--','evidence'],cwd=ROOT).decode().split('\0')
    names=sorted(p for p in names if p.startswith('evidence/cstar_m1_') or p=='evidence/m1_causal_theory_search_20260909.txt')
    records=[];stage=[]
    for name in names:
        p=ROOT/name;item={'original':name,'bytes':p.stat().st_size,'sha256':digest(p)}
        if p.stat().st_size>1024*1024:
            dest=PACK/'raw'/Path(name+'.gz');dest.parent.mkdir(parents=True,exist_ok=True)
            with p.open('rb') as src,dest.open('xb') as raw:
                with gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0,compresslevel=6) as gz: shutil.copyfileobj(src,gz)
            item.update(stored=dest.relative_to(ROOT).as_posix(),encoding='gzip',stored_sha256=digest(dest))
        else: item.update(stored=name,encoding='identity',stored_sha256=item['sha256'])
        records.append(item);stage.append(item['stored'])
    proposal=Path('D:/LeStoreDownload/PMFS_M1_THEORY_FREEZE_V3_C2_EVIDENCE_BOUND_20260910.zip')
    dest=PACK/proposal.name;shutil.copyfile(proposal,dest)
    manifest={'scope':'current M1 progress; unrelated historical scratch/checkpoints not added',
       'status':'NOT_CLOSED_LOOP_EFFECTIVE','base_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
       'proposal':{'path':dest.relative_to(ROOT).as_posix(),'sha256':digest(dest),'status':'user-supplied proposal, not endorsed execution instructions'},'files':records}
    (PACK/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    # Explicit pathspec list, no git add-all.
    stage.extend([dest.relative_to(ROOT).as_posix(),(PACK/'manifest.json').relative_to(ROOT).as_posix()])
    subprocess.run(['git','add','--',*stage],cwd=ROOT,check=True)
    print('files',len(records),'raw_MB',round(sum(r['bytes'] for r in records)/1e6,2),'stored_MB',round(sum((ROOT/r['stored']).stat().st_size for r in records)/1e6,2))
if __name__=='__main__': main()
