#!/usr/bin/env python3
"""Read-only 3D wind severity census; no concentration decoding or simulations."""
import csv
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path('/home/zyc/pmfs_3d_author_limitation_d0')
OUT = ROOT/'census'
ASSET = Path('/home/zyc/ocb_r2_s1_tools/static_asset_audit/S1_STATIC_ASSET_AUDIT.json')
S2 = ROOT/'OCB_R2_S2_DISCOVERY_RUNLIST_32.tsv'
S2X = ROOT/'OCB_R2_S2X_RUNLIST_32.tsv'
PROBES = Path('/home/zyc/aod_r2_f0/tools/E1_HOUSE_PROBE_CONTRACTS.tsv')

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def rows(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
def dump(p,obj):p.write_text(json.dumps(obj,sort_keys=True,indent=2,allow_nan=False)+'\n')
def tsv(p,data):
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(data)

def occupancy(path):
    lines=Path(path).read_text().splitlines()
    origin=np.array(list(map(float,lines[0].split()[1:])))
    dims=np.array(list(map(int,lines[2].split()[1:])))
    cell=float(lines[3].split()[1]);assert cell==.1
    blocks=[];block=[]
    for line in lines[4:]:
        if line.strip()==';':
            if block:blocks.append(np.array(block,dtype=np.uint8));block=[]
        elif line.strip():block.append(list(map(int,line.split())))
    if block:blocks.append(np.array(block,dtype=np.uint8))
    # GADEN CSV: for each z slice, x rows each containing y values.
    assert len(blocks)==dims[2],(len(blocks),dims)
    assert all(b.shape==(dims[0],dims[1]) for b in blocks),(blocks[0].shape,dims)
    occ=np.stack(blocks).transpose(0,2,1).copy()
    assert occ.shape==tuple(dims[::-1]) and set(np.unique(occ))<={0,1,2}
    zz,yy,xx=np.indices(occ.shape)
    xyz=origin+(np.stack([xx,yy,zz],axis=-1)+.5)*cell
    return origin,dims,cell,occ,xyz

def region_masks(xyz,free,source,probes):
    domain=free.copy()
    source_region=free & (np.linalg.norm(xyz-source,axis=-1)<=1.)
    probe_region=np.zeros(free.shape,bool);corridor=np.zeros(free.shape,bool)
    for p in probes:
        probe_region|=np.linalg.norm(xyz-p,axis=-1)<=.30
        v=p-source;w=xyz-source
        a=np.clip(np.sum(w*v,axis=-1)/max(float(v@v),1e-12),0.,1.)
        corridor|=np.linalg.norm(w-a[...,None]*v,axis=-1)<=.30
    return dict(DOMAIN=domain,SOURCE=source_region,PROBES=free&probe_region,CORRIDOR=free&corridor)

def metrics(wind,mask,cell):
    selected=wind[mask];n=len(selected)
    pair=mask[1:] & mask[:-1]
    if n==0:return dict(voxels=0,shear_pairs=int(pair.sum()),Rz=None,VH_mean=None,VH_rms=None,angle_deg=None,shear_per_s=None)
    uv=np.linalg.norm(selected[:,:2],axis=1);w=np.abs(selected[:,2]);speed=np.linalg.norm(selected,axis=1)
    shear=np.linalg.norm(wind[1:]-wind[:-1],axis=-1)[pair]/cell
    return dict(voxels=n,shear_pairs=int(pair.sum()),Rz=float(np.mean(w/(speed+1e-12))),
                VH_mean=float(np.mean(w/(uv+1e-12))),VH_rms=float(np.sqrt(np.mean(w*w)/(np.mean(uv*uv)+1e-12))),
                angle_deg=float(np.degrees(np.arctan2(w,uv)).mean()),
                shear_per_s=float(shear.mean()) if len(shear) else None)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    assets=json.loads(ASSET.read_text())
    assert isinstance(assets,list)
    assets=[a for a in assets if int(a['config_index'])<8]
    assert len(assets)==8 and {a['house'] for a in assets}=={'House01','House02'}
    runs=rows(S2)+rows(S2X);assert len(runs)==64
    pp=rows(PROBES)
    record=[];inventory=[];shapes={}
    for a in assets:
        idx=int(a['config_index']);context=f'X{idx:02d}';house=a['house']
        group_runs=[r for r in runs if int(r.get('parent_s2_config_index') or r['config_index'])==idx]
        assert len(group_runs)==8
        source_rows={r['source_id']:np.array([float(r[f'source_{d}']) for d in 'xyz']) for r in group_runs}
        assert len(source_rows)==2
        probes=np.array([[float(p[f'center_{d}_m']) for d in 'xy']+[float(p['z_m'])] for p in pp if p['house']==house])
        assert probes.shape==(30,3)
        op=Path(a['occupancy_path']);assert sha(op)==a['occupancy_sha256']
        origin,dims,cell,occ,xyz=occupancy(op)
        shapes[house]=dict(origin=origin.tolist(),dimensions=dims.tolist(),cell_size=cell,free_voxels=int((occ==0).sum()))
        masks={s:region_masks(xyz,occ==0,loc,probes) for s,loc in source_rows.items()}
        inventory.append(dict(context=context,path=str(op),bytes=op.stat().st_size,sha256=sha(op),kind='occupancy'))
        for state in range(11):
            data=[]
            for axis in 'UVW':
                f=next(w for w in a['wind_files'] if int(w['state'])==state and w['axis']==axis)
                path=Path(f['path']);assert sha(path)==f['sha256'] and path.stat().st_size==f['size_bytes']
                with path.open('rb') as fd:assert int(np.fromfile(fd,'<u4',1)[0])==999
                ar=np.fromfile(path,'<f8',offset=4);assert ar.size==int(np.prod(dims)) and np.isfinite(ar).all()
                data.append(ar.reshape(tuple(dims[::-1])))
                inventory.append(dict(context=context,path=str(path),bytes=path.stat().st_size,sha256=f['sha256'],kind=axis,state=state))
            field=np.stack(data,axis=-1)
            for s,regs in masks.items():
                for reg,mask in regs.items():record.append(dict(context=context,house=house,source=s,state=state,region=reg,**metrics(field,mask,cell)))
        print('SEVERITY_COMPLETE',context,flush=True)
    groups=[]
    for c in sorted({r['context'] for r in record}):
        for s in sorted({r['source'] for r in record if r['context']==c}):
            for reg in ('DOMAIN','SOURCE','PROBES','CORRIDOR'):
                rr=[r for r in record if r['context']==c and r['source']==s and r['region']==reg];assert len(rr)==11
                d={k:rr[0][k] for k in ('context','house','source','region','voxels','shear_pairs')}
                for k in ('Rz','VH_mean','VH_rms','angle_deg','shear_per_s'):
                    d[k]=float(np.mean([r[k] for r in rr])) if all(r[k] is not None for r in rr) else None
                groups.append(d)
    per_run=[]
    for r in runs:
        c=f"X{int(r.get('parent_s2_config_index') or r['config_index']):02d}"
        g=next(g for g in groups if g['context']==c and g['source']==r['source_id'] and g['region']=='CORRIDOR')
        per_run.append(dict(run_id=r['run_id'],context=c,house=r['house'],source=r['source_id'],seed=r['master_seed'],corridor_Rz=g['Rz'],independent_wind_sample=False))
    tsv(OUT/'SEVERITY_BY_STATE.tsv',record);tsv(OUT/'SEVERITY_BY_GROUP.tsv',groups);tsv(OUT/'SEVERITY_BY_REALIZATION.tsv',per_run)
    dump(OUT/'CENSUS_AUDIT.json',dict(decision='DISCOVERY_WIND_SEVERITY_CENSUS_COMPLETE',contexts=8,source_context_groups=16,discovery_realizations=64,
        state_files_checked=264,shapes=shapes,concentration_read=False,confirmation_read=False,house03_read=False,
        input_sha256={str(p):sha(p) for p in (ASSET,S2,S2X,PROBES,Path(__file__),ROOT/'SEVERITY_FREEZE.md')},inventory=inventory))

if __name__=='__main__':main()
