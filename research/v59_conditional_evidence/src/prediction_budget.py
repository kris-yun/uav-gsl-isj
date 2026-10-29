"""An honest global prediction ledger for a native adapter.

The charge unit is one declared high-fidelity latent trajectory evaluation,
not one Python callback and not one policy-tree root. Batched calls declare
their full latent trajectory count. Sensor-history and model-version changes
invalidate caches. This module supplies accounting, not a cheap gas simulator.
"""
from __future__ import annotations
from contextlib import contextmanager
from dataclasses import dataclass, asdict, field
from hashlib import sha256
import json
from time import perf_counter
from typing import Callable, Any


class BudgetExhausted(RuntimeError):
    pass


@dataclass(frozen=True)
class PredictionKey:
    model_version: str
    geometry_digest: str
    history_digest: str
    latent_bank_digest: str
    action_digest: str
    sensor_state_digest: str
    horizon: int
    fidelity: str = 'high'

    def __post_init__(self):
        if any(not x for x in (self.model_version,self.geometry_digest,self.history_digest,
                               self.latent_bank_digest,self.action_digest,self.sensor_state_digest)):
            raise ValueError('Cache identity fields must be non-empty and traceable')
        if self.horizon < 1 or self.fidelity not in ('high','low'):
            raise ValueError('Invalid horizon/fidelity')


@dataclass
class Ledger:
    high_limit: int
    high_charged: int = 0
    low_charged: int = 0
    forward_callbacks: int = 0
    cache_hits: int = 0
    failed_callbacks: int = 0
    blocked_requests: int = 0
    stage_seconds: dict = field(default_factory=dict)
    events: list = field(default_factory=list)


class PredictionBudget:
    def __init__(self, high_limit: int):
        if not isinstance(high_limit,int) or high_limit < 0:
            raise ValueError('High-fidelity limit must be a nonnegative integer')
        self.ledger = Ledger(high_limit)
        self._cache = {}

    @contextmanager
    def stage(self, name):
        """Instrument features, cached-field builds, safety, inference, scoring."""
        t0=perf_counter()
        try:
            yield
        finally:
            self.ledger.stage_seconds[name] = self.ledger.stage_seconds.get(name,0.)+perf_counter()-t0

    def predict(self, key: PredictionKey, latent_trajectories: int,
                callback: Callable[[],Any], stage: str):
        if not isinstance(latent_trajectories,int) or latent_trajectories < 1:
            raise ValueError('Declare the full batch of latent trajectories')
        if key in self._cache:
            self.ledger.cache_hits += 1
            self.ledger.events.append({'stage':stage,'status':'cache_hit','key':asdict(key),'charge':0})
            return self._cache[key]
        if key.fidelity == 'high' and self.ledger.high_charged+latent_trajectories > self.ledger.high_limit:
            self.ledger.blocked_requests += 1
            self.ledger.events.append({'stage':stage,'status':'blocked','key':asdict(key),
                                       'requested_charge':latent_trajectories})
            raise BudgetExhausted('Global high-fidelity budget would be exceeded')
        if key.fidelity == 'high':
            self.ledger.high_charged += latent_trajectories
        else:
            self.ledger.low_charged += latent_trajectories
        self.ledger.forward_callbacks += 1
        event={'stage':stage,'status':'started','key':asdict(key),'charge':latent_trajectories}
        self.ledger.events.append(event)
        try:
            with self.stage(stage):
                result=callback()
        except Exception:
            self.ledger.failed_callbacks += 1
            event['status']='failed_charged'
            raise
        self._cache[key]=result
        event['status']='completed'
        return result

    def snapshot(self):
        return asdict(self.ledger)


def content_digest(value):
    return sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def verify_accounting():
    """A meaningful regression: count batches, invalidate history, block early."""
    calls=[]
    budget=PredictionBudget(8)
    common=dict(model_version='analytic-test-v1',geometry_digest='fixed-world',
                history_digest='causal-prefix-1',latent_bank_digest='bank-4',
                sensor_state_digest='sensor-state-1',horizon=2)
    a=PredictionKey(**common,action_digest='root-C-child-G0')
    b=PredictionKey(**common,action_digest='root-C-child-G1')
    def execute(label):
        calls.append(label)
        return {'label':label}
    with budget.stage('feature_generation'):
        content_digest(common)
    budget.predict(a,4,lambda:execute('A'),'candidate_predict')
    budget.predict(a,4,lambda:execute('A-again'),'candidate_predict')
    budget.predict(b,4,lambda:execute('B'),'branch_predict')
    changed=PredictionKey(**{**common,'history_digest':'causal-prefix-2'},action_digest='root-C-child-G0')
    blocked=False
    try:
        budget.predict(changed,4,lambda:execute('stale-cache-must-not-run'),'candidate_predict')
    except BudgetExhausted:
        blocked=True
    assert calls == ['A','B'] and blocked
    assert budget.ledger.high_charged == 8 and budget.ledger.cache_hits == 1
    return {'status':'PASS','scope':'accounting interface, not native cost saving',
            'actual_callbacks':calls,'ledger':budget.snapshot()}


if __name__ == '__main__':
    from pathlib import Path
    p=Path(__file__).resolve().parent/'results'
    p.mkdir(exist_ok=True)
    result=verify_accounting()
    (p/'prediction_budget.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'status':result['status'],'actual_callbacks':result['actual_callbacks'],
                      'high_charged':result['ledger']['high_charged'],
                      'cache_hits':result['ledger']['cache_hits'],
                      'blocked_requests':result['ledger']['blocked_requests']},indent=2))
