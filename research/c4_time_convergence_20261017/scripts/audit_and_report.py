from pathlib import Path
import csv,json,hashlib,math,datetime
import numpy as np
R=Path(__file__).resolve().parents[1];A=R/'analysis'
def rows(n):
    with (A/n).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def write(n,data):
    with (A/n).open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
plan=json.loads((R/'FROZEN_PLAN.json').read_text(encoding='utf-8'))
response=rows('SOURCE_RECEIVER_RESPONSES.csv');pair=rows('SOURCE_PAIR_LOGSCORES.csv');summary=rows('PAIR_SUMMARY.csv');costs=rows('COSTS.csv');diffs=rows('FULL_MAP_DURATION_DIFFERENCES.csv')
jobs=list(csv.DictReader((R/'inputs/jobs.csv').open(encoding='utf-8')))
j={(a['key'],a['seed'],a['job_id']):a for a in jobs}
gaussian=[]
for context in plan['cases']:
 for condition in plan['conditions']:
  for seed in plan['prediction_states']:
   p=R/'results'/context['key']/condition['id']/str(seed)/'scores.csv'
   for a in csv.DictReader(p.open()):
    before=int(a['gaussian_before']);moves=int(a['particle_moves']);after=int(a['gaussian_after'])
    assert (before+2*moves)%2500==after
    assert a['rng_before']==j[(context['key'],a['seed'],a['job_id'])]['rng_before']
    gaussian.append(dict(key=context['key'],condition=condition['id'],seed=seed,job_id=a['job_id'],
        gaussian_before=before,gaussian_after=after,gaussian_values_consumed=2*moves,
        gaussian_table_cycles=(before+2*moves)//2500,passed=True))
write('GAUSSIAN_STATE_AUDIT.csv',gaussian)
flags=[]
for d in diffs:
 if d['later']!='W360_R20':continue
 key,seed,ident=d['key'],d['seed'],d['job_id']
 r180=[a for a in response if a['key']==key and a['seed']==seed and a['job_id']==ident and a['condition']=='W180_R20']
 r360=[a for a in response if a['key']==key and a['seed']==seed and a['job_id']==ident and a['condition']=='W360_R20']
 bystop={a['stop']:a for a in r180}
 raw=max(abs(float(a['raw_frequency'])-float(bystop[a['stop']]['raw_frequency'])) for a in r360)
 blur=max(abs(float(a['blurred_frequency'])-float(bystop[a['stop']]['blurred_frequency'])) for a in r360)
 a=r360[0]
 flags.append(dict(key=key,seed=seed,job_id=ident,receiver_max_raw_change=raw,receiver_max_blur_change=blur,
                  full_map_raw_Linf=float(d['raw_Linf']),full_map_blur_Linf=float(d['blur_Linf']),
                  source_logscore_change=float(d['source_logscore_change']),
                  late_60s_survivor_delta=int(a['late_warmup_60s_survivor_delta']),
                  late_60s_exit_count=int(a['late_warmup_60s_exit_count']),
                  meets_frozen_raw_and_blur_and_score_plateau_screen=(raw<=.02 and blur<=.02 and abs(float(d['source_logscore_change']))<=.1),
                  formal_convergence_proven=False))
write('CONVERGENCE_FLAGS.csv',flags)
assert len(gaussian)==1092
main=[a for a in summary if a['key']=='C4_update_1']
assert all(int(a['states_truth_outranks_locked_competitor'])==0 for a in main)
oracle=[a for a in response if a['key']=='C4_update_1' and a['condition']=='W360_R20' and a['job_id']=='oracle_true' and a['stop'] in ['2','4','5']]
assert len(oracle)==9 and all(int(a['unique_filaments_ever_observed'])>0 for a in oracle)
decision=dict(primary_verdict='HOLD_CONVERGENCE_UNRESOLVED',secondary_finding='RESPONSE_IMPROVEMENT_WITHOUT_DISCRIMINATION_GAIN',
    ordinary_forward_convergence_effect_fully_established=False,residual_response_mismatch_at_convergence_established=False,
    finite_time_affects_c4_response=True,all_c4_final_pair_scores_still_negative=True,
    exact_point_oracle_discrete_2d_paths_to_stops_2_4_5_observed_in_all_three_states=True,
    wrong_interpretation_rejected='Initial near-zero response alone proves a missing 2D source-receiver pathway',
    normal_control='C3 fine true-cell/competitor gap flips from positive under adaptive warmup to negative at W360_R20. Longer is not uniformly better.',
    excluded=['The time extension results are caused by changes to wind/map/noise/source/scoring: unchanged-kernel and 156-source exact parity checks pass.',
              'The selected C4 stop cells are absolutely unreachable by the diagnostic native 2D trajectories: explicit oracle arrivals refute this stronger claim.'],
    not_excluded=['Finite predictive population and correlated random approximation','Warmup/record phase transition and lack of a demonstrated receiver-wise stationary regime',
                  'PID-threshold versus massless-centre occupancy event semantics','3D effects on response probabilities, not absolute path existence'],
    next_minimum_proposal=dict(status='PROPOSED_NOT_EXECUTED',type='Ordinary phase-consistent 2D numerical control',
        sources='Existing C4 0.25m true source cell and prelocked 0.25m competitor, exact same three recorded per-source states',
        calls=6,horizon_seconds=360,dt=.1,releases_per_iteration=5,
        measurement='One continuous native recording-stage kernel trajectory per source/state from empty, 20s blocks, survivor/exits and receiver arrivals; no warmup/record dt/cadence switch. This is a separate unexecuted protocol with a fixed 360s ceiling.',
        purpose='Separate the existing native warmup protocol from a constant-step continuous simulation; still numerical diagnosis, not a PMFS correction or innovation.',
        stopping='If response/population remains nonstationary, retain HOLD without chasing an arbitrary steady limit; do not jump to 3D/world-model necessity.'),
    no_new_full_posterior=True,no_ROS=True,no_new_gas_world=True,no_innovation_or_task_gain_claim=True,
    planned_successful_calls=1092,actual_call_starts_including_one_incomplete=1093,
    completed_simulation_cpu_s=sum(float(a['cpu_s']) for a in costs),completed_particle_moves=sum(int(a['particle_moves']) for a in costs),
    stop_after_package_and_independent_branch=True)
(R/'FINAL_DECISION.json').write_text(json.dumps(decision,ensure_ascii=False,indent=2),encoding='utf-8')

lines=['# C4二维前向时长审计：预热确有影响，但360秒仍未收敛',
       '', '**主裁决：`HOLD_CONVERGENCE_UNRESOLVED`；同时存在 `RESPONSE_IMPROVEMENT_WITHOUT_DISCRIMINATION_GAIN`。**',
       '', '延长原生预热可让原先近零的远端响应出现，不能再把这些零直接解释成二维通路不存在。但真源在所有冻结时长和三组状态下仍未胜过原锁竞争源；360秒下响应、全图和存活气团数仍明显变化。未满足“普通延长已经修复源判别”，也未满足“已收敛后仍失配”。本轮停止，不启动下一项实验。',
       '', '## 证据身份与冻结', '',
       '采用修风后的2026开发实现 `4e141e162551e674f2f30ddb8859136c72139aac`、重新生成的GADEN世界中的已采集历史和仿真水平真风。不是作者原始轨迹、2024论文精确复现或湖岸局地测风运行。风在整个离线模拟内固定，不代表真实随时间变化的气象。',
       '', '上一轮ZIP SHA-256：`518de2e838a014c35b7a8ea7320afffd10d39f3eb7455f4d040f04ec1addb834`。核验1937项原输入/代码/目标地图；未重跑原10122次批次。C4 update_1为主，update_0为早期对照，C3 update_2为正常控制。原生移动、源释放、噪声、模糊、全图评分函数逐字保留。',
       '', '使用2026101701/02/03三个预测状态，并为每个源恢复上一轮保存的RNG、2500项高斯表及索引。156项定向自适应基准的原图、模糊图、评分、RNG及气团更新数与旧结果逐项一致。',
       '', '45/90/180/360秒预热对应225/450/900/1800次原生0.2秒暖启步；记录20/40/80秒对应200/400/800次0.1秒步。每步释放5个气团不变。A固定记录20秒；B固定预热180秒；共同的180/20只运行一次。所有时间均为名义推进时间，实际浮点dt沿用原生float。',
       '', '真源区域分别有6、24、12个合法0.25米子源，全部保留，不挑最优子源。原锁竞争源在C4末次为格514、C3为格807；C4 update_0原本没有预锁竞争源，保持NA，不事后补选。',
       '', '## C4末次源对判别', '',
       '下表为真源减竞争源的原生全图logscore范围（三状态）。正数才表示这两个冻结假设之间真源更受支持；不是新源后验、全源排名或定位成功。区域内部采用正确面积加权似然边际化；没有把新时长的少数候选与旧候选混合归一化。',
       '', '| 条件 | 原真源区域 | 全子源面积边际化 | 真源0.25米格 | 精确点oracle |',
       '|---|---:|---:|---:|---:|']
reps=['native_true_region','all_subsources_area_likelihood','true_0p25m_cell','exact_point_oracle']
for cond in [a['id'] for a in plan['conditions']]:
    vals=[]
    for rep in reps:
        a=next(a for a in main if a['condition']==cond and a['representation']==rep)
        vals.append(f"{float(a['pair_gap_min']):.3f}至{float(a['pair_gap_max']):.3f}")
    lines.append('| '+cond+' | '+' | '.join(vals)+' |')
lines += ['', '所有四种表示均为0/3个状态胜过锁定竞争源。区域似然与区域后验质量不同；本表不额外加入区域面积先验，亦不构造一个不完整的后验。Oracle仅用于诊断。',
          '', '## 远端响应确实能出现', '',
          'C4 stop 2/4/5的已消费窗口检出比例均为1，窗口均值ppm范围分别0.7268—0.8111、0.8597—0.8913、0.7228—0.8148。以下为360秒预热、20秒记录的原始占格频率，按三状态固定顺序列出：',
          '', '| 源表示 | stop 2 | stop 4 | stop 5 |','|---|---|---|---|']
for ident,label in [('region_truth','原真源区域'),('fine_truth_1272','真源0.25米格'),('oracle_true','精确点oracle')]:
    vals=[]
    for stop in ['2','4','5']:
        a=[x for x in response if x['key']=='C4_update_1' and x['condition']=='W360_R20' and x['job_id']==ident and x['stop']==stop]
        vals.append(' / '.join(f"{float(x['raw_frequency']):.3f}" for x in a))
    lines.append('| '+label+' | '+' | '.join(vals)+' |')
first=[float(a['first_occupied_sample_time_s']) for a in oracle]
lines += ['', f'在延长暖启协议下，精确点oracle在三个受体、三个状态中均观察到气团中心到达，首个离散占格采样出现在名义{min(first):.1f}—{max(first):.1f}秒。它证明这些受体在本诊断二维运动中可达；这不是每个气团的旅行年龄，不是现实气体到达时间，也不等于PID越阈概率已预测正确。',
          '', '## 为什么仍不能宣布收敛', '',
          '- C4末次上述三种代表源从180到360秒的全图原频率最大变化为0.59—0.995，模糊图最大变化约0.216—0.672；远超冻结的0.02描述性平台筛查值。完整逐源差分在CSV中。',
          '- 360秒预热的最后60秒，代表真源仍新增约670—837个存活气团（每源每状态该段释放1500个）。已有出流并不等于全局或逐受体响应稳定。10秒分段频率继续起伏，三状态差异明显。',
          '- 不把零方差的全零序列记作高有效样本量，不把气团数、帧数或不同更新当成独立物理世界。相关时间只作描述性诊断，三个预测状态不生成夸大的置信区间。',
          '- 暖启沿用dt=0.2、每步5个释放，记录为dt=0.1、每步5个释放，所以两阶段名义释放节律为25/50个每秒，运动步长也不同。没有在本轮改动这些规则；因此不能把阶段转换后的20/40/80秒简单视为同一物理过程的独立稳态样本。',
          '', '记录时间从20延至80秒并未修复C4判别：在180秒暖启下，真源细格、面积边际化与oracle的三个源对评分差均变得更负。原区域有一个状态改善，另两个退化，不应选取有利状态。',
          '', '## 早期和正常控制反证', '',
          'C4 update_0的真源源评分随时长变化，但没有原先冻结的竞争源，故不补造源对差、全源排名或完整后验。未消费的stop 4—6仅作为事后诊断受体列出，明确标识consumed_by_this_update=false，不进入早期评分。',
          '', 'C3正常控制的真源细格相对竞争源差，原自适应为+0.607至+1.167；180/20为+0.012至+0.111，360/20变为−0.678至−0.319。加长预热不是普遍更准确。C3与C4源及原生噪声不同，这也不是隔离三维影响的单因素实验。',
          '', '## 四个最终问题', '',
          '**1. 近零是不是时长不足？** 原生时长确有影响，长暖启能恢复不少原来缺失的占格响应；但尚不能说全部由时长造成，亦未恢复源判别。',
          '', '**2. 排除了什么？** 结合旧轮，普通区域细化/三随机重复不足以修复末次判别。本轮进一步反驳“这些受体在原生二维诊断里完全不可达”，也排除新增计数改动了原运动/评分这一执行解释。没有排除有限相关随机计算或不稳定采样。',
          '', '**3. 传感器算子还是二维结构？** 当前不能区分。massless二维中心占格与PID浓度叠加后越阈不同；二维预测缺少z、气团气量、sigma/年龄及传感器响应。即使可达，二维概率仍可能错，但本轮未获得足以归因该项的稳定对照。',
          '', '**4. 下一项最小必要证据？** 只建议六次相位一致的普通二维数值控制：既有C4真源0.25米格和原锁竞争格×原三状态，从空场以原记录阶段dt=0.1、每步5个释放连续运行到同一360秒上限，按20秒分段跟踪响应、存活与出流。单次连续时长预先限定360秒、不换状态、不生成世界，用它隔离原暖启/记录转换，而非无穷延长时间。该控制改变暖启数值协议，须作为独立普通诊断，不冒充原生PMFS性能。本轮未执行；若仍不稳，保留HOLD，不能强行转向三维主模块。',
          '', '## 成本、失败与交付', '',
          f"有效结果1092项，共{decision['completed_particle_moves']:,}次气团更新，源级计时CPU {decision['completed_simulation_cpu_s']:.3f}秒（包含额外观测计数与文件输出）。没有新增完整源后验、ROS回合或气体世界。记录窗口公共前缀逐字节一致；独立全图评分最大差3.55e−15。",
          '', '切换驱动以消除重复HGFS全目录统计时，误中断了一个已开始的调用。保留27项已完成源结果及最后一个不完整现场，只用原保存状态补齐最后一项；实际启动1093次，其中1次不完整。原冻结1092项有效对照清单不变。旧驱动、失败日志、额外调用核算和逐文件保留哈希都在lineage。此为我方执行错误，不是PMFS缺陷。',
          '', '原始未阈值consumer gas读数及时间/位置完整保留；位置关联不冒充每条PID与平均窗口的精确owner。文件中同时保留原始频率、模糊频率、10秒块、累计结果、三状态、存活/到达/出流、CPU和所有正反结果。',
          '', '**本轮到此停止。未建立主创新或真实闭环定位收益，不追加全候选重算、三维模型或新算法。**']
(R/'科学裁决_zh.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps(decision,ensure_ascii=False,indent=2))
