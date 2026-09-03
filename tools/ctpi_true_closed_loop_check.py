#!/usr/bin/env python3
"""Fail-closed causal-chain checker for CTPI smoke/screen/formal runs."""
from __future__ import annotations
import argparse,csv,json,math
from pathlib import Path

def rows(path):
    if not path.is_file(): raise RuntimeError(f'MISSING:{path}')
    with path.open(newline='',encoding='utf-8') as f: return list(csv.DictReader(f))

def goals(nav):
    return [(round(float(r['goal_x']),6),round(float(r['goal_y']),6)) for r in nav if r.get('event')=='SENT']

def movement(pose):
    pts=[]
    for r in pose:
        try: pts.append((float(r.get('x',r.get('pose_x'))),float(r.get('y',r.get('pose_y')))))
        except Exception: continue
    if len(pts)<2:return 0.0
    return max(math.hypot(x-pts[0][0],y-pts[0][1]) for x,y in pts)

def changed_numeric(trace, keys):
    vals=[]
    for r in trace:
        for k in keys:
            if k in r and r[k] not in ('','NA','nan'):
                try: vals.append(float(r[k])); break
                except ValueError: pass
    return len(vals)>=2 and max(vals)-min(vals)>1e-12

def check_run(root:Path, arm:str):
    nav=rows(root/'navigation_trace.csv'); sensor=rows(root/'sensor_trace.csv'); pose=rows(root/'sim_pose_trace.csv'); post=rows(root/'source_estimate_trace.csv')
    sent=goals(nav)
    checks={
      'navigation_sent_ge_1':len(sent)>=1,
      'motion_feedback':movement(pose)>0.05,
      'fresh_sensor_stream':len(sensor)>=2,
      'posterior_trace_ge_2':len(post)>=2,
      'posterior_changes':changed_numeric(post,['posterior_entropy','posterior_variance','estimate_x','estimate_y']),
    }
    if arm in {'F10','F11'}:
        audit=rows(root/'ctpi_audit'/'ctpi_m3_action_audit.csv')
        checks['m3_decisions_exist']=len(audit)>=1
        checks['posterior_to_action']=len(audit)>=1 and len(sent)>=1
        if audit and sent:
            chosen=[(round(float(r['selected_goal_x']),6),round(float(r['selected_goal_y']),6)) for r in audit]
            checks['m3_goal_reaches_navigation_trace']=any(g in sent for g in chosen)
    return checks,sent

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--run-root',type=Path,required=True); ap.add_argument('--house',default='H01'); ap.add_argument('--seed',type=int,default=0); ap.add_argument('--output',type=Path,required=True); args=ap.parse_args()
    results={}; sequences={}
    for arm in ('F00','F10','F11'):
        root=args.run_root/f'{args.house}_seed{args.seed}_{arm}'
        results[arm],sequences[arm]=check_run(root,arm)
    results['cross_arm']={
      'F10_trajectory_differs_from_F00':sequences['F10']!=sequences['F00'],
      'F11_trajectory_differs_from_F00':sequences['F11']!=sequences['F00'],
      'F10_F11_both_have_actions':bool(sequences['F10'] and sequences['F11']),
    }
    passed=all(all(v.values()) for v in results.values())
    report={'contract':'CTPI_TRUE_CLOSED_LOOP_CAUSAL_CHAIN_V0','house':args.house,'seed':args.seed,'checks':results,'pass':passed,'verdict':'TRUE_CLOSED_LOOP_CAUSAL_CHAIN=PASS' if passed else 'TRUE_CLOSED_LOOP_CAUSAL_CHAIN=FAIL'}
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(report['verdict']); return 0 if passed else 2
if __name__=='__main__': raise SystemExit(main())
