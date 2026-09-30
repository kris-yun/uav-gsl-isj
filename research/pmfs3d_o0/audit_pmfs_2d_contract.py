#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path

def must(text:str, pat:str, label:str):
    if not re.search(pat,text,re.M|re.S):
        raise RuntimeError(f"missing PMFS 2D contract: {label}")
    return True

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root",type=Path,required=True)
    ap.add_argument("--out",type=Path)
    a=ap.parse_args()
    root=a.repo_root
    h=(root/"ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.hpp").read_text()
    c=(root/"ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp").read_text()
    p=(root/"ros2_package/src/gsl_server/algorithms/PMFS/PMFS.cpp").read_text()
    checks={
      "filament_position_Vector2": must(h,r"struct\s+Filament\s*\{[^}]*Vector2\s+position","Filament Vector2"),
      "wind_grid_Vector2": must(h,r"Grid2D<Vector2>\s+wind","Grid2D<Vector2> wind"),
      "source_point_Vector2": must(h,r"const\s+Vector2\s+point","SimulationSource Vector2 point"),
      "move_filament_Vector2": must(c,r"Vector2\s+velocity\s*=\s*wind\.dataAt","2D moveFilament velocity"),
      "move_path_Vector2": must(c,r"Vector2\s+newPos\s*=\s*filament\.position","2D newPos"),
      "pmfs_estimatedWindVectors_Vector2": must(p,r"Grid2D<Vector2>\s+windGrid","PMFS windGrid Vector2"),
      "export_estimated_wind_xy_only": must(c,r"estimated_wind\.csv[^\n]*[\s\S]{0,500}wind_x,wind_y","estimated wind xy only"),
    }
    out={
      "decision":"PMFS_NATIVE_2D_TRANSPORT_CONTRACT_PASS",
      "checks":checks,
      "interpretation":"Native PMFS source-forward transport stores filament position and wind as Vector2 and exports x/y,u/v only; this audit does not claim 3D would improve localization."
    }
    if a.out:
      a.out.parent.mkdir(parents=True,exist_ok=True)
      a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
