# M0 R0 资源估计与预算门

当前实际 M0 simulation calls=0。下面为工程预算，不是实测 wall time；静态 NumPy field algebra 不计为 GADEN run。不得以预算表暗示执行获准。

## 科学运行与停止顺序

| 阶段 | 固定数量 | 启动条件 |
|---|---:|---|
| U0 baseline | 2 sources × 4 seeds = 8 | 后续明确执行指令；native asset、hash、物理/RMSE、磁盘/RAM门通过 |
| 4 wrong winds | 4 × 2 × 4 = 32 | 全 8 baseline 支撑、RNG、A relevance、observation、sampling parity及预算门通过 |
| 总计 | **40** | 两 inference 与 BMA 复用同一预测库，无额外 rollout |

最多 40 条 scientific simulations，没有 626 candidate-grid sweep、OpenFOAM、NN、额外 gas/source/seed/context。Baseline 失败 -> HOLD，保留输出，停止；没有自动扩域 revision、额外 8 条 baseline 或参数 retry。基础设施失败尝试也单列保留，重试需要后续 review，不能静默突破 run budget。

## 输入、输出和内存

- Domain 3,686,400 cells。原生 wind 每 arm `8 + 3*4*3,686,400 = 44,236,808` bytes；5 个约 221 MB。Native 每 run 保存一次 wind 的保守重复上限约 1.77 GB；需实际确认是否 duplicate。
- Outlet/free occupancy 格式以 native parser readback 为准；即使文本每 cell 20 bytes，约 74 MB。仅一套 occupancy，不能复制旧 House 作为新场景。
- 10 filaments/s × 140 s ≈1,400 active filaments 上限，1,400 ticks。Native save 的严格 `>` 与 float clock 约产生 230–281 snapshots，不把估计当实际记录数。每个 filament position+sigma 16 bytes，40×281×1,400×16≈252 MB aggregate raw payload 加 metadata（按所有 snapshot 都有终末 filament 数的保守估计）；压缩与实际 active count会减少这一项。日志/manifest 另预留。
- ROI footprint 为 51×40×32×4 = 261,120 bytes/run；40 条约 10.5 MB。Whole-domain secondary column 上界 51×120×80×4 ≈1.96 MB/run，40 条约 78.4 MB。Route 数据只有 40×51 点。
- Footprint 必须使用支持半径内的 filament scatter，保留 native 3σ cutoff/LOS/原生函数并逐 frame parity；不可逐 sample 全扫所有 filaments 来构建稠密场。沿 z streaming 求 column，不存 full-3D time-volume bank。若保存 40×51×3,686,400 float32 则约 30.1 GB，违背本合同。
- Serial RAM 工程估计 0.5–1 GiB；设置峰值 RSS 上限 **2 GiB**。原生 wind 临时复制、disturbance map、occupancy 和解压 buffers应实测，不宣称已满足。预计算浓度 false，GPU不用，单进程/单 OMP thread。

Outputs+inputs 硬预算 **5 GiB**，任何 future launch 前 free disk≥12 GiB、available RAM≥3 GiB。本轮 read-only VM 快照 free disk=29,267,152,896 bytes、available RAM=5,865,455,616 bytes，仅反映当时状态，执行前重查。禁止清理历史 bank 来达预算。

## 时间与未来可执行门

以每 run 20–180 s 作为工程排期 allowance（不是 measured GADEN performance），40 条约 13–120 min；再给 native extraction、hash 和 analysis 预留约 30 min。壁钟总上限 **3 h**，此 allowance 有不确定性，特别是 decoder、scatter/LOS和磁盘写入。

首 8 baseline 需同时记录 simulation 和 extraction wall time、RSS、output bytes。继续 32 条之前：

1. 用线性 q95 的实测 per-run **simulation+extraction** 时间，按 `3 × q95 × 32 + 已用时间 + 30 min` 投影；应 ≤3 h。
2. 用 `32 × baseline_max_output_bytes + 已生成 bytes + 共享输入 bytes` 投影；应 ≤5 GiB。
3. 所有实际 peak RSS≤2 GiB、free disk/RAM 仍满足；无并行/隐藏其他 campaign 占用。

任何预算门失败 -> `M0_RESOURCE_HOLD`。不能临时减 frame、改步长/浓度阈值、缩 domain/时间窗、删除 raw 或增 threads 救预算；先交 review 再制定新冻结版。发生 disk/RAM不足时中止新增 runs，保留已有完整和失败叶目录。

Native constructor会删除其 `saveDataDirectory`。未来唯一允许的 output root 为 `/home/zyc/ros2_ws/m0_clean_support_r0_20261007`，实际 launcher 必须验证 resolved parent、run ID allowlist 和 **leaf此前不存在**，因此不能重用目录。R0 本轮没有创建该 VM目录，没有启动 simulator，也没有改变现有 ROS runtime。

预算通过仍不能证明科学资格。Baseline/干预的 support、CRN、obs 和 matched-error门分别强制；所有未来 run 原始输出、实际 argv/runtime flags、source/runtime/input/output SHA256及异常记录应保存。当前 design freeze只证明已给出可审查、受预算约束的实验规范。
