#!/usr/bin/env python3
"""Package RIA-A1 frozen inputs, code, outputs and SHA inventories."""
import hashlib
import json
import tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SPX=ROOT/"evidence/source_probe_crossed_audit_v0"
RIA=ROOT/"evidence/relational_identifiability_a0"
OUT=ROOT/"evidence/ria_signal_noise_a1"
PACKAGE=Path(r"D:\ZYC\A-gas\_staging\RIA_A1_REVIEW_20260926.tar.gz")

def digest(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for part in iter(lambda:f.read(1<<20),b""):h.update(part)
    return h.hexdigest()

def main():
    assert json.loads((OUT/"RIA_A1_RESULT.json").read_text())["decision"]=="RIA_A1_MIXED_SIGNAL_AND_VARIABILITY"
    assert json.loads((OUT/"RIA_A1_INDEPENDENT_RECOMPUTATION.json").read_text())["decision_matches"]
    code=list((ROOT/"research/ria_signal_noise_a1").glob("*.py"))+list((ROOT/"research/ria_signal_noise_a1").glob("*.md"))
    inputs=[SPX/"SPX_G0_CENTRAL_P_G1A_10x30.npy",SPX/"SPX_G0_CENTRAL_P_E2_10x30.npy",
            SPX/"SPX_G0_FROZEN_PAIRS.csv",SPX/"SPX_G0_PRE_SCORE_LOCK.json",
            RIA/"RIA_A0_REFERENCE_IDENTIFIABILITY.csv",RIA/"RIA_A0_BOUNDED_OPERATIONAL.csv",
            RIA/"RIA_A0_PRE_RUN_LOCK.json",RIA/"RIA_A0_RESULT.json"]
    outputs=[p for p in OUT.iterdir() if p.is_file() and not p.name.endswith("_SHA256.tsv")]
    def manifest(name,files):
        (OUT/name).write_bytes(("\n".join(f"{digest(p)}  {p.relative_to(ROOT).as_posix()}" for p in sorted(files))+"\n").encode())
    manifest("RIA_A1_CODE_SHA256.tsv",code)
    manifest("RIA_A1_INPUT_SHA256.tsv",inputs)
    manifest("RIA_A1_OUTPUT_SHA256.tsv",outputs)
    allfiles=code+inputs+outputs+[OUT/n for n in ("RIA_A1_CODE_SHA256.tsv","RIA_A1_INPUT_SHA256.tsv","RIA_A1_OUTPUT_SHA256.tsv")]
    if PACKAGE.exists():raise FileExistsError(PACKAGE)
    with tarfile.open(PACKAGE,"w:gz") as tar:
        for p in sorted(allfiles):tar.add(p,arcname=p.relative_to(ROOT).as_posix(),recursive=False)
    with tarfile.open(PACKAGE,"r:gz") as tar:
        members=tar.getmembers()
        assert len(members)==len(allfiles)
        for member in members:
            content=tar.extractfile(member).read()
            assert hashlib.sha256(content).hexdigest()==digest(ROOT/member.name)
    print(json.dumps({"path":str(PACKAGE),"bytes":PACKAGE.stat().st_size,"sha256":digest(PACKAGE),
                      "members":len(allfiles)},sort_keys=True))

if __name__=="__main__":main()
