from pathlib import Path
import hashlib,json,os,shlex,subprocess,time
R=Path('/mnt/hgfs/workspace/PMFS_O24_ROS_QUAL_20261018');V=Path('/home/zyc/ros2_ws/pmfs_o24_port_gmrf_20261018');Q=R/'rng_qualification';Q.mkdir(exist_ok=True)
build=json.loads((R/'BUILD_RESULT.json').read_text());assert build['status'].startswith('PASS_COMPLETE_O24')
commands=json.loads((R/'build/compile_commands.json').read_text());entry=next(r for r in commands if r['file'].endswith('/Common/Utils/Math.cpp'));args=shlex.split(entry['command']);out=[];i=0
while i<len(args):
 if args[i]in ['-o','-c','-MT','-MF']:i+=2;continue
 if args[i]in ['-MD','-MMD']:i+=1;continue
 out.append(args[i]);i+=1
mathobj=R/'build/CMakeFiles/GSL_common.dir/src/gsl_server/algorithms/Common/Utils/Math.cpp.o';assert mathobj.exists()
exe=V/'rng_recording_check';out +=[str(R/'rng_recording_check.cpp'),str(mathobj),'-o',str(exe)]
t=time.monotonic();q=subprocess.run(out,capture_output=True,timeout=90);(Q/'compile.stdout').write_bytes(q.stdout);(Q/'compile.stderr').write_bytes(q.stderr);receipts=[dict(command=out,exit_code=q.returncode,wall_s=time.monotonic()-t)];(Q/'COMMANDS.json').write_text(json.dumps(receipts,indent=2));assert q.returncode==0,'See RNG compile.stderr'
cmd=[str(exe),str(Q/'cache')];t=time.monotonic();q=subprocess.run(cmd,capture_output=True,timeout=30);(Q/'run.stdout').write_bytes(q.stdout);(Q/'run.stderr').write_bytes(q.stderr);receipts.append(dict(command=cmd,exit_code=q.returncode,wall_s=time.monotonic()-t));(Q/'COMMANDS.json').write_text(json.dumps(receipts,indent=2));assert q.returncode==0,('RNG recording/replay did not pass',q.returncode)
r=json.loads(q.stdout);assert r['status']=='PASS_PRODUCTION_RNG_VS_AUTHOR_MIRROR_AND_CAPTURE_REPLAY';r.update(production_Math_object_sha256=hashlib.sha256(mathobj.read_bytes()).hexdigest(),qualification_exe_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),production_seed_forced=False,scope='Direct recorded RNG stream parity and snapshot replay; not a proof of deterministic multithreaded robot trajectories',new_ROS=0,new_forward_simulations=0,new_worlds=0)
(R/'RNG_RECORDING_QUALIFICATION.json').write_text(json.dumps(r,indent=2));print(json.dumps(dict(status=r['status'],production_seed_forced=False,new_ROS=0)),flush=True)
