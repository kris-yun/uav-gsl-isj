"""Report actual bounded results, negatives and one unexecuted next proposal."""
import json,csv,datetime
from protocol import *

def main():
 c=config();cost=json.loads((OUT/'PHYSICAL_RUN_AND_COST_AUDIT.json').read_text());qa=json.loads((OUT/'INDEPENDENT_QA.json').read_text())
 assert cost['status'].startswith('PASS_') and qa['status'].startswith('PASS_')
 d=json.loads((OUT/'DEV_RESULT.json').read_text());m=json.loads((OUT/'MIRROR_DEV_RESULT.json').read_text())
 exploratory=json.loads((OUT/'TRAIN_MOTION_STRONG_SINGLE_ANNOTATION.json').read_text())
 choose=lambda name:next(x for x in m['summary'] if x['method']==name)
 primary=next(x for x in d['summary'] if x['scope']=='known' and x['method']=='strongest_global_single')
 write('FINAL_DECISION.json',{'status':'BOUNDED_EIGHT_WORLD_TRIAL_COMPLETE_NO_INDEPENDENT_MIRROR_DEV_GAIN',
 'generator_identity':'PASS_EXACT_ORIGINAL_ELF_TRACKED_PATCHES_PARAMETERS_WIND_AND_CLOCK',
 'new_worlds':8,'physical_retries':0,'robot_ROS_closed_loops':0,'M2_M3_runs':0,
 'same_height_confound_removed':True,'primary_DEV_strong_single_correct':primary['strict_correct'],
 'primary_DEV_static_dual_correct':4,'primary_DEV_temporal_dual_correct':4,
 'frozen_all_mirror_correct':choose('frozen_all_mirror_features')['strict_correct'],
 'original_M1_correct':choose('original_secondary')['strict_correct'],'original_M1_selected_filters':[],
 'frozen_pair_right_channel_identically_zero':True,
 'TRAIN_apparent_spatial_increment_is_same_side_subsampling':True,
 'general_mirror_uselessness_proven':False,'main_innovation_pass':False,
 'TRAIN_only_conditional_mirror_signals':exploratory['candidates'],
 'no_extra_DEV_pair_or_time_queried':True,'next_proposal_only_no_execution':True,
 'remaining_limits':['known three-source calibration diagnostic, not full-map O24 localization',
 'two DEV master-seed groups and already-open A control','one House and one wind programme',
 'conditional ideal continuous concentrations, no real PID/rotor qualification',
 'historical shared-library byte identity not available for every dependency; current lookup archived',
 'legacy temperature/pressure binding retained, no absolute mol/s requalification']})
 write('ENGINEERING_EVENTS.json',{'physics_changes':0,'events':[
 {'event':'VM initially stopped and host service inaccessible','resolution':'user started the original VM; no VM configuration or VM disks changed'},
 {'event':'original /mnt/hgfs/workspace missing after boot','resolution':'task-owned read-only FUSE mount; exact occupancy SHA matched; only path alias differs'},
 {'event':'first metadata read used path instead of name','resolution':'schema key repaired before first TRAIN score; initial error log retained'},
 {'event':'synthetic scalar tie check raised numpy scalar assignment TypeError','resolution':'np.where handles scalar/vector identically; fixed before first TRAIN scoring, thresholds unchanged'},
 {'event':'numeric random gzip access was slow','resolution':'own read-only extractor interrupted; streaming member order fills original timestamp axis; completed B1 array equality asserted; no physics repeated'}],
 'additional_controls':[{'name':'mirror shadow','authorization':'user requested careful mirror examination before DEV; original primary protocol unchanged'},
 {'name':'unknown-amplitude strong single','reason':'known-amplitude-selected single need not be strongest under gain uncertainty; separate TRAIN-only control frozen before DEV'}],
 'all_first_physical_runs_preserved':True,'old_negative_packages_not_overwritten':True})
 # No automatic second DEV lookup. This explicit proposal identifies the
 # one TRAIN lead and all controls needed to refute it.
 proposal={'status':'PROPOSAL_ONLY_NOT_EXECUTED','new_physical_worlds':0,
 'primary_candidate':{'window_s':[300,320],'probe_ranks':[12,30],
 'TRAIN_cross_world':{'all_frozen_mirror':6,'same_pair_full_raw':4,'same_pair_static':4,
 'same_pair_ordinary_delay':4,'unordered_mirror':4,'best_endpoint_single':5,'best_global_single':6}},
 'scientific_question':'at fixed measurement geometry, is nonlinear mirror compression better than all frozen ordinary same-input baselines across independent realizations, rather than merely choosing a better location?',
 'limitations':['post-primary TRAIN lead after multiple comparisons','some B/C worlds lack three above-0.1ppm records on both sides',
 'a different TRAIN single already reaches 6/6','existing DEV controls already partly opened, so not new blind validation'],
 'required_frozen_controls':['same-pair full raw and means','ordinary same-kernel delay features','best same-pair single','TRAIN-selected global single',
 'same Gaussian and nearest-profile heads','original M1 target0.04 unchanged','static-only and order-destroyed mirror'],
 'execution':'one new contract required before a second DEV window; never overwrite this completed trial or call exploratory selection confirmatory',
 'no_M2_M3_or_robot_ROS':True}
 write('NEXT_SINGLE_MIRROR_PROPOSAL.json',proposal)
 report=f'''# 同高三源：双点与镜像独立价值有界实测

日期2026-10-23。接续7fdcf236，用户批准原生成器核验、最多补8个世界、TRAIN选点后冻结DEV；其后要求认真检验镜像。原M1目标0.04、O24、源/种子/风与科学参数未按成绩调整。

## 结论

**8个新世界全部完成，身份、时钟、参数和原生读出通过；本轮冻结DEV仍没有镜像独立定位收益。**这不是“镜像在任何困难条件下都没用”的证明。我们查到了一个明确的未生效原因：冻结测点右侧在六个TRAIN和六个DEV窗口均为零，双点镜像实际退化成单点滞后整流。

TRAIN探索另外留下一个固定测点下的镜像线索（300–320秒、12/30），但没有查询其DEV；另一个700秒候选被同点单点6/6反例削弱。它们只能作为下一轮提案，不能替代本轮负结果。

## 1. 身份和实际执行

原ELF SHA为`{ELF_SHA}`。父仓库17adaf650a4f11d29aa049cf0661e9f9ea2e636f、核心9e93c36ae1af74f6a62c42f1c9d7b813153222ed、两份完整dirty补丁及关键源码SHA均逐项匹配；11状态原风和占据图SHA一致。动态库实际解析路径和当前SHA已保存，无法声称每一项历史系统库也逐字节相同。

原共享目录未随VM启动挂载，改为任务目录内只读挂载，地图内容不变。生成器没有重编译、修公式或改温压绑定。历史温压绑定行为保留，因此本轮是同生成器的相对数值判别试验，不重新认证绝对mol/s。

源A(-0.60,1.95,0.40)复用原4个世界；B(-0.40,-2.90,0.40)、C(-0.10,-2.90,0.40)各补4次，B/C间距0.3m。三源与原30探针全部合法。沿用2026900001–2026900004：r01/r02为TRAIN，r03/r04为DEV。跨源同seed是配对组，不能称12个独立种子重复。

8次原生生成共{cost['generation_wall_s_sum']:.3f}秒墙钟、{cost['generator_child_CPU_s_sum']:.3f}秒子进程CPU；每次模拟物理时长1000秒，保存1803帧，时钟/风序与旧A逐字节一致。离线数值程序没有实时等待，故物理秒不等于墙钟秒。这些不是无人机ROS闭环。所有14,424个新帧SHA已核对，未重试任何物理世界。原生生成器本身使用ROS运行库与参数接口，未启动机器人、导航或PMFS闭环。

8份原始气体tar保留全部新帧，重复风以一次共享文件束提供；完整逻辑文件名/SHA保留，未改动原风内容。执行成本、源码身份、每次stdout和首错均见收据。

## 2. 一次冻结比较

只在6个TRAIN世界查询原30探针全1803帧，固定19个20秒窗口。采用整实现交叉，无帧级拆分。双点比较包括同标量预算；强单点从同一窗口全部30探针中按TRAIN选择，不只使用双点中较弱的一侧。

冻结结果为50–70秒、探针10/24、间距1.61245m；强单点为探针10均值。TRAIN双点降采样均值6/6，完整均值单点5/6。位置、全部普通原型和镜像模型均先冻结，再生成/读取DEV；只打开这一个DEV窗口，额外的未知幅度强单点也在DEV前冻结。旧A控制已开放，不把整个面板称新盲测。

| 已知幅度DEV方法 | 严格正确/6 | 错误/平局 | 固定三候选平均XY误差 |
|---|---:|---|---:|
| TRAIN选出的全30点最强单点 | 4 | 2错、0平局 | 0.8626m |
| 普通双点均值 | 4 | 2错、0平局 | 0.8626m |
| 普通完整双点时序 | 4 | 2错、0平局 | 0.8626m |
| 去时间顺序双点 | 4 | 2错、0平局 | 0.8626m |
| 原M1（仍selection=[]） | 4 | 2错、0平局 | 0.8626m |
| 原母方法（选静态梯度） | 4 | 2错、0平局 | 0.8626m |
| 全部冻结镜像特征＋同式Gaussian头 | 3 | 3错、0平局 | 0.9126m |

A正常控制均正确；近邻B/C是困难部分。这是已知三候选离线标定诊断，不是全域O24后验、未知新源或实际航线成绩。

为隔离评分头，同式Gaussian对照另行保留：静态双点均值4/6、完整raw 3/6、普通同核线性延迟3/6、全部镜像3/6；母特征4/6且只选静态梯度。各表示维数不同，已在模型收据披露，不能把压缩/正则化差异自动称为新增物理信息。

未知幅度下，普通双点均值为0严格正确、6平局；完整时序3正确、2平局，同采样左侧单点也相同。降采样双点为4正确、2平局，同样等于降采样左侧单点；不能归因于第二测点。另行TRAIN选出的未知增益强单点为2/6，仍保留同点完整单点3/6这个更强的DEV反例，不只展示较弱基线。

## 3. 为什么这次镜像没发挥

右侧TRAIN/DEV最大浓度严格为0。若R=0、偏置为0，则

`h=max(<log(1+L),w-kappa*w_delay>,0)`。

另一镜像分支非正，静态梯度与共同强度又相同。这是精确的单侧退化；C++/Python和代数重算误差均在数值精度内。因此本例没有提供检验双侧气味运动所需的输入条件。

我此前把TRAIN的6/6对5/6称为“机会”。进一步归因发现它来自左侧时间降采样/求积：采用双点相同采样时刻的左侧单点也为6/6，全部DEV预测也逐项相同。它不是新增空间信息，更不能成为几何主创新。首批结果保留，纠正写在`ZERO_RIGHT_AND_SAMPLING_ATTRIBUTION.json`，没有换点重测。

## 4. 镜像还留下什么真实线索

在同一批TRAIN中，只作事后探索、不查新DEV：8265个相关测点对—窗口中，有167个符合几何且B/C四世界双侧正响应变化的窗口，其中60个在0.1ppm事件定义下也满足双侧至少3个检出记录。固定镜像库没有改lag、decay或阈值。

| TRAIN交叉诊断 | 静态双点 | 完整raw | 普通同核延迟 | 全镜像 | 去序镜像 | 最强同点单点 | 全30点单点 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 300–320秒，12/30 | 4/6 | 4/6 | 4/6 | 6/6 | 4/6 | 5/6 | 6/6 |
| 700–720秒，16/24 | 4/6 | 4/6 | 4/6 | 6/6 | 4/6 | 6/6 | 6/6 |

300秒窗口是一个值得保留的固定几何线索：镜像比相同测点的普通方法和最佳端点单点更好，去序后下降。但它来自事后多重筛查、每源仅两TRAIN实现；另一个位置的单点已经6/6，并且部分B/C世界双侧0.1ppm检出条件不充分。不能把它写成DEV有效、主创新成立或全局优于单机。700秒窗口连同点单点也已6/6，保留为反例。

这解释了我们接下来该检验什么：**双侧有效且存在时间结构时，固定镜像变换能否在相同输入、标定样本和预算下，比普通联合/延迟处理更稳定地保留源判别？**它需要一次新的、事前冻结的开发检查；不能在本轮看过失败后自动打开另一组DEV救分。

## 5. 核验、边界和停止

独立复算450个普通DEV源评分；24个三源C++推理/符号/后验检查通过，最大镜像特征差约{qa['max_CPP_feature_error']:.3g}。左右交换奇对称与单侧退化检查通过。未更改O24、原M1、0.04、0.1ppm或原负结果。

当前停止在：`NO_INDEPENDENT_MIRROR_DEV_GAIN / TRAIN_CONDITIONAL_SIGNAL_ONLY`。不跑M2/M3、机器人ROS、新世界、新seed或新House。唯一未执行提案见`NEXT_SINGLE_MIRROR_PROPOSAL.json`：使用已有世界，对300秒12/30候选建立新合同，所有强对照与普通单点保留；明确开发性质，不称新盲测。
'''
 (OUT/'SAME_HEIGHT_THREE_SOURCE_REPORT_zh.md').write_text(report,encoding='utf8',newline='\n')
 (PROJECT/'SAME_HEIGHT_THREE_SOURCE_REPORT_zh.md').write_text(report,encoding='utf8',newline='\n')
 write('REPRODUCE_COMMANDS.json',{'ordered_commands':[
 'python native/sameheight3_20261023/freeze.py',
 'python native/sameheight3_20261023/run_and_collect.py train',
 'python native/sameheight3_20261023/extract.py train',
 'python native/sameheight3_20261023/analysis.py train',
 'python native/sameheight3_20261023/mirror_shadow.py train',
 'python native/sameheight3_20261023/unknown_single.py train',
 'python native/sameheight3_20261023/run_and_collect.py dev',
 'python native/sameheight3_20261023/extract.py dev',
 'python native/sameheight3_20261023/analysis.py dev',
 'python native/sameheight3_20261023/mirror_shadow.py dev',
 'python native/sameheight3_20261023/unknown_single.py dev',
 'python native/sameheight3_20261023/train_motion_diagnostic.py',
 'python native/sameheight3_20261023/verify.py',
 'python native/sameheight3_20261023/degeneracy.py',
 'python native/sameheight3_20261023/audit_costs.py',
 'python native/sameheight3_20261023/finalize.py'],
 'success_exit_code':0,'first_failures_and_repairs':'ENGINEERING_EVENTS.json and logs, including original KeyError and interrupted I/O run',
 'external_reviewer_entry':'verify.py requires only bundled derived arrays/models, not a running VM or original gas archives',
 'frozen_stages_refuse_automatic_reruns':True})
 print('FINAL_SCIENTIFIC_REPORT_READY')

if __name__=='__main__':main()
