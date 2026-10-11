from common import *
files={('map_labels/'+p.name):p.read_bytes() for p in (W/'native_map_labels').glob('*.csv')}
code=r'''
import os,subprocess,time,hashlib,tarfile
entry=Path('/home/zyc/pmfs_m2_event_map_replay_20261010')
exe=entry/'event_map_replay';assert hashlib.sha256(exe.read_bytes()).hexdigest()=='7d05e5124bd8e2bc6c6e1eb9b567599a6a456b3baf92c9dec9e698fed669cfbc'
env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
 LD_LIBRARY_PATH='/opt/ros/humble/lib:/home/zyc/ros2_ws/install/olfaction_msgs/lib:/home/zyc/ros2_ws/install/gsl_actions/lib:/home/zyc/ros2_ws/install/gmrf_msgs/lib:/home/zyc/ros2_ws/install/gaden_msgs/lib')
results=[]
for root in sorted((t/'realizations').iterdir()):
 name=root.name;labels=t/'map_labels'/(name+'_branch0.csv');labels1=t/'map_labels'/(name+'_branch1.csv')
 assert labels.read_bytes()==labels1.read_bytes(),'branches differ; both must run rather than silently choose'
 out=t/'aligned_maps'/name;assert not out.exists()
 start=time.monotonic();p=subprocess.run([str(exe),str(entry/'snapshot'),str(entry/'event_covariates.csv'),str(labels),str(out)],env=env,capture_output=True,text=True,timeout=30)
 (t/'aligned_maps'/(name+'.stdout')).write_text(p.stdout);(t/'aligned_maps'/(name+'.stderr')).write_text(p.stderr)
 assert p.returncode==0,(name,p.stderr)
 results.append(dict(bank_id=name,map_native_update_calls=50,candidate_simulations=0,full_source_posterior_updates=0,wall_s=time.monotonic()-start,
                     labels_sha256=hashlib.sha256(labels.read_bytes()).hexdigest(),branches_identical=True,map_SHA256=hashlib.sha256((out/'map.csv').read_bytes()).hexdigest()))
(t/'ALIGNED_MAP_EXECUTION.json').write_text(json.dumps(results,indent=2))
archive=t/'ALIGNED_NATIVE_MAP_EVIDENCE.tar.gz';assert not archive.exists()
with tarfile.open(archive,'w:gz') as a:
 a.add(t/'ALIGNED_MAP_EXECUTION.json',arcname='ALIGNED_MAP_EXECUTION.json')
 a.add(t/'aligned_maps',arcname='aligned_maps')
print(json.dumps(dict(records=results,archive_bytes=archive.stat().st_size,archive_SHA256=hashlib.sha256(archive.read_bytes()).hexdigest()),indent=2))
'''
r=json.loads(upload(files,code,'EXECUTE_EIGHT_IDENTICAL_OBSERVATION_MAPS',60))
c=json.loads(CONNECTION.read_text(encoding='utf-8'));target=W/'ALIGNED_NATIVE_MAP_EVIDENCE.tar.gz'
scp=['scp','-q','-i',c['key'],'-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+c['known_hosts'],
      c['target']+':'+REMOTE+'/ALIGNED_NATIVE_MAP_EVIDENCE.tar.gz',str(target)]
p=subprocess.run(scp,capture_output=True,timeout=45);assert p.returncode==0,p.stderr
import hashlib,tarfile
assert hashlib.sha256(target.read_bytes()).hexdigest()==r['archive_SHA256']
with tarfile.open(target) as a:
    for item in a.getmembers():assert (OUT/'native_aligned_maps'/item.name).resolve().is_relative_to((OUT/'native_aligned_maps').resolve())
    a.extractall(OUT/'native_aligned_maps',filter='data')
(OUT/'ALIGNED_MAP_CAPTURE_SUMMARY.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(complete_bank_maps=len(r['records']),new_2D_simulations=0,new_posterior_updates=0,archive_bytes=r['archive_bytes']),indent=2))
