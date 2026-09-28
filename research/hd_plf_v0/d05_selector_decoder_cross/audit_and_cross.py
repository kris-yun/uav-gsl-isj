"""Read-only D0.5 aggregation and selector/decoder cross-evaluation.

No simulation, fitting, action reselection, or scientific relabelling.
For cross evaluation, first export the archived GOAL_COUNTERFACTUALS.csv to a
normalized CSV with these explicit columns (do not regenerate observations):
environment,source_index,target_index,goal_cell,decoder,expected_rank
`decoder` must be exactly LF-u or LF-rawu. `expected_rank` must be the original
pre-frozen tie-aware expected rank, not strict rank or an invented posterior.
"""
from __future__ import annotations
import argparse, csv, json, math
from collections import Counter, defaultdict
from pathlib import Path

ARMS = ('LF-u', 'LF-rawu')

def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError('No rows to export')
    with path.open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

def summarize(d: dict) -> list[dict]:
    rows=[]
    for env in sorted({e['environment'] for e in d['episodes']}):
        eps=[e for e in d['episodes'] if e['environment']==env]
        for arm in ARMS:
            delta=[float(e[arm]['selected_minus_median_rank_gain']) for e in eps]
            if not all(math.isfinite(v) for v in delta):
                raise ValueError('Non-finite saved difference')
            rows.append(dict(environment=env,arm=arm,episodes=len(eps),
                above_median=sum(v>0 for v in delta),equal_to_median=sum(v==0 for v in delta),
                below_median=sum(v<0 for v in delta),mean_selected_minus_median_gain=sum(delta)/len(delta),
                unique_anchor_cells=len({e['anchor_cell'] for e in eps}),
                unique_selected_cells=len({e[arm]['selected_cell'] for e in eps})))
    return rows

def cross(d: dict, observations: list[dict]) -> list[dict]:
    tables=defaultdict(lambda:defaultdict(dict))
    for row in observations:
        key=tuple(int(row[k]) for k in ('environment','source_index','target_index'))
        arm=row['decoder']; goal=int(row['goal_cell']); rank=float(row['expected_rank'])
        if arm not in ARMS or not math.isfinite(rank) or not 1<=rank<=6:
            raise ValueError('Invalid decoder/rank; six-source archived experiment required')
        if goal in tables[key][arm]:
            raise ValueError(f'Duplicate row: {key,arm,goal}')
        tables[key][arm][goal]=rank
    result=[]; expected_keys=set()
    for ep in d['episodes']:
        key=tuple(ep[k] for k in ('environment','source_index','target_index'))
        expected_keys.add(key)
        t=tables.get(key)
        if t is None or set(t)!=set(ARMS):
            raise ValueError(f'Missing decoder data: {key}')
        goals=set(t[ARMS[0]])
        if goals!=set(t[ARMS[1]]) or len(goals)!=int(ep['feasible_goals']):
            raise ValueError(f'Feasible action sets do not match: {key}')
        selected={a:int(ep[a]['selected_cell']) for a in ARMS}
        if not set(selected.values()).issubset(goals):
            raise ValueError('Archived selected action not present')
        for decoder in ARMS:
            ranks=t[decoder]
            oracle=min(ranks.values())
            policies={a:ranks[g] for a,g in selected.items()}
            policies['uniform_actions_exact_mean']=sum(ranks.values())/len(ranks)
            policies['truth_oracle_diagnostic_only']=oracle
            for policy,rank in policies.items():
                result.append(dict(environment=key[0],source_index=key[1],target_index=key[2],
                    decoder=decoder,selector=policy,expected_final_rank=rank,
                    normalized_rank_loss=(rank-1)/5,
                    regret_to_oracle_rank=rank-oracle,
                    selected_goal=selected.get(policy,''),action_count=len(goals)))
    if set(tables)!=expected_keys:
        raise ValueError('Unexpected episodes: no silent exclusions allowed')
    return result

def group_cross(rows: list[dict]) -> list[dict]:
    groups=defaultdict(list)
    for r in rows:
        groups[(r['environment'],r['decoder'],r['selector'])].append(r)
    out=[]
    for key, rs in sorted(groups.items()):
        per_source=defaultdict(list)
        for r in rs: per_source[r['source_index']].append(r)
        def balanced(field):
            return sum(sum(r[field] for r in v)/len(v) for v in per_source.values())/len(per_source)
        out.append(dict(environment=key[0],decoder=key[1],selector=key[2],sources=len(per_source),
             episodes=len(rs),source_balanced_expected_final_rank=balanced('expected_final_rank'),
             source_balanced_regret_to_oracle=balanced('regret_to_oracle_rank')))
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--result',type=Path,required=True)
    p.add_argument('--normalized-goals',type=Path)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args(); a.out.mkdir(parents=True,exist_ok=True)
    d=json.loads(a.result.read_text(encoding='utf-8'))
    write_csv(a.out/'saved_result_summary.csv',summarize(d))
    if a.normalized_goals:
        with a.normalized_goals.open(encoding='utf-8-sig',newline='') as f: obs=list(csv.DictReader(f))
        rows=cross(d,obs)
        write_csv(a.out/'crossed_episode_results.csv',rows)
        write_csv(a.out/'crossed_source_balanced_summary.csv',group_cross(rows))
