#!/usr/bin/env python3
from __future__ import annotations
import struct,tempfile
from pathlib import Path
import numpy as np
from ctt_bank_io import MAGIC,HEADER,read_trace_fields

def main():
    T=200; C=70; W=(C+63)//64; carrier=3; member=5
    occ=np.zeros((T,W),dtype='<u8')
    # cell 1 occupied at steps 2,3,4 => freq 3/200, first=2
    for t in (2,3,4): occ[t,0] |= np.uint64(1)<<np.uint64(1)
    # cell 65 occupied every even step => freq .5, first=0
    for t in range(0,T,2): occ[t,1] |= np.uint64(1)<<np.uint64(1)
    first=np.full(C,-1,dtype='<i4');first[1]=2;first[65]=0
    active=np.zeros(T,dtype='<u4')
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'x.cttbin'
        with p.open('wb') as f:
            f.write(HEADER.pack(MAGIC,1,carrier,member,T,C,W));f.write(active.tobytes());f.write(first.tobytes());f.write(occ.tobytes())
        fh,fr,n=read_trace_fields(p,[1,65,69],carrier,member)
        assert n==C
        assert fh.tolist()==[2,0,200],fh
        assert abs(float(fr[0])-3/200)<1e-8,fr
        assert abs(float(fr[1])-.5)<1e-8,fr
        assert float(fr[2])==0.0,fr
    print('CG_PC_CTT_CTT_BANK_IO_SELFTEST PASS')
if __name__=='__main__':main()
