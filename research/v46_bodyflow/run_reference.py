"""Run actual reference loop. Outputs are certificates, never benchmark scores."""
from pathlib import Path
import argparse
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/"tests"))
from test_chain import setup


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="results/reference_run.json")
    p.add_argument("--mode",default="m1_full")
    args=p.parse_args()
    controller,world,initial=setup(mode=args.mode)
    while True:
        candidate,record=controller.decide()
        if candidate is None:break
        controller.execute_and_update(world,candidate)
    xy,mass=controller.posterior.xy_probability()
    model=controller.posterior.model
    result={"scope":"REFERENCE_DISCRETE_GREEN_ZOH_ONLY_NOT_NATIVE_PERFORMANCE",
            "mode":args.mode,"decisions":controller.decisions,"stop":record,
            "xy":xy.tolist(),"mass":mass.tolist(),"raw_unique_frames":len(controller.posterior.ledger),
            "forward_calls":model.forward_calls,"field_evaluations":model.field_evaluations,
            "safety_pair_checks":controller.safety.pair_checks,
            "source_confirmation":controller.source_confirmation}
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"output":str(out),"decisions":len(controller.decisions),
                      "raw_frames":len(controller.posterior.ledger),"scope":result["scope"]}))


if __name__=="__main__":main()
