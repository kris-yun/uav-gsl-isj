"""Train-time physical-field-conditioned teacher, with an exogenous world bank.

This is a runnable surrogate architecture, not an instrumented GADEN solver.
Full 3D gas fields may supply *training readouts*, never a source-independent
bank of actual-source plume snapshots. Native physics qualification is strict.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from pathlib import Path
import hashlib,json,math
import numpy as np
import torch
from torch import nn
from .model import NeuralJointGenerator,NeuralConfig,Geometry
from ..types import Mechanism


@dataclass
class PhysicalBank:
    # [world, point, 7] = xyz, time, 3D wind. Each world is one nuisance draw.
    points: np.ndarray
    log_weights: np.ndarray
    metadata: dict

    def __post_init__(self):
        self.points=np.asarray(self.points,np.float32)
        self.log_weights=np.asarray(self.log_weights,np.float32)
        if self.points.ndim!=3 or self.points.shape[2]!=7 or min(self.points.shape[:2])<1:
            raise ValueError('Physical bank points must be [K,P,7]=xyz,time,wind_xyz')
        if not np.isfinite(self.points).all() or self.log_weights.shape!=(len(self.points),) or not np.isfinite(self.log_weights).all():
            raise ValueError('Invalid physical bank support/weights')
        m=self.metadata
        if m.get('split')!='train' or m.get('source_independent_exogenous') is not True:
            raise ValueError('BLOCKED_BANK: only TRAIN exogenous wind/world bank accepted; true-source gas snapshots are forbidden')
        if m.get('wind_units')!='m/s' or m.get('position_units')!='m' or m.get('time_units')!='s':
            raise ValueError('BLOCKED_BANK_UNITS')
        if m.get('scope') not in ('ENGINEERING_ONLY','PHYSICALLY_QUALIFIED_TRAIN'):
            raise ValueError('BLOCKED_BANK_SCOPE')
        if m.get('scope')=='PHYSICALLY_QUALIFIED_TRAIN':
            required=('physics_qualification_sha256','readout_contract_sha256','world_lineage_sha256')
            if any(len(str(m.get(k,'')))!=64 for k in required):
                raise ValueError('BLOCKED_NATIVE_TEACHER_QUALIFICATION: missing physical/readout/lineage receipts')
        ids=m.get('world_ids',[])
        if len(ids)!=len(self.points) or len(set(ids))!=len(ids):
            raise ValueError('Each bank atom needs a distinct documented exogenous world ID')

    @property
    def version(self):
        h=hashlib.sha256(self.points.tobytes()+self.log_weights.tobytes())
        h.update(json.dumps(self.metadata,sort_keys=True).encode());return h.hexdigest()

    def save(self,path):
        path=Path(path);path.mkdir(parents=True,exist_ok=True)
        np.savez_compressed(path/'physical_bank.npz',points=self.points,log_weights=self.log_weights)
        meta=dict(self.metadata,bank_sha256=self.version)
        (path/'physical_bank.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False))

    @classmethod
    def load(cls,path):
        path=Path(path);m=json.loads((path/'physical_bank.json').read_text());expected=m.pop('bank_sha256')
        with np.load(path/'physical_bank.npz',allow_pickle=False) as data:
            bank=cls(data['points'],data['log_weights'],m)
        if bank.version!=expected: raise ValueError('Physical bank checksum mismatch')
        return bank


class PrivilegedPhysicalTeacher(NeuralJointGenerator):
    format_version='gsl_physical_teacher_v2'

    def __init__(self,bank,config=None,geometry=None,field_width=32):
        config=config or NeuralConfig(hidden=96,query_width=64,geometry_width=32,modes=len(bank.points))
        if config.modes!=len(bank.points): raise ValueError('Teacher modes are exogenous bank atoms')
        super().__init__(config,geometry,extra_width=int(field_width))
        self.bank=bank;self.field_width=int(field_width)
        self.register_buffer('physical_points',torch.tensor(bank.points))
        self.register_buffer('bank_prior',torch.tensor(bank.log_weights))
        # No learned world ID: all atom-specific representation comes from fields.
        self.mode_embeddings.requires_grad_(False)
        with torch.no_grad(): self.mode_embeddings.zero_()
        self.field_encoder=nn.Sequential(nn.Linear(10,field_width),nn.SiLU(),nn.Linear(field_width,field_width),nn.Tanh())
        self.field_initial=nn.Linear(field_width,config.hidden)
        self.wind_noise=nn.Parameter(torch.tensor([-1.5,-1.5]))

    def _field_weights(self,action):
        points=self.physical_points
        if not self.bank.metadata.get('static_wind',False):
            tmin=points[:,:,3].min(dim=1).values;tmax=points[:,:,3].max(dim=1).values
            if not bool(((tmin<=action.time)&(action.time<=tmax)).all()): raise ValueError('BLOCKED_TEACHER_TIME_SUPPORT')
        q=self.tensor([action.x,action.y,action.z]);dt=(points[:,:,3]-action.time)/self.config.time_scale
        if self.bank.metadata.get('static_wind',False): dt=dt*0
        d2=((points[:,:,:3]-q)/self.config.length_scale).square().sum(-1)
        return torch.softmax(-0.5*(d2+dt.square()),dim=1)

    def _extra(self,source,action):
        points=self.physical_points
        s3=torch.cat((source,self.tensor([self.config.source_height])))
        q=self.tensor([action.x,action.y,action.z])
        dt=(points[:,:,3:4]-action.time)/self.config.time_scale
        if self.bank.metadata.get('static_wind',False):dt=dt*0
        feats=torch.cat(((points[:,:,:3]-s3)/self.config.length_scale,
                         (points[:,:,:3]-q)/self.config.length_scale,
                         points[:,:,4:7]/self.config.wind_scale,dt),-1)
        weights=self._field_weights(action)
        return (weights[:,:,None]*self.field_encoder(feats)).sum(1)

    def initial_state(self,source):
        h,_=super().initial_state(source)
        # Fixed legal map centroid query keeps source gradients through field features.
        p=self.physical_points[:,:,0:3].mean((0,1)).detach().cpu().numpy()
        from ..types import Action
        common_start=float(self.physical_points[:,:,3].min(dim=1).values.max())
        common_end=float(self.physical_points[:,:,3].max(dim=1).values.min())
        if common_start>common_end and not self.bank.metadata.get('static_wind',False):raise ValueError('BLOCKED_NO_COMMON_BANK_TIME')
        action=Action(*map(float,p),time=common_start)
        h=torch.tanh(h+self.field_initial(self._extra(source,action)))
        return h,torch.log_softmax(self.bank_prior,0)

    def _emission_parameters(self,h,q,mechanism,index,action,mode_indices=None):
        params=list(super()._emission_parameters(h,q,mechanism,index,action,mode_indices))
        mean=(self._field_weights(action)[:,:,None]*self.physical_points[:,:,4:6]).sum(1)
        if mode_indices is not None:mean=mean[mode_indices]
        m=mechanism or Mechanism()
        if m.kind=='wind_bias' and m.active(index):mean=mean+self.tensor([m.magnitude,0.])
        params[0]=mean
        params[1]=(torch.nn.functional.softplus(self.wind_noise)+self.config.min_wind_sigma).expand_as(mean)*self.config.wind_scale
        return tuple(params)

    def atom_log_prob(self,history,source,mechanism=None):
        return self.filter_torch(history,source,mechanism)[3]

    def log_prior(self,source):
        # Leave the source connected with a zero term for the identity tests.
        return self.bank_prior+source.sum()*0

    def projector(self,require_native=False):
        from ..m1_distill.projection import ConditionalEvidenceProjector
        if require_native:
            raise ValueError('BLOCKED_NATIVE_DERIVATIVE: this is a smooth surrogate; GADEN Malliavin/ASD is not instrumented')
        # This derivative is of the learned smooth *surrogate*, not of GADEN.
        return ConditionalEvidenceProjector(self.atom_log_prob,self.log_prior,derivative_valid=True)

    @property
    def version(self):
        return hashlib.sha256((super().version+self.bank.version).encode()).hexdigest()[:20]

    def save(self,path):
        super().save(path);path=Path(path)
        self.bank.save(path/'bank')
        m=json.loads((path/'model.json').read_text());m.update(field_width=self.field_width,
             training_only=True,native_malliavin_asd='BLOCKED_NOT_INSTRUMENTED',
             derivative_scope='smooth_surrogate_only; not unbiased simulator derivative')
        (path/'model.json').write_text(json.dumps(m,indent=2,ensure_ascii=False))

    @classmethod
    def load(cls,path,device='cpu'):
        path=Path(path);meta=json.loads((path/'model.json').read_text())
        if meta.get('format')!=cls.format_version:raise ValueError('Wrong teacher checkpoint format')
        if hashlib.sha256((path/'weights.pt').read_bytes()).hexdigest()!=meta['weights_sha256']:raise ValueError('Teacher checkpoint hash mismatch')
        model=cls(PhysicalBank.load(path/'bank'),NeuralConfig(**meta['config']),Geometry(**meta['geometry']),meta['field_width']).to(device)
        model.load_state_dict(torch.load(path/'weights.pt',map_location=device,weights_only=True));model.training_receipt=meta.get('receipt',{})
        model.eval()
        if model.version!=meta['version']:raise ValueError('Teacher identity mismatch')
        return model
