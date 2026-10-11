from common_n import *
import csv,io,shutil,numpy as np
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8',newline='')))
def cb(rs):
 s=io.StringIO();w=csv.DictWriter(s,fieldnames=list(rs[0]),lineterminator='\n');w.writeheader();w.writerows(rs);return s.getvalue().encode()
src=(CORE/'source/native_point_entry.cpp').read_text()
needle='r4_set_gaussian(c,integer(r,"phase"));Utils::r4_rng_restore(r.at("engine"));'
assert needle in src
src=src.replace(needle,'bool ready=!r.count("ready")||integer(r,"ready");if(ready)r4_set_gaussian(c,integer(r,"phase"));Utils::r4_rng_restore(r.at("engine"));')
src=src.replace('R4Audit::cache_ready=true;R4Audit::last_index=r4_gaussian_index();','auto state=csv(in/"rng.csv").at(0);bool ready=!state.count("ready")||integer(state,"ready");R4Audit::cache_ready=ready;R4Audit::last_index=ready?r4_gaussian_index():0;')
old=BASE/'outputs/PMFS_B4_OFFICIAL_TERMINAL_RESUMED_20261010/runtime/updates/update_0';first=rows(old/'candidates.csv')[0];assert first['gaussian_ready_before']=='0';second=rows(old/'candidates.csv')[1];assert second['gaussian_ready_before']=='1';initial=rows(old/'gaussian_initial.csv')[0]
host=Path('D:/ZYC/A-gas/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011');files={}
for group,base in [('DERIVED',CORE/'native_inputs/inputs/DERIVED'),('B4_FIRST',old)]:
 folder='cold_inputs/'+group
 for n in ['input.csv','gaussian_cache.f32']:files[folder+'/'+n]=(base/n).read_bytes()
 if group=='DERIVED':
  for n in ['metadata.csv','settings.csv']:files[folder+'/'+n]=(base/n).read_bytes()
 else:
  files[folder+'/metadata.csv']=cb([load(old/'metadata.json')]);files[folder+'/settings.csv']=(CORE/'native_inputs/inputs/B4/settings.csv').read_bytes();files[folder+'/anchor_job.csv']=cb([{k:first[k] for k in ['origin_i','origin_j','size_i','size_j']}])
 files[folder+'/rng.csv']=cb([dict(ready=0,phase=0,engine=first['rng_before'])])
for rep,state in enumerate([dict(ready=1,phase=initial['index'],engine=initial['rng_after_initialization']),dict(ready=1,phase=second['gaussian_index_before'],engine=second['rng_before'])]):
 olddir=host/f'point_inputs/R{rep}';new=host/f'point_corrected_inputs/R{rep}';new.mkdir(parents=True,exist_ok=False)
 for p in olddir.iterdir():shutil.copy2(p,new/p.name)
 (new/'rng.csv').write_bytes(cb([state]))
for n,b in files.items():p=host/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
(CORE/'source/native_cold_entry.cpp').write_text(src,encoding='utf-8');dump(CORE/'COLD_INITIALIZATION_REPAIR_CONTRACT.json',dict(status='REPAIR_BEFORE_FRESH_ENDPOINT_EVALUATION',
 defect='Warm-preloaded historical cache was paired with uninitialized-cache sentinelphase0 and pre-initialization uniform engine; this is not exact cold initial state.',
 preserved='All previous native outputs and input bytes; old branch labelled HYBRID_INITIALIZATION_SHADOW_EXCLUDED_FROM_PRIMARY_N0',
 corrected='Restore captured original engine; let original native lazyGaussian constructor execute in original order. For point diagnostics use recorded ready index19/engine1739431495 and nextcandidate ready state.',
 scientific_fields_changed=False,seeds_changed=False,technical_issue_repair_count=1,new_gas_calls=0,phase_after_first_real_init=initial))
code=r'''from pathlib import Path
import subprocess,time,shutil,json,hashlib
r4=Path('/home/zyc/pmfs_native_capture_r4_20261009');ctx=json.loads((r4/'BUILD_CONTEXT.json').read_text());ram=Path('/dev/shm/nmc_cold');ram.mkdir()
objs=[Path('/home/zyc/pmfs_b4_m1_representation_20261010/Simulations_native.o'),Path('/home/zyc/pmfs_m2_semantic_anchor_20261010_build2/PMFSLib_frozen.o'),r4/'Math_accessors.o',r4/'NQAQuadtree.o']
cmds=[['/usr/bin/c++',*ctx['compileflags'],'-c',str(t/'code/native_cold_entry.cpp'),'-o',str(ram/'cold_entry.o')],['/usr/bin/c++','-fopenmp','-fsanitize=undefined','-Wl,--gc-sections',str(ram/'cold_entry.o'),*[str(x) for x in objs],'-o',str(ram/'native_cold_entry'),*ctx['link_tail']]]
cost=[]
for i,cmd in enumerate(cmds):
 start=time.time();p=subprocess.run(cmd,stdout=(t/f'cold_build_{i}.stdout').open('w'),stderr=(t/f'cold_build_{i}.stderr').open('w'),timeout=180);assert p.returncode==0,(t/f'cold_build_{i}.stderr').read_text()[-3000:];cost.append(time.time()-start)
keep=Path(DATA)/'cold_binary_preservation';keep.mkdir()
for f in ram.iterdir():shutil.copy2(f,keep/f.name)
print(json.dumps({'status':'COMPILE_PASS_COLD_RESTORE_NOT_YET_QUALIFIED','build_seconds':cost,'entry_SHA256':hashlib.sha256((ram/'native_cold_entry').read_bytes()).hexdigest()}))
'''.replace('DATA',repr(DATA))
r=json.loads(upload({'code/native_cold_entry.cpp':src.encode()},code,'cold_init_thin_driver_same_core_compile',240));dump(CORE/'COLD_ENTRY_PROVENANCE.json',r);print(json.dumps(r))
