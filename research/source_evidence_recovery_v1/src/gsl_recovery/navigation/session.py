"""Persistent simulator/robot adapter: JSONL, retained risk and pending block.
The native supervisor supplies collision-checked action blocks and complete
sensor blocks. No source truth, future wind, or response library is accepted.
"""
from dataclasses import asdict
import numpy as np
from ..types import Action,Mechanism,observation_from_dict
from ..m2_replay import EvidenceLedger,ReplayEngine
from ..m3_codebook import JointCodebookBuilder,CorruptionChannel
from ..m3_planner import RobustCounterEvidencePlanner
from ..posterior import source_map

class ActiveSession:
    def __init__(self,model,sources,mechanisms,seed=0,draws=128,wall_seconds=10.):
        from ..pipeline import inference_version
        self.model=model;self.sources=np.asarray(sources,float);self.mechanisms=list(mechanisms)
        self.version=inference_version(model,mechanisms,sources);self.ledger=EvidenceLedger()
        self.engine=ReplayEngine(model,sources,mechanisms,model_version=self.version)
        self.planner=RobustCounterEvidencePlanner(len(sources),CorruptionChannel(max_flips=1),seed=seed)
        self.builder=JointCodebookBuilder(model,model_version=self.version)
        self.rng=np.random.default_rng(seed+1);self.pending=None;self.round=0
        self.draws=int(draws);self.wall_seconds=float(wall_seconds)

    def request(self,obj):
        allowed={'op','action_blocks','navigation_qualified','observations','costs'}
        if set(obj)-allowed:raise ValueError('Unknown or oracle request fields: '+str(set(obj)-allowed))
        if obj.get('op')=='plan':
            if self.pending is not None:raise ValueError('Pending block must be completed; no unregistered replan')
            if obj.get('navigation_qualified') is not True:raise ValueError('Native collision/timing qualification required')
            blocks=[[Action(**a) for a in block] for block in obj['action_blocks']]
            now=self.ledger.history[-1].action.time if len(self.ledger) else -float('inf')
            for b in blocks:
                times=[now]+[a.time for a in b]
                if any(t2<=t1 for t1,t2 in zip(times,times[1:])):raise ValueError('Action time must increase')
            result=self.engine.infer(self.ledger.history)
            books=self.builder.build(self.ledger.history,blocks,self.sources,self.mechanisms,self.draws,self.rng,
                                     delta=.01/((self.round+1)*(self.round+2)),costs=obj.get('costs'),wall_seconds=self.wall_seconds)
            self.pending=self.planner.plan(books,result.source_posterior,result.conditional_mechanism_posterior)
            return {'op':'plan','plan_id':self.pending.plan_id,'actions':[asdict(a) for a in self.pending.actions],
                    'reason':self.pending.reason,'model_version':self.version,'risk_spent':self.planner.risk.spent,
                    'source_map':source_map(self.sources,result.source_posterior)}
        if obj.get('op')=='observe':
            if self.pending is None:raise ValueError('No committed action block')
            observations=[observation_from_dict(o) for o in obj['observations']]
            candidate=EvidenceLedger(self.ledger.history);candidate.extend(observations)
            outcome=self.planner.observe(self.pending,observations,model_version=self.version)
            self.ledger=candidate;self.pending=None;self.round+=1
            result=self.engine.infer(self.ledger.history)
            return {'op':'update','observations':len(self.ledger),'test':outcome,'model_version':self.version,
                    'source_map':source_map(self.sources,result.source_posterior),'source_log_posterior':result.source_log_posterior,
                    'conditional_mechanism_posterior':result.conditional_mechanism_posterior,'joint_posterior':result.joint_posterior}
        raise ValueError('op must be plan or observe')

def run_jsonl(model_path,setup_path,instream,outstream,log_path=None):
    import json
    from pathlib import Path
    from ..m1_generator import JointObservationGenerator
    from ..io import read_json,json_default
    setup=read_json(setup_path)
    allowed={'candidates','mechanisms','seed','draws','wall_seconds'}
    if set(setup)-allowed:raise ValueError('Setup cannot contain truth/response assets')
    session=ActiveSession(JointObservationGenerator.load(model_path),setup['candidates'],[Mechanism(**e) for e in setup['mechanisms']],setup.get('seed',0),setup.get('draws',128),setup.get('wall_seconds',10.))
    logger=None
    if log_path:
        Path(log_path).parent.mkdir(parents=True,exist_ok=True);logger=open(log_path,'a',encoding='utf-8')
    try:
        for line in instream:
            if not line.strip():continue
            request=json.loads(line);response=session.request(request)
            encoded=json.dumps(response,ensure_ascii=False,default=json_default,allow_nan=False)
            outstream.write(encoded+'\n');outstream.flush()
            if logger:logger.write(json.dumps({'request':request,'response':response},ensure_ascii=False,default=json_default,allow_nan=False)+'\n');logger.flush()
    finally:
        if logger:logger.close()
