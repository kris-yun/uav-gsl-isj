"""Post-run resource, original evidence checks and complete native archive."""
from pathlib import Path
import csv,hashlib,json,shutil,zipfile
R=Path('/home/zyc/ros2_ws/m0_clean_support_r0_20261007/e2_sentinel');BASE=R.parent;OUT=R.parent.parent/'M0_E2_RAW_NATIVE_20261007.zip'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
progress=json.loads((R/'E2_PROGRESS.json').read_text());assert progress['completed']==4 and progress['E3_runs']==0
with (BASE/'NATIVE_ALL_FILES_SHA256.csv').open() as f:old=list(csv.DictReader(f))
for q in old:assert sha(BASE/q['path'])==q['sha256'],q['path']
m={r.split(':')[0]:int(r.split()[1])*1024 for r in Path('/proc/meminfo').read_text().splitlines() if len(r.split())>1 and r.split()[1].isdigit()};disk=shutil.disk_usage(R).free;ram=m['MemAvailable'];assert disk>=12*1024**3 and ram>=3*1024**3
(R/'E2_POST_RESOURCE_AND_PARENT_VERIFICATION.json').write_text(json.dumps({'disk_free_bytes':disk,'RAM_available_bytes':ram,'resource_gate_pass':True,'original_2551_E1_native_files_unchanged':True,'new_wrong_wind_runs':4,'new_baseline_runs':0,'remaining_28_runs':0,'runtime_stop':True},indent=2)+'\n')
files=sorted(p for p in R.rglob('*') if p.is_file());manifest=R/'NATIVE_ALL_FILES_SHA256.csv';assert not manifest.exists() and not OUT.exists()
with manifest.open('w') as f:
    w=csv.writer(f,lineterminator='\n');w.writerow(['path','bytes','sha256'])
    for p in files:w.writerow([p.relative_to(R).as_posix(),p.stat().st_size,sha(p)])
files.append(manifest)
with zipfile.ZipFile(OUT,'x',zipfile.ZIP_DEFLATED,compresslevel=5) as z:
    for p in files:z.write(p,p.relative_to(R).as_posix())
with zipfile.ZipFile(OUT) as z:
    assert z.testzip() is None
    for p in files:assert hashlib.sha256(z.read(p.relative_to(R).as_posix())).hexdigest()==sha(p)
out={'path':str(OUT),'bytes':OUT.stat().st_size,'sha256':sha(OUT),'files':len(files),'CRC_and_member_hashes':'PASS','new_wrong_wind_runs':4,'new_baseline_runs':0,'remaining_28_runs':0,'original_E1_native_files_unchanged':True}
(OUT.parent/'M0_E2_RAW_NATIVE_PACKAGE_VERIFICATION.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
