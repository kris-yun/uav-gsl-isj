from common_n import *
code='''import subprocess
from pathlib import Path
d=Path(DATA)/'readout';old=json.loads((d/'READOUT_LEDGER.json').read_text());assert not old['records'] and old['error']=="KeyError('saved_frame')"
d.rename(d.with_name('readout_FAILED_SERIALIZATION_ZERO_NATIVE_CALLS'))
p=subprocess.Popen(['python3',str(t/'readout_worker_framefix.py')],stdout=(t/'readout_framefix.stdout').open('w'),stderr=(t/'readout_framefix.stderr').open('w'),start_new_session=True)
print(json.dumps({'pid':p.pid,'repair':'actual saved trace field is frame; no scientific change','old_query_calls':0}))
'''.replace('DATA',repr(DATA))
r=json.loads(upload({'readout_worker_framefix.py':(WORK/'readout_worker.py').read_bytes()},code,'resume_readout_frame_serialization',45));dump(CORE/'READOUT_SERIALIZATION_REPAIR.json',r);print(json.dumps(r))
