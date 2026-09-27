#!/usr/bin/env python3
"""Export the complete bank defined by the hash-frozen E1 geometry, not gas."""
import argparse,csv,hashlib,json,math
from pathlib import Path
import numpy as np
from scipy.ndimage import distance_transform_edt

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read_occ(p):
    h={};v=[]
    for line in Path(p).read_text().splitlines():
        if line.startswith('#'):
            key,*vals=line[1:].split();h[key]=list(map(float,vals))
        elif line.strip()!=';':v.extend(map(int,line.split()))
    nx,ny,nz=map(int,h['num_cells']);assert len(v)==nx*ny*nz
    return h,np.array(v,np.int8).reshape(nz,nx,ny)
def table(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
def write(p,rows):
    with Path(p).open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--evidence',type=Path,required=True);ap.add_argument('--protocol',type=Path,required=True);a=ap.parse_args()
    I=a.evidence/'inputs';G=I/'geometry';E=I/'e1'
    expected={'OccupancyGrid3D.csv':'ac8c9e69e762c8941dab46cd7e804684c2aa50dc6f0912806d19b070c135c4af','pruned_meta.json':'cdda9e893a35fb2ee3e094a5d66b23acb1503afc61210f2a038a1117b607c3e5','pruned_seed0.bin':'32d362e73211532547d76f699e957ca3c0f3f6f2b3f6cc4f4fa862cf4f4943d7','pruned_seed1.bin':'32d362e73211532547d76f699e957ca3c0f3f6f2b3f6cc4f4fa862cf4f4943d7'}
    for n,h in expected.items():assert sha(G/n)==h,n
    for line in (E/'SHA256SUMS.txt').read_text().splitlines():
        h,n=line.split('  ',1)
        if (E/n).is_file():assert sha(E/n)==h,n
    assert sha(E/'E1_HOUSE_PROBE_CONTRACTS.tsv')=='7996509bb2dd1f073a9a1c1f35d61df226fee380c9e3ba824e73308b500cc745'
    assert hashlib.sha256((E/'E1_HOUSE_PROBE_CONTRACTS.tsv').read_bytes().replace(b'\r\n',b'\n')).hexdigest()=='364c7a2f0333c95845cfb7a10dbb96ee8c5f30a47282e508e3961d4eec575812'
    m=json.loads((G/'pruned_meta.json').read_text());header,occ=read_occ(G/'OccupancyGrid3D.csv')
    origin=header['env_min(m)'];cell=header['cell_size(m)'][0];assert cell==.1
    nav=np.fromfile(G/'pruned_seed0.bin',np.uint8).reshape(m['height'],m['width']).T==1
    valid=np.zeros_like(nav);inds={};iz=math.floor((.2-origin[2])/cell)
    for i,j in np.argwhere(nav):
        x=origin[0]+(i+.5)*.30;y=origin[1]+(j+.5)*.30
        fi=math.floor((x-origin[0])/cell);fj=math.floor((y-origin[1])/cell)
        if 0<=fi<occ.shape[1] and 0<=fj<occ.shape[2] and occ[iz,fi,fj]==0:
            valid[i,j]=True;inds[int(i),int(j)]=(fi,fj)
    count=int(valid.sum());prior=json.loads((E/'E1_RESULT.json').read_text())['houses']['House03']
    assert count==prior['source_candidate_count']==624 and int(nav.sum())==prior['pmfs_pruned_free_count']==626
    clearance=distance_transform_edt(np.pad(valid,1,constant_values=False))[1:-1,1:-1]*.30
    rows=[]
    for i,j in np.argwhere(valid):
        i=int(i);j=int(j);fi,fj=inds[i,j]
        rows.append(dict(house='House03',source_id=f'pmfs_{i}_{j}',pmfs_i=i,pmfs_j=j,x_m=origin[0]+(i+.5)*.30,y_m=origin[1]+(j+.5)*.30,z_m=.2,free=1,clearance_m=float(clearance[i,j]),gaden_ix=fi,gaden_iy=fj,gaden_iz=iz))
    by={r['source_id']:r for r in rows}
    anchors=table(a.protocol/'HOUSE03_EXISTING_ANCHOR_PAIRS.tsv')
    canonical=[r for r in table(E/'E1_HOUSE_SOURCE_PANELS.tsv') if r['house']=='House03']
    assert len(canonical)==len(anchors)==6
    for r in anchors:
        cr=next(c for c in canonical if c['source_id']==r['source_id'])
        for k in r:
            assert str(r[k])==str(cr[k]) or (k not in ['house','role','source_id'] and math.isclose(float(r[k]),float(cr[k]),abs_tol=1e-12)),(k,r,cr)
        for k in ['pmfs_i','pmfs_j','x_m','y_m','z_m','clearance_m','gaden_ix','gaden_iy','gaden_iz']:
            assert math.isclose(float(r[k]),float(by[r['source_id']][k]),abs_tol=1e-12),(k,r,by[r['source_id']])
    pp=table(a.protocol/'HOUSE03_FROZEN_30_PROBES.tsv');cp=[r for r in table(E/'E1_HOUSE_PROBE_CONTRACTS.tsv') if r['house']=='House03'];assert len(pp)==len(cp)==30
    for r,c in zip(pp,cp):
        assert r==c or (r['house']==c['house'] and all(math.isclose(float(r[k]),float(c[k]),abs_tol=1e-12) for k in r if k!='house'))
    bank=a.evidence/'HOUSE03_CANONICAL_SOURCE_GEOMETRY_BANK_624.tsv';write(bank,rows)
    audit=dict(passed=True,canonical_bank_representation='complete E1 source set materialized from frozen occupancy and navigation geometry using the unchanged E1 source eligibility and clearance definition',source_count=count,all_sources_free_at_z_m=.2,source_bank_sha256=sha(bank),geometry_hashes=expected,anchor_rows_match_E1=True,probe_rows_match_E1=True,source_selection_used_gas=False)
    (a.evidence/'SOURCE_BANK_AND_PROBE_AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps(audit,indent=2))
if __name__=='__main__':main()
