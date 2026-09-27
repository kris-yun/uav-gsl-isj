#!/usr/bin/env python3
"""Independent graph recomputation and frozen geometry/manifest verification."""
import argparse,csv,hashlib,json,math
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rows(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--evidence',type=Path,required=True);ap.add_argument('--protocol',type=Path,required=True);a=ap.parse_args();E=a.evidence
    panel=rows(E/'HOUSE03_F1_SOURCE_PANEL_12.tsv');assert len({r['source_id'] for r in panel})==12
    for i in range(1,7):
        p,q=[r for r in panel if int(r['pair_id'])==i]
        assert abs(int(p['pmfs_i'])-int(q['pmfs_i']))+abs(int(p['pmfs_j'])-int(q['pmfs_j']))==1
        assert math.isclose(math.hypot(float(p['x_m'])-float(q['x_m']),float(p['y_m'])-float(q['y_m'])),.3,abs_tol=1e-6)
        assert min(float(p['clearance_m']),float(q['clearance_m']))>=.3
    G=E/'inputs/geometry';m=json.loads((G/'pruned_meta.json').read_text());nav=np.fromfile(G/'pruned_seed0.bin',np.uint8).reshape(m['height'],m['width'])==1
    pts=rows(a.protocol/'HOUSE03_FROZEN_30_PROBES.tsv');xy=[(2.,0.)]+[(float(r['center_x_m']),float(r['center_y_m'])) for r in pts]
    cells=[(math.floor((x-m['origin_x'])/m['resolution']),math.floor((y-m['origin_y'])/m['resolution'])) for x,y in xy]
    def center(c):return (m['origin_x']+(c[0]+.5)*m['resolution'],m['origin_y']+(c[1]+.5)*m['resolution'])
    freecells=[(int(i),int(j)) for j,i in np.argwhere(nav)];index={c:n for n,c in enumerate(freecells)}
    n=len(freecells)+31;ii=[];jj=[];vv=[]
    def edge(u,v,cost):ii.append(u);jj.append(v);vv.append(cost)
    for c,u in index.items():
        for dx in [-1,0,1]:
            for dy in [-1,0,1]:
                if dx==dy==0:continue
                q=(c[0]+dx,c[1]+dy)
                if q not in index:continue
                if dx and dy and ((c[0]+dx,c[1]) not in index or (c[0],c[1]+dy) not in index):continue
                edge(u,index[q],math.hypot(dx,dy)*m['resolution'])
    off=len(freecells)
    for k,c in enumerate(cells):
        assert c in index
        dist=math.dist(xy[k],center(c));edge(off+k,index[c],dist);edge(index[c],off+k,dist)
        for t in range(k):
            if c==cells[t]:edge(off+k,off+t,math.dist(xy[k],xy[t]));edge(off+t,off+k,math.dist(xy[k],xy[t]))
    D=dijkstra(csr_matrix((vv,(ii,jj)),shape=(n,n)),indices=list(range(off,n)),directed=False)[:,off:]
    stored=np.loadtxt(E/'GEODESIC_DISTANCE_MATRIX_31.csv',delimiter=',',skiprows=1)[:,1:]
    assert np.allclose(D,stored,atol=1e-9,equal_nan=False)
    speed=json.loads((E/'inputs/NAVIGATION_SPEED_AUDIT.json').read_text())['nominal_navigation_speed_m_s']
    def choose(avoid):
        selected=[];at=0
        for _ in range(10):
            eligible=[k for k in range(1,31) if k not in selected and D[at,k]/speed<=47.+1e-12]
            pref=[k for k in eligible if k not in avoid]
            if pref:eligible=pref
            if not selected:chosen=min(eligible,key=lambda k:(round(D[0,k],12),k))
            else:
                scores={k:round(min(math.dist(xy[k],xy[t]) for t in selected),12) for k in eligible}
                chosen=min(eligible,key=lambda k:(-scores[k],k))
            selected.append(chosen);at=chosen
        return selected
    A=choose(set());B=choose(set(A))
    for label,expected in [('A',A),('B',B)]:
        path=rows(E/f'HOUSE03_PATH_{label}_10.tsv');assert [int(r['probe_rank']) for r in path]==expected
        assert len(path)==len(set(expected))==10
        for r in path:
            f=int(r['from_probe_rank']);t=int(r['probe_rank'])
            assert math.isclose(float(r['geodesic_distance_m']),D[f,t],abs_tol=1e-9)
            assert math.isclose(float(r['travel_time_s']),D[f,t]/speed,abs_tol=1e-9)
            assert D[f,t]/speed<=47.+1e-12
    gd=rows(E/'HOUSE03_FUTURE_GADEN_SEEDS_96.tsv');pf=rows(E/'HOUSE03_FUTURE_PMFS_SEEDS_1056.tsv');assert len(gd)==96 and len(pf)==1056
    assert len(set(r['requested_seed'] for r in gd+pf))==1152
    for r in gd+pf:
        h=hashlib.sha256(r['seed_key'].encode()).hexdigest();assert h==r['seed_sha256'] and int(r['requested_seed'])==1+int(h[:16],16)%(2**31-2)
        assert r['status']=='FUTURE_NOT_EXECUTED_F1_SIGNATURE_REQUIRED'
    for sid in {r['source_id'] for r in panel}:
        assert len([r for r in gd if r['source_id']==sid])==8
        for st in range(11):assert len([r for r in pf if r['source_id']==sid and int(r['wind_state'])==st])==8
    for line in (a.protocol/'SHA256SUMS.txt').read_text().splitlines():h,name=line.split('  ',1);assert sha(a.protocol/name)==h
    wind=json.loads((E/'inputs/WIND_ASSET_AUDIT.json').read_text());assert wind['passed'] and wind['state_count']==11
    assert [r['state'] for r in wind['states']]==list(range(11))
    output=dict(passed=True,source_pairs=6,source_count=12,independent_weighted_graph_nodes=n,independent_graph_matrix_matches=True,path_A= A,path_B=B,path_algorithm_independently_recomputed=True,path_overlap=len(set(A)&set(B)),path_segments_all_feasible=True,future_gaden_rows=96,future_pmfs_rows=1056,seed_derivation_recomputed=True,seed_collisions=0,protocol_sha256_checks_passed=True,wind_states=11,gas_arrays_loaded=0,forward_runs=0,scores_computed=0)
    (E/'INDEPENDENT_F0_VERIFICATION.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output,indent=2))
if __name__=='__main__':main()
