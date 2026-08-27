#!/usr/bin/env python3
from __future__ import annotations
import csv, json, struct
from pathlib import Path
import numpy as np

MAGIC = 0x32564B4E42545443
HEADER = struct.Struct('<7Q')
TIMESTEPS = 200
NEVER = TIMESTEPS

def read_csv(path: Path):
    with path.open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def read_first_hits(path: Path, expected_carrier=None, expected_member=None):
    with path.open('rb') as f:
        raw=f.read(HEADER.size)
        if len(raw)!=HEADER.size: raise ValueError(f'short header: {path}')
        magic,version,carrier,member,timesteps,cell_count,words=HEADER.unpack(raw)
        if magic!=MAGIC or version!=1 or timesteps!=TIMESTEPS:
            raise ValueError(f'contract mismatch: {path}')
        if expected_carrier is not None and carrier!=expected_carrier: raise ValueError('carrier header mismatch')
        if expected_member is not None and member!=expected_member: raise ValueError('member header mismatch')
        f.seek(HEADER.size + 4*timesteps)
        b=f.read(4*cell_count)
        if len(b)!=4*cell_count: raise ValueError(f'short first-hit payload: {path}')
    a=np.frombuffer(b,dtype='<i4').copy(); a[a<0]=NEVER
    if np.any(a>NEVER): raise ValueError(f'invalid first-hit: {path}')
    return a.astype(np.int16), int(cell_count)

def load_bank_first_hits(bank: Path):
    contract=json.loads((bank/'ctt_trace_bank_contract.json').read_text(encoding='utf-8'))
    if contract.get('contract')!='CTT_V13_TRUTH_FREE_TRACE_BANK_V1' or contract.get('source_truth_used') is not False:
        raise ValueError('not a truth-free CTT V13 bank')
    carriers=read_csv(bank/'carrier_manifest.csv')
    if len(carriers)!=int(contract.get('carrier_count',len(carriers))): raise ValueError('carrier count drift')
    xy=np.asarray([[float(r['x']),float(r['y'])] for r in carriers],dtype=np.float64)
    wind=read_csv(bank/'estimated_wind.csv')
    free_idx=np.asarray([int(r['cell_index']) for r in wind],dtype=np.int32)
    query_xy=np.asarray([[float(r['x']),float(r['y'])] for r in wind],dtype=np.float64)
    S=len(carriers); M=int(contract['transport_members']); D=len(free_idx)
    out=np.empty((S,M,D),dtype=np.int16)
    cell_count=None
    for s in range(S):
        for m in range(M):
            a,n=read_first_hits(bank/'records'/f'carrier_{s:04d}_member_{m:02d}.cttbin',s,m)
            if cell_count is None: cell_count=n
            elif n!=cell_count: raise ValueError('cell_count drift')
            if np.any(free_idx<0) or np.any(free_idx>=n): raise ValueError('free index out of range')
            out[s,m]=a[free_idx]
    return out,xy,query_xy,free_idx,contract
