"""Repair upload layout only: reuse exact bytes already on VM, never overwrite."""
from common_b import *
import shutil,base64
assert not (Path(load(CORE/'experiment_registry.json')['host_data_path'])/'CAMPAIGN_STARTED.json').exists()
shutil.copyfile(Path(__file__),CORE/'source'/Path(__file__).name)
sourcehashes={p.name:sha(p) for p in (CORE/'source').iterdir()};dump(CORE/'PREPHYSICAL_SOURCE_SHA256.json',sourcehashes)
files={'experiment_registry.json':(CORE/'experiment_registry.json').read_bytes(),'PREFLIGHT.json':(CORE/'PREFLIGHT.json').read_bytes()}
for n in ['generate_b.py','verify_raw_receiver_queries.py','cache_native.py']:files[n]=(WORK/n).read_bytes()
content={n:base64.b64encode(b).decode() for n,b in files.items()}
code='from pathlib import Path\nimport base64,json,hashlib,shutil,subprocess,time\nt=Path('+repr(REMOTE)+')\ndata=Path('+repr(DATA)+')\n'
code+='for n,b in '+repr(content)+'.items():\n p=t/n;actual=base64.b64decode(b)\n if p.exists():assert p.read_bytes()==actual or (n=="PREFLIGHT.json" and json.loads(p.read_bytes())==json.loads(actual)),n\n else:p.write_bytes(actual)\n'
code+='assert not any(data.iterdir())\npref=json.loads((t/"PREFLIGHT.json").read_text())\nassert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in pref["runtime_assets_SHA256"].items())\n'
code+='assert shutil.disk_usage(data).free>=10737418240\nassert shutil.disk_usage(t).free>=4294967296+16777216\n'
code+='active=[]\nfor p in Path("/proc").iterdir():\n if p.name.isdigit():\n  try:\n   name=(p/"comm").read_text().strip()\n   if name in ("filament_simula","filament_simulat","gsl_server","simpleFoam","pimpleFoam"):active.append((p.name,name))\n  except OSError:pass\nassert not active,active\n'
code+='inc=Path("/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws/src/gaden_common/third_party/gaden_core")\n'
code+='cmd=["/usr/bin/time","-v","-o",str(t/"rng_build_resource.log"),"c++","-O2","-std=c++20","-I/home/zyc/pmfs_m2_process_observation_20261010/include","-I"+str(inc/"include"),"-I"+str(inc/"third_party/DDA/third_party/glm"),str(t/"rng_probe.cpp"),"-o",str(t/"rng_probe_resource_check")]\n'
code+='before=time.monotonic();p=subprocess.run(cmd,capture_output=True,timeout=170);assert p.returncode==0,p.stderr.decode()\nassert (t/"rng_probe_resource_check").read_bytes()==(t/"rng_probe").read_bytes()\n'
code+='resource=(t/"rng_build_resource.log").read_text();rss=int(next(l.split(":")[-1].strip() for l in resource.splitlines() if "Maximum resident set size" in l))*1024\nassert rss<=1610612736\n'
code+='(data/"PREPHYSICAL_SOURCE_SHA256.json").write_text('+repr(json.dumps(sourcehashes,indent=2))+')\nprint(json.dumps(dict(status="PASS_PREPHYSICAL_FREEZE_REPAIR_IDENTICAL_METADATA",new_physical_outputs=0,wrapper_resource_check_wall_s=time.monotonic()-before,wrapper_peak_RSS_bytes=rss,probe_binary_identical=True,active_generation_navigation_CFD=active)))\n'
result=run_remote(code,'FINAL_PREPHYSICAL_FREEZE_REPAIRED2',60);print(result);dump(CORE/'WRAPPER_RESOURCE_AUDIT.json',json.loads(result))
scp=['scp','-i','C:/Users/50176/.ssh/id_ed25519_vm','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes']
for src,dst in [('/home/zyc/pmfs_b4_native_validation_20261009/derived_B4/OccupancyGrid3D.csv',RAW/'OccupancyGrid3D.csv'),(REMOTE+'/rng_build_resource.log',CORE/'WRAPPER_BUILD_RESOURCE.log')]:
    p=subprocess.run(scp+['zyc@192.168.111.128:'+src,str(dst)],capture_output=True);assert p.returncode==0,p.stderr
assert sha(RAW/'OccupancyGrid3D.csv')=='00914f3d7114d45d764ff24be9e832da70d6e2e69528918f2c3c1143fea40295'
repairs=load(CORE/'technical_repairs/LEDGER.json');repairs['repairs'].append(dict(kind='metadata upload path collision',count=2,physical_attempts_before_repair=0,action='Existing preflight differs by JSON whitespace only; require full parsed object equality, preserve original bytes; all other existing files must match bytes; upload only absent files'))
dump(CORE/'technical_repairs/LEDGER.json',repairs)
for name in ['FINAL_PREPHYSICAL_FREEZE.stdout','FINAL_PREPHYSICAL_FREEZE.stderr']:shutil.copyfile(WORK/name,CORE/'technical_repairs'/name)
dump(CORE/'PREPHYSICAL_FREEZE_COMPLETE.json',dict(time_ns=time.time_ns(),registry_SHA256=sha(CORE/'experiment_registry.json'),source_SHA256=sha(CORE/'PREPHYSICAL_SOURCE_SHA256.json'),physical_outputs=0,mode=24,all_evaluation_code_present_before_first_generation=True))
print('PREPHYSICAL_FREEZE_COMPLETE')
