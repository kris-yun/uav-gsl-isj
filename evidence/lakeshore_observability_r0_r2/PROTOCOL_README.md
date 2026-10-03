# 湖岸场景机制最小验证实验协议（给 Codex）
日期：2026-10-03
目标：在不发明新算法、不改 PMFS、不进入闭环的前提下，先验证“湖岸低空气象结构是否会系统性改变 UAV 气体源定位的可观测性”，并判断“主动三维诊断采样”是否值得升为主创新机制。

## 0. 冻结原则
1. 本轮只做离线机制验证，不训练神经网络，不做闭环导航，不设计最终算法。
2. 不把 Allouche/JGR LES 直接作为 GADEN 瞬态 3D 风场；它只提供物理状态与参数范围。
3. WiscoDISCO-21 只用于真实湖岸结构证据，不计算源定位误差。
4. PMFS 只保留为后续 baseline；本轮主判据不用 PMFS，避免把“场景效应”和“某算法失配”混在一起。
5. 每一阶段有 GO/HOLD/STOP 门；未过门不得继续下一阶段。
6. 所有新生成风场、气体场、源位置、随机种子、阈值、轨迹和脚本均冻结 MANIFEST+SHA256。

---

## 1. 本轮实际需要的数据

### A. WiscoDISCO-21（必须）
用途：证明真实湖岸一次任务时间尺度内确实存在垂直分层/风切变/湖风入侵等结构。

优先案例：
- 2021-05-22，论文明确标记 18:00 UTC 后湖风入侵；
- 18:30–19:00 UTC 为过渡窗口；
- 21:00 约 250 m AGL marine layer；
- 22:00 约 100 m AGL marine layer。

优先变量：
- lidar profiles：height, windSpeed, windDir；
- M210：Altitude_Average_magl, Temperature_Average_degC, RH；
- RAAVEN：风矢量/温湿度仅作补充，先解决 MSL→AGL 后再做绝对高度合并；
- 暂不把 stare 文件作为主证据，因为审计已发现日期/height 单位契约疑点。

### B. JGR 2025 Allouche LES（必须但只作物理边界）
用途：约束湖岸热力环流的背景风/状态范围，不能直接送进 GADEN。

只用：
- Mg=0.4 m/s, alpha=0°：主候选；
- Mg=2 m/s, alpha=0°：高背景风对照；
- U/W/T X-Z 平均结构与论文物理结论。

不要做：
- 不在时间轴/reshape 契约未解开前构造 matched snapshot；
- 不把二维时间/横向平均场伪装成瞬态 XYZ 风场。

### C. 新生成的局地 GADEN/GADEN-RT 湖岸机制数据（本轮核心）
这是唯一承担“湖岸结构是否伤害 GSL”因果检验的数据。

### D. House01–03（第二优先级）
只在湖岸机制出现正信号后，作为“普通复杂障碍环境”负对照/回归检查。
本轮第一刀不需要重跑 House。

### E. TopoGSL、Merced、PG&E
本轮不用。
TopoGSL 留到最终算法 baseline；
Merced/PG&E 留到后续真实 UAV 外部验证。
不要把精力分散到这些数据上。

---

## 2. Phase R0：真实湖岸结构证据（WiscoDISCO）

### 2.1 目标
只回答：
“在一次 UAV 任务相关的时间窗内，低空不同高度的风/温度结构是否显著不同？”

不是回答 GSL。

### 2.2 数据窗口
以论文标记为锚，不自行重新定义 lake-breeze event。

对 2021-05-22：
- PRE：选择 18:00 UTC 前最近一个数据覆盖完整的 30–60 min 窗；
- TRANSITION：18:30–19:00 UTC；
- POST：21:00 和 22:00 附近各取 ±15 min（若覆盖不足则记录实际可用窗）。

### 2.3 计算
按 20–25 m 高度 bin 统计：
- windSpeed(z)
- circular mean windDir(z)
- vertical wind-direction shear：Δdir(z1,z2)
- wind-speed shear：ΔU/Δz
- M210 temperature lapse / inversion strength
- 各窗口 profile-to-profile variability

重点高度：
0–50 m、50–100 m、100–200 m（按数据覆盖调整，不硬插值）。

### 2.4 输出
- `R0_wisco_profiles.png`
- `R0_wisco_vertical_shear.csv`
- `R0_wisco_temperature_structure.csv`
- `R0_wisco_effect_summary.json`

### 2.5 R0 判定
R0_GO：
至少在论文已标记的湖风窗口中，观察到“低层与上层明显不同”的可重复结构，并且强于 PRE 窗口；报告实际效应量，不为了过门修改窗口。

R0_HOLD：
有结构但平台/时间覆盖不足，需更多日期复核。

R0_STOP：
论文标记事件在可用公开数据里无法复现任何垂直结构差异，且问题不是数据缺失/同步契约。

R0 未通过，不进入 GADEN 机制实验。

---

## 3. Phase R1A：构造最小局地湖岸风场，不做高成本热 CFD

### 3.1 为什么先这样做
第一刀目的是隔离机制，不是证明整个湖岸 CFD。
先用“受公开数据约束的参数化 3D 风场”回答：若存在浅薄低层流、垂直风切变、锋面辐合/抬升，它是否会改变 GSL 可观测性？
若连这个理想化门都不过，没有必要做昂贵 CFD。

### 3.2 计算域
建议：
- x（跨岸）：-50 m ～ 200 m
- y（沿岸）：-60 m ～ 60 m
- z：0 ～ 120 m
- shoreline：x=0
- open/flat geometry，第一刀不加建筑和植被
- 网格 2.5–5 m，优先保证计算可承受

### 3.3 四个环境，只改变风场
所有源、轨迹、释放、采样预算相同。

**N0：普通均匀风**
- 水平 onshore 风；
- 无垂直风；
- 无垂直切变；
- 作为普通场景控制。

**L1：湖岸浅薄低层流/垂直切变**
- 低层 onshore 风明显；
- 上层风速减弱或方向偏转；
- w≈0；
- 只隔离“分层/风切变”。

**F1：湖风锋辐合+中等抬升**
- 低层湖风在 x_front 附近与前方背景流形成平滑辐合；
- 由连续性构造正的 w；
- 目标 `w_max ≈ 0.5 m/s`；
- 只做中等强度。

**F2：湖风锋辐合+较强抬升**
- 同 F1；
- `w_max ≈ 1.0 m/s`；
- 用于强度敏感性，不作为唯一结果。

建议采用连续、可微、近似散度约束的参数化风场：
1. 先定义 `u(x,z)` 为“低层 behind-front 强 onshore、ahead-front 弱/反向背景流”的平滑 tanh 结构；
2. 再由
   `w(x,z) = -∫_0^z ∂u/∂x dz`
   构造垂直速度；
3. 对顶部边界做小幅修正，使 `w(z_top)` 接近 0；
4. `v=0` 为第一刀，后续才加 alongshore 扰动。

不要为了产生效果手工在局部塞一个浓度/上升区。

### 3.4 风场参数来源
- 湖风层高度和垂直结构范围：WiscoDISCO R0；
- 背景风强度/状态对照：JGR 2025；
- 第一刀允许在合理范围内做 2 个强度，但参数必须在运行前冻结。

---

## 4. Phase R1B：气体传播数据生成

### 4.1 源
先固定 9 个候选源：
- x = {20, 50, 80} m
- y = {-20, 0, 20} m
- z = 1 m

front 建议初始 `x_front = 120 m`，保证大部分源位于 front 上游并可跨越 front。

### 4.2 随机传播
每个：
- 环境 × 源
- K=8 个独立 GADEN plume realization 起步；
- 若主效应接近门槛，再扩 K=16；
- seed 必须显式登记，不允许把导航 seed 当 plume seed。

### 4.3 释放
不要沿用 House 中审计不完整的 release contract。
为本湖岸实验新建并冻结完整 release 配置。

建议先预注册 3 个 release level（low / mid / high），全部运行。
主结论要求至少 2/3 release level 同方向，避免靠单一释放强度“调出效果”。

### 4.4 观测
第一层用 ideal concentration / hit，隔离大气机制。
采样率统一 1 Hz。

hit threshold：
- 主阈值使用新场景统一固定值；
- 同时做 0.5× / 2× 阈值敏感性；
- 不允许每个环境单独调阈值。

传感器 response/recovery 暂不作为主实验；
机制门通过后再做 1/3/5 s 一阶响应敏感性。

---

## 5. 固定 UAV 轨迹：不闭环

### 5.1 横向轨迹
所有高度复用完全相同 XY 轨迹。

推荐 3 条 crosswind transect：
- x=100 m
- x=130 m
- x=160 m
- y=-40 ～ +40 m

用连接段组成一条 ladder path，重复直到 300 s。
速度固定 2 m/s（若现有平台规范不同则用平台常用值，但全条件一致）。

### 5.2 高度
分别运行：
- z=10 m
- z=30 m
- z=60 m
- z=100 m

这样得到完全等轨迹、仅高度不同的数据。

---

## 6. 四个核心诊断指标

### M1：局地风“指向真源”的有效性
对每个观测点 q：
- 取水平局地风 `u_h(q)`；
- 计算 upwind 方向 `-u_h`;
- 计算 q→true source 的 bearing；
- 得角误差 `e_theta`。

只在有气体证据或距离源合理的段落统计，避免远场无意义点。

输出：
- median / q75 angular error
- true source 是否落入 ±45° upwind cone 的比例

问题：
湖风分层/锋面是否让“沿当前上风向找源”显著变差？

### M2：低层未检出是否形成“假阴性盲区”
跨 K 个 plume realization 估计每个轨迹点/高度的：
`p_hit(q,z)`。

定义候选盲区（不要直接写死为结论）：
- 在 N0 中某位置 `p_hit >= 0.5`
- 在 F1/F2 的低高度 `p_hit <= 0.2`
- 同一 XY 的较高高度又恢复 `p_hit >= 0.5`

输出：
- blind-zone spatial fraction
- low→high hit probability recovery
- 对 source / release / seed 的稳定性

问题：
“低层没闻到”是否可能只是 plume 被抬升，而不是 source 不存在？

### M3：浓度峰值是否被 front/汇合结构搬走
对每个 seed：
- 在 UAV 可达轨迹上找浓度最大点；
- 记录 `d_peak_to_source`
- 记录 `d_peak_to_front`

观察：
不同 source 是否在 F1/F2 中反复把峰值集中到 front 附近，而 N0 不会。

问题：
“追最高浓度”是否可能追到湖风结构而不是真源？

### M4（主指标）：源可辨识性是否具有高度盲区
这一步不用 PMFS，避免算法偏差。

对每个环境、每个候选源、每个高度：
1. 有 K 个 stochastic plume realizations；
2. leave-one-realization-out；
3. 用 K-1 个 realization 为每个候选源估计每个时间点的 hit probability；
4. 对 held-out test realization 用 Brier score 给 9 个候选源打分；
5. 按 Brier 从低到高排序；
6. 记录 true-source rank / Top-1 / Top-3。

概率估计使用 Beta(1,1) 平滑：
`p_hat = (1 + hits)/(2 + K-1)`。

这一步回答最核心的问题：
**同一个搜索轨迹，仅改变高度，真实源是否在湖岸 front 场景中从“不可辨”变成“可辨”？**

这比单纯看浓度场重要得多。

---

## 7. R1 总判据

### Primary Gate：高度依赖源可辨识性
R1_PRIMARY_PASS 需要：
- F1/F2 中不同高度的 Top-1 success spread ≥ 25 percentage points；
- 且 median true-source rank 至少相差 2 个名次；
- 效果至少出现在 2 个不同 x 源位置，并在 ≥6/8 seed 中方向一致；
- 同时 N0 的高度差明显更小（建议 <10 pp，或至少小于 front effect 的一半）。

### Secondary Gate
M1/M2/M3 至少一项满足明确场景效应：
- M1：upwind-cone capture 相对 N0 下降 ≥20 pp；
或
- M2：存在低层 p_hit 下降 ≥0.3、较高层恢复的盲区，且跨 ≥2 source 稳定；
或
- M3：峰值在多个不同 source 下明显聚集于 front，而非随 source 移动。

### 判定
- `R1_PASS_LAKESHORE_OBSERVABILITY_DISTORTION`：
  Primary PASS + 至少 1 个 Secondary PASS。
- `R1_HOLD_WEAK_OR_UNSTABLE`：
  仅 Secondary 有信号，或 Primary 接近但 seed 不稳。
- `R1_FAIL_STOP_SCENE_MECHANISM`：
  Primary 不通过且 Secondary 无稳定信号。

FAIL 后不要设计主动感知算法。

---

## 8. Phase R2：只在 R1 PASS 后测试“主动三维诊断动作”

目的：证明创新不是“切算法”，而是主动改变观测条件能消除歧义。

### 8.1 找歧义点
只使用开发集：
- true-source rank 差；
- Top1/Top2 Brier 接近；
- 或 M2 blind-zone 位置。

不要用最终测试真源标签实时触发。

### 8.2 两个等预算动作
固定额外 30 s。

**A：水平控制动作**
- 原高度继续横移/沿原路径采样 30 s。

**B：垂直诊断动作**
- 当前 XY 附近执行 10→40→10 m（或按可飞空间等价高度差）微剖面；
- 总时间同样 30 s；
- 新观测并入同一个候选 scoring，不换算法。

### 8.3 R2 指标
比较动作前后：
- true-source rank
- Top-1 / Top-3
- Brier gap(true source vs best false source)
- unresolved rate

### 8.4 R2 Gate
`R2_PASS_ACTIVE_DIAGNOSTIC_SIGNAL`：
在 F1/F2 中垂直诊断相对等预算水平动作：
- Top-1 提升 ≥15 pp，或
- median true-source rank 至少改善 1；
- 至少 2 个 source 位置成立；
- seed 方向稳定；
- N0 中收益明显较小。

若不通过：
`R2_FAIL_STOP_ACTIVE_DIAGNOSTIC`
说明湖岸机制可能存在，但“垂直主动诊断”不是正确解决方案，需重新找机制。

---

## 9. 暂时不要做的事
- 不训练 GFNO / diffusion / world model；
- 不做 full closed-loop；
- 不把 PMFS 改成新方法；
- 不上 TopoGSL；
- 不把 Merced/PG&E 强行分航次；
- 不做建筑/植被；
- 不加多无人机；
- 不把 R0/R1 的正信号提前写成“创新已成立”。

---

## 10. 只有 R1+R2 都通过后才进入的下一步
届时才设计正式方法：
1. 湖岸结构状态/歧义检测器；
2. 源位置概率反演；
3. 主动三维诊断触发；
4. GADEN-RT 闭环；
5. PMFS / TopoGSL / fixed-route / information strategy 等强基线；
6. 最后 Merced/实飞做外部验证。

---

## 11. Codex 工程交付要求
建议分支：
`research/lakeshore-observability-r0-r2-20261003`

必须提交：
- `experiments/lakeshore_observability/README.md`
- `configs/*.yaml`
- `scripts/build_parametric_wind.py`
- `scripts/run_gaden_matrix.py`
- `scripts/extract_fixed_paths.py`
- `scripts/score_identifiability.py`
- `scripts/score_mechanisms.py`
- `scripts/run_active_probe_offline.py`（仅 R1 PASS 后）
- `evidence/lakeshore_observability_r0_r2/`
  - `MANIFEST.csv`
  - `SHA256SUMS.txt`
  - `R0_WISCO_REPORT.md`
  - `R1_MECHANISM_REPORT.md`
  - `R2_ACTIVE_PROBE_REPORT.md`（若执行）
  - 所有 CSV/JSON/PNG
  - `FINAL_DECISION.json`

`FINAL_DECISION.json` 只允许：
- `R1_PASS_LAKESHORE_OBSERVABILITY_DISTORTION`
- `R1_HOLD_WEAK_OR_UNSTABLE`
- `R1_FAIL_STOP_SCENE_MECHANISM`
- 若 R1 PASS 后：
  - `R2_PASS_ACTIVE_DIAGNOSTIC_SIGNAL`
  - `R2_FAIL_STOP_ACTIVE_DIAGNOSTIC`

最后回报：
branch、commit、每个 Gate 数值、最终判定、证据 ZIP 路径和 SHA256。
