"""Original ELF only. New leaf per attempt. No robot/controller or ROS loop."""
from pathlib import Path
import hashlib,json,subprocess,sys,os,time,signal,shutil,resource
ROOT=Path('/home/zyc/ros2_ws/research_runs/v7_sameheight3_20261023')
BUILD=Path('/home/zyc/ocb_r2_seeded_gaden')
ELF=BUILD/'install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator'

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def put(name,obj):
 p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf8')
def cfg():return json.loads((ROOT/'PROTOCOL.json').read_text())
def identity():
 c=cfg();src=BUILD/'src/GADEN';core=src/'gaden_common/third_party/gaden_core'
 r={'binary_sha256':sha(ELF),'parent_head':subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD'],text=True).strip(),
 'core_head':subprocess.check_output(['git','-C',str(core),'rev-parse','HEAD'],text=True).strip(),
 'parent_diff_sha256':hashlib.sha256(subprocess.check_output(['git','-C',str(src),'diff','--binary'])).hexdigest(),
 'core_diff_sha256':hashlib.sha256(subprocess.check_output(['git','-C',str(core),'diff','--binary'])).hexdigest(),
 'mathutils':sha(core/'include/gaden/internal/MathUtils.hpp'),'running':sha(core/'src/RunningSimulation.cpp'),
 'timeline_patch':sha(BUILD/'READONLY_TIMELINE.patch'),'occupancy':sha(c['occupancy_path_alias'])}
 assert r==c['expected_identity'],r
 for w in c['expected_wind']:
  assert sha(Path(c['base_parameters']['wind_data']+f"_{w['index']}.csv_gaden"))==w['sha256']
 prefix='set -Ee -o pipefail\nsource /opt/ros/humble/setup.bash\nsource '+str(BUILD)+'/install/setup.bash\nexport LD_LIBRARY_PATH='+str(BUILD)+'/build/gaden_common/third_party/gaden_core/third_party/libbsc:${LD_LIBRARY_PATH:-}\nexec ldd "$1"'
 deps=subprocess.check_output(['bash','-c',prefix,'v7-identity',str(ELF)],text=True)
 assert 'not found' not in deps,deps
 objects=[]
 for line in deps.splitlines():
  parts=line.split();p=next((Path(x) for x in parts if x.startswith('/')),None)
  if p and p.is_file():objects.append({'path':str(p),'sha256':sha(p)})
 result={'status':'PASS_ORIGINAL_ELF_SOURCE_PATCH_PARAMS_AND_WIND','identity':r,'wind':c['expected_wind'],
 'protocol_sha256':sha(ROOT/'PROTOCOL.json'),'loaded_lookup':deps,'resolved_shared_objects':objects,
 'historical_shared_library_SHA_not_available_for_all_dependencies':True,
 'acceptance_scope':'exact original executable plus exact parent/core tracked patches and key source hashes; current dynamic lookup archived, no claim of all historical library byte identity',
 'occupancy_path_alias_only':c['occupancy_path_alias'],'legacy_temperature_pressure_binding_preserved':True}
 put('IDENTITY_GATE.json',result);return result
def size():
 seen=set();logical=unique=0
 for p in (ROOT/'runs').glob('**/*'):
  if p.is_file():
   st=p.stat();logical+=st.st_size;k=(st.st_dev,st.st_ino)
   if k not in seen:unique+=st.st_size;seen.add(k)
 return {'logical_bytes':logical,'deduplicated_bytes':unique}
def run(source,repeat):
 assert source in ('B','C') and repeat in (1,2,3,4)
 c=cfg();identity()
 ledger_path=ROOT/'ATTEMPTS.json';ledger=json.loads(ledger_path.read_text()) if ledger_path.exists() else []
 assert len(ledger)<c['maximum_new_attempts']
 key=f'v7h3_{source}_r{repeat:02d}';leaf=ROOT/'runs'/key
 assert not leaf.exists() and all(x['run_id']!=key for x in ledger)
 assert leaf.resolve().is_relative_to((ROOT/'runs').resolve())
 if repeat>=3:
  assert (ROOT/'DEV_AUTHORIZATION.json').is_file(),'no DEV physics before selection/model freeze'
  dev=json.loads((ROOT/'DEV_AUTHORIZATION.json').read_text());assert dev['one_development_check']
 assert shutil.disk_usage(ROOT).free>=c['minimum_free_disk_before_run_bytes']
 assert size()['deduplicated_bytes']<c['maximum_new_scientific_bytes']
 remaining=c['maximum_generation_wall_s']-sum(x.get('wall_s',0) for x in ledger)
 assert remaining>0
 params=dict(c['base_parameters']);params['occupancy3D_data']=c['occupancy_path_alias'];params['results_location']=str(leaf)
 for axis,val in zip('xyz',c['source_xyz_m'][c['source_ids'].index(source)]):params['source_position_'+axis]=format(val,'.2f')
 argv=[str(ELF),'--ros-args']
 for k,v in params.items():argv+=['-p',f'{k}:={v}']
 env=os.environ.copy();env.update(GADEN_RNG_SEED=str(c['master_seeds'][repeat-1]),OMP_NUM_THREADS='1',
 OMP_DYNAMIC='FALSE',OMP_PROC_BIND='TRUE',ROS_DOMAIN_ID='229',ROS_LOCALHOST_ONLY='1')
 prefix='set -Ee -o pipefail\nsource /opt/ros/humble/setup.bash\nsource '+str(BUILD)+'/install/setup.bash\nexport LD_LIBRARY_PATH='+str(BUILD)+'/build/gaden_common/third_party/gaden_core/third_party/libbsc:${LD_LIBRARY_PATH:-}\nexec "$@"'
 entry={'run_id':key,'source':source,'repeat':repeat,'seed':c['master_seeds'][repeat-1],'status':'ATTEMPT_STARTED',
 'parameters':params,'protocol_sha256':sha(ROOT/'PROTOCOL.json'),'original_binary_sha256':sha(ELF)}
 ledger.append(entry);put('ATTEMPTS.json',ledger);(ROOT/'runs').mkdir(exist_ok=True)
 log=ROOT/'logs'/(key+'.stdout.log');log.parent.mkdir(exist_ok=True);start=time.monotonic();failure=None
 before_cpu=resource.getrusage(resource.RUSAGE_CHILDREN)
 with log.open('wb') as handle:
  proc=subprocess.Popen(['bash','-c',prefix,'v7-h3',*argv],env=env,stdout=handle,stderr=subprocess.STDOUT,start_new_session=True)
  while proc.poll() is None:
   if time.monotonic()-start>remaining:failure='GENERATION_WALL_BUDGET'
   if size()['deduplicated_bytes']>c['maximum_new_scientific_bytes']:failure='SCIENTIFIC_BYTE_BUDGET'
   if failure:
    os.killpg(proc.pid,signal.SIGTERM)
    try:proc.wait(timeout=10)
    except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
    break
   time.sleep(2)
 after_cpu=resource.getrusage(resource.RUSAGE_CHILDREN)
 entry.update(wall_s=time.monotonic()-start,exit_code=proc.returncode,stdout_sha256=sha(log),
 child_user_cpu_s=after_cpu.ru_utime-before_cpu.ru_utime,child_system_cpu_s=after_cpu.ru_stime-before_cpu.ru_stime,
 worker_child_max_rss_KiB=after_cpu.ru_maxrss)
 if failure or proc.returncode:
  entry['status']=failure or 'ORIGINAL_SIMULATOR_FAILURE';put('ATTEMPTS.json',ledger);raise RuntimeError(entry)
 timeline=leaf/'RECORD_TIMELINE.tsv';frames=sorted(leaf.glob('iteration_*'),key=lambda p:int(p.name.split('_')[1]))
 assert len(frames)==c['expected_record_count'] and sha(timeline)==c['expected_timeline_sha256']
 # Deduplicate byte-identical output winds by hardlink, only inside this new
 # task-owned leaf. Every original filename remains readable. Frozen inputs
 # are not edited; both logical size and unique inode size are reported.
 wind_receipts=[]
 for w in c['expected_wind']:
  dest=leaf/'wind'/f"wind_iteration_{w['index']}";origin=Path(params['wind_data']+f"_{w['index']}.csv_gaden")
  assert dest.resolve().is_relative_to(leaf.resolve()) and sha(dest)==sha(origin)==w['sha256']
  link=dest.with_name(dest.name+'.new_hardlink');assert not link.exists();os.link(origin,link);os.replace(link,dest)
  wind_receipts.append({'name':str(dest.relative_to(leaf)),'sha256':w['sha256'],'shared_input':str(origin)})
 inventory=[{'name':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in frames]
 (leaf/'FRAME_SHA256.json').write_text(json.dumps(inventory,indent=2)+'\n')
 entry.update(status='PASS_ORIGINAL_GENERATION',record_count=len(frames),timeline_sha256=sha(timeline),
 source_xyz_m=c['source_xyz_m'][c['source_ids'].index(source)],wind=wind_receipts,
 retained_size=size(),cpu_and_memory='RUSAGE_CHILDREN CPU delta; maximum child RSS in this worker; no GPU use')
 (leaf/'RUN_MANIFEST.json').write_text(json.dumps(entry,indent=2)+'\n')
 put('ATTEMPTS.json',ledger);print(json.dumps(entry),flush=True)

if __name__=='__main__':
 if sys.argv[1:]==['identity']:print(json.dumps(identity(),indent=2))
 else:run(sys.argv[1],int(sys.argv[2]))
