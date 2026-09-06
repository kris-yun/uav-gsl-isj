from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from common.trace_io import discover_seed12_run_root

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--run-root",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); args=ap.parse_args(); r=discover_seed12_run_root(args.run_root); args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(r,indent=2)+"\n"); print(f"CSTAR_SPENT_MANIFEST episodes={len(r['episodes'])} missing={len(r['missing_run_dirs'])}"); return 0 if r['episodes'] else 3
if __name__=="__main__": raise SystemExit(main())
