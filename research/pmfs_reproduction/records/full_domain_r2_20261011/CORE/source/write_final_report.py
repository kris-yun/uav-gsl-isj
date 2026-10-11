from common_r2 import *
import shutil,numpy as np
def md(name,s):(CORE/name).write_text(s.strip()+'\n',encoding='utf-8')
decision=dict(status='R2_REGISTERED_CAMPAIGN_COMPLETED_NO_AUTOMATIC_EXTENSION',main_choice=3,choice_text='Prioritize observation-conditioned source discrimination over fieldfit; qualified by coarse representation and finite reference support, not a proved unique evidence-operator fault',mechanism_level='R1 controlled D/V/readout composition evidence retained; R2 full-domainCOARSE readout sourceNLL gains supported',method_level='Registered coordinate confirmationNOTMET; this exact construction ends withoutseed/temperature/model repair',ordinary_correct_model='Useful affordable strong physical reference, insufficient for reliable coordinate inference onall six',compression_necessity='NOT_ESTABLISHED: no measured compute-body bottleneck atcurrent staticlibrary scale',atomic447='NOT_TESTED;32geometric regionscover447cells; cannotdeclare447atomic gain',memory_or_timevarying_wind='NOT_TESTED; observationperiodstaticCFD10',calibration='NOT_ESTABLISHED: proper truthloss/Brier improvement isnot reliability calibration',novel_method='NONE_TRAINED_OR_CLAIMED',no_unique_rootcause_claim=True,three_observation_sourcegroups_only=True)
dump(CORE/'FINAL_METHOD_NECESSITY_DECISION.json',decision)
md('FINAL_METHOD_NECESSITY_DECISION_zh.md',r'''
# R2：全域普通模型价值与创新必要性判决

这次确认了读出保真在全域粗源竞争中具有概率价值，否证了“有预测收益就自然获得稳定坐标改善”的解释。本轮全部注册分支已经结束，不能再笼统地写成“根因还没找到，继续HOLD”。R1活动域、垂向运动与读出组成因素的干预证据保留；本轮没有重复其38次因素实验。

**判决：选择任务书选项3作为下一项研究问题——观测条件下的源判别；当前未建立动力学压缩或新网络的必要性。** 这是问题分流，不是已经证明证据算子是唯一根因，更不是已经完成新算法。

| 50块终点，R01、同源支持同原生评分 | 开发19份 O0→O1 | 前瞻6份 O0→O1 |
|---|---:|---:|
| 真源区域负对数损失 | 2.426511→2.113134 | 3.354986→2.086147 |
| 原生 Top-5% 距离 | 2.573014→2.395073m | 2.218220→2.309638m |
| MAP距离 | 3.305136→3.293278m | 2.406331→2.724995m |
| 全后验均值距离 | 2.709447→2.271790m | 2.678394→2.015835m |
| 实际受体事件Brier | 0.162895→0.051053 | 0.153333→0.036667 |

开发门通过；新六份三个源组的平均源NLL都下降，受体预测也改善。但 Top-5%平均距离增加0.091417m，未通过事前“不退化”确认标准，必须结束这一构造而不增加种子。Z04的Top-5%从1.291604增至3.934045m、MAP从1.767767增至4.981215m；Z05在Top-5%上改善，但MAP退化。全部负例保留。没有以平均概率改善遮盖坐标伤害。

## 能说清的具体机制边界

P3-O0与P3-O1共享完全相同的3D状态、参考seed、时刻、源目录、面积先验、native blur和评分；唯一改变量是中心投影占用 versus 实际PID严格检出。因此这对比较提供读出组成因素的源概率证据。N_POINT_ALL→P3还同时改变了粒子/羽团注入、sigma/浓度物性、高度、风场分量及传播状态，不能全部归于读出。N0保留原自适应树，不能与粗点源库相减成纯处理效应。

“正确3D”在这里指追溯生成合同与已核验数值读出，不等于真实风洞/湖岸物理已独立验证，也不等于两份参考足够精确地估计总体响应分布。

## 什么阻碍了可靠源坐标

1. 有限二值观察确有多义：32源在B4计划末端形成22个两参考事件等价类，PUBLIC_B为25类，最大类分别6源、3源。同样的有限事件，经同一原生建图也具有相同均值图。这是有限样本等价，不是总体物理不可辨识证明；连续ppm和四个预登记辅助受体差异已保留。
2. 粗源表示不能产生未模拟的细格信息。本轮32区域覆盖447合法源格，区域代表点由几何选取，面积先验，概率均匀回填。新观测源在代表点，开发源还存在共同离散化误差。区域质量最大的源与单格密度最大的源可能不同。
3. 官方 `ExpectedValue(grid,.05)` 选取排序前5%的自由格数，本图447格实际取23格，不是前5%概率质量。1125份普通后验中1000份在截取边界有未全部选入的并列格。实际C++结果仍作为主指标；额外提供并列格坐标包络及代表点均值，不能事后用它们改成通过。
4. 两参考有明显敏感性：前瞻P3-O1的R0/R1真源NLL平均绝对差0.855818。不能选最好参考、加参考直到正确，或把6个realization视为6个完全不同信息的观测序列；本轮6份仅4种二值历史，其中Z02/Z03零检出而保留。

## 创新必要性

64份1000s参考的生成共325.56s，生成加批量查询405.83s，索引/建图/blur/保存计入后共620.66s；每参考平均9.70s。64次native点源前向5.47s。缓存后一次观测前缀的15个评分组合平均0.0431s。这些是当前VM、静态场、32源、两个固定受体计划的实际成本，不是无人机在线实时性能。

没有证据要求为了本例训练随机动力学压缩模型。447原子模式事前以保守72s银行额度和1.5因子拒绝，不能结果出现后切模式；优化后按实际均值的447源两参考外推约8669.9s，加入1.5因子仍超过150分钟物理预算。该外推不是实验，但明确说明原先模式保守、不能把原额度当运算本体瓶颈。

普通正确模型已经是有用的强参考，却没有解决所有坐标判别。E-event/A1亦按合同完整计算，没有稳定变成可靠全域解；它们的评分尺度与原生不同，不能跨头比较NLL百分比来挑胜者。事件头采用均值边缘复合评分温度1，地图头采用固定负均方距离，后验可能较平；这不否证所有事件逆推法，也不授权事后调温度。

**给PRO的聚焦问题：在有限事件等价类、有限参考和粗源表示均被显式记录的前提下，是否可以定义一种源盲、可否证的观测条件源判别目标与证据构造，使源概率增益稳定转化为物理坐标收益？先给出该目标的增量必要性及最小公平对照，而不是继续提高场拟合或重做D×V。**

原子分辨率、跨场景、时变风/记忆必要性、论文30次统计复现均未测试；不以这些未测项撤销已有机制证据，也不据此再无限补同类审计。当前没有完成可清楚辩护的SCI主算法。
''')
md('README_zh.md',r'''
# PMFS R2 一次性交付

先读 `FINAL_METHOD_NECESSITY_DECISION_zh.md` 和 `SEND_TO_PRO_zh.md`。本轮完成32几何粗源区域全覆盖、64三维参考、64原生点源前向、19已见观测与6预登记新观测，所有普通评分头及负例。没有新CFD、导航goal、网络训练、L修复或额外seed。原VM保持运行，原始R1/E3/B4冻结。

## 复核

解压CORE和RAW到短目录；安装Python+NumPy后运行：
```
python -B CORE/source/verify_r2.py --core CORE --raw RAW
```
只提供CORE也可复算1125份源后验、概率质量、源损失、覆盖与判决；提供RAW增加所有包内哈希、6580个已用/代表帧和280个固定实际受体PID查询的独立浮点复算。它不会连接VM、启动GADEN、ROS或新更新。`source/`其他文件是执行血统，**不要为复核运行生成脚本**。

## 数据组织

- `inference_inputs/`及`future_inference_inputs/`：冻结候选预测、过去观测与native测量地图；不含真源映射。两个目录共享同一预测SHA。
- `evaluation_only/`：真源、种子角色及事前未来选择；仅评价使用。
- `development_inference/`、`future_inference/`：1125份普通后验及真实native位置/方差，另75份N0快照。N0原生树结果不可与统一点源作纯读出效应相减。
- `PAIRED_SOURCE_METRICS.csv`、`FUTURE_PAIRED_SOURCE_METRICS.csv`：全部单源/区域损失、rank/ties、MAP、官方Top-5%、均值、1m邻域、最强错误区域。前缀20/35/50。区域NLL主端点和细格NLL明确分开。
- `RECEPTOR_METRICS`、`REFERENCE_SENSITIVITY`、`EVENT_EQUIVALENCE`及其FUTURE版本：受体预测、两参考敏感性和有限等价类。
- RAW `references/`、`observations/`：每银行94个实际使用/代表帧、全部1803帧的SHA/时间索引、完整45000数值查询、物理/RNG/参数与时间日志。未携带从未使用帧的原始字节，详见RAW_COVERAGE。
- RAW `N_POINT_ALL/`及`observations/*/N0/`：native随机状态、候选图、树、评分和后验；RAW `diagnostics/`逐源逐评分格贡献。
- `EXTERNAL_TASK_ARTIFACT_SHA256.csv`：外部本轮完整工件索引；未携带实际二进制/旧父银行的边界显式标记，不暗示它们可由ZIP独立重建。

源码差分合同只允许P3主配对的`readout`改变。576张图的独立普通logscore与真实native评分最大差1.95e−14；原生Top5的并列排序结果保留，不能假设跨实现完全相同。三项盲性及前缀测试均通过。

32粗源不等于447逐格源预测。447主要是地图评分/回填格；94个实际帧不等于完整1803原始帧全部装包。50测量块来自10停留位置，时间相关，未作为独立实验。所有0检出银行保留。
''')
md('SEND_TO_PRO_zh.md',r'''
# 直接转发PRO

本轮按你给的R2连续合同完成，没有再重做R1因素实验或修L。采用结果出现前冻结的32几何区域COARSE目录，覆盖全部447合法源格；每源2份3D参考，N_POINT_ALL使用相同32点、面积先验和评分。855份开发普通后验、270份新观测后验、75份原生N0快照，连同全部参考/RNG/原始片段/成本交付。

机制已经定位到有干预证据的组成因素；这次不再笼统判“原因未知”。P3-O0/O1唯一变化是同状态的中心投影读出 versus 实际PID检出。开发19份源区域NLL从2.426511降至2.113134；开发门通过后，按事前冻结源与seed生成6份新观测。新六份NLL从3.354986降至2.086147，三个源组全部改善；实际受体Brier从0.153333降至0.036667。**但Top-5%平均距离2.218220→2.309638m，MAP2.406331→2.724995m，确认门未通过，未追加seed。** 全均值距离反而2.678394→2.015835m，故必须区分概率、MAP和均值收益。

最重要反例是Z04：区域NLL改善0.549815，却Top-5%1.291604→3.934045m，MAP1.767767→4.981215m。所有六份保留，Z02/Z03零检出没有删除。两份参考/有限二值记录存在混叠：32源在B4/PUBLIC_B末端分别只有22/25种事件参考类；连续ppm和四辅助受体差异已完整提供，不能将其升级成总体不可辨识。

还有表示问题必须读：32区域均匀回填使1125份普通后验中1000份在官方Top-5%截取边界出现部分并列格；官方函数取前23格而不是5%概率质量。我保留真实native结果作为原主门，提供额外代表点均值与并列格坐标包络，未事后改成功标准。新观测源正好是几何代表点，开发源共同离散化误差另报。N0/N_POINT/3D信息权限与源表示变化单列，只有P3-O0/O1能作为纯读出效应。

计算方面，64参考库实际端到端约621秒，缓存后15个评分组合每观测前缀平均0.043秒；没有证明动力学压缩的必要性。事前原子模式保守排除，现阶段不切447原子模式也不谎称已经测试。所有普通事件/A1对照已完成，不把它们叫新算法，不跨评分头减NLL百分比挑胜者。

请这一次集中判断：**既然正确读出改善源概率却不能稳定改善坐标，而且普通物理参考在本静态任务中可负担，下一项原创目标应如何定义为“观测条件下的源判别”，并显式处理有限参考、候选等价类和粗源表示？当前是否还欠原子源公平性证据，才能把问题唯一归到证据构造？** 不需要再要求一轮D×V，也不要先引入PFCG/记忆网络；本轮没有建立计算瓶颈或时变风记忆需求。

复核入口：`README_zh.md`、`FINAL_METHOD_NECESSITY_DECISION_zh.md`、两个完整source posterior NPZ、全部paired metrics、equivalence与cost。`verify_r2.py`可离线复算，无VM/新仿真。原R1/E3/B4和所有STOP均保持冻结。
''')
md('REGISTERED_BRANCH_COMPLETION_zh.md',r'''
# 注册分流完成情况

| 分支 | 本轮结果及边界 |
|---|---|
| R-A 普通正确模型 | 源概率/Brier有价值；前瞻坐标确认未过。已完成强参考及反例，不能说普通模型全部解决。 |
| R-B 运算成本 | 实测生成/查询/索引/保存、缓存评分全账已完成；当前不支持运算本体瓶颈/压缩必要性。 |
| R-C 证据构造 | 完成E-event/A1全矩阵、逐格贡献、单参考、先验、普通头尺度与退化结果。不是“换Bayes”的原创。 |
| R-D 有限等价类 | 两参考事件/A1精确等价类、连续浓度与辅助受体差异全部交付；不证明总体不可辨识。 |
| R-E 源表示/树 | 原生N0与共同点源支持分开；面积先验诊断、代表点偏差、Top5并列截取全部交付。未构造不存在的同状态原树反事实，不将组合差异归给3D。 |
| R-F 未测端点 | 447逐格原子模式事前成本未放行，不能由32区图填充宣称完成。所有已登记有效分支完成，没有共有输入故障。 |

开发門通过后恰执行6份注册观察，没有第7份。前瞻不通过后没有技术“修复”、增seed、换参数或更换源。唯一执行技术修复是加载native共享库路径；物理过程没有重跑。关闭所有本轮生成worker已自行正常结束，未关闭VM或移动其他项目文件。
''')
for p in [WORK/'write_final_report.py',WORK/'final_facts_and_runtime.py',WORK/'plot_r2_diagnostics.py']:shutil.copy2(p,CORE/'source'/p.name)
print(json.dumps({'decision':decision,'reports':'written'}))
