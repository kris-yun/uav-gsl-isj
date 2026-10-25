from pathlib import Path
import json,csv,hashlib,shutil,subprocess,os,datetime
from analyze import O,OLD,B,load,rows,put,table
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 summary=load(O/'ANALYSIS_SUMMARY.json');qa=load(O/'INDEPENDENT_QA.json');age=rows(O/'ORIGINAL_GAS_AGE_SUPPORT_AUDIT.csv');ageqa=load(O/'AGE_INFERENCE_QA.json');physical=load(O/'PHYSICAL_CAMPAIGN_RECEIPT.json');event=load(O/'event_control/RECEIPT.json')
 verdict=dict(identity='E3_CAUSAL_PAIR_NATIVE_PHYSICS_EVENT_OPERATOR_20261025',
  primary_attribution='真实物理可分，原生响应错序',
  applicability='Conditional on fixed common release settings, this exact source pair, same geometry/wind and frozen path; two physical realizations per source. Not generalization or a new algorithm gain.',
  physical_information=dict(continuous_known_release_reference='4of4 realization-held-out physical-template comparisons correct across13stations; evaluation-only source-labelled diagnostic, not a deployable reference bank',unknown_amplitude='3of4 across13stations,2of4 across8to13; stable source information under unknown strength not established',critical_binary='all30windows in all4worlds are hits;4-way exact realized collision, not120independent trials',whole_history_binary='ordinary template Brier0of4, insufficient to establish no binary information in the population'),
  source_model=dict(native2D_point_response='all true-source worlds prefer rival across both prediction streams',ordinary_event_readout='no source-rank rescue; same native trajectories, native3DGaussian/LOS, actual mass/spread/window threshold',beta11_sensitivity='does not rescue; retained',unvisited_spatial_amplification='parent audit preserved; not the only source of error'),
  causal_exclusions=['Changing only center-frequency aggregation to any-center window is insufficient','Changing only to PID concentration-window readout on the same native2D transport/history is insufficient','LOS and3sigma cutoff alone cannot explain zero response at10to13: diagnostic noLOS/untruncated upper bounds stay below0.1ppm in both predictions'],
  residual_support=dict(gas_age='97.4to100percent of original8to13station concentration comes from contributions older than readout-model max spread-equivalent age40.4s; actual weighted ages100to127s',posthoc_attribution='Readonly state contribution audit, not pre-registered gain endpoint and not a regenerated causal world',not_yet_separated=['GMRF drift/path error','2D versus3D transport','warmup termination and release-history support']),
  ordinary_planning='STOP_RESPONSE_RELIABILITY_GATE_FAILED; existing frozen-action signals retained; no new reliable planner or ANCA/Poleg run',
  full_domain_metrics='Original frozen O24 posterior retained; new1132cell fixed-bank raw-window diagnostic reported separately. Two-hypothesis errors never called full-domain localization.',
  new_physical_worlds=4,physical_query_values=2416,new_native_point_forward_calls=4,new_ROS=0,neural_training=0,
  historical_baseline_unchanged=True,new_method_main_innovation_PASS=False)
 put(O/'SCIENTIFIC_VERDICT.json',verdict)
 repro=[]
 for w in load(O/'PREREGISTERED_CAUSAL_CONTRACT.json')['worlds']:
  d=O/'worlds'/w['id'];identity=hashlib.sha256(json.dumps(dict(task=load(d/'TASK.json'),RNG=next(r for r in rows(O/'RNG_AND_WORLD_QUALIFICATION.csv') if r['world']==w['id'])),sort_keys=True).encode()).hexdigest();repro.append(dict(name='E3PAIR-V1-'+w['id'],world_identity=identity,source=w['source_xyz'],old_E3_identity=False,source_height=.7,queries=604,empty_to240s=True,replicate=w['replicate']))
 put(O/'NEW_WORLD_IDENTITY_REGISTRY.json',repro)
 # Preserve baseline normal/domain controls without synthesizing any new run.
 controls=O/'historical_controls';controls.mkdir(exist_ok=True)
 for name in ['CASE_AUDIT.json','UPDATE_TRAJECTORIES.csv','FIXED_TABLE_ORDINARY_CONTROLS.csv','MEASUREMENT_SUPPORT_QUALIFIER.json','B2_DOMAIN_DIAGNOSTIC_ONLY.csv','SCIENTIFIC_VERDICT.json','GITHUB_DELIVERY_RECEIPT.json']:
  shutil.copy2(OLD/name,controls/name)
 historical=O/'historical_E3_bank';historical.mkdir(exist_ok=True)
 for name in ['CASE_META.json','runtime/resolved_GSL_parameters.json','runtime/NAVIGATION_MAP_METADATA.json','runtime/native_posterior_updates.csv','runtime/native_candidate_maps.csv','runtime/native_candidate_maps.f32','runtime/native_window_consumption.csv','runtime/robot_path.json']:
  dest=historical/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(OLD/'inputs/E3_R01'/name,dest)
 for name in ['PREREGISTERED_SCOPE.json','ORDINARY_EIG_SELECTED_BEFORE_READOUT.json','FROZEN_QUERY_DESIGNS.json','STOP_RESPONSE_COMPARISON.csv','WINDOW_RESPONSE_COMPARISON.csv']:
  shutil.copy2(OLD/name,historical/name)
 parent_layout=O/'parent_audit';(parent_layout/'inputs').mkdir(parents=True,exist_ok=True);shutil.copytree(historical,parent_layout/'inputs/E3_R01',dirs_exist_ok=True)
 for name in ['ORDINARY_EIG_SELECTED_BEFORE_READOUT.json','STOP_RESPONSE_COMPARISON.csv','WINDOW_RESPONSE_COMPARISON.csv']:
  shutil.copy2(OLD/name,parent_layout/name)
 put(O/'ENGINEERING_FIRST_FAILURES.json',dict(no_scientific_parameter_retuning=True,no_physical_realization_retried=True,first_failures=['Standalone C++ lambda syntax and missing namespace corrected before any propagation','CSV CRLF header parsing corrected before any propagation','Orchestration local map variable shadowed builtin map, losing first failed-build CPU receipt; corrected and preserved compiler error log'],first_failed_build_CPU_s='UNKNOWN_NOT_FABRICATED',all_four_world_generation_calls='attempt1 only; fixed preregistered seeds and source coordinates; no result retries',historical_STOP_receipt='PHYSICAL_STOP_RECEIPT.json is an earlier engineering-stop receipt. Final physical status is PHYSICAL_CAMPAIGN_RECEIPT.json; both kept.'))
 text=f'''# O24-E3 最小配对物理与原生响应归因结果

## 本轮唯一主裁决

**真实物理可分，原生响应错序。**此裁决仅针对共同释放参数、这两个固定源、同一几何/风和已冻结航迹下的四个物理实现。连续响应的物理可辨性获得了条件性证据；未知源强、跨环境及完整概率定位泛化仍未建立。

普通 PID 事件匹配读出没有救回真源。下一步应围绕**原生源条件输运状态及其历史支撑不足**交给Pro，而不是直接训练主动神经模块。尚未分清GMRF漂移、二维路径、预热/释放历史三者的独立贡献，因此不能把其中某一项写成已经证实的唯一原因。

本轮没有ROS、ANCA/Poleg训练，没有修改冻结O24、旧E3、A2或B2，也没有移动任何历史真源。

## 1. 实际生成了什么，资格如何确认

新身份为 E3PAIR-V1，和旧E3、官方A–E原始数据分开。源为(-4,-1.9,0.7)及(-2.375,-4.875,0.7)，各两份传播实现。原E3地图SHA为24cc18fb1b428bd12d53de22e6434560f9fa34d28798d0f19b372ba9f2c8e403，加载风SHA为135690ce4679f43bb02d7d40fe39b338a250f2aa94cf3e71d0f2dbf8bbe4705a，均未替换。

原生GADEN物理参数：butane/type10、10团/秒、初始中心10ppm、sigma10cm、gamma15cm²/s、noise输入0.015、298K、1atm、deltaTime0.1秒。native内部保留其noise×10兼容缩放及后续乘dt。连续从空场推进2400步；float时钟实际末值240.005447秒已记录，未把浮点累积假装成精确240.000。

资格门先复算旧E4默认随机过程前11个保存状态：逐气团位置和展宽最大差0，随后才生成四个新世界。四世界各使用事前登记、由OS熵产生的独立128位初始化字，分别初始化Gaussian与uniform MT19937；真实引擎、分布缓存、1000项Gaussian表、表初末下标及调用顺序全部保存。四组初态及表SHA均不同，单线程消费次序可核对。**保留了原生循环Gaussian缓存，所以不声称每一步噪声独立同分布。**

四世界各604条查询，共2416条；342个原生格式完整气团快照/世界，合计1368帧。只在预先固定查询所需物理步保存状态，并非只传播这些步。全部2416条浓度由原生Playback再次加载快照复验，最大差0ppm。原始世界未覆盖。

## 2. 对旧E3第8–13站做了真正的三维读出核查

逐项复用原生3D气团位置、sigma、摩尔量、空气摩尔密度、3σ截断和障碍LOS，逐气团贡献相加，结果与原生浓度读数完全一致。65个原消费窗口均按实际样本数/均值恢复；边界回调有多个等价包时全部列出，没有捏造唯一归属。

第8–13站有129条原始气体读数。其中43条读数在传感器二维粗格内没有气团中心，但浓度仍超过阈值：气团在邻格、具有空间展宽并通过原生LOS，仍能贡献浓度。因此“中心未占此格”和“该点浓度必为零”确实不是同一事件。这并不自动证明改读出即可定位，因为候选输运也可能没有把任何合理气团送到附近。

新增配对世界在同一实际站位、窗口和物理时间查询。第8–13站：**两源×两实现×30个窗口全部检出**，每个世界的这30位hit串都是全1。它们不是120次独立物理实验，独立传播实现仍只有4个。对于这些已见实现，这段二值事件没有源区分力。

## 3. 真实连续观测有没有源信息

仅作为“物理信息是否存在”的源标签诊断：用实现0作参考、实现1评价，再交换。候选固定为同一对真实源；没有选择更有利源、时段或阈值。

| 评价读出（四个源实现评价） | 全13站 | 第8–13站 |
|---|---:|---:|
| 普通连续响应模板MSE | 4/4 | 4/4 |
| 普通非负未知幅度拟合 | 3/4 | 2/4 |
| 二值模板Brier | 0/4 | 全部平局（折算2/4） |

这说明固定释放合同下连续浓度幅度/空间形状有区分信号。未知幅度后收益明显变弱，尤其只看后6站时尚无稳定区分证据。不能把“普通参考模板4/4”写成部署算法已定位成功：这是一份源标签物理可观测性诊断，参考库从未进入在线选点、风估计或新前向模型。

它也不是四个未见源：只有两个源位置，每个两个独立传播实现；交叉交换的训练集相互依赖，不做显著性与跨环境宣称。完整65位二值序列仍可能含复杂信息，本轮普通Brier的负结果不能证明其总体互信息为零。

## 4. 普通事件匹配到底做了什么

主对照保持同一二维原生输运、同一最终局地GMRF、同一候选点、同一RNG轨迹、同一warmup/record预算。不是另造绕障风场，也没有把全图真实风交给预测器。

每源两个预测随机表；中心与PID读出直接共用各自同一组轨迹。先重放原call589/660，2112个float32命中图、原生分数和RNG终点全部完全一致，再执行4次点源诊断前向。

比较三臂：原生中心占格频率；普通窗口内任一中心占格；普通原生Gaussian质量/展宽/三维LOS产生的窗口平均浓度>0.1ppm。另保留预注册Beta(1,1)平滑敏感性，均无调参。

原生每步5条轨迹是模拟概率路径，不等于实际释放5个同质量物理团。因此普通浓度读出的质量权重从冻结物理释放率推导：warmup每0.2秒5条，每条等价0.4个实际团；record每0.1秒5条，每条等价0.2个实际团，均严格对应10团/秒。moles与sigma/gamma来自真实物理参数，没有按目标浓度拟合源强。此转换是一项普通结构适配，绝非主创新。

源对评分对所有臂使用同一站位平衡兼容项，D=0.2；连续五窗不当作五份独立物理证据。分数比和归一化工作权重不称校准Bayes因子/后验。两源比较的MAP只代表假设排序，未冒充1132格定位精度。

三臂、包括平滑敏感性，均只在竞争源世界选对：8个“物理实现×预测重复”组合中4个正确；真源世界的4个组合全部仍偏好竞争源。每个物理实现被两个预测重复评价，不能称8个独立世界。**普通事件匹配没有恢复源排序。**

## 5. 剩下的是不是又一个LOS接口问题

不是单凭本轮就能宣布的LOS故障。正式读出始终保留原生障碍检查。另对已保存的二维轨迹计算了一个**仅供诊断、不参与评分的宽松浓度上界**：保留质量/展宽但计入全部Gaussian尾部，并不扣除遮挡贡献。

即使这样，第10–13站两个真源预测重复的窗口上界仍全部低于0.1ppm。第10站两重复最大约5.5e-5与1.16e-3ppm，后3站更低。故这几站无法仅靠修正LOS或取消3σ截断解释；没有关闭检查来救结果。第8–9站存在有限例外，全部保留，不能把结论扩大到每个站位。

这个上界针对本轮已保存轨迹，不是所有可能随机路径的零概率证明。两个预测重复也不等于预测分布已收敛。

## 6. 新发现：旧观测依赖的气团年龄远超普通读出中的状态支撑

这是完成主实验后的只读贡献归因，非预注册算法收益终点，没有据此延长模拟或改warmup。

由原生sigma递推 `sigma +=15/(2sigma)*0.1` 建立float32年龄表。原档案32571个正贡献的sigma全部精确匹配，最大宽度误差0。关键测点最近气团sigma约39.5–46.6cm；本轮两个二维轨迹普通读出的最大sigma约25.8–26.6cm，折算的展宽龄期支撑上界约40.4秒。

| 原E3站位 | 浓度加权气团年龄 | 浓度中来自超出该支撑年龄的比例 |
|---|---:|---:|
| 8 | 125.0s | 100% |
| 9 | 127.3s | 98.8% |
| 10 | 110.1s | 97.4% |
| 11 | 103.8s | 99.1% |
| 12 | 100.2s | 100% |
| 13 | 102.2s | 100% |

固定真实状态中只统计支撑年龄内的气团贡献，30个原正窗口仅1个仍超过0.1ppm。它说明这批实际读数高度依赖长驻留历史，而非只依赖刚释放的气团。**这是固定状态质量贡献剖分，不是重新生成的年龄干预世界，不能单凭它证明加长warmup必定恢复定位。**

原生PMFS中心模型本身没有sigma/moles状态，不能把这个40.4秒说成官方算法的理论有效时限。它是本轮共享轨迹普通读出能覆盖的最大展宽等价支撑。剩余原因仍包括局地风/GMRF漂移、二维传播路径及“首团离域即结束warmup”的历史近似，尚未逐一隔离。

## 7. 完整合法候选域的结果另列，不以二选一冒充定位

保留旧E3原生完整结果：MAP误差3.389875m、官方Top-5%3.247628m、真源rank131–150，原生方差声明0.524461m²。

对四个新物理实现，另外使用旧1132合法格响应库及同一raw-window普通兼容评分，冻结原细分树：

| 新物理世界 | 真源排名 | 该固定库诊断MAP误差 |
|---|---:|---:|
| true_r0 | 176–195 | 3.277m |
| true_r1 | 143–162 | 3.390m |
| rival_r0 | 1 | 0.000m |
| rival_r1 | 12 | 0.791m |

这进一步显示旧响应库偏好锁定竞争源一侧。但它是全支持固定库离线诊断：没有重新建立native命中图/置信传播、没有重新细分树或执行ROS，不能写成4次新的官方闭环成绩。普通PID匹配对照只在同一对精确源点上完成；尚无完整1132格PID响应图，故本轮**不宣称新算法全域定位改善**。

## 8. 普通信息规划现在能不能进入下一步

不能据本轮晋级。既有普通IG选择的三个动作和全部合法对照均沿用，未按新读数重新挑点。两源下的所有短动作实际响应与正反例已保存，每动作同4.5秒、5窗口。第一个/第三个原IG动作在四新世界中均全检出；第二个动作的检出侧别随实现反转。连续值也有差异，但未知幅度诊断尚不稳定。

普通事件响应模型仍把真源世界排错，可靠响应前提没有通过。因此没有新跑一个依赖这些错响应的规划器，也未借未来真实响应或源标签生成动作。原已执行路线只作为事实回放，不是可用未来航迹。

这不证明其他动作都不可分，也不证明高级主动算法无效；只说明当前不能以“规划不够复杂”作为已证根因。

## 9. A2、B2、历史负例与资源

三条A2正常参考、原E3错源、B2源域限制和此前NO-GO均保留身份，未重新命名。A2官方Top-5%仍为0.2425/0.6132/0.4972m；没有给A2运行新算子，所以不声称做完了新算子的正常场景反退化试验。B2不进入源判别主实验。

记录的物理工程阶段约{physical['total_execution_wall_s']:.1f}s，事件对照阶段约{event['wall_s']:.1f}s，合计{event['combined_execution_wall_s']:.1f}s，低于900s；记录的单命令子进程CPU均低于120s。四个240秒气体世界的实际生成各约3.5–4.1秒墙钟：C++离线推进，不是实时ROS。完整交付又补入原E3已查询的95帧和最小编译源码，最终科学输出大小以FINAL_DELIVERY_RECEIPT.json为准；打包前再次核验低于128MiB。

首次独立工具编译出现语法/命名空间问题，另有CRLF解析错误，均在四世界生成前纠正并保留。首次失败编译的精确聚合CPU记录因脚本NameError缺失，明确标UNKNOWN，未补造。之后全部生成、原生回放及成功对照成本均有收据；四个正式物理实现都只执行首次登记随机流，没有因成绩重试。

最终交付包含：真实配对世界的完整查询帧、全部随机状态/表、原生三维贡献、中心与PID共同轨迹、所有源对/全域固定库指标、既有动作结果、年龄与上界诊断、源码、命令、SHA及独立QA。到此停止，不自动追加更长warmup、全域新前向或ROS。

## 给Pro的下一项问题

先从这些证据判断，怎样在合法局地观测权限和有限预算下覆盖长驻留贡献及源条件传播状态。应先提出**普通历史支撑/稳态资格对照**，把“历史缺口”与“漂移/二维路径缺口”隔离；本轮没有授权按结果调大warmup，也没有证明记忆网络或2026新算子有独立增量。

如果普通历史完整性或普通3D物理适配就解决，应归入正确性基线。只有同权限、同预算强对照仍有具体残差，才继续远领域主算子。
'''
 (O/'中文科学裁决报告.md').write_text(text,encoding='utf8')
 (O/'FOR_PRO_交接说明.md').write_text('本轮唯一主归因：固定共同释放合同下，真实物理连续响应条件性可分，原生源证据排错。普通同轨迹PID事件匹配仍不能救回；第10–13站宽松Gaussian上界也低于阈值。新增只读年龄剖分表明旧E3关键浓度97.4–100%依赖超出本次普通读出支撑的老气团，尚未因果区分GMRF漂移、二维路径和预热/释放历史。先设计普通历史支撑对照，不直接训练ANCA/Poleg，不把模板4/4或两源MAP当完整定位收益。全数据、首次失败与普通负结果在包内。\n',encoding='utf8')
 code=O/'code';code.mkdir(exist_ok=True)
 for p in Path(__file__).parent.glob('*'):
  if p.is_file():shutil.copy2(p,code/p.name)
 parent=O/'code/e3_information_audit';parent.mkdir(exist_ok=True)
 shutil.copy2(Path(__file__).resolve().parents[1]/'e3_information_audit/audit.py',parent/'audit.py')
 # Analysis imports parent from this sibling location on portable reruns.
 code_sibling=O/'e3_information_audit';code_sibling.mkdir(exist_ok=True);shutil.copy2(parent/'audit.py',code_sibling/'audit.py')
 put(O/'ANALYSIS_ENVIRONMENT.json',dict(python=__import__('sys').version,numpy=np.__version__,original_output=str(O),parent_commit='01b2a9507590b770503e138151ede211c0a08b82',baseline_source='631145657461c41840f6844f118de57d1e747ea4',baseline_ELF='e63fadfdb5b4b20ea6936f38c3a1d5edf0d1e9e236ed8d78a4846b009aefed78'))
 print('SCIENTIFIC_REPORT_COMPLETE',flush=True)
if __name__=='__main__':
 import numpy as np
 main()
