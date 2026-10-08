from pathlib import Path
import csv,hashlib,json,shutil,subprocess,zipfile
R=Path('/home/zyc/ros2_ws/m0_clean_support_r0_20261007');OUT=R.parent/'M0_E0_E1_RAW_NATIVE_20261007.zip'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert json.loads((R/'E1_PROGRESS.json').read_text())['completed']==8
assert json.loads((R/'E1_PROGRESS.json').read_text())['intervention_runs']==0
e0=json.loads((R/'E0_QUALIFICATION.json').read_text());(R/'runtime_source_actual').mkdir(exist_ok=True)
for p,digest in e0['source_sha256'].items():
    p=Path(p);assert sha(p)==digest;shutil.copyfile(p,R/'runtime_source_actual'/p.name)
deps={}
for program in [Path('/home/zyc/ocb_r2_seeded_gaden/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator'),R/'bin/native_audit',R/'bin/native_e1_audit']:
    text=subprocess.check_output(['ldd',str(program)],text=True);assert 'not found' not in text
    for line in text.splitlines():
        words=line.split();paths=[Path(s) for s in words if s.startswith('/')]
        for p in paths:
            if p.is_file():deps[str(p)]={'resolved':str(p.resolve()),'bytes':p.stat().st_size,'sha256':sha(p)}
(R/'RUNTIME_DEPENDENCY_SHA256.json').write_text(json.dumps(deps,indent=2)+'\n')
files=sorted(p for p in R.rglob('*') if p.is_file());manifest=R/'NATIVE_ALL_FILES_SHA256.csv'
assert not manifest.exists() and not OUT.exists()
with manifest.open('w') as f:
    w=csv.writer(f,lineterminator='\n');w.writerow(['path','bytes','sha256'])
    for p in files:w.writerow([p.relative_to(R).as_posix(),p.stat().st_size,sha(p)])
files.append(manifest)
with zipfile.ZipFile(OUT,'x',zipfile.ZIP_DEFLATED,compresslevel=5) as z:
    for p in files:z.write(p,p.relative_to(R).as_posix())
with zipfile.ZipFile(OUT) as z:
    assert z.testzip() is None
    for p in files:assert hashlib.sha256(z.read(p.relative_to(R).as_posix())).hexdigest()==sha(p)
result={'path':str(OUT),'bytes':OUT.stat().st_size,'sha256':sha(OUT),'files':len(files),'CRC_and_member_hashes':'PASS','baseline_runs':8,'wrong_wind_runs':0}
(R.parent/'M0_E0_E1_RAW_NATIVE_PACKAGE_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
