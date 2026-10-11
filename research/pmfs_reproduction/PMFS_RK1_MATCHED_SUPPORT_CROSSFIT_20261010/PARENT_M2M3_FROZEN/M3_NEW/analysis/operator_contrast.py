"""New same-path physical readout interventions; no simulation or retuning."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import importlib.util,csv,json,math,hashlib,time,argparse
import numpy as np
W=Path(__file__).resolve().parent;BASE=W.parents[1]
M2=BASE/'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010'
O=BASE/'outputs/PMFS_M3_PHYSICAL_ROOT_DISCRIMINATION_20261010'
OPS=['PID_NATIVE','CENTER_COLUMN','CENTER_SENSOR_BAND','PID_CELL_TRUNCATED','PID_NO_GROWTH_KERNEL']
def module(p,name):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def js(p):return json.loads(p.read_text(encoding='utf-8'))
def rows(p):
    with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def writecsv(p,data):
    assert not p.exists()
    with p.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
def choose(a,b,larger=True):
    if abs(a-b)<=1e-12:return 'TIE'
    return 'C7' if (a>b if larger else a<b) else 'K2'
def analyse(m2,output,write=False):
    start=time.perf_counter();p=output/'M3_FROZEN_CONTRACT.json'
    assert sha(p)==(output/'M3_PRE_COMPUTE_SHA256.txt').read_text().split()[0]
    r=module(m2/'independent_raw_query_verify/verify_raw_receiver_queries.py','raw_math')
    scorer=module(m2/'score_source_blind.py','frozen_scorer')
    F=np.float32
    meta=js(m2/'native_reference_evidence/FROZEN_METADATA.json');origin=np.array([meta['origin_x'],meta['origin_y']],dtype=np.float32);cell=F(meta['cell_size'])
    occ=r.occupancy(m2/'frozen_B4_inputs/derived_B4/OccupancyGrid3D.csv')
    ledger={int(x['block_id']):x for x in rows(m2/'event_map_anchor/vm_evidence/observed_anchor/event_replay_ledger.csv')}
    predictions={name:{} for name in OPS};perquery=[];percontrib=[];branch_checks=[]
    source_files={}
    def contrib(fil,point,desc,override=None):
        sigma=F(fil[3] if override is None else override);delta=fil[:3]-point
        sq=r.dot_sqr(delta);limit=F(F(sigma*F(3))/F(100))
        if not sq<F(limit*limit):return None
        if not r.los(point,fil[:3],desc,occ):return None
        dcm=F(F(100)*r.length(delta));exponent=F(-F(dcm*dcm)/F(F(F(2)*sigma)*sigma))
        den=math.sqrt(float(F(F(8)*r.PI_CUBED)))*float(sigma)**3
        mol=F(float(desc['total_moles'])/den);peak=F(1e6*float(mol)/float(desc['all_gas_moles']))
        return F(float(peak)*math.exp(float(exponent)))
    for bank in sorted((m2/'native_reference_evidence/realizations').iterdir()):
        if not bank.is_dir():continue
        query=[q for q in rows(bank/'QUERY_OUTPUT.csv') if q['query_id'].startswith('receiver_')]
        cache={};vectors={name:[None]*50 for name in OPS};byblock={}
        for q in query:
            block=int(q['query_id'].split('_')[1][1:]);branch=int(q['query_id'].split('_')[2][1:]);frame=int(q['frame'])
            if frame not in cache:
                fp=bank/'bank'/('iteration_'+str(frame));cache[frame]=r.snapshot(fp);source_files[fp.relative_to(m2).as_posix()]=sha(fp)
            desc=cache[frame];point=np.array([F(float(q[k])) for k in ['x','y','z']],dtype=np.float32)
            xy_index=np.floor((point[:2]-origin)/cell).astype(int)
            assert tuple(xy_index)==(int(ledger[block]['robot_i']),int(ledger[block]['robot_j']))
            centres=desc['filaments'];indices=np.floor((centres[:,:2]-origin)/cell).astype(int)
            same=np.all(indices==xy_index,axis=1);band=np.abs(centres[:,2]-point[2])<F(.125)
            total=F(0);inside=F(0);outside=F(0);nearheight=F(0);small=F(0);ncontrib=0;outsidecount=0
            for index,fil in enumerate(centres):
                v=contrib(fil,point,desc)
                if v is not None:
                    total=F(total+v);ncontrib+=1
                    if same[index]:inside=F(inside+v)
                    else:outside=F(outside+v);outsidecount+=1
                    if same[index] and band[index]:nearheight=F(nearheight+v)
                    percontrib.append(dict(bank_id=bank.name,block_id=block,membership_branch=branch,frame=frame,filament_serial_in_snapshot=index,
                      centre_x=float(fil[0]),centre_y=float(fil[1]),centre_z=float(fil[2]),sigma_cm=float(fil[3]),native_contribution_ppm=float(v),
                      same_native_XY_cell=bool(same[index]),same_sensor_height_band=bool(band[index]),horizontal_distance_m=float(np.linalg.norm(fil[:2]-point[:2])),vertical_offset_m=float(fil[2]-point[2])))
                vsmall=contrib(fil,point,desc,F(10))
                if vsmall is not None:small=F(small+vsmall)
            expected=F(float(q['ppm_float32']));assert total==expected,(bank.name,q['query_id'],total,expected)
            events=dict(PID_NATIVE=int(float(expected)>.1),CENTER_COLUMN=int(same.any()),CENTER_SENSOR_BAND=int((same&band).any()),
                        PID_CELL_TRUNCATED=int(float(inside)>.1),PID_NO_GROWTH_KERNEL=int(float(small)>.1))
            rec=dict(bank_id=bank.name,block_id=block,membership_branch=branch,frame=frame,native_pid_ppm=float(total),
               centre_column_count=int(same.sum()),centre_sensor_band_count=int((same&band).sum()),same_XY_cell_contribution_ppm=float(inside),
               outside_XY_cell_contribution_ppm=float(outside),same_XY_sensor_band_contribution_ppm=float(nearheight),
               no_growth_kernel_pid_ppm=float(small),outside_cell_fraction=float(outside)/float(total) if total>0 else None,
               contributing_filaments=ncontrib,outside_cell_contributors=outsidecount,**events)
            perquery.append(rec)
            if branch==0:
                for op in OPS:vectors[op][block]=events[op]
                byblock[block]=rec
            else:
                old=byblock[block]
                assert all(old[op]==events[op] for op in OPS)
                assert old['native_pid_ppm']==rec['native_pid_ppm'] and old['no_growth_kernel_pid_ppm']==rec['no_growth_kernel_pid_ppm']
                branch_checks.append(dict(bank_id=bank.name,block_id=block,all_operators_events_equal=True))
        assert all(all(x is not None for x in v) for v in vectors.values())
        for op in OPS:predictions[op][bank.name]=vectors[op]
    # Actual observations do not change with the prediction readout intervention.
    original=js(m2/'source_blind_inputs/branch_0.json')['observation_events']
    score_objects={};score_rows=[];count_rows=[]
    generating=js(m2/'HELDOUT_GENERATOR_MAPPING_ANALYSIS_ONLY.json')
    for op in OPS:
        ref={c:[predictions[op][c+'_0'],predictions[op][c+'_1']] for c in ['C7','K2']}
        data={'reference_events':ref,'observation_events':original}
        score=scorer.source_blind_scores(ref,original);score_objects[op]=score
        if write:
            ip=output/'operator_contrast'/('ANONYMOUS_INPUT_'+op+'.json');assert not ip.exists();ip.write_text(json.dumps(data,indent=2),encoding='utf-8')
            sp=output/'operator_contrast'/('SCORES_'+op+'.json');assert not sp.exists();sp.write_text(json.dumps(score,indent=2),encoding='utf-8')
        for task,item in score['tasks'].items():
            a=item['C7'];b=item['K2']
            score_rows.append(dict(operator=op,task_id=task,actual_generator='C7' if task=='O0' else generating[task],
              C7_log=a['log_sum'],K2_log=b['log_sum'],C7_Brier=a['brier_mean'],K2_Brier=b['brier_mean'],
              log_selected=choose(a['log_sum'],b['log_sum']),Brier_selected=choose(a['brier_mean'],b['brier_mean'],False)))
        for bank,v in predictions[op].items():count_rows.append(dict(operator=op,bank_id=bank,positive_blocks=sum(v),negative_blocks=50-sum(v)))
    native=score_objects['PID_NATIVE'];old=js(m2/'SOURCE_BLIND_SCORES_BRANCH_0.json')
    assert native['tasks']==old['tasks'] and native['candidate_reference_probabilities']==old['candidate_reference_probabilities']
    active=[r for r in perquery if r['membership_branch']==0 and r['native_pid_ppm']>.1]
    summary=dict(verdict='COMPLETED_SAME_PATH_OBSERVATION_KERNEL_INTERVENTIONS',operators=OPS,receiver_members=408,distinct_blocks_per_realization=50,
      new_GADEN_realizations=0,new_forward_calls=0,original_PID_scores_unchanged=True,
      branch_sensitivity='all 8 ambiguous alternatives agree for all five operators',
      positive_native_queries=len(active),positive_native_queries_without_XY_centre=sum(r['centre_column_count']==0 for r in active),
      median_outside_cell_mass_fraction=float(np.median([r['outside_cell_fraction'] for r in active])),
      candidates_selected_for_original={r['operator']:{'log':r['log_selected'],'Brier':r['Brier_selected']} for r in score_rows if r['task_id']=='O0'},
      heldout_correct_by_operator={op:{name:sum(r[name+'_selected']==r['actual_generator'] for r in score_rows if r['operator']==op and r['task_id']!='O0') for name in ['log','Brier']} for op in OPS},
      causal_scope='Within identical frozen paths and constants, only observation-support/kernel changes. Does not prove a self-consistent new transport process or full PMFS root cause.',
      exploratory_reused_M2_evaluation=True,wall_s=time.perf_counter()-start,input_snapshot_SHA256=source_files)
    return summary,score_rows,count_rows,perquery,percontrib,branch_checks
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args()
    if a.write:(O/'operator_contrast').mkdir(exist_ok=False)
    result,*tables=analyse(M2,O,a.write)
    if a.write:
        for name,table in zip(['OPERATOR_SCORE_COMPARISON.csv','OPERATOR_EVENT_COUNTS.csv','RECEPTOR_CONTRIBUTION_DECOMPOSITION.csv','FILAMENT_CONTRIBUTION_DECOMPOSITION.csv','MEMBERSHIP_BRANCH_OPERATORS.csv'],tables):writecsv(O/'operator_contrast'/name,table)
        (O/'operator_contrast/OPERATOR_RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='input_snapshot_SHA256'},ensure_ascii=False,indent=2))
