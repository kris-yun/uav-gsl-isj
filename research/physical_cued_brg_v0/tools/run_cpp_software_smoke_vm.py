"""26 package tests and real C++/Python TCP exchange, functional only."""
import json,os,subprocess,sys,time,socket
from pathlib import Path
ROOT=Path('/home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927')
sys.path.insert(0,str(ROOT))
from pmfs_brg.bank import TemplateBank
out=Path('/home/zyc/brg_closedloop_20260927/cpp_software_smoke_02');out.mkdir(exist_ok=False)
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONNOUSERSITE='1',
    PYTHONPATH='/home/zyc/.local/lib/python3.10/site-packages:'+os.environ.get('PYTHONPATH',''))
with (out/'tests.log').open('w') as f:
    subprocess.run(['python3','-m','unittest','discover','-s','tests','-v'],cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
binary=out/'client_smoke'
subprocess.run(['g++','-std=c++17','-O2',str(ROOT/'integration/client_smoke.cpp'),'-o',str(binary)],check=True)
bank=TemplateBank.load(ROOT/'example_banks/h03_model_only.npz')
port=17931
with (out/'sidecar.log').open('w') as f:
    proc=subprocess.Popen(['python3',str(ROOT/'tools/serve.py'),'--checkpoint',str(ROOT/'trained/brg/best.pt'),
        '--bank',str(ROOT/'example_banks/h03_model_only.npz'),'--allow-warmstart','--tcp-port',str(port),'--threads','1',
        '--log',str(out/'sidecar_events.jsonl')],env=env,stdout=f,stderr=subprocess.STDOUT)
    try:
        for _ in range(200):
            if proc.poll() is not None:raise RuntimeError('sidecar exited')
            try:
                with socket.create_connection(('127.0.0.1',port),.2):break
            except OSError:time.sleep(.1)
        else:raise TimeoutError('sidecar readiness')
        c=subprocess.run([str(binary),str(port),bank.fingerprint,'624','1242','2.0','0.0','.2','0.0','0.0','0'],
            text=True,capture_output=True,check=True)
        (out/'client.log').write_text(c.stdout+c.stderr)
        report={'software_tests':'26 PASS','real_cpp_tcp_exchange':c.stdout.strip(),'software_only':True,
            'weights':'six-candidate functional warmstart; excluded from scored campaign','bank_count':624,'gas_truth_inputs':False}
        (out/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
    finally:
        proc.terminate()
        try:proc.wait(timeout=10)
        except subprocess.TimeoutExpired:proc.kill();proc.wait()
