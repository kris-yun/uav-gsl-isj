#!/usr/bin/env python3
"""One-shot export of the frozen House02 C0.5 raw filament bank.

Reads the already-existing VM bank; does not rerun GADEN.
Exports all 8 factorial cells + reconstructed lineage + full 3-D W1/W2.
"""
from __future__ import annotations
import argparse, csv, json, subprocess, sys
from pathlib import Path

CELLS=[
"S1_W1_A","S1_W1_B","S1_W2_A","S1_W2_B",
"S2_W1_A","S2_W1_B","S2_W2_A","S2_W2_B",
]

def read_contract(path:Path):
    out={}
    for line in path.read_text().splitlines():
        if line.strip():
            k,v=line.split("\t",1); out[k]=v
    return out

def run(cmd):
    print("+"," ".join(map(str,cmd)),flush=True)
    subprocess.run([str(x) for x in cmd],check=True)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--bank-root",type=Path,default=Path("/home/zyc/c0_5_real_gaden_bank_20260923"))
    ap.add_argument("--repo-root",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--hash-inputs",action="store_true")
    args=ap.parse_args()

    contract=read_contract(args.bank_root/"bank_contract.tsv")
    args.out.mkdir(parents=True,exist_ok=False)
    research=args.repo_root/"research/source_lineage_lagrangian_v2"
    exp=research/"export_gaden_filaments.py"
    lin=research/"reconstruct_filament_lineage.py"
    wind=research/"export_gaden_wind_3d.py"

    run([sys.executable,wind,contract["occupancy"],contract["wind_W1"],
         contract["wind_W2"],args.out/"wind3d",
         "--wind-iteration-dt","1.0","--loop-from","1","--loop-to","10"])

    manifests={}
    for cell in CELLS:
        src=args.bank_root/cell/"realization"
        if not src.is_dir():
            raise FileNotFoundError(src)
        dst=args.out/cell
        dst.mkdir()
        fil=dst/"filaments.npz"
        cmd=[sys.executable,exp,src,fil,
             "--sim-dt",contract["time_step_s"],
             "--save-dt",contract["results_time_step_s"]]
        if args.hash_inputs: cmd.append("--hash-inputs")
        run(cmd)
        lineage=dst/"lineage.npz"
        run([sys.executable,lin,fil,lineage,
             "--sim-dt",contract["time_step_s"],
             "--emission-rate",contract["num_filaments_sec"],
             "--initial-sigma",contract["filament_initial_std"],
             "--growth-gamma",contract["filament_growth_gamma"]])
        manifests[cell]={
          "filaments":json.loads(fil.with_suffix(".json").read_text()),
          "lineage":json.loads(lineage.with_suffix(".json").read_text()),
        }

    result={
      "format":"source_lineage_house02_c05_v1",
      "raw_bank_root":str(args.bank_root),
      "cells":CELLS,
      "contract":contract,
      "cell_manifests":manifests,
      "decision":"EXPORT_AND_LINEAGE_PASS",
    }
    (args.out/"export_manifest.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"decision":result["decision"],"out":str(args.out)},indent=2))

if __name__=="__main__":
    main()
