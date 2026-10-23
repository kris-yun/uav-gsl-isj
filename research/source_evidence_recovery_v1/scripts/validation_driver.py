"""Run final frozen reference commands and preserve every subprocess receipt."""
from pathlib import Path
import subprocess,sys,time,json,os,resource
root=Path(__file__).resolve().parents[1];os.chdir(root)
env=dict(os.environ);env['PYTHONPATH']=str(root/'src')+os.pathsep+env.get('PYTHONPATH','')
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):env[key]='2'
commands=[
 ('tests',[sys.executable,'-m','pytest','-q','--junitxml=artifacts/unit_tests.xml']),
 ('generate',[sys.executable,'-m','gsl_recovery','generate-controlled','--out','examples/controlled','--episodes','64','--length','10']),
 ('qualify',[sys.executable,'-m','gsl_recovery','audit-data','--manifest','examples/controlled/manifest.json','--training','--out','artifacts/data_qualification.json']),
 ('train_m1',[sys.executable,'-m','gsl_recovery','train','--manifest','examples/controlled/manifest.json','--variant','Bprime','--out','artifacts/m1_Bprime','--maxiter','200']),
 ('train_m2',[sys.executable,'-m','gsl_recovery','train-diagnosis','--manifest','examples/controlled/manifest.json','--model','artifacts/m1_Bprime/model.npz','--out','artifacts/diagnosis_reference','--maxiter','300']),
 ('offline',[sys.executable,'-m','gsl_recovery','evaluate','--manifest','examples/controlled/manifest.json','--model','artifacts/m1_Bprime/model.npz','--out','artifacts/offline_reference']),
 ('closed_loop',[sys.executable,'-m','gsl_recovery','demo','--model','artifacts/m1_Bprime/model.npz','--diagnosis','artifacts/diagnosis_reference/diagnosis.npz','--out','artifacts/closed_loop','--rounds','3','--draws','128']),
 ('native_b4',[sys.executable,'-m','gsl_recovery','native-replay','--out','artifacts/level3_b4']),
 ('matrix_offline',[sys.executable,'-m','gsl_recovery','matrix','--manifest','examples/controlled/manifest.json','--config','configs/controlled_matrix.yaml','--out','artifacts/matrix_offline']),
 ('matrix_active',[sys.executable,'-m','gsl_recovery','matrix','--manifest','examples/controlled/manifest.json','--config','configs/engineering_active.yaml','--out','artifacts/matrix_active','--active'])]
logdir=root/'artifacts/execution';logdir.mkdir(parents=True,exist_ok=True);receipts=[]
for name,command in commands:
 start=time.perf_counter()
 with open(logdir/(name+'.log'),'w',encoding='utf-8') as f:
  result=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,env=env,timeout=1200)
 receipt={'name':name,'command':command,'returncode':result.returncode,'wall_seconds':time.perf_counter()-start,'peak_child_RSS_MiB':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss/1024,'log':str((logdir/(name+'.log')).relative_to(root))}
 receipts.append(receipt);(logdir/'receipts.json').write_text(json.dumps(receipts,ensure_ascii=False,indent=2))
 print(json.dumps(receipt),flush=True)
 if result.returncode:raise SystemExit(result.returncode)
