# CP-SBD-GSL 项目完整交接文档

**最后更新**: 2026-07-03
**项目状态**: 实验进行中，存在多个已知问题需要解决

---

## 一、项目概述

### 1.1 研究目标
UAV气体源定位（GSL），目标投稿IEEE Sensors Journal (ISJ, Q2, IF~3.4)。

### 1.2 方法：CP-SBD-GSL
Conformal Prediction-guided Sequential Bayesian Design，三个核心模块：
- **DDM-Stopping**：漂移扩散模型停止准则（灵感来自神经科学Gold & Shadlen 2007）
- **W-RAIG**：Wasserstein风险感知信息增益（风险控制决策）
- **CP-Stopping**：Conformal Prediction停止准则（分布无关终止保证）

### 1.3 当前评分
ISJ副主编视角：4.5/10，审稿人视角：5.5/10。**当前不可投稿**。

---

## 二、VM环境

### 2.1 访问信息
- **IP**: 192.168.111.128
- **用户**: zyc / **密码**: 123456
- **ROS2**: Humble
- **工作空间**: /home/zyc/gsl_ws/

### 2.2 关键路径
```
# 我们的方法代码
/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/
├── OPGSL.cpp          # 主算法（~1500行，包含DDM/W-RAIG/CP集成）
├── OPGSL.hpp          # 头文件
├── WATS_GSL.hpp       # 场估计器 + WRAIG类
├── DDM_Stopping.hpp   # DDM停止模块
├── CP_Stopping.hpp    # CP停止模块
└── CMakeLists.txt

# VGR数据集（3个House，CFD 3D filament仿真）
/home/zyc/vgr_data_scenarios/
├── House01/           # config_id: 2,4-1_fast, 源: (-0.40, -2.90, -0.30)
├── House02/           # config_id: 3,5-1_fast, 源: ( 0.00, -1.00,  0.20)
└── House03/           # config_id: 1-2,5_fast, 源: (-0.45,  1.90, -0.10)

# Launch文件
/home/zyc/gsl_ws/src/vgr_bridge/launch/
├── vgr_ablation.launch.py      # 我们方法的launch（有ablation开关）
├── vgr_gsl_pmfs.launch.py      # 经典方法launch（PMFS/GrGSL/SurgeCast通用）
└── vgr_gsl_benchmark.launch.py # 简单benchmark launch

# 实验结果
/tmp/cp_sbd_exp/
├── ablation_summary.csv        # 3-seed消融（36 runs，已完成）
├── baselines_final.csv         # 经典基线（27 runs，已完成）
├── extended_ablation_fixed.csv # 扩展消融（36 runs，已完成，部分缺失）
└── ablation_10seeds.csv        # 10-seed消融（进行中，有大量失败）
```

### 2.3 编译命令
```bash
ssh zyc@192.168.111.128
cd /home/zyc/gsl_ws
source install/setup.bash
colcon build --packages-select gsl_server
```

---

## 三、如何运行实验

### 3.1 运行我们的方法（OPGSL + ablation开关）

```bash
# SSH到VM
ssh zyc@192.168.111.128
cd /home/zyc/gsl_ws && source install/setup.bash

# 运行Full方法（DDM+W-RAIG+CP全部开启）
ros2 launch vgr_bridge vgr_ablation.launch.py \
    vgr_data_path:=/home/zyc/vgr_data_scenarios/House01 \
    config_id:=2,4-1_fast \
    algorithm:=OPGSL \
    method:=M7_full_saisc_pf \
    source_x:=-0.40 source_y:=-2.90 source_z:=-0.30 \
    start_x:=-0.9 start_y:=0.15 \
    seed:=0 \
    timeout_sec:=300 \
    use_sbd:=true \
    opgsl_ddm:=true opgsl_wraig:=true opgsl_cp:=true \
    opgsl_wraig_beta:=0.5

# Ablation开关：
# Full:      opgsl_ddm:=true  opgsl_wraig:=true  opgsl_cp:=true
# NoDDM:     opgsl_ddm:=false opgsl_wraig:=true  opgsl_cp:=true
# NoWRAIG:   opgsl_ddm:=true  opgsl_wraig:=false opgsl_cp:=true
# NoCP:      opgsl_ddm:=true  opgsl_wraig:=true  opgsl_cp:=false
# CPonly:    opgsl_ddm:=false opgsl_wraig:=false opgsl_cp:=true
# DDMonly:   opgsl_ddm:=false opgsl_wraig:=true  opgsl_cp:=false
# WRAIGonly: opgsl_ddm:=true  opgsl_wraig:=false opgsl_cp:=false
# Baseline:  opgsl_ddm:=false opgsl_wraig:=false opgsl_cp:=false
```

### 3.2 运行经典基线（PMFS / GrGSL / SurgeCast）

经典基线使用**同一个launch文件**，通过`algorithm`参数切换：

```bash
# PMFS
ros2 launch vgr_bridge vgr_gsl_pmfs.launch.py \
    vgr_data_path:=/home/zyc/vgr_data_scenarios/House01 \
    config_id:=2,4-1_fast \
    algorithm:=PMFS \
    source_x:=-0.40 source_y:=-2.90 source_z:=-0.30 \
    start_x:=-0.9 start_y:=0.15 \
    seed:=0 \
    flight_height:=0.3

# GrGSL
ros2 launch vgr_bridge vgr_gsl_pmfs.launch.py \
    ... algorithm:=GrGSL ...

# SensorAwareSurgeCastPF（官方实现，不是我们自己写的）
ros2 launch vgr_bridge vgr_gsl_pmfs.launch.py \
    ... algorithm:=SensorAwareSurgeCastPF ...
```

**重要**：经典基线的launch文件是`vgr_gsl_pmfs.launch.py`，不是`vgr_ablation.launch.py`！

### 3.3 已验证的批量脚本模板

之前成功运行的脚本在VM上：`/tmp/extended_ablation.sh`

关键技巧：
1. `ros2 launch ... > log 2>&1 &` 后台运行
2. 轮询日志检测 `DONE, CLOSING`
3. `kill -0 $LPID` 检查进程是否存活
4. `pkill -9 -f gsl_actionserver_node` 清理（在每次run之前）
5. 用 `sed 's/\x1b\[[0-9;]*m//g'` 去除ANSI颜色码再解析
6. 用 `sed` 而不是 `grep -oP` 提取数据（更可靠）

---

## 四、已有实验数据

### 4.1 消融实验（3 seeds × 3 houses，ablation_summary.csv）

| Config | House01 | House02 | House03 | Median | Mean | Std |
|--------|---------|---------|---------|--------|------|-----|
| Full | 1.015-1.574 | 1.616-1.983 | 1.244-1.333 | **1.333** | 1.431 | 0.307 |
| NoDDM | 1.635-3.345 | 1.473-1.892 | 0.784-1.377 | 1.635 | 1.757 | 0.725 |
| NoWRAIG | 0.679-1.520 | 1.460-1.690 | 2.146-2.505 | 1.610 | 1.688 | 0.585 |
| Baseline | 1.295-1.646 | 1.690-2.863 | 0.755-0.829 | 1.646 | 1.639 | 0.758 |

**统计检验**（Wilcoxon signed-rank，3 seeds）：
- Full vs Baseline: p=0.89 (不显著)
- Full vs NoDDM: p=0.48 (不显著)
- Full vs NoWRAIG: p=0.26 (不显著)

### 4.2 经典基线（3 seeds × 3 houses，baselines_final.csv）

| Method | House01 | House02 | House03 | Median |
|--------|---------|---------|---------|--------|
| **CP-SBD-GSL** | 1.0-1.6m | 1.6-2.0m | 1.2-1.3m | 1.333 |
| **SensorAwareSurgeCastPF** | 2.9-3.9m | **0.3-0.5m** | **0.8-1.5m** | ~0.75 |
| GrGSL | 3.7-4.2m | 3.6-7.3m | 2.2-7.6m | 4.178 |
| PMFS | 3.0-3.1m | 5.2-6.8m | 5.5-6.3m | 5.242 |

**关键发现**：SurgeCast在House02和House03显著优于我们！只有House01我们更好。

### 4.3 扩展消融（单模块测试，3 seeds，extended_ablation_fixed.csv）

| Config | House01 | House02 | House03 |
|--------|---------|---------|---------|
| NoCP | 0.55,0.04,- | 0.05,1.23,0.73 | 1.92,1.83,1.86 |
| DDMonly | 0.50,-,0.93 | 0.66,1.54,0.37 | 1.87,0.05,1.27 |
| WRAIGonly | 0.43,-,- | 0.92,2.16,0.28 | 1.58,0.02,2.18 |
| CPonly | -,-,0.02 | 0.98,0.19,0.51 | 2.48,0.02,1.33 |

**关键发现**：CPonly在House02达到0.19m，但Full在House02是1.6-2.0m。**模块间存在负协同效应**。

### 4.4 10-seed消融（进行中，ablation_10seeds.csv）

目前133个数据点，但大量缺失（很多run被cleanup误杀或distance提取失败）。脚本仍在VM上运行中。

---

## 五、已知问题（按严重程度排序）

### 🔴 致命问题

**P1: SurgeCast在2/3场景优于我们**
- House02: SurgeCast 0.3-0.5m vs 我们 1.6-2.0m（4-6倍差距）
- House03: SurgeCast 0.8-1.5m vs 我们 1.2-1.3m
- House01: 我们 1.0-1.6m vs SurgeCast 2.9-3.9m（唯一优势）
- **SensorAwareSurgeCastPF是MAPIRlab官方实现**，在`gsl_server`包中，不是我们自己写的

**P2: 统计不显著**
- Full vs Baseline: p=0.89, Cliff's δ=0.000
- 3 seeds太少，需要至少10-20 seeds
- 没有bootstrap CI或Wilcoxon检验

**P3: CPonly > Full 消融矛盾**
- CPonly在House02达0.19m，Full在House02是1.6-2.0m
- 说明DDM和W-RAIG可能有害（过早停止阻止了CP收敛）
- 消融逻辑基础被动摇

### 🟡 严重问题

**P4: CP Exchangeability假设被违反**
- 标准CP要求i.i.d./exchangeable
- UAV GSL中：传感器漂移、风场时变、自适应轨迹 → 分布持续变化
- 需要用adaptive CP (Gibbs & Candès 2021)或证明drift有界

**P5: 模块是"浅层移植"**
- DDM本质 = 带时间衰减的SPRT变体（Cisek 2009已有robotics应用）
- W-RAIG = 信息增益 × Wasserstein权重
- 缺乏GSL-specific理论贡献

**P6: 单数据集**
- 只在VGR上验证，需要GADEN或MATRIX数据集
- VGR的3个house只是同一数据集的不同配置

### 🟢 已解决的问题

**P7: 无数据泄露** ✅
- OPGSL.cpp中没有引用ground_truth位置
- source_x/y/z只传给benchmark_runner（用于日志记录），不传给算法

**P8: benchmark_runner trace文件问题** ⚠️ 部分解决
- benchmark_runner因"missing synchronized trace file"崩溃
- 不影响算法本身运行，但导致结果不写入官方CSV
- 解决方案：直接从日志提取distance（见下方脚本模板）

---

## 六、代码结构

### 6.1 核心文件
```
OPGSL.cpp (~69KB, ~1500行):
  - SimpleGP: 高程自适应的GP模型
  - OPGSL::declareParameters(): 所有参数声明
  - OPGSL::onUpdate(): 主循环
  - 停止逻辑 (line 1340-1400):
    1. CP-STOP (line 1346): cp_stopping_.shouldStop()
    2. DDM-STOP (line 1354): ddm_stopping_.shouldStop()
    3. V5 Convergence (line 1376): entropy + distance check
    4. FAST EXIT (line 1393): step>=20 && best_hit>0.05 && near_hit

CP_Stopping.hpp: 滑动窗口conformal prediction
  - 残差的(1-alpha)分位数作为"宽度"
  - width < threshold(1.5)持续stable_req(3)步则停止

DDM_Stopping.hpp: 漂移扩散模型
  - 累积对数似然比（带泄漏的Ornstein-Uhlenbeck过程）
  - 自适应阈值: theta(t) = theta_0 * exp(-gamma*t) + theta_min
  - 最少25次观测、60秒才允许停止

WATS_GSL.hpp: 场估计器 + WRAIG类
  - W-RAIG(a) = E_m[EIG_m(a)] - beta * sqrt(Var_m[EIG_m(a)])
  - beta=0 退化为标准EIG (= Infotaxis)
```

### 6.2 参数说明
```
opgsl.modules.sbd:      启用SBD主框架
opgsl.modules.ddm:      启用DDM停止
opgsl.modules.wraig:    启用W-RAIG决策
opgsl.modules.cp:       启用CP停止
opgsl.modules.levy:     启用Lévy飞行探索
opgsl.modules.bout:     启用Bout探索
opgsl.modules.adaptive_step: 启用自适应步长
opgsl.modules.upwind_tracking: 启用上风追踪
opgsl.wraig.beta:       W-RAIG风险厌恶参数(0.5)
opgsl.cp.alpha:         CP显著性水平(0.10)
opgsl.cp.width_threshold: CP宽度阈值(1.5)
opgsl.ddm.urgency:      DDM紧迫性衰减率(0.005)
opgsl.ddm.theta_min:    DDM最小阈值(1.5)
```

---

## 七、GitHub仓库

- **地址**: https://github.com/kris-yun/cp-sbd-gsl (私有)
- **账号**: kris-yun
- **认证**: `gh auth login`
- **注意**: 论文接收后公开

---

## 八、下一步工作

### 优先级P0（必须完成）
1. **修复10-seed批量脚本**：当前脚本有cleanup误杀问题，需要用`extended_ablation.sh`模板
2. **增加seeds到10+**：当前3 seeds统计不显著
3. **运行统计检验**：Wilcoxon signed-rank + bootstrap CI
4. **修复CPonly > Full矛盾**：分析DDM和CP的停止时序冲突

### 优先级P1（应该完成）
5. **补GADEN数据集实验**
6. **补多起点敏感性实验**（3-5个起始位置）
7. **CP coverage实测表**（target 90% → actual X%）
8. **诚实处理SurgeCast更好的事实**

### 优先级P2（可以做）
9. **搜索2025-2026年最新跨领域创新文献**
10. **更新开题报告Word**
11. **推送代码到GitHub**

---

## 九、开题报告模板

- **模板文件**: D:\ZYC\A-gas\docs\template.doc
- **师兄参考**: D:\ZYC\A-gas\docs\senior_report.docx
- **注意**: 需要参考模板格式（字体、字号、章节结构）

---

## 十、关键命令速查

```bash
# SSH到VM
ssh zyc@192.168.111.128

# 编译
cd /home/zyc/gsl_ws && source install/setup.bash && colcon build --packages-select gsl_server

# 检查实验进度
wc -l /tmp/cp_sbd_exp/ablation_10seeds.csv
tail -10 /tmp/cp_sbd_exp/ablation_10seeds.csv

# 查看算法日志
grep -a 'OPGSL-AI\|CP-STOP\|DDM-STOP\|DONE' /tmp/cp_sbd_exp/Full_House01_s0.log

# 清理ros2进程
pkill -9 -f gsl_actionserver_node; pkill -9 -f vgr_sim_node; pkill -9 -f gsl_benchmark_runner

# 检查VM上的进程
ps aux | grep -E 'gsl_action|vgr_sim|ros2' | grep -v grep

# 本地代码目录
D:\ZYC\A-gas\src\    # 源代码
D:\ZYC\A-gas\docs\   # 文档
D:\ZYC\A-gas\scripts\ # 脚本
D:\ZYC\A-gas\launch\  # Launch文件
```

---

## 十一、多Agent审查报告

详见: `docs/MULTI_AGENT_REVIEW_20260703.md`

核心结论：
- 两位专家一致认为当前不可投稿（4.5-5.5/10）
- 最致命问题：SurgeCast在2/3场景优于我们
- 需要6-8周密集工作才能达到投稿门槛
- 故事应该定位为"risk-controlled decision-making"而非"precision improvement"