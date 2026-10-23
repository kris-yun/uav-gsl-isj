"""Model-adequacy flag, separate from source/mechanism likelihood factors.

It can distinguish a current MAP conflict from a block unexplained by every
declared candidate/mechanism. It cannot name an unmodeled physical cause.
Its empirical tail score has no domain-shift or repeated-look coverage claim.
"""
from dataclasses import dataclass,asdict
from pathlib import Path
import json
import numpy as np


def explanation_scores(model,history,future,sources,mechanisms):
    if not future:raise ValueError('Need a nonempty precommitted observation block')
    observed=sum(int(o.gas_available)+sum(o.wind_available) for o in future)
    if observed==0:raise ValueError('BLOCKED_NO_OBSERVED_CHANNELS')
    values=np.array([[(model.log_prob(list(history)+list(future),s,m)-model.log_prob(history,s,m))
                      for m in mechanisms] for s in sources])
    if not np.isfinite(values).all():raise ValueError('Nonfinite explanation density')
    return -values/observed


@dataclass
class PredictiveAdequacyGuard:
    calibration_scores: list
    model_version: str
    tail_level: float = .05
    block_length: int = 3

    def __post_init__(self):
        x=np.asarray(self.calibration_scores,float)
        if x.ndim!=1 or len(x)<4 or not np.isfinite(x).all():raise ValueError('At least 4 finite independent-development calibration scores required')
        if not 0<self.tail_level<1:raise ValueError('Invalid diagnostic tail level')

    def assess(self,model,history,future,sources,mechanisms,current_map):
        if model.version!=self.model_version:raise ValueError('Stale adequacy calibration model')
        if len(future)!=self.block_length:raise ValueError('Adequacy block length differs from calibration')
        scores=explanation_scores(model,history,future,sources,mechanisms)
        cal=np.asarray(self.calibration_scores)
        tail=lambda value:float((1+np.sum(cal>=value))/(len(cal)+1))
        best=float(scores.min());mapbest=float(scores[int(current_map)].min());pall=tail(best);pmap=tail(mapbest)
        unknown=pall<=self.tail_level
        label='none_of_declared_sources_mechanisms_explains_block' if unknown else ('current_map_conflict' if pmap<=self.tail_level else 'within_development_reference')
        return {'status':label,'best_explanation_nll':best,'map_explanation_nll':mapbest,
             'empirical_tail_all':pall,'empirical_tail_map':pmap,'counterevidence_allowed':not unknown,
             'posterior_qualified':not unknown,'not_a_likelihood_factor':True,
             'cause_not_identified':unknown,'coverage_claim':'none under shifted/adaptive data; diagnostic only'}

    def save(self,path):
        Path(path).parent.mkdir(parents=True,exist_ok=True);Path(path).write_text(json.dumps(asdict(self),indent=2))

    @classmethod
    def load(cls,path):return cls(**json.loads(Path(path).read_text()))


def fit_adequacy_guard(model,episodes,sources,mechanisms,block_length=3,tail_level=.05):
    scores=[];groups=set()
    for ep in episodes:
        if ep['metadata']['split']!='development':raise ValueError('Adequacy calibration uses development only')
        if ep['metadata']['lineage_group'] in groups:continue
        groups.add(ep['metadata']['lineage_group']);h=ep['observations'];cut=len(h)-block_length
        if cut<1:raise ValueError('Short calibration history')
        scores.append(float(explanation_scores(model,h[:cut],h[cut:],sources,mechanisms).min()))
    return PredictiveAdequacyGuard(scores,model.version,tail_level,block_length)
