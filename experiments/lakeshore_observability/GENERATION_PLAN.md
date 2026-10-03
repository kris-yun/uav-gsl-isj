# C 类数据生成方案：局地湖岸 GADEN/GADEN-RT 机制数据

## 结论先行

本轮 C 类数据**不先用 OpenFOAM 做昂贵热力 CFD**。第一刀采用：

`Python 参数化三维风场生成器 -> GADEN/gaden_core 预处理 -> GADEN-RT/filament simulator 生成随机羽流 -> 固定 UAV 轨迹离线采样`

目的只是回答一个因果问题：如果真实湖岸文献所支持的“浅薄低层流、垂直风切变、锋面辐合/抬升”存在，它是否足以系统性改变源可辨识性。

若 R1/R2 通过，再升级为：

`WiscoDISCO/JGR 约束 -> OpenFOAM 局地热力 CFD -> GADEN/GADEN-RT -> 同一评价协议`

这样先低成本隔离机制，再做高保真确认。

---

## 1. 为什么可以这样生成

GADEN 官方工作流的风输入本质上是规则/点云形式的三维速度向量，典型文件为 `wind_at_cell_centers.csv`，随后由 preprocessing 转为 GADEN 的规则 3D 风网格。官方教程通常从 OpenFOAM/ParaView 导出该 CSV，但第一阶段并不要求 CSV 必须来自 OpenFOAM。

因此，本轮可以由 Python 直接生成满足相同几何/字段契约的规则三维速度点云，再交给 GADEN preprocessing。关键要求不是“来源必须是 CFD”，而是：
- 坐标、单位、网格和列格式正确；
- 风场连续、边界合理；
- F1/F2 的 `w` 由质量连续性近似构造，而不是随手画一个上升区；
- 全部参数在看 GSL 结果前冻结；
- 先做散度/边界/速度范围 QC。

---

## 2. Codex 先做运行时审计，不要先装新软件

在已有实验 VM 上检查：
1. 当前 ROS 2 GADEN 版本；
2. 是否已有 `gaden_core` / GADEN 3.x；
3. 当前 House/VGR 数据所用 GADEN 的 preprocessing / simulator 入口；
4. 一个现有小场景的 wind CSV 和预处理后 wind 文件格式；
5. 是否可直接使用 gaden_core Python binding；若不能，就沿用现有 ROS 2 GADEN CLI。

输出：
- `evidence/lakeshore_observability_r0_r2/runtime_audit.md`
- 现有 GADEN commit/version
- 现有 wind 输入文件头部 20 行（只记录格式，不复制大数据）
- 最终选择的 adapter：`gaden_core_python` 或 `ros2_gaden`

禁止为了本实验直接升级/替换现有 House 运行环境。

---

## 3. 风场生成

实现：
`experiments/lakeshore_observability/scripts/build_parametric_wind.py`

输入：
`configs/wind_N0.yaml`
`configs/wind_L1.yaml`
`configs/wind_F1.yaml`
`configs/wind_F2.yaml`

推荐大域：
- x: -100 .. 300 m
- y: -100 .. 100 m
- z: 0 .. 150 m
- evaluation ROI 仍按 README 中 -50..200, -60..60, 0..120 m
- 网格第一轮 5 m；只有结果需要才做 2.5 m 敏感性

### N0
`u=U0, v=0, w=0`

### L1
只做浅薄低层湖风+垂直切变：
`u(z)=U_upper + (U_low-U_upper)*0.5*(1-tanh((z-H_lake)/delta_z))`

若需要上层方向偏转，可加入小 `v(z)`，但第一版优先只改变 u(z)，减少自由度。

### F1/F2
在 L1 基础上加入平滑推进锋：
`s(x)=0.5*(1-tanh((x-x_front)/delta_x))`

令低层水平速度：
`u(x,z)=u_ahead(z)+(u_behind(z)-u_ahead(z))*s(x)`

然后由二维不可压缩近似：
`dw/dz = -du/dx`
从地面 `w(x,0)=0` 数值积分得到 w，并做顶部弱修正使 `w(x,z_top)≈0`。

F1/F2 只通过一个预注册强度参数改变，使：
- F1 `w_max≈0.5 m/s`
- F2 `w_max≈1.0 m/s`

这些强度是机制筛选，不是最终真实湖风定量结论。

### QC 必须通过
每个风场生成：
- `max|div U|`
- `w_max/w_min`
- `u/v/w` 分位数
- 边界值
- x-z quiver/streamline
- z=10/30/60/100 m 水平切片

如出现数值尖峰、网格尺度单元跳变或非物理局部喷流，STOP 修复，不运行 gas。

---

## 4. 转成 GADEN 可用输入

优先沿当前安装版本的现有格式，不硬编码旧版格式。

目标目录建议：

`experiments/lakeshore_observability/generated_project/`
- `cad_models/`
- `wind_simulations/N0/`
- `wind_simulations/L1/`
- `wind_simulations/F1/`
- `wind_simulations/F2/`
- `simulations/`
- `params/`

Python 输出 regular point-cloud wind CSV 后：

### 若使用 ROS 2 GADEN
用当前安装的 `gaden_preprocessing` / `gaden_preproc_launch.py` 把：
- 简单开放场景 occupancy
- regular wind point cloud
转换成 GADEN 3D wind grid。

### 若使用 gaden_core
用 `EnvironmentConfiguration` + `Preprocess()` 或官方示例中“manually preprocess wind files”的接口生成：
- `OccupancyGrid3D.csv`
- `wind/` 预处理文件

无论走哪条 adapter，必须用 N0 先跑 smoke test，验证：
- player/query 到的风与 Python 原始风在随机 100 个 grid points 上一致；
- 最大绝对误差 < 1e-5（若格式量化导致更大，记录真实误差并冻结容差）。

---

## 5. 环境几何

第一刀只做空旷平坦场景。

不要模拟建筑、树木或复杂岸线，因为本轮只隔离“湖风层/锋面”本身。

最简单方案：
- 大矩形自由空间；
- 地面为唯一实体边界；
- shoreline 只是 x=0 的**物理标签**，不是墙；
- source/UAV/front 均远离计算域外边界，避免边界反射成为结果。

若当前 GADEN preprocessing 必须从 STL 创建 bounding volume，可程序化生成 minimal box/ground STL；不要手工 CAD。

---

## 6. Gas plume 生成

每个 `wind condition × source × release level × plume seed` 都是独立 Simulation。

首轮：
- 4 wind conditions
- 9 sources
- 3 release levels
- K=8 plume seeds

总计 864 个 plume realizations。
先做 1 release × 3 sources × 2 seeds 的 smoke matrix，确认运行时间和输出契约后才扩全量。

源位置和 release 参数全部写 YAML，不从 House 配置继承隐含默认值。

推荐用 GADEN filament model 的原生随机性产生独立 realization；seed 必须显式可控并写进 MANIFEST。

不要通过修改风场或 concentration 后处理人为制造 plume lift。

---

## 7. 固定 UAV 轨迹数据的生成

不需要真实 robot simulator。

GADEN 负责产生 gas/wind 场后，离线在预定义轨迹坐标上 query：
- time
- x,y,z
- U,V,W
- ideal concentration
- hit (统一 threshold)
- environment
- source_id
- release_id
- plume_seed

输出 parquet/csv：
`observations/{env}/{source}/{release}/seed_{k}/z_{height}.parquet`

同一 XY-time 轨迹复用于 10/30/60/100 m，确保“高度”是唯一变化因素之一。

---

## 8. 为什么第一刀不用 OpenFOAM

如果一开始用完整热力 OpenFOAM，有两个风险：
1. CFD 边界、湍流模型、网格、热通量等自由度太多，若 GSL 改善/退化，很难知道是“湖岸机制”还是某个 CFD 设置造成的；
2. 成本高，会再次陷入“先做很大工程、最后源定位没信号”。

所以第一阶段参数化场是**机制消融实验**，不是最终真实性证据。

只有当：
- R0_GO；
- R1_PASS；
- 最好 R2_PASS；
之后再用 OpenFOAM 做高保真复核。

---

## 9. 高保真升级（R1/R2 PASS 后）

第二阶段才建立局地热力 CFD：
- OpenFOAM；
- 近岸空气域 5–10 m 级网格起步；
- 地面/水面不同 surface temperature / heat flux；
- 背景来流由 JGR/WiscoDISCO 约束；
- 必要时 transient PIMPLE；
- 输出 U(x,y,z,t)；
- 通过 ParaView/`paraview_process.py` 导出 GADEN wind CSV；
- 用完全相同的 source/trajectory/scoring protocol 重跑。

最终论文不能只靠参数化风场宣称真实湖岸定量性能；参数化场负责发现机制，OpenFOAM/GADEN 负责高保真确认。

---

## 10. 本轮 Codex 的执行顺序

1. 拉取本分支；
2. 读 README；
3. runtime audit；
4. R0 WiscoDISCO；
5. 只有 R0_GO 才写/build_parametric_wind；
6. N0 smoke test；
7. L1/F1/F2 wind QC；
8. plume smoke matrix；
9. 冻结 configs + hashes；
10. 扩 R1 全矩阵；
11. 只在 R1_PASS 后做 R2；
12. 不做闭环。

任何时候发现 GADEN 当前版本无法无损接入自定义 wind CSV，不要私自改 simulator 内核；记录 BLOCKED，并先实现一个最小 adapter 或改走 gaden_core 官方 preprocessing。
