#!/usr/bin/env python3
from __future__ import annotations
import multiprocessing as mp
import sys
from pathlib import Path
sys.path.insert(0,'/mnt/data/h01_temporal_gate')
import v4_physics_certified_interval_temporal_nre as v4

def worker(update:int)->str:
    return str(v4.evaluate_one_update(update))

def main():
    with mp.Pool(5) as pool:
        paths=pool.map(worker,range(1,6))
    summary=v4.finalize_median([Path(p) for p in paths])
    import json
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    main()
