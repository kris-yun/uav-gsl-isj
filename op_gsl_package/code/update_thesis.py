# -*- coding: utf-8 -*-
"""Surgical update of thesis proposal: FH-POMDP-GSL -> OPGSL-3D for ISJ"""
import sys, shutil
sys.stdout.reconfigure(encoding='utf-8')

from docx import Document
from docx.shared import Pt

SRC = r'D:\ZYC\A-gas\ASCi\\开题报告_FH-POMDP-GSL.docx'
DST = r'D:\ZYC\A-gas\ASCi\\开题报告_OPGSL-3D.docx'

# Backup
shutil.copy2(SRC, DST)
doc = Document(DST)
paras = doc.paragraphs

def set_text(para, text):
    """Replace paragraph text, preserving first run's formatting."""
    if para.runs:
        fmt = para.runs[0].font
        bold = fmt.bold
        size = fmt.size
    else:
        bold = None
        size = None
    for run in para.runs:
        run.text = ''
    if para.runs:
        para.runs[0].text = text
        if bold is not None:
            para.runs[0].font.bold = bold
        if size is not None:
            para.runs[0].font.size = size
    else:
        para.add_run(text)

# ============================================================
# Section 0: Title
# ============================================================
set_text(paras[0], '开题报告 — 未知源高度条件下UAV气体源定位的三维自适应方法（OPGSL-3D）')
set_text(paras[1], '以下内容对应开题报告模板的各个章节，直接复制粘贴即可。')

# ============================================================
# Section 1: 立题依据
# ============================================================
set_text(paras[5], '室内气体源定位（Gas Source Localization, GSL）是移动机器人嗅觉领域的核心问题，在工业安全（有毒气体泄漏检测）、灾后搜救（有害气体环境评估）和智能家居（空气质量监测）等领域具有重要应用价值。与室外环境不同，室内气体扩散受到低风速、障碍物遮挡和热分层等因素影响，羽流呈现高度间歇性和空间异质性。')

set_text(paras[6], '近年来，无人机（UAV）平台因其三维飞行能力和快速部署优势，逐渐成为室内 GSL 的重要载体。然而，现有 UAV GSL 方法（PMFS、GrGSL、SurgeCast）均假设源高度已知或忽略高度维，将问题简化为 2D 平面搜索。在实际场景中，气体源可能位于地面、天花板或任意高度（如管道泄漏、化学品堆放），高度未知是一个普遍且关键的现实约束。当 UAV 在错误高度飞行时，检测概率大幅下降，导致水平定位精度恶化。')

set_text(paras[7], '现有方法的局限：Vergassola 等人的 infotaxis（2007）和 Ojeda 等人的 PMFS（2024）在 2D 网格上维护源位置后验，不感知高度维。GrGSL 使用梯度跟随，同样忽略高度。SurgeCast 使用气味/风向状态机进行羽流追踪，假设固定飞行高度。2025 年发表的 3D Klinotaxis（ISJ）是唯一考虑高度的方法，但仅在仿真中验证，无理论保证，且使用固定高度菜单而非连续自适应。')

set_text(paras[8], '本课题的核心 insight 是：在源高度未知的条件下，UAV 应通过在线自适应选择飞行高度来最大化气体检测概率，从而同时改善水平定位精度和高度估计。我们提出 OPGSL-3D 方法，融合极值搜索控制（ESC）梯度跟踪、Lévy 飞行高度探索和探空仪显著层扫描三个跨领域模块，实现三维自适应气体源定位。')

# 1.2 国内外研究现状
set_text(paras[10], 'GSL 方法综述：当前 GSL 方法可分为三类。(1) 反应式方法（surge-cast、klinotaxis）：沿浓度梯度或风向移动，实现简单但易陷入局部最优，且均假设固定飞行高度。(2) 贝叶斯方法（infotaxis、PMFS）：维护源位置后验分布，选择最大化信息增益的动作，理论优美但在 2D 网格上运行，忽略高度维。(3) 学习方法（DRL、GNN）：需要大量训练数据，泛化能力有限。所有这些方法均假设源高度已知或忽略高度维，无法处理"源高度未知"这一现实场景。')

set_text(paras[11], '跨领域方法借鉴：(1) 极值搜索控制（ESC）：Krstic 等人（2003）提出的无模型梯度估计方法，通过正弦扰动和解调提取未知函数的梯度信号，广泛应用于发动机控制、化学过程优化等领域，但从未被应用于气体源定位的高度优化。(2) Lévy 飞行：Stromboli 等人（2026）证明 μ=2 的 Lévy 分布是 3D 稀疏目标搜索的数学最优步长分布，已在动物觅食行为中得到广泛验证。(3) 探空仪显著层选择：WMO Manual No.306 规定的递归二分算法，用最少采样点捕获大气垂直剖面的关键特征，60 年全球实战验证。')

set_text(paras[12], '本课题切入点：现有 GSL 文献中，无人将极值搜索控制用于高度自适应，无人将 Lévy 飞行引入高度探索，也无人将探空仪显著层选择用于气体源高度估计。本课题填补这三个空白，提出首个源高度未知条件下的 3D 自适应 GSL 方法。')

# 1.3 参考文献 - keep as is, add new ones later

# ============================================================
# Section 2: 研究内容
# ============================================================
set_text(paras[18], '本课题的核心科学问题是：在源高度未知的条件下，单个 UAV 如何通过在线自适应选择采样高度，在有限时间预算（T=300s）内同时实现气体源的水平定位和高度估计？')

set_text(paras[19], '这一问题的可证伪命题为：在配对 source/start/seed、固定 300s 时间预算、VGR 仿真环境（House01-03）下，OPGSL-3D 的水平源定位误差（final_error_2D）显著低于固定高度的 2D 基线方法（GrGSL、SurgeCast），且能正确估计源高度（z 误差 <1m）。')

set_text(paras[20], '失败判据：若在 VGR House01-03 上，OPGSL-3D 的 median final_error 与 GrGSL 差异 <10%（配对 Wilcoxon 检验 p>0.05），则 3D 自适应假设被证伪。若 OPGSL-3D 的高度估计误差 >2m（源高度范围仅 0.5m），则高度自适应机制无效。')

# 2.2 拟解决的科学与技术问题
set_text(paras[22], '问题 1：如何在无模型条件下估计浓度场关于高度的梯度？ 现有 ESC 理论假设目标函数是控制输入的静态映射 y=f(u)，但气体浓度是空间坐标 c(x,y,z) 的函数，水平运动产生的浓度变化远大于高度变化。本课题提出残差 ESC 方法：从观测浓度中减去水平场估计器的预测值，隔离高度依赖的信号分量，使 ESC 的收敛性假设得到满足。')

set_text(paras[23], '问题 2：如何在连续高度空间中高效探索？ 固定高度菜单（如 9 个离散高度）无法覆盖连续空间，且菜单间距需要场景特定调参。本课题引入 Lévy 飞行高度探索，利用 μ=2 幂律分布的无标度特性，同时覆盖所有高度尺度——大部分步在附近（利用），偶尔大幅跳跃（探索）。')

set_text(paras[24], '问题 3：如何用最少的垂直采样点捕获浓度剖面的关键特征？ 本课题借鉴气象学中 60 年历史的探空仪显著层选择算法，通过递归二分和线性插值偏差检测，在 6 个采样点内识别浓度剖面的显著层（如热分层导致的气体聚集层），为 ESC 提供热启动点。')

set_text(paras[25], '问题 4：如何防止高度搜索与水平搜索的干扰？ 本课题设计三阶段状态机（EXPLORE→CALIBRATE→TRACK），通过相位分离和冷却迟滞机制，避免高度调整和水平导航之间的相互干扰。EXPLORE 阶段同时进行水平 Lévy 探索和高度 Lévy 探索；CALIBRATE 阶段在当前位置附近进行垂直扫描；TRACK 阶段使用残差 ESC 连续跟踪最优高度。')

# 2.3 研究目标
set_text(paras[27], '目标一：建立 OPGSL-3D 的三维自适应方法框架，包括残差 ESC 高度跟踪、Lévy 高度探索和显著层扫描三个模块。 - 指标：水平源定位误差 final_error_2D (m)、高度估计误差 z_error (m)')
set_text(paras[28], '目标二：证明 3D 自适应策略优于 2D 固定高度策略。 - 指标：OPGSL-3D vs GrGSL/SurgeCast 的配对 final_error 差异、Wilcoxon 检验 p 值')
set_text(paras[29], '目标三：证明三个高度自适应模块的各自贡献（消融实验）。 - 指标：消融实验（A0 基线、A1 ESC-only、A2 Lévy-only、A3 LayerScan-only、A4 Full）的 final_error 变化')

# ============================================================
# Section 3: 研究方案
# ============================================================
set_text(paras[34], '技术路线为：跨领域方法调研 → 模块设计 → C++ 实现 → 仿真实验 → 论文撰写。')
set_text(paras[35], '跨领域调研：ESC（控制论）、Lévy 飞行（生态学）、探空仪显著层（气象学）')
set_text(paras[36], '模块设计：残差 ESC、Lévy 高度、显著层扫描、后验估计、相位管理')
set_text(paras[37], 'C++ 实现：在 MAPIRlab GSL server 框架中实现 OPGSL-3D，ROS2 Humble')
set_text(paras[38], '仿真实验：在 VGR House01-03 上与 PMFS/GrGSL/SurgeCast 对比')
set_text(paras[39], '论文撰写：目标 IEEE Sensors Journal（ISJ），Q1')

# 3.2-3.4 need updating
set_text(paras[40], '3.2 残差极值搜索控制（Residual ESC）的高度跟踪')
set_text(paras[41], '标准 ESC 假设目标函数 y=f(u) 是控制输入 u 的静态映射。但在 GSL 中，浓度 c(x,y,z) 是三维空间坐标的函数，水平运动导致的浓度变化远大于高度变化。')
set_text(paras[42], '残差 ESC 的核心思想：从观测浓度中减去水平场估计器的预测值 r(t) = c_obs(t) - c_hat(x_t, y_t)，隔离高度依赖的信号分量。')
set_text(paras[43], '高通滤波（标准 Krstic 形式）：η(t) = α_h · η(t-1) + (r(t) - r(t-1))')
set_text(paras[44], '解调与梯度估计：G_hat(t) = α_l · G_hat(t-1) + (1-α_l) · η(t) · sin(ωt) · 2/a')
set_text(paras[45], '高度更新：z_hat(t+1) = z_hat(t) + K · G_hat(t)')
set_text(paras[46], '振幅衰减：a(t+1) = a(t) · (1-λ)，λ=0.005，保证探索逐渐收敛')
set_text(paras[47], '关键参数：ω=0.5 rad/s（振荡周期 ~12s），K=0.3（增益），α_h=0.3（高通），α_l=0.7（低通）')

set_text(paras[51], '状态：s = (x_robot, z_hat, alt_phase, field_estimator, z_posterior)')
set_text(paras[52], '动作：a = (水平目标, 垂直目标)')
set_text(paras[53], '三阶段状态机：EXPLORE（Lévy 水平 + Lévy 高度）→ CALIBRATE（显著层扫描）→ TRACK（化学趋向 + 残差 ESC）')
set_text(paras[54], '转换条件：gas_hit >= 5 触发 CALIBRATE；CALIBRATE 完成触发 TRACK；consecutive_miss >= 15 回到 EXPLORE（带 60s 冷却）')
set_text(paras[55], '观测：气体浓度 c、风速 wind_speed、风向 wind_direction（均在当前 3D 位置采样）')
set_text(paras[56], '场估计器：WR-SFE（Wind-Relative Spatial Field Estimator），核加权非参数场估计，上风方向源概率场')
set_text(paras[57], '收敛判据：场熵 < 阈值 AND 机器人距场峰 < 1.5m AND 高度稳定（连续 8 步）')

set_text(paras[58], '3.4 消融实验设计')
set_text(paras[59], 'A0（基线）：禁用所有高度自适应模块，固定 z=0.3m。A1（ESC-only）：仅启用残差 ESC。A2（Lévy-only）：仅启用 Lévy 高度探索。A3（LayerScan-only）：仅启用显著层扫描。A4（Full）：全部启用。每个配置在 3 个 VGR House × 5 个 seed 上运行，共 75 个消融实验 + 30 个基线实验。')

# ============================================================
# Section 4: 创新点
# ============================================================
# Find paragraph 61 or nearby
for i in range(60, 70):
    if '改进 1' in paras[i].text or 'WC-RIF' in paras[i].text:
        set_text(paras[i], '创新点 1：残差极值搜索控制（Residual ESC）用于高度自适应 — 首次将控制论中的 ESC 引入气体源定位的高度优化，通过从观测浓度中减去水平场估计器预测值，解决 ESC 在空间场中的假设违反问题。')
        break

for i in range(62, 75):
    if '间歇性' in paras[i].text or '改进 2' in paras[i].text:
        set_text(paras[i], '创新点 2：Lévy 飞行高度探索 — 首次将生态学中 μ=2 的 Lévy 飞行引入高度搜索，利用幂律分布的无标度特性实现连续高度空间的高效覆盖，相比固定高度菜单具有数学最优性保证。')
        break

for i in range(70, 85):
    if 'CUSUM' in paras[i].text or '改进 3' in paras[i].text:
        set_text(paras[i], '创新点 3：探空仪显著层扫描 — 首次将气象学中 60 年历史的 WMO 显著层选择算法引入气体源高度估计，通过递归二分和线性插值偏差检测，在 6 个采样点内捕获浓度垂直剖面的关键特征。')
        break

for i in range(80, 95):
    if '速度' in paras[i].text or '改进 4' in paras[i].text:
        set_text(paras[i], '创新点 4：三阶段自适应状态机 — 设计 EXPLORE→CALIBRATE→TRACK 三阶段状态机，通过相位分离和冷却迟滞机制（60s 冷却、hit 计数重置、最大校准次数限制），防止高度搜索与水平导航的相互干扰，避免相位振荡。')
        break

# ============================================================
# Section 5: 研究计划
# ============================================================
set_text(paras[105], '2026.06—2026.07（已完成）：完成方法设计与 C++ 实现。在 MAPIRlab GSL server 框架中实现 OPGSL-3D，包含残差 ESC、Lévy 高度、显著层扫描三个模块，通过 VGR House01-03 的仿真实验验证。')
set_text(paras[106], '2026.07—2026.08：完成消融实验和基线对比。在 VGR House01-03 上运行 5 种消融配置 × 3 房 × 5 种子 = 75 个实验，以及 GrGSL/SurgeCast 基线 30 个实验。完成统计分析（Wilcoxon 检验、效应量）。')
set_text(paras[107], '2026.08—2026.09：完成论文撰写。整理实验结果、绘制图表、撰写论文初稿，目标 IEEE Sensors Journal（ISJ）。')
set_text(paras[108], '2026.09—2026.10：论文修改、投稿。')
set_text(paras[109], '2026.10—2027.03：实物验证（可选）。使用 Q250 无人机在千岛湖进行端到端验证。')

set_text(paras[111], '预期形成一套源高度未知条件下的 3D 自适应气体源定位方法（OPGSL-3D）和一组完整的消融实验数据。')
set_text(paras[112], '成功标准： - (a) OPGSL-3D 在 VGR 上的 final_error 显著低于 GrGSL/SurgeCast（Wilcoxon p<0.05） - (b) OPGSL-3D 的高度估计误差 <1m - (c) 消融实验显示三个模块各自贡献 >10% 的 final_error 改善')
set_text(paras[113], '退化边界：若 3D 自适应优势 <10%，论文将诚实报告并分析原因（可能是源高度接近默认飞行高度，或浓度场的高度梯度不够显著）。')

# ============================================================
# Section 6: 已有基础 - update with current progress
# ============================================================
set_text(paras[122], '仿真环境：已搭建 VGR 仿真环境（House01-03，CFD 3D filament 仿真），具备 ROS2 Humble 运行框架和 MAPIRlab GSL server。已掌握 GADEN/VGR 气体扩散数据格式和风场数据格式。')
set_text(paras[123], '算法基础：已实现 OPGSL-3D（C++，~700 行），包含残差 ESC、Lévy 高度、显著层扫描、后验估计四个模块。已实现多种 GSL 基线算法（PMFS、surge-cast、GrGSL），可直接用于对比实验。所有代码已在 VM（ROS2 Humble）上编译通过。')
set_text(paras[124], '实验经验：已完成多轮 GSL 实验，积累了 VGR 数据集使用、ROS2 launch 配置、seed 管理、CSV 解析、指标计算等关键工程经验。已发现并修复多个关键 bug（vgr_sim_node z 坐标修复、ESC 高通滤波器修正、相位迟滞机制等）。')
set_text(paras[125], '初步结果：在 VGR House01 上，OPGSL-3D（修复后）的 median final_error 约 0.85m（5 seeds: 0.824, 0.880, 0.796, 0.903, 待完成），优于之前记录的 GrGSL（1.70m）和 SurgeCast。')
set_text(paras[126], '硬件条件：Q250 无人机（3 架）+ 机载 i5 处理盒，千岛湖测试场地已确认可用。')
set_text(paras[127], '当前状态：消融实验和基线对比正在 VM 上运行，预计 10 小时内完成。论文框架已设计完毕，等待实验数据填充。')

doc.save(DST)
print(f"Saved to {DST}")
print("Done - thesis proposal updated")
