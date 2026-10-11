"""Zero-forward diagnostic of frozen 2D maps and B4 raw event labels."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import csv, json, math, struct, hashlib
HERE=Path(__file__).resolve().parent
BASE=HERE.parents[2]
M1=BASE/'outputs/PMFS_B4_M1_SOURCE_REPRESENTATION_20261010'
M2=BASE/'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010'
B4=BASE/'outputs/PMFS_B4_OFFICIAL_TERMINAL_RESUMED_20261010'
def rows(p): return list(csv.DictReader(p.open(encoding='utf8',newline='')))
def js(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]
def safe_log_event(y,p):
    assert y in (0,1) and 0<=p<=1
    if y and p==0 or not y and p==1:return -math.inf
    if y:return math.log(p)
    return math.log1p(-p)
def finite_json(x):
    if isinstance(x,float) and not math.isfinite(x):return '-Infinity' if x<0 else 'Infinity'
    if isinstance(x,dict):return {k:finite_json(v) for k,v in x.items()}
    if isinstance(x,list):return [finite_json(v) for v in x]
    return x
def add_logs(values):return -math.inf if any(v==-math.inf for v in values) else math.fsum(values)
def choose(t,w,larger=True):
    if t==w or (math.isfinite(t) and math.isfinite(w) and abs(t-w)<=1e-12):return 'TIE'
    return 'TRUE' if (t>w if larger else t<w) else 'WRONG'
def write(name, arr):
    p=HERE/name;assert not p.exists(),p
    with p.open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(arr[0]));w.writeheader();w.writerows(arr)

def run():
    contract=js(HERE/'frozen_proxy_contract.json')
    ev=list(csv.reader((B4/'runtime/measurement_events.csv').open(encoding='utf8',newline='')))
    meta=js(M1/'snapshot/metadata.json');input_rows=rows(M1/'snapshot/input.csv')
    width=meta['width'];n=meta['width']*meta['height'];assert n==1530
    ox=f32(meta['origin_x']);oy=f32(meta['origin_y']);cell=f32(meta['cell_size'])
    free=[i for i,r in enumerate(input_rows) if r['occupancy']=='1'];assert len(free)==447
    measured=[1-1/(1+math.exp(float(r['logOdds']))) for r in input_rows]
    confidence=[float(r['confidence']) for r in input_rows]
    events=[]
    for j,e in enumerate(ev):
        # Native Vector2 subtraction/division evaluate in float32 before floor.
        i=math.floor(f32(f32(f32(float(e[4]))-ox)/cell)); k=math.floor(f32(f32(f32(float(e[5]))-oy)/cell));idx=i+k*width
        assert idx in free
        events.append(dict(block_id=j,stop_id=int(e[6]),within_stop=int(e[7]),x=float(e[4]),y=float(e[5]),grid_i=i,grid_j=k,cell_index=idx,event=int(float(e[1])>.1),measured_belief=measured[idx],confidence=confidence[idx]))
    assert len(ev)==50 and all(e['event']==1 for e in events)
    assert len(set(e['cell_index'] for e in events))==10
    per_event=[];per_stop=[];summary=[];native_summary=[];provenance={}
    for bundle,pair in contract['2D_candidates'].items():
        hitmaps={}
        for role,job in pair.items():
            p=M1/'evidence/forwards'/job
            row=rows(p/'candidates.csv')[0]
            blurred=p/row['map_file'];unblurred=blurred.with_name(blurred.stem+'_unblurred.f32')
            provenance[job]={str(q.relative_to(M1)).replace('\\','/'):sha(q) for q in [p/'RESULT.json',p/'candidates.csv',blurred,unblurred]}
            for variant,fp in [('blurred_native_scoring_map',blurred),('unblurred_occupied_cell_frequency',unblurred)]:
                hitmaps[role,variant]=struct.unpack('<'+'f'*n,fp.read_bytes())
                assert all(math.isfinite(v) and 0<=v<=1 for v in hitmaps[role,variant])
            recomputed=math.fsum(math.log(1-.4*confidence[idx]*abs(measured[idx]-hitmaps[role,'blurred_native_scoring_map'][idx])) for idx in free)
            assert math.isclose(recomputed,float(row['logscore']),rel_tol=1e-12,abs_tol=1e-12)
        for variant in contract['2D_map_variants']:
            ht=hitmaps['true_uniform_1x1',variant];hw=hitmaps['wrong_uniform_1x1',variant]
            counts_error=max(abs(v*200-round(v*200)) for idx,v in enumerate(ht) if idx in free) if 'unblurred' in variant else None
            for smooth in ('EXACT_UNSMOOTHED','PREDECLARED_JEFFREYS_200_STEP_SENSITIVITY'):
                sample=[]
                for e in events:
                    idx=e['cell_index'];yt=e['event'];t=ht[idx];w=hw[idx]
                    if smooth!='EXACT_UNSMOOTHED':t=(200*t+.5)/201;w=(200*w+.5)/201
                    lt=safe_log_event(yt,t);lw=safe_log_event(yt,w);bt=(yt-t)**2;bw=(yt-w)**2
                    ft=1-.4*e['confidence']*abs(e['measured_belief']-ht[idx]);fw=1-.4*e['confidence']*abs(e['measured_belief']-hw[idx])
                    r=dict(bundle=bundle,variant=variant,smoothing=smooth,**e,true_frequency_raw=ht[idx],wrong_frequency_raw=hw[idx],true_probability_proxy=t,wrong_probability_proxy=w,true_log_proxy=lt,wrong_log_proxy=lw,true_Brier_proxy=bt,wrong_Brier_proxy=bw,event_log_selected=choose(lt,lw),event_Brier_selected=choose(bt,bw,False),true_native_factor=ft,wrong_native_factor=fw,delta_native_log_wrong_minus_true=math.log(fw)-math.log(ft),meaning='UNQUALIFIED_2D_PID_PROXY_POSTHOC_CONTROL')
                    sample.append(r);per_event.append(r)
                for stop in range(10):
                    ss=[r for r in sample if r['stop_id']==stop];assert len(ss)==5
                    lt=add_logs([r['true_log_proxy'] for r in ss]);lw=add_logs([r['wrong_log_proxy'] for r in ss]);bt=math.fsum(r['true_Brier_proxy'] for r in ss)/5;bw=math.fsum(r['wrong_Brier_proxy'] for r in ss)/5
                    per_stop.append(dict(bundle=bundle,variant=variant,smoothing=smooth,stop_id=stop,cell_index=ss[0]['cell_index'],x=ss[0]['x'],y=ss[0]['y'],true_frequency_raw=ss[0]['true_frequency_raw'],wrong_frequency_raw=ss[0]['wrong_frequency_raw'],blocks=5,true_log_proxy=lt,wrong_log_proxy=lw,true_mean_Brier_proxy=bt,wrong_mean_Brier_proxy=bw,log_selected=choose(lt,lw),Brier_selected=choose(bt,bw,False),native_direct_log_ratio_wrong_over_true=ss[0]['delta_native_log_wrong_minus_true'],meaning='ONE_SPATIAL_STOP_FIVE_CORRELATED_BLOCKS_UNQUALIFIED_PROXY'))
                lt=add_logs([r['true_log_proxy'] for r in sample]);lw=add_logs([r['wrong_log_proxy'] for r in sample]);bt=math.fsum(r['true_Brier_proxy'] for r in sample)/50;bw=math.fsum(r['wrong_Brier_proxy'] for r in sample)/50
                summary.append(dict(bundle=bundle,variant=variant,smoothing=smooth,true_log_proxy=lt,wrong_log_proxy=lw,true_mean_Brier_proxy=bt,wrong_mean_Brier_proxy=bw,log_selected=choose(lt,lw),Brier_selected=choose(bt,bw,False),true_impossible_observed_events=sum(r['true_probability_proxy']==0 for r in sample),wrong_impossible_observed_events=sum(r['wrong_probability_proxy']==0 for r in sample),unblurred_true_max_200_count_rounding_error=counts_error,meaning='RAW_EVENT_SCORE_WITH_2D_FREQUENCY_PROXY_NOT_PHYSICAL_LIKELIHOOD'))
            for scope,idxs in [('ALL_447_FREE_CELLS',free),('DIRECT_10_CELLS_ONCE',sorted(set(e['cell_index'] for e in events))),('RAW_50_EVENT_CELL_FACTORS_CORRELATED',[e['cell_index'] for e in events])]:
                lt=math.fsum(math.log(1-.4*confidence[i]*abs(measured[i]-ht[i])) for i in idxs);lw=math.fsum(math.log(1-.4*confidence[i]*abs(measured[i]-hw[i])) for i in idxs)
                native_summary.append(dict(bundle=bundle,variant=variant,scope=scope,cells_or_repetitions=len(idxs),true_native_log_similarity=lt,wrong_native_log_similarity=lw,wrong_over_true_similarity=math.exp(lw-lt),selected=choose(lt,lw),meaning='NATIVE_SIMILARITY_NOT_INDEPENDENT_LIKELIHOOD'))
    ref={}
    for cid in ('C7','K2'):
        for rep in (0,1):
            p=M2/'native_reference_evidence/realizations'/f'{cid}_{rep}'/'QUERY_OUTPUT.csv'
            ref[cid,rep]={r['query_id']:r for r in rows(p)}
    controls=[];ctlsummary=[]
    for operator in ('ACTUAL_CAPTURED_PID_RECEIVER','NATIVE_ROBOT_GRID_CENTRE_3D_PID'):
        arr=[]
        for e in events:
            j=e['block_id'];idx=e['cell_index'];qid=f'receiver_b{j}_v0' if operator=='ACTUAL_CAPTURED_PID_RECEIVER' else f'grid_b{j}_v0_c{idx}'
            kt=sum(float(ref['C7',rep][qid]['ppm_float32'])>.1 for rep in (0,1));kw=sum(float(ref['K2',rep][qid]['ppm_float32'])>.1 for rep in (0,1));pt=(kt+.5)/3;pw=(kw+.5)/3
            r=dict(operator=operator,**e,true_reference_hit_count=kt,wrong_reference_hit_count=kw,true_probability=(kt+.5)/3,wrong_probability=(kw+.5)/3,true_log=safe_log_event(e['event'],pt),wrong_log=safe_log_event(e['event'],pw),true_Brier=(e['event']-pt)**2,wrong_Brier=(e['event']-pw)**2,scope='QUALIFIED_3D_PID_MARGINAL_OR_DECLARED_SPATIAL_GRID_COUNTERFACTUAL_NOT_JOINT')
            controls.append(r);arr.append(r)
        lt=math.fsum(x['true_log'] for x in arr);lw=math.fsum(x['wrong_log'] for x in arr);bt=math.fsum(x['true_Brier'] for x in arr)/50;bw=math.fsum(x['wrong_Brier'] for x in arr)/50
        ctlsummary.append(dict(operator=operator,true_log=lt,wrong_log=lw,true_mean_Brier=bt,wrong_mean_Brier=bw,log_selected=choose(lt,lw),Brier_selected=choose(bt,bw,False)))
    write('B4_FROZEN_NATIVE_RECEIVER_GRID.csv',events)
    write('M1_2D_PROXY_PER_EVENT.csv',per_event)
    write('M1_2D_PROXY_PER_STOP.csv',per_stop)
    write('M1_2D_PROXY_SCORE_SUMMARY.csv',summary)
    write('M1_NATIVE_SIMILARITY_SCOPE_SUMMARY.csv',native_summary)
    write('M2_3D_RECEIVER_CONTROLS_PER_EVENT.csv',controls)
    write('M2_3D_RECEIVER_CONTROLS_SUMMARY.csv',ctlsummary)
    result=dict(status='FROZEN_MAP_READONLY_PROXY_FACTORIAL_COMPLETED',new_forward_calls=0,new_ROS_nodes=0,new_GADEN_realizations=0,contract_sha256=sha(HERE/'frozen_proxy_contract.json'),source_map_provenance=provenance,proxy_summary=summary,native_summary=native_summary,M2_3D_controls=ctlsummary,physical_PID_probability_qualification='2D_NOT_QUALIFIED_PROXY_ONLY',observed_map_causal_claim='Does not prove accumulated map is unnecessary for full B4 failure. Can show bypassing measured map does not remove wrong ordering under this frozen 2D-frequency proxy.',model_dimension_cause='HOLD_POINT_VS_UNIFORM_AREA_RELEASE_RATE_TIME_HEIGHT_OCCUPANCY_VS_PID_OPERATOR_CONFOUNDERS',limitations=['two recorded PMFS RNG states are not independent physical realizations','50 labels from 10 correlated stops','blurred 200-step smoothing is a pseudo-count transform, not a Beta posterior from integer counts','2D uses 1x1 uniform releases; M2 uses precise 3D points','2D centre-occupied frequency has no concentration unit or matching PID sensor operator','no new localization, posterior, seed selection or reference added'])
    p=HERE/'PROXY_FACTORIAL_RESULT.json';assert not p.exists();p.write_text(json.dumps(finite_json(result),ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(finite_json(dict(proxy_summary=summary,M2_3D_controls=ctlsummary)),ensure_ascii=False,indent=2))

if __name__=='__main__':run()
