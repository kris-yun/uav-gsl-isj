#!/usr/bin/env python3
import csv, hashlib, json, math, re, shutil
from pathlib import Path
import numpy as np
root=Path('/home/zyc/wind_alignment_d0_20260926')
out=root/'inputs'; assert not out.exists()
out.mkdir(); (out/'historical_maps').mkdir()
historical=Path('/home/zyc/native_pmfs_recovery_v1/runs/R1_R2_SOURCE_CORRECTED_House01_S0_20260923')
manifest=json.loads((historical/'r1_scores_frozen_manifest.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name in ('measurement_events.csv','measured_map_at_update.csv','frozen_candidate_geometry.csv','wind_source_update.csv'):
    p=historical/name; assert sha(p)==manifest['source_blind_inputs'][name],name
    shutil.copyfile(p,out/name)
shutil.copyfile(historical/'r1_scores_frozen_manifest.json',out/'r1_scores_frozen_manifest.json')
scores=historical/'R1_arm_C/candidate_scores.csv'
assert sha(scores)==manifest['arms']['C']['scores_sha256']
shutil.copyfile(scores,out/'C_candidate_scores.csv')
candidates=list(csv.DictReader(scores.open(newline='')))
assert len(candidates)==87
for r in candidates:
    p=historical/'R1_arm_C'/r['map_file']
    assert sha(p)==manifest['arms']['C']['candidate_map_sha256'][r['candidate_id']]
    shutil.copyfile(p,out/'historical_maps'/p.name)
binary=Path('/home/zyc/native_pmfs_recovery_v1/install/gsl_server/lib/gsl_server/native_pmfs_r1_forward_replay')
assert sha(binary)==manifest['replay_binary_sha256']
sequences=list(csv.DictReader((root/'code/event_state_sequences.csv').open(newline='')))
events=list(csv.DictReader((out/'measurement_events.csv').open(newline='')))
assert len(sequences)==len(events)==20
for s,e in zip(sequences,events):
    assert int(s['unique_state_sequences'])==1 and int(s['event_id'])==int(e['event_id'])
    for a,b in (('robot_x','robot_x'),('robot_y','robot_y'),('hit','hit'),('wind_speed_event','wind_speed'),('wind_direction_event','wind_direction')):
        assert abs(float(s[a])-float(e[b]))<=1e-12
    assert all(0<=int(s[f'state_{j}'])<=10 for j in range(1,11))
trace=list(csv.DictReader(Path('/home/zyc/wind_contract_identity_audit_20260926/evidence/trace_state_diagnostic.csv').open(newline='')))
recovery=[]
for event in sequences:
    samples=[r for r in trace if r['site']=='ABCD'[(int(event['event_id'])-1)//5]]
    groups=set(); matched=0
    for start in range(len(samples)-9):
        block=samples[start:start+10]
        if int(block[-1]['step'])-int(block[0]['step'])!=9:continue
        speed_sum=np.float32(0); cx=np.float32(0); cy=np.float32(0)
        for r in block:
            u=float(r['exact_u']); v=float(r['exact_v'])
            angle=float(np.float32(math.atan2(v,u)))
            speed_sum=np.float32(float(speed_sum)+math.hypot(u,v))
            cx=np.float32(float(cx)+math.cos(angle)); cy=np.float32(float(cy)+math.sin(angle))
        speed=float(np.float32(speed_sum/np.float32(10)))
        direction=float(np.float32(math.atan2(float(cy),float(cx))))
        angle_error=abs((direction-float(event['wind_direction_event'])+math.pi)%(2*math.pi)-math.pi)
        if abs(speed-float(event['wind_speed_event']))<=1e-6 and angle_error<=1e-6:
            groups.add(tuple(int(r['matched_file_id']) for r in block)); matched+=1
    expected=tuple(int(event[f'state_{j}']) for j in range(1,11))
    assert groups=={expected}, ('sequence not unique',event['event_id'],groups,expected)
    recovery.append({'event_id':int(event['event_id']),'matching_windows':matched,'unique_state_sequences':len(groups),'state_sequence':list(expected)})
(out/'sequence_verification.json').write_text(json.dumps(recovery,indent=2)+'\n')

windrows=list(csv.DictReader((out/'wind_source_update.csv').open(newline='')))
assert len(windrows)==626
states=root/'state_inputs'; states.mkdir()
wind_dir=Path('/mnt/hgfs/workspace/GADEN_files/scenarios/House01/wind_simulations/2,4-1_fast')
field_manifest=[]
for state in range(11):
    p=wind_dir/f'2,4-1_fast_{state}.csv'; positions=[]; vectors=[]
    with p.open() as f:
        reader=csv.reader(f); next(reader)
        for row in reader:
            if len(row)>=6:
                vectors.append([float(row[0]),float(row[1]),float(row[2])]);positions.append([float(row[3]),float(row[4]),float(row[5])])
    pos=np.array(positions);vec=np.array(vectors); output=[]; indices=[]
    for r in windrows:
        q=np.array([float(r['x']),float(r['y']),0.3])
        k=int(np.argmin(np.linalg.norm(pos-q[np.newaxis,:],axis=1)))
        new=dict(r); u,v=map(float,np.float32(vec[k,:2]));new.update(internal_u=repr(u),internal_v=repr(v),magnitude=repr(math.hypot(u,v)))
        output.append(new);indices.append(k)
        if state==0:
            q[2]=0.0;k0=int(np.argmin(np.linalg.norm(pos-q[np.newaxis,:],axis=1)))
            assert np.float32(vec[k0,0])==np.float32(float(r['internal_u']))
            assert np.float32(vec[k0,1])==np.float32(float(r['internal_v']))
    target=states/f'state_{state}.csv'
    with target.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(windrows[0]));writer.writeheader();writer.writerows(output)
    field_manifest.append({'state':state,'z':0.3,'asset':str(p),'asset_sha256':sha(p),'field_sha256':sha(target),'nearest_csv_row_indices':indices})
    print('WIND_FIELD_READY',state,flush=True)
(states/'field_manifest.json').write_text(json.dumps(field_manifest,indent=2,sort_keys=True)+'\n')
print('INPUTS_FROZEN_AND_20_SEQUENCE_IDENTITIES_VERIFIED',flush=True)
