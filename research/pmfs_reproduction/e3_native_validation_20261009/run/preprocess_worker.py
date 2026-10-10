from pathlib import Path
import subprocess,time,json
t=Path(__file__).resolve().parent
assert not (t/'PREPROCESS_STARTED.json').exists()
start=time.time();(t/'PREPROCESS_STARTED.json').write_text(json.dumps(dict(preprocessing_executions=1,start_wall_time=start)))
try:
 with (t/'preprocessing.log').open('w') as f:q=subprocess.run(['bash',str(t/'preprocess.sh')],stdout=f,stderr=f,timeout=900)
 result=dict(exit_code=q.returncode,wall_seconds=time.time()-start,preprocessing_executions=1)
except Exception as e:result=dict(exit_code=None,error=str(e),wall_seconds=time.time()-start,preprocessing_executions=1)
(t/'PREPROCESSING_RESULT.json').write_text(json.dumps(result,indent=2))
