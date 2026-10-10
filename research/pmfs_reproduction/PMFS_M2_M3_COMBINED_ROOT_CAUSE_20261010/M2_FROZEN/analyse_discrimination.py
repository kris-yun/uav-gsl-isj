"""Fixed comparisons, no simulations and no retuning. Default returns recomputed outputs."""
import sys
sys.dont_write_bytecode=True
import csv,hashlib,json,math,re
from pathlib import Path
import numpy as np

def js(p):return json.loads(p.read_text(encoding='utf-8'))
def rows(p):
    with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def winner(a,b,larger=True):
    if abs(a-b)<=1e-12:return 'TIE'
    return 'C7' if (a>b if larger else a<b) else 'K2'

def analyse(root):
    lock=js(root/'POST_SCORE_PRE_UNBLIND_SHA256.json')
    for name,digest in lock.items():assert sha(root/name)==digest
    score=js(root/'SOURCE_BLIND_SCORES_BRANCH_0.json');score1=js(root/'SOURCE_BLIND_SCORES_BRANCH_1.json')
    assert score==score1
    generating=js(root/'HELDOUT_GENERATOR_MAPPING_ANALYSIS_ONLY.json')
    task_rows=[]
    for task,item in score['tasks'].items():
        row=dict(task_id=task,generating_candidate='C7' if task=='O0' else generating[task],
                 scope='historical B4 posthoc diagnostic' if task=='O0' else 'new independent RNG realization on frozen B4 route',
                 C7_log_sum=item['C7']['log_sum'],K2_log_sum=item['K2']['log_sum'],
                 C7_mean_Brier=item['C7']['brier_mean'],K2_mean_Brier=item['K2']['brier_mean'],
                 log_margin_C7_minus_K2=item['C7']['log_sum']-item['K2']['log_sum'],
                 Brier_margin_K2_minus_C7=item['K2']['brier_mean']-item['C7']['brier_mean'],
                 log_selected_candidate=winner(item['C7']['log_sum'],item['K2']['log_sum']),
                 Brier_selected_candidate=winner(item['C7']['brier_mean'],item['K2']['brier_mean'],False))
        task_rows.append(row)
    data=rows(root/'native_reference_evidence/FROZEN_INPUT.csv');free=np.array([r['occupancy']=='1' for r in data]);n=len(data)
    confidence=np.array([float(r['confidence']) for r in data]);weight=np.where(confidence>=0,np.minimum(confidence,1),0)
    observed=1-1/(1+np.exp([float(r['logOdds']) for r in data]))
    bankdirs=sorted((root/'native_reference_evidence/realizations').iterdir());physical_maps={};concentration_rows=[];event_counts=[]
    for bank in bankdirs:
        samples=rows(bank/'QUERY_OUTPUT.csv');lookup={r['query_id']:r for r in samples}
        array=np.full((50,n),np.nan);branches_equal=True
        for block in range(50):
            for index in np.flatnonzero(free):
                row=lookup[f'grid_b{block}_v0_c{index}'];array[block,index]=float(row['ppm_float32'])
                if block==40:
                    alt=lookup[f'grid_b40_v1_c{index}'];branches_equal&=row['ppm_float32']==alt['ppm_float32'] and row['frame']==alt['frame']
        assert branches_equal
        physical_maps[bank.name]=np.where(free,np.mean((array>.1).astype(float),axis=0),0)
        hits=[]
        for block in range(50):
            row=lookup[f'receiver_b{block}_v0'];value=float(row['ppm_float32']);hit=int(value>.1);hits.append(hit)
            concentration_rows.append(dict(bank_id=bank.name,block_id=block,stop=block//5,concentration_ppm=value,event_hit=hit))
        event_counts.append(dict(bank_id=bank.name,split='reference' if int(bank.name.split('_')[1])<2 else 'heldout',
                                 positive_blocks=sum(hits),negative_blocks=50-sum(hits),distinct_stops=10,
                                 membership_branches_identical=True,concentration_min_ppm=min(r['concentration_ppm'] for r in concentration_rows[-50:]),
                                 concentration_max_ppm=max(r['concentration_ppm'] for r in concentration_rows[-50:])))
    aligned={bank.name:np.array([float(r['probability']) for r in rows(root/'native_aligned_maps'/bank.name/'map.csv')]) for bank in bankdirs}
    native_anchor=js(root/'event_map_anchor/OBSERVED_MAP_ANCHOR_COMPARISON.json')
    reference_maps={cid:np.mean([aligned[cid+'_0'],aligned[cid+'_1']],axis=0) for cid in ['C7','K2']}
    references_freq={cid:np.mean([physical_maps[cid+'_0'],physical_maps[cid+'_1']],axis=0) for cid in ['C7','K2']}
    grid_rows=[];unmatched_scores=[]
    for cid in ['C7','K2']:
        freq=references_freq[cid];factor=1+((1-np.abs(observed-freq)*.4)-1)*weight
        assert np.isfinite(factor[free]).all() and np.all(factor[free]>0)
        logscore=math.fsum(math.log(float(v)) for v in factor[free]);rawscore=math.exp(logscore)
        unmatched_scores.append(dict(candidate_id=cid,deliberately_unmatched_log_similarity=logscore,deliberately_unmatched_similarity=rawscore,
                                     aligned_map_MSE=float(np.mean((observed[free]-reference_maps[cid][free])**2)),
                                     raw_physical_frequency_MSE=float(np.mean((observed[free]-freq[free])**2)),
                                     scope='same 3D reference banks; dependent 447-cell descriptive comparisons, not physical likelihood'))
        for index in np.flatnonzero(free):
            grid_rows.append(dict(candidate_id=cid,cell_index=int(index),observed_belief=float(observed[index]),confidence=float(confidence[index]),
                                  reference_raw_hit_frequency=float(freq[index]),reference_aligned_belief=float(reference_maps[cid][index]),
                                  unmatched_factor=float(factor[index]),log_unmatched_factor=math.log(float(factor[index])),
                                  aligned_squared_difference=float((observed[index]-reference_maps[cid][index])**2)))
    map_task_rows=[]
    tasks={'O0':observed,**{tid:aligned[cid+'_'+('2' if tid in ['H101','H102'] else '3')] for tid,cid in generating.items()}}
    for tid,mapvalues in tasks.items():
        errors={cid:float(np.mean((mapvalues[free]-ref[free])**2)) for cid,ref in reference_maps.items()}
        map_task_rows.append(dict(task_id=tid,generating_candidate='C7' if tid=='O0' else generating[tid],
                                 C7_aligned_map_MSE=errors['C7'],K2_aligned_map_MSE=errors['K2'],
                                 aligned_selected_candidate=winner(errors['C7'],errors['K2'],False),
                                 scope='fixed descriptive dependent-map discrepancy, not likelihood or new localization'))
    raw_choice=winner(unmatched_scores[0]['deliberately_unmatched_log_similarity'],unmatched_scores[1]['deliberately_unmatched_log_similarity'])
    align_choice=winner(unmatched_scores[0]['aligned_map_MSE'],unmatched_scores[1]['aligned_map_MSE'],False)
    evaluation=dict(status='SMALL_BUDGET_SOURCE_DISCRIMINATION_COMPLETED_PHYSICAL_CAUSE_HOLD',
                    raw_event_original_selected=task_rows[0]['log_selected_candidate'],
                    heldout_log_correct=sum(r['log_selected_candidate']==r['generating_candidate'] for r in task_rows if r['task_id']!='O0'),
                    heldout_Brier_correct=sum(r['Brier_selected_candidate']==r['generating_candidate'] for r in task_rows if r['task_id']!='O0'),
                    heldout_realizations=4,reference_realizations_per_candidate=2,
                    historical_B4_and_new_physics_same_model=True,new_geometries=0,new_wind_conditions=0,
                    unmatched_3D_original_selected=raw_choice,aligned_3D_original_selected=align_choice,
                    same_bank_observation_alignment_selection_changed=raw_choice!=align_choice,
                    compared_2D_PID_operator='NOT_COMPLETED_NO_VALID_OPERATOR; original 2D occupancy frequency cannot be assigned ppm',
                    new_PMFS_localization_performance='NOT_TESTED',prototype_admission='HOLD_NO_INDEPENDENT_UNSELECTED_TASK_AND_NO_CAUSAL_SINGLE_TRANSFORM_PROOF',
                    branch_sensitivity='Both branches exactly same saved frame/prediction in every new bank',
                    repeated_samples='50 blocks, 10 correlated stops, 8 physical RNG realizations; statistical unit is realization, not grid',
                    field_MSE_not_task_success=True,source_blind_scores_frozen_before_role_mapping=True)
    return evaluation,task_rows,event_counts,map_task_rows,unmatched_scores,grid_rows,concentration_rows

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--write-derived',action='store_true');a=p.parse_args()
    r=a.root.resolve();result,*tables=analyse(r)
    if a.write_derived:
        for name,table in zip(['SOURCE_DISCRIMINATION_PER_REALIZATION.csv','REALIZATION_EVENT_COUNTS.csv','ALIGNED_MAP_HELDOUT_COMPARISON.csv',
                               'SAME_3D_BANK_UNMATCHED_ALIGNED_COMPARISON.csv','SAME_3D_BANK_PER_CELL_COMPARISON.csv','RAW_CONCENTRATION_INFORMATION_ENHANCED.csv'],tables):
            path=r/name;assert not path.exists()
            with path.open('w',encoding='utf-8',newline='') as f:
                w=csv.DictWriter(f,fieldnames=list(table[0]));w.writeheader();w.writerows(table)
        path=r/'DISCRIMINATION_RESULT.json';assert not path.exists();path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
