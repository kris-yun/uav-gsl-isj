#!/usr/bin/env python3
"""Reconstruct high-rate UAV gas sequences from the frozen raw House02 filament bank.

Purpose: MZ Innovation Likelihood M0 only.
No new GADEN simulation is generated and no concentration-grid target is opened.

The two frozen navigation geometries are historical PMFS paths compressed as
save-index change points. Positions are held until the next change point; this
exactly reproduces the nearest-0.2-s sensor-pose sampling used when the paths
were frozen against the 566 GADEN save times.
"""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
SLL=HERE.parent/"source_lineage_lagrangian_v2"
sys.path.insert(0,str(SLL))
from export_gaden_filaments import parse_snapshot  # noqa: E402

CELLS=[
"S1_W1_A","S1_W1_B","S2_W1_A","S2_W1_B",
"S1_W2_A","S1_W2_B","S2_W2_A","S2_W2_B",
]

NAV={
0:[
(0,-0.5,-2.5,.3),(29,-1.2855,-2.5009,.3),(30,-1.6427,-2.5009,.3),
(62,-1.9427,-2.5009,.3),(63,-2.5427,-2.5009,.3),(90,-2.8427,-2.5009,.3),
(91,-3.4427,-2.5009,.3),(119,-2.8427,-2.5009,.3),(120,-2.0306,-2.713,.3),
(121,-1.3942,-3.3494,.3),(122,-1.3427,-3.4009,.3),(149,-.7427,-3.4009,.3),
(150,.1573,-3.4009,.3),(151,.8815,-2.9766,.3),(152,1.5179,-2.3402,.3),
(153,1.6573,-2.2009,.3),(180,1.1451,-1.9887,.3),(181,1.0573,-1.9009,.3),
(208,1.0573,-2.2009,.3),(209,.8451,-3.013,.3),(210,.7573,-3.1009,.3),
(240,.9694,-3.613,.3),(241,1.0573,-3.7009,.3),(273,.7573,-3.7009,.3),
(274,-.1427,-3.7009,.3),(275,-.7427,-3.7009,.3),(276,-1.5549,-3.913,.3),
(277,-1.6427,-4.4766,.3),(278,-1.767,-5.3251,.3),(279,-2.1913,-5.7494,.3),
(280,-2.2427,-5.8009,.3),(313,-1.7306,-5.5887,.3),(314,-1.6427,-5.5009,.3),
(346,-2.2427,-5.5009,.3),(347,-2.7549,-5.2887,.3),(348,-2.8427,-5.2009,.3),
(380,-2.2427,-5.2009,.3),(414,-1.6427,-5.2009,.3),(415,-1.2185,-5.6251,.3),
(416,-1.0427,-5.8009,.3),(448,-1.0427,-5.2009,.3),(481,-1.2549,-5.713,.3),
(482,-1.6427,-6.1009,.3),(515,-1.4306,-5.8887,.3),(516,-.7063,-5.4645,.3),
(517,-.4427,-5.2009,.3),(550,-1.3427,-5.2009,.3),(551,-1.9427,-5.2009,.3),
(552,-2.8427,-5.2009,.3),(553,-3.267,-5.6251,.3),(554,-3.7427,-6.1009,.3),
],
1:[
(0,-.5,-2.5,.3),(29,-1.2855,-2.5009,.3),(30,-1.6427,-2.5009,.3),
(62,-1.9427,-2.5009,.3),(63,-2.5427,-2.5009,.3),(91,-3.4427,-2.5009,.3),
(119,-2.8427,-2.5009,.3),(120,-2.2063,-3.1373,.3),(121,-1.6427,-3.7009,.3),
(148,-1.3427,-3.7009,.3),(149,-.4427,-3.7009,.3),(150,.2815,-3.2766,.3),
(151,.9179,-2.6402,.3),(152,1.3573,-2.2009,.3),(179,1.3573,-2.5009,.3),
(180,1.6573,-2.8009,.3),(207,1.3573,-2.8009,.3),(208,.7573,-3.1009,.3),
(238,.1573,-3.1009,.3),(239,-.1427,-3.1009,.3),(271,-.4427,-3.1009,.3),
(272,-1.167,-3.5251,.3),(273,-1.5913,-3.9494,.3),(274,-1.6427,-4.8281,.3),
(275,-1.8034,-5.3615,.3),(276,-2.2427,-5.8009,.3),(310,-1.8185,-5.0766,.3),
(311,-1.6427,-4.5494,.3),(312,-1.6427,-3.6494,.3),(313,-1.8913,-3.1524,.3),
(314,-1.9427,-3.1009,.3),(346,-1.3427,-3.1009,.3),(379,-1.6427,-3.1009,.3),
(380,-2.4549,-3.313,.3),(381,-2.5427,-3.4009,.3),(414,-2.0306,-3.613,.3),
(415,-1.6427,-4.0524,.3),(416,-1.6427,-4.9524,.3),(417,-1.3942,-5.4494,.3),
(418,-1.0427,-5.8009,.3),(450,-1.0427,-5.5009,.3),(451,-1.0427,-5.2009,.3),
(484,-1.9427,-5.2009,.3),(518,-2.5427,-5.2009,.3),(519,-2.8427,-5.5009,.3),
(552,-3.567,-5.9251,.3),(553,-3.7427,-6.1009,.3),
]}

def read_contract(path:Path):
    out={}
    for line in path.read_text().splitlines():
        if line.strip():
            k,v=line.split("\t",1); out[k]=v
    return out

def read_occ(path:Path):
    lines=path.read_text().splitlines()
    mn=np.asarray([float(x) for x in lines[0].split()[1:]],float)
    dims=tuple(int(x) for x in lines[2].split()[1:])
    cell=float(lines[3].split()[1]); nx,ny,nz=dims
    occ=np.ones((nz,nx,ny),np.int8); z=x=0
    for line in lines[4:]:
        if line.strip()==";": z+=1;x=0;continue
        if z>=nz: break
        a=np.fromstring(line,sep=" ",dtype=np.int8)
        if len(a):
            if len(a)!=ny: raise ValueError("occupancy y dimension mismatch")
            occ[z,x]=a;x+=1
    return mn,dims,cell,occ

def idx(p,mn,cell):
    # GADEN/GLM conversion truncates toward zero.
    return np.trunc((p-mn)/cell).astype(np.int64)

def state(p,mn,dims,cell,occ):
    q=idx(p,mn,cell); nx,ny,nz=dims
    if q[0]<0 or q[0]>=nx or q[1]<0 or q[1]>=ny or q[2]<0 or q[2]>=nz:
        return 3
    return int(occ[q[2],q[0],q[1]])

def los(a,b,mn,dims,cell,occ):
    if state(a,mn,dims,cell,occ)!=0 or state(b,mn,dims,cell,occ)!=0:
        return False
    v=b-a; dist=float(np.linalg.norm(v))
    if dist<=1e-12: return True
    steps=int(dist/cell)
    if steps<=1: return True
    direction=v/dist; inc=dist/steps
    for i in range(1,steps):
        p=a+direction*(inc*i)
        if state(p,mn,dims,cell,occ)!=0: return False
    return True

def nav_positions(seed:int,n=566):
    cp=NAV[seed]; out=np.zeros((n,3),float); j=0
    for k in range(n):
        while j+1<len(cp) and cp[j+1][0]<=k: j+=1
        out[k]=cp[j][1:4]
    return out

def concentration(fil,point,mn,dims,cell,occ,ppm0,sigma0):
    if len(fil)==0: return 0.0
    xyz=fil[:,:3].astype(float); sig=fil[:,3].astype(float)
    d2=np.sum((xyz-point[None,:])**2,axis=1)
    lim=3.0*sig/100.0
    hit=np.where(d2<lim*lim)[0]
    total=0.0
    for j in hit:
        if los(point,xyz[j],mn,dims,cell,occ):
            center=ppm0*(sigma0/sig[j])**3
            dcm=100.0*math.sqrt(float(d2[j]))
            total += center*math.exp(-(dcm*dcm)/(2.0*sig[j]*sig[j]))
    return total

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--bank-root",type=Path,default=Path("/home/zyc/c0_5_real_gaden_bank_20260923"))
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    contract=read_contract(args.bank_root/"bank_contract.tsv")
    mn,dims,cell,occ=read_occ(Path(contract["occupancy"]))
    ppm0=float(contract["ppm_filament_center"])
    sigma0=float(contract["filament_initial_std"])
    nav={s:nav_positions(s) for s in (0,1)}

    gas=np.zeros((len(CELLS),2,566),np.float32)
    versions={}
    for ci,name in enumerate(CELLS):
        root=args.bank_root/name/"realization"
        for k in range(566):
            p=root/f"iteration_{k}"
            fil,meta=parse_snapshot(p)
            versions[name]=[meta["major"],meta["minor"],meta["compression"]]
            for ni,seed in enumerate((0,1)):
                gas[ci,ni,k]=concentration(fil,nav[seed][k],mn,dims,cell,occ,ppm0,sigma0)
        print(name,float(np.max(gas[ci])),float(np.mean(gas[ci])),flush=True)

    args.out.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(args.out,gas_ppm=gas,cells=np.asarray(CELLS),
                        nav_seed0=nav[0],nav_seed1=nav[1],
                        save_index=np.arange(566,dtype=np.int32))
    meta={
      "format":"mz_il_uav_gas_sequences_v1",
      "cells":CELLS,
      "shape":list(gas.shape),
      "nav_seeds":[0,1],
      "ppm0":ppm0,"sigma0_cm":sigma0,
      "concentration_contract":"GADEN 3-sigma cutoff + obstacle LOS + ppm0*(sigma0/sigma)^3",
      "versions":versions,
      "uses_target_concentration_grid":False,
      "generates_new_plume_data":False
    }
    args.out.with_suffix(".json").write_text(json.dumps(meta,indent=2)+"\n")
    print(json.dumps(meta,indent=2))

if __name__=="__main__":
    main()
