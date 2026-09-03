#!/usr/bin/env python3
"""Pre-registered small-N screening Gate before expensive cross-House closed loop."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--performance',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args()
    p=json.loads(a.performance.read_text()); c=p['comparisons']
    def task_win(label):
        x=c[label]; auc=x['error_auc_m_s']; t2=x['time_to_2m_s']; fe=x['final_error_m']
        return (auc['wins']>=2 or t2['wins']>=2) and fe['losses']<3
    checks={'M1_screen':task_win('M1_F00_vs_A0'),'M3_screen':task_win('M3_F10_vs_F00'),'M2_downstream_screen':task_win('M2_DOWNSTREAM_F11_vs_F10')}
    passed=all(checks.values())
    out={'contract':'CTPI_FASTTRACK_H01_3SEED_SCREEN_V0','checks':checks,'pass':passed,'formal_crosshouse_authorized':passed,'verdict':'CTPI_FASTTRACK_H01_3SEED_SCREEN=PASS' if passed else 'CTPI_FASTTRACK_H01_3SEED_SCREEN=NO_GO'}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(out['verdict']); return 0 if passed else 2
if __name__=='__main__':raise SystemExit(main())
