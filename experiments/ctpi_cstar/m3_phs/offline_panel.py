from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from cstar_reference import prospective_resolution_scores


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--panel",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); args=ap.parse_args()
    if not args.panel.is_file():
        report={"contract":"CSTAR_M3_OFFLINE_GATE_V1","pass":False,"verdict":"M3_REAL_GATE_BLOCKED_ASSET_MISSING","required_asset":"same decision context x >=2 feasible routes x independent realized outcomes","panel":str(args.panel)}
        args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(report,indent=2)+"\n"); print(report["verdict"]); return 3
    data=json.loads(args.panel.read_text()); cases=data["cases"]; wins=losses=ties=0; details=[]
    for case in cases:
        scores=prospective_resolution_scores(case["posterior"],case["route_laws"]); chosen=max(scores,key=lambda s:(s.resolution,-s.route_index)).route_index
        native=int(case["native_route"]); risk=[float(x) for x in case["realized_source_risk"]]
        dc=risk[chosen]-risk[native]; wins+=dc<0; losses+=dc>0; ties+=dc==0
        details.append({"id":case.get("id"),"chosen_route":chosen,"native_route":native,"chosen_resolution":scores[chosen].resolution,"risk_delta":dc})
    passed=wins>losses and wins>0
    report={"contract":"CSTAR_M3_OFFLINE_GATE_V1","cases":len(cases),"wins":wins,"losses":losses,"ties":ties,"pass":passed,"verdict":"M3_OFFLINE_PASS" if passed else "M3_OFFLINE_NO_GO","details":details}
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(report,indent=2)+"\n"); print(report["verdict"]); return 0 if passed else 2
if __name__=="__main__": raise SystemExit(main())
