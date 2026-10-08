"""Pure decision arithmetic for a future scored table; never launches experiments.

Synthetic examples in the independent static verifier are NOT M0 observations.
Inputs: eight rows per pair, source S0/S1 and realization 1..4. Each row contains
D_F_first/second, D_Y_first/second and brier[family][oracle/first/second].
"""
import json
import math
from pathlib import Path

CONFIG=json.loads(Path(__file__).with_name('M0_GATE_CONTRACT.json').read_text(encoding='utf-8'))

def decide(prerequisites, qualified_runs, pair_rows):
    failed=[k for k in CONFIG['prerequisites'] if prerequisites.get(k) is not True]
    if qualified_runs!=CONFIG['required_qualified_runs'] or failed:
        return {'verdict':'M0_PREREQUISITE_HOLD','failed_or_unknown':failed,'qualified_runs':qualified_runs}
    expected={(s,r) for s in CONFIG['sources'] for r in CONFIG['realizations']}
    if set(pair_rows)!=set(CONFIG['pairs']):
        return {'verdict':'M0_PREREQUISITE_HOLD','reason':'missing or additional contrast'}
    for pair,rows in pair_rows.items():
        if len(rows)!=8 or {(d.get('source'),d.get('realization')) for d in rows}!=expected:
            return {'verdict':'M0_PREREQUISITE_HOLD','reason':'pair row coverage','pair':pair}
        for d in rows:
            try:
                forwards=[d[f'D_{metric}_{arm}'] for metric in ['F','Y'] for arm in ['first','second']]
                probs=[d['brier'][f][a] for f in CONFIG['families'] for a in ['oracle','first','second']]
                if not all(math.isfinite(x) and x>=0 for x in forwards+probs) or not all(x<=1 for x in probs):
                    raise ValueError('score domain')
            except (KeyError,ValueError,TypeError):
                return {'verdict':'M0_PREREQUISITE_HOLD','reason':'missing/nonfinite/invalid scores','pair':pair}
    margins=CONFIG['material_margins'];n=CONFIG['replication']['seeds_required_per_source']
    reports={};complete=[];partial=[]
    for pair,rows in pair_rows.items():
        reports[pair]={}
        for sign in CONFIG['replication']['allowed_pair_directions']:
            counts={};partial_counts={}
            for source in CONFIG['sources']:
                passing=[];single={f:[] for f in CONFIG['families']}
                for d in rows:
                    if d['source']!=source:continue
                    forward=(sign*(d['D_F_first']-d['D_F_second'])>=margins['absolute_D_F_pair_difference_min'] and
                             sign*(d['D_Y_first']-d['D_Y_second'])>=margins['absolute_D_Y_pair_difference_min'])
                    harm_arm='first' if sign==1 else 'second'
                    posterior=[]
                    for f in CONFIG['families']:
                        b=d['brier'][f]
                        material=sign*(b['first']-b['second'])>=margins['absolute_Brier_pair_difference_min_each_family']
                        if material:single[f].append(d['realization'])
                        posterior.append(material and b[harm_arm]-b['oracle']>=margins['worse_arm_Brier_damage_vs_oracle_min_each_family'])
                    if forward and all(posterior):passing.append(d['realization'])
                counts[source]=sorted(passing);partial_counts[source]=single
                for f,ids in single.items():
                    if len(ids)>=n:partial.append({'pair':pair,'sign':sign,'source':source,'family':f,'seed_ids':sorted(ids)})
            reports[pair][str(sign)]={'intersection_seed_ids':counts,'material_source_seed_ids':partial_counts}
            if all(len(ids)>=n for ids in counts.values()):complete.append({'pair':pair,'sign':sign})
    if complete:
        return {'verdict':'M0_PASS','tier':'TWO_PAIR' if len({x['pair'] for x in complete})==2 else 'ONE_PAIR_REPLICATED','surviving':complete,'pair_reports':reports,'meaning':'mechanism screen only; FSR review required'}
    if partial:return {'verdict':'M0_PARTIAL_HOLD','partial':partial,'pair_reports':reports}
    return {'verdict':'M0_STOP','pair_reports':reports,'meaning':'null for the frozen qualified mechanism box; stop this route'}
