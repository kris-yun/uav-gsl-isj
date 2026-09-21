"""Truth-blind preparation; reads only geometry, wind, native context fields."""
import collections,csv,hashlib,itertools,json,pathlib,sys
import numpy as np
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]/'reference'))
import tnqc_vgr_fixed_trajectory_replay as native

def dump(p,x): p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def bfs(start,neighbors):
    dist={start:0};parent={start:None};queue=collections.deque([start])
    while queue:
        u=queue.popleft()
        for v in neighbors[u]:
            if v not in dist: dist[v]=dist[u]+1;parent[v]=u;queue.append(v)
    return dist,parent
def path_to(v,parent):
    p=[]
    while v is not None: p.append(v);v=parent[v]
    return p[::-1]

def prepare(root,out):
    out.mkdir(parents=True,exist_ok=False)
    worlds=[{'id':f'train_{i:02}', 'angle_deg':a,'speed':v,'noise':d,'replica':0}
            for i,(a,v,d) in enumerate(itertools.product([-15,0,15],[.8,1.,1.2],[.8,1.,1.2]))]
    worlds += [{'id':f'heldout_{i:02}', 'angle_deg':a,'speed':v,'noise':d,'replica':1}
               for i,(a,v,d) in enumerate(itertools.product([-7.5,7.5],[.9,1.1],[.9,1.1]))]
    with (out/'worlds.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(worlds[0]));w.writeheader();w.writerows(worlds)
    allcases=[]
    for h,s in itertools.product(['House01','House02','House03'],[0,1]):
        case=f'{h}_seed{s}';bank=root/'native'/f'{case}_off_off'/'context_bank'
        uid,t=native.choose_final_update(bank,300);d=bank/f'source_update_{uid:04}'
        cells,bygrid=native.load_cells(d); candidates=native.load_candidates(d)
        partition=native.final_partition(cells,candidates); measure=collections.Counter(partition.values())
        timing=next(r for r in native.rows(bank/'source_update_timing.csv') if int(r['source_update_id'])==uid)
        geom=native.load_grid_metadata(bank,uid)
        robot=np.array([float(timing['robot_x']),float(timing['robot_y'])])
        start=min(cells,key=lambda i:(np.linalg.norm(np.array([cells[i].x,cells[i].y])-robot),i))
        neighbors={i:sorted(bygrid[g] for g in [(c.grid_i-1,c.grid_j),(c.grid_i+1,c.grid_j),(c.grid_i,c.grid_j-1),(c.grid_i,c.grid_j+1)] if g in bygrid) for i,c in cells.items()}
        ds,parents=bfs(start,neighbors)
        entry=float(np.linalg.norm(robot-np.array([cells[start].x,cells[start].y])))
        budget=max(0.,(300-t-6)*.35-entry)
        allowed=sorted(i for i in ds if ds[i]*geom.cell_size<=budget+1e-9)
        actions=[start];dists={start:ds};paths={start:parents}
        while len(actions)<min(12,len(allowed)):
            selected=min((i for i in allowed if i not in actions),key=lambda i:(-min(dists[a][i] for a in actions),i))
            actions.append(selected);dists[selected],paths[selected]=bfs(selected,neighbors)
        pairs=[]
        for a,b in itertools.product(actions,repeat=2):
            length=entry+geom.cell_size*(ds[a]+dists[a][b])
            if length/.35+6<=300-t+1e-8:
                pairs.append({'a':actions.index(a),'b':actions.index(b),'length_m':length,'duration_s':length/.35+6,
                              'first_path':path_to(a,parents),'second_path':path_to(b,paths[a])})
        records={r['candidate_id']:r for r in native.rows(d/'candidate_manifest.csv')}
        roots=[]
        for k,c in candidates.items():
            if not any(o.area>c.area and o.origin_i<=c.origin_i and o.origin_j<=c.origin_j and o.origin_i+o.size_i>=c.origin_i+c.size_i and o.origin_j+o.size_j>=c.origin_j+c.size_j for o in candidates.values()):roots.append(k)
        sources=[{'id':k,'x':float(records[k]['native_source_x']),'y':float(records[k]['native_source_y']),
                  'measure':measure[k], 'root':k in roots,'native_score':float(records[k]['native_score'])} for k in sorted(candidates)]
        cd=out/case;cd.mkdir()
        with (cd/'sources.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(sources[0]));w.writeheader();w.writerows(sources)
        inputs=[bank/'source_update_timing.csv',d/'candidate_manifest.csv',d/'measured_hit_probability.csv',d/'estimated_wind.csv',d/'candidate_support_alignment.csv',d/'source_posterior.csv']
        conf=[{'cell_index':i,'confidence':cells[i].confidence} for i in sorted(cells)]
        payload={'case':case,'house':h,'seed':s,'bank':str(bank),'update':uid,'time_s':t,'remaining_s':300-t,
                 'geometry':vars(geom),'robot_xy':robot.tolist(),'start_cell':start,'point_robot_grid_only':True,
                 'sources':sources,'partition':partition,'actions':[{'cell_index':i,'x':cells[i].x,'y':cells[i].y} for i in actions],
                 'pairs':pairs,'confidence':conf,'inputs_sha256':{str(p):sha(p) for p in inputs},
                 'existing_full_maps':len(list((d/'candidate_maps').glob('*.f32'))),'truth_read':False}
        dump(cd/'design.json',payload);allcases.append({'case':case,'sources':len(sources),'leaves':len(measure),'actions':len(actions),'pairs':len(pairs),'design_sha256':sha(cd/'design.json')})
    dump(out/'PRE_RESPONSE_FREEZE.json',{'contract_sha256':sha(pathlib.Path(__file__).with_name('CONTRACT.md')),'worlds_sha256':sha(out/'worlds.csv'),'cases':allcases,'truth_read':False})
    print(json.dumps(allcases,indent=2))

if __name__=='__main__':prepare(pathlib.Path(sys.argv[1]).resolve(),pathlib.Path(sys.argv[2]).resolve())
