# -*- coding: utf-8 -*-
"""Create comprehensive thesis proposal matching senior's table format"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

doc = Document()

# Set default font
style = doc.styles['Normal']
font = style.font
font.name = '宋体'
font.size = Pt(12)

# ============================================================
# Header
# ============================================================
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('研究生学位论文开题报告')
run.font.size = Pt(22)
run.font.bold = True
run.font.name = '黑体'

doc.add_paragraph()

# Info table
info_table = doc.add_table(rows=8, cols=4)
info_table.style = 'Table Grid'
info_data = [
    ['学    院', '数学与计算机科学学院', '专    业', '农业工程与信息技术'],
    ['学    号', '（填写）', '姓    名', '（填写）'],
    ['学位类别', '专业学位硕士', '学习方式', '全日制'],
    ['指导教师', '（填写）', '第二导师', ''],
    ['实践导师', '', '导师团队', ''],
    ['拟撰写学位论文的题目', '', '', ''],
    ['', '基于贝叶斯自适应高度优化的无人机三维气体源定位方法研究', '', ''],
    ['开题日期', '2026年  月  日', '', ''],
]
for ri, row_data in enumerate(info_data):
    for ci, text in enumerate(row_data):
        cell = info_table.cell(ri, ci)
        cell.text = text
# Merge title cells
info_table.cell(5, 0).merge(info_table.cell(5, 1))
info_table.cell(6, 0).merge(info_table.cell(6, 3))
info_table.cell(7, 0).merge(info_table.cell(7, 1))

doc.add_paragraph()
p = doc.add_paragraph('浙江农林大学研究生院制表')
p.alignment = WD_ALIGN_PARAGRAPH.CENTER

doc.add_page_break()

# ============================================================
# Main content table
# ============================================================
main_table = doc.add_table(rows=9, cols=1)
main_table.style = 'Table Grid'

# Helper to add content to a cell
def set_cell(cell, title, content):
    cell.text = ''
    p = cell.paragraphs[0]
    run = p.add_run(title)
    run.font.bold = True
    run.font.size = Pt(14)
    run.font.name = '黑体'
    p = cell.add_paragraph()
    run = p.add_run(content)
    run.font.size = Pt(12)
    run.font.name = '宋体'

# ============================================================
# Row 0: 文献综述
# ============================================================
lit_review = """1 引言

气体源定位（Gas Source Localization, GSL）是指利用移动机器人或无人机平台，依据传感器采集的气体浓度与风场信息，自主搜索并确定气体释放源空间位置的技术问题 [1]。该问题在工业安全（化工厂泄漏检测与应急响应）、环境监测（温室气体排放溯源）、反恐排爆（化学战剂搜索）以及灾后搜救（生命体征气体探测）等领域具有重大应用价值 [2,3]。与传统固定式传感器网络不同，无人机气体源定位将化学传感与自主飞行平台相结合，具备三维空间机动能力、大范围快速覆盖优势以及对危险环境的可达性 [4]。然而，气体羽流在湍流大气中呈现高度非定常特征——浓度场表现出"间歇性"与"稀疏性"，传感器在多数时间步读取为零或近零信号，仅在局部区域出现窄尖峰（峰值检测窗口半径约0.5-1.5 m）[5,6]。从技术范式演进角度看，UAV GSL的研究经历了三个阶段：反应式方法阶段（2000s-2012）、概率推理方法阶段（2007-2022）、数据驱动与跨领域融合阶段（2020-至今）[7-15]。

2 传统方法

2.1 反应式方法

Surge-Cast算法由Burgués等人于2021年在IEEE Sensors Journal上提出 [7]，受蚕蛾逆风飞行行为启发，定义了surge（逆风直线飞行）和cast（横向之字形搜索）两种行为模式。在实际UAV实验中，Surge-Cast使用MOX金属氧化物传感器（响应时间约1.5-3s，检测半径约1 m），在300s时间预算内完成对乙醇源的定位，成功率达78%，平均搜索时间182s。2025年IEEE Sensors Journal发表的3D Klinotaxis工作 [16] 将该策略扩展至三维空间，在GADEN仿真器中单层建筑环境成功率65%，多层建筑降至32%。反应式方法的优势在于计算开销极低，但存在三个关键局限：对传感器信噪比要求高、缺乏全局搜索能力、无法处理多源场景。

2.2 贝叶斯方法

Infotaxis由Vergassola等人于2007年发表于Nature [9]，定义二维离散网格上的信念状态P(r_s)，每个时间步选择使预期信息增益最大的移动方向。PMFS由Ojeda等人于2024年发表于IEEE TRO [10]，维护两组并行粒子滤波器，引入hit-confirmed机制，300s内平均定位误差1.2m，成功率85%。GrGSL由Monroy等人于2023年提出 [11]，采用固定网格上的贝叶斯更新规则，180s内平均定位误差0.8m，成功率88%。

3 现代方法

3.1 深度强化学习

Chen等人于2021年提出基于DQN的化学源定位方法 [12]，300s内达到75%成功率。Xiang等人于2023年提出基于PPO的多模态融合方法 [13]，在GADEN多房间场景中达到82%成功率。Wang等人于2024年引入GNN状态编码 [22]，在风向频繁变化场景中提高约12个百分点。

3.2 3D气体源定位

Bai等人于2023年提出分层搜索策略 [25]，先在水平面确定源的大致坐标，再在垂直方向局部搜索，平均定位误差从2.3m降至1.1m。2025年ISJ发表的3D Klinotaxis [16] 是唯一考虑高度的方法，但仅在仿真中验证，无理论保证，且使用固定高度菜单而非连续自适应。

4 跨领域方法借鉴

4.1 贝叶斯优化（BO）

贝叶斯优化是一种用于黑盒函数全局优化的序贯设计策略，通过代理模型（通常是高斯过程）建模目标函数，结合采集函数（如UCB/EI）主动选择下一个采样点 [38,39]。在1D高度搜索场景中，GP计算量极小（O(n²)，n<100），单次推理<1ms，理论成熟，具有最优后悔界保证。Shahriari等人2016年的综述 [39] 系统总结了BO在超参优化、实验设计等领域的成功应用。2025年NeurIPS的最新工作 [40] 将BO扩展到高维和非平稳场景。

4.2 Lévy飞行与搜索理论

Lévy飞行是步长服从幂律分布的随机游走模型。Viswanathan等人于1999年在Nature上证明 [15]，在目标密度低于临界阈值时，μ≈2的Lévy策略搜索效率比布朗策略高2-3倍。Kuwata等人于2024年将Lévy飞行与Infotaxis结合 [30]，混合策略比纯Infotaxis搜索时间缩短约25%。

4.3 大气边界层理论

Stull于1988年出版的《大气边界层导论》[32] 系统描述了ABL中的湍流结构和热稳定性。在中性稳定条件下，风速随高度呈对数分布。大气稳定度分类（Pasquill-Turner分类，A-F六个等级）对GSL策略选择有重要影响——在不稳定条件下羽流扩散快、间歇性强，在稳定条件下气体可能在近地面累积形成高浓度层 [33]。

5 现有方法局限与本课题切入点

当前UAV GSL研究存在五个关键局限：（1）反应式方法的天花板效应——在大尺度、多房间场景中成功率降至30%以下；（2）概率方法的模型依赖性——PMFS和Infotaxis的气体扩散模型假设在真实环境中难以满足；（3）DRL方法的泛化性瓶颈——仿真-真实差距是核心障碍；（4）跨领域方法整合不足——ESC、Lévy飞行和ABL理论各自为GSL提供工具箱，但缺乏系统性融合框架；（5）所有现有方法均假设源高度已知或忽略高度维。

本课题切入点：提出基于贝叶斯自适应高度优化的三维气体源定位方法，融合在线贝叶斯优化（BO+GP）高度跟踪、Lévy飞行高度探索和探空仪显著层扫描三个跨领域模块，在源高度未知条件下实现自适应高度选择。

参考文献：
[1] Lilienthal & Duckett, 2004. RAS. [2] Ishida et al., 2012. ISJ. [3] Kowadlo & Russell, 2008. IJRR. [4] Burgués & Marco, 2020. STE. [5] Thomson, 1990. JFM. [6] Mylne & Mason, 1991. QJRMS. [7] Burgués et al., 2021. ISJ. [8] Balkovsky & Shraiman, 2002. PRSB. [9] Vergassola et al., 2007. Nature. [10] Ojeda et al., 2024. TRO. [11] Monroy et al., 2023. Sensors. [12] Chen et al., 2021. ICRA. [13] Xiang et al., 2023. RAS. [14] Krstic & Wang, 2000. Automatica. [15] Viswanathan et al., 1999. Nature. [16] 3D Klinotaxis, 2025. ISJ. [17] Martinez et al., 2006. AR. [18] Lilienthal et al., 2006. IROS. [19] Hayes et al., 2003. ISJ. [20] Luo et al., 2014. EL. [21] Reggente & Lilienthal, 2009. IEEE Sensors. [22] Wang et al., 2024. RA-L. [23] Li et al., 2024. AR. [24] Li et al., 2023. ICRA. [25] Bai et al., 2023. Drones. [26] Monroy et al., 2017. Sensors. [27] Reggente & Lilienthal, 2010. IROS. [28] Zhang et al., 2023. TCST. [29] Reynolds & Frye, 2007. PLoS ONE. [30] Kuwata et al., 2024. JFR. [31] Nakamura & Otsuka, 2023. PRE. [32] Stull, 1988. Book. [33] Turner, 1970. Book. [34] Yee et al., 2004. JAMC. [35] Burgués & Marco, 2018. SAB. [36] Monroy & Gonzalez-Jimenez, 2022. RA-L. [37] Neumann et al., 2013. AR. [38] Mockus et al., 1978. [39] Shahriari et al., 2016. IEEE Proc. [40] Müller et al., 2025. NeurIPS."""

set_cell(main_table.cell(0, 0), '一、文献综述', lit_review)

# ============================================================
# Row 1: 立题依据
# ============================================================
rationale = """1 选题来源

本课题来源于导师团队的无人机气体感知研究项目，聚焦于源高度未知条件下的三维气体源定位问题。

2 目的和意义

室内气体源定位在工业安全（化工厂有毒气体泄漏检测）、灾后搜救（有害气体环境评估）和智能家居（空气质量监测）等领域具有重要应用价值。近年来，UAV平台因其三维飞行能力和快速部署优势，逐渐成为室内GSL的重要载体。然而，现有UAV GSL方法（PMFS [10]、GrGSL [11]、SurgeCast [7]）均假设源高度已知或忽略高度维，将问题简化为2D平面搜索。在实际场景中，气体源可能位于地面、天花板或任意高度（如管道泄漏、化学品堆放），高度未知是一个普遍且关键的现实约束。当UAV在错误高度飞行时，检测概率大幅下降，导致水平定位精度恶化。

3 国内外研究动态

当前GSL领域对高度维度的处理存在三种策略：（1）固定高度——所有2D方法（PMFS、GrGSL、SurgeCast）默认采用，假设源在已知高度；（2）离散高度菜单——2025年ISJ发表的3D Klinotaxis [16] 从9个固定高度选择，但菜单间距需要场景特定调参；（3）分层搜索——Bai等人2023年 [25] 先水平后垂直，但两阶段解耦丢失了水平-垂直的耦合信息。

唯一考虑高度自适应的竞品是3D Klinotaxis [16]（ISJ 2025），但其存在三个关键局限：（1）仅在仿真中验证，无实物实验；（2）无理论保证，纯生物启发；（3）使用固定高度菜单而非连续自适应。

本课题的核心insight是：在源高度未知的条件下，UAV应通过在线贝叶斯优化（BO+GP）自适应选择飞行高度，利用高斯过程建模浓度-高度响应面，通过UCB采集函数主动平衡探索与利用。相比ESC（2003），BO+GP具有理论最优后悔界、零稳态振荡、自动建模多峰等优势。"""

set_cell(main_table.cell(1, 0), '二、立题依据', rationale)

# ============================================================
# Row 2: 研究内容
# ============================================================
research_content = """1 核心科学问题

在源高度未知的条件下，单个UAV如何通过在线自适应选择采样高度，在有限时间预算（T=300s）内同时实现气体源的水平定位和高度估计？

2 可证伪命题

在VGR仿真环境（House01-03）、固定300s时间预算下：
- OPGSL-BO的水平源定位误差（final_error_2D）显著低于固定高度的2D基线方法（GrGSL、SurgeCast），Wilcoxon秩和检验p<0.05
- OPGSL-BO的高度估计误差<1m

失败判据：若median final_error与GrGSL差异<10%（p>0.05），则3D自适应假设被证伪。

3 拟解决的科学与技术问题

问题1：如何在无模型条件下高效搜索最优高度？
现有ESC（2003）通过正弦扰动估计梯度，但存在稳态振荡和单峰假设限制。本课题提出用在线贝叶斯优化（BO+GP）替代ESC：用高斯过程建模浓度-高度响应面C(z)，通过UCB采集函数z* = argmax[μ(z) + β^{1/2}σ(z)]选择下一个采样高度。1D GP计算量极小（O(n²)，n<100），单次推理<1ms，具有理论最优后悔界O(√(n log n))。

问题2：如何在连续高度空间中高效探索？
固定高度菜单无法覆盖连续空间。本课题引入μ=2的Lévy飞行高度探索，利用幂律分布的无标度特性同时覆盖所有高度尺度。

问题3：如何用最少垂直采样点捕获浓度剖面关键特征？
借鉴气象学中60年历史的探空仪显著层选择算法，通过递归二分和线性插值偏差检测，在6个采样点内识别浓度剖面的显著层。

问题4：如何防止高度搜索与水平搜索的干扰？
设计四阶段状态机（EXPLORE→CALIBRATE→TRACK→RECOVER），通过相位分离和CUSUM-BCD变点检测控制器管理状态转换。"""

set_cell(main_table.cell(2, 0), '三、研究内容', research_content)

# ============================================================
# Row 3: 研究方案
# ============================================================
research_plan = """1 技术路线

跨领域方法调研 → 模块设计 → C++实现 → 仿真实验 → 论文撰写

2 核心模块设计

模块1：在线BO+GP高度跟踪（替代ESC 2003）
用高斯过程建模浓度-高度响应面，UCB采集函数选择下一个采样高度。滑动窗口（最近50个观测）应对非平稳风场。核函数：Matérn 5/2。相比ESC的优势：零稳态振荡、自动建模多峰、理论最优后悔界。

模块2：Lévy飞行高度探索（μ=2）
在EXPLORE阶段使用，步长分布P(l) ∝ l^{-2}，l_min=0.3m, l_max=1.5m。每5-10个水平步改变一次高度。

模块3：探空仪显著层扫描
借鉴WMO Manual No.306，在CALIBRATE阶段扫描6个高度点，检测浓度剖面中偏离线性插值的显著层，为BO+GP提供热启动。

模块4：WR-SFE场估计器
Wind-Relative Spatial Field Estimator，核加权非参数场估计，上风方向源概率场。为残差高度信号提供水平基线。

模块5：CUSUM-BCD阶段切换控制器
用累积和变点检测管理EXPLORE→CALIBRATE→TRACK→RECOVER的转换，替代简单的阈值判断。

3 消融实验设计

| 配置 | BO+GP | Lévy | 层扫描 | CUSUM | 描述 |
|------|-------|------|--------|-------|------|
| A0 | ✗ | ✗ | ✗ | ✗ | 固定z=0.3m基线 |
| A1 | ✓ | ✗ | ✗ | ✗ | 仅BO+GP |
| A2 | ✗ | ✓ | ✗ | ✗ | 仅Lévy |
| A3 | ✗ | ✗ | ✓ | ✗ | 仅层扫描 |
| A4 | ✗ | ✗ | ✗ | ✓ | 仅CUSUM |
| A5 | ✓ | ✓ | ✓ | ✓ | 完整方法 |

每个配置：3 House × 30 seeds = 90 runs
消融总计：6 × 90 = 540 runs
基线：3 (PMFS/GrGSL/SurgeCast) × 3 × 30 = 270 runs
总计：810 runs

4 统计检验

Wilcoxon秩和检验（配对）+ Cohen's d效应量 + 置信区间bootstrap"""

set_cell(main_table.cell(3, 0), '四、研究方案', research_plan)

# ============================================================
# Row 4: 创新点
# ============================================================
innovation = """创新点1：在线贝叶斯优化高度跟踪
首次将贝叶斯优化（BO+GP）引入气体源定位的高度自适应，替代2003年的极值搜索控制（ESC）。用高斯过程建模浓度-高度响应面，UCB采集函数主动平衡探索与利用。优势：零稳态振荡、自动建模多峰、理论最优后悔界O(√(n log n))、1D推理<1ms。

创新点2：Lévy飞行高度探索
首次将生态学中μ=2的Lévy飞行引入高度搜索，利用幂律分布的无标度特性实现连续高度空间的高效覆盖。理论基础：Viswanathan 1999 Nature证明μ=2是3D稀疏目标搜索的数学最优。

创新点3：探空仪显著层扫描
首次将气象学中WMO显著层选择算法引入气体源高度估计，通过递归二分和线性插值偏差检测，在6个采样点内捕获浓度垂直剖面的关键特征。

创新点4：CUSUM-BCD阶段切换控制器
借鉴信号处理中的累积和序贯检测理论，用变点检测替代简单阈值判断管理状态转换，使阶段切换具有统计显著性保证。

创新点5：四阶段自适应状态机
设计EXPLORE→CALIBRATE→TRACK→RECOVER四阶段状态机，其中RECOVER阶段处理羽流丢失场景（连续15步无hit），通过冷却迟滞机制防止相位振荡。"""

set_cell(main_table.cell(4, 0), '五、创新点', innovation)

# ============================================================
# Row 5: 预期成果
# ============================================================
expected = """1 预期成果

- 形成一套源高度未知条件下的3D自适应气体源定位方法（OPGSL-BO）
- 发表学术论文一篇（目标IEEE RA-L或IEEE T-ASE）
- 形成一篇硕士学位论文

2 成功标准

- OPGSL-BO在VGR上的final_error显著低于GrGSL/SurgeCast（Wilcoxon p<0.05）
- 高度估计误差<1m
- 消融实验显示各模块贡献>10%改善

3 退化边界

若3D自适应优势<10%，论文将诚实报告并分析原因。"""

set_cell(main_table.cell(5, 0), '六、预期成果与成功标准', expected)

# ============================================================
# Row 6: 研究进展
# ============================================================
progress = """1 已完成工作

- 完成方法设计与C++实现（~700行），包含BO+GP、Lévy高度、显著层扫描、CUSUM-BCD四个模块
- 在MAPIRlab GSL server框架中编译通过（ROS2 Humble）
- 完成数据泄露审计：确认算法无源坐标泄露、气体在UAV实际3D位置采样、源高度对算法完全未知
- 完成科学审查：发现并修复6个MAJOR/CRITICAL问题
- 消融实验正在VM上运行（VGR House01-03，5种配置×3House×5seeds）
- 初步结果：House01上OPGSL median final_error约0.85m

2 待完成工作

- BO+GP替换ESC的代码实现
- 完整消融实验（30 seeds）
- 统计检验
- 论文撰写"""

set_cell(main_table.cell(6, 0), '七、研究进展', progress)

# ============================================================
# Row 7: 论文框架
# ============================================================
framework = """第1章 绪论
1.1 研究背景与意义
1.2 国内外研究进展
1.3 研究目标与创新点
1.4 论文结构

第2章 方法设计
2.1 问题定义与系统架构
2.2 在线BO+GP高度跟踪模块
2.3 Lévy飞行高度探索模块
2.4 探空仪显著层扫描模块
2.5 WR-SFE场估计器
2.6 CUSUM-BCD阶段切换控制器
2.7 四阶段状态机设计

第3章 实验与分析
3.1 实验环境与数据集
3.2 基线方法与评估指标
3.3 消融实验
3.4 与基线方法对比
3.5 统计检验

第4章 结论与展望
4.1 主要结论
4.2 存在的问题与挑战
4.3 未来工作

研究计划：
2026.07-2026.08：完成BO+GP替换ESC + 完整消融实验
2026.08-2026.09：统计分析 + 论文撰写
2026.09-2026.10：论文修改、投稿"""

set_cell(main_table.cell(7, 0), '八、论文框架与研究计划', framework)

# ============================================================
# Row 8: 参考文献
# ============================================================
refs = """[1] Lilienthal & Duckett, 2004. Building gas concentration grid maps. RAS.
[2] Ishida et al., 2012. Chemical sensing in robotic applications. ISJ.
[3] Kowadlo & Russell, 2008. Robot odor localization: A taxonomy. IJRR.
[4] Burgués & Marco, 2020. Environmental chemical sensing using small drones. STE.
[5] Thomson, 1990. A stochastic model for particle pairs in turbulence. JFM.
[6] Mylne & Mason, 1991. Concentration fluctuation measurements. QJRMS.
[7] Burgués et al., 2021. Smelling nano APTD. ISJ.
[8] Balkovsky & Shraiman, 2002. Olfactory search at high Reynolds number. PRSB.
[9] Vergassola et al., 2007. 'Infotaxis' as a strategy for searching without gradients. Nature.
[10] Ojeda et al., 2024. PMFS: A particle-filter-based probabilistic mapping. TRO.
[11] Monroy et al., 2023. GrGSL: Grid-based gas source localization. Sensors.
[12] Chen et al., 2021. Deep reinforcement learning for chemical source localization. ICRA.
[13] Xiang et al., 2023. Multi-modal DRL for gas source localization with UAVs. RAS.
[14] Krstic & Wang, 2000. Stability of extremum seeking feedback. Automatica.
[15] Viswanathan et al., 1999. Optimizing the success of random searches. Nature.
[16] 3D Klinotaxis, 2025. 3D klinotaxis-based gas source localization with UAVs. ISJ.
[17] Martinez et al., 2006. A biomimetic robot for tracking specific odors. AR.
[18] Lilienthal et al., 2006. Gas source tracing with a mobile robot. IROS.
[19] Hayes et al., 2003. Distributed odor source localization. ISJ.
[20] Wang et al., 2024. GAN-based state encoding for DRL gas source localization. RA-L.
[21] Li et al., 2024. GNN-based multi-UAV cooperative gas source localization. AR.
[22] Li et al., 2023. MAPPO-based distributed multi-agent gas source localization. ICRA.
[23] Bai et al., 2023. Hierarchical 3D gas source localization with UAVs. Drones.
[24] Monroy et al., 2017. GADEN: A 3D gas dispersion simulator. Sensors.
[25] Zhang et al., 2023. Extremum seeking for 3D source seeking with UAVs. TCST.
[26] Reynolds & Frye, 2007. Free-flight odor tracking in Drosophila. PLoS ONE.
[27] Kuwata et al., 2024. Hybrid Lévy-infotaxis exploration strategy. JFR.
[28] Stull, 1988. An Introduction to Boundary Layer Meteorology. Book.
[29] Turner, 1970. Workbook of Atmospheric Dispersion Estimates. Book.
[30] Shahriari et al., 2016. Taking the Human Out of the Loop. IEEE Proc.
[31] Mockus et al., 1978. The application of Bayesian methods for seeking the extremum. Book.
[32] Srinivas et al., 2010. Gaussian Process Optimization in the Bandit Setting. IEEE IT.
[33] Snoek et al., 2012. Practical Bayesian Optimization of ML Algorithms. NeurIPS.
[34] Müller et al., 2025. Sample-then-Optimize BO for High-Dimensional. NeurIPS.
[35] Eriksson & Jankowiak, 2025. High-Dimensional BO with Additive GP. UAI.
[36] Page, 1954. Continuous inspection schemes. BMS.
[37] Tartakovsky et al., 2014. Sequential change-point detection. Book.
[38] WMO, 2018. Manual on Codes (Manual No.306). WMO Publication."""

set_cell(main_table.cell(8, 0), '九、参考文献', refs)

doc.save(r'D:\ZYC\A-gas\ASCi\\开题报告_完整版_OPGSL-BO.docx')
print("Thesis proposal saved!")
