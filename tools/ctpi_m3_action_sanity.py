#!/usr/bin/env python3
"""Truth-blind sanity Gate for CTPI M3 action decisions."""
from __future__ import annotations
import argparse, csv, json, math
from pathlib import Path

TOL=1e-12

def read_rows(path: Path):
    with path.open(newline='',encoding='utf-8') as f:
        rows=list(csv.DictReader(f))
    if not rows: raise RuntimeError('CTPI_M3_AUDIT_EMPTY')
    return rows

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--audit',type=Path,required=True); ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args(); rows=read_rows(args.audit)
    modes={r['mode'] for r in rows}
    if len(modes)!=1 or next(iter(modes)) not in {'ctpi_f10','ctpi_f11'}: raise RuntimeError(f'CTPI_M3_MODE:{modes}')
    changed=0; native_comparable=0; strictly_better=0; goals=set(); min_candidates=10**9
    for i,r in enumerate(rows,1):
        candidates=int(r['candidate_count']); min_candidates=min(min_candidates,candidates)
        if candidates < 2: raise RuntimeError(f'CTPI_M3_CANDIDATE_COUNT:{i}:{candidates}')
        ss=float(r['decision_sensor_state_ppm']); si=float(r['selected_info_nats'])
        if not (math.isfinite(ss) and ss>=0 and math.isfinite(si) and si>=-TOL): raise RuntimeError(f'CTPI_M3_NUMERIC:{i}')
        ni=float(r['native_info_nats'])
        if math.isfinite(ni):
            native_comparable+=1
            if si+TOL < ni: raise RuntimeError(f'CTPI_M3_SELECTED_INFO_BELOW_NATIVE:{i}:{si}:{ni}')
            strictly_better += int(si>ni+TOL)
        changed += int(r['action_changed'])
        goals.add((round(float(r['selected_goal_x']),9),round(float(r['selected_goal_y']),9)))
    checks={
      'decision_count_ge_2':len(rows)>=2,
      'candidate_count_ge_2':min_candidates>=2,
      'native_comparable_exists':native_comparable>=1,
      'selected_never_below_native_info':True,
      'action_changed_at_least_once':changed>=1,
      'selected_goal_diversity_ge_2':len(goals)>=2 if len(rows)>=2 else True,
    }
    passed=all(checks.values())
    report={'contract':'CTPI_M3_ACTION_SANITY_V0','mode':next(iter(modes)),'decisions':len(rows),'changed_decisions':changed,'native_comparable':native_comparable,'strictly_higher_info_than_native':strictly_better,'unique_selected_goals':len(goals),'checks':checks,'pass':passed,'verdict':'CTPI_M3_ACTION_SANITY=PASS' if passed else 'CTPI_M3_ACTION_SANITY=FAIL'}
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(report['verdict']); print(json.dumps(report,sort_keys=True)); return 0 if passed else 2
if __name__=='__main__': raise SystemExit(main())
