from pathlib import Path
import hashlib,json,os,resource,subprocess,time
R=Path('/mnt/hgfs/workspace/PMFS_EQ6_ALIGNMENT_20261017')
P=json.loads((R/'FROZEN_PLAN.json').read_text())
out=R/'execution';out.mkdir(exist_ok=False)
env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
commands=[('build',['g++','-std=c++17','-O2','-Wall','-Wextra',str(R/'cpp/check.cpp'),'-o',str(out/'eq6_check')]),('unit',[str(out/'eq6_check'),'--unit'])]
commands += [(c['key'],[str(out/'eq6_check'),str(R/'fixtures'/c['key']),str(out/(c['key']+'.csv'))])for c in P['contexts']]
start=time.monotonic();receipts=[]
for name,argv in commands:
    before=resource.getrusage(resource.RUSAGE_CHILDREN);t=time.monotonic()
    q=subprocess.run(argv,capture_output=True,env=env,timeout=min(90,max(1,P['max_guest_wall_s']-(time.monotonic()-start))))
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    (out/(name+'.stdout')).write_bytes(q.stdout);(out/(name+'.stderr')).write_bytes(q.stderr)
    receipts.append(dict(name=name,argv=argv,exit_code=q.returncode,wall_s=time.monotonic()-t,child_cpu_s=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime))
    (out/'COMMANDS.json').write_text(json.dumps(receipts,indent=2))
    if q.returncode:raise SystemExit(q.returncode)
result=dict(status='PASS_ALL_COMPONENT_COMMANDS',wall_s=time.monotonic()-start,child_cpu_s=sum(r['child_cpu_s']for r in receipts),commands=len(receipts),new_forward_calls=0,new_ROS=0,new_worlds=0,binary_sha256=hashlib.sha256((out/'eq6_check').read_bytes()).hexdigest())
(out/'RESULT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
