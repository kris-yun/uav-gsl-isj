from common import *
import argparse
p=argparse.ArgumentParser();p.add_argument('phase',choices=['smoke','remaining']);args=p.parse_args()
files={'generation_worker.py':(W/'generation_worker.py').read_bytes()} if args.phase=='smoke' else {}
code="""import subprocess
phase=PHASE
assert not (t/(phase+'_GENERATION_STARTED.json')).exists()
p=subprocess.Popen(['python3',str(t/'generation_worker.py'),phase],stdout=(t/(phase+'_worker.stdout')).open('w'),stderr=(t/(phase+'_worker.stderr')).open('w'),start_new_session=True)
print(json.dumps(dict(phase=phase,worker_pid=p.pid,maximum_total_realizations=8,maximum_total_generation_wall_s=900)))
""".replace('PHASE',repr(args.phase))
print(upload(files,code,'START_GENERATION_'+args.phase.upper(),45))
