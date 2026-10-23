"""Generate factual reports and one proposed next contract; no new experiment."""
from pathlib import Path
import csv,json,sys,time,subprocess,zipfile,hashlib
import numpy as np
from common import PROJECT,OUT,PROTOCOL,sha,write,csvout,dataset

def reports():
    train=json.loads((OUT/'TRAIN_ANALYSIS_RESULT.json').read_text())
    dev=json.loads((OUT/'DEV_CHECK_RESULT.json').read_text())
    qa=json.loads((OUT/'INDEPENDENT_QA.json').read_text());assert qa['status']=='PASS_SCOPED_AUDIT'
    agg=json.loads((OUT/'DESCRIPTIVE_AGGREGATES.json').read_text())
    extract=json.loads((OUT/'TRAIN_EXTRACTION_RECEIPT.json').read_text())
    m1=json.loads((OUT/'M1_STRUCTURE_AUDIT.json').read_text())
    cfg=json.loads(PROTOCOL.read_text())
    # Only existing TRAIN metadata is used to audit nominal equality. It does
    # not certify the old physical mol/s without the historical executable.
    from common import run_path,decode_frame
    nominal=[]
    for run in cfg['only_TRAIN_runs_before_selection_freeze']:
        meta=json.loads((run_path(run)/'RUN_MANIFEST.json').read_text())
        frame=decode_frame(run_path(run)/'iteration_92')
        nominal.append({'run':run,'master_seed':meta['master_seed'],
             'parameters':{k:meta['simulation_parameters'][k] for k in ('gas_type','num_filaments_sec','variable_rate','ppm_filament_center','filament_initial_std','filament_growth_gamma','filament_noise_std','temperature','pressure')},
             'serialized_moles_over_air':frame['moles']/frame['air']})
    assert all(r['parameters']==nominal[0]['parameters'] for r in nominal)
    assert all(r['serialized_moles_over_air']==nominal[0]['serialized_moles_over_air'] for r in nominal)
    write('RELEASE_AND_WIND_CONFOUND_AUDIT.json',{'nominal_release_equal':True,'serialized_concentration_scale_equal':True,
       'same_local_wind_at_fixed_clock_and_probes':qa['all_four_world_local_winds_equal'],'records':nominal,
       'source_height_independently_controlled':False,'wind_condition_generalization_tested':False,
       'unknown_amplitude_scope':'one nonnegative multiplicative response gain; not arbitrary changing release rate, sensor law, or wind field',
       'absolute_mol_per_second_recertified':False})
    # A single geometry-only future proposal. Coordinates are inspected without
    # any gas response; invalid attempted point remains in the record.
    proposal_geometry=json.loads((OUT/'PROPOSAL_SOURCE_GEOMETRY.json').read_text())
    c=next(r for r in proposal_geometry['candidates'] if abs(r['point_m'][0]+.1)<1e-6)
    assert c['legal_free']
    from recover_assets import geometry_receipt
    all_proposed=geometry_receipt([[-.6,1.95,.4],[-.4,-2.9,.4],[-.1,-2.9,.4]])
    assert all(r['legal_free'] for r in all_proposed)
    proposal={'status':'PROPOSAL_ONLY_NOT_EXECUTED','objective':'ordinary same-height three-source spatial observability before any M1/M2/M3 development',
       'house':'House01','source_xyz_m':[[-.6,1.95,.4],[-.4,-2.9,.4],[-.1,-2.9,.4]],
       'source_BC_separation_m':.3,'source_heights_equal':True,'source_legality_receipts':all_proposed,'existing_A_worlds_reusable_only_if_generator_and_sensor_contract_match':True,
       'maximum_new_gas_worlds':8,'master_seeds':[2026900001,2026900002,2026900003,2026900004],
       'no_new_random_seed_IDs':True,'paired_seed_groups_not_12_independent_worlds':True,
       'TRAIN_seeds':[2026900001,2026900002],'DEV_seeds':[2026900003,2026900004],
       'same_existing_wind':'1,3-2,4_fast; no new CFD',
       'sim_time_s':1000,'save_parameter_s':.5,'read_actual_saved_times':True,'probe_catalog':'same original 30 probes',
       'sensor_scope':'same ideal native pooled concentration; no fast olfactory-motion or hardware claim',
       'first_metrics':'known and unknown-gain ordinary single, static dual and full-window profiles; exact ties and world-level differences',
       'selection_scope':'TRAIN only, one frozen DEV check, preserve ordinary simple baselines',
       'no_M1_M2_M3_training_or_active_controller':True,'maximum_generation_wall_s':5400,
       'maximum_new_scientific_bytes':805306368,'minimum_free_disk_before_run_bytes':2147483648,
       'hard_prerequisite':'restore and verify original generator ELF ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688 and physical configuration; otherwise STOP without silently rebuilding a different generator',
       'no_inherited_authorization_from_this_audit':True,'do_not_execute_automatically':True,
       'deployment_boundary':'high-fidelity response worlds are evaluator/calibration data, never a free online candidate response bank',
       'stop':'if ordinary single/static dual methods saturate, do not add neural modules or more seeds; do not claim new-algorithm necessity'}
    write('NEXT_SINGLE_PROPOSAL.json',proposal)
    write('FINAL_DECISION.json',{'verdict':'STOP_CURRENT_M1_DYNAMIC_MAIN_CLAIM_NO_INDEPENDENT_GAIN',
        'TRAIN_extraction':'PASS_4_WORLDS_7212_FRAMES_30_PROBES',
        'dynamic_necessity':'NOT_ESTABLISHED_BY_FROZEN_FINITE_DIAGNOSTICS',
        'static_spatial_opportunities':'14 correlated TRAIN pair-windows; 3 satisfy frozen separation domain; one checked',
        'selected_DEV':'known amplitude ordinary pair 4/4 but ordinary single mean also 4/4; unknown gain pair 3/4 and ordering adds 0',
        'M2_main_innovation':'NOT_ESTABLISHED; geometry remains a candidate, not promoted automatically',
        'M1_structure':'TRAIN clipping and one-bit loss confirmed; no threshold or model changed',
        'new_worlds':0,'new_ROS':0,'new_M1_M2_M3_fit':0,'new_seeds_or_Houses':0,
        'sealed_or_H03_gas_opened':False,'one_future_proposal_only':True,'automatic_followup':False})
    summary=dev['summaries']
    get=lambda scope,method:next(r for r in summary if r['amplitude_scope']==scope and r['method']==method)
    selected=train['selected_candidate']
    text=f'''# V7 源对辨识条件与双点动态线索资格审计

日期：2026-10-23。接续提交 `061ecf5ddea0a59dcf932b5038ad646b7af454a4`。只读原生气体世界查询；未修改M1的0.04、原负结果或冻结O24，未执行新GADEN、ROS、M2/M3。

## 科学裁决

**当前两源资料没有建立双点动态机制的必要性，也没有给M1新的独立收益。**找到了少量静态双点的TRAIN候选，但一次冻结的DEV检查中，普通单点均值同样判对4/4，不能升级为双机主创新。未知幅度敏感性中，静态双点和完整双点时序均为3/4；时间顺序没有额外收益。

这不等于时间信息在真实气体里不存在，也不等于所有双点几何无效。本轮只有两个已标定、源高不同的源、每源两个TRAIN世界和两个已开放DEV世界。距离评分是普通模板诊断，不是已校准测量似然或部署方法。

## 1. 实际审查范围

仅对A/B各r01/r02四个TRAIN世界查询全部1803帧、原30探针，合计7212帧和216360个池化标量读数。每个池为四个原生格点均值，所有120格点合法。逐帧SHA、三维遮挡与浓度读出、原实际时钟和局地风沿用上一轮已验收C++组件。查询耗时{extract['wall_s']:.2f} s；这是已保存世界的读取，不是新的1000秒物理仿真。

预先固定50、100、…、950秒起始的19个20秒窗口，逐窗采用全部原生保存帧。19×435＝8265个测点对—窗口诊断高度相关，不是8265个独立场景。每个窗口做两次整实现交叉：用各源r01预测r02，再反过来。没有帧级随机拆分。

全历史含启动时零场，故另列50秒以后的真实间歇性。120个世界—探针对中，{agg['post50_all_zero_world_probe']}个始终精确为零，{agg['post50_all_positive_world_probe']}个始终为正，{agg['post50_at_least_two_hit_switches_world_probe']}个在0.1ppm门限下至少有两次切换。这些都是相关统计项，不是独立重复。完整结果见 `PER_WORLD_PROBE_FULL_HISTORY.csv`、`POST50_WORLD_PROBE_STATISTICS.csv`、`PER_WORLD_PROBE_WINDOWS.csv`。

**不是所有点都容易，也不是所有点都有信息。**很多点从未采到气体；同时19个时段中，每个时段均存在至少一个普通单点对照在当前四个TRAIN交叉判别中达到4/4。因此，当前两源整体并没有迫使我们必须依赖双点动态观测。

## 2. 三层必要性分别检查

保留完整单点窗口、单点均值、单点检出比例作为强单点集合；普通双点均值/检出比例为静态对照；完整双点序列、去时间顺序的双点多重集、分别排序的两侧分布为时间结构对照。

全双点读数是单点的两倍，因此另外冻结“单点N读数、双点最多N标量读数”的降采样对照，并保留实际末次采样时刻差异。固定探头不存在飞行成本主张；不能将这里的预算对照称为无人机航线公平实验。

- 单点不稳的有限TRAIN测点对—窗口：{agg['single_ambiguous_pair_windows']}项。这里的“不稳”是普通冻结模板的交叉实现错误/平局，不是信息论不可辨识证明。
- 静态双点及同标量预算双点都4/4、而所有单点对照最多3/4：14项。其中3项满足预先限定0.3–2.0m双点间距。
- 同时满足单点/静态双点不稳、时间顺序必要、同标量预算仍有效的动态机会：0项。

不能把最后一项写成“没有任何时间信号”。存在一个部分信号：100–120秒、探针2/30中，完整双点序列4/4、单点/均值/去序对照3/4，但同标量预算后也降到3/4。它未通过预算门，不能宣称动态机制独立有效，也没有被追加DEV测试。

## 3. 唯一冻结DEV检查

按与M1无关的规则，在TRAIN中选择最弱例也最稳的静态组合：**探针16/27、550–570秒**。间距1.56205m；两点为(-5.25,-5.98,0.20)、(-4.05,-4.98,0.20)。到源A距离约9.19/7.74m，到源B约5.77/4.23m，本例不靠紧贴某个源取样。

选择后，先冻结两TRAIN实现平均的各源普通响应模板、代码、测点、时钟和所有指标，再只查询这一个窗口在4个已开放DEV世界中的实际读数。旧DEV已经被用于前轮，绝不称新盲测。未检查其他候选的DEV表现。

| 普通方法 | 已知幅度严格正确/4 | 未知非负增益严格正确/4 |
|---|---:|---:|
| 左侧完整窗口 | {get('known','single_L_full')['strict_correct']} | {get('unknown_gain','single_L_full')['strict_correct']} |
| 右侧完整窗口 | {get('known','single_R_full')['strict_correct']} | {get('unknown_gain','single_R_full')['strict_correct']} |
| 左侧均值 | {get('known','single_L_mean')['strict_correct']} | 0，4次平局 |
| 双点均值 | {get('known','pair_means')['strict_correct']} | {get('unknown_gain','pair_means')['strict_correct']} |
| 双点均值、等标量预算 | {get('known','pair_means_equal_scalar_budget')['strict_correct']} | {get('unknown_gain','pair_means_equal_scalar_budget')['strict_correct']} |
| 完整双点时序 | {get('known','pair_ordered_full')['strict_correct']} | {get('unknown_gain','pair_ordered_full')['strict_correct']} |
| 去除双点时间顺序 | {get('known','pair_unordered_joint')['strict_correct']} | {get('unknown_gain','pair_unordered_joint')['strict_correct']} |

结论：已知幅度下，双点4/4而单点均值也4/4，没有相对最强单点的独立定位增益；未知增益下，双点相对单点形状有局部优势，但静态均值已取得与完整时序相同的3/4。不能把它归功于气味运动，更不能称M2已优于普通EIG。

未知增益只是普通比例干扰敏感性，不覆盖任意释放率变化或风场变化；正标量未知时，一个非零均值可以被任一候选用增益拟合，标量平局是该模型的代数边界，不是人为丢掉浓度后构造创新。

`SELECTED_DEV_PER_WORLD.csv`保留所有分数、错误和平局；分数不是NLL，不报告伪概率校准。两个候选的二维投影误差也不是全域未知源定位误差。

## 4. 竞争解释没有混为一谈

四个TRAIN世界的名义释放参数一致，保存浓度常数之比相同，同一时钟各探针局地风逐值相同。没有发现人为设置不同浓度尺度来标识A/B。但源高不同仍未隔离；一个风程序也不足以证明风不确定性下稳健。绝对mol/s和真实PID带宽没有在本轮重新认证。

源高、几何通道、输运随机性与观测表示对响应的共同影响，不能凭当前二源数据唯一拆开。0.1ppm门限与模拟精确零是不同事件，已分别统计。所选DEV右端有大量低于0.1ppm的读数，理想连续值的可用性不能自动延伸到真实硬件。

约0.5–0.6秒原生保存能支持实际采样点上的粗时序比较、采样到的检出切换及更长滞后的离散统计；不支持重建0.2秒线索、证明无混叠连续运动速度，亦不为原M1默认高速滤波补资格。

## 5. M1结构问题与实验难度分别成立

原冻结M1的TRAIN JS=0.242586、目标上限0.04、selection=[]均保持不变。这里只有一个源对，初始目标已达全局上界，任何额外通道都不可能获得正的目标增益。这是可直接核验的运算行为，不是通过修改阈值得出的新算法成绩。

另作一个严格标注的数学反例：两个源真实观测律完全相同，均为Bernoulli(0.5)，每源仅两个独立世界样本，沿用总平滑质量1。枚举16种四比特样本，有10种使经验JS超过0.04。**62.5%只属于这个构造零假设，不是实测GADEN误判率。**它说明经验源间JS不能被直接当成跨实现分离保证。

共同强度一位编码确实丢失左右侧别；而母特征换普通Gaussian头的旧结果说明概率量化也可能损失信息。但没有证据证明必须用动态M1才能修复：本轮普通静态与单点强方法已经解释主要表现。没有重训M1、强制选通道、调高阈值或改已见DEV。

## 6. 不确定性、核验与最终分流

样本单位始终是物理世界。每源仅两个TRAIN和两个已开DEV，多个窗口不能增加独立实现数。624项独立标量重算验证TRAIN预测与门限判定，最大分数差约{qa['max_margin_difference']:.2g}；已冻结DEV分数另行复算。原V7冻结结果与M1源码哈希保持不变。

当前分流是：**静态空间条件有少量开发线索，动态必要性未建立，当前M1停止，M2不能自动晋升。**保留当前数据为简单/正常对照，不能为了创新把它重新包装成“普遍难例”。

本轮只交付一个下一步提案：在同一House、同风、同源高和相同释放条件下，先让三个合法候选源接受普通单点/静态双点判别检验。详细坐标、原世界复用前提、最多8个新世界上限和停止规则在 `NEXT_SINGLE_PROPOSAL.json`。**它只是提案，未获本轮执行授权，也未启动任何新世界。**如果原生成器或参数身份无法恢复，先停止，不换物理实现继续造数据。该提案不要求立刻训练M1/M2/M3或运行无人机闭环。
'''
    (PROJECT/'SOURCE_PAIR_OBSERVABILITY_AUDIT.md').write_text(text,encoding='utf8',newline='\n')
    (OUT/'SOURCE_PAIR_OBSERVABILITY_AUDIT.md').write_text(text,encoding='utf8',newline='\n')
    next_md='''# 唯一下一轮提案：同高三源普通空间判别资格

状态：PROPOSAL_ONLY_NOT_EXECUTED。不是本轮可自动执行的后续任务。

保持House01原几何、原风1,3-2,4_fast、四个已有seed编号和相同释放参数。源A(-0.60,1.95,0.40)为正常控制；B(-0.40,-2.90,0.40)与C(-0.10,-2.90,0.40)相距0.3m，三者同高。静态地图检查三点合法。曾检查的C=(-0.70,-2.90,0.40)在障碍内，保留拒绝记录，未生成任何气体。

原A四世界只有在生成器、风、释放与读出合同完全一致时才复用；另最多8次B/C原生生成。seed沿用2026900001–2026900004，不新增编号；同seed跨源属于配对组，不能称12个独立世界。r01/r02训练，r03/r04开发。保存参数0.5秒并读取实际原生时钟，沿用30探针、理想池化浓度合同；这仍不是高速气味运动或真实PID实验。

首先只比较普通单点、静态双点、完整序列和去序列对照，分别报告已知幅度与普通未知增益。探针选择仅TRAIN，后冻结一次DEV检查。若普通单点/双点已经饱和，不进入M1/M2/M3。不得用测试真源选择动作，不将响应库作为部署免费输入。

执行硬前提：恢复历史生成器SHA ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688及冻结补丁/生效参数；否则停止。新数据最大768MiB、生成墙钟上限5400秒、开始前剩余空间至少2GiB。没有本轮对新世界的执行授权，不启动。
'''
    (OUT/'NEXT_SINGLE_FROZEN_PROPOSAL.md').write_text(next_md,encoding='utf8',newline='\n')
    logs=['observability_train_extract.log','observability_train_extract_fixed.log','observability_train_analysis.log',
          'observability_selected_freeze.log','observability_selected_DEV_first.log','observability_QA_first.log',
          'observability_QA_complete.log']
    for name in logs:
        src=PROJECT/name;target=OUT/'logs'/name;target.parent.mkdir(exist_ok=True);target.write_bytes(src.read_bytes())
    write('EXECUTION_RECEIPT.json',{'parent_commit':cfg['parent_commit'],'protocol_sha256':sha(PROTOCOL),
        'extraction_wall_s':extract['wall_s'],'TRAIN_analysis_wall_s':train['wall_s'],'DEV_check_wall_s':dev['wall_s'],
        'original_missing_Path_import_failure_retained':True,'new_physical_worlds':0,'new_ROS':0,
        'M1_threshold_change':False,'peak_RSS_and_GPU_not_instrumented':True,
        'commands':[{'command':'python native/observability_20261023/'+c,'exit_code':e} for c,e in
         [('extract_train.py first attempt',1),('extract_train.py after import repair',0),('m1_structure_audit.py',0),
          ('analyze_train.py',0),('check_selected_dev.py',0),('check_selected_dev.py evaluate',0),
          ('verify_audit.py first scoped check',0),('verify_audit.py complete TRAIN and DEV check',0),
          ('finalize_audit.py',0)]]})
    print('REPORTS_READY',OUT)

if __name__=='__main__':reports()
