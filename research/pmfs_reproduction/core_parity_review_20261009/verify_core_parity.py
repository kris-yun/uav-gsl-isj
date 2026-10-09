"""Portable, read-only replay of frozen candidate maps and provenance.
No ROS, CFD, GADEN, candidate propagation, or training is executed.
Independent score re-evaluation is intentionally narrower than full P1 parity.
"""
import argparse,csv,hashlib,json,math,struct
from decimal import Decimal
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parent);ap.add_argument('--out',type=Path,required=True)
a=ap.parse_args();root=a.root;out=a.out;out.mkdir(parents=True,exist_ok=True)
def rows(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=read(root/'SOURCE_MANIFEST.json');before={r['package_path']:sha(root/r['package_path']) for r in manifest}
assert all(before[r['package_path']]==r['sha256'] for r in manifest)
pinned=read(root/'PINNED_SOURCE_BLOB_CHECKS.json')
for r in pinned['checks']:
    data=(root/r['package_path']).read_bytes()
    blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    assert r['verdict']=='PASS' and blob==r['local_git_blob']==r['pinned_git_blob']
tolerance=read(root/'NUMERICAL_CONTRACT.json')
r1=root/'evidence/R1';freeze=read(r1/'r1_scores_frozen_manifest.json')
inputs={f:sha(r1/f) for f in freeze['source_blind_inputs']}
assert inputs==freeze['source_blind_inputs']
snapshot=rows(r1/'measured_map_at_update.csv');events=rows(r1/'measurement_events.csv');candidates=rows(r1/'frozen_candidate_geometry.csv')
assert len(events)==20 and len(candidates)==87 and len(snapshot)==29*38
online_comparisons={f:sha(r1/f)==sha(root/'evidence/online_capture'/f) for f in ('measurement_events.csv','measured_map_at_update.csv','frozen_candidate_geometry.csv','wind_source_update.csv')}
assert all(online_comparisons.values())
wind=rows(r1/'wind_source_update.csv');assert len(wind)==626
free=[r for r in snapshot if r['occupancy']=='Free'];assert len(free)==626
geometry={r['candidate_id']:r for r in candidates}
for r in candidates:
    covered=[c for c in free if int(r['origin_i'])<=int(c['grid_i'])<int(r['origin_i'])+int(r['size_i']) and int(r['origin_j'])<=int(c['grid_j'])<int(r['origin_j'])+int(r['size_j'])]
    assert len(covered)==int(r['size_i'])*int(r['size_j'])
# This calculation uses only C's already frozen official-parameter hit-map and
# archived measured map, never the runtime source coordinates.
native=rows(r1/'R1_arm_C/candidate_scores.csv');assert len(native)==87
result=[];errors=[];normalized_map={};hits=[]
decl=tolerance['score_decimal_export_to_float64']
for r in native:
    cid=r['candidate_id'];p=r1/'R1_arm_C'/r['map_file'];p2=r1/'R1_arm_C_repeat'/r['map_file']
    assert sha(p)==sha(p2)==freeze['arms']['C']['candidate_map_sha256'][cid]
    b=p.read_bytes();assert len(b)==len(snapshot)*4
    field=struct.unpack('<'+str(len(snapshot))+'f',b)
    logscore=0.;prod=1.;zeros=0
    for m in free:
        i=int(m['cell_index']);factor=1-float(m['confidence'])*abs(float(m['probability'])-field[i])*0.3
        assert 0<=factor<=1
        prod*=factor
        if factor==0:zeros+=1
        else:logscore+=math.log(factor)
    score=0. if zeros else math.exp(logscore)
    archived=float(r['source_score']);diff=abs(score-archived);rel=diff/max(abs(score),abs(archived),1e-300)
    assert diff<=decl['abs']+decl['rel']*abs(archived)
    errors.append((diff,rel));hits.append(cid)
    result.append(dict(candidate_id=cid,archived_score=r['source_score'],recomputed_score=score,absolute_error=diff,relative_error=rel,zero_factors=zeros))
    g=geometry[cid]
    for m in free:
        if int(g['origin_i'])<=int(m['grid_i'])<int(g['origin_i'])+int(g['size_i']) and int(g['origin_j'])<=int(m['grid_j'])<int(g['origin_j'])+int(g['size_j']):
            idx=int(m['cell_index']);assert idx not in normalized_map
            normalized_map[idx]=(cid,score,float(m['x']),float(m['y']))
assert len(normalized_map)==626
total=sum(v[1] for v in normalized_map.values())
derived=[dict(cell_index=i,candidate_id=v[0],x=v[2],y=v[3],probability=v[1]/total) for i,v in sorted(normalized_map.items())]
assert abs(sum(r['probability'] for r in derived)-1)<1e-12
raw_scores_sha=sha(r1/'R1_arm_C/candidate_scores.csv');assert raw_scores_sha==freeze['arms']['C']['scores_sha256']
assert sha(r1/'R1_arm_C_repeat/candidate_scores.csv')==raw_scores_sha
archived_audit={}
for line in (r1/'R1_arm_C/source_blind_replay_audit.txt').read_text().splitlines():
    k,v=line.split('=',1);archived_audit[k]=v
assert float(archived_audit['max_live_C_log_odds_diff'])==0 and float(archived_audit['max_live_C_confidence_diff'])==0
scoring_results=dict(candidate_count=87,float32_map_elements_checked=87*len(snapshot),
 max_score_abs=max(x[0] for x in errors),max_score_rel=max(x[1] for x in errors),
 all_87_C_maps_match_frozen_hashes_and_repeats=True,
 normalized_coarse_diagnostic_cells=626,normalized_sum=sum(r['probability'] for r in derived),
 online_native_full_candidate_maps_available=False,online_native_final_posterior_available=False,
 warning='derived coarse map is a scorer normalization diagnostic; NOT the online adaptive PMFS posterior')
# Truth is opened only after recomputation and score-validation.
truth=read(r1/'R1_three_arm_truth_evaluation.json')
truth_id=truth['arms']['C']['truth_candidate_id'];arch={r['candidate_id']:Decimal(r['source_score']) for r in native}
v=arch[truth_id];rank=1+sum(x>v for x in arch.values())+.5*(sum(x==v for x in arch.values())-1)
assert rank==truth['arms']['C']['truth_candidate_rank']==47
estimated={r['candidate_id']:r['recomputed_score'] for r in result};rv=estimated[truth_id]
newrank=1+sum(x>rv for x in estimated.values())+.5*(sum(x==rv for x in estimated.values())-1)
scoring_results.update(truth_rank_native_decimal=rank,truth_rank_float64_recomputed=newrank,rank_equal=(rank==newrank))
for name,data in [('C_SCORE_RECOMPUTATION.csv',result),('C_COARSE_NORMALIZATION_DIAGNOSTIC.csv',derived)]:
    with (out/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
after={r['package_path']:sha(root/r['package_path']) for r in manifest};assert before==after
report=dict(verdict='CORE_PARITY_HOLD',checked_source_files=len(manifest),all_source_hashes_verified=True,
 pinned_official_blobs_verified=len(pinned['checks']),
 frozen_input_hashes_verified=inputs,original_capture_inputs_byte_identical=online_comparisons,
 events=20,coarse_candidates=87,grid=[29,38],free_cells=626,
 reused_hit_map_core_parity=dict(logOdds_max_abs=0,confidence_max_abs=0,origin='archived official C replay audit; same native event/map bytes; not newly executing C++'),
 score_only_current_recomputation=scoring_results,
 first_unverified_layer='raw sensor messages/receipt blocks to delivered native events; for delivered-event core testing, next unverified layer is online candidate simulation maps/RNG state',
 missing_layers=['raw message membership for 20 delivered events','online candidate sampled point sequence and RNG/cache/thread state','online native per-candidate float32 hit maps','online raw candidate scores and final refined source posterior'],
 current_adapter_scope=dict(historical_R2='DEVIATES: EventKeyedTransportRng and different parameters; useful variant/diagnostic',S2_demo='UNKNOWN full P1 equivalence: hand-created events/grid, single update, native navigation not executed',frozen_C_scorer='PASS for fixed saved maps and same delivered observations only'),
 P2='FULL_PIPELINE_HOLD',P3='UNRESOLVED; not run because P1 full parity and legal physical time contract are incomplete',
 raw_evidence_unchanged=True,new_forward_simulations=0,new_gas_simulations=0)
(out/'CORE_PARITY_RESULTS.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
print(json.dumps({'verdict':report['verdict'],'source_hashes':len(manifest),'score':scoring_results},ensure_ascii=False,indent=2))
