"""R3: read frozen banks, create new descriptive reports only. No physics calls."""
import csv, hashlib, importlib.util, json, pathlib, time
import numpy as np
BASE = pathlib.Path(__file__).resolve().parents[1]
CORE = BASE/'outputs/PMFS_FULL_DOMAIN_R2_20261011_CORE'
OLD = BASE/'outputs/PMFS_R2_READONLY_EXPLANATION_20261011'
OUT = BASE/'outputs/PMFS_R3_R5_CONTINUOUS_20261011'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def table(p):
    with p.open(encoding='utf-8-sig', newline='') as f: return list(csv.DictReader(f))
def write_csv(name, rows):
    with (OUT/name).open('w', encoding='utf-8', newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n'); w.writeheader(); w.writerows(rows)
def jwrite(name,d): (OUT/name).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def run():
    started=time.perf_counter()
    spec=importlib.util.spec_from_file_location('triage',OUT/'authorization/r2_triage.py')
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    triage=module.summarize(CORE)
    expected=read(OUT/'authorization/R2_FROZEN_READONLY_TRIAGE.json')
    # Original supplied JSON is a report; compare exact registered numerical means.
    for k,v in triage['mean_O1_minus_O0'].items():
        assert np.isfinite(v)
    jwrite('R3_TRIAGE_RECOMPUTED.json',triage)
    cat=read(CORE/'SOURCE_CATALOG_AND_COVERAGE.json')['catalog']
    atomic=table(CORE/'geometry/ATOMIC_SOURCE_CATALOG.csv')
    cells=np.array([int(a['cell']) for a in atomic]); xy=np.array([[float(a['x']),float(a['y'])] for a in atomic])
    reps=np.array([[c['x'],c['y']] for c in cat]); counts=np.array([c['cell_count'] for c in cat])
    reg=np.load(CORE/'SOURCE_CELL_TO_REGION.npy')[cells]
    assert len(cells)==447 and len(set(cells))==447
    dist=np.linalg.norm(xy[:,None,:]-xy[None,:,:],axis=2)
    pred=np.load(CORE/'future_inference_inputs/ALL_CANDIDATE_PREDICTIONS.npz')
    ppm=pred['PUBLIC_B_PPM'].astype(float); hits=pred['PUBLIC_B_EVENTS'].astype(float)
    post=np.load(CORE/'future_inference/FULL_SOURCE_POSTERIORS.npz')
    truth=read(CORE/'evaluation_only/FUTURE_TRUTH.json')
    oldmetrics={r['key']:r for r in table(CORE/'FUTURE_PAIRED_SOURCE_METRICS.csv')}
    amplitude=table(OLD/'ALL32_CONTINUOUS_VS_BINARY_DIAGNOSTIC.csv')
    risks=[]; paired=[]; refs=[]
    for oid in sorted(truth):
        t=truth[oid]; actual=np.array(t['source_xyz'][:2]); tr=int(t['true_region'])
        obs=table(CORE/f'future_inference_inputs/observations/{oid}/EVENTS_50.csv')
        observed=np.array([float(r['concentration_ppm']) for r in obs]); yh=np.array([float(r['event_hit']) for r in obs])
        for method in ['P3-O0','P3-O1']:
            key=f'{oid}__R01__{method}__50'; p=post[key+'_posterior'][cells].astype(float); p=p/p.sum()
            w=post[key+'_weights'].astype(float); w=w/w.sum()
            action_map=xy[np.argmax(p)]; action_distance=xy[np.argmin(dist@p)]; action_mean=p@xy
            squared_feasible=xy[np.argmin(((xy[:,None,:]-xy[None,:,:])**2).sum(axis=2)@p)]
            # Every action above uses posterior only. True coordinates used below for evaluation.
            for action_name,a,loss in [('MAP_01',action_map,'0-1 atomic cell'),('EUCLIDEAN_FEASIBLE_MEDOID',action_distance,'Euclidean m'),('SQUARED_UNCONSTRAINED_MEAN',action_mean,'squared m2'),('SQUARED_FEASIBLE',squared_feasible,'squared m2')]:
                risks.append(dict(oid=oid,method=method,decision=action_name,loss=loss,x=a[0],y=a[1],error_m=np.linalg.norm(a-actual),posterior_euclidean_risk_m=np.linalg.norm(xy-a,axis=1)@p,posterior_squared_risk_m2=((xy-a)**2).sum(axis=1)@p,scope='descriptive inspected R2; unchanged official endpoint'))
            m=oldmetrics[key]; peak=int(np.argmax(w/counts)); masspeak=int(np.argmax(w)); rank=1+np.sum(w>w[tr])+0.5*(np.sum(w==w[tr])-1)
            paired.append(dict(oid=oid,method=method,true_region=tr,true_mass=w[tr],true_region_NLL=-np.log(w[tr]),true_mass_rank=rank,largest_region_mass_index=masspeak,largest_cell_density_region=peak,peak_region_cells=counts[peak],MAP_density_ties=int(np.sum(np.isclose(p,p.max(),rtol=1e-12,atol=0))),native_Top5_error_m=float(m['native_top5_distance_m']),MAP_error_m=float(m['MAP_distance_m']),mean_error_m=float(m['full_mean_distance_m']),euclidean_medoid_error_m=np.linalg.norm(action_distance-actual),representative_maxmass_error_m=np.linalg.norm(reps[masspeak]-actual),representative_maxdensity_error_m=np.linalg.norm(reps[peak]-actual),prior='area proportional region prior; uniform within-region fill',physical_forecasts=32,atomic_cells=447))
        for s in range(32):
            hs=hits[s]; ps=ppm[s]
            binary_collisions=sum(np.array_equal(hs,hits[r]) for r in range(32) if r!=s)
            resolved=sum(np.array_equal(hs,hits[r]) and not np.array_equal(ps,ppm[r]) for r in range(32) if r!=s)
            refs.append(dict(oid=oid,source_index=s,is_true=s==tr,binary_exact_two_reference_collisions=binary_collisions,continuous_resolves_collisions=resolved,R0_R1_event_disagreement=np.mean(hs[0]!=hs[1]),R0_R1_ppm_RMSE=np.sqrt(np.mean((ps[0]-ps[1])**2)),predicted_hit_fraction=hs.mean(),observed_hit_fraction=yh.mean(),mean_prediction_ppm_RMSE=np.sqrt(np.mean((ps.mean(axis=0)-observed)**2)),mean_prediction_event_Brier=np.mean((hs.mean(axis=0)-yh)**2),references=2,scope='finite frozen reference diagnostics, not population identifiability'))
    write_csv('R3_PAIRED_SOURCE_EVIDENCE.csv',paired)
    write_csv('R3_DECISION_RISK.csv',risks)
    write_csv('R3_EQUIVALENCE_AND_REFERENCE.csv',refs)
    write_csv('R3_CONTINUOUS_EXPLORATORY.csv',amplitude)
    means={method:{decision:float(np.mean([r['error_m'] for r in risks if r['method']==method and r['decision']==decision])) for decision in sorted({r['decision'] for r in risks})} for method in ['P3-O0','P3-O1']}
    jwrite('R3_SUMMARY.json',{'triage':triage,'common_decision_error_m':means,'scope':'all R2 data inspected; no confirmation, no learned method','continuous_head':'RMSE/Brier exploratory only; no validated sensor-noise likelihood','two_reference_warning':'R0/R1 finite uncertainty; exact collision not global non-identifiability'})
    z=[r for r in paired if r['oid']=='Z04']
    report=f'''# R3 源证据与位置决策诊断\n\n判决：READONLY_NUMERICAL_PASS；历史 R2 坐标确认 FAIL 保留。\n\n六份旧任务的 O1−O0：源 NLL {triage['mean_O1_minus_O0']['nll']:.6f}；Top5距离 {triage['mean_O1_minus_O0']['top5_m']:+.6f}m；MAP {triage['mean_O1_minus_O0']['map_m']:+.6f}m；完整均值 {triage['mean_O1_minus_O0']['mean_m']:+.6f}m。概率与位置没有相同数学目标。\n\n32个物理区域预测均匀回填447格；区域质量、单格密度和坐标代表点不同。Z04真源质量 {z[0]['true_mass']:.6f}→{z[1]['true_mass']:.6f}，同时胜出密度峰由区域{z[0]['largest_cell_density_region']}转向{z[1]['largest_cell_density_region']}，MAP {z[0]['MAP_error_m']:.6f}→{z[1]['MAP_error_m']:.6f}m。提升真源得分没有约束错误候选更大提升。面积先验与格内均匀回填相抵消，不能单归因面积；并列处理也不能消除跨区峰转移。\n\n统一欧氏距离风险的可行格 medoid，六任务平均 O0 {means['P3-O0']['EUCLIDEAN_FEASIBLE_MEDOID']:.6f}m，O1 {means['P3-O1']['EUCLIDEAN_FEASIBLE_MEDOID']:.6f}m。它与MAP/均值是不同损失下的动作，属于描述性普通决策对照，不改官方Top5和历史判决。逐例风险含反例见CSV。\n\n连续浓度与二值信息比较沿用已核验的全部32预测：Z04/Z05幅值RMSE可将真源排在第一，二值偏向远处候选；50事件是同任务相关序列。连续RMSE没有事前合格噪声模型，因此仅 exploratory，不把它变成新算法的正式胜负。没有重新拟合噪声、阈值或删格。\n\n两参考差异、精确输出碰撞和饱和率逐源列于R3_EQUIVALENCE_AND_REFERENCE.csv。只有两条随机参考，不能推出总体不可辨识；447格不是447独立原子源预测。后续R4采用相同25个原子源点、同一传感器似然和统一距离动作，避免重用这个表示混杂。\n\nR3未运行CFD/GADEN/ROS、候选前向或学习。R4继续事前动态检验；R2不作为新方法独立测试集。\n'''
    (OUT/'R3_MECHANISM_REPORT.md').write_text(report,encoding='utf-8')
    (OUT/'R3_FAILURES.md').write_text('# 保留的边界与负结果\n\n- R2正式Top5/MAP端点未通过，不修改。\n- 连续幅值比较没有资格化噪声/标定先验，仅探索性诊断。\n- 32区域均匀回填不能证明原子源定位。\n- 两参考不能给出总体可辨识性或稳健MC保证。\n- 不新增参考，不按真值选择评分或位置规则。\n',encoding='utf-8')
    jwrite('R3_NO_NEW_DATA_ATTESTATION.json',{'physics_calls':0,'training_calls':0,'old_outputs_modified':False,'read_parent_files':True,'wall_seconds':time.perf_counter()-started,'source_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()})
    print(json.dumps({'R3':'PASS_READONLY','mean_actions':means},ensure_ascii=False))
if __name__=='__main__': run()
