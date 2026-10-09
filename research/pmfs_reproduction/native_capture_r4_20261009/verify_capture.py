"""R4 portable evidence verification; only stdlib, no ROS or unknown program execution.
Usage: python verify_capture.py AUDIT_DIRECTORY
"""
import csv,json,struct,math,hashlib,sys
from pathlib import Path
from decimal import Decimal,localcontext

ROOT=Path(sys.argv[1]).resolve();E=ROOT/'evidence';N=E/'native';F=E/'offline_forward_result';C=E/'offline_control_result'
P=json.loads((E/'input/PARAMETERS.json').read_text());T=P['tolerances'];CHECKS=[]
def rows(path):
    with path.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def binary(path,code,n=None):
    b=path.read_bytes();s=struct.calcsize(code);assert len(b)%s==0,str(path)
    a=struct.unpack('<'+str(len(b)//s)+code,b)
    if n is not None:assert len(a)==n,str(path)
    assert all(math.isfinite(x) for x in a),str(path)
    return a
def passed(layer,**facts):CHECKS.append(dict(layer=layer,verdict='PASS',**facts))
def difference(a,b,abs_tol,rel_tol=0):
    assert len(a)==len(b)
    errors=[abs(x-y) for x,y in zip(a,b)]
    assert all(e<=abs_tol+rel_tol*abs(y) for e,y in zip(errors,b)),max(errors)
    return max(errors,default=0)
def key(r):return tuple(int(r[k]) for k in ['origin_i','origin_j','size_i','size_j'])
def cells(k):
    x,y,w,h=k
    return [i+29*j for j in range(y,y+h) for i in range(x,x+w)]
def relative(x,y):return abs(x-y)/max(abs(y),Decimal('1e-1000'))

try:
    native=json.loads((N/'NATIVE_COMPLETE.json').read_text());driver=json.loads((E/'driver/DRIVER_RESULT.json').read_text())
    assert native['native_source_updates']==driver['native_successful_updates']==1
    assert driver['execution']=='COMPLETE_NATIVE_FORWARD_AND_CLEAN_CONTROL'
    schema=json.loads((N/'READY_SCHEMA.json').read_text());pre=json.loads((E/'driver/PRE_RUN_SCHEMA_VALIDATION.json').read_text())
    assert schema['pid']==native['pid']==pre['schema']['pid'];assert schema['threads']==1
    assert (N/'SOURCE_UPDATE_STARTED.txt').exists() and (N/'PRE_UPDATE_VALIDATION.json').exists()
    assert pre['preflight_ns']<int((N/'SOURCE_UPDATE_STARTED.txt').read_text())
    for name,digest in pre['input_SHA256'].items():assert hashlib.sha256((E/'input'/name).read_bytes()).hexdigest()==digest
    passed('native_execution_and_pre_run_contract',native_updates=1,pid=native['pid'],input_class=P['input_class'],truth_used=False)
    occ=rows(E/'input/occupancy.csv');assert len(occ)==1102
    free=[r['occupancy']=='Free' for r in occ];assert sum(free)==626
    coarse=rows(N/'coarse_tree.csv');assert len(coarse)==schema['coarse_leaves']
    coverage=[0]*1102
    for r in coarse:
        assert r['value']=='1' and r['has_children']=='0' and r['parent_id']=='ROOT'
        x,y,w,h=key(r);assert 0<=x<x+w<=29 and 0<=y<y+h<=38 and 1<=w<=5 and 1<=h<=5
        for i in cells(key(r)):coverage[i]+=1
    assert coverage==[int(x) for x in free]
    passed('actual_native_candidate_forest',coarse_leaves=len(coarse),free_cells=626,complete_nonoverlapping_coverage=True,replay_uses_captured_order=True)
    raw=rows(N/'raw_consumed_messages.csv');assert len(raw)==18
    cdr=[json.loads(x) for x in (N/'raw_ros_cdr.jsonl').read_text().splitlines()];assert len(cdr)==18
    max_age=max((int(r['receipt_ns'])-int(r['stamp_ns']))/1e9 for r in raw)
    assert 0<=max_age<T['message_age_s']
    for r,w in zip(raw,cdr):
        assert all(v!='' for v in r.values());assert r['frame_id']=='r4_sensor'
        assert int(w['receipt_ns'])==int(r['receipt_ns']) and int(w['block_id'])==int(r['block_id'])
        assert len(bytes.fromhex(w['cdr_hex']))>0
        assert float(r['pose_drift_xy_m'])<T['position_m'] and float(r['pose_drift_yaw_rad'])<T['angle_rad']
        if r['kind']=='wind':
            assert int(r['returned_TF_stamp_ns'])==int(r['stamp_ns'])
            assert abs(math.atan2(math.sin(float(r['map_TO_direction'])-float(r['local_direction'])-float(r['sample_yaw'])),math.cos(float(r['map_TO_direction'])-float(r['local_direction'])-float(r['sample_yaw']))))<T['angle_rad']
    assert len(json.loads((E/'driver/TF_AT_SAMPLE_AND_RECEIPT.json').read_text()))==18
    gmrf=(E/'driver/GMRF_consumed.csv').read_text().splitlines();assert len(gmrf)==9
    theta=math.atan2(P['measured_wind_v'],P['measured_wind_u'])
    max_snap=0
    for number,line in enumerate(gmrf,1):
        r=line.split(',');assert r[8]==r[9]=='1' and r[11]=='0' and int(r[12])==number
        assert math.hypot(float(r[6])-P['robot_x'],float(r[7])-P['robot_y'])<T['position_m']
        max_snap=max(max_snap,math.hypot(float(r[14])-float(r[6]),float(r[15])-float(r[7])))
        assert max_snap<=float(occ[0]['cell_size'])/math.sqrt(2)+1e-6
        assert abs(math.atan2(math.sin(float(r[5])-theta),math.cos(float(r[5])-theta)))<T['angle_rad']
    passed('raw_ROS_clock_TF_and_wind_interfaces',gas_members=9,wind_members=9,gmrf_members=9,max_message_age_s=max_age,max_GMRF_cell_center_quantization_m=max_snap,static_pose=True)
    events=rows(N/'measurement_events.csv');replayed=rows(F/'measurement_blocks.csv');assert len(events)==len(replayed)==3
    for a,b in zip(events,replayed):
        for k in ['block_id','gas_members','wind_members','hit']:assert a[k]==b[k]
        for k in ['concentration','wind_speed','wind_direction']:assert abs(float(a[k])-float(b[k]))<=T['measurement_abs']
    passed('raw_to_StopAndMeasure_blocks',blocks=3,hit_sequence=[int(r['hit']) for r in events])
    hit_error=0
    for name in ['hit_before_update.csv']+['hit_after_block_'+str(i)+'.csv' for i in range(1,4)]:
        a,b,c=rows(N/name),rows(F/name),rows(C/name);assert len(a)==len(b)==len(c)==1102
        for aa,bb,cc in zip(a,b,c):
            for k in aa:hit_error=max(hit_error,difference([float(aa[k])],[float(bb[k])],T['measurement_abs']),difference([float(aa[k])],[float(cc[k])],T['measurement_abs']))
    passed('measured_hit_probability_grids',max_abs=hit_error)
    wr=rows(E/'input/wind.csv');expected=[]
    for r in wr:expected.extend(struct.unpack('<2f',struct.pack('<2f',float(r['u']),float(r['v']))))
    difference(binary(N/'forward_wind_snapshot.f32','f',2204),expected,0)
    passed('forward_wind_grid',bit_exact=True,source='static numerical fixture; independent of measured GMRF output')
    candidates=rows(N/'candidates.csv');fscore=rows(F/'candidate_scores.csv');assert len(candidates)==len(fscore)==native['candidate_simulations']
    assert [key(x) for x in candidates[:len(coarse)]]==[key(x) for x in coarse]
    assert len({r['candidate_id'] for r in candidates})==len(candidates)
    binary(N/'gaussian_cache.f32','f',2500);gi=rows(N/'gaussian_initial.csv');assert len(gi)==1
    assert (N/'rng_before_update.txt').read_text().strip()==candidates[0]['rng_before']
    measured=rows(N/'hit_before_update.csv');rawgrid=[Decimal(0)]*1102
    maperror=scoreerror=decimalerror=0;pointcount=0
    with localcontext() as ctx:
        ctx.prec=60
        for r,s in zip(candidates,fscore):
            assert r['candidate_id']==s['candidate_id'] and r['serial']==s['serial']
            assert s['points_used']==r['point_count'] and s['gaussian_index_after']==r['gaussian_index_after']
            assert all(r[k] for k in ['rng_before','rng_after','gaussian_index_before','gaussian_index_after'])
            pts=binary(N/r['points_file'],'f',int(r['point_count'])*2);pointcount+=len(pts)//2
            x,y,w,h=key(r);m=occ[0];originx=float(m['origin_x']);originy=float(m['origin_y']);step=float(m['cell_size'])
            # World limits are float32 products/additions in the upstream grid; use cell-scale slack only for serialization rounding.
            slack=2e-6
            assert all(originx+x*step-slack<=px<=originx+(x+w)*step+slack and originy+y*step-slack<=py<=originy+(y+h)*step+slack for px,py in zip(pts[::2],pts[1::2]))
            for suffix in ['.f32','_unblurred.f32']:
                a=binary(N/'maps'/(r['candidate_id']+suffix),'f',1102);b=binary(F/'maps'/(r['candidate_id']+suffix),'f',1102)
                maperror=max(maperror,difference(a,b,T['forward_f32_abs'],T['forward_f32_rel']))
            native_score=Decimal(r['score']);forward_score=Decimal(s['score']);re=relative(forward_score,native_score);assert re<=Decimal(str(T['score_long_double_rel'])),(r['candidate_id'],str(re));scoreerror=max(scoreerror,float(re))
            product=Decimal(1);a=binary(N/r['map_file'],'f',1102)
            for i,hp in enumerate(measured):
                if not free[i]:continue
                probability=1-1/(1+math.exp(float(hp['log_odds'])))
                frequency=1-abs(probability-a[i])*P['simulation']['sourceDiscriminationPower']
                confidence=float(hp['confidence']);factor=1 if confidence<0 or math.isnan(confidence) else 1+(frequency-1)*min(1.,confidence)
                product*=Decimal.from_float(factor)
            re=relative(product,native_score);assert re<=Decimal(str(T['score_long_double_rel'])),(r['candidate_id'],str(re));decimalerror=max(decimalerror,float(re))
            for i in cells(key(r)):rawgrid[i]=native_score
        recorded=[Decimal(r['score']) for r in rows(N/'raw_cell_scores.csv')];assert len(recorded)==1102
        assert rawgrid==recorded
        normalization=sum(x for x,f in zip(recorded,free) if f);native_norm=Decimal((N/'normalization.txt').read_text().strip());assert relative(normalization,native_norm)<=Decimal(str(T['score_long_double_rel']))
        independently=[float(x/normalization) if f else 0. for x,f in zip(recorded,free)]
    passed('conditional_forward_core_replay',candidate_simulations=len(candidates),actual_source_points=pointcount,max_hit_map_abs=maperror,max_score_relative=scoreerror,uses_native_points_and_noise=True)
    passed('independent_score_and_raw_grid_replay',max_decimal_score_relative=decimalerror,region_overwrites_equal=True)
    posterior=binary(N/'posterior.f64','d',1102);control=binary(C/'posterior.f64','d',1102)
    independent_error=difference(posterior,independently,T['posterior_f64_abs']);control_error=difference(posterior,control,T['posterior_f64_abs'])
    assert abs(sum(posterior)-1)<T['posterior_f64_abs'];assert all((p>=0 if f else p==0) for p,f in zip(posterior,free))
    ranks=lambda a:sorted((i for i,f in enumerate(free) if f),key=lambda i:(-a[i],i))
    assert ranks(posterior)==ranks(control)==ranks(independently)
    passed('final_posterior_and_ranking',max_independent_abs=independent_error,max_clean_control_abs=control_error,all_626_free_cell_ranks_equal=True,probability_sum=sum(posterior))
    variance_error=difference(binary(N/'variance.f64','d',1102),binary(C/'variance.f64','d',1102),T['posterior_f64_abs'])
    cmerror=0
    for r in coarse:cmerror=max(cmerror,difference(binary(N/'maps'/(r['node_id']+'.f32'),'f',1102),binary(C/'coarse_maps'/(r['node_id']+'.f32'),'f',1102),T['forward_f32_abs'],T['forward_f32_rel']))
    passed('passive_instrumentation_same_candidate_clean_control',max_variance_abs=variance_error,max_coarse_map_abs=cmerror,uses_actual_native_forest=True)
    tree=rows(N/'final_tree.csv');byid={r['node_id']:r for r in tree};assert len(byid)==len(tree)
    final=[r for r in tree if r['has_children']=='0'];cover=[0]*1102
    for r in final:
        assert r['node_id'] in {c['candidate_id'] for c in candidates}
        for i in cells(key(r)):cover[i]+=1
    assert cover==[int(f) for f in free]
    passed('captured_final_refinement_tree',nodes=len(tree),final_leaves=len(final),complete_nonoverlapping_coverage=True)
    mapindex=ranks(posterior)[0];m=occ[0];step=float(m['cell_size'])
    result=dict(verdict='CORE_UPDATE_PARITY_PASS',input_class=P['input_class'],checks=CHECKS,native_updates=1,coarse_leaves=len(coarse),candidate_simulations=len(candidates),final_leaves=len(final),MAP=dict(cell_index=mapindex,i=mapindex%29,j=mapindex//29,x=float(m['origin_x'])+(mapindex%29+.5)*step,y=float(m['origin_y'])+(mapindex//29+.5)*step,probability=posterior[mapindex],ground_truth_not_supplied=True),full_pipeline='HOLD',physical_model_mismatch='UNRESOLVED',historical_adapter='NOT_QUALIFIED_BY_THIS_FIXTURE',boundaries=['conditional parity for captured candidate tree, samples and RNG, one thread only','controlled synthetic ROS input; not C1/B1 or real gas localization','native quadtree greedy hash-pointer fusion is not asserted deterministic across processes'])
except Exception as e:
    result=dict(verdict='CORE_UPDATE_PARITY_FAIL',checks=CHECKS,first_failed_layer_after=CHECKS[-1]['layer'] if CHECKS else 'none',error=repr(e))
(ROOT/'R4_CORE_PARITY_RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
sys.exit(0 if result['verdict']=='CORE_UPDATE_PARITY_PASS' else 1)
