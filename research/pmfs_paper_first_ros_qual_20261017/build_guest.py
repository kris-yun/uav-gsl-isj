from pathlib import Path
import hashlib,json,os,psutil,resource,shutil,signal,subprocess,sys,time
S=Path('/mnt/hgfs/workspace/PMFS_PAPER_FIRST_ROS_QUAL_20261017');V=Path('/home/zyc/ros2_ws/pmfs_paper_first_qual_20261017')
plan=json.loads((S/'BUILD_PRECOMMIT.json').read_text());attempt=sys.argv[1]if len(sys.argv)>1 else 'attempt1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
if not V.exists():
    V.mkdir();shutil.copytree(S/'source_runtime',V/'src/gsl_server')
else:
    assert attempt!='attempt1','Do not repeat the first build'
logs=S/'build_logs'/attempt;logs.mkdir(parents=True,exist_ok=False)
assert shutil.disk_usage(V).free>plan['guest_free_floor_bytes']
manifest=[dict(path=str(p.relative_to(V/'src/gsl_server')),sha256=sha(p))for p in sorted((V/'src/gsl_server').rglob('*'))if p.is_file()]
put(logs/'ACTUAL_SOURCE_INPUTS.json',manifest)
shell='source /opt/ros/humble/setup.bash; source /home/zyc/ros2_ws/install/setup.bash; source /home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws/install/setup.bash; env -0'
q=subprocess.run(['bash','-c',shell],capture_output=True,check=True,timeout=30);env=os.environ.copy()
for row in q.stdout.split(b'\0'):
    if b'='in row:k,v=row.split(b'=',1);env[k.decode()]=v.decode()
old=Path('/home/zyc/ros2_ws/pmfs_official_repro_audit_20261016')
prefixes=[str(old/'install_paper_gmrf_tfqualified_2024'),str(old/'install_paper_pmfs_2024')]
for key in ['AMENT_PREFIX_PATH','CMAKE_PREFIX_PATH']:env[key]=':'.join(prefixes)+':'+env.get(key,'')
env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',CMAKE_BUILD_PARALLEL_LEVEL='1')
commands=[('configure',['cmake','-S',str(V/'src/gsl_server'),'-B',str(V/'build'),'-DCMAKE_BUILD_TYPE=Release','-DCMAKE_INSTALL_PREFIX='+str(V/'install'),'-DCMAKE_EXPORT_COMPILE_COMMANDS=ON']),('compile',['cmake','--build',str(V/'build'),'--parallel','1']),('install',['cmake','--install',str(V/'build')])]
start=time.monotonic();receipts=[];failed=None;peak=0
for name,argv in commands:
    t=time.monotonic();before=resource.getrusage(resource.RUSAGE_CHILDREN)
    with (logs/(name+'.log')).open('wb')as f:
        proc=subprocess.Popen(argv,stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
        pid=proc.pid;created=psutil.Process(pid).create_time()
        while proc.poll()is None:
            total=time.monotonic()-start
            mem=psutil.virtual_memory().available;disk=shutil.disk_usage(V).free
            rss=0
            try:
                procs=[psutil.Process(pid)]+psutil.Process(pid).children(recursive=True)
                for p in procs:
                    try:rss+=p.memory_info().rss
                    except psutil.NoSuchProcess:pass
            except psutil.NoSuchProcess:pass
            peak=max(peak,rss)
            put(S/'BUILD_PROGRESS.json',dict(stage=name,attempt=attempt,pid=pid,create_time=created,elapsed_s=total,owned_rss_bytes=rss,guest_free_bytes=disk,guest_memory_available_bytes=mem))
            if total>plan['max_build_wall_s']or disk<plan['guest_free_floor_bytes']or mem<2*2**30:
                failed='BUILD_RESOURCE_GUARD';os.killpg(pid,signal.SIGTERM);proc.wait(timeout=10);break
            time.sleep(1)
        after=resource.getrusage(resource.RUSAGE_CHILDREN);receipts.append(dict(stage=name,command=argv,exit_code=proc.returncode,wall_s=time.monotonic()-t,child_cpu_s=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime))
        put(logs/'COMMANDS.json',receipts)
        if proc.returncode or failed:failed=failed or 'BUILD_COMMAND_FAILED';break
exe=V/'install/lib/gsl_server/gsl_actionserver_node'
result=dict(status='PASS_COMPLETE_SEPTEMBER_BASELINE_BUILD'if failed is None else failed,attempt=attempt,source_commit=plan['source_commit'],binary=str(exe),binary_sha256=sha(exe)if exe.exists()else None,wall_s=time.monotonic()-start,commands=receipts,guest_peak_owned_rss_bytes=peak,reused_old_object_files=False,all_objects_built_in_new_directory=True,new_ROS=0,new_worlds=0)
if exe.exists():
    (S/'binaries').mkdir(exist_ok=True);shutil.copyfile(exe,S/'binaries/gsl_actionserver_node')
    q=subprocess.run(['ldd',str(exe)],capture_output=True,text=True);(logs/'ldd.txt').write_text(q.stdout+q.stderr)
    for n in ['compile_commands.json','CMakeCache.txt']:
        if (V/'build'/n).exists():shutil.copyfile(V/'build'/n,logs/n)
put(logs/'RESULT.json',result);put(S/'BUILD_RESULT.json',result);print(json.dumps(result),flush=True)
if failed:raise SystemExit(1)
