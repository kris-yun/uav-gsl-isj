from common_n import *
code='''from pathlib import Path
import hashlib,json,shutil,time
d=Path(DATA).resolve();factor=d/'factorial';canon=d/'SHARED_IDENTICAL_CFD_INPUTS';assert not canon.exists();canon.mkdir()
def sh(p):return hashlib.sha256(p.read_bytes()).hexdigest()
folders=[p/'bank/wind' for p in factor.iterdir() if p.is_dir() and (p/'QUALIFICATION.json').exists()]
assert len(folders)==32
names=sorted(p.name for p in folders[0].iterdir());assert len(names)==11 and all(n.startswith('wind_iteration_') for n in names)
for n in names:shutil.copy2(folders[0]/n,canon/n)
expected={n:sh(canon/n) for n in names};proof=[]
for folder in folders:
 assert folder.resolve().is_relative_to(d) and not folder.is_symlink()
 assert sorted(p.name for p in folder.iterdir())==names and all(sh(folder/n)==expected[n] for n in names)
 bytes_before=sum((folder/n).stat().st_size for n in names)
 backup=folder.with_name('wind_verified_duplicate_backup');assert not backup.exists();folder.rename(backup)
 try:folder.symlink_to(canon,target_is_directory=True)
 except Exception:backup.rename(folder);raise
 assert all(sh(folder/n)==expected[n] for n in names)
 assert backup.resolve().is_relative_to(d) and not backup.is_symlink() and sorted(p.name for p in backup.iterdir())==names
 # Only these verified identical copies in this campaign are removed; canonical bytes and original CFD are preserved.
 shutil.rmtree(backup)
 proof.append({'logical_directory':str(folder),'canonical_directory':str(canon),'identical_original_bytes':bytes_before})
result={'status':'PASS_STORAGE_ONLY_DEDUPLICATION','science_content_SHA256_unchanged':True,'directories':proof,'CFD_files_SHA256':expected,'unique_canonical_bytes':sum((canon/n).stat().st_size for n in names),'redundant_storage_released_bytes':sum(r['identical_original_bytes'] for r in proof)-sum((canon/n).stat().st_size for n in names),'original_CFD_assets_modified':False,'physical_results_removed':False}
(d/'OWN_WIND_STORAGE_DEDUPLICATION.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
'''.replace('DATA',repr(DATA))
r=json.loads(run_remote(code,'owned_qualified_banks_identical_CFD_storage_dedup',180));dump(CORE/'OWN_WIND_STORAGE_DEDUPLICATION.json',r)
print(json.dumps({'status':r['status'],'saved_bytes':r['redundant_storage_released_bytes'],'science_input_bytes_preserved':True}))
