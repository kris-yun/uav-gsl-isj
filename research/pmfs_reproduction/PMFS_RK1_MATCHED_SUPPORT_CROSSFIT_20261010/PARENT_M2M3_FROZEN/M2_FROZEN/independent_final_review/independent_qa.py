"""Independent read-only scalar recalc of M2 scores and map statistics.
Writes only this separate review directory; never starts ROS or simulations.
"""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import csv, json, math, hashlib, importlib.util
HERE=Path(__file__).resolve().parent
BASE=HERE.parents[2]
ROOT=BASE/'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010'
def js(p):return json.loads(p.read_text(encoding='utf8'))
def rows(p):return list(csv.DictReader(p.open(encoding='utf8',newline='')))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def near(a,b,abs_tol=1e-12):
    assert math.isfinite(float(a)) and math.isfinite(float(b))
    assert math.isclose(float(a),float(b),rel_tol=2e-12,abs_tol=abs_tol),(a,b)
def select(a,b,larger=True):
    if abs(a-b)<=1e-12:return 'TIE'
    return 'C7' if (a>b if larger else a<b) else 'K2'
def compare_table(path, expected):
    saved=rows(path);assert len(saved)==len(expected),(path,len(saved),len(expected))
    diff=0.
    for s,e in zip(saved,expected):
        assert set(s)==set(e),(path,'columns')
        for k,x in e.items():
            if isinstance(x,(int,float)) and not isinstance(x,bool):
                near(s[k],x,abs_tol=1e-14 if 'similarity' in k else 1e-12)
                diff=max(diff,abs(float(s[k])-float(x)))
            else:assert s[k]==str(x),(path,k,s[k],str(x))
    return dict(rows=len(saved),maximum_abs_numeric_difference=diff)

contract=js(ROOT/'frozen_contract.json')
assert contract['maximum_new_GADEN_realizations']==8
assert contract['reference_split']==[0,1] and contract['heldout_split']==[2,3]
assert contract['smoothing']['alpha']==contract['smoothing']['beta']==.5
assert len({tuple(j['seeds']) for j in contract['jobs']})==8
assert len(set(s for j in contract['jobs'] for s in j['seeds']))==16
assert contract['extra_2D_candidate_forwards']==0
lock=js(ROOT/'POST_SCORE_PRE_UNBLIND_SHA256.json')
assert all(sha(ROOT/k)==v for k,v in lock.items())
inputs=[js(ROOT/f'source_blind_inputs/branch_{b}.json') for b in (0,1)]
assert inputs[0]==inputs[1]
assert all(set(x)=={'reference_events','observation_events'} for x in inputs)
assert set(inputs[0]['reference_events'])=={'C7','K2'}
assert set(inputs[0]['observation_events'])=={'O0','H101','H102','H103','H104'}
lock_in=js(ROOT/'SOURCE_BLIND_PRE_SCORE_LOCK.json')
for b,record in enumerate(lock_in['inputs']):
    assert sha(ROOT/f'source_blind_inputs/branch_{b}.json')==record['input_sha256']
    assert sha(ROOT/'score_source_blind.py')==record['scorer_sha256']
sc=[js(ROOT/f'SOURCE_BLIND_SCORES_BRANCH_{b}.json') for b in (0,1)]
assert sc[0]==sc[1]
independent_scores={}
for cid,reps in inputs[0]['reference_events'].items():
    assert len(reps)==2 and all(len(x)==50 for x in reps)
    p=[(reps[0][j]+reps[1][j]+.5)/3 for j in range(50)]
    assert sc[0]['candidate_reference_probabilities'][cid]==p
    for task,y in inputs[0]['observation_events'].items():
        assert len(y)==50 and all(x in (0,1) for x in y)
        logs=[math.log(q) if z else math.log1p(-q) for z,q in zip(y,p)]
        briers=[(z-q)**2 for z,q in zip(y,p)]
        wanted={'log_sum':math.fsum(logs),'log_mean':math.fsum(logs)/50,'brier_sum':math.fsum(briers),'brier_mean':math.fsum(briers)/50,'per_block_log':logs,'per_block_brier':briers,'per_stop_log_mean':[math.fsum(logs[j:j+5])/5 for j in range(0,50,5)],'per_stop_brier_mean':[math.fsum(briers[j:j+5])/5 for j in range(0,50,5)]}
        for k,v in wanted.items():
            if isinstance(v,list):
                for a,b in zip(sc[0]['tasks'][task][cid][k],v):near(a,b)
            else:near(sc[0]['tasks'][task][cid][k],v)
        independent_scores.setdefault(task,{})[cid]=wanted
labels=js(ROOT/'HELDOUT_GENERATOR_MAPPING_ANALYSIS_ONLY.json')
winners={task:dict(log=select(s['C7']['log_sum'],s['K2']['log_sum']),Brier=select(s['C7']['brier_mean'],s['K2']['brier_mean'],False)) for task,s in independent_scores.items()}
assert winners['O0']=={'log':'C7','Brier':'C7'}
assert all(winners[t]['log']==labels[t] and winners[t]['Brier']==labels[t] for t in labels)

data=rows(ROOT/'native_reference_evidence/FROZEN_INPUT.csv')
free=[i for i,r in enumerate(data) if r['occupancy']=='1'];assert len(free)==447 and len(data)==1530
observed=[1.-1./(1.+math.exp(float(r['logOdds']))) for r in data]
physical={};aligned={};all_events={};bank_rowcounts={};physical_lineages={};receiver_records={}
for cid in ('C7','K2'):
    for rep in range(4):
        name=f'{cid}_{rep}';bank=ROOT/'native_reference_evidence/realizations'/name
        q=rows(bank/'QUERY_OUTPUT.csv');lookup={r['query_id']:r for r in q};assert len(q)==len(lookup)==22848
        receiver_records[name]={key:row for key,row in lookup.items() if key.startswith('receiver_')}
        bank_rowcounts[name]=len(q)
        all_events[name]=[int(float(lookup[f'receiver_b{j}_v0']['ppm_float32'])>.1) for j in range(50)]
        for key,row in lookup.items():
            value=float(row['ppm_float32']);assert math.isfinite(value) and value>=0
            if key.startswith('grid_b40_v0'):
                alt=lookup[key.replace('_v0_','_v1_')]
                assert alt['frame']==row['frame'] and alt['ppm_float32']==row['ppm_float32']
        assert lookup['receiver_b40_v0']['frame']==lookup['receiver_b40_v1']['frame']
        assert lookup['receiver_b40_v0']['ppm_float32']==lookup['receiver_b40_v1']['ppm_float32']
        physical[name]={i:sum(float(lookup[f'grid_b{j}_v0_c{i}']['ppm_float32'])>.1 for j in range(50))/50 for i in free}
        amap=rows(ROOT/'native_aligned_maps'/name/'map.csv');assert len(amap)==1530
        assert all(int(r['cell_index'])==i for i,r in enumerate(amap))
        aligned[name]=[float(r['probability']) for r in amap]
        for i in free:near(aligned[name][i],1.-1./(1.+math.exp(float(amap[i]['logOdds']))))
        timeline=rows(bank/'PHYSICAL_FRAME_TIME.csv')
        lineage=rows(bank/'QUERY_PHYSICAL_LINEAGE.csv');assert len(lineage)==51
        # Qualification of floor-frame temporal mapping without filename-time arithmetic.
        for r in lineage:
            assert float(r['selected_frame_physical_s']) <= float(r['target_physical_s']) < float(r['next_frame_physical_s'])
            idx=int(r['selected_frame']);assert int(timeline[idx]['frame'])==idx
            near(r['selected_frame_physical_s'],timeline[idx]['physical_snapshot_time_s'])
            near(r['next_frame_physical_s'],timeline[idx+1]['physical_snapshot_time_s'])
            assert int(r['wind_index'])==int(timeline[idx]['wind_index_at_save'])==10
        physical_lineages[name]=True
        for rep_id in (0,1):
            if rep==rep_id:assert all_events[name]==inputs[0]['reference_events'][cid][rep]
for task,cid in labels.items():
    rep=2 if task in ('H101','H102') else 3
    assert all_events[f'{cid}_{rep}']==inputs[0]['observation_events'][task]
assert inputs[0]['observation_events']['O0']==[1]*50

mapstats={};percell_saved=rows(ROOT/'SAME_3D_BANK_PER_CELL_COMPARISON.csv');assert len(percell_saved)==894
pcm={(r['candidate_id'],int(r['cell_index'])):r for r in percell_saved}
for cid in ('C7','K2'):
    freq={i:(physical[f'{cid}_0'][i]+physical[f'{cid}_1'][i])/2 for i in free}
    meanmap={i:(aligned[f'{cid}_0'][i]+aligned[f'{cid}_1'][i])/2 for i in free}
    factors={i:1.-.4*min(max(float(data[i]['confidence']),0.),1.)*abs(observed[i]-freq[i]) for i in free}
    logsim=math.fsum(math.log(factors[i]) for i in free)
    mse=math.fsum((observed[i]-meanmap[i])**2 for i in free)/447
    fmse=math.fsum((observed[i]-freq[i])**2 for i in free)/447
    mapstats[cid]=dict(unmatched_log_similarity=logsim,unmatched_similarity=math.exp(logsim),aligned_MSE=mse,raw_frequency_MSE=fmse)
    for i in free:
        r=pcm[cid,i]
        for key,value in {'observed_belief':observed[i],'confidence':float(data[i]['confidence']),'reference_raw_hit_frequency':freq[i],'reference_aligned_belief':meanmap[i],'unmatched_factor':factors[i],'log_unmatched_factor':math.log(factors[i]),'aligned_squared_difference':(observed[i]-meanmap[i])**2}.items():near(r[key],value)
rawselect=select(mapstats['C7']['unmatched_log_similarity'],mapstats['K2']['unmatched_log_similarity'])
alignselect=select(mapstats['C7']['aligned_MSE'],mapstats['K2']['aligned_MSE'],False)
assert rawselect==alignselect=='C7'

# Read-only replay of root helper to check every derived table, separate from above scalar logic.
spec=importlib.util.spec_from_file_location('analyse_discrimination',ROOT/'analyse_discrimination.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
evaluation,*tables=m.analyse(ROOT)
checks={name:compare_table(ROOT/name,table) for name,table in zip(['SOURCE_DISCRIMINATION_PER_REALIZATION.csv','REALIZATION_EVENT_COUNTS.csv','ALIGNED_MAP_HELDOUT_COMPARISON.csv','SAME_3D_BANK_UNMATCHED_ALIGNED_COMPARISON.csv','SAME_3D_BANK_PER_CELL_COMPARISON.csv','RAW_CONCENTRATION_INFORMATION_ENHANCED.csv'],tables)}
assert js(ROOT/'DISCRIMINATION_RESULT.json')==evaluation
rawpred=rows(ROOT/'RAW_SOURCE_CONDITIONED_BLOCK_PREDICTIONS.csv');assert len(rawpred)==800
for r in rawpred:
    q=ROOT/'native_reference_evidence/realizations'/r['bank_id']/'QUERY_OUTPUT.csv'
    # branch equivalence already established; both saved branch tables must agree with independent events.
    j=int(r['block_id']);assert int(r['block_hit'])==all_events[r['bank_id']][j]
    assert int(r['consumed_members'])==1
    bid=int(r['membership_branch']); key=f'receiver_b{j}_v{bid}'
    # For unambiguous blocks, both reported scoring branches intentionally use v0.
    if key not in receiver_records[r['bank_id']]: key=f'receiver_b{j}_v0'
    raw=receiver_records[r['bank_id']][key]
    assert float(r['PID_ppm'])==float(raw['ppm_float32'])
    assert int(r['frame'])==int(raw['frame'])
    for axis in ('x','y','z'): assert float(r['sensor_'+axis])==float(raw[axis])
local=BASE/'work/pmfs_m2_observation_discrimination_20261010/scoring_contract'
coverage=[]
for p in sorted(local.iterdir()):
    if not p.is_file():continue
    target=ROOT/'observation_lineage'/p.name
    elsewhere=ROOT/p.name
    coverage.append(dict(file=p.name,copied_to_observation_lineage=target.exists(),identical_if_copied=(sha(target)==sha(p)) if target.exists() else None,root_level_copy=elsewhere.exists(),root_level_identical=(sha(elsewhere)==sha(p)) if elsewhere.exists() else None))
result=dict(verdict='PASS_INDEPENDENT_ARITHMETIC_AND_SCOPE_QA_WITH_REPORTED_LIMITATIONS',actual_actions='local read-only raw evidence and independent scalar arithmetic; no simulator, ROS, forwards or navigation',source_blind_scores=winners,heldout_log_correct=4,heldout_Brier_correct=4,heldout_n=4,reference_per_candidate=2,mapstats=mapstats,unmatched_selected=rawselect,aligned_selected=alignselect,E1='NOT_ESTABLISHED_NO_SELECTION_FLIP_ON_SAME_3D_BANK',E2='HOLD_NO_COMPARABLE_2D_PID_OPERATOR',new_localization_gain='NOT_TESTED',independent_physical_model_validation='NOT_DONE_SAME_GADEN',map_anchor_max_abs=js(ROOT/'event_map_anchor/OBSERVED_MAP_ANCHOR_COMPARISON.json')['max_absolute_difference'],query_rows_by_bank=bank_rowcounts,branch_equivalence='PASS_BOTH_RECEPTOR_AND_FULL_GRID_ALL_BANKS',floor_frame_physical_time_lineages=physical_lineages,derived_csv_checks=checks,limitations=['4 heldouts on one selected B4 task do not establish significance or new unselected-task transfer','source IDs hidden from scorer but coordinates remain visible in public preparation contract; computational input isolation, not analyst double-blind','REALIZATION_EVENT_COUNTS independent_stops is a terminology issue: 10 distinct correlated stops, not 10 independent experiments','aligned C7 MSE exactly zero follows identical all-positive event vectors under deterministic frozen map operator, not perfect concentration prediction','unmatched control uses concentration>0.1ppm temporal frequency as predeclared, not native 2D filament occupancy or independent-cell likelihood','heldout map association H101/H102 to rep2 and H103/H104 rep3 is hardcoded in analysis; verified against raw source-blind task vectors here'],observation_lineage_delivery_coverage=coverage,evidence_sha256={name:sha(ROOT/name) for name in ['frozen_contract.json','analyse_discrimination.py','SOURCE_BLIND_SCORES_BRANCH_0.json','SOURCE_BLIND_SCORES_BRANCH_1.json','DISCRIMINATION_RESULT.json']})
(HERE/'INDEPENDENT_FINAL_QA.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:result[k] for k in ['verdict','heldout_log_correct','heldout_Brier_correct','unmatched_selected','aligned_selected','E1','E2']},ensure_ascii=False,indent=2))
