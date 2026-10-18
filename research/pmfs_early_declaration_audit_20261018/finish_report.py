from pathlib import Path
import csv,datetime,hashlib,json,re,shutil,statistics,subprocess
R=Path(__file__).resolve().parent;A=R/'analysis';OLD=R.parent/'PMFS_PAPER_FIRST_ROS_QUAL_20261017'
def read(p):return list(csv.DictReader(p.open()))
def put(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
new=[r for r in read(A/'EPISODES.csv')if r['phase']=='new'];ctrl=read(A/'FORMULA_CONTROLS_NATIVE_CPP_READOUT.csv');nativeparity=json.loads((A/'FINAL_NATIVE_READOUT_PARITY.json').read_text());par=read(A/'EXACT_NATIVE_REPLAY_PARITY.csv')
assert len(new)==4 and len(par)==7 and all(r['result']=='NATIVE_ACTION_RETURNED'for r in new)
lasts=[]
for row in new:
 u=max(int(c['update'])for c in ctrl if c['role']==row['role'])
 d1=next(c for c in ctrl if c['role']==row['role']and int(c['update'])==u and c['control']=='paper_alpha_D1')
 d02=next(c for c in ctrl if c['role']==row['role']and int(c['update'])==u and c['control']=='paper_alpha_D02')
 oldalpha=next(c for c in ctrl if c['role']==row['role']and int(c['update'])==u and c['control']=='code_alpha_D1')
 assert float(d1['variance_m2'])<1<float(d02['variance_m2']) and float(oldalpha['variance_m2'])<1
 lasts.append(dict(role=row['role'],update=u,paper_D1_variance_m2=float(d1['variance_m2']),same_maps_D02_variance_m2=float(d02['variance_m2']),same_maps_linear_alpha_D1_variance_m2=float(oldalpha['variance_m2']),native_error_m=float(row['native_top5_error_m']),same_maps_D02_error_m=float(d02['top5_error_m'])))
put(A/'DECLARATION_FACTOR_ATTRIBUTION.json',dict(status='SAME_HISTORY_DIRECT_SCORE_COEFFICIENT_EFFECT_IN_ALL_FOUR_RUNS',rows=lasts,causal_scope='One-factor algebraic intervention on the same sampled forward maps, measurement map, confidence, support, and final native tree. No different trajectory, new measurement or RNG draw is used.',not_claimed=['Not a full closed-loop run with D0.2; its refinement and later trajectory would generally differ','Does not identify the entire reason the physical source is misranked','Does not prove author paper experiments used D1 or the September public code','Does not authorize selecting D to improve the benchmark']))
report='''# PMFS提前错误声明：官方配置核对与A2/B2小规模复跑

日期：2026-10-18。裁决：`EARLY_DECLARATION_REPRODUCED_PAPER_CODE_DIVERGENCE_IDENTIFIED_PERFORMANCE_REPRODUCTION_HOLD`。

本轮完成了源坐标、二维地图、三维释放合法性、官方时钟、实际输入/参数、停止读出和两配置各两次复跑。四次均正常返回并在错误位置触发方差声明。未运行AIMMD，未生成气体世界，没有为了误差或时间调整任何在线参数。旧两次记录与全部新负结果保留。

## 1. 最重要的直接证据

当前运行的是“正式论文公式优先、未定义细节用2024-09-18 GitHub补足”的重建版，不是作者原样发布版，也不是已恢复作者实验快照。它使用论文Eq6的Omega平方、论文Eq8没有额外缩放时对应的D=1、论文停止方差1m²。

公开启动文件则给出D=0.2，公开代码Eq6使用线性Omega，公开启动文件方差门槛1.5m²。阈值1m²来自论文明确描述；本轮保持原重建政策，不按实验结果选参数。

本轮保存每次真正计算的候选响应，离线只改变评分系数，对同一历史、同一测量图、同一置信度和同一已采样细化树重算：

| 回合末次更新 | 实际D=1方差/m² | 同预测D=0.2方差/m² | 实际声明误差/m |
|---|---:|---:|---:|
'''
for x in lasts:report+=f"| {x['role']} / update{x['update']} | {x['paper_D1_variance_m2']:.6f} | {x['same_maps_D02_variance_m2']:.6f} | {x['native_error_m']:.5f} |\n"
report+='''
四个末次状态在D=1时全部低于1m²，在同预测D=0.2时全部高于1m²。仅把Eq6换回公开代码线性Omega，仍然四个状态全部触发声明。因此在这些固定状态上，额外评分系数差异直接改变是否停止，单改置信度平方不足以消除这四个末次声明。**这不代表Eq6无影响**：EA18_A2_R02的中间update2，平方公式方差1.040545m²尚不声明，线性公式为0.960984m²会声明，线性甚至可能更早；该反例同样保留。停止条件只检查概率图的空间方差，不检查真实定位误差；读到`convergence_steps=5`也不能自行添加连续五次确认，实际PMFS代码只声明该参数而未用它约束checkSourceFound。

**这解释了当前重建版为什么可能很早停下，不等于解释了全部错源原因。** D=0.2的同历史Top-5%位置依然错误，不能把概率变宽写成定位改善；其原生细化树和后续航线若真按D=0.2运行会变化，当前离线结果不是那种闭环的预测成绩。也不能把当前重建版的失误直接归于正式发表的PMFS。

逐源响应共1,120次原生候选模拟，7次源更新；没有额外反事实前向调用。重新组装原生概率图的最大绝对差低于8e-16。最终方差与Top-5%读出用提取的原生C++方法复算，共28组公式控制，不以NumPy对并列概率的排序代替原生std::sort。

## 2. 本轮真实闭环结果与论文

| 配置 | 回合1误差/墙钟搜索 | 回合2误差/墙钟搜索 | 两次平均 | 论文30次平均 |
|---|---:|---:|---:|---:|
'''
for case,papererr,papertime in [('A2',.6,87.),('B2',2.3,110.5)]:
 vals=[x for x in new if x['case']==case]
 report+=f"| {case} | {float(vals[0]['native_top5_error_m']):.3f}m / {float(vals[0]['native_search_wall_s']):.2f}s | {float(vals[1]['native_top5_error_m']):.3f}m / {float(vals[1]['native_search_wall_s']):.2f}s | {statistics.mean(float(x['native_top5_error_m'])for x in vals):.3f}m / {statistics.mean(float(x['native_search_wall_s'])for x in vals):.2f}s | 约{papererr:.1f}m / {papertime:.1f}s |\n"
report+='''
论文时间87.0/110.5为Fig11柱上印出的一位小数均值；误差来自Fig10图示读数。每配置本轮只有2次，复用同一个本机重新生成的气体世界；它们是算法运行重复，不是独立物理重复，也不是作者未公开的30次原始实验。旧记录合并后每配置3次的汇总另存，不选择性删除坏结果。

## 3. B2真源为何被排除

官方B2源为(-0.4,-2.9,-0.3)m，二维PGM原点(-7.55,-7.88)、分辨率0.01m。实际Nav2地图与官方PGM的全部像素转换逐字节相同。源点索引(715,498)，图像像素(715,641)为黑色；原生0.25m格(28,19)因此不通过“625个细像素全部自由”的规则。

同一配置重建的三维CSV按z/x/y顺序解析，源索引(71,49,7)为Free0；源在三维物理场中合法，且其下方多个高度层是障碍。二维机器人导航与三维气体释放并非同一几何支持，这两项可以同时成立。不能为了让真源可选而开障碍格或移动释放点。

最近合法粗格中心距真源仅0.248294m。因此这不是“场景无解”的证据，不能取消B2定位成绩，更不能单凭排除真源格解释4m错误。正式论文Fig12与结果讨论指出B2三维流动给二维PMFS带来困难，但论文没有将源格排除量化为本次损失原因。

## 4. 时钟逐项对齐

| 部件 | 固定官方/实际设置 | 本轮处理 |
|---|---|---|
| PMFS | use_sim_time=False，node->now计搜索和0.4s采样窗 | 保持系统墙钟，未乘除5修饰结果 |
| BasicSim | deltaTime0.1、speed5，机器人钟约5×墙钟 | 保持公开值，逐回合实测斜率 |
| PID/风传感器 | use_sim_time=True；历史循环为墙钟10/20Hz | 保留机器人时间戳和原采样率 |
| GMRF | 原核心/2Hz执行频率；拒绝缺TF读数的已披露适配 | 核对实际接受观测与TF区间，未换全场真风 |
| 播放器 | 2Hz墙钟文件节律；A2循环，B2初始500不循环 | 保留已披露新版文件适配，另存物理帧年龄 |

混合时钟来自公开启动示例，不是根据本轮结果任意设定；论文没有给出作者30次运行的完整时钟记录，不能把保留公开配置称作已证明实验时钟等价。传感器窗口0.4墙钟秒约对应2机器人秒，气体帧时间还有单独含义。单纯将搜索时间乘5不能恢复论文成绩。

A2循环边界经独立枚举与实际记录核清：历史“load当前帧→自增→>=200归100”与现代“load→自增→>199归100”都产生首次200一次、随后100..199。三条已有A2轨迹均有真实199→100回绕，逐行错帧0。现有CASE_META中inclusive100..200为描述性误述，已另记erratum，未据此修改播放器或补跑。

四次新运行的风向π转换、单点真实世界传感器查询和局地GMRF TF区间一致性全部核对；不把区间一致性夸大为恢复每个内部TF owner。世界水平真风没有作为PMFS的全场免费输入，构建USE_GADEN=False且useWindGroundTruth=False。

## 5. 本轮修复、保留与限制

- 本轮唯一新C++差异为被动候选图导出，所有科学计算公式与在线参数沿用前一轮；127个源码文件逐个核对，其他126个完全不变。被动I/O有成本且可能影响线程调度，不宣称本轮墙钟是无记录开销的性能成绩。
- 旧版已有必要适配为矩形方差遍历、地图启动与空测量保护，以及构建/追踪；完整分类在嵌入的前一轮冻结包。矩形修复不是创新。
- 离线分析初稿曾用闭区间中心距离判断真源格，A2恰在格边界会多计一格，定稿已改为原生半开网格规则。另NumPy并列排序与原生C++Top5%读数可能略不同，决定性读出全部改用原生C++；不涉及改动ROS结果。
- 作者论文实验准确提交、原始世界/种子未恢复；年龄增长覆盖函数仍无明确公式，按用户授权沿用固定GitHub中心占格事件。这些限制使“完整字面论文复现”仍不能宣称完成。

## 6. 结束裁决

已经排除了地图读反、源坐标转换错、A2循环端点错、当前空观测，以及把5倍机器人钟误当PMFS搜索钟这几项解释。确认了当前重建版在固定原生响应上的D系数差异，足以改变四个末次状态是否过早声明。尚未确认哪一项传播/估计假设导致各回合错误区域获得最高证据，也没有证明恢复作者D设置后能达到论文定位误差。

本轮停止于已冻结的4回合。AIMMD保持暂停。不得把D改回0.2后可能得到的更长时间自动写成“复现修好了”，也不得把D=1重建版当前的4m错误写成作者正式PMFS缺陷。后续任何作者发布版与论文重建版比较都应分开命名，事前冻结，而不能按成绩挑版本。

## 7. 复算与交付入口

- `analyze.py`：用已存候选f32、逐格Omega和真实观测图重建原生评分与四种公式控制；需要Python、NumPy。
- `verify_readout_guest.py`与`native_readout_check.cpp`：编译原生Top5%/均值/方差读出。可直接复用前一轮包的DDA头文件，无ROS要求。
- `final_checks.py`：校验四回合实际参数、地图、测量窗、循环与原生读出一致性。
- `independent_review/`：独立只读核验185官方文件、地图/三维网格/正式论文和循环端点。
- `cases/`：原始CDR、服务查询、导航、消费窗口、候选图、概率图、全部日志及退出状态。
- `previous_qualified_baseline.zip`：前一轮已冻结完整代码、官方配置和旧两次结果；按原SHA嵌入。大体积气体世界不重复打包，血统和逐帧清单仍由该包给出。
'''
(R/'核查结论_zh.md').write_text(report,encoding='utf-8')
put(A/'FINAL_VERDICT.json',dict(verdict='EARLY_DECLARATION_REPRODUCED_PAPER_CODE_DIVERGENCE_IDENTIFIED_PERFORMANCE_REPRODUCTION_HOLD',new_real_ROS_episodes=4,technical_failures=0,new_native_forward_calls=1120,new_source_updates=7,new_gas_worlds=0,AIMMD=0,actual_online_parameter_changes=0,small_scale_repeated_early_declarations=4,source_map_clock_audits_complete=True,exact_author_paper_reproduction_claimed=False,native_score_max_abs_replay_error=max(float(x['native_tree_posterior_max_abs_error'])for x in par),strongest_attribution='Fixed history and native sampled tree: D1 declares in4/4 terminal snapshots; D0.2 does not in4/4. Position errors remain large; no new D0.2 closed-loop benefit demonstrated.'))
put(A/'ANALYSIS_IMPLEMENTATION_NOTES.json',dict(notes=['Initial half-cell inclusive membership would double-count A2 at exact boundaryx1.75; replaced by native half-open index membership before final delivery.','Initial NumPy stable Top5 sorting differs on tied coarse cells from native float-coordinate std::sort; authoritative FORMULA_CONTROLS_NATIVE_CPP_READOUT.csv reproduces nativeC++.','Prior CASE_META retains historical receipt paths and descriptive flags; see INHERITED_METADATA_ERRATA.json, not treated as live executed identity.'],scientific_data_or_online_parameters_modified=False))
previous=Path(r'C:\Users\50176\Downloads\PMFS_完整ROS基线_A2B2实测与适配记录_20261017_复核版.zip');expected='4dea960689cdac85697144255d4c1421d981c1080345479915341f6fef8c9e1d';assert sha(previous)==expected
shutil.copyfile(previous,R/'previous_qualified_baseline.zip')
shutil.copyfile(OLD/'README.md',R/'PREVIOUS_BASELINE_README.md')
shutil.copyfile(OLD/'PATCH_CLASSIFICATION.json',R/'PREVIOUS_PATCH_CLASSIFICATION.json')
put(R/'DELIVERY_CONTENTS.json',dict(previous_qualified_archive_sha256=expected,contains_new_world_frame_bytes=False,contains_all_new_candidate_maps=True,contains_new_source_and_actual_binary=True,contains_previous_complete_baseline_archive=True,big_worlds_are_not_upload_reference_library=True))
print(json.dumps(dict(report=str(R/'核查结论_zh.md'),new_runs=len(new),maximum_replay_error=max(float(x['native_tree_posterior_max_abs_error'])for x in par))))
