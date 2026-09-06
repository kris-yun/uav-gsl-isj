from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path

def run(cmd):
    p=subprocess.run(cmd,text=True,capture_output=True); return {"cmd":" ".join(map(str,cmd)),"returncode":p.returncode,"stdout":p.stdout[-4000:],"stderr":p.stderr[-4000:]}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--manifest",type=Path,required=True); ap.add_argument("--out-dir",type=Path,required=True); ap.add_argument("--m3-panel",type=Path); args=ap.parse_args(); root=Path(__file__).resolve().parent; args.out_dir.mkdir(parents=True,exist_ok=True)
    jobs=[]
    jobs.append(run([sys.executable,str(root/'m1_picr/offline.py'),'--manifest',str(args.manifest),'--output',str(args.out_dir/'M1_GATE.json')]))
    jobs.append(run([sys.executable,str(root/'m2_cpo/offline.py'),'--manifest',str(args.manifest),'--output',str(args.out_dir/'M2_GATE.json')]))
    panel=args.m3_panel or (args.out_dir/'MISSING_COUNTERFACTUAL_PANEL.json')
    jobs.append(run([sys.executable,str(root/'m3_phs/offline_panel.py'),'--panel',str(panel),'--output',str(args.out_dir/'M3_GATE.json')]))
    states=[]
    for name in ('M1','M2','M3'):
        p=args.out_dir/f'{name}_GATE.json'; states.append(json.loads(p.read_text()) if p.is_file() else {"verdict":f"{name}_MISSING"})
    report={"contract":"CSTAR_OFFLINE_ORCHESTRATOR_V1","jobs":jobs,"modules":states,"formal_closed_loop_authorized":all(s.get('pass') is True for s in states)}
    (args.out_dir/'CSTAR_OFFLINE_SUMMARY.json').write_text(json.dumps(report,indent=2)+"\n"); print('CSTAR_OFFLINE_FORMAL_CLOSED_LOOP_AUTHORIZED='+str(report['formal_closed_loop_authorized']).upper()); return 0 if report['formal_closed_loop_authorized'] else 2
if __name__=='__main__': raise SystemExit(main())
