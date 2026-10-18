from pathlib import Path
import hashlib,json,os,shutil,subprocess,time,resource
R=Path('/mnt/hgfs/workspace/PMFS_O24_ROS_QUAL_20261018')
V=Path('/home/zyc/ros2_ws/pmfs_o24_port_gmrf_20261018')
plan=json.loads((R/'PRECOMMIT.json').read_text());assert not (R/'BUILD_RESULT.json').exists()
assert shutil.disk_usage(V.parent).free>plan['guest_free_floor_bytes']
logs=R/'build_logs';logs.mkdir();V.mkdir(exist_ok=False)
(R/'EXECUTION_STARTED.json').write_text(json.dumps(dict(wall_time=time.time(),budget_s=plan['total_batch_wall_s'])))
q=subprocess.run(['bash','-c','source /opt/ros/humble/setup.bash; source /home/zyc/ros2_ws/install/setup.bash; source /home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws/install/setup.bash; env -0'],capture_output=True,check=True)
env=os.environ.copy()
for row in q.stdout.split(b'\0'):
 if b'='in row:k,v=row.split(b'=',1);env[k.decode()]=v.decode()
old='/home/zyc/ros2_ws/pmfs_official_repro_audit_20261016'
for k in ['AMENT_PREFIX_PATH','CMAKE_PREFIX_PATH']:env[k]=old+'/install_paper_gmrf_tfqualified_2024:'+old+'/install_paper_pmfs_2024:'+env.get(k,'')
env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',CMAKE_BUILD_PARALLEL_LEVEL='1')
commands=[('configure',['cmake','-S',str(R/'source_runtime'),'-B',str(R/'build'),'-DCMAKE_BUILD_TYPE=Release','-DCMAKE_INSTALL_PREFIX='+str(R/'install'),'-DCMAKE_EXPORT_COMPILE_COMMANDS=ON']),('compile',['cmake','--build',str(R/'build'),'--parallel','1']),('install',['cmake','--install',str(R/'build')])]
out=[];start=time.monotonic()
for name,argv in commands:
 t=time.monotonic();cpu=resource.getrusage(resource.RUSAGE_CHILDREN)
 with (logs/(name+'.log')).open('wb')as f:q=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,env=env,timeout=1200)
 after=resource.getrusage(resource.RUSAGE_CHILDREN)
 out.append(dict(stage=name,argv=argv,exit_code=q.returncode,wall_s=time.monotonic()-t,cpu_s=after.ru_utime+after.ru_stime-cpu.ru_utime-cpu.ru_stime))
 (logs/'COMMANDS.json').write_text(json.dumps(out,indent=2))
 assert q.returncode==0,(name,'see build log')
exe=V/'gsl_actionserver_node';shutil.copyfile(R/'install/lib/gsl_server/gsl_actionserver_node',exe);exe.chmod(0o755)
h=hashlib.sha256(exe.read_bytes()).hexdigest()
result=dict(status='PASS_COMPLETE_O24_ROS_BUILD_NATIVE_FORMULAS_WITH_RNG_RECORDING',binary=str(exe),binary_sha256=h,wall_s=time.monotonic()-start,commands=out,algorithm_parameters_unchanged=True,new_worlds=0,AIMMD=0)
(R/'BUILD_RESULT.json').write_text(json.dumps(result,indent=2))
for role in plan['roles']:
 p=R/'cases'/role['id']/'CASE_META.json';m=json.loads(p.read_text());m['actual_binary_sha256']=h;p.write_text(json.dumps(m,indent=2)+'\n')
print(json.dumps(result),flush=True)
