from common_n import *
import csv,numpy as np,math,shutil
def rows(n):return list(csv.DictReader((CORE/n).open(encoding='utf-8',newline='')))
def write(n,s):(CORE/n).write_text(s.strip()+'\n',encoding='utf-8')
def table(rs,cols):
 return '| '+' | '.join(cols)+' |\n| '+' | '.join(['---']*len(cols))+' |\n'+'\n'.join('| '+' | '.join(str(r.get(k,'')) for k in cols)+' |' for r in rs)
fresh=rows('FRESH_CONFIRMATION_RESULTS.csv');met=rows('FRESH_RECEPTOR_PREDICTION_METRICS.csv');nf=rows('QUALIFIED_FRESH_N0_COMPLETE_MAP_RESULTS.csv');pn=rows('QUALIFIED_N0_COMPLETE_MAP_RESULTS.csv');point=rows('QUALIFIED_N_POINT_DIAGNOSTIC_RESULTS.csv')
summary=[]
for m in ['O0','O1','N_POINT']:
 rs=[r for r in fresh if r['method']==m];bs=[r for r in met if r['method']==m]
 summary.append(dict(method=m,unique_correct=f"{sum(r['unique_top1_correct']=='True' for r in rs)}/6",ties=sum(int(r['tied_max_count'])>1 for r in rs),mean_Brier=round(np.mean([float(r['Brier']) for r in bs]),6) if bs else '无可比事件预测',mean_true_margin=round(np.mean([float(r['true_minus_bestwrong']) for r in rs]),6)))
paired=[]
for oid in sorted({r['oid'] for r in fresh}):
 a=next(r for r in met if r['oid']==oid and r['method']=='O0');b=next(r for r in met if r['oid']==oid and r['method']=='O1');ma=next(r for r in fresh if r['oid']==oid and r['method']=='O0');mb=next(r for r in fresh if r['oid']==oid and r['method']=='O1');last=next(r for r in nf if r['oid']==oid and r['update']=='2')
 paired.append(dict(oid=oid,source=ma['true_candidate'],O0_selected=ma['selected'],O1_selected=mb['selected'],Brier_O0=round(float(a['Brier']),6),Brier_O1=round(float(b['Brier']),6),delta_Brier_O1_minus_O0=round(float(b['Brier'])-float(a['Brier']),6),N0_Top5_error_m=round(float(last['native_Top5_error_m']),4),N0_variance=round(float(last['variance']),4)))
dump(CORE/'FRESH_WHOLE_REALIZATION_SUMMARY.json',dict(method_summary=summary,paired_realizations=paired,not_formal_full_map_method_gain=True))
factor=next(r for r in rows('CONTROLLED_FACTORIAL_CONTRASTS.csv') if r['oid']=='B4' and r['wrong_candidate']=='K2' and r['group']=='R01' and r['method']=='O1')
write('MECHANISM_CLOSURE_REPORT_zh.md',f'''# 原生 PMFS 机制闭合 R1：完整科学报告

本轮从提交 `a5d93c9433f6a70ddbfba87329073fcf959018ea` 接续。原历史 E3 成功、B4 错误收敛、RK2-A PASS、RK2-B FAIL 和其他 STOP/HOLD 全部保留。没有新导航 goal、CFD、神经网络训练或 L 调参。

## 结论先行

本轮不再只有一个错误收敛现象：**在锁定 B4 数据和同一三维物理引擎下，活动域限制与垂向运动省略均具有改变源判别证据的干预支持；在完全相同粒子状态上，中心占据代理与真实传感器读出也产生可复算的方向反转。** 这是失效组成因素的证据，尚不是原生 PMFS 唯一根因或已验证的新定位方法。

原生二维精确点源对照仍在两组已保存随机初态中选择错误候选 K2：真源相对最佳错误源的对数评分差分别为 −8.99849、−8.61011。于是粗叶面积差不能单独解释错误。完整三维过程加真实读出，在两参考平均、五点候选的条件比较中恢复真源优势，但单参考、同二值观测的等价候选以及完整447格未检验的边界必须同时保留。

## 1. 到底运行了什么

1. 复算历史 E3/B4 共295个候选、后验及一个前向锚点/案例；候选图、释放点、RNG与缓存相位均一致。另对 B4 首次冷初始化候选进行独立锚定，连初始化顺序也逐项一致。
2. 对12个既有公开观测任务执行真正原生概率核心的固定50块回放，每个在20/35/50块后更新，全447格、原生自适应树；另对6份新物理 realization 执行相同原生回放。共18条历史、54次更新。它们不是新的官方 ROS Action 或 Nav2 定位成绩。
3. 在同一现有物理银行上做40组查询；新增30份条件物理银行查询60组。每组完整50×448查询值保留，共2,240,000个原生查询。447个网格是推断地图采样点，不是447次独立传感器观测。
4. 生成2份全关闭干预锚点、30份三条件干预银行、6份未改物理的新观测银行，总38次；D1V1复用既有银行。未追加第3随机状态、源、环境或反馈挑种子。
5. 统一精确点源候选面积，使用原生 Point 模式和相同预算/已记录状态；合格点源共10图。评分函数始终原生，未使用温度、评分下限或删区域修复。

## 2. 原生模型与物理观测的连接位置

原生 `simulateSourceInPosition`（附源码291行起）在二维导航自由支持中移动无高度、无年龄尺度的粒子中心；每步注入5个粒子，记录网格是否含中心。`blurHitMap`（510行起）施加固定高斯模糊及自由空间边界校正。`sourceProbFromMaps`（236行起）再用全推断测量图作相似性乘积：

`score(s)=∏[1−D·confidence(g)·|p_measured(g)−q_s(g)|]`，D=0.4。

对数比较本轮全部数值采用该公式，称“相似性评分”而非经校准的物理似然。原生 `EstimateHitProbabilities`（19行起）会把一次检出空间传播为多格概率，并累积 confidence；这解释为何逐格乘积可能放大空间传播后的差异，但本轮没有将此因素单独消除并证明其因果份额。

GADEN 的实际 PID 样本则由三维丝团位置、年龄相关 sigma、3sigma截断、LOS和文件头摩尔常数求浓度，再按0.1 ppm阈值检出。本案例PID比例修正关闭，响应为瞬时浓度，无MOX记忆。中心不在接收格仍可产生检出：12个预定原始快照查询已逐丝团复算，最大ppm误差0。高度/尺度、LOS与单位都在包中可审计。

## 3. 同状态读出干预：中心占据不等价于传感器响应

O0=中心投影占据代理；O1=真实原生 PID 读出；两者采用同一原生高斯模糊和完全同一测量图、支持、评分。A1=真实事件再经原生测量地图传播，是检查表示一致性的普通对照，不是新算法。

B4真源C7相对K2：O0为 −0.508908，O1为 +3.303355。相对全部五点中的最佳错误源，O1优势仅 +0.233567，不能把两候选间的大差当五源定位收益。原12公开任务加B4的探索性比较，O0唯一正确12/13，O1 13/13；A1是12/13加B4真源与B000精确平分。

必须保留的反例：单参考0的O1仍选择B000，真源相对最佳错误源 −0.358731；单参考1为 +0.81369。同一B4冻结事件下，C7与B000全为正检出，经相同地图算子后完全相同。因此“这批二值观测能唯一识别真源”没有通过。O1平均条件评分正确不能替代独立观测可辨识性证明。

## 4. 同引擎D×V干预：两个组成因素均有支持

D0=原生三维物理支持再加二维导航支持；D1=仅真实三维支持。V0=在保留所有原随机消耗后取消全部垂向位移，中心保持源高；V1=原生三维运动。V0不只关闭浮力；D0不是重新求解CFD的另一物理环境。原壁面处理保留。

每源两组旧随机初态；D1V1复用原银行。全关闭锚点2/2通过全部1803帧、时间、缓存及状态终点一致性。不同路径后粒子数量会不同，没有稳定粒子ID，因此共享初态不等于逐粒子相同随机噪声。

B4固定C7/K2、O1、两参考平均的真源−错误源对数差：

| 条件 | 分数差 |
| --- | ---: |
| D0V0 | {float(factor['m00']):.9f} |
| D0V1 | {float(factor['m01']):.9f} |
| D1V0 | {float(factor['m10']):.9f} |
| D1V1 | {float(factor['m11']):.9f} |

开放真实域在V0/V1条件下分别增加4.83370/4.49003；恢复垂向运动在D0/D1条件下增加5.29696/4.95329。两个旧参考的方向均为正。交互 −0.343667，为轻度负交互，**不能称为强正协同**。C7的接收事件Brier依次0.80、0.19、0.60、0，是真实读出端点的互证，而非后验评分唯一证据。

五候选平均条件分别选择K2、B000、K2、C7。这个组合是本案例、此候选库的充分恢复，不是两个因素对所有源都必要，也不是纯二维/三维模型的完美公平比较。原生2D注入50/s与GADEN7/s、sigma和模糊等仍不同；因果组成因素在同引擎中隔离，但尚未逐项证明其等同于原生模型每一个误差来源。

## 5. 新6份 realization：锁定后确认，不能省略负结果

O1选择、5点参考银行、全部接收位置/时间、随机初态和Brier端点均在新气体输出前冻结。使用未改的原三维引擎，B000/B001/B002各2份新随机 realization。同一环境与源；不是新源、跨环境或真实传感器外部验证。每个50块来自10停留点，统计单位为整份 realization；不把块、相邻帧或地图格当独立样本。

{table(summary,['method','unique_correct','ties','mean_Brier','mean_true_margin'])}

{table(paired,['oid','source','O0_selected','O1_selected','Brier_O0','Brier_O1','delta_Brier_O1_minus_O0','N0_Top5_error_m','N0_variance'])}

O0/O1候选库比较与完整447格N0必须分别解读。N_POINT是诊断参考；没有把改良O1放进完整447格原生候选生成与导航，因此没有可宣称的完整方法增益。即使两者都能分对新6份，读出Brier改善仍是组成因素的确认，却不构成新增定位分类收益。连续ppm MAE/RMSE仅O1有物理单位，不能给O0占据值伪造ppm。

## 6. 原生基线完整性与本轮技术修正

历史核心锚点原始评分差0、候选图/点/RNG一致，后验独立最大误差约2.78e−17。B4原50块测量地图与新读出回放的logOdds、omega、confidence均完全一致。

本轮发现薄包装器最初混用了“缓存已加载”与“历史首次未初始化相位0”。这些旧12条输出及旧R0点图全部保留并标记为排除的技术影子分支，未作为主科学结果。修复只改变状态恢复：让原生lazy Gaussian在原顺序初始化；B4首候选图、点、缓存、初始化相位19、评分、Uniform终态全匹配。主N0必须读取 `QUALIFIED_N0_*`、`QUALIFIED_FRESH_N0_*` 和RAW/native；合格点源读取 `QUALIFIED_N_POINT_*`。未改算法或择种子。

另有开始前的C++相对include、查询列序列化、HGFS不支持symlink、协调器错误提示字符串替换语法、存储检查重复计数等技术问题，全部留档并在依赖分支启动前修复，没有新增物理随机 realization 来补好结果。批准转存的另任务3个未运行二进制哈希不变、原路径保留链接；只合并本轮银行重复CFD副本，气体帧完整保留。

## 7. 哪些疑点已缩小，哪些仍开放

- **源支持**：5个真实源3D合法、二维支持合法；447评分格中446在传感器高度自由，1个伪接收格仍保留原支持。单格评分比最大可能对数差0.510826，不能独自解释点源约−8.8的差。
- **候选面积**：精确点源同预算、两已存状态仍偏向K2，故不是唯一根因；全图自适应树放大及随机有限预算仍未隔离。
- **时变风历史**：全部定位观测使用CFD10静态场；11个输入场存在不代表观测阶段时变，本轮不支持传播历史失配归因。
- **风高度**：−0.5释放高与−0.2查询高的三维风截面不同，包内有数值；未另跑替代风前向，只能作为代码/物理状态差异，不能称为已分离因果机制。
- **相关证据**：逐块地图与固定最终库贡献全保存；不删y带、不增似然温度，不以条件敏感性冒充方法收益。相关放大仍是待分離因素。
- **有限参考**：同平均成功、单参考失败并存；4参考和两个额外参考的全部结果保留，无删反例。未对两参考做显著性检验或推断总体发生率。

## 8. 科学层级判决及交给PRO的最少问题

`CODE_FACT_PASS / NATIVE_ANCHOR_PASS / CONTROLLED_CONSTITUENT_SUPPORT / FRESH_REALIZATION_RESULTS_RECORDED / FULL_MAP_TREATMENT_GAIN_NOT_TESTED`。

本轮结论不是“根因未知所以全部HOLD”，也不是“已经完成创新”：活动域、垂向状态和传感器读出之间的表示不一致已有组成因素证据，唯一根因、跨环境稳定性与部署增益尚未证明。

请PRO重点判断：

1. 这些同引擎干预、实际读出及新6份反例，是否足以把研究对象定为“与接收器响应一致的候选输运证据”，而不继续修改L？
2. 哪个最小同观测、同支持、同预算的**完整原生候选**比较能区分普通正确3D参考已经足够与需要新的可压缩响应状态？现在没有计算复杂度/跨场景证据支持母理论必要性。
3. 如何把二值观测不可辨识和空间地图证据依赖分别纳入可否证边界，而不声称五点库胜出就是完整定位改进？

当前不激活PFCG、跨模拟学习映射、世界模型或新网络；普通正确物理读出是必需对照。保持开题冻结。本轮完成后停止，待独立审核。

## 9. 审核包覆盖

CORE提供原始合同、逐行源码、数值表、所有反例、状态修复、资源与哈希；RAW提供18条完整后验/候选预测、100组全部查询数值、38份新银行完整时间/hash/参数/状态表及每银行3份原始快照、12份原始受体快照。完整原始1803帧/银行保存在共享D盘，包中不假称携带全部原始气体。原生所有候选释放点外部完整保留；轻包仅每更新首候选点及冷初始化/点源锚点。

运行 `python CORE/source/portable/verify_native_mechanism_bundle.py 解压根目录`，需要NumPy，不需要VM/ROS或执行未知二进制。核验脚本只读，容差比较与原始SHA分开，原CSV换行/末位差异不改冻档。
''')
write('00_READ_FIRST_FOR_PRO_zh.md',f'''# 直接交给PRO的说明

请以本轮 `MECHANISM_CLOSURE_REPORT_zh.md` 与 `QUALIFIED_*` 原生结果为准。已完成原生锚点、同引擎D×V干预、同状态读出干预、统一点源反例，以及6份预冻结新物理 realization。请勿把旧影子初始化分支当主结果。

最强证据：B4相同候选库/评分，真实域与垂向状态各有正向干预效应；真实传感器读出将C7−K2分数差从−0.509转为+3.303。最重要反例：单参考0真实读出仍偏B000；A1下C7/B000精确平分；统一点源二维两次仍偏K2；组合交互是−0.344，非强正协同。五点比较正确不能证明447格或新导航方法有效。

新6份结果：

{table(summary,['method','unique_correct','ties','mean_Brier','mean_true_margin'])}

请求你一次审查：这些证据足以支持哪一级失效机制；普通正确物理读出基线之外，是否真有新方法需求；下一次最小完整原生干预应如何可否证地注册。请优先利用包中反例和全部样本，不再要求重复同类型机制审计。完整原始银行在本地有哈希索引，轻包覆盖范围明确，不把未携带原始字节写成已独立重验。
''')
mechanisms=[('01_DOMAIN','活动域与物理可达性','CONDITIONAL_FACTOR_SUPPORTED','D0/D1同引擎干预；固定V0/V1、源、观测、读出和评分','B4 O1 C7−K2提高4.83370/4.49003；两参考方向一致','D0是人为附加导航限制而非新CFD环境，不能当真实风场扰动；原生与参考其他差异未全部匹配'),('02_VERTICAL','垂向状态与接收器高度','CONDITIONAL_FACTOR_SUPPORTED','V0取消所有垂向位移并保留原随机消耗；V1原生三维','B4 O1提高5.29696/4.95329；真实源事件Brier由.80/.60降至.19/0','浮力、垂向风和噪声共同取消；没有单独证明浮力是根因。共享初态不是逐粒子配对噪声'),('03_READOUT','物理状态到传感器预测的映射','SAME_STATE_READOUT_SUPPORT','同一丝团快照；O0中心占据与O1真实PID；同原生blur/score','B4 C7−K2从−.508908到+3.303355；12原始查询逐丝团复算误差0','单参考0仍错；事件A1 C7/B000平分；五候选平均结果不是完整447格方法收益'),('04_AREA_RANDOM_TREE','候选区域、随机前向、自适应细分','AREA_NOT_SOLE_CAUSE_TREE_STILL_OPEN','同原生Point模式5源×2保存状态；记录全部树和释放点','精确点源仍选择K2，真源对数差−8.99849/−8.61011','树细分放大与MC噪声尚无同预算全原子库因果隔离；不能把反例当全部排除'),('05_EVIDENCE_OBSERVABILITY','观测可辨识性与空间证据聚合','BOUNDED_OPEN_FACTOR','原生逐块地图血统、固定最终候选库贡献；不改评分','B4全正10停留、C7/B000事件地图精确相同；逐格积非独立样本似然','没有资格化空间独立性或唯一观测；禁止删格/加温度获得事后改进'),('06_FRESH','新物理realization确认','FRESH_ENDPOINTS_COMPLETE','预测、接收计划、源和初态在气体输出前固定；6份原引擎','见FRESH_CONFIRMATION_RESULTS及Brier/MAE/RMSE完整表','新初态同源同环境，不是新源、外部物理验证或完整方法增益')]
for ident,title,level,intervention,result,limits in mechanisms:
 write('MECHANISM_'+ident+'_zh.md',f'''# {title}

判决：`{level}`。

对象与干预：{intervention}。

结果：{result}。

限制/反例：{limits}。

证据：原生源码 `source/native/Simulations_native_with_state_access.cpp` 236–267评分、291–459输运、510–523模糊；`PMFSLib_frozen.cpp`19–86测量传播；`source/C/`同引擎插桩，全部SHA在清单。见同名主报告章节及CONTROLLED_FACTORIAL_CONTRASTS、SAME_BANK_READOUT_CONTRASTS、QUALIFIED_N_POINT、QUALIFIED_NATIVE、FRESH系列表。每张比较都固定源、观测、支持、评分，改变的算子单独标记；不得混用原生完整后验与五点候选权重。

下一步：先由PRO判定最小可否证完整原生候选对照，本轮不自动追加实验。
''')
write('RAW_COVERAGE_AND_REPLAY_LIMITS_zh.md','''# 数据覆盖与复算边界

轻量包不包含完整38份×1803气体原始帧，包含全时间/hash索引、全参数、全随机初态、原始缓存、全部38份资格记录、32份干预状态计数和每份3个原始帧。完整气体银行保留在共享D盘，未删帧。

包内100组×22400数值查询全部提供；它们不等于包内可逐字节重验所有被查询原始快照。独立脚本实际重算12个预定受体查询；其余组的查询/读出字段与源评分可数值检查。18条主原生历史54次全部候选预测和后验提供；所有释放点本地完整，包内每更新首候选及点源/历史/冷锚点。完整外部输出有执行前/指标前freeze清单。

原生2D Gaussian缓存2500、LCG引擎状态和相位保存，但没有记录完整Gaussian查表调用总数，不以相位冒充总数；物理因子运行逐步Gaussian消耗及1000缓存相位都有记录。全物理轨迹没有稳定粒子ID，不把快照行号当粒子路径。

旧混合初始化分支完整保留在DATA/native_results，仅作为技术影子。主结果为DATA/native_cold_results。所有旧成功/失败、源码、气体及开题保持冻结。
''')
dump(CORE/'MECHANISM_LEVEL_DECISION.json',dict(code_fact='PASS',native_anchor='PASS',domain='CONDITIONAL_FACTOR_SUPPORTED',vertical='CONDITIONAL_FACTOR_SUPPORTED',readout='SAME_STATE_CONSTITUENT_SUPPORTED',candidate_area='NOT_SOLE_CAUSE',adaptive_tree='NOT_SEPARATELY_CLOSED',observability='B4_BINARY_NONUNIQUE_COUNTEREXAMPLE',fresh=summary,full_native_map_treatment='NOT_TESTED',main_innovation='NOT_YET_ESTABLISHED',training_authorized=False,stop_after_review_delivery=True))
print(json.dumps(dict(status='REPORTS_WRITTEN',fresh=summary),ensure_ascii=False))
