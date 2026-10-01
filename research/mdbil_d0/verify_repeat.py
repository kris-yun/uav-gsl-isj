#!/usr/bin/env python3
import argparse,hashlib,json
from pathlib import Path
FILES=["DATA_CONTRACT.json","MODEL_CONFIG.json","SEED_METRICS.tsv","FOLD_METRICS.tsv","MDBIL_D0_RESULT.json","DECISION.md"]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main(a,b):
 rows=[]; ok=True
 for n in FILES:
  x,y=a/n,b/n; same=x.exists() and y.exists() and sha(x)==sha(y); ok=ok and same
  rows.append(dict(file=n,a_sha256=sha(x) if x.exists() else None,b_sha256=sha(y) if y.exists() else None,same=same))
 o=dict(decision="MDBIL_D0_DETERMINISTIC_REPEAT_PASS" if ok else "MDBIL_D0_DETERMINISTIC_REPEAT_FAIL",files=rows)
 print(json.dumps(o,indent=2,sort_keys=True)); return 0 if ok else 2
if __name__=="__main__":
 p=argparse.ArgumentParser(); p.add_argument("--a",type=Path,required=True); p.add_argument("--b",type=Path,required=True); a=p.parse_args(); raise SystemExit(main(a.a.resolve(),a.b.resolve()))
