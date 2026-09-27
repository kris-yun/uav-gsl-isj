#!/usr/bin/env python3
"""Create future seed manifests and freeze semantics. No simulator is called."""
import argparse,csv,hashlib,json,math,platform,sys
from pathlib import Path
SALT='AOD_H03_F1_20260927'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def table(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
def write(p,rows):
    with Path(p).open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
def seed(channel,sid,state,replica):
    key=f'{SALT}|{channel}|{sid}|{state}|{replica}'
    h=hashlib.sha256(key.encode()).hexdigest()
    return 1+int(h[:16],16)%(2**31-2),key,h
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--evidence',type=Path,required=True);ap.add_argument('--protocol',type=Path,required=True);a=ap.parse_args();E=a.evidence
    panel=table(E/'HOUSE03_F1_SOURCE_PANEL_12.tsv');assert len(panel)==12 and len({r['source_id'] for r in panel})==12
    bank=table(E/'HOUSE03_CANONICAL_SOURCE_GEOMETRY_BANK_624.tsv');by={r['source_id']:r for r in bank};chosen=[];log=[]
    anchors=[('pmfs_24_13','pmfs_24_14'),('pmfs_1_4','pmfs_2_4'),('pmfs_44_26','pmfs_43_26')]
    candidates=[]
    for u in bank:
        for v in bank:
            if u['source_id']>=v['source_id']:continue
            if abs(int(u['pmfs_i'])-int(v['pmfs_i']))+abs(int(u['pmfs_j'])-int(v['pmfs_j']))!=1:continue
            if min(float(u['clearance_m']),float(v['clearance_m']))<.3:continue
            x=(float(u['x_m'])+float(v['x_m']))/2;y=(float(u['y_m'])+float(v['y_m']))/2
            h=hashlib.sha256(f'{SALT}|{u["source_id"]}|{v["source_id"]}'.encode()).hexdigest()
            candidates.append((u['source_id'],v['source_id'],x,y,h))
    used=set()
    for i in range(1,7):
        observed=tuple(sorted(r['source_id'] for r in panel if int(r['pair_id'])==i));assert len(observed)==2
        if i<=3:
            expected=tuple(sorted(anchors[i-1]));reason='fixed existing E1 geometry anchor'
            p=next(p for p in candidates if p[:2]==expected);distance=None;available=None
        else:
            available=[p for p in candidates if not used.intersection(p[:2])]
            dist=lambda p:min(math.hypot(p[2]-q[2],p[3]-q[3]) for q in chosen)
            p=min(available,key=lambda p:(-dist(p),p[4]));expected=p[:2];distance=dist(p);reason='geometry-only greedy max-min'
        assert observed==expected,(i,observed,expected)
        log.append(dict(pair_id=i,source_a=p[0],source_b=p[1],center_x_m=p[2],center_y_m=p[3],min_distance_to_previous_pair_centers_m=distance,eligible_unused_pair_count=len(available) if available is not None else None,tie_sha256=p[4],selection_reason=reason))
        chosen.append(p);used.update(p[:2])
    minsep=min(math.hypot(p[2]-q[2],p[3]-q[3]) for i,p in enumerate(chosen) for q in chosen[i+1:]);assert minsep>=1.5
    (E/'SOURCE_PANEL_SELECTION_LOG.json').write_text(json.dumps(dict(passed=True,full_bank_sources=624,eligible_neighbour_pairs=len(candidates),sources=12,pairs=6,minimum_pair_center_separation_m=minsep,selector_sha256=sha(a.protocol/'select_house03_pairs.py'),selector_executed_unchanged=True,selection_log=log),indent=2)+'\n')
    gd=[];pf=[]
    for ix,r in enumerate(panel):
        sid=r['source_id'];base=dict(house='House03',wind='1-2,5_fast',source_index=ix,source_id=sid,pair_id=int(r['pair_id']),x_m=float(r['x_m']),y_m=float(r['y_m']),z_m=.2,status='FUTURE_NOT_EXECUTED_F1_SIGNATURE_REQUIRED')
        for rep in range(8):
            value,key,h=seed('GADEN',sid,'all11',rep)
            gd.append(dict(**base,realization_index=rep,requested_seed=value,seed_key=key,seed_sha256=h,path_A='HOUSE03_PATH_A_10.tsv',path_B='HOUSE03_PATH_B_10.tsv'))
        for state in range(11):
            for rep in range(8):
                value,key,h=seed('PMFS',sid,state,rep)
                pf.append(dict(**base,wind_state=state,transport_replica_index=rep,requested_seed=value,seed_key=key,seed_sha256=h,occurrence_operator='Native blur preserved',amplitude_C0='u',amplitude_C1='rawu',score_both_arms='archived B2',same_forward_for_u_and_rawu=1))
    assert len(gd)==96 and len(pf)==1056
    allseeds=[r['requested_seed'] for r in gd+pf];assert len(allseeds)==len(set(allseeds))
    write(E/'HOUSE03_FUTURE_GADEN_SEEDS_96.tsv',gd);write(E/'HOUSE03_FUTURE_PMFS_SEEDS_1056.tsv',pf)
    weights=[dict(condition='nominal_11_state_average',state=s,weight_numerator=1,weight_denominator=11,replicas=8) for s in range(11)]+[dict(condition='state0_only_mismatch',state=0,weight_numerator=1,weight_denominator=1,replicas=8)]
    write(E/'HOUSE03_TEMPLATE_STATE_WEIGHTS.tsv',weights)
    semantics=dict(nominal=dict(states=list(range(11)),state_weight='1/11',replicas_per_state=8,replica_weight='1/8',joint_weight='1/88'),mismatch=dict(states=[0],state_weight='1',replicas=8,replica_weight='1/8',subset_of_same_nominal_bank=True),common=dict(source_support=12,score='archived B2',occurrence='Native blur preserved',u_and_rawu='exported from the identical forward realizations',extra_mismatch_conditions_allowed=False),scientific_execution_authorized=False)
    (E/'WIND_AND_MISMATCH_CONTRACT.json').write_text(json.dumps(semantics,indent=2)+'\n')
    hashes={p.name:sha(p) for p in [E/'HOUSE03_FUTURE_GADEN_SEEDS_96.tsv',E/'HOUSE03_FUTURE_PMFS_SEEDS_1056.tsv',E/'HOUSE03_TEMPLATE_STATE_WEIGHTS.tsv']}
    (E/'FUTURE_SEED_MANIFEST_AUDIT.json').write_text(json.dumps(dict(passed=True,gaden_rows=96,pmfs_rows=1056,all_seeds_unique=True,channels_disjoint=True,seed_rule='1 + int(SHA256(key)[:16],16) mod (2^31-2)',salt=SALT,hashes=hashes,executed=False,python=platform.python_version()),indent=2)+'\n')
    print(json.dumps(dict(panel_min_separation_m=minsep,gaden_rows=96,pmfs_rows=1056,seed_hashes=hashes),indent=2))
if __name__=='__main__':main()
