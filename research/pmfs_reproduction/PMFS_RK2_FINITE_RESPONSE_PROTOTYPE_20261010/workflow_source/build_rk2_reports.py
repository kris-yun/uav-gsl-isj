"""Post-run reporting only. Does not fit models, query physics, or change frozen runs."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import json, csv, math, hashlib, time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parents[2]
WORK = Path(__file__).resolve().parent
RUN = BASE / 'outputs/PMFS_RK2_FINITE_RESPONSE_PROTOTYPE_20261010_REPAIR1'
OUT = WORK / 'final_reports'
OUT.mkdir(exist_ok=True)
started = time.perf_counter()
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def rows(n):
    with (RUN/n).open(encoding='utf-8',newline='') as f: return list(csv.DictReader(f))
def write(n,s): (OUT/n).write_text(s,encoding='utf-8')
result = load(RUN/'RK2_RESULT.json')
cap = load(RUN/'FINAL_CAPACITY_AND_STORAGE.json')
ledger = load(RUN/'EXECUTION_LEDGER.json')
contract = load(RUN/'contract.json')
fits = load(RUN/'FINAL_MODEL_RULES_AND_TRAIN_FITS.json')
source = rows('SOURCE_TASK_METRICS_AFTER_FREEZE.csv')
comp = rows('COMPRESSION_METRICS.csv')
cost = rows('READOUT_COST_SUMMARY.csv')
src = {(r['observation_id'],r['method']):r for r in source}
ct = {(r['role'],r['method']):r for r in cost}
nll = {k:v['equal_bank_source_NLL'] for k,v in result['source_summary'].items()}
gain = {m:(nll[m]-nll['L'])/nll[m] for m in ('U_query','S_query')}
o3 = float(src['O03','L']['source_NLL_nat'])-float(src['O03','U_query']['source_NLL_nat'])
train = result['offline_model_fit_and_search_wall_s']
prog = [json.loads(s) for s in (RUN/'PROGRESS_EVENTS.jsonl').read_text(encoding='utf-8').splitlines()]
sp = next(p['wall_s'] for p in prog if p['phase']=='S_QUERY_FITTED')
incremental_l = train-sp
f_time = float(ct['candidate_reference','F']['total_readout_wall_s'])
l_time = float(ct['candidate_reference','L']['total_readout_wall_s'])
s_time = float(ct['candidate_reference','S_query']['total_readout_wall_s'])
cache = BASE/'outputs/PMFS_RK1_PRO_REVIEW_BUNDLE_20261010/RK0_NEW/reference_contribution_cache/CONTRIBUTION_CACHE_RESULT.json'
cache_meta=load(cache)
cold = cache_meta['wall_seconds']
cost_note=dict(historical_reference_cache_wall_s=cold, historical_cache_result_SHA256=hashlib.sha256(cache.read_bytes()).hexdigest(),
    historical_cache_parent_relative_path=cache.relative_to(BASE/'outputs/PMFS_RK1_PRO_REVIEW_BUNDLE_20261010').as_posix(),
    fit_and_search_wall_s=train,incremental_L_search_wall_s=incremental_l,
    reference_F_readout_wall_s=f_time,reference_L_readout_wall_s=l_time,
    local_Python_F_time_reduction_fraction=(f_time-l_time)/f_time,
    illustrative_all_fit_break_even_queries=train/((f_time-l_time)/200),
    illustrative_all_fit_plus_historical_cache_break_even_queries=(train+cold)/((f_time-l_time)/200),
    illustrative_incremental_L_vs_S_break_even_queries=incremental_l/((s_time-l_time)/200),
    assumptions='Arithmetic illustration from measured warm-process means, not a deployment benchmark; excludes full propagation, transfer, future receiver changes and allocator overhead.')
write('COLD_START_AND_AMORTIZATION_NOTE.json',json.dumps(cost_note,ensure_ascii=False,indent=2)+'\n')

main = f'''# RK2-A：响应保真有限状态原型的完整结果

**最终判决：A_DEVELOPMENT_GATE_PASS_REQUEST_B_ONLY。本轮已结束；B 未批准、未生成。**

本次实现了一个共享四叶物理特征树 L，与采用相同查询损失的 U_query、S_query 和完整物理读出 F 比较。在不读取观察侧真实粒子、Q、φ、真源标签或真实尾项的源推断中，L 的四份旧开发材料等权源 NLL 低于普通两基线，幅度仅约 {gain['U_query']*100:.2f}% / {gain['S_query']*100:.2f}%。四种方法均已正确选择4/4个源，L 没有提高 Top1。它在这个有限二值接口上恢复了 F 的候选事件和源评分，没有超过 F。

这一结果足够按冻结合同提交下一项前瞻任务申请，**不足以宣称研究内容一主创新已成立、B4物理根因唯一确定或原生PMFS定位性能改善**。下面完整保留反例、开发材料条件和资源账目。

## 1. 本轮问题与事实边界

RK1 支持“相同二维统计下，隐藏的格内位置、高度、尺度和可见性组成影响传感器响应”。物理读出规律本身没有因源标签而改变；不同候选的隐藏组成不同，可能需要保留额外有限状态。RK2 检验这种信息能否用一个共享、有限、可解释路由恢复，并转为不使用测试隐藏状态的源条件预测。

这不是再次证明条件残差，也不是重新导航。新增工作只有旧输入上的统计拟合、一个树构造、局部原生数学读出及源评分。GADEN/CFD/ROS/VM/导航/网络训练新增执行均为0。历史B4、M0/M1/M2/M3、RK0/RK1及STOP/HOLD保持冻结。

## 2. 数据与训练/评价隔离

训练参考：C7_0、C7_1、K2_0、K2_1，4份完整旧实现，196个唯一帧、224296条唯一粒子记录；采样时间重复帧保留原权重，不算新独立实验。共同计划包含10处受体、每处5块、每份50查询。每受体20条训练总响应，由4份参考各5块构成。

旧开发评价：C7_2/3、K2_2/3，分别标作O00–O03，4份之前已经查看的实现。本轮新增独立物理实现为0。50块在停留点内相关；200查询、224296粒子、72候选划分都不能当作独立样本量。没有用这些数量构造显著性结论或置信区间。

源任务只有两个预定候选，每候选2份参考；不是447格完整源定位、距离误差评测或无人机闭环。几何、静态第10帧风与原始受体计划固定，不能检验时变风历史失配或湖岸泛化。

## 3. 两个实际分开的接口与源盲验收

`compression(snapshot, receiver)`用于明确的oracle编码诊断：输入完整模拟器状态，允许检查读出误差。

`infer(reference_forecasts_for_all_candidates, observed_gas, receiver_plan)`只读取每个候选自己的2×50预测浓度和观察端50个标量浓度。候选预测生成完并冻结哈希，才读取测试压缩状态；源概率冻结之后才读取真源映射评价。infer数据类不包含粒子、Q、φ或真源。

三项验收均PASS：隐藏文件删除/替换不改变结果；候选重命名/置换只重排输出；没有真源映射仍能推断。另以独立 `python -I -B` 子进程实际仅读取4份候选预测NPZ和4份标量观察JSON，共8个许可数据文件；16组评分最大差0、16组置换/重命名通过，实际非法读取及阻止尝试0。专设非法读取软件测试被拦截。审计范围为Python可见open事件，不能宣称监控了所有原生系统调用。

首次独立审计在NumPy导入时遇MKL运行库代码白名单缺项，尚未读标量数据；补充代码依赖许可后通过。8文件数据许可和实验预测未变，原失败日志保留。这与下面唯一数值实现修复分开记录。

## 4. 模型定义与普通基线公平性

F：每次从对应候选原始状态重新执行正确PID/LOS/3sigma/单位规则，按原生float32叠加；成本不是缓存浓度求和。参考缓存的原生C++锚点及本次读出锚点保存。F不是部署端获得真实物理场的假设。

U_query：只有XY格的共享非负核。S_query：同一XY格内固定高度×sigma中位四类。L：共享轴对齐物理特征树，最多4叶/3节点。三个模型用完全相同的查询级总响应损失、正则化λ=0.01、训练权重、先验和物理回退。

每受体求解 `mean((Z beta-y)^2)+lambda*||beta-beta0||², beta>=0`；Z以每列RMS缩放。共同先验由4份完整参考实现等权的每粒子响应均值构成，所有零响应保留。训练损失按查询等权、每份实现贡献相同，不把粒子当独立样本。

U/S/L都只有一次共同λ，不做测试调参。每受体仅20条查询而系数很多，无正则的数据拟合系统欠定；λ>0使当前ridge目标严格凸，已求解到冻结KKT门。固定先验和正则化对解重要，不能据一次λ和一个计划就断言所有普通响应模型都不够。

S训练加权中位阈值z=0.765743732m、sigma=39.768516541cm。它是本轮公平查询版本，与RK1原S的训练方案不同，原S文件和结论未改。

L从一个状态开始，每叶4特征各25/50/75加权分位切点；只按训练总响应MSE贪心择优，平局按叶ID/特征ID/切点值。拟合并记录12+24+36=72个训练候选，最后只有一个L。不是72次留出任务选择。使用全局共享树是任务草案“每格有限划分”的受限子类，不含源ID分支。

四特征为float32 XY格内位置、z/m、sigma/cm。XY按0.25m诊断网格floor投影；这不是原生3D占据索引规则，原始3D读出/LOS保持不变。

最终树：sigma<27.225940704cm时检查格内x<0.753850937；该分支再以z<-0.109085068m切分；其余为另外两叶。规则由参考响应训练得到，**不证明这些阈值是唯一物理根因**。它是普通有限表示载体，没有CSCG/HMM、动态转移或低维传播求解。

## 5. 全查询覆盖与回退

三个压缩模型遇缺核/越界(cell,class)时，执行该输入自己的完整物理读出，逐次记录φ/LOS、粒子数和耗时。源推断只使用候选预测侧状态，不读取测试真实尾项。无静默置零、共有Q截取、困难查询删除或用真源指导区域选择。

候选参考200查询全部训练支持覆盖，三个模型物理回退均0。旧测试oracle压缩200查询中，L回退885/238448粒子，约0.371%；4份实现分别48、41、41、50块发生回退。小粒子比例不等于少数查询受影响。U和S分别回退471、985粒子，政策相同。

## 6. 源任务：小幅平均增量与明确反例

每份候选参考先将浓度转float32、严格大于0.1ppm判检出，再按M=2构成Jeffreys事件频率 `p=(hit_count+0.5)/(M+1)`。50块平均边缘Bernoulli log score，经共同温度1 softmax产生源概率。不是先平均浓度再过阈值，也不是把50相关块当独立联合似然；**归一化源图为复合评分图，尚未校准为完整物理后验**。

| 方法 | 4份等权源NLL/nat | Top1错误 |
|---|---:|---:|
| F | {nll['F']:.12f} | 0/4 |
| U_query | {nll['U_query']:.12f} | 0/4 |
| S_query | {nll['S_query']:.12f} | 0/4 |
| L | {nll['L']:.12f} | 0/4 |

| 旧任务 | F/L NLL | U_query NLL | S_query NLL | L真源概率 |
|---|---:|---:|---:|---:|
'''
for oid in ('O00','O01','O02','O03'):
    main+=f"| {oid} | {float(src[oid,'L']['source_NLL_nat']):.12f} | {float(src[oid,'U_query']['source_NLL_nat']):.12f} | {float(src[oid,'S_query']['source_NLL_nat']):.12f} | {float(src[oid,'L']['true_source_probability']):.9f} |\n"
main+=f'''
L相对S为4/4改善，相对U为3/4改善。**O03相对U恶化{o3:.12f}nat**，不能用平均掩盖。源概率约0.535–0.608，只是温和区分，不是高置信收敛。L/F全部候选参考事件相同，因此F与L在4份观察任务的源输出逐项相同；连续预测没有完全相同，不能说L超过完整物理读出。

冻结A门只要求等权源NLL优于两个正确普通基线、Top1不更差、资源符合，不预设10%收益。本轮通过该开发门。未来B建议10%门仍未测试，**不能用本轮约1%的收益替代B的实用价值门**。

## 7. 压缩诊断：不混为定位收益

| 方法 | 旧4实现等权MSE/ppm² | 训练总响应MSE/ppm² |
|---|---:|---:|
| U_query | 6.265153670 | 0.000206693 |
| S_query | 1.171923182 | 0.000143806 |
| L | 0.829440874 | 0.000011281 |

L相对S旧开发MSE约降29.22%，但源NLL仅约降1.22%。连续读出改善并不自动转成定位改善。训练与旧评价误差差距很大，显示明显的留出预测失配/泛化差距；参考自拟合、组成/时空差异和模型局限尚未被单独分离，不能用训练成绩宣称泛化。

完整每实现MSE/MAE/有符号偏差/事件错误/回退表在 `RK2_NEW/COMPRESSION_METRICS.csv`。O02阈值错误U/S/L=20/22/20；O03均9；O00/O01均1。L虽然连续MSE四任务都低于普通模型，事件错误并未全部消除。旧RK1指出的K2方向反例没有删除，本包保留Pro交接和独立复算表；本轮query级版本不覆盖或重写旧S结果。

## 8. 容量、真实计时与冷启动

| 方法 | 活动cell类状态 | 解码标量/非零 | 路由节点 | canonical字节 | 实际最小Python字节 | runtime NPZ字节 |
|---|---:|---:|---:|---:|---:|---:|
'''
for m,c in cap.items():
    main+=f"| {m} | {c['active_states']} | {c['decoder_coefficients']}/{c['decoder_nonzero_coefficients']} | {c['routing_nodes']} | {c['canonical_total_bytes']} | {c['actual_minimal_runtime_object_bytes']} | {c['actual_runtime_NPZ_file_bytes']} |\n"
main+=f'''
每状态3个int32键和10个float64核系数；L额外3节点96bytes计入总量。L相对S约少16.7%存储，但比U大。4全局叶不等于4参数，L有2328活动状态和23280解码标量。最小Python对象字节排除allocator/库开销；整体RSS单列。

共同S容量上限控制L，L额外路由从总字节扣除，最后实际模型和runtime文件都未超过S。U本来更简单/小，未给U额外复杂模块；本实验只比较预定U与S普通模型，不称对所有同容量普通模型的充分搜索或严格等自由度证明。

| 场景/200查询 | F秒 | U秒 | S秒 | L秒 |
|---|---:|---:|---:|---:|
| 候选参考实际读出 | 1.636738 | 0.540585 | 1.070356 | 0.942500 |
| 旧测试oracle压缩读出 | 2.367102 | 0.558088 | 1.065974 | 0.961735 |

F逐次重新执行原生数学，参考229060粒子检查/11237 LOS，测试238448/17596；L参考0φ/LOS，测试回退885检查/132 LOS。输入解析共同成本参考0.120621s、测试0.119966s，不能隐去。1600行逐查询成本保存，独立验证复算汇总但未重新计时。

这些是**本机单线程、Python物理数学与Python路由解码之间的局部计时**；参考L读出比F少42.4%、约1.74倍，非C++/ROS闭环加速。F本来也只有约8.18ms/query，尚未证明必须用复杂压缩。U仍最快。完整3D候选气体生成、保存、传输并未减少，L读取候选粒子进行编码，不是闭合的低维物理传播。

一次拟合+72项树搜索含设置耗时{train:.3f}s，其中S拟合后L增量约{incremental_l:.3f}s。使用旧参考φ缓存；该缓存历史建设{cold:.3f}s必须算冷启动成本，不能称缓存免费。示意若只按参考F-L平均每查询差，摊回全拟合约{cost_note['illustrative_all_fit_break_even_queries']:.0f}查询，加历史缓存约{cost_note['illustrative_all_fit_plus_historical_cache_break_even_queries']:.0f}查询；增量L相对S约{cost_note['illustrative_incremental_L_vs_S_break_even_queries']:.0f}查询。仅为算术估计，不含传播/换受体/数据传输等，非实际部署回本证明。本轮只构造固定计划参考forecast一次，后续infer都读取同形标量预测数组，不是每次源推断反复节省F-L读出；回本估计仅在新候选状态需反复读出且仍共享这10受体时成立。

## 9. 一次数值故障及允许的隔离修复

首次在U拟合第二受体时，SciPy宣布相对目标收敛，但独立KKT为3.37576e-6>3.02894e-6，冻结验收失败。2.183s即停止，没有产生U模型、L或测试源评分。原合同、源码、日志全部保留在 `FIRST_NUMERICAL_ATTEMPT_FROZEN/`，不把该早停说成科学负结果。

按任务允许只修一次隔离实现：原相同凸目标和KKT门下增加最多32步确定性20维dual Newton polish；未改λ、特征、输入、容量、划分择优、评分或阈值。30个最终受体解及全部划分拟合达到相同KKT要求，原SciPy状态如实保存，部分迭代上限不能直接当最优。

首次+修复运行墙钟合计{contract['first_attempt_wall_s']+ledger['wall_s']:.3f}s<600s，修复峰值RSS{ledger['peak_RSS_bytes']/2**20:.2f}MiB<1GiB；修复原始输出约3.56MB。QA/报告/打包为只读轻量审查进程，独立记录时间和RSS；未借它们拟合第二套方法或逃避实验预算。

## 10. 独立核验与可复算性

完整独立验证器不导入producer/model/infer，不优化、不调用φ/LOS：核对7源码SHA、642父输入、18准备输入、12预测冻结SHA；从196缓存重建3套X逐元素完全相同，先验最大差2.3037e-15；30最终KKT、72划分日志、200候选预测、16源结果、600压缩行和1600成本行一致。只重算已保存划分选择，没有重新优化72候选。原生数学真实性依赖父包锚点与本次预拟合锚点，不把无φ核验说成新物理实验。

本包只附新增数据和Pro本次交接，以旧RK1根manifest SHA `{contract['parent_root_manifest_SHA256']}` 引用旧原始库，旧ZIP SHA见 `PARENT_REFERENCE.json`。只解压新包可复算最终矩阵/KKT、源评分、压缩、资源账目；要重新检查642外部输入、196缓存血统和旧原生锚点，应同时提供旧RK1包。包内有明确范围不同的两个验证入口。

## 11. 下一步只设计，不自动运行

几何规则已选3个新源与10新受体，排除旧C7/K2所在二维格，只依几何合法性、固定哈希、最远点覆盖，未查看气体/φ。未来12份为3源×(2参考+2留出)，是同几何静态风派生测试任务，不是作者原样场景或跨湖岸泛化。源高-0.5m、受体-0.2m、强度/气体/扩散不变，未来生成前仍验运行环境、释放支持与真实物理时钟。

方案提出900s生成、3GiB磁盘、600s单方法分析预算，以及至少10%源NLL增益、Top1不更差、最差恶化≤0.2nat门。都只是待批方案。本轮生成数0，申请条件通过不等于授权。完整 `B_DESIGN_ONLY/` 保留静态候选表、选择代码和12seed提案。

## 12. 请Pro集中判断的三个问题

1. 约1%的复合源NLL增量、Top1饱和、O03反例及训练/评价偏移，是否仍足以值得运行这一项预冻结三源否证？还是普通query模型已足够、本轮压缩增量价值偏低？
2. 仅固定10受体的局部读出省时，考虑72训练划分和原生F已较快后，最合理的方法价值门应是什么？不要把当前树直接当原创算法。
3. 若批准B，是否接受已提交的几何盲选择、12份、10%/0.2nat与资源门？如修改，必须在新气体出现前一次性确定；不要回旧材料继续挑L或调λ。

科学假设有已继承支持；当前有限构造有小幅开发任务收益；独立新任务泛化与正式主创新仍未成立。冻结结果并提交审核，至此停止。
'''
write('RK2_FINITE_PROTOTYPE_REPORT_zh.md',main)
summary=f'''给Pro：已按你RK2任务书完成一次A旧材料原型，没有新GADEN/CFD/ROS/导航，也未执行B。

核心结果：共享四叶响应树L通过冻结A开发门。相同查询损失和合法预测侧回退下，4份旧开发源任务平均NLL：U_query={nll['U_query']:.12f}、S_query={nll['S_query']:.12f}、L/F={nll['L']:.12f}nat。L只改善约1.10%/1.22%，四方法Top1都是4/4；O03的L比U退化{o3:.12f}nat。L和F参考检出事件及源评分相同，连续预测不同，不能说超过完整物理。

压缩oracle MSE：U6.26515、S1.17192、L0.82944ppm²；约29.2%的MSE改善只转成约1%的源NLL收益。L2328状态/23280核系数，214272canonical bytes，小于S257172，但大于U72588。200参考局部Python读出F1.6367s、L0.9425s；完整传播未减少，训练搜索72.704s，历史φ缓存40.273s，冷启动价值必须讨论。

信息边界已实际验收：独立进程只读4份候选预测+4份标量观察；无测试粒子/Q/φ/真源映射，16评分完全复现、重命名置换通过。另独立重建196缓存→三套X/先验，核对642父输入和30KKT、72候选划分、16任务、600压缩行/1600成本行。首次数值KKT早停在测试前，用任务允许的一次同目标求解修复，原失败全部保留，合计86.17s、峰值140.50MiB。

请不要再确认RK1同类型机制；请直接判这三个问题：(1)小幅源增量和反例是否值得单项B否证；(2)局部读出收益是否足以抵偿离线搜索与完整参考物理库，方法应怎样定位；(3)是否接受已冻结几何盲三源、12份实现、至少10%源NLL收益/最坏≤0.2nat的待批B方案。B目前只是静态设计，0份生成，不会因A通过自动启动。

先读本包RK2_FINITE_PROTOTYPE_REPORT_zh.md与两份独立审核。只读新包可核验分数/矩阵和成本；原始642外部输入重验需要之前RK1包，SHA见PARENT_REFERENCE.json。所有旧判决和原始哈希不覆盖。这是有限读出原型，不是主创新确认、低维动态模型、PMFS闭环提升或时变风/湖岸证据。
'''
write('SEND_TO_PRO_zh.txt',summary)
decision=dict(status=result['status'], independent_review='PASS',information_boundary='PASS_ISOLATED_SOURCE_BLIND_INFER',
    development_effect='SMALL_POSITIVE_MEAN_NLL_WITH_O03_COUNTEREXAMPLE',mean_NLL_gain_fraction=gain,
    Top1_gain=0,L_minus_U_O03_NLL_nat=o3, L_equals_F_reference_events_and_source_scores=True,
    main_innovation='NOT_ESTABLISHED',new_independent_physics=0,B_execution='NOT_AUTHORIZED_NOT_STARTED',
    all_prior_decisions_and_evidence='FROZEN_UNCHANGED',stop='COMPLETED_A_AND_DESIGN_ONLY_WAIT_REVIEW')
write('FINAL_DECISION.json',json.dumps(decision,ensure_ascii=False,indent=2)+'\n')

# Standard diagnostic plots, all values from frozen tables. No scientific inference from plot style.
colors={'F':'#222222','U_query':'#8e8e8e','S_query':'#3b78a3','L':'#b55d32'}
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(2,2,figsize=(10.4,7.3),layout='constrained')
x=np.arange(4)
for i,m in enumerate(('F','U_query','S_query','L')):
    axs[0,0].bar(x+(i-1.5)*.18,[float(src[o,m]['source_NLL_nat']) for o in ('O00','O01','O02','O03')],width=.18,color=colors[m],label=m)
axs[0,0].set(xticks=x,xticklabels=['O00','O01','O02','O03'],ylabel='Source NLL (nat)',title='A. Old development tasks; lower is better')
axs[0,0].set_ylim(0,.72);axs[0,0].legend(ncols=2,fontsize=8)
axs[0,0].annotate('L worse than U on O03',xy=(3.25,.63),xytext=(1.5,.70),arrowprops={'arrowstyle':'->'},fontsize=8)
for m in ('U_query','S_query','L'):
    vals=[float(next(r for r in comp if r['observation_id']==o and r['method']==m)['MSE_ppm2']) for o in ('O00','O01','O02','O03')]
    axs[0,1].plot(x,vals,'o-',color=colors[m],label=m)
axs[0,1].set(xticks=x,xticklabels=['O00','O01','O02','O03'],yscale='log',ylabel='MSE (ppm squared)',title='B. Oracle encoding, not localization gain')
axs[0,1].legend(fontsize=8)
ms=('F','U_query','S_query','L')
axs[1,0].bar(ms,[float(ct['candidate_reference',m]['total_readout_wall_s']) for m in ms],color=[colors[m] for m in ms])
axs[1,0].set(ylabel='Seconds / 200 reference queries',title='C. Local Python readout only; propagation excluded')
ms2=('U_query','S_query','L')
axs[1,1].bar(ms2,[cap[m]['canonical_total_bytes']/1024 for m in ms2],color=[colors[m] for m in ms2])
axs[1,1].set(ylabel='Canonical keys + decoder + routing (KiB)',title='D. Routing charged; L larger than U')
fig.suptitle('RK2-A finite-response prototype: small task gain, bounded scope',fontsize=12)
fig.savefig(OUT/'RK2_DIAGNOSTIC_SUMMARY.png',dpi=180)
fig.savefig(OUT/'RK2_DIAGNOSTIC_SUMMARY.pdf')
plt.close(fig)
write('REPORT_BUILD_LEDGER.json',json.dumps(dict(status='PASS_POST_RUN_REPORTING_ONLY',wall_s=time.perf_counter()-started,model_fits=0,phi_LOS_calls=0,new_physics=0,source='frozen RK2 output tables'),indent=2)+'\n')
print(json.dumps(dict(output=str(OUT),gain=gain,cost=cost_note),indent=2))
