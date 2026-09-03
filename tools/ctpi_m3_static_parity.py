#!/usr/bin/env python3
"""Static formula parity check between frozen TSDC Python and C++ CTPI M3 constants."""
from __future__ import annotations
import argparse, importlib.util, re
from pathlib import Path
import numpy as np

def load(path):
    spec=importlib.util.spec_from_file_location('tsdc',path); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--cpp',type=Path,required=True); ap.add_argument('--tsdc',type=Path,required=True); args=ap.parse_args()
    text=args.cpp.read_text()
    vals=[]
    for name in ('kBeta0','kBetaK','kBetaM'):
        m=re.search(rf'constexpr double {name} = ([^;]+);',text)
        if not m: raise RuntimeError(f'MISSING:{name}')
        vals.append(float(m.group(1)))
    ts=load(args.tsdc); beta=np.asarray(ts.TSDC_BETA_V0,float)
    if not np.array_equal(np.asarray(vals,float),beta): raise RuntimeError(f'BETA_MISMATCH:{vals}:{beta.tolist()}')
    rng=np.random.default_rng(20260903); k=rng.integers(0,9,10000,dtype=np.int64); state=rng.uniform(0,1.5,10000)
    p=(k+.5)/9.; rk=np.log(p/(1-p)); rm=np.log1p(state/.1); eta=vals[0]+vals[1]*rk+vals[2]*rm; q=1/(1+np.exp(-eta)); ref=ts.predict_committor(k,state)
    d=float(np.max(np.abs(q-ref)))
    if d>2e-15: raise RuntimeError(f'PREDICTION_PARITY:{d}')
    print('CTPI_M3_CPP_TSDC_STATIC_PARITY=PASS'); print(f'MAX_ABS={d:.17g}')
if __name__=='__main__':main()
