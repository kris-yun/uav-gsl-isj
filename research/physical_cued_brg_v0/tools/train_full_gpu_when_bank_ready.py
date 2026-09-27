#!/usr/bin/env python3
"""Immediate execution pipeline for the authorized full-support OPEN recipe."""
import argparse,hashlib,json,os,subprocess,sys,time
from pathlib import Path

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);a=ap.parse_args();root=Path(a.root)
    remote='/home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927'
    key=str(Path.home()/'.ssh/id_ed25519_vm');host='zyc@192.168.111.128'
    ssh=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8','-i',key,host]
    scp=['scp','-i',key]
    banks=root/'legal_training_banks';banks.mkdir(exist_ok=True)
    print('WAITING_FOR_FULL_SUPPORT_BANK_NOT_USING_SIX_CANDIDATE_WEIGHTS',flush=True)
    while True:
        p=subprocess.run(ssh+['test -f '+remote+'/full_support/BANK_COMPLETE.json'],capture_output=True)
        h01=subprocess.run(ssh+['test -f '+remote+'/h01_native_rebuild/BANK_COMPLETE.json'],capture_output=True)
        if p.returncode==0 and h01.returncode==0:
            subprocess.run(ssh+['bash '+remote+'/tools/run_bind_native_bank_views_vm.sh'],check=True)
            break
        if p.returncode not in (1,255):raise RuntimeError('unexpected bank readiness status')
        print('BANK_PENDING',time.strftime('%Y-%m-%d %H:%M:%S'),flush=True);time.sleep(45)
    for name in ['LEGAL_SUPPORT_COMPLETE.json','LEGAL_MASKS_COMPLETE.json']+[f'env_{e}_bank.npz' for e in range(3)]:
        subprocess.run(scp+[host+':'+remote+'/legal_support_v2/'+name,str(banks/name)],check=True)
    complete=json.loads((banks/'LEGAL_SUPPORT_COMPLETE.json').read_text())
    for row in complete['banks']:
        p=banks/f'env_{row["environment"]}_bank.npz'
        assert hashlib.sha256(p.read_bytes()).hexdigest()==row['bank_sha256']
    source=root/'data/open_vm';source.mkdir(parents=True,exist_ok=True)
    for name in ['manifest.json']+[f'env_{e}_open.npz' for e in range(3)]:
        subprocess.run(scp+[host+':'+remote+'/data/open/'+name,str(source/name)],check=True)
    dest=root/'data/full_open'
    subprocess.run([sys.executable,'-I',str(root/'tools/align_full_support_training.py'),'--data',str(source),'--banks',str(banks),'--out',str(dest)],check=True)
    env=dict(os.environ,PYTHONNOUSERSITE='1',PYTHONUTF8='1',CUBLAS_WORKSPACE_CONFIG=':4096:8',BRG_TRAIN_DEVICE='cuda')
    for variant,width in [('gru',35),('brg',32),('ungated',32)]:
        command=[sys.executable,'-I',str(root/'tools/train.py'),'--data',str(dest),'--out',str(root/'trained_full'/variant),
            '--variant',variant,'--hidden',str(width),'--epochs','30','--routes','8','--batch','48','--threads','2','--seed','2026092701']
        print('FIXED_GPU_TRAINING',json.dumps(command),flush=True)
        subprocess.run(command,env=env,check=True)
    configs=[json.loads((root/'trained_full'/v/'run_config.json').read_text()) for v in ['gru','brg','ungated']]
    assert all(c['training_groups']==configs[0]['training_groups'] and c['development_groups']==configs[0]['development_groups'] for c in configs)
    assert len(configs[0]['training_groups'])==216 and len(configs[0]['development_groups'])==72
    assert not set(configs[0]['training_groups']) & set(configs[0]['development_groups'])
    routes=[(root/'trained_full'/v/'routes.json').read_bytes() for v in ['gru','brg','ungated']];assert routes[0]==routes[1]==routes[2]
    weights={v:hashlib.sha256((root/'trained_full'/v/'best.pt').read_bytes()).hexdigest() for v in ['gru','brg','ungated']}
    freeze={'purpose':'OPEN_NATIVE_LEGAL_FULL_SUPPORT_CHECKPOINT_FREEZE_BEFORE_P0_P1','weights_sha256':weights,
        'native_legal_support_complete_sha256':hashlib.sha256((banks/'LEGAL_SUPPORT_COMPLETE.json').read_bytes()).hexdigest(),
        'manifest_sha256':hashlib.sha256((dest/'manifest.json').read_bytes()).hexdigest(),
        'train_dev_leakage':False,'independent_train_plumes':216,'independent_dev_plumes':72,
        'same_routes':True,'same_full_support':True,'legal_rule':'Native fine z0.20 slice / scale3 / fixed-start prune','pilot_only_until_P1_STOP':True,'house03_gas_used_for_training':False}
    (root/'CHECKPOINT_FREEZE.json').write_text(json.dumps(freeze,indent=2)+'\n')
    subprocess.run(ssh+['mkdir -p '+remote+'/trained_full'],check=True)
    subprocess.run(scp+['-r',str(root/'trained_full/gru'),str(root/'trained_full/brg'),str(root/'trained_full/ungated'),host+':'+remote+'/trained_full/'],check=True)
    subprocess.run(scp+[str(root/'CHECKPOINT_FREEZE.json'),host+':'+remote+'/CHECKPOINT_FREEZE.json'],check=True)
    print('FULL_SUPPORT_GPU_TRAINING_AND_TRANSFER_COMPLETE',json.dumps(freeze),flush=True)
if __name__=='__main__':main()
