"""Apply fixed gates after frozen dev/test outputs; no model calls."""
import csv,json,pathlib
import numpy as np
BASE=pathlib.Path(__file__).resolve().parents[1];OUT=BASE/'outputs/PMFS_R3_R5_CONTINUOUS_20261011'
def loadcsv(p):
    with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def csvout(name,rows):
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def jsonout(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def report():
    rows=loadcsv(OUT/'R4_DEVELOPMENT_METRICS.csv')+loadcsv(OUT/'R4_HELDOUT_METRICS.csv');csvout('R4_B0_B1_B2_SOURCE_OUTPUT.csv',rows)
    held=[r for r in rows if r['split']=='heldout'];csvout('R4_PER_TASK_HOLDOOUT.csv',held)
    final=[r for r in rows if r['events']=='50'];groups=[];lookup={(r['task_id'],r['method']):r for r in final}
    for split in ['development','heldout']:
        for source in sorted({r['true_source_id'] for r in final if r['split']==split}):
            for regime in ['constant','slow','fast']:
                case=[r for r in final if r['split']==split and r['true_source_id']==source and r['regime']==regime];z={'split':split,'true_source_id':source,'regime':regime,'realizations':2}
                for method in ['B0_FIXED','B1_TRANSIENT','B2_JOINT_PF','WIND_ORACLE']:
                    z[method+'_distance_m']=np.mean([float(r['main_distance_m']) for r in case if r['method']==method])
                z['B0_minus_B1_distance_m']=z['B0_FIXED_distance_m']-z['B1_TRANSIENT_distance_m'];groups.append(z)
    csvout('R4_GROUP_PAIRED_EFFECTS.csv',groups)
    dev=json.loads((OUT/'R4_DEVELOPMENT_SUMMARY.json').read_text());test=json.loads((OUT/'R4_HELDOUT_SUMMARY.json').read_text());selection=json.loads((OUT/'R4_ORDINARY_SELECTION_FROZEN.json').read_text());chosen=selection['selected_ordinary_method'];value=test[chosen]
    constant_delta=np.mean([r['B0_minus_B1_distance_m'] for r in groups if r['regime']=='constant']);dynamic_dev=[r for r in groups if r['split']=='development' and r['regime']!='constant'];dynamic_test=[r for r in groups if r['split']=='heldout' and r['regime']!='constant']
    static_gap=(np.mean([r['B0_minus_B1_distance_m'] for r in dynamic_dev])>=.5 and sum(r['B0_minus_B1_distance_m']>=.5 for r in dynamic_dev)>=2 and np.mean([r['B0_minus_B1_distance_m'] for r in dynamic_test])>=.5 and sum(r['B0_minus_B1_distance_m']>=.5 for r in dynamic_test)>=2 and abs(constant_delta)<=.5)
    suff=(value['main_distance_m']<=2. and value['coverage90']>=.8 and value['raw_predictive_CRPS']<=.05 and value['method_wall_s']<=120)
    receipt=json.loads((OUT/'R4_BATCH_RECEIPT.json').read_text());generation=json.loads((OUT/'R4_GENERATION_VALIDITY.json').read_text());clips=sum(int(r['wind_boundary_clips']) for r in final)
    physical={'status':'PASS_CONTROLLED_2D_MATH','not_qualified_for':['3D gas physics','lakeshore geometry','real sensor','native PMFS navigation','independent physical teacher'],'scope':'same discrete FV truth/likelihood solver; deliberate model-method gate, not external validation','mass_max_residual_mg':max(t['max_mass_residual_mg'] for t in generation['tasks']),'source_support':'25 identical legal atomic points; all six truth positions included','clock':'dt=.2s, sensor after 10 steps, wind available at start of each fifth step; no interpolated future wind','causality_test':'PASS B1/B2 exact prefix equality under future changes','sensor':'mg/m3 Gaussian censored at 0; CDF for zero; no ppm claim; binary deterministic only','independence':'36 whole tasks with 252 unique distinct RNG stream seeds; 18 dev/18 heldout; same 6 fixed source positions grouped; deterministic regime core plus independent OU wind/release/sensor realizations','matched_release_process':True,'wind_model_difference':'true sinusoid+OU; ordinary random-walk filter approximation. Finite PF(K24) and process approximation not certified converged. Any residual alone cannot admit R5.','wind_boundary_particle_clips_total':clips,'resource_receipt':receipt}
    jsonout('R4_PHYSICAL_VALIDITY.json',physical)
    gate={'WIND_STATIC_GAP':'PASS' if static_gap else 'NOT_CONFIRMED','ORDINARY_BASELINE_SUFFICIENT':'PASS' if suff else 'NOT_MET','LOCAL_WIND_INFORMATION_LIMIT':'NOT_INDICATED' if suff else 'UNRESOLVED','MEMORY_CANDIDATE_ADMITTED':False,'R5':'STOP_COMPLEX_MEMORY_NOT_NECESSARY' if suff else 'SKIPPED_NECESSITY_NOT_ESTABLISHED','selected_ordinary':chosen,'selected_heldout_metrics':value,'constant_negative_control_B0_minus_B1_m':constant_delta,'dynamic_development_B0_minus_B1_m':float(np.mean([r['B0_minus_B1_distance_m'] for r in dynamic_dev])),'dynamic_heldout_B0_minus_B1_m':float(np.mean([r['B0_minus_B1_distance_m'] for r in dynamic_test])),'independent_physical_validation':False,'accuracy_gate_is_not_PMFS_official_gate':True,'no_new_batch_or_R5_training':True}
    jsonout('R4_DECISION.json',gate)
    lines=['# R4 普通动态基线与机制判决','','仅在二维周期匹配求解器数学任务内成立，非原生PMFS、真实湖岸或三维验证。固定气体状态连续推进，变化风不能由静态图拼接。','','| 分组/方法 | 主定位距离 m | 源NLL | 90%覆盖 | 预测CRPS mg/m³ | 每任务方法墙钟s |','|---|---:|---:|---:|---:|---:|']
    for label,summary in [('开发',dev),('未见源/具体风历史',test)]:
        for m,s in summary.items():lines.append(f"|{label}/{m}|{s['main_distance_m']:.6f}|{s['source_NLL']:.6f}|{s['coverage90']:.3f}|{s['raw_predictive_CRPS']:.6f}|{s['method_wall_s']:.3f}|")
    lines.extend(['',f"WIND_STATIC_GAP：{gate['WIND_STATIC_GAP']}。动态开发 B0−B1={gate['dynamic_development_B0_minus_B1_m']:.6f}m；动态未见任务={gate['dynamic_heldout_B0_minus_B1_m']:.6f}m；恒定均风负对照={constant_delta:.6f}m。全部源×风分组方向见CSV，保留零检出及反例。",'',f"开发集按固定主距离选定 {chosen}，没有拟合参数；仅检验一次18个未见任务。ORDINARY_BASELINE_SUFFICIENT：{gate['ORDINARY_BASELINE_SUFFICIENT']}。门为平均距离≤候选间距2m、90%集合覆盖≥0.8、平均原始信号预测CRPS≤0.05及方法≤120s/任务。这是事前本数值任务门，不能改称PMFS成功。",'',f"R5：{gate['R5']}。B1本来已保存全部浓度历史，B2也保存联合风/释放/羽流状态。本轮没有证明一个普通状态模型无法承载的历史结构缺口，不能拿固定风对照的失败证明神经记忆必要。",'','完整风真值仅ORACLE读取；全部可部署方法用相同局地测风。公开观测文件没有真源标签，评估读取真源在推断冻结之后。源码无调用任何新网络。','',f"36份独立随机任务，统一25源点，50观测是每任务相关序列。批次墙钟{receipt['wall_s']:.2f}s，峰值RSS {receipt['peak_RSS_bytes']/2**20:.2f}MiB。",'','必须保留的边界：周期持续注入没有有限稳态；空间均匀风让局部仪器可代表整域，是公开的简化假设。真风是sinusoid+OU，B1/B2使用普通random-walk滤波近似；有限24粒子误差未经加倍参考资格化。不从残余误差推断原创必要性，不追加参考或种子。','', '主端点是共同Euclidean medoid，辅报MAP、均值与2/25候选Top5，非官方PMFS Top5。原始R2端点FAIL、E3/B4及STOP保持不动。'])
    (OUT/'R4_MECHANISM_GO_NOGO.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    reason='# R5 条件性准入未触发\n\n'+('普通动态模型已满足本轮预注册数值定位/覆盖/预测/成本门，因此停止复杂记忆训练。' if suff else '预注册普通充分性门未完全满足，但尚无排除有限粒子、过程近似或信息限制的独立历史结构必要性证据，因此不允许从一般误差跳到神经记忆。')+'\n\n已获得用户连续执行授权；此处是合同科学停止分支，不是请求再次审批。没有运行训练、R5额外种子或新的物理批次。普通FV、风滤波、粒子源推断不是原创。FloWM提供视觉空间记忆启发，尚不能直接证明气体源判别需要它。\n'
    (OUT/'R5_NOT_AUTHORIZED_REASON.md').write_text(reason,encoding='utf-8')
    jsonout('RUN_STATUS.json',{'R3':'PASS_READONLY_DIAGNOSTIC','R4':'PASS_QUALIFIED_CONTROLLED_BATCH','R5':gate['R5'],'native_ROS_calls':0,'CFD_calls':0,'new_GADEN_calls':0,'training_calls':0,'batch_count':1,'halt_after_package':True})
    print(json.dumps(gate,ensure_ascii=False,indent=2))
if __name__=='__main__':report()
