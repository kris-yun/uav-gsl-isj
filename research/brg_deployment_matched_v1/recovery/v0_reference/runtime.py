"""Stateful causal inference + PMFS planner-cache update. No target labels allowed."""
from __future__ import annotations
import hashlib,json,math
import numpy as np
import torch
from .features import FeatureConfig,encode
from .model import load_checkpoint,log_posterior

class InferenceSession:
    def __init__(self,model,metadata,bank,allow_warmstart=False,max_events=128):
        if metadata.get('deployment_status')!='VALIDATED_FOR_LOCKED_CLOSED_LOOP' and not allow_warmstart:
            raise ValueError('warm-start weights require explicit --allow-warmstart; no validated policy shipped')
        self.model=model.eval();self.metadata=metadata;self.bank=bank
        self.feature_cfg=FeatureConfig(**metadata['feature_config'])
        self.max_events=max_events;self.run_id=None;self.temperature=float(metadata.get('temperature',1.))
        self.prior=np.ones(len(bank.ids))/len(bank.ids)
    def reset(self,run_id,expected_bank,prior=None):
        if expected_bank!=self.bank.fingerprint:raise ValueError('template version mismatch')
        if not run_id or not isinstance(run_id,str):raise ValueError('explicit run id required')
        self.run_id=run_id;self.h=self.model.initial(1,len(self.bank.ids));self.last_event=None;self.last_digest=None;self.last_response=None;self.last_time=-np.inf;self.count=0
        if prior is not None:
            prior=np.asarray(prior,dtype=float)
            if prior.shape!=(len(self.bank.ids),) or not np.isfinite(prior).all() or (prior<=0).any():raise ValueError('bad prior')
            self.prior=prior/prior.sum()
        else:self.prior=np.ones(len(self.bank.ids))/len(self.bank.ids)
        return {'status':'RESET','bank_id':self.bank.fingerprint,'sources':len(self.bank.ids),'map_cells':self.bank.n}

    @torch.inference_mode()
    def observe(self,event):
        allowed={'run_id','event_id','time_s','x','y','z','concentration_ppm'}
        if set(event)!=allowed:raise ValueError(f'event schema mismatch; extra/missing: {set(event)^allowed}')
        if self.run_id is None or event['run_id']!=self.run_id:raise ValueError('reset/run mismatch')
        eid=event['event_id']
        if not isinstance(eid,int) or eid<0:raise ValueError('integer monotonic event id required')
        nums=[float(event[k]) for k in ['time_s','x','y','z','concentration_ppm']]
        if not all(math.isfinite(v) for v in nums) or nums[-1]<0:raise ValueError('invalid event values')
        digest=hashlib.sha256(json.dumps(event,sort_keys=True,allow_nan=False).encode()).hexdigest()
        if self.last_event==eid:
            if digest!=self.last_digest:raise ValueError('same event id with different contents')
            return self.last_response
        if self.last_event is not None and eid<=self.last_event:raise ValueError('stale/reordered event')
        if nums[0]<=self.last_time:raise ValueError('non-increasing event time')
        if self.count>=self.max_events:raise ValueError('history budget exceeded; no silent reset')
        if abs(nums[3]-float(self.bank.meta['height_m']))>1e-4:raise ValueError('height outside template contract')
        footprint=(float(self.bank.meta.get('footprint_x_m',.2)),float(self.bank.meta.get('footprint_y_m',.2)))
        p,u=self.bank.project([[nums[1],nums[2]]],footprint)
        o,c=encode([nums[4]],[[nums[1],nums[2]]],self.bank.xy,p,u,self.feature_cfg)
        logits,h=self.model.step(torch.from_numpy(o),torch.from_numpy(c),self.h)
        lp=log_posterior(logits.double(),self.prior,self.temperature)[0]
        q=lp.exp().cpu().numpy()
        if not np.isfinite(q).all() or abs(q.sum()-1)>1e-8:raise ValueError('invalid model probabilities')
        src,var=self.bank.planner_maps(q)
        self.h=h;self.count+=1;self.last_time=nums[0];self.last_event=eid;self.last_digest=digest
        self.last_response={'status':'OK','run_id':self.run_id,'event_id':eid,'bank_id':self.bank.fingerprint,'q':q.tolist(),'log_q':lp.cpu().numpy().tolist(),'source_map':src.tolist(),'variance_of_hit_prob':var.tolist(),'observations':self.count,'history_extrapolated':self.count>int(self.metadata.get('max_tested_history',10))}
        return self.last_response
