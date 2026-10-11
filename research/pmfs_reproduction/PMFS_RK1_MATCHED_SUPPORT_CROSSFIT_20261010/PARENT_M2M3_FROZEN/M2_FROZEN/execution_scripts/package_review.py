"""Freeze and package completed evidence; rerun read-only verification on fresh extraction."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import csv,hashlib,json,shutil,subprocess,zipfile
W=Path(__file__).resolve().parent
BASE=W.parents[1]
O=BASE/'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(path,obj):
    assert not path.exists(),path
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
# Keep actual operation scripts, including resource guards, and the final preparation provenance.
for p in W.glob('*.py'):
    dest=O/'execution_scripts'/p.name
    if dest.exists():assert sha(dest)==sha(p),(p,dest)
    else:shutil.copy2(p,dest)
for p in W.iterdir():
    if p.is_file() and p.suffix in ('.stderr','.stdout'):
        dest=O/'execution_scripts'/p.name
        if dest.exists():assert sha(dest)==sha(p)
        else:shutil.copy2(p,dest)
attr=O/'.gitattributes'
if not attr.exists():attr.write_text('* -text\n',encoding='utf-8')
assert (O/'independent_raw_query_verify/verify_raw_queries.py').exists()
pre=subprocess.run([sys.executable,'-B',str(O/'verify_m2.py'),'--root',str(O),'--skip-package-hashes'],capture_output=True,timeout=60)
assert pre.returncode==0,pre.stderr.decode(errors='replace')
pre_result=json.loads(pre.stdout)
write(O/'VERIFICATION_RESULT.json',dict(stage='pre_final_manifest_all_numerical_checks',**pre_result))
manifest={p.relative_to(O).as_posix():sha(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name!='SHA256_MANIFEST.json'}
write(O/'SHA256_MANIFEST.json',manifest)
after=subprocess.run([sys.executable,'-B',str(O/'verify_m2.py'),'--root',str(O)],capture_output=True,timeout=60)
assert after.returncode==0,after.stderr.decode(errors='replace')
(W/'FINAL_DIRECTORY_VERIFY.json').write_bytes(after.stdout)
archive=BASE/'outputs'/(O.name+'_REVIEW.zip')
assert not archive.exists()
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9,strict_timestamps=False) as z:
    for p in sorted(O.rglob('*')):
        if p.is_file():z.write(p,p.relative_to(O).as_posix())
fresh=W/'fresh_zip_verify'
assert not fresh.exists();fresh.mkdir()
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for n in z.namelist():assert (fresh/n).resolve().is_relative_to(fresh.resolve())
    z.extractall(fresh)
final=subprocess.run([sys.executable,'-B',str(fresh/'verify_m2.py'),'--root',str(fresh)],capture_output=True,timeout=60)
assert final.returncode==0,final.stderr.decode(errors='replace')
q=dict(verdict='PASS_FRESH_ZIP_HASH_AND_READ_ONLY_RECOMPUTATION',zip_name=archive.name,zip_bytes=archive.stat().st_size,zip_SHA256=sha(archive),zip_members=len(manifest)+1,hashed_members=len(manifest),fresh_verification=json.loads(final.stdout),new_experiments_in_packaging=0)
write(archive.with_suffix('.verification.json'),q)
archive.with_suffix('.sha256.txt').write_text(q['zip_SHA256']+'  '+archive.name+'\n',encoding='ascii')
print(json.dumps(q,ensure_ascii=False,indent=2))
