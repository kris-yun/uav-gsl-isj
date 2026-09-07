"""Build deterministic source-blind coverage routes from map free cells.

Waypoints are selected by farthest-point sampling in the candidate domain,
then connected by A* on the free-cell graph.  No source or gas values are read.
"""
from __future__ import annotations
import argparse, csv, hashlib, heapq, json, math
from pathlib import Path

def nearest(points, target):
    return min(range(len(points)), key=lambda i:(points[i][0]-target[0])**2+(points[i][1]-target[1])**2)

def graph(points):
    idx={(round(x,2),round(y,2)):i for i,(x,y) in enumerate(points)}; out=[[] for _ in points]
    for i,(x,y) in enumerate(points):
        for dx in (-.1,0,.1):
            for dy in (-.1,0,.1):
                if dx==dy==0: continue
                j=idx.get((round(x+dx,2),round(y+dy,2)))
                if j is not None: out[i].append(j)
    return out

def astar(points,nbr,start,goal):
    q=[(0.,0.,start)]; prev={start:None}; cost={start:0.}
    while q:
        _,g,u=heapq.heappop(q)
        if u==goal:
            r=[]
            while u is not None: r.append(u);u=prev[u]
            return r[::-1]
        if g>cost[u]+1e-12: continue
        for v in nbr[u]:
            ng=g+math.hypot(points[v][0]-points[u][0],points[v][1]-points[u][1])
            if ng<cost.get(v,float('inf')):
                cost[v]=ng;prev[v]=u
                h=math.hypot(points[v][0]-points[goal][0],points[v][1]-points[goal][1])
                heapq.heappush(q,(ng+h,ng,v))
    return [start,goal]

def resample(points,n):
    cum=[0.]
    for a,b in zip(points,points[1:]): cum.append(cum[-1]+math.hypot(b[0]-a[0],b[1]-a[1]))
    total=cum[-1]; out=[]; j=0
    for k in range(n):
        s=total*k/(n-1)
        while j<len(cum)-2 and cum[j+1]<s: j+=1
        d=cum[j+1]-cum[j]; a=0 if d==0 else (s-cum[j])/d
        out.append((points[j][0]+a*(points[j+1][0]-points[j][0]),points[j][1]+a*(points[j+1][1]-points[j][1])))
    return out,total

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--maps',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--frames',type=int,default=301);ap.add_argument('--waypoints',type=int,default=12);a=ap.parse_args()
    summary={}
    for house in ('H01','H02','H03'):
        with (a.maps/house/'candidate.csv').open(encoding='utf-8',newline='') as f: pts=[(float(r['x']),float(r['y'])) for r in csv.DictReader(f)]
        xs,ys=zip(*pts); center=((min(xs)+max(xs))/2,(min(ys)+max(ys))/2); chosen=[nearest(pts,center)]
        for _ in range(a.waypoints-1):
            j=max(range(len(pts)),key=lambda i:min((pts[i][0]-pts[k][0])**2+(pts[i][1]-pts[k][1])**2 for k in chosen)); chosen.append(j)
        order=[chosen.pop(0)]
        while chosen:
            j=min(chosen,key=lambda i:(pts[i][0]-pts[order[-1]][0])**2+(pts[i][1]-pts[order[-1]][1])**2); chosen.remove(j); order.append(j)
        nbr=graph(pts); path=[]
        for s,t in zip(order,order[1:]):
            seg=astar(pts,nbr,s,t); path.extend([pts[i] for i in (seg if not path else seg[1:])])
        route,length=resample(path,a.frames); out=a.out/house;out.mkdir(parents=True,exist_ok=True); p=out/'history_route.csv'
        with p.open('w',encoding='utf-8',newline='') as f:
            w=csv.writer(f,lineterminator='\n');w.writerow(('t_sim_s','x','y','z'));w.writerows((round(i*.2,9),x,y,.3) for i,(x,y) in enumerate(route))
        ds=[math.hypot(b[0]-a[0],b[1]-a[1]) for a,b in zip(route,route[1:])]
        summary[house]={'frames':len(route),'waypoints':a.waypoints,'path_length_m':length,'max_step_m':max(ds),'bounds':[min(xs),max(xs),min(ys),max(ys)],'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    (a.out/'ROUTE_RULE.json').write_text(json.dumps({'contract':'CSTAR_SOURCE_BLIND_MAP_COVER_ROUTE_V1','source_coordinates_read':False,'candidate_domain_only':True,'waypoint_selection':'farthest_point_euclidean_from_map_center_then_nearest_neighbor','graph':'0.1m free-cell 8-neighbor A*','sample_period_s':.2,'houses':summary},indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(summary,sort_keys=True))

if __name__=='__main__': main()
