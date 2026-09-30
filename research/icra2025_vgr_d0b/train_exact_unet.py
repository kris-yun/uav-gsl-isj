"""D0B supervised engineering test, exact upstream U-Net/loss, no PMFS execution."""
import ast,hashlib,json,os,random,sys,time
os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset,DataLoader
from audit_open49 import OUT,ROOT,CACHE,load,dump,sha
METHOD=Path(r'D:\ZYC\Topography-aware-Gas-Source')
UP=METHOD/'Topography-aware-Gas-Source-Localization-lfs'

class PrefixDataset(Dataset):
    def __init__(self,rows):
        self.items=[]
        for r in rows:
            assert sha(r['path'])==r['sha256']
            with np.load(r['path'],allow_pickle=False) as z:self.items.append((z['x'].copy(),z['label'].copy()))
    def __len__(self):return len(self.items)*4
    def __getitem__(self,i):
        x,y=self.items[i//4];k=i%4
        return torch.from_numpy(np.rot90(x,k,axes=(1,2)).copy()),torch.from_numpy(np.rot90(y,k).copy())

def exact_definitions():
    nb=load(UP/'train/GSL_train.ipynb');text=''.join(nb['cells'][2]['source'])
    nodes=[n for n in ast.parse(text).body if isinstance(n,ast.ClassDef)]
    infer=load(UP/'train/GSLInference.ipynb');ni=[n for n in ast.parse(''.join(infer['cells'][2]['source'])).body if isinstance(n,ast.ClassDef)]
    assert [ast.dump(n,include_attributes=False) for n in nodes if n.name!='CustomLoss']==[ast.dump(n,include_attributes=False) for n in ni]
    ns=dict(torch=torch,nn=nn,F=F);exec(compile(ast.Module(body=nodes,type_ignores=[]),'<exact-upstream-cell2>','exec'),ns)
    return ns['UNet'],ns['CustomLoss'],hashlib.sha256('\n'.join(ast.dump(n,include_attributes=False) for n in nodes).encode()).hexdigest()

def main():
    freeze=OUT/'PRE_TARGET_TRAINING_FREEZE.json';c=load(freeze);assert sha(freeze)==sys.argv[1]
    assert sha(OUT/'PREFIX_MANIFEST.json')==c['input_manifest_sha256']
    for n,h in c['notebooks_sha256'].items():assert sha(UP/'train'/n)==h
    for n,h in c['code_sha256'].items():assert sha(ROOT/'research/icra2025_vgr_d0b'/n)==h
    seed=c['seed'];random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)
    torch.set_num_threads(2);torch.use_deterministic_algorithms(True);torch.backends.cudnn.benchmark=False;torch.backends.cudnn.deterministic=True
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    assert torch.cuda.is_available();UNet,Loss,astsha=exact_definitions();device='cuda'
    rows=load(OUT/'PREFIX_MANIFEST.json');train=PrefixDataset([r for r in rows if r['split']=='train']);val=PrefixDataset([r for r in rows if r['split']=='validation'])
    tl=DataLoader(train,batch_size=c['batch_size'],shuffle=True,num_workers=0,generator=torch.Generator().manual_seed(seed));vl=DataLoader(val,batch_size=c['batch_size'],shuffle=False,num_workers=0)
    model=UNet(3,1).to(device);criterion=Loss(positive_weight=5.);optimizer=torch.optim.Adam(model.parameters(),lr=c['learning_rate'],weight_decay=c['weight_decay'])
    scheduler=torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer,mode='min',factor=.5,patience=5)
    dest=CACHE/'training';dest.mkdir(exist_ok=True);checkpoint=dest/'best_validation_unet.pth';assert not checkpoint.exists(),'Do not overwrite an earlier model'
    history=[];best=float('inf');start=time.perf_counter()
    print('TRAIN_START',torch.cuda.get_device_name(0),'TRAIN_SAMPLES',len(train),'VAL_SAMPLES',len(val),'EPOCHS',c['max_epochs'],flush=True)
    for epoch in range(1,c['max_epochs']+1):
        estart=time.perf_counter();model.train();total=0.
        for i,(x,y) in enumerate(tl,1):
            x=x.to(device);y=y.to(device).unsqueeze(1);optimizer.zero_grad();p=model(x);loss=criterion(p,y);assert torch.isfinite(loss)
            loss.backward();optimizer.step();total+=float(loss.detach().cpu())
            if i%50==0:print('BATCH',epoch,i,'/',len(tl),'elapsed_s',round(time.perf_counter()-estart,1),flush=True)
        model.eval();vtotal=0.
        with torch.inference_mode():
            for x,y in vl:vtotal+=float(criterion(model(x.to(device)),y.to(device).unsqueeze(1)).cpu())
        vloss=vtotal/len(vl);scheduler.step(vloss);improved=vloss<best
        if improved:best=vloss;torch.save(model.state_dict(),checkpoint)
        item=dict(epoch=epoch,train_loss=total/len(tl),validation_loss=vloss,lr=optimizer.param_groups[0]['lr'],new_best=improved,epoch_s=time.perf_counter()-estart)
        history.append(item);dump(OUT/'TRAINING_HISTORY.json',history);print('EPOCH',json.dumps(item),flush=True)
    result=dict(decision='D0B_TRAINING_COMPLETE',epochs=len(history),best_epoch=min(history,key=lambda r:r['validation_loss'])['epoch'],best_validation_loss=best,
        checkpoint_path=str(checkpoint),checkpoint_sha256=sha(checkpoint),checkpoint_bytes=checkpoint.stat().st_size,
        training_s=time.perf_counter()-start,network_loss_ast_sha256=astsha,parameter_count=sum(p.numel() for p in model.parameters()),
        device=torch.cuda.get_device_name(0),torch_version=torch.__version__,freeze_sha256=sha(freeze),
        train_samples=len(train),validation_samples=len(val),new_gaden=0,new_pmfs=0,target_used_for_training=False,confirmation_read=False,house03_read=False)
    dump(OUT/'TRAINING_RESULT.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':main()
