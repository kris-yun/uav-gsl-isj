from pathlib import Path
import json,resource,subprocess,time
R=Path('/mnt/hgfs/workspace/PMFS_EQ6_ALIGNMENT_20261017');out=R/'execution'
assert (R/'GRID_COMPONENT_PRECOMMIT.json').exists()
assert not (out/'GRID_COMMANDS.json').exists()
receipts=[]
for name,argv in [('grid_build',['g++','-std=c++17','-O2','-Wall','-Wextra',str(R/'cpp/grid_probe.cpp'),'-o',str(out/'grid_probe')]),('grid_run',[str(out/'grid_probe')])]:
    t=time.monotonic();before=resource.getrusage(resource.RUSAGE_CHILDREN);q=subprocess.run(argv,capture_output=True,timeout=30);after=resource.getrusage(resource.RUSAGE_CHILDREN)
    (out/(name+'.stdout')).write_bytes(q.stdout);(out/(name+'.stderr')).write_bytes(q.stderr)
    receipts.append(dict(name=name,argv=argv,exit_code=q.returncode,wall_s=time.monotonic()-t,child_cpu_s=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime))
    (out/'GRID_COMMANDS.json').write_text(json.dumps(receipts,indent=2))
    if q.returncode:raise SystemExit(q.returncode)
print((out/'grid_run.stdout').read_text())
