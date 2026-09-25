#!/usr/bin/env python3
"""Hash and package frozen RIA inputs, code, and outputs for review."""
import hashlib
import json
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "evidence/relational_identifiability_a0"
UP = ROOT / "evidence/source_probe_crossed_audit_v0"
DEST = Path(r"D:\ZYC\A-gas\_staging\RIA_A0_REVIEW_20260926.tar.gz")

def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()

def manifest(name,paths):
    lines=[f"{sha(p)}  {p.relative_to(ROOT).as_posix()}" for p in sorted(paths)]
    (OUT/name).write_text("\n".join(lines)+"\n",encoding="utf-8")

def main():
    assert json.loads((OUT/"RIA_A0_RESULT.json").read_text())["decision"]=="RIA_A0_PHYSICAL_IDENTIFIABILITY_TARGET_SUPPORTED"
    assert json.loads((OUT/"RIA_A0_INDEPENDENT_RECOMPUTATION.json").read_text())["decision_matches"]
    code=list((ROOT/"research/relational_identifiability_a0").glob("*.py"))
    code+=list((ROOT/"research/relational_identifiability_a0").glob("*.md"))
    inputs=[UP/n for n in ("SPX_G0_PRE_SCORE_LOCK.json","SPX_G0_A0_COMPATIBILITY.json",
            "SPX_G0_FROZEN_PAIRS.csv","SPX_G0_CENTRAL_PAIR_PROBE.csv","SPX_G0_OFFSTRIP_PAIR_PROBE.csv",
            "SPX_G0_TARGET_METRICS.csv")]
    inputs+=list(UP.glob("SPX_G0_*_10x30.npy"))
    outputs=[p for p in OUT.iterdir() if p.is_file() and not p.name.endswith("_SHA256.tsv")]
    manifest("RIA_A0_CODE_SHA256.tsv",code)
    manifest("RIA_A0_INPUT_SHA256.tsv",inputs)
    manifest("RIA_A0_OUTPUT_SHA256.tsv",outputs)
    bundle=code+inputs+outputs+[OUT/n for n in ("RIA_A0_CODE_SHA256.tsv","RIA_A0_INPUT_SHA256.tsv","RIA_A0_OUTPUT_SHA256.tsv")]
    DEST.parent.mkdir(parents=True,exist_ok=True)
    if DEST.exists():
        raise FileExistsError(DEST)
    with tarfile.open(DEST,"w:gz") as tar:
        for p in sorted(bundle):
            tar.add(p,arcname=p.relative_to(ROOT).as_posix(),recursive=False)
    # Verify every member against the final source file.
    with tarfile.open(DEST,"r:gz") as tar:
        members=tar.getmembers()
        assert len(members)==len(bundle)
        for m in members:
            content=tar.extractfile(m).read()
            assert hashlib.sha256(content).hexdigest()==sha(ROOT/m.name)
    print(json.dumps({"path":str(DEST),"bytes":DEST.stat().st_size,"sha256":sha(DEST),
                      "member_count":len(bundle)},sort_keys=True))

if __name__=="__main__":
    main()
