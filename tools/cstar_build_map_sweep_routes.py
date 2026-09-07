"""Build source-blind map-only lawnmower routes on the free-cell graph."""
from __future__ import annotations
import argparse, csv, hashlib, heapq, json, math
from pathlib import Path


def nearest(points, target):
    return min(range(len(points)), key=lambda i: (points[i][0]-target[0])**2 + (points[i][1]-target[1])**2)


def graph(points):
    # Candidate maps are regular ~0.1 m grids with House02 carrying a fixed offset.
    idx = {}
    for i, (x, y) in enumerate(points):
        idx.setdefault((round(x, 2), round(y, 2)), i)
    nbr = [[] for _ in points]
    for i, (x, y) in enumerate(points):
        for dx in (-0.1, 0.0, 0.1):
            for dy in (-0.1, 0.0, 0.1):
                if dx == dy == 0.0:
                    continue
                j = idx.get((round(x + dx, 2), round(y + dy, 2)))
                if j is not None:
                    nbr[i].append(j)
    return nbr


def astar(points, nbr, start, goal):
    q = [(0.0, 0.0, start)]
    prev, g = {start: None}, {start: 0.0}
    while q:
        _, gc, u = heapq.heappop(q)
        if u == goal:
            out = []
            while u is not None:
                out.append(u); u = prev[u]
            return out[::-1]
        if gc > g[u] + 1e-12:
            continue
        for v in nbr[u]:
            w = math.hypot(points[v][0]-points[u][0], points[v][1]-points[u][1])
            ng = gc + w
            if ng < g.get(v, float('inf')):
                g[v] = ng; prev[v] = u
                h = math.hypot(points[v][0]-points[goal][0], points[v][1]-points[goal][1])
                heapq.heappush(q, (ng+h, ng, v))
    return [start, goal]


def resample(points, n):
    cum = [0.0]
    for a, b in zip(points, points[1:]):
        cum.append(cum[-1] + math.hypot(b[0]-a[0], b[1]-a[1]))
    total = cum[-1]
    out = []
    for k in range(n):
        s = total * k / (n - 1)
        j = min(len(points)-2, max(0, next((j for j in range(len(cum)-1) if cum[j+1] >= s), len(cum)-2)))
        den = cum[j+1] - cum[j]
        a = 0.0 if den == 0 else (s-cum[j])/den
        out.append((points[j][0] + a*(points[j+1][0]-points[j][0]),
                    points[j][1] + a*(points[j+1][1]-points[j][1])))
    return out, total


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--maps', type=Path, required=True); ap.add_argument('--out', type=Path, required=True); ap.add_argument('--frames', type=int, default=301); args = ap.parse_args()
    summaries = {}
    for house in ('H01','H02','H03'):
        with (args.maps/house/'candidate.csv').open(encoding='utf-8', newline='') as f:
            pts=[(float(r['x']),float(r['y'])) for r in csv.DictReader(f)]
        xs, ys = zip(*pts); xmin,xmax,ymin,ymax=min(xs),max(xs),min(ys),max(ys)
        # More vertical passes are needed in narrow Houses; the rule depends
        # only on map aspect ratio, never on source coordinates or gas output.
        rows = 4
        levels = [ymin + (ymax-ymin)*(i+1)/(rows+1) for i in range(rows)]
        targets=[]
        for i,y in enumerate(levels):
            targets.extend([(xmin,y),(xmax,y)] if i%2==0 else [(xmax,y),(xmin,y)])
        nbr=graph(pts); ids=[nearest(pts,t) for t in targets]
        path=[]
        for a,b in zip(ids,ids[1:]):
            seg=astar(pts,nbr,a,b)
            if path: seg=seg[1:]
            path.extend([pts[i] for i in seg])
        route,total=resample(path,args.frames)
        out=args.out/house; out.mkdir(parents=True,exist_ok=True); p=out/'history_route.csv'
        with p.open('w',encoding='utf-8',newline='') as f:
            w=csv.writer(f,lineterminator='\n'); w.writerow(('t_sim_s','x','y','z'))
            w.writerows((round(i*.2,9),x,y,.3) for i,(x,y) in enumerate(route))
        ds=[math.hypot(b[0]-a[0],b[1]-a[1]) for a,b in zip(route,route[1:])]
        summaries[house]={'frames':len(route),'path_length_m':total,'max_step_m':max(ds),'sweep_rows':rows,'bounds':[xmin,xmax,ymin,ymax],'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    (args.out/'ROUTE_RULE.json').write_text(json.dumps({'contract':'CSTAR_SOURCE_BLIND_MAP_SWEEP_ROUTE_V1','source_coordinates_read':False,'candidate_domain_only':True,'sample_period_s':.2,'houses':summaries},indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(summaries,sort_keys=True))


if __name__=='__main__': main()
