#!/usr/bin/env python3
"""Frozen scoring; no truth files are accepted or opened."""
import argparse, csv, hashlib, json, math, random
from pathlib import Path
import numpy as np

def rows(p):
    with p.open(newline='') as f: return list(csv.DictReader(f))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def writecsv(p, fields, data):
    with p.open('w', newline='') as f:
        w=csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(data)
def scores(pred, events):
    elog=brier=0.0
    for p,e in zip(pred,events):
        h=int(e['hit']); p=float(p); q=min(1-1e-6,max(1e-6,p))
        elog+=h*math.log(q)+(1-h)*math.log1p(-q); brier-=(h-p)**2
    return elog,brier

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('bank'); ap.add_argument('out'); a=ap.parse_args()
    root=Path(a.root); bank=Path(a.bank); out=Path(a.out); out.mkdir(exist_ok=False)
    events=rows(root/'inputs/measurement_events.csv'); seq=rows(root/'code/event_state_sequences.csv')
    candidates=rows(root/'inputs/C_candidate_scores.csv'); grid=rows(root/'inputs/measured_map_at_update.csv')
    width=int(grid[0]['grid_width']); n=len(grid)
    assert len(events)==len(seq)==20 and len(candidates)==87
    for e,s in zip(events,seq):
        assert all(e[k]==s[k] for k in ('event_id','robot_i','robot_j','hit'))
    states=[[int(s['state_'+str(i)]) for i in range(1,11)] for s in seq]
    sites={}
    for i,e in enumerate(events): sites.setdefault((int(e['robot_i']),int(e['robot_j'])),[]).append(i)
    assert len(sites)==4 and all(len(v)==5 for v in sites.values())
    rng=random.Random(2026092601); assignments=[]
    for _ in range(200):
        assignment=list(range(20))
        for indices in sites.values():
            shuffled=indices.copy(); rng.shuffle(shuffled)
            for i,j in zip(indices,shuffled): assignment[i]=j
        assignments.append(assignment)
    (out/'permutation_assignments.json').write_text(json.dumps({'seed':2026092601,'generator':'Python random.Random; insertion-order sites; 200 sequential within-site shuffle calls per site','assignments':assignments},indent=2)+'\n')
    score_rows=[]; perm_rows=[]; pred_rows=[]; inventory=[]
    for c in candidates:
        cid=c['candidate_id']; maps=[]
        for k in range(11):
            p=bank/'bank'/('state_'+str(k))/'maps'/(cid+'.f32')
            v=np.fromfile(p,dtype='<f4'); assert len(v)==n and np.isfinite(v).all() and ((v>=0)&(v<=1)).all()
            maps.append(v); inventory.append({'candidate_id':cid,'state':k,'path':str(p.relative_to(bank)),'bytes':p.stat().st_size,'sha256':sha(p)})
        historic=np.fromfile(root/'inputs/historical_maps'/(cid+'.f32'),dtype='<f4')
        cell=[int(e['robot_j'])*width+int(e['robot_i']) for e in events]
        p0=[float(historic[x]) for x in cell]; p1=[float(maps[0][x]) for x in cell]
        p2=[sum(float(maps[k][x]) for k in ss)/10 for x,ss in zip(cell,states)]
        c1=[0.0]*20
        for indices in sites.values():
            pool=[k for i in indices for k in states[i]]
            p=sum(float(maps[k][cell[indices[0]]]) for k in pool)/50
            for i in indices: c1[i]=p
        for arm,pred in [('historical',p0),('P1',p1),('C1',c1),('P2',p2)]:
            elog,brier=scores(pred,events)
            score_rows.append({'candidate_id':cid,'arm':arm,'Elog':elog,'Ebrier':brier})
            pred_rows.extend({'candidate_id':cid,'arm':arm,'event_id':e['event_id'],'hit':e['hit'],'probability':p} for e,p in zip(events,pred))
        for pi,assignment in enumerate(assignments):
            pred=[sum(float(maps[k][cell[i]]) for k in states[j])/10 for i,j in enumerate(assignment)]
            elog,brier=scores(pred,events)
            perm_rows.append({'candidate_id':cid,'permutation':pi,'Elog':elog,'Ebrier':brier})
    writecsv(out/'candidate_scores_source_blind.csv',['candidate_id','arm','Elog','Ebrier'],score_rows)
    writecsv(out/'permutation_scores_source_blind.csv',['candidate_id','permutation','Elog','Ebrier'],perm_rows)
    writecsv(out/'event_predictions.csv',['candidate_id','arm','event_id','hit','probability'],pred_rows)
    writecsv(out/'map_hashes.csv',['candidate_id','state','path','bytes','sha256'],inventory)
    manifest={'candidate_count':87,'state_count':11,'sensor_height_bank_map_count':957,'P0_maps':87,'P1_reuses_state0':True,'events':20,'sites':4,'permutations':200,'seed':2026092601,'eps':1e-6,'input_hashes':{str(p.relative_to(root)):sha(p) for p in sorted((root/'inputs').rglob('*')) if p.is_file()},'code_hashes':{p.name:sha(p) for p in sorted((root/'code').iterdir()) if p.is_file()},'binary_sha256':sha(root/'wind_alignment_replay')}
    (out/'forward_bank_manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    files=[p for p in sorted(out.iterdir()) if p.is_file()]
    (out/'SCORES_SHA256.txt').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in files))
    print(json.dumps({'score_rows':len(score_rows),'permutation_rows':len(perm_rows),'map_count':len(inventory)},indent=2))
if __name__=='__main__': main()
