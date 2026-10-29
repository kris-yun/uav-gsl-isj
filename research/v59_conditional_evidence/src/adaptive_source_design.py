"""Exact finite-state counterexamples for source-targeted sequential design.

This is an analytic sensing experiment, NOT a gas plume simulator, COPEx
replication, or a native UAV performance result. All source/wind/noise states
and every legal policy branch are explicitly integrated. Independent mismatch
noise is resampled on every measurement conditional on the latent state.
"""
from __future__ import annotations

import itertools
import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path
from time import perf_counter
import numpy as np


def entropy(prob):
    p = np.asarray(prob, dtype=float)
    p = p[p > 0]
    return float(-np.dot(p, np.log(p)))


@dataclass
class Ledger:
    kernel_builds: int = 0
    latent_response_evaluations: int = 0
    kernel_cache_hits: int = 0
    information_node_evaluations: int = 0
    policy_leaf_evaluations: int = 0


class FiniteExperiment:
    """S: source bit; W: which gas location is diagnostic; N: irrelevant bit.

    C observes W through a binary symmetric channel. G0/G1 observes S through
    a binary symmetric channel if W matches its index, otherwise a fresh fair
    coin. U observes N. All methods see the same model and prior.
    """
    def __init__(self, wind_error=0., gas_error=0., cost=0.03,
                 include_irrelevant=False, max_kernel_builds=None):
        if not (0 <= wind_error <= .5 and 0 <= gas_error <= .5 and cost >= 0):
            raise ValueError('Channel errors must be in [0,.5]; cost nonnegative')
        self.atoms = np.asarray(list(itertools.product((0, 1), repeat=3)), int)
        self.prior = np.full(8, 1/8)
        self.wind_error, self.gas_error, self.cost = wind_error, gas_error, cost
        self.actions = ('C', 'G0', 'G1', 'H') + (('U',) if include_irrelevant else ())
        self.max_kernel_builds = max_kernel_builds
        self.cache, self.ledger = {}, Ledger()

    def kernel(self, action):
        if action not in self.actions:
            raise ValueError('Unknown action')
        if action in self.cache:
            self.ledger.kernel_cache_hits += 1
            return self.cache[action]
        if self.max_kernel_builds is not None and self.ledger.kernel_builds >= self.max_kernel_builds:
            raise RuntimeError('Global prediction budget exhausted before this kernel build')
        s, w, n = self.atoms.T
        if action == 'C':
            p1 = np.where(w == 1, 1-self.wind_error, self.wind_error)
        elif action.startswith('G'):
            match = w == int(action[1])
            p1 = np.where(match, np.where(s == 1, 1-self.gas_error, self.gas_error), .5)
        elif action == 'U':
            p1 = n.astype(float)
        else:  # H is a hold with a constant, uninformative observation.
            p1 = np.zeros(8)
        kernel = np.stack((1-p1, p1), axis=1)
        self.ledger.kernel_builds += 1
        self.ledger.latent_response_evaluations += len(self.atoms)
        self.cache[action] = kernel
        return kernel

    def h(self, belief, target='source'):
        if target == 'joint':
            return entropy(belief)
        return entropy(np.bincount(self.atoms[:,0], weights=belief, minlength=2))

    def step(self, belief, action, target='source'):
        self.ledger.information_node_evaluations += 1
        joint = belief[:,None]*self.kernel(action)
        py = joint.sum(axis=0)
        branches = [(y, float(py[y]), joint[:,y]/py[y]) for y in (0,1) if py[y] > 1e-15]
        gain = self.h(belief,target)-sum(p*self.h(b,target) for _,p,b in branches)
        return gain, branches

    def action_cost(self, action):
        return 0. if action == 'H' else self.cost


def best_adaptive(model, belief, horizon, target='source', selector=None):
    """Exact Bellman solution. selector is a declared proposal restriction."""
    if horizon == 0:
        return {'utility':0., 'information':0., 'expected_cost':0., 'action':None, 'branches':{}}
    actions = model.actions if selector is None else tuple(selector(belief,horizon))
    if not actions:
        raise ValueError('At least the safe hold action must remain')
    best = None
    for action in actions:
        gain, branches = model.step(belief,action,target)
        children = {str(y):best_adaptive(model,b,horizon-1,target,selector) for y,p,b in branches}
        information = gain+sum(p*children[str(y)]['information'] for y,p,b in branches)
        cost = model.action_cost(action)+sum(p*children[str(y)]['expected_cost'] for y,p,b in branches)
        node = {'utility':information-cost, 'information':information,
                'expected_cost':cost, 'action':action, 'branches':children}
        if best is None or node['utility'] > best['utility']+1e-12:
            best = node
    return best


def evaluate_policy(model, belief, tree, target='source'):
    if tree['action'] is None:
        model.ledger.policy_leaf_evaluations += 1
        return 0.,0.
    action = tree['action']
    gain, branches = model.step(belief,action,target)
    info,cost = gain,model.action_cost(action)
    for y,p,b in branches:
        ci,cc = evaluate_policy(model,b,tree['branches'][str(y)],target)
        info += p*ci
        cost += p*cc
    return info,cost


def fixed_tree(sequence):
    if not sequence:
        return {'action':None, 'branches':{}}
    child = fixed_tree(sequence[1:])
    return {'action':sequence[0], 'branches':{'0':child,'1':child}}


def best_fixed(model,horizon):
    best = None
    for sequence in itertools.product(model.actions,repeat=horizon):
        info,cost = evaluate_policy(model,model.prior,fixed_tree(sequence))
        row = {'sequence':list(sequence),'information':info,'expected_cost':cost,'utility':info-cost}
        if best is None or row['utility'] > best['utility']+1e-12:
            best = row
    return best


def greedy_policy(model,belief,horizon):
    if horizon == 0:
        return {'action':None,'branches':{}}
    action = max(model.actions, key=lambda a:model.step(belief,a)[0]-model.action_cost(a))
    _,branches = model.step(belief,action)
    return {'action':action,'branches':{str(y):greedy_policy(model,b,horizon-1) for y,p,b in branches}}


def summarize_tree(tree):
    return {'action':tree['action'],
            'branches':{k:summarize_tree(v) for k,v in tree.get('branches',{}).items()}}


def run_case(wind_error=0.,gas_error=0.,cost=.03):
    start = perf_counter()
    model = FiniteExperiment(wind_error,gas_error,cost)
    adaptive = best_adaptive(model,model.prior,2)
    adaptive_ledger = asdict(model.ledger)
    fixed = best_fixed(model,2)
    greedy = greedy_policy(model,model.prior,2)
    gi,gc = evaluate_policy(model,model.prior,greedy)
    one = best_adaptive(model,model.prior,1)
    # A conventional Bayesian policy tree and an EFE=-source-IG+cost objective
    # are the same optimization in this fully specified finite experiment.
    return {'wind_error':wind_error,'gas_error':gas_error,'cost_per_measurement':cost,
            'one_step':{k:one[k] for k in ('action','information','utility')},
            'adaptive':{**{k:adaptive[k] for k in ('information','expected_cost','utility')},
                        'policy':summarize_tree(adaptive)},
            'best_fixed':fixed,
            'receding_one_step':{'information':gi,'expected_cost':gc,'utility':gi-gc,
                                 'policy':summarize_tree(greedy)},
            'adaptive_ledger':adaptive_ledger,'all_comparisons_ledger':asdict(model.ledger),
            'wall_seconds_all_comparisons':perf_counter()-start}


def posterior_map_counterexample():
    model = FiniteExperiment(cost=0.)
    rows = []
    for wind_mode in (0,1):
        b = model.prior*(model.atoms[:,1] == wind_mode)*2
        best = best_adaptive(model,b,1)
        rows.append({'wind_known':wind_mode,'source_posterior':[.5,.5],
                     'best_action':best['action'],'source_information':best['information']})
    return rows


def wrong_target_counterexample():
    model = FiniteExperiment(wind_error=.1,gas_error=.05,cost=.03,include_irrelevant=True)
    source_policy = best_adaptive(model,model.prior,2,'source')
    joint_policy = best_adaptive(model,model.prior,2,'joint')
    source_i,source_c = evaluate_policy(model,model.prior,source_policy,'source')
    joint_i,joint_c = evaluate_policy(model,model.prior,joint_policy,'source')
    return {'source_target':{'policy':summarize_tree(source_policy),'source_information':source_i,'utility':source_i-source_c},
            'all_latent_target':{'policy':summarize_tree(joint_policy),'source_information':joint_i,
                                 'source_utility':joint_i-joint_c,'joint_information':joint_policy['information']}}


def budget_accounting_check():
    # A table for eight latent states costs eight latent evaluations, not one
    # source simulation. Cache reuse is exact only for these static channels.
    model = FiniteExperiment(max_kernel_builds=2)
    model.kernel('C'); model.kernel('G0'); model.kernel('C')
    blocked = False
    try:
        model.kernel('G1')
    except RuntimeError:
        blocked = True
    assert blocked and model.ledger.kernel_builds == 2
    return {**asdict(model.ledger),'third_unique_kernel_blocked':blocked,
            'scope':'API mechanism check only; no native runtime/energy saving claim'}


def main():
    destination = Path(__file__).resolve().parent/'results'
    destination.mkdir(exist_ok=True)
    exact = run_case()
    assert abs(exact['adaptive']['information']-math.log(2)) < 1e-12
    assert abs(exact['best_fixed']['information']-.5*math.log(2)) < 1e-12
    assert abs(exact['receding_one_step']['information']-.5*math.log(2)) < 1e-12
    assert exact['adaptive']['policy']['action'] == 'C'
    assert exact['one_step']['action'] in ('G0','G1')
    sweep = [run_case(we,ge) for we in (0.,.05,.1,.2,.3,.4,.5) for ge in (0.,.05,.15,.3,.5)]
    for row in sweep:
        assert row['adaptive']['utility']+1e-11 >= row['best_fixed']['utility']
        assert row['adaptive']['utility']+1e-11 >= row['receding_one_step']['utility']
    no_wind = next(r for r in sweep if r['wind_error'] == .5 and r['gas_error'] == 0)
    no_gas = next(r for r in sweep if r['wind_error'] == 0 and r['gas_error'] == .5)
    assert no_wind['adaptive']['policy']['action'] != 'C'
    assert no_gas['adaptive']['policy']['action'] == 'H'
    results = {'model_status':'EXACT_ANALYTIC_CHANNEL_NOT_NATIVE_GSL',
               'units':'natural logarithm (nat); costs are declared information-equivalent penalties',
               'assumptions':['S,W,N are independent uniform bits before measurements',
                              'all two-step actions are safe and reachable in this toy',
                              'mismatch noises independent across repeated measurements',
                              'no unknown release amplitude or sensor memory in this toy'],
               'perfect_case':exact,'noise_sweep':sweep,
               'same_source_map_different_action':posterior_map_counterexample(),
               'wrong_target':wrong_target_counterexample(),
               'budget_gate':budget_accounting_check()}
    (destination/'adaptive_source_design.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps({'perfect_case':exact,'no_wind_information':no_wind,
                      'no_gas_information':no_gas,'same_source_map':results['same_source_map_different_action'],
                      'wrong_target':results['wrong_target'],'sweep_cases':len(sweep)},indent=2))


if __name__ == '__main__':
    main()
