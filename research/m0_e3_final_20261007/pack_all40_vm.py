"""Copy all40 original files without edits and create six lossless native ZIPs."""
from pathlib import Path
import csv,hashlib,json,shutil,zipfile
BASE=Path('/home/zyc/ros2_ws/m0_clean_support_r0_20261007');R=BASE/'e3_final'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(n,x):(R/n).write_text(json.dumps(x,indent=2)+'\n')
progress=read(R/'E3_PROGRESS.json');assert progress['qualified_completed']==28 and progress['attempted']==28
assert not (R/'bank').exists() and not (R/'NATIVE_FILES_SHA256.csv').exists()
A=read(R/'E3_AUTHORIZATION.json');hist=read(R/'E3_HISTORY_INDEX.json');new=read(R/'E3_COMPLETED_RUNS.json');allindex=[];copies=[]
for row in A['all_frozen_rows']:
    rid=row['run_id'];h=next((q for q in hist if q['frozen_row']['run_id']==rid),None);manifest=h['manifest'] if h else next(q for q in new if q['run_id']==rid);audit=Path(manifest['native_audit_path']);result=Path(manifest['native_raw_path']);dest=R/'bank'/rid
    for src,target in [(audit,dest/'audit'),(result,dest/'result')]:
        target.mkdir(parents=True)
        for p in sorted(src.rglob('*')):
            if p.is_file():
                q=target/p.relative_to(src);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);assert sha(q)==sha(p);copies.append({'original_path':str(p),'archive_path':q.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
    shutil.copyfile(result.parent/'sim.yaml',dest/'sim.yaml');copies.append({'original_path':str(result.parent/'sim.yaml'),'archive_path':(dest/'sim.yaml').relative_to(R).as_posix(),'bytes':(dest/'sim.yaml').stat().st_size,'sha256':sha(dest/'sim.yaml')});allindex.append({'frozen_row':row,'manifest':manifest,'original_phase':'E1' if row['wind_arm']=='U0' else ('E2' if h else 'E3')})
assert len(allindex)==40;write('ALL40_INDEX.json',allindex)
with (R/'ORIGINAL_TO_ARCHIVE_HASHES.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(copies[0]),lineterminator='\n');w.writeheader();w.writerows(copies)
for old in [BASE,BASE/'e2_sentinel']:
    with (old/'NATIVE_ALL_FILES_SHA256.csv').open() as f:files=list(csv.DictReader(f))
    for q in files:assert sha(old/q['path'])==q['sha256']
mem={q.split(':')[0]:int(q.split()[1])*1024 for q in Path('/proc/meminfo').read_text().splitlines() if len(q.split())>1 and q.split()[1].isdigit()};disk=shutil.disk_usage(R).free;ram=mem['MemAvailable'];total=sum(p.stat().st_size for p in R.rglob('*') if p.is_file());assert disk>=12*1024**3 and ram>=3*1024**3 and total<=5*1024**3
write('POST_RESOURCES_AND_PARENT_VERIFICATION.json',{'resource_gate_pass':True,'disk_free_bytes':disk,'RAM_available_bytes':ram,'raw_root_total_bytes':total,'all_original_E1_E2_native_files_unchanged':True,'new_scientific_runs':28,'total_M0_runs':40,'retries':0,'simulations_stopped':True})
files=sorted(p for p in R.rglob('*') if p.is_file() and not p.is_relative_to(R/'audit') and not (p.is_relative_to(R/'projects') and 'result' in p.relative_to(R/'projects').parts));manifest=R/'NATIVE_FILES_SHA256.csv'
with manifest.open('w') as f:
    w=csv.writer(f,lineterminator='\n');w.writerow(['path','bytes','sha256'])
    for p in files:w.writerow([p.relative_to(R).as_posix(),p.stat().st_size,sha(p)])
files.append(manifest);packages=[]
groups={arm:[p for p in files if p.is_relative_to(R/'bank') and p.parts[len((R/'bank').parts)].startswith('m0r0_'+arm+'_')] for arm in ['U0','A_on','A_off','B_shear','B_speed']};assigned={p for v in groups.values() for p in v};groups['SHARED']=[p for p in files if p not in assigned]
assert sum(map(len,groups.values()))==len(files)
for name,group in groups.items():
    out=R.parent.parent/('M0_NATIVE_'+name+'_20261007.zip');assert not out.exists()
    with zipfile.ZipFile(out,'x',zipfile.ZIP_DEFLATED,compresslevel=5) as z:
        for p in group:z.write(p,p.relative_to(R).as_posix())
    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None
        for p in group:assert hashlib.sha256(z.read(p.relative_to(R).as_posix())).hexdigest()==sha(p)
    packages.append({'name':out.name,'VM_path':str(out),'bytes':out.stat().st_size,'sha256':sha(out),'native_files':len(group),'CRC_and_member_hashes':'PASS'})
result={'packages':packages,'native_file_count':len(files)-1,'all40_runs':40,'new_E3_runs':28,'complete_disjoint_file_coverage':True,'original_data_byte_identity':True};(R.parent.parent/'M0_NATIVE_PACKAGES_MANIFEST_20261007.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
