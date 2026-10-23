"""Auditable neural training, source-evidence distillation, and checkpoints.

There is one observation-density anchor and one constrained evidence risk.
The source-evidence target is constructed by the projection operator; neither
the optimizer nor an extra loss term is claimed as an invention.
"""
from __future__ import annotations
from dataclasses import asdict,dataclass
from pathlib import Path
import hashlib,json,math,os,time
import numpy as np
import torch
from .model import NeuralJointGenerator,NeuralConfig,Geometry
from .teacher import PrivilegedPhysicalTeacher,PhysicalBank
from ..types import Action,Observation,Mechanism,observation_from_dict,observation_to_dict


def sha256(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@dataclass
class TrainConfig:
    epochs: int = 8
    batch_size: int = 8
    learning_rate: float = 0.002
    seed: int = 23
    device: str = 'cpu'
    wall_seconds: float = 900.
    memory_fraction: float = 0.75
    grad_clip: float = 5.
    evidence_tolerance: float = 0.05
    dual_step: float = 0.1
    max_dual: float = 20.
    target_batch: int = 4
    variant: str = 'nll'
    directional: bool = True


def select_device(config):
    if config.device.startswith('cuda'):
        if not torch.cuda.is_available():raise RuntimeError('BLOCKED_GPU_NOT_AVAILABLE')
        free,total=torch.cuda.mem_get_info(torch.device(config.device))
        if free<512*1024**2:raise RuntimeError('BLOCKED_GPU_FREE_MEMORY')
        torch.cuda.set_per_process_memory_fraction(config.memory_fraction,torch.device(config.device))
    elif config.device!='cpu':raise ValueError('Use explicit cpu or cuda device')
    return torch.device(config.device)


def episode_from_record(record,*,training=False):
    allowed={'id','source','mechanism','observations','metadata','world_index'}
    if set(record)-allowed:raise ValueError('Unsupported fields in offline episode')
    m=record['metadata']
    if training and (m.get('split')!='train' or m.get('training_allowed') is not True):
        raise ValueError('BLOCKED_TRAIN_PERMISSION')
    if m.get('scope') not in ('ENGINEERING_ONLY','NUMERICAL_ONLY','PHYSICALLY_QUALIFIED'):
        raise ValueError('Unqualified episode scope')
    if len(record['source'])!=2:raise ValueError('Offline labels must be 2D source coordinates')
    observations=[observation_from_dict(o) for o in record['observations']]
    if not observations:raise ValueError('Empty episode')
    return dict(record,observations=observations,mechanism=Mechanism(**record.get('mechanism',{})))


def load_dataset(manifest_path,split='train'):
    manifest_path=Path(manifest_path);manifest=json.loads(manifest_path.read_text())
    if manifest.get('format')!='gsl_v2_dataset':raise ValueError('Wrong V2 dataset format')
    selected=[];seen={}
    for e in manifest['episodes']:
        # Only routing metadata are read for other splits; no held-out values.
        key=e['lineage_group']
        if key in seen and seen[key]!=e['split']:raise ValueError('Physical lineage crosses train/development/test')
        seen[key]=e['split']
        if e['split']!=split:continue
        p=(manifest_path.parent/e['path']).resolve()
        if not p.is_relative_to(manifest_path.parent.resolve()):raise ValueError('Dataset path escapes its root')
        if sha256(p)!=e['sha256']:raise ValueError('Episode checksum mismatch')
        record=json.loads(p.read_text())
        if record['metadata']['split']!=split or record['metadata']['lineage_group']!=key:raise ValueError('Manifest/record lineage mismatch')
        selected.append(episode_from_record(record,training=split=='train'))
    if not selected:raise ValueError('Empty requested split')
    return manifest,selected


def write_dataset(root,records,config,geometry,candidates,extra=None):
    root=Path(root);root.mkdir(parents=True,exist_ok=True);entries=[]
    for index,record in enumerate(records):
        name=f'episodes/{index:05d}.json';p=root/name;p.parent.mkdir(exist_ok=True)
        p.write_text(json.dumps(record,ensure_ascii=False,indent=2))
        entries.append({'path':name,'sha256':sha256(p),'split':record['metadata']['split'],
                        'lineage_group':record['metadata']['lineage_group']})
    data={'format':'gsl_v2_dataset','config':asdict(config),'geometry':asdict(geometry),
          'candidates':np.asarray(candidates,float).tolist(),'episodes':entries,'extra':extra or {}}
    (root/'manifest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
    return root/'manifest.json'


def save_training_checkpoint(path,model,optimizer,epoch,dual,rng,config,manifest_sha,binding=None):
    path=Path(path);path.mkdir(parents=True,exist_ok=True)
    # Torch weights_only-compatible tensors and primitives, not executable objects.
    torch.save({'model':model.state_dict(),'optimizer':optimizer.state_dict(),
                'torch_rng':torch.get_rng_state(),'cuda_rng':torch.cuda.get_rng_state_all() if torch.cuda.is_available() else [],
                'epoch':int(epoch),'dual':float(dual)},path/'trainer.pt')
    (path/'trainer.json').write_text(json.dumps({'numpy_rng':rng.bit_generator.state,
          'config':asdict(config),'manifest_sha256':manifest_sha,'binding':binding or {},'trainer_sha256':sha256(path/'trainer.pt')},indent=2))


def _resume(path,model,optimizer,rng,config,manifest_sha,binding=None):
    path=Path(path);meta=json.loads((path/'trainer.json').read_text())
    if meta['manifest_sha256']!=manifest_sha or sha256(path/'trainer.pt')!=meta['trainer_sha256']:
        raise ValueError('Resume dataset/checkpoint mismatch')
    # Epoch cap and wall cap may increase; model, optimizer, objectives and seed may not.
    if meta.get('binding',{})!=(binding or {}):raise ValueError('Resume target/teacher/bank identity mismatch')
    for key in ('seed','variant','learning_rate','batch_size','evidence_tolerance','dual_step','target_batch','max_dual','grad_clip','directional'):
        if meta['config'].get(key,True if key=='directional' else None)!=asdict(config)[key]:raise ValueError('Resume objective/config changed: '+key)
    state=torch.load(path/'trainer.pt',map_location=model.device,weights_only=True)
    model.load_state_dict(state['model']);optimizer.load_state_dict(state['optimizer'])
    torch.set_rng_state(state['torch_rng'].cpu())
    if torch.cuda.is_available() and state['cuda_rng']:torch.cuda.set_rng_state_all(state['cuda_rng'])
    rng.bit_generator.state=meta['numpy_rng']
    return int(state['epoch']),float(state['dual'])


def load_targets(path,manifest_sha=None):
    root=Path(path);meta=json.loads((root/'targets.json').read_text())
    if meta.get('format')!='gsl_projected_targets_v2' or meta.get('split')!='train':raise ValueError('Unqualified teacher targets')
    if manifest_sha is not None and meta['manifest_sha256']!=manifest_sha:raise ValueError('Teacher target/data identity mismatch')
    result=[]
    for row in meta['targets']:
        r=dict(row);r['history']=[observation_from_dict(o) for o in row['history']]
        r['future']=[observation_from_dict(o) for o in row['future']]
        r['mechanism']=Mechanism(**row['mechanism']);result.append(r)
    if not result:raise ValueError('No qualified source-evidence targets')
    return meta,result


def train_student(manifest_path,out,config=None,targets=None,resume=None,model_override=None):
    config=config or TrainConfig();out=Path(out);out.mkdir(parents=True,exist_ok=True)
    device=select_device(config);torch.manual_seed(config.seed);rng=np.random.default_rng(config.seed)
    manifest,episodes=load_dataset(manifest_path,'train');digest=sha256(manifest_path)
    mcfg=NeuralConfig(**manifest['config'])
    model=model_override or NeuralJointGenerator(mcfg,Geometry(**manifest['geometry']))
    model.to(device);optimizer=torch.optim.Adam(model.parameters(),lr=config.learning_rate)
    variants=('nll','distribution','privileged_pair','mean_log','projected_evidence','projected_no_anchor')
    if config.variant not in variants:raise ValueError('Unknown student ablation')
    if config.variant=='nll' and targets is not None:raise ValueError('NLL baseline must not load teacher target artifacts')
    rows=None;target_meta=None
    if config.variant!='nll':
        if targets is None:raise ValueError('Distillation requires a qualified TRAIN target artifact')
        target_meta,rows=load_targets(targets,digest)
    binding={'targets_sha256':sha256(Path(targets)/'targets.json'),'teacher_version':target_meta['teacher_version']} if targets else {}
    start=0;dual=1.;clock=time.perf_counter();history=[]
    if resume:
        start,dual=_resume(resume,model,optimizer,rng,config,digest,binding)
        if (out/'training_curve.json').exists():
            history=json.loads((out/'training_curve.json').read_text())
            if history and history[-1]['epoch']!=start:raise ValueError('Resume curve/checkpoint epoch mismatch')
    if config.epochs<=start:raise ValueError('Resume epoch cap must exceed completed epoch')
    terminated='COMPLETE'
    for epoch in range(start,config.epochs):
        model.train();order=rng.permutation(len(episodes));stats=[]
        for offset in range(0,len(order),config.batch_size):
            if time.perf_counter()-clock>config.wall_seconds:
                terminated='STOP_WALL_BUDGET';break
            batch=[episodes[int(i)] for i in order[offset:offset+config.batch_size]]
            optimizer.zero_grad(set_to_none=True)
            nll=torch.stack([-model.log_prob_torch(e['observations'],e['source'],e['mechanism'])/len(e['observations']) for e in batch]).mean()
            evidence=torch.zeros((),device=device);density=nll*0
            if rows:
                target_rng=np.random.default_rng(config.seed+982451653*(epoch+1)+offset)
                picked=[rows[int(i)] for i in target_rng.integers(len(rows),size=config.target_batch)]
                margins=[];anchors=[]
                for row in picked:
                    la=model.conditional_log_prob_torch(row['history'],row['future'],row['a'],row['mechanism'])
                    lb=model.conditional_log_prob_torch(row['history'],row['future'],row['b'],row['mechanism'])
                    key={'privileged_pair':'privileged_pair','mean_log':'mean_log_pair'}.get(config.variant,'projected_pair')
                    endpoint_error=(lb-la-model.tensor(row[key])).square()
                    if config.directional and config.variant in ('projected_evidence','projected_no_anchor','privileged_pair','mean_log'):
                        sm=model.tensor(row['mid_source']).requires_grad_(True)
                        ls=model.conditional_log_prob_torch(row['history'],row['future'],sm,row['mechanism'])
                        gradient=torch.autograd.grad(ls,sm,create_graph=True)[0]
                        directional=torch.dot(gradient,model.tensor(row['direction']))
                        dkey={'privileged_pair':'privileged_direction','mean_log':'mean_log_direction'}.get(config.variant,'projected_direction')
                        margins.append(0.5*(endpoint_error+(directional-model.tensor(row[dkey])).square()))
                    else:margins.append(endpoint_error)
                    anchors.append(-(la if row['sampled_from']=='a' else lb)/len(row['future']))
                evidence=torch.stack(margins).mean();density=torch.stack(anchors).mean()
            if config.variant=='nll':loss=nll
            elif config.variant=='distribution':loss=0.5*(nll+density)
            elif config.variant=='projected_no_anchor':loss=evidence
            else:loss=0.5*(nll+density)+dual*(evidence-config.evidence_tolerance)
            if not torch.isfinite(loss):raise RuntimeError('STOP_NONFINITE_TRAINING_LOSS')
            loss.backward();norm=torch.nn.utils.clip_grad_norm_(model.parameters(),config.grad_clip)
            if not torch.isfinite(norm):raise RuntimeError('STOP_NONFINITE_GRADIENT')
            optimizer.step()
            if rows and config.variant not in ('distribution','projected_no_anchor'):
                dual=float(np.clip(dual+config.dual_step*(float(evidence.detach())-config.evidence_tolerance),0,config.max_dual))
            stats.append({'nll':float(nll.detach()),'evidence_risk':float(evidence.detach()),'density_ce':float(density.detach()),'dual':dual})
        if terminated!='COMPLETE':break
        row={'epoch':epoch+1,**{k:float(np.mean([s[k] for s in stats])) for k in stats[0]}}
        history.append(row);save_training_checkpoint(out/'resume',model,optimizer,epoch+1,dual,rng,config,digest,binding)
        (out/'training_curve.json').write_text(json.dumps(history,indent=2))
    model.eval();receipt={'status':terminated,'variant':config.variant,'epochs_completed':history[-1]['epoch'] if history else start,
         'wall_seconds':time.perf_counter()-clock,'parameters':sum(p.numel() for p in model.parameters()),
         'device':str(device),'max_cuda_allocated_bytes':torch.cuda.max_memory_allocated(device) if device.type=='cuda' else 0,
         'manifest_sha256':digest,'training_episodes':len(episodes),'unique_lineage_groups':len({e['metadata']['lineage_group'] for e in episodes}),
         'scope':mcfg.scope,'native_3d_physics_claim':False,'test_values_read':0,'target_teacher_version':None if target_meta is None else target_meta['teacher_version'],
         'normalized_density_anchor':config.variant!='projected_no_anchor',
         'evidence_constraint_status':'NOT_APPLICABLE' if config.variant=='nll' else 'TRAIN_MINIBATCH_DIAGNOSTIC_NOT_A_CERTIFICATE',
         'last_epoch_train_evidence_risk':history[-1]['evidence_risk'] if history and rows else None,
         'target_binding':binding,'directional_supervision':bool(rows and config.directional and config.variant!='distribution')}
    model.training_receipt=receipt;model.save(out/'model');(out/'training_receipt.json').write_text(json.dumps(receipt,indent=2))
    return receipt


def train_teacher(manifest_path,bank_path,out,config=None,resume=None):
    config=config or TrainConfig(epochs=8);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    torch.manual_seed(config.seed);rng=np.random.default_rng(config.seed);device=select_device(config)
    manifest,episodes=load_dataset(manifest_path,'train');bank=PhysicalBank.load(bank_path)
    mc=dict(manifest['config']);mc.update(hidden=96,geometry_width=32,query_width=64,modes=len(bank.points))
    model=PrivilegedPhysicalTeacher(bank,NeuralConfig(**mc),Geometry(**manifest['geometry'])).to(device)
    opt=torch.optim.Adam(model.parameters(),lr=config.learning_rate);start=0;clock=time.perf_counter();curve=[]
    continuation=None;continuation_path=None
    binding={'physical_bank_version':bank.version}
    if resume:
        start,_=_resume(resume,model,opt,rng,config,sha256(manifest_path),binding)
        previous_root=Path(resume).parent
        previous_curve=previous_root/'training_curve.json'
        continuation={'status':'STARTED','resumed_from_epoch':start,'epochs_completed':start,
             'requested_epoch_cap':config.epochs,'resume_checkpoint':str(Path(resume).resolve()),
             'resume_checkpoint_sha256':sha256(Path(resume)/'trainer.pt'),
             'prior_curve_available':previous_curve.exists(),'preserved_curve_rows':0,
             'prior_curve_snapshot':None,'prior_receipt_snapshot':None}
        if previous_curve.exists():
            curve=json.loads(previous_curve.read_text())
            if curve and curve[-1]['epoch']!=start:raise ValueError('Teacher resume curve/checkpoint epoch mismatch')
            curve_snapshot=out/f'training_curve_before_resume_{start:06d}_{sha256(previous_curve)[:12]}.json'
            curve_snapshot.write_bytes(previous_curve.read_bytes())
            continuation.update(preserved_curve_rows=len(curve),prior_curve_snapshot=curve_snapshot.name)
        previous_receipt=previous_root/'training_receipt.json'
        if previous_receipt.exists():
            receipt_snapshot=out/f'training_receipt_before_resume_{start:06d}_{sha256(previous_receipt)[:12]}.json'
            receipt_snapshot.write_bytes(previous_receipt.read_bytes())
            continuation['prior_receipt_snapshot']=receipt_snapshot.name
        continuation_path=out/f'continuation_{start:06d}_to_{config.epochs:06d}.json'
    if config.epochs<=start:raise ValueError('Resume epoch cap must increase')
    if continuation_path is not None:continuation_path.write_text(json.dumps(continuation,indent=2))
    for epoch in range(start,config.epochs):
        model.train();order=rng.permutation(len(episodes));losses=[]
        for offset in range(0,len(order),config.batch_size):
            if time.perf_counter()-clock>config.wall_seconds:
                if continuation is not None:
                    continuation['status']='STOP_WALL_BUDGET'
                    continuation_path.write_text(json.dumps(continuation,indent=2))
                raise RuntimeError('STOP_WALL_BUDGET; completed epoch checkpoint retained')
            batch=[episodes[int(i)] for i in order[offset:offset+config.batch_size]];opt.zero_grad(set_to_none=True);terms=[]
            for e in batch:
                j=e.get('world_index')
                if j is None or not 0<=j<len(bank.points):raise ValueError('Teacher training requires an authorized TRAIN exogenous-world index')
                if e['metadata'].get('bank_world_id')!=bank.metadata['world_ids'][j]:raise ValueError('Episode/physical-world lineage mismatch')
                terms.append(-model.atom_log_prob(e['observations'],model.tensor(e['source']),e['mechanism'])[j]/len(e['observations']))
            loss=torch.stack(terms).mean()
            if not torch.isfinite(loss):raise RuntimeError('Nonfinite teacher objective')
            loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),config.grad_clip);opt.step();losses.append(float(loss.detach()))
        curve.append({'epoch':epoch+1,'complete_state_nll':float(np.mean(losses))});save_training_checkpoint(out/'resume',model,opt,epoch+1,0.,rng,config,sha256(manifest_path),binding)
        (out/'training_curve.json').write_text(json.dumps(curve,indent=2))
        if continuation is not None:
            continuation.update(status='IN_PROGRESS',epochs_completed=epoch+1)
            continuation_path.write_text(json.dumps(continuation,indent=2))
    if continuation is not None:
        continuation.update(status='COMPLETE',epochs_completed=config.epochs)
        continuation_path.write_text(json.dumps(continuation,indent=2))
    model.eval();receipt={'status':'COMPLETE','scope':bank.metadata['scope'],'native_GADEN_teacher':'BLOCKED_QUALIFIED_MULTI_SOURCE_BANK_MISSING' if bank.metadata['scope']=='ENGINEERING_ONLY' else 'SURROGATE_ONLY_NOT_SIMULATOR_DERIVATIVE',
          'parameters':sum(p.numel() for p in model.parameters()),'epochs':config.epochs,'training_episodes':len(episodes),'bank_worlds':len(bank.points),
          'device':str(device),'wall_seconds':time.perf_counter()-clock,'manifest_sha256':sha256(manifest_path),'test_values_read':0,
          'source_ids_as_features':False,'full_field_read_only_during_training':True,
          'continuation':continuation}
    model.training_receipt=receipt;model.save(out/'model');(out/'training_curve.json').write_text(json.dumps(curve,indent=2));(out/'training_receipt.json').write_text(json.dumps(receipt,indent=2));return receipt


def build_targets(manifest_path,teacher_path,out,count=24,seed=23,order=6):
    manifest,episodes=load_dataset(manifest_path,'train');teacher=PrivilegedPhysicalTeacher.load(teacher_path)
    if teacher.training_receipt.get('manifest_sha256')!=sha256(manifest_path):raise ValueError('Teacher/dataset identity mismatch')
    projector=teacher.projector();rng=np.random.default_rng(seed);candidates=np.unique(np.array([e['source'] for e in episodes]),axis=0)
    if len(candidates)<2:raise ValueError('At least two TRAIN sources required for evidence targets')
    rows=[];attempts=[]
    for index in range(int(count)):
        e=episodes[int(rng.integers(len(episodes)))];obs=e['observations'];cut=max(1,len(obs)//2);h=obs[:cut]
        actions=[o.action for o in obs[cut:cut+3]]
        if not actions:raise ValueError('Need a legal future action block after the prefix')
        a,b=candidates[rng.choice(len(candidates),2,replace=False)];label='a' if rng.random()<.5 else 'b';s=a if label=='a' else b
        future,actual_mode=teacher.sample_future_with_mode(h,actions,s,e['mechanism'],rng)
        pair=projector.pair_endpoint(h,future,teacher.tensor(a),teacher.tensor(b),e['mechanism'])
        # Smooth-surrogate path only; native obstacle/branch path needs qualified validator.
        integral=projector.line_integral(h,future,teacher.tensor(a),teacher.tensor(b),e['mechanism'],order=order)
        av=teacher.atom_log_prob(h+future,teacher.tensor(a),e['mechanism'])-teacher.atom_log_prob(h,teacher.tensor(a),e['mechanism'])
        bv=teacher.atom_log_prob(h+future,teacher.tensor(b),e['mechanism'])-teacher.atom_log_prob(h,teacher.tensor(b),e['mechanism'])
        wa=projector.posterior_weights(h,teacher.tensor(a),e['mechanism']);wb=projector.posterior_weights(h,teacher.tensor(b),e['mechanism'])
        j=actual_mode
        sm=teacher.tensor((a+b)/2).requires_grad_(True);direction=teacher.tensor(b-a)
        cp=projector.conditional_log_prob(h,future,sm,e['mechanism'])
        projected_direction=torch.dot(torch.autograd.grad(cp,sm)[0],direction)
        sm=teacher.tensor((a+b)/2).requires_grad_(True)
        af=teacher.atom_log_prob(h+future,sm,e['mechanism'])-teacher.atom_log_prob(h,sm,e['mechanism'])
        privileged_direction=torch.dot(torch.autograd.grad(af[j],sm,retain_graph=True)[0],direction)
        ww=projector.posterior_weights(h,sm,e['mechanism'])
        mean_log_direction=torch.dot(torch.autograd.grad((ww*af).sum(),sm)[0],direction)
        # Deliberately labeled controls: oracle atom, and E log p instead of log E p.
        record={'history':[observation_to_dict(o) for o in h],'future':[observation_to_dict(o) for o in future],
                'a':a.tolist(),'b':b.tolist(),'mechanism':asdict(e['mechanism']),'sampled_from':label,
                'projected_pair':float(pair.detach()),'privileged_pair':float((bv[j]-av[j]).detach()),
                'mean_log_pair':float(((wb*bv).sum()-(wa*av).sum()).detach()),
                'path_certificate':integral.as_record(),'history_world':e['id'],
                'mid_source':((a+b)/2).tolist(),'direction':(b-a).tolist(),
                'projected_direction':float(projected_direction.detach()),'privileged_direction':float(privileged_direction.detach()),
                'mean_log_direction':float(mean_log_direction.detach()),'privileged_rollout_mode':actual_mode}
        rows.append(record)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    def clean(x):
        if torch.is_tensor(x):return x.detach().cpu().tolist()
        if isinstance(x,np.ndarray):return x.tolist()
        if hasattr(x,'__dataclass_fields__'):return {k:clean(v) for k,v in asdict(x).items()}
        if isinstance(x,dict):return {k:clean(v) for k,v in x.items()}
        if isinstance(x,(tuple,list)):return [clean(v) for v in x]
        return x
    payload={'format':'gsl_projected_targets_v2','split':'train','manifest_sha256':sha256(manifest_path),'teacher_version':teacher.version,
             'teacher_scope':teacher.bank.metadata['scope'],'native_gradient_claim':False,'source_candidates_from':'training_sources_only',
             'generation':'whole teacher joint rollout; no realized future wind used','targets':clean(rows)}
    (out/'targets.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False));return {k:v for k,v in payload.items() if k!='targets'}|{'count':len(rows),'out':str(out)}
