#!/usr/bin/env python3
"""Self-checking RPO-G0 review archive with numeric physical inputs."""
import hashlib
import json
import tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"evidence/relational_physical_observability_v0"
UP=ROOT/"evidence/source_probe_crossed_audit_v0"
RIA=ROOT/"evidence/relational_identifiability_a0"
ASSET=Path(r"D:\ZYC\A-gas\_staging\SPX_G0_ASSETS_20260925")
RAW=Path(r"D:\ZYC\A-gas\_staging\RPO_G0_HOUSE02_W0_RAW_20260926")
WIND=RAW/"gas_simulations/3,5-1_slow/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20/wind"
PACKAGE=Path(r"D:\ZYC\A-gas\_staging\RPO_G0_REVIEW_20260926.tar.gz")

def hashfile(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def main():
    assert json.loads((OUT/"RPO_G0_RESULT.json").read_text())["decision"]=="RPO_G0_STOP_PHYSICAL_CONTEXT_NOT_PREDICTIVE_BEYOND_BASELINES"
    assert json.loads((OUT/"RPO_G0_INDEPENDENT_RECOMPUTATION.json").read_text())["decision_matches"]
    code=[(p,"repo/"+p.relative_to(ROOT).as_posix()) for p in (ROOT/"research/relational_physical_observability_v0").glob("*") if p.is_file()]
    input_repo=[UP/"SPX_G0_ASSET_AUDIT.json",UP/"SPX_G0_FROZEN_PAIRS.csv",UP/"SPX_G0_PRE_SCORE_LOCK.json",
                RIA/"RIA_A0_REFERENCE_IDENTIFIABILITY.csv",RIA/"RIA_A0_RESULT.json",
                ROOT/"evidence/causal_emergent_source_scale_v0/d1r/CESS_D1R_PANEL_168.tsv",
                ROOT/"evidence/environment_level_benchmark_v0/e1/E1_HOUSE_SOURCE_PANELS.tsv"]
    inputs=[(p,"repo/"+p.relative_to(ROOT).as_posix()) for p in input_repo]
    inputs += [(ASSET/"gate1a_contract.json","physical_contracts/gate1a_contract.json"),
               (ASSET/"e1_probe_contracts.tsv","physical_contracts/e1_probe_contracts.tsv"),
               (RAW/"OccupancyGrid3D.csv","physical_raw/OccupancyGrid3D.csv")]
    inputs += [(WIND/f"wind_iteration_{i}",f"physical_raw/wind_iteration_{i}") for i in range(11)]
    outputs=[(p,"repo/"+p.relative_to(ROOT).as_posix()) for p in OUT.iterdir() if p.is_file() and not p.name.endswith("_SHA256.tsv")]
    def manifest(name,items):
        (OUT/name).write_bytes(("\n".join(f"{hashfile(p)}  {arc}" for p,arc in sorted(items,key=lambda x:x[1]))+"\n").encode())
    manifest("RPO_G0_CODE_SHA256.tsv",code)
    manifest("RPO_G0_INPUT_SHA256.tsv",inputs)
    manifest("RPO_G0_OUTPUT_SHA256.tsv",outputs)
    allfiles=code+inputs+outputs+[(OUT/n,"repo/"+(OUT/n).relative_to(ROOT).as_posix())
               for n in ("RPO_G0_CODE_SHA256.tsv","RPO_G0_INPUT_SHA256.tsv","RPO_G0_OUTPUT_SHA256.tsv")]
    if PACKAGE.exists():raise FileExistsError(PACKAGE)
    with tarfile.open(PACKAGE,"w:gz") as archive:
        for path,arc in sorted(allfiles,key=lambda x:x[1]):archive.add(path,arcname=arc,recursive=False)
    expected={arc:hashfile(path) for path,arc in allfiles}
    with tarfile.open(PACKAGE,"r:gz") as archive:
        members=archive.getmembers()
        assert len(members)==len(expected)
        for member in members:
            assert hashlib.sha256(archive.extractfile(member).read()).hexdigest()==expected[member.name]
    print(json.dumps({"path":str(PACKAGE),"bytes":PACKAGE.stat().st_size,"sha256":hashfile(PACKAGE),
                      "members":len(expected)},sort_keys=True))

if __name__=="__main__":main()
