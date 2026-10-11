from common import *
import argparse
p=argparse.ArgumentParser();p.add_argument('phase',choices=['smoke','remaining']);args=p.parse_args()
M1=ROOT/'outputs/PMFS_B4_M1_SOURCE_REPRESENTATION_20261010'
files={'query_worker.py':(W/'query_worker.py').read_bytes(),
 'FROZEN_RECEPTOR_SCHEDULE.csv':(W/'scoring_contract/FROZEN_RECEPTOR_SCHEDULE_ALL_MEMBERSHIP_BRANCHES.csv').read_bytes(),
 'FROZEN_INPUT.csv':(M1/'snapshot/input.csv').read_bytes(),'FROZEN_METADATA.json':(M1/'snapshot/metadata.json').read_bytes(),
 'PRE_QUERY_OBSERVATION_CONTRACT.json':(OUT/'PRE_QUERY_OBSERVATION_CONTRACT.json').read_bytes()} if args.phase=='smoke' else {}
code="""import subprocess
phase=PHASE
assert not (t/(phase+'_QUERY_STARTED.json')).exists()
p=subprocess.Popen(['python3',str(t/'query_worker.py'),phase],stdout=(t/(phase+'_query_worker.stdout')).open('w'),stderr=(t/(phase+'_query_worker.stderr')).open('w'),start_new_session=True)
print(json.dumps(dict(phase=phase,query_worker_pid=p.pid,new_GADEN_calls=0,navigation_goals=0)))
""".replace('PHASE',repr(args.phase))
print(upload(files,code,'START_QUERIES_'+args.phase.upper(),45))
