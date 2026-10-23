"""Persistent V2 active session. Only the deployable student is accepted.

Codebooks use sampled gas-event words; fallback compares the FULL gas+wind
observation EIG. A test result schedules attention, never a new Bayes factor.
"""
from dataclasses import asdict
from pathlib import Path
import json,time
import numpy as np
from ..types import Action,Mechanism,observation_from_dict
from ..m2_replay import EvidenceLedger,ReplayEngine
from ..m3_codebook import JointCodebookBuilder,CorruptionChannel
from ..m3_planner import RobustCounterEvidencePlanner
from ..posterior import source_map
from ..io import json_default


class ActiveSessionV2:
    def __init__(self,model,sources,mechanisms,*,seed=0,draws=256,eig_draws=16,wall_seconds=60.,
                 variant='Bprime',guard=None,max_flips=1,m2_variant='Bprime'):
        if model.format_version!='gsl_neural_joint_v2':raise ValueError('BLOCKED_ONLINE_TEACHER')
        if model.config.time_semantics!='seconds' or model.config.scope=='NUMERICAL_ONLY':raise ValueError('BLOCKED_NONPHYSICAL_CLOCK_OR_WIND')
        if model.training_receipt.get('normalized_density_anchor') is False:raise ValueError('BLOCKED_NO_GENERATIVE_ANCHOR')
        from ..pipeline import inference_version
        self.model=model;self.sources=np.asarray(sources,float);self.mechanisms=list(mechanisms)
        self.version=inference_version(model,mechanisms,sources);self.ledger=EvidenceLedger()
        self.engine=ReplayEngine(model,sources,mechanisms,model_version=self.version)
        threshold=.5 if model.config.gas_model=='binary' else model.config.gas_lod
        self.builder=JointCodebookBuilder(model,threshold=threshold,model_version=self.version)
        self.planner=RobustCounterEvidencePlanner(len(sources),CorruptionChannel(max_flips=max_flips),seed=seed)
        self.rng=np.random.default_rng(seed+1);self.eig_rng=np.random.default_rng(seed+2)
        self.draws=int(draws);self.eig_draws=int(eig_draws);self.wall_seconds=float(wall_seconds)
        self.pending=None;self.round=0;self.variant=variant;self.guard=guard;self.m2_variant=m2_variant
        self.adequacy={'status':'not_calibrated','counterevidence_allowed':True,'coverage_claim':'model-conditional only; physical error unbounded'}

    def request(self,obj):
        allowed={'op','action_blocks','navigation_qualified','observations','costs'}
        if set(obj)-allowed:raise ValueError('Unknown or privileged request fields: '+str(set(obj)-allowed))
        if obj.get('op')=='plan':
            if self.pending is not None:raise ValueError('Complete the precommitted pending block')
            if obj.get('navigation_qualified') is not True:raise ValueError('Native collision/timing qualification required')
            blocks=[[Action(**a) for a in b] for b in obj['action_blocks']]
            now=self.ledger.history[-1].action.time if len(self.ledger) else -float('inf')
            for b in blocks:
                if not b:raise ValueError('Empty block')
                times=[now]+[a.time for a in b]
                if any(y<=x for x,y in zip(times,times[1:])):raise ValueError('Future action times must increase')
            result=self.engine.infer(self.ledger.history,self.m2_variant);alpha=self.planner.risk.next_alpha();start=time.perf_counter()
            books=self.builder.build(self.ledger.history,blocks,self.sources,self.mechanisms,self.draws,self.rng,
                     delta=.01/((self.round+1)*(self.round+2)),costs=obj.get('costs'),wall_seconds=self.wall_seconds)
            variant=self.variant if self.adequacy['counterevidence_allowed'] else 'Aprime'
            self.pending=self.planner.plan(books,result.source_posterior,result.conditional_mechanism_posterior,variant)
            full_eig=[]
            if self.pending.test is None and variant in ('Aprime','Bprime'):
                from ..m3_planner.joint_eig import full_observation_eig
                for b in books:
                    value=full_observation_eig(self.model,self.ledger.history,b.actions,self.sources,self.mechanisms,
                          result.source_posterior,result.conditional_mechanism_posterior,draws=self.eig_draws,rng=self.eig_rng)
                    full_eig.append(value)
                best=int(np.argmax([v['eig']/b.cost for v,b in zip(full_eig,books)]))
                # No risk was reserved. This replaces only the untested fallback
                # action, before any realized response can be read.
                self.pending.actions=books[best].actions;self.pending.codebook=books[best];self.pending.action_index=best
                self.pending.reason='full_gas_wind_joint_eig_fallback';self.pending.score=full_eig[best]['eig']/books[best].cost
            from ..m3_planner.diagnostics import diagnose_counterevidence_layers
            diagnostics=diagnose_counterevidence_layers(self.pending.codebook,self.pending.null_source,self.pending.challenge_indices,
                              channel=self.planner.channel,alpha=alpha)
            return {'op':'plan','plan_id':self.pending.plan_id,'actions':[asdict(a) for a in self.pending.actions],
                 'reason':self.pending.reason,'counterevidence_test_reserved':self.pending.test is not None,
                 'source_map':source_map(self.sources,result.source_posterior),'model_version':self.version,
                 'risk_spent':self.planner.risk.spent,'adequacy':self.adequacy,'power_diagnostics':diagnostics,
                 'full_observation_eig':full_eig,'wall_seconds':time.perf_counter()-start,
                 'risk_scope':'learned model + declared channel + MC bound; not a physical false-rejection certificate'}
        if obj.get('op')=='observe':
            if self.pending is None:raise ValueError('No committed action block')
            observations=[observation_from_dict(o) for o in obj['observations']]
            if any(not o.gas_available for o in observations):raise ValueError('BLOCKED_ONLINE_GAS_ERASURE_READOUT_NOT_QUALIFIED')
            probe=EvidenceLedger(self.ledger.history);probe.extend(observations)
            if self.guard is not None:
                self.adequacy=self.guard.assess(self.model,self.ledger.history,observations,self.sources,self.mechanisms,self.pending.null_source)
            outcome=self.planner.observe(self.pending,observations,model_version=self.version)
            if not self.adequacy['counterevidence_allowed']:
                outcome['unqualified_model_test_rejected']=outcome['rejected']
                outcome.update(rejected=False,trigger_replay=False,counterevidence_status='abstained_model_adequacy')
                self.planner.recovery.active=set(range(len(self.sources)))
                self.planner.recovery.recently_recovered=set(range(len(self.sources)))
                self.planner.recovery.records.append({'event':'restore_after_unexplained_block','model_version':self.version})
                outcome['recovery_list']=list(range(len(self.sources)))
            self.ledger=probe;self.pending=None;self.round+=1
            result=self.engine.infer(self.ledger.history,self.m2_variant)
            replay_discrepancies=[abs(r['full_recompute_error']) for r in result.records
                                  if r.get('full_recompute_error') is not None]
            return {'op':'update','observations':len(self.ledger),'test':outcome,'adequacy':self.adequacy,
                   'model_version':self.version,'source_map':source_map(self.sources,result.source_posterior),
                   'source_log_posterior':result.source_log_posterior,'joint_posterior':result.joint_posterior,
                   'conditional_mechanism_posterior':result.conditional_mechanism_posterior,
                   'maximum_suffix_replay_discrepancy':max(replay_discrepancies,default=None),
                   'diagnosis_added_as_evidence':False}
        raise ValueError('op must be plan or observe')


def run_jsonl_v2(model_path,setup_path,instream,outstream,log_path):
    from ..v2_pipeline import load_online_model
    from ..m2_diagnosis.adequacy import PredictiveAdequacyGuard
    obj=json.loads(Path(setup_path).read_text());allowed={'candidates','mechanisms','seed','draws','eig_draws','wall_seconds','variant','guard_path','max_flips','require_physical','m2_variant'}
    if set(obj)-allowed:raise ValueError('Unknown or privileged setup fields')
    model=load_online_model(model_path,require_physical=obj.get('require_physical',False))
    kwargs={k:obj[k] for k in ('seed','draws','eig_draws','wall_seconds','variant','max_flips','m2_variant') if k in obj}
    guard=PredictiveAdequacyGuard.load(obj['guard_path']) if obj.get('guard_path') else None
    session=ActiveSessionV2(model,obj['candidates'],[Mechanism(**m) for m in obj['mechanisms']],guard=guard,**kwargs)
    path=Path(log_path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a',encoding='utf-8') as log:
        for line in instream:
            if not line.strip():continue
            req=json.loads(line);response=session.request(req)
            encoded=json.dumps(response,ensure_ascii=False,default=json_default,allow_nan=False)
            log.write(json.dumps({'request':req,'response':response},ensure_ascii=False,default=json_default,allow_nan=False)+'\n');log.flush()
            outstream.write(encoded+'\n');outstream.flush()
