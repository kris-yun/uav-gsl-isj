"""Build a transparent report from frozen saved tables; no additional experiment."""
from common_b import *
import csv,collections,numpy as np
def rows(p):
    with Path(p).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def mdtable(rr,fields):
    if not rr:return '无有效结果。'
    a=['| '+' | '.join(fields)+' |','| '+' | '.join(['---']*len(fields))+' |']
    for r in rr:a.append('| '+' | '.join(str(r.get(k,'NA')) for k in fields)+' |')
    return '\n'.join(a)
def main():
    reg=load(CORE/'experiment_registry.json');summary=rows(CORE/'SUMMARY_METRICS.csv');gate=load(CORE/'ORIGINAL_B_GATE.json');audit=load(CORE/'ACTUAL_INFORMATION_ISOLATION_AUDIT.json');assert audit['status'].startswith('PASS')
    gate['information_audit']='PASS_ACTUAL_SCALAR_ONLY_PROCESS_INVARIANCE';gate['status']='LIMITED_PROSPECTIVE_PASS' if gate['scientific_endpoint'].startswith('PASS_') else gate['scientific_endpoint'];dump(CORE/'ORIGINAL_B_GATE_FINAL.json',gate)
    metric=rows(CORE/'per_realization_metrics.csv');predict=rows(CORE/'predictive_metrics.csv');events=rows(CORE/'reference_event_changes.csv');costs=rows(CORE/'METHOD_COST_AND_STORAGE.csv');sensitive=rows(CORE/'sampling_sensitivity_evaluation.csv');future=rows(CORE/'future_prediction_scores.csv');coverage=rows(CORE/'state_coverage_by_realization.csv');runtime=load(CORE/'LOCAL_RUNTIME_LEDGER.json');gen=load(CORE/'GENERATION_LEDGER.json');meta={M:load(CORE/f'M{M}/MODEL_METADATA.json') for M in [2,4]}
    flips=[];continuous=[];sens=[];forecasts=[];capacity=[];cover=[]
    for M in [2,4]:
        for name in ['F','U_query','S_query','L']:
            er=[r for r in events if int(r['M'])==M and r['method']==name and int(r['reference'])<M]
            flips.append(dict(M=M,method=name,reference_events=len(er),event_flips_vs_F=sum(r['flip']=='True' for r in er),positive_to_negative=sum(r['flip_direction']=='positive_to_negative' for r in er),negative_to_positive=sum(r['flip_direction']=='negative_to_positive' for r in er)))
            r=[a for a in predict if int(a['M'])==M and a['method']==name and a['head']=='H0' and a['task']=='formal']
            continuous.append(dict(M=M,method=name,formal_forecast_ppm_MSE=float(np.mean([float(a['mean_ppm_MSE']) for a in r])),formal_correct_source_CRPS=float(np.mean([float(a['mean_CRPS_log1p']) for a in r])),formal_correct_source_Brier=float(np.mean([float(a['mean_Brier']) for a in r])),own_reference_compression_ppm_MSE_vs_F=float(np.mean([float(a['same_reference_compression_ppm_MSE_vs_F']) for a in r]))))
            for role in ['reference','extra_reference','diagnostic','heldout']:
                q=[a for a in coverage if int(a['M'])==M and a['method']==name and a['role']==role and a['unknown_fraction']!='NA_EMPTY']
                if q:cover.append(dict(M=M,method=name,role=role,realizations=len(q),mean_unknown_fraction=float(np.mean([float(a['unknown_fraction']) for a in q])),maximum_unknown_fraction=max(float(a['unknown_fraction']) for a in q)))
            if name in meta[M]:
                m=meta[M][name];capacity.append(dict(M=M,method=name,train_MSE=m['train_MSE'],active_states=m['capacity']['active_states'],canonical_bytes=m['capacity']['canonical_total_bytes'],actual_runtime_NPZ_bytes=m['capacity']['runtime_NPZ_bytes'],tree_nodes=m['capacity']['routing_nodes']))
    for head in ['H0','H1']:
        for pair in ['original2','extra2','all4']:
            r=[a for a in sensitive if a['head']==head and a['reference_pair']==pair and a['task']=='formal'];sens.append(dict(head=head,F_reference_pair=pair,mean_NLL=float(np.mean([float(a['NLL']) for a in r])),Top1_errors=sum(int(a['top1_error']) for a in r)))
        for M in [2,4]:
            for name in ['F','U_query','S_query','L']:
                r=[a for a in future if int(a['M'])==M and a['method']==name and a['head']==head and a['task']=='formal'];forecasts.append(dict(M=M,head=head,method=name,prefix25_to_future25_Brier=float(np.mean([float(a['mean_Brier']) for a in r])),prefix25_to_future25_CRPS=float(np.mean([float(a['mean_CRPS_log1p']) for a in r]))))
    derived=dict(event_flip_counts=flips,continuous_formal=continuous,F_reference_sensitivity=sens,future_prediction_formal=forecasts,capacity=capacity,coverage=cover,summary_metrics=summary,original_B_gate=gate)
    dump(CORE/'REVIEW_SUMMARY_NUMBERS.json',derived)
    true_nll={name:[r for r in metric if r['M']=='2' and r['head']=='H0' and r['task']=='formal' and r['method']==name] for name in ['F','U_query','S_query','L']}
    comparisons=[]
    for name in ['U_query','S_query','L']:
        for f,r in zip(true_nll['F'],true_nll[name]):comparisons.append(dict(oid=f['oid'],method=name,NLL_method_minus_F=float(r['NLL'])-float(f['NLL']),F_Top1_error=f['top1_error'],method_Top1_error=r['top1_error']))
    dump(CORE/'FINITE_F_NOT_BAYES_OPTIMAL_COUNTEREXAMPLES.json',dict(all_registered_formal_comparisons=comparisons,better_than_F_cases=[r for r in comparisons if r['NLL_method_minus_F']<0],scope='candidate finite-reference distributions; F fidelity is not guaranteed true-source improvement'))
    full=load(CORE/'FULL_BANK_PRESERVATION.json');exp=load(CORE/'EXPORT_SUPPORT_LEDGER.json');response_wall=gen['response_wall_s']+next(r['wall_s'] for r in runtime if r['stage']=='REFERENCE_CACHE');alltime=sum(r['wall_s'] for r in runtime)
    report=f'''# RK2-B/B+一次性连续研究报告

本轮执行固定24份：每源原2参考+额外2参考+2诊断+2正式测试。三个源、十个主受体、50块实际时间查询和四个几何先选辅助受体不变。原B端点只用正式6份、M2、H0。

**主门判决：{gate['status']}。** 与U/S的NLL相对变化分别为{gate['gain_each_baseline']}；逐实现最坏退化为{gate['maximum_individual_harm_nat']} nat。所有有效预注册分支均完成；没有因为主门成绩而换seed/源/路线/阈值/模型。本轮不认证主创新，也不覆盖RK2-A的开发门PASS。

## 1. 正式6份源判别结果

以下每行独立实现数为6；同一实现的50块含时间相关性，十处虚拟停留不是十次独立物理实验。诊断6份单独在SUMMARY_METRICS.csv，不并入确认样本。

{mdtable([r for r in summary if r['task']=='formal'],['M','head','method','mean_NLL','Top1_errors','mean_p_true','mean_posterior_mean_distance_m'])}

H0是float32浓度严格大于float32(0.1ppm)、Jeffreys p=(hits+0.5)/(M+1)、50块平均Bernoulli log和温度1均匀先验softmax。H1为log1p(ppm/1ppm)经验CRPS，各方法共用该M的F参考z总体IQR；退化IQR时尺度=1。H1不能替代H0主门，不用跨head/M的NLL百分比宣称收益。完整两档尺度在HEAD_SCALE_FROZEN.json。

这只是三个预置候选源的分类与三点位置误差，不是447格完整PMFS定位，不是新导航或湖岸试验。F是同预算的有限参考集原生读出，既不是测试真值，也不是Bayes最优。

## 2. 误差发生在哪条接口

{mdtable(flips,['M','method','reference_events','event_flips_vs_F','positive_to_negative','negative_to_positive'])}

逐候选、逐参考、逐块浓度及阈值距离保存在reference_event_changes.csv。M2主统计只纳入原2参考；它对额外2参考的读出也保存，供固定参考更换诊断，不能混入原B。

{mdtable(continuous,['M','method','formal_forecast_ppm_MSE','formal_correct_source_CRPS','formal_correct_source_Brier','own_reference_compression_ppm_MSE_vs_F'])}

最后一列比较同一候选自己的参考状态被压缩前后的误差；前几列比較候选参考预测与新实现的标量观测。二者不是同一接口，不将误差比率作加性因果分解。测试粒子从未进入infer。FINITE_F_NOT_BAYES_OPTIMAL_COUNTEREXAMPLES.json列出普通模型优于F的全部条件反例。

candidate_pairwise_margins.csv同时给出F与各模型得分差、R=range(score_method-score_F)和KL(F||method)≤R²/8。它约束对F的保真；F若选错，保持其排序不等于保持真源。精确碰撞组见FINITE_REFERENCE_COLLISIONS.json，只针对本规则/本有限参考，不宣称普遍不可辨识。

## 3. 参考数量、观测幅值和未来预测

{mdtable(sens,['head','F_reference_pair','mean_NLL','Top1_errors'])}

原2、额外2、全部4参考全部报告，没有择优选对。参考更换时H1使用该对/四份F自己的预注册IQR，其尺度一起列在sampling_sensitivity.csv；因此变化是有限参考与所定义评分尺度的共同结果，不单独归因于粒子记忆。

{mdtable(forecasts,['M','head','method','prefix25_to_future25_Brier','prefix25_to_future25_CRPS'])}

前25块只用于推断源分布，随后固定分布混合候选未来参考，评价后25块，后25块不反向更新源。10/20/30/40/50块全部前缀保存，不据其表现修改正式终点。辅助4受体未拟合decoder，显式使用候选侧F回退；额外矩阵只作诊断，不输入主定位，不声称零样本受体泛化。

## 4. 拟合、状态覆盖与真实成本

{mdtable(capacity,['M','method','train_MSE','active_states','canonical_bytes','actual_runtime_NPZ_bytes','tree_nodes'])}

保持lambda=.01、同一非负ridge目标、列RMS、全参考粒子含零响应的先验、原分位候选、最多4叶/3节点、最多72次提案和训练择优规则。唯一模型接口改变是每pose训练行数20→30或60。所有保存解的KKT独立核验；源码差异仅该断言及注释。零粒子记录按零查询保留，不造粒子。

{mdtable(costs,['M','method','readout_wall_s','fallback_wall_s','fallback_particles','all_particles','canonical_model_bytes','runtime_model_bytes'])}

F的原生C++矩阵先计算并缓存，后续source infer只读标量，**不给F每次推断重复收取粒子读出费**。上表F为共享已付费缓存，0个Python压缩query不能解释为F生成免费。24份原生矩阵总墙钟{gen['response_wall_s']:.3f}s（含首份独立锚点）；参考cache阶段{response_wall-gen['response_wall_s']:.3f}s；共享物理生成进程含保存{gen['generation_wall_s']:.3f}s。阶段全墙钟合计{alltime:.3f}s，包含格式/hash/时间资格检查；细分账与整段账不可相加重复计费。

U/S/L读出是Python实现，F是既有C++原生查询；不据这些异构实现时间宣称算法C++加速。L拟合搜索、路由、状态查找、候选侧回退均入账。模型训练参考集合与诊断/正式集的状态覆盖分角色报告于state_coverage_by_realization.csv。后者是最终预测冻结之后的隐藏状态元数据审查，未产生新源概率或参与调参。

## 5. 物理合同、隔离和可复核性

新gas_type13、7丝团/s、源高-0.5m、受体-0.2m和原B4锁定扩散参数保持不变，未重新计算CFD。所有源中心均在原生3D自由空间与二维候选支持中，点源资格不被偷换成整3σ球全自由要求。所有1803帧/实现的原字节、源位置、粒子有限值、正尺度、gas单位常量、实际时间与风索引逐帧核验。320–502s观测使用静态末帧10；不将11个CFD资产当作时变风证据。

实际记录按保存时钟定位：例如320s使用frame605的319.810302734s快照、下一快照320.310333252s；不是frame×0.5。该零阶保持规则跨所有源/角色一致，保存每块实际时刻和下一时刻。ppm是原生气体浓度数值读出，不冒充真实传感器硬件验证或独立实验校准。

原12base seed数值与角色保留；新增12使用PRO指定tag。Gaussian=base、uniform=完整tag后缀SHA大端的显式绑定在生成前锁定，两引擎初态和1000项Gaussian缓存提前冻结，实际24份均与其SHA一致。没有稳定跨帧particle ID，行号不当粒子身份。

生成前冻结提交4cff281；所有模型/预测在正式标量打开前封存，所有候选源概率在truth映射评价前封存。实际执行{audit['child_processes']}个新隔离Python子进程，检查隐藏文件替换/移除不变、候选匿名改名与排列等变、无truth仍推断、显式非法读取被拒绝。范围为Python open事件白名单，未声称操作系统内核沙箱。

前置断言/元数据上传修复原始错误日志留存，未改变seed、科学数据、loss或端点。完整父RK2-A的193项文件SHA本轮复核不变。没有重跑旧RK1、R7或B4导航；没有解封H03、训练网络或继续找理论。

## 6. 数据保全及解释边界

本轮完整{full['complete_frames']}帧留在{full['complete_bank_root']}，逐帧索引在complete_bank_indices。审核支撑选择全部主查询实际使用的{full['selected_raw_frames']}份原字节快照，保留14×50原生矩阵、查询血统和参考phi缓存；未选择快照保持原地未删除。

受控仿真物理血统通过不等于CFD已获真实实验验证；6份正式实现不是跨几何或统计论文复现。连续head、有限参考扩展、正确物理读出是对照工具，不是本轮新算法贡献。任何正结果只允许LIMITED_PROSPECTIVE_PASS，不将次级诊断翻案为主B。

复核：python source/verify_b.py CORE目录；原始支撑：python source/verify_raw_support_b.py CORE目录 RAW目录。它们不生成数据、不拟合、不调用ROS；CSV按数值容差比较，避免跨平台换行/浮点字符串字节误判。
'''
    (CORE/'RK2B_CONTINUOUS_RESEARCH_REPORT_zh.md').write_text(report,encoding='utf-8')
    formal=[r for r in summary if r['task']=='formal' and r['M']=='2' and r['head']=='H0']
    executive=f'''本轮已完成24份预列物理实现、M2/M4两档固定F/U/S/L、H0/H1、全部参考配对、前缀、未来和成本诊断。

原B主门：{gate['status']}。L相对U/S的NLL改善为{gate['gain_each_baseline']}；两档/两头不能替换此判决。

{mdtable(formal,['method','mean_NLL','Top1_errors','mean_p_true'])}

完整报告、逐实现反例和所有标量预测均在本包。L不自动升级为主创新；F为有限物理参考，保F不保证保真源。本轮结束，不追加seed、源、模型或导航。

给PRO优先分析的三个问题：
1. 同head同M的F/U/S/L差距和事件翻转，是否留下足够的表示增量？
2. F原对/额外对/四参考与前缀未来预测，说明哪个环节限制新实现判别：参考波动、阈值丢失幅值，还是当前固定采样？
3. 考虑原生F只付一次缓存费、L训练/路由/回退成本后，应否继续将L保留为辅助对照，主研究转向明确的条件预测问题？

这些是研究决策问题；本轮不凭单几何六测试宣称科学根因已经普遍成立。
'''
    (CORE/'EXECUTIVE_DECISION_zh.md').write_text(executive,encoding='utf-8');(CORE/'SEND_TO_PRO_zh.txt').write_text(executive,encoding='utf-8')
    print(json.dumps(gate,indent=2))
if __name__=='__main__':main()
