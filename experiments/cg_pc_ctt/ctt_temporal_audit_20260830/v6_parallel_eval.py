#!/usr/bin/env python3
from __future__ import annotations
import multiprocessing as mp
import sys
from pathlib import Path
sys.path.insert(0,'/mnt/data/h01_temporal_gate')
import v6_physics_certified_isotonic_temporal_evidence as v6

def worker(args):
    u,mode=args
    return str(v6.evaluate_one_update(u,mode))

def main(mode='median'):
    with mp.Pool(5) as pool:
        paths=pool.map(worker,[(u,mode) for u in range(1,6)])
    import json
    print(json.dumps(v6.finalize([Path(p) for p in paths],mode),indent=2))

if __name__=='__main__': main('median')
