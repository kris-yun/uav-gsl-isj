"""Complete the authorized fixed one-case workflow after the existing trainer exits."""
import json,subprocess,sys,time
from pathlib import Path
import psutil
from audit_open49 import ROOT,OUT,CACHE,load,dump,sha

def main():
    pid=int(sys.argv[1]);process=psutil.Process(pid);assert 'train_exact_unet.py' in ' '.join(process.cmdline())
    creation=process.create_time();start=time.monotonic();receipt=CACHE/'WORKFLOW_STATUS.json'
    dump(receipt,dict(status='WAITING_FOR_FROZEN_20_EPOCH_TRAINER',trainer_pid=pid,worker_pid=__import__('os').getpid(),trainer_creation_time=creation,
        subsequent_steps=['one existing target inference','review package and Git commit/push','STOP'],new_simulations=0))
    while psutil.pid_exists(pid):
        try:
            if psutil.Process(pid).create_time()!=creation:break
        except psutil.NoSuchProcess:break
        if time.monotonic()-start>3*3600:raise TimeoutError('Trainer exceeded finite workflow wait; no inference launched')
        time.sleep(15)
    trained=load(OUT/'TRAINING_RESULT.json');assert trained['epochs']==20
    assert trained['freeze_sha256']=='4df3b5a7c46a059ba67ec7f90c020857160040c9d85e29e70c352ac1262f4ca7'
    assert sha(trained['checkpoint_path'])==trained['checkpoint_sha256']
    for name in ['evaluate_existing_target.py','package_d0b.py']:
        dump(receipt,dict(status='RUNNING_'+name,trainer_pid=pid,new_simulations=0))
        subprocess.run([sys.executable,'-u',str(ROOT/'research/icra2025_vgr_d0b'/name)],cwd=ROOT,check=True)
    final=load(CACHE/'FINAL_REVIEW_RECEIPT.json');dump(receipt,dict(status='COMPLETED_AND_STOPPED',**final))

if __name__=='__main__':
    try:main()
    except Exception as exc:
        dump(CACHE/'WORKFLOW_STATUS.json',dict(status='D0B_HOLD_EXECUTION',error=repr(exc),new_simulations=0,scientific_result_not_reclassified=True))
        raise
