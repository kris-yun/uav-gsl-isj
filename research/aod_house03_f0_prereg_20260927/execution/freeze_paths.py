#!/usr/bin/env python3
"""The path constructor has no source-panel, plume, wind, or score input."""
import argparse,csv,hashlib,heapq,json,math
from pathlib import Path
import numpy as np

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def table(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
def write(p,rows):
    with Path(p).open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--geometry',type=Path,required=True);ap.add_argument('--probes',type=Path,required=True);ap.add_argument('--speed-audit',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    m=json.loads((a.geometry/'pruned_meta.json').read_text());speed=json.loads(a.speed_audit.read_text())['nominal_navigation_speed_m_s'];assert speed>0
    nav=np.fromfile(a.geometry/'pruned_seed0.bin',np.uint8).reshape(m['height'],m['width'])==1
    probes=table(a.probes);assert len(probes)==30 and [int(r['probe_rank']) for r in probes]==list(range(1,31))
    xy={0:(2.,0.)};xy.update({int(r['probe_rank']):(float(r['center_x_m']),float(r['center_y_m'])) for r in probes})
    cells={q:(math.floor((p[0]-m['origin_x'])/m['resolution']),math.floor((p[1]-m['origin_y'])/m['resolution'])) for q,p in xy.items()}
    def free(i,j):return 0<=i<m['width'] and 0<=j<m['height'] and nav[j,i]
    def center(ij):return (m['origin_x']+(ij[0]+.5)*m['resolution'],m['origin_y']+(ij[1]+.5)*m['resolution'])
    for q,c in cells.items():assert free(*c),(q,c)
    offsets=[(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
    trees={};distances=np.full((31,31),np.inf)
    for q in range(31):
        start=cells[q];cost={start:0.};parent={start:None};heap=[(0.,start)]
        while heap:
            d,c=heapq.heappop(heap)
            if d>cost[c]+1e-12:continue
            for di,dj in offsets:
                n=(c[0]+di,c[1]+dj)
                if not free(*n):continue
                if di and dj and (not free(c[0]+di,c[1]) or not free(c[0],c[1]+dj)):continue
                nd=d+math.hypot(di,dj)*m['resolution']
                if nd<cost.get(n,math.inf)-1e-12:
                    cost[n]=nd;parent[n]=c;heapq.heappush(heap,(nd,n))
        trees[q]=parent
        for k in range(31):
            if k==q:distances[q,k]=0
            elif cells[k]==start:distances[q,k]=math.dist(xy[q],xy[k])
            elif cells[k] in cost:distances[q,k]=math.dist(xy[q],center(start))+cost[cells[k]]+math.dist(center(cells[k]),xy[k])
    assert np.allclose(distances,distances.T,atol=1e-10)
    feasible=distances/speed<=47.+1e-12
    def construct(avoid):
        picked=[];overlaps=[];cur=0
        while len(picked)<10:
            pool=[q for q in range(1,31) if q not in picked and feasible[cur,q]]
            preferred=[q for q in pool if q not in avoid]
            if preferred:pool=preferred
            if not pool:raise RuntimeError('AOD_H03_F0_HOLD_PATH_GEOMETRY: greedy path exhausted')
            if not picked:q=min(pool,key=lambda q:(round(float(distances[0,q]),12),q))
            else:q=min(pool,key=lambda q:(-round(min(math.dist(xy[q],xy[k]) for k in picked),12),q))
            if q in avoid:overlaps.append(dict(step=len(picked)+1,probe_rank=q,reason='all unused feasible candidates exhausted'))
            picked.append(q);cur=q
        return picked,overlaps
    A,oa=construct(set());B,ob=construct(set(A));assert not oa
    summaries={};segment_json={}
    for label,ordered,overlaps in [('A',A,oa),('B',B,ob)]:
        rows=[];segments=[];cur=0
        for step,q in enumerate(ordered,1):
            d=float(distances[cur,q]);t=d/speed;assert t<=47.+1e-12
            if cells[cur]==cells[q]:route=[xy[cur],xy[q]];routecells=[cells[cur]]
            else:
                routecells=[];node=cells[q]
                while node is not None:routecells.append(node);node=trees[cur][node]
                routecells.reverse();route=[xy[cur]]+[center(c) for c in routecells]+[xy[q]]
            assert math.isclose(sum(math.dist(p,v) for p,v in zip(route,route[1:])),d,abs_tol=1e-10)
            rows.append(dict(path=label,step=step,probe_rank=q,x_m=xy[q][0],y_m=xy[q][1],z_m=float(probes[q-1]['z_m']),sample_time_relative_to_path_start_s=50.*step,observation_slot_spacing_s=50.,reserved_dwell_s=3.,from_probe_rank=cur,geodesic_distance_m=d,travel_time_s=t,remaining_slot_s=47.-t,overlap_with_A=int(label=='B' and q in A)))
            segments.append(dict(step=step,from_probe_rank=cur,to_probe_rank=q,geodesic_distance_m=d,travel_time_s=t,grid_cells=routecells,waypoints_xy=route))
            cur=q
        write(a.out/f'HOUSE03_PATH_{label}_10.tsv',rows)
        segment_json[label]=segments
        summaries[label]=dict(ordered_probe_ranks=ordered,total_route_distance_m=sum(r['geodesic_distance_m'] for r in rows),max_segment_distance_m=max(r['geodesic_distance_m'] for r in rows),max_segment_travel_time_s=max(r['travel_time_s'] for r in rows),sample_count=10,distinct_probe_count=10,overlaps_logged=overlaps)
    # CSV matrix is geometry only. Infinity is retained explicitly for disconnected cells.
    with (a.out/'GEODESIC_DISTANCE_MATRIX_31.csv').open('x',newline='') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(['from_probe_rank',*range(31)])
        for q,row in enumerate(distances):w.writerow([q,*map(float,row)])
    (a.out/'PATH_SEGMENT_GEOMETRY.json').write_text(json.dumps(segment_json,indent=2)+'\n')
    audit=dict(passed=True,navigation_speed_m_s=speed,start_xy=[2.,0.],graph='8-neighbour weighted PMFS pruned grid; diagonal corner cutting forbidden; endpoints connected within their containing free cells',grid_resolution_m=m['resolution'],tie_rounding_m=1e-12,path_inputs_include_sources=False,path_inputs_include_gas=False,path_inputs_include_wind=False,observation_interval_s=50.,dwell_s=3.,maximum_travel_s=47.,relative_observation_slots_s=list(range(50,501,50)),fresh_GADEN_physical_snapshot_binding='F1 preregistration must bind these physical slots to future simulator snapshots; legacy frame numbers are not assumed to be seconds',paths=summaries,overlap_count=len(set(A)&set(B)),inputs={str(p):sha(p) for p in [a.geometry/'pruned_meta.json',a.geometry/'pruned_seed0.bin',a.probes,a.speed_audit]})
    (a.out/'PATH_FREEZE_AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit,indent=2))
if __name__=='__main__':main()
