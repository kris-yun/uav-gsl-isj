#!/usr/bin/env python3
"""I/O for frozen CTT V13 truth-free trace banks.

Binary layout is defined by CTTTransportTrace.hpp / ctt_trace_bank_builder.cpp:
  <7Q> header
  activeFilamentCounts[T] uint32
  firstHitBins[cell_count] int32
  occupancyWords[T,words_per_step] uint64

The occupancy bitset reconstructs the native PMFS cumulative hit-frequency map
exactly: frequency(q)=mean_t occupied(t,q).
"""
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

def _header(f,path,expected_carrier=None,expected_member=None):
    raw=f.read(HEADER.size)
    if len(raw)!=HEADER.size: raise ValueError(f'short header: {path}')
    magic,version,carrier,member,timesteps,cell_count,words=HEADER.unpack(raw)
    if magic!=MAGIC or version!=1 or timesteps!=TIMESTEPS or words!=(cell_count+63)//64:
        raise ValueError(f'contract mismatch: {path}')
    if expected_carrier is not None and carrier!=expected_carrier: raise ValueError('carrier header mismatch')
    if expected_member is not None and member!=expected_member: raise ValueError('member header mismatch')
    return int(carrier),int(member),int(timesteps),int(cell_count),int(words)

def read_trace_fields(path: Path, selected_cells=None, expected_carrier=None, expected_member=None):
    """Return selected first-hit bins and exact reconstructed hit frequencies.

    selected_cells: global cell indices. None means all cells.
    first_hit uses NEVER=200 for never reached; frequency is float32 in [0,1].
    """
    with path.open('rb') as f:
        carrier,member,T,C,W=_header(f,path,expected_carrier,expected_member)
        f.seek(HEADER.size + 4*T)
        raw_first=f.read(4*C)
        if len(raw_first)!=4*C: raise ValueError(f'short first-hit payload: {path}')
        first=np.frombuffer(raw_first,dtype='<i4').copy()
        first[first<0]=NEVER
        if np.any(first>NEVER): raise ValueError(f'invalid first-hit: {path}')
        raw_occ=f.read(8*T*W)
        if len(raw_occ)!=8*T*W: raise ValueError(f'short occupancy payload: {path}')
    occ=np.frombuffer(raw_occ,dtype='<u8').reshape(T,W)
    idx=np.arange(C,dtype=np.int64) if selected_cells is None else np.asarray(selected_cells,dtype=np.int64).reshape(-1)
    if len(idx)<1 or np.any(idx<0) or np.any(idx>=C): raise ValueError('selected cell out of range')
    words=idx//64; bits=idx%64
    # Advanced indexing gives [T,D]. Each bit is native occupancy at one record step.
    occupied=((occ[:,words] >> bits[None,:]) & np.uint64(1)).astype(np.float32)
    freq=occupied.mean(axis=0,dtype=np.float64).astype(np.float32)
    return first[idx].astype(np.int16),freq,C

def read_first_hits(path: Path, expected_carrier=None, expected_member=None):
    first,_,C=read_trace_fields(path,None,expected_carrier,expected_member)
    return first,C

def load_bank_trace_fields(bank: Path):
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
    first=np.empty((S,M,D),dtype=np.int16); freq=np.empty((S,M,D),dtype=np.float32)
    cell_count=None
    for s in range(S):
        for m in range(M):
            a,p,n=read_trace_fields(bank/'records'/f'carrier_{s:04d}_member_{m:02d}.cttbin',free_idx,s,m)
            if cell_count is None: cell_count=n
            elif n!=cell_count: raise ValueError('cell_count drift')
            first[s,m]=a; freq[s,m]=p
    return first,freq,xy,query_xy,free_idx,contract

def load_bank_first_hits(bank: Path):
    first,_,xy,qxy,idx,contract=load_bank_trace_fields(bank)
    return first,xy,qxy,idx,contract
