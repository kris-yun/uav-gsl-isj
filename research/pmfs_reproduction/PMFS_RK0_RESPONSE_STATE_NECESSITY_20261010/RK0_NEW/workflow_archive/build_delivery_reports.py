"""Create derived reports/plots from completed frozen RK0 outputs. No experiment."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import csv,json,math,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE=Path(__file__).resolve().parents[2]
OUT=BASE/'outputs/PMFS_RK0_RESPONSE_STATE_NECESSITY_20261010'
WORK=Path(__file__).resolve().parent
def js(p): return json.loads(p.read_text(encoding='utf-8'))
def rows(p):
    with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def write(name,s): (OUT/name).write_text(s.strip()+'\n',encoding='utf-8')
def csvsave(name,rr):
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)

qa=js(WORK/'RK0_SCIENTIFIC_DECISION_QA.json')
ind=js(WORK/'independent_rk0_complete_audit/RK0_INDEPENDENT_RESULT.json')
pairs=rows(OUT/'PAIRED_U_S_HELDOUT_RESULTS.csv')
ledger=js(OUT/'EXECUTION_LEDGER.json')
bias=rows(WORK/'independent_rk0_complete_audit/INDEPENDENT_REFERENCE_BANK_POSE_RESIDUALS.csv')
conserve=rows(WORK/'independent_rk0_complete_audit/INDEPENDENT_KERNEL_POOL_CONSERVATION.csv')
maxpool=max(float(r['absolute_difference']) for r in conserve)
biastable=[]
for pose in [0,1]:
    for bank in ['C7_0','C7_1','K2_0','K2_1']:
        u=next(r for r in bias if r['model']=='U' and r['reference_bank']==bank and int(r['pose_id'])==pose)
        s=next(r for r in bias if r['model']=='S' and r['reference_bank']==bank and int(r['pose_id'])==pose)
        biastable.append(dict(pose_id=pose,reference_bank=bank,native_particle_sum_mean_ppm=float(u['mean_native_particle_sum_float64_ppm']),U_mean_ppm=float(u['mean_reconstructed_concentration_ppm']),S_mean_ppm=float(s['mean_reconstructed_concentration_ppm']),U_residual_ppm=float(u['mean_reconstructed_minus_native_ppm']),S_residual_ppm=float(s['mean_reconstructed_minus_native_ppm'])))
csvsave('POOLED_CONSERVATION_SOURCE_CONDITIONAL_EXAMPLES.csv',biastable)

decision={
 'numerical_qualification':'PASS_INDEPENDENT_RECOMPUTATION',
 'PRO_same_bank_same_scorer_readout_contrast':'PASS_CONDITIONAL_EXPLORATORY_MECHANISM',
 'gas_navigation_support_intervention':'PREVIOUS_M3_CONDITIONAL_EFFECT_RETAINED',
 'U_current_two_source_choices':'SUFFICIENT_FOR_ALL_FIVE_OBSERVED_DECISIONS_INCLUDING_O0',
 'S_added_value':'POSITIVE_MARGIN_IN_4_OF_4_INSPECTED_TASKS_WITH_PARTIAL_RECEIVER_RESPONSE_SUPPORT',
 'same_cap_R':'S_GREATER_SOURCE_MARGINS_THAN_THIS_ONE_NONPHYSICAL_GROUPING',
 'full_heldout_receiver_response_improvement':'NOT_ESTABLISHED_COVERAGE_AND_COUNTEREXAMPLES_REPORTED',
 'CSCG_necessity':'NOT_ESTABLISHED_FIXED_PHYSICAL_BINS_ALREADY_PROVIDE_OBSERVED_GAIN',
 'new_deployed_localization_gain':'NOT_TESTED',
 'B4_unique_root_cause':'NOT_IDENTIFIED_MULTIPLE_SUPPORTED_COMPONENTS',
 'next_action':'REVIEW_COVERAGE_AND_PROSPECTIVE_CORRECT_BASELINE_DESIGN_BEFORE_ANY_CLONE_PROTOTYPE_OR_NEW_GAS',
 'no_auto_execution':['24_new_realizations','additional_state_counts','CSCG_training','ROS_navigation','new_CFD'],
 'source_tasks':4,'independent_new_tasks':0,'new_physical_realizations':0,
 'U_S_full_point_coverage_200':[144,62],
 'U_S_total_event_error_bounds_200':[[27,34],[16,33]],
 'pooled_conservation_max_abs_ppm':maxpool,
 'research_scope':'Previously inspected B4 two-source/one-trajectory oracle readout compression; not temporal transition learning or joint source posterior calibration.'
}
write('RK0_FINAL_SCIENTIFIC_DECISION.json',json.dumps(decision,ensure_ascii=False,indent=2))

evidence=[
 dict(component='导航域约束气体运动',evidence='M3同柱平均风/点源/壁面/预算的支持干预，真源评分增加约49–51倍',qualification='CONDITIONAL_INTERVENTION_SUPPORTED',not_shown='原B4风下部署定位改善；唯一根因',next='保留；正确三维连通并非投影并集'),
 dict(component='中心占用代替受体读出',evidence='同3D参考同447格原生相似度：中心−0.258862/PID+4.008207；同blur仍翻转',qualification='CONDITIONAL_READOUT_CONTRAST_SUPPORTED',not_shown='高度单独必要；动态风/传感器记忆原因',next='响应保持普通基线'),
 dict(component='共享核跨状态混合',evidence='U pooled质量守恒但K2参考48/49正检出，F35/36；固定S为40/40',qualification='ADDED_DIAGNOSTIC_VALUE_WITH_COVERAGE_LIMIT',not_shown='完整响应保真或克隆必要',next='参考覆盖与普通固定分箱的前瞻比较'),
 dict(component='高度与尺度分箱',evidence='S四任务两种源评分margin均提升；只两任务共同支持MSE下降',qualification='PARTIAL_POSITIVE_ORACLE_DIAGNOSTIC',not_shown='全量预测改善；高度/尺度效应单独分离',next='不得自动增加状态数'),
 dict(component='隐藏状态转移/记忆',evidence='本轮没有轨迹身份、转移拟合或短时预测',qualification='NOT_TESTED',not_shown='CSCG/HMM及非Markov记忆必要',next='身份/物理转移合格后再预注册'),
 dict(component='空间证据依赖与自适应细分',evidence='历史M0归因；本轮未更新原生后验',qualification='NOT_RESOLVED_BY_RK0',not_shown='对此两因素的因果分解',next='保持独立问题；不把margin作后验改善')]
csvsave('ROOT_MECHANISM_EVIDENCE_MATRIX.csv',evidence)

prefix='PARENT_M2M3_FROZEN/M2_FROZEN/frozen_B4_inputs/source/'
code=[
 dict(path=prefix+'gsl/PMFS/PMFSLib.cpp',line=211,evidence='PruneUnreachableCells形成导航连通的二维occupancy，传入simulations.initializeMap'),
 dict(path=prefix+'gsl/PMFS/internal/Simulations.cpp',line=355,evidence='同一时刻同一XY格至多hitMap++一次；粒子数量、Z及sigma未进入该记录定义'),
 dict(path=prefix+'gsl/PMFS/internal/Simulations.cpp',line=402,evidence='moveAlongPath调用measuredHitProb.freeAt及visibilityMap限制气团运动'),
 dict(path=prefix+'gsl/PMFS/internal/Simulations.cpp',line=512,evidence='GaussianBlur后除blurredFreeSpaceMask并clamp到0–1'),
 dict(path=prefix+'gsl/PMFS/internal/Simulations.cpp',line=240,evidence='源评分跨自由格乘积；probabilitySingleFrequency=1−D|p−q|并confidence插值'),
 dict(path=prefix+'sensor/fake_gas_sensor.cpp',line=179,evidence='model30 PID分支；simulate_pid在323行，校正因子关闭时sum原气体ppm'),
 dict(path='RK0_NEW/source/verify_raw_receiver_queries.py',line=106,evidence='3sigma截止、3DLOS、sigma依赖高斯峰值、粒子ppm加和与原顺序float32'),
 dict(path='RK0_NEW/source/run_rk0.py',line=23,evidence='reference-only共享核与固定四物理类；全粒子分母，源身份不作为kernel/class输入'),
 dict(path='RK0_NEW/source/run_rk0.py',line=60,evidence='完整数量投影与未覆盖kernel显式UNSUPPORTED；未匹配状态不置零'),
 dict(path='RK0_NEW/source/run_rk0.py',line=115,evidence='每realization总浓度阈值后合并参考事件；不是均值场阈值')]
csvsave('SOURCE_CODE_EVIDENCE_INDEX.csv',code)

marginrows=[]
for p in pairs:
    marginrows.append(f"| {p['bank']} | {float(p['U_truth_directed_mean_log_margin']):.6f} | {float(p['S_truth_directed_mean_log_margin']):.6f} | {float(p['delta_Brier_contrast']):.6f} | {p['common_complete_support_blocks']} | {p['U_MSE_common_support']} → {p['S_MSE_common_support']} |")
bt='\n'.join(f"| {r['pose_id']} | {r['reference_bank']} | {r['native_particle_sum_mean_ppm']:.6f} | {r['U_mean_ppm']:.6f} | {r['S_mean_ppm']:.6f} |" for r in biastable)
write('RK0_RESPONSE_STATE_NECESSITY_REPORT_zh.md',r'''
# RK0：共享响应核与有限物理状态的必要性检验

## 给PRO的结论

本轮完成了交接书第一阶段的一次有界U/S/F计算，以及预先规定、同样最多四类的非物理R对照。**得到有限物理状态具有附加源判别信息的探索性正结果，但并未证明需要CSCG。**共享核U已经保持原B4观测O0及四份旧留出的全部二源选择；S改进的是源假设评分差，分类准确率没有增加。S还产生覆盖下降和局部预测退化，应与正结果一起审核。

现阶段不应退回“什么也不知道”的笼统HOLD，也不应把“固定四类比共享核更强”升级为主创新。可以具体保留两个失效组成因素：M3的气体传播支撑受导航约束，以及同物理过程下中心占用读出未保持受体判别。新增结果进一步指向**把不同响应组成混成一个共享条件均值，会保住总体均值却损失源条件检出结构**。这仍不是B4全部错误收敛的唯一根因。

数值资格为PASS；下一研发门为“先解决覆盖并规划新的正确常规基线对照”，当前不进入克隆训练或24份新气体生成。

## 1. PRO新增证据已独立复算

先检查提供的脚本只读范围，保留原PRO ZIP及全部21项声明SHA；旧联合包1510项SHA未变，嵌入M2与独立M2包877个文件字节相同。随后执行PRO脚本，并用不导入其函数的整数/标量脚本独立核对。

| 同参考、同原生D=0.4相似度 | C7−K2对数差 | 源排序 |
|---|---:|---|
| 3D中心投影占用，不模糊 | −0.258862065822 | K2 |
| 原生受体高度PID阈值频率，不模糊 | +4.008206781851 | C7 |
| 中心占用，相同原nav分母模糊 | −0.508908775650 | K2 |
| PID频率，相同原nav分母模糊 | +3.303354838685 | C7 |

物理参考、50块时刻、447格p/confidence及评分函数相同，读出定义本身足以翻转当前源对排序。这恢复了高度、尺度、数量相加与遮挡等多个因素，没有证明高度单独必要。447格是oracle物理查询，不是447次独立传感器测量；这是旧任务的确定性反事实，不是新任务或新定位成绩。

原ALLXY分子除旧nav分母的弱真源翻转需修正解释：clamp之前111/119个评分格超过1，峰值3.60/4.46；全框匹配分母后margin为−0.754449464330，没有超过1。原文件和原值保持冻结，新补充说明指出该弱翻转不是合格概率恢复。M3运动域干预数值仍通过，投影并集不构成定位性能上界。

OpenCV版本字面值及NumPy标签类型差异单独记录，新可移植复核按原科学容差、严格整数成员资格和显式标签公式进行。**不是声称PRO环境下旧版验证器原样全PASS。**详见PRO_REVIEW/PRO_INDEPENDENT_RECOMPUTATION_zh.md。

## 2. 本轮究竟执行了什么

只读M2的八份已生成物理银行和B4冻结受体轨迹。C7_0/1、K2_0/1为reference；C7_2/3、K2_2/3是已经被分析过的探索性留出。C7源为(−3.2,−3.3,−0.5)，K2是原错误峰候选(−1.675,1.495,−0.5)。这个候选对具有历史结果选择偏差，不能替代几何预选的新任务。

50块观测对应10次停留；51条成员包含block40的替代成员，不能多算一次曝光。每bank49个唯一快照，重复frame1001按冻结50块计划在核分子和分母同权重计入。所有块及粒子记录有时间相关性，统计单位不能改称200次独立实验。

核在参考的全部物理时刻上拟合为stationary响应，跨源共享，不是按某个留出时刻配对取h。它依赖本条已知轨迹的十个精确受体位姿；没有学习任意位置的响应函数，没有学习短时转移或未来预测。参考全时段离线构造属于本次oracle设计，不能声称在线因果时序模型已经实现。

执行前冻结543项输入SHA、实现源码、资源与判定门。输出U/S/F源盲事件及评分并保存SHA后，才读取生成源映射用于分析。R的salt/分组/触发规则也在前置合同冻结；它是在探索性门通过后的预设条件对照，不是再寻找有利随机分组。

本轮没有新的气体、CFD、候选输运前向、ROS定位、VM或模型训练，也没有增加状态数。计算内容是旧快照逐粒子读出和响应压缩；调用已有数学实现复算受体贡献，不调用物理仿真程序。

## 3. 模型的可计算定义

以原(−7.55,−7.88)原点、0.25m建立独立气体计数格，数学floor；保留导航非自由格及旧二维框外格。此处与框外原生C++截断的差别明确写入合同，不能冒称native二维模拟完全等价。

对参考粒子曝光j、受体a，原生贡献φ(j,a)包括3σ截止、三维LOS、σ依赖高斯峰值、气体单位与float32原累加。任一零贡献仍是完整分母的一部分。

`h_U(c,a)=Σ参考曝光 φ(j,a) / 参考曝光粒子数(c)`；`Ĉ_U(a)=Σ_c N(c)h_U(c,a)`。

S在同一XY格内按参考全局曝光加权中位高度与sigma切成最多四类，公式同U，改用N(c,k)与h(c,k,a)。切点z=0.8293430805206299m，σ=39.99423599243164cm；切点以上含等号。没有以真假源标签分裂，没有看留出信息调边界。

四个reference银行各有两份每源，但核不是等bank均值：每粒子曝光同权，C7_0/1为48493/49435，K2_0/1为65817/65315。这是前置定义的粒子总体条件均值，反映所选参考混合分布，不保证对新的源分布不变。

R用native float32(x,y,z,σ)的固定SHA256散列mod4，排除源ID、时钟及行号。它与S有相同四类上限，但实际活跃类更多：U789、S2803、R3105；三者覆盖同789个参考XY格，完整曝光分母均229060。因此R是一个同上限、非物理组织的控制，**不是已经排除所有容量、参数量或复杂度混杂**。

F是已有原生三维/PID受体读出端点。F不是有限样本任务分数的性能上界。U/S/R都需要真实粒子计数，S还读取真实高度/尺度类数量，属于oracle信息，部署中的隐状态估计未实现。

先对每个realization总浓度使用nativefloat32 0.1ppm阈值，之后才合并两份参考的事件，Jeffreys(.5,.5)给出p∈{1/6,1/2,5/6}。没有对跨实现平均浓度直接阈值。保留的总体数量随机性只来自这有限几份银行；类内响应方差被h条件均值压掉，没有建立完整随机集合滤波器。

源任务指标为50块平均marginal log与Brier对比；它们不是50块独立性的证明，也不是原生447格相似度的联合似然，不能softmax后称已校准源后验。当前没有更新原生后验或导航。

## 4. 源任务：有附加差异，但U已能选对

U、S、R、F都在四份留出上由两种评分选对生成源；O0原B4事件也都选C7。S对四份留出同时改善真−错平均log差和错−真Brier差，R的参考事件及源评分则与U完全相同。

| 旧留出银行 | U平均log差 | S平均log差 | S新增Brier差 | U/S共同完整点数/50 | 同点浓度MSE，ppm² |
|---|---:|---:|---:|---:|---|
'''+'\n'.join(marginrows)+r'''

只有C7_2和C7_3同时达到预设“共同支持MSE降低＋源评分差增强”探索门。K2_2同点MSE反而升高；K2_3没有一个全状态覆盖点，不能报告点MSE。共同支持总共62/200，不能把这个子集推广到全时段。

拆开正确源与错误源的绝对分数，正结果更清楚：C7两份留出的正确源预测本来就是参考50/50正检出，S没有改变正确源log/Brier，margin增益全部来自压低K2错误假设；K2两份留出则确有正确源proper预测改善。不是每种真实物理状态都预测得更好。

K2参考的positive block数为U/R48、49，S40、40，F35、36。共享均值核把K2检出结构抹得过于接近C7，物理分箱恢复了一部分区别。S在K2_3的margin超过F只是有限两参考样本的结果，不能写成压缩优于完整物理。

完整各候选分数、概率与逐块loss在SOURCE_BLIND_SCORES_*.json；正确源绝对log/Brier与分析表在independent_scientific_review/中。

## 5. 受体预测：缺失不能置零，局部反例必须保留

reference包含的所有状态当然有kernel；旧留出仍有未出现过的XY或类。规则是N>0且h未见时点预测写UNSUPPORTED，不补零、不借留出均值、不扩大类别。用已知非负贡献下界与固定单粒子峰值上界判断是否可确定阈值事件；上下界只针对未知h，不包含已覆盖类的压缩误差，**不是物理真值置信区间**。

| 银行 | U完整点/50 | S完整点/50 | U全量事件误差界 | S全量事件误差界 | 解释 |
|---|---:|---:|---:|---:|---|
| C7_2 | 47 | 16 | 1 | 1 | 同点MSE改善，事件误差不变 |
| C7_3 | 48 | 37 | 1 | 3–4 | 同点MSE改善但检出退化 |
| K2_2 | 49 | 9 | 22 | 12–18 | 阈值检出改善在未覆盖界下仍稳健，浓度MSE退化 |
| K2_3 | 0 | 0 | 3–10 | 0–10 | 点预测无完整支持，事件区间重叠 |
| 总计200 | 144 | 62 | 27–34 | 16–33 | 总误差区间重叠，整体稳健改善未证实 |

S只有992/238448=0.416%的粒子曝光缺少kernel，但影响138/200个整点预测。一份实现的每个时刻都出现稀有状态，因此“少数粒子没有覆盖”不能解释成数据资格已基本通过。事件可由下界确定不等于浓度点已支持：U193/200、S183/200事件确定。详细未知状态及每块区间全部交付。

## 6. 总体均值守恒仍可损失源条件响应

独立检查三模型每个受体的`Σ全部参考 N*h=Σ原生逐粒子贡献`，最大绝对差'''+f'{maxpool:.3g}'+r'''ppm。这是加权核构造的守恒恒等式，不是留出保真证据，更不保证每源条件响应。

下面列出每个固定受体对参考全部50计划帧曝光的响应均值；不是在该站实际采样50次，更不是50次独立测量。Native列使用float64逐粒子贡献和作守恒端点，事件F仍使用原生顺序float32总量。

| 受体pose | 参考bank | Native均值ppm | U均值ppm | S均值ppm |
|---|---|---:|---:|---:|
'''+bt+r'''

pose0的S显著减轻混合偏差，pose1仍有约1.47–1.55ppm残差。**四类不是充分状态**：类内细XY位置、连续高度/尺度、遮挡及其他条件仍可不同。这里按源bank切片只用于事后解释；源ID没有进入共享kernel。不能根据这张表新增源特定核，再冒称源盲模型。

## 7. 源码与物理组成因素

冻结源码可将现象落实到具体计算路径，完整行号见SOURCE_CODE_EVIDENCE_INDEX.csv：

- PMFSLib对二维图PruneUnreachableCells后将occupancy交给Simulations；moveAlongPath用同一measuredHitProb自由格/visibility约束气团移动。M3干预已证明该约束实质影响评分，条件是固定柱平均风而非原B4全部设置。
- Simulations记录每时刻“此XY格是否至少有一个中心”，同格多个粒子只加一次。高度、sigma和浓度加和未进入此hit定义；后续统一blur不是原生三维PID响应算子。
- 原生受体查询按单粒子sigma、真实受体XYZ与三维遮挡计算贡献，再将ppm相加；PID model30在校正关闭时返回总浓度。中心占用与PID阈值是不同随机变量，PRO同bank同scorer实验已实证区别会改变排序。
- 本轮从中心占用改为保数量共享核U；U保持整体响应均值，却混合源条件内部组成。固定高度/尺度S能部分恢复该组成，但四分类仍保留较大残差。剩余误差不能唯一归为高度、sigma或某一个未观测物理变量。

因此目前是**有条件支持的多环节失真链**，不是单个配置错误，也不是已证明的唯一物理根因。空间证据依赖、随机输运、自适应细分的贡献未在RK0中分离。

## 8. 验证、资源与证据完整性

先以旧native C7_0 frame611锚点复算得0.9068903923034668ppm，abs/ULP均0；随后196参考快照×10位姿构成2,242,960贡献对，31,311正贡献、2,211,649明确零。全部204个原参考query总量与原生float32精确一致。零贡献没有删出229060加权曝光分母。

独立实现只读cache及原快照：196NPZ SHA、原filament数组逐位同一；全部核分子/分母/h再算、408条各模型预测、所有missing、两评分及配对表逐层通过，24个branch40配对一致。没有仅比较最终源选择。

计算批次一次、退出码0，监督墙钟60.35s，峰值RSS72.18MiB；600s/1GiB/2GiB上限未触发。新增计算文件约6.72MB，随后交付复制父证据不属于计算内存占用。资源日志、stdout/stderr及独立audit同时保留。

原始4d15d0d父提交、M2/M3报告/快照/源码/验证器及已执行RK0源码/合同全部未改。新报告是补充解释，不回写历史结论。主包保留父证据及PRO原包，不需VM、SSH或网络即可复算。

## 9. 对下一步的明确决定

**可以保留“有限物理状态改善源条件响应结构”的机制候选，暂不开发CSCG。**理由不是抽象HOLD：U已经完成当前二源决定；固定四物理类得到额外margin，而CSCG没有与固定分箱比较、没有合格转移身份、也没有部署隐状态估计。普通分箱不是克隆方法的胜利证据。

下一次新物理任务之前应冻结：kernel缺失处理、参考覆盖标准、源几何选择及普通正确响应基线。不得用本次结果增加状态数或选择更有利旧源、轨迹、mask与种子。若PRO认可有限原型入口，应先将“共享响应＋固定分箱”设为强制基线，并设计响应差异驱动分裂在相同信息/有效状态预算下的否证对照；不能只比较原PMFS。

PRO建议的6源×4实现需要另行资源预算与批准，本轮未执行。跨场景、未知受体位置、动态风、时间转移、湖岸条件、校准源后验及闭环收益均未取得新证据。文献候选只作为交接思想保留，本轮没有独立文献/新颖性审查。

要请PRO集中判断三件事：①当前正结果是否足以投入一个有限响应保持原型，还是先扩大reference覆盖；②应如何处理共享核的条件混合与少数稀有状态，而不以源标签补核；③下一新任务的否证门如何要求候选超过正确常规响应与固定分箱。这样可直接决策，不再重复旧根因搜索。
''')

write('NEXT_RESPONSE_PRESERVATION_GATE_zh.md',r'''
# 下一关：先保证覆盖，再检验响应保持状态是否必要

当前已完成一次RK0，不再追加旧任务状态数、随机分组或新仿真。本文件是审核后的候选路线，不构成额外实验启动授权。

1. 先决定目标。若目标仅是当前二源分类，U已足够；S附加margin不能证明克隆必要。若目标是源条件检出与可靠边缘化，应将全量预测覆盖、proper绝对预测与margin一起验收，避免只奖励压低错误假设。
2. 在新物理数据生成前冻结缺失处理。任何N>0且kernel未出现都不得置零。可以研究由连续几何/LOS构造的常规响应或reference-only平滑，但必须有统一来源、固定参数与新留出审查；不能本轮事后补值冒充原门通过。
3. 源与轨迹按几何/安全合法性预选，不能取原错误峰或按检出结果挑任务。PRO的6源×(2参考+2留出)是待预算建议，未执行；12个新留出亦不足以直接称发表级跨场景验证。
4. 原PMFS、正确气体域+响应普通基线、固定物理分箱、待测状态构造及折叠消融必须同观测、释放、风、受体、高度与预算。比较绝对正确源loss、排序/概率质量和未知状态覆盖，不能只追求场MSE或旧源选择。
5. 只有候选超过固定分箱/正确常规基线，且新任务有完整覆盖与独立收益，才投入CSCG或其他状态分裂；状态ID必须由物理轨迹/合法转移构造支持，快照序号不能当粒子身份。无人机动作控制受体采样，不控制气团运动。
6. 分箱有效但新构造无附加收益时，保留普通响应基线，停止克隆主创新；全量检出仍退化时，先审查类内方差与状态不足，不自动增为8/16/32类。

本轮决定：`LIMITED_PHYSICAL_STATE_DIAGNOSTIC_VALUE / NO_CSCG_NECESSITY_CLAIM / COVERAGE_BEFORE_PROSPECTIVE_TEST`。原M2语义E1未恢复，原R7/E3/B4/STOP结果不变。
''')

# Audit plot: paired-task margins plus missing-support event limits.
fig,ax=plt.subplots(2,2,figsize=(11,7.4),layout='constrained')
tasks=['H101','H102','H103','H104']; labels=['C7_2','K2_2','C7_3','K2_3']; x=np.arange(4)
colors={'U':'#777777','S':'#0072B2','R':'#D55E00','F':'#009E73'}
for j,m in enumerate(['U','S','R','F']):
    vals=[qa['source_scoring_from_frozen_inputs'][m][t]['truth_directed_mean_log_margin'] for t in tasks]
    ax[0,0].bar(x+(j-1.5)*.18,vals,width=.18,color=colors[m],label=m)
ax[0,0].set_xticks(x,labels);ax[0,0].set_ylabel('True minus false mean log score');ax[0,0].legend(ncols=4,fontsize=8);ax[0,0].set_title('a. Four inspected tasks; all models choose correctly')
for j,m in enumerate(['U','S']):
    q=qa['receiver_metrics_recomputed_from_frozen_predictions'][m]
    vals=[q[b]['full_point_count'] for b in labels]
    ax[0,1].bar(x+(j-.5)*.25,vals,width=.25,color=colors[m],label=m)
ax[0,1].set_ylim(0,52);ax[0,1].set_xticks(x,labels);ax[0,1].set_ylabel('Fully supported points / 50');ax[0,1].legend();ax[0,1].set_title('b. Sparse states reduce point coverage')
for j,m in enumerate(['U','S']):
    q=qa['receiver_metrics_recomputed_from_frozen_predictions'][m];lo=np.array([q[b]['event_error_lower'] for b in labels]);hi=np.array([q[b]['event_error_upper'] for b in labels]);mid=(lo+hi)/2
    ax[1,0].errorbar(x+(j-.5)*.14,mid,yerr=[mid-lo,hi-mid],fmt='o',capsize=5,color=colors[m],label=m)
ax[1,0].set_xticks(x,labels);ax[1,0].set_ylabel('Detection errors / 50');ax[1,0].legend();ax[1,0].set_title('c. Unknown-kernel bounds, not confidence intervals')
for j,m in enumerate(['U','S']):
    vals=[next(r[m+'_MSE_common_support'] for r in pairs if r['bank']==b) for b in labels]
    vals=[float(v) if v!='UNSUPPORTED' else np.nan for v in vals]
    ax[1,1].bar(x+(j-.5)*.25,vals,width=.25,color=colors[m],label=m)
ax[1,1].set_xticks(x,labels);ax[1,1].set_ylabel('Common-support concentration MSE (ppm²)');ax[1,1].set_title('d. Only 16, 9, 37, 0 matched supported points');ax[1,1].legend();ax[1,1].text(3,.14,'UNSUPPORTED',ha='center',fontsize=8)
for a in ax.flat:a.spines[['top','right']].set_visible(False);a.grid(axis='y',alpha=.15);a.set_axisbelow(True)
fig.savefig(OUT/'RK0_PAIRED_RESPONSE_DIAGNOSTIC.png',dpi=170)
fig.savefig(OUT/'RK0_PAIRED_RESPONSE_DIAGNOSTIC.svg')
plt.close(fig)
write('RK0_PAIRED_RESPONSE_DIAGNOSTIC_CAPTION_zh.md',r'''
# RK0配对诊断图说明

图为本轮实际计算数据，不是示意或算法性能表。a：S对四份旧留出增加真/错平均log分数差，U/S/R/F分类均4/4；b：完整点覆盖下降，S62/200、U144/200；c：针对未知kernel的事件错误上下界，不是独立样本置信区间，全量区间重叠，C7_3反例保留；d：仅同一共同覆盖子集MSE，K2_2退化、K2_3无可比点。四个银行是已被检查的同场景探索性实现，不是新的跨场景确认。
''')
print(json.dumps({'reports_written':True,'figure':str(OUT/'RK0_PAIRED_RESPONSE_DIAGNOSTIC.png'),'no_experiment_executed':True},ensure_ascii=False))
