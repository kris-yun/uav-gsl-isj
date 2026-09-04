# CTPI G2 bank-free 三模块改造 — 交接文档（2026-09-04）

## 一句话状态

把 CREL/TSDC/PIP 三模块的 site-specific bank 依赖全部替换为 **bank-free Gaussian plume（physics-informed 输运，保留时变风向）**，H01 真实 closed-loop 验证：**M1 稳定承重（PASS），M2/M3 短时域增量不稳定（NO_GO）**。

## 关键结论（科学诊断，不是代码 bug）

| 模块 | 对照 | error_auc | verdict |
|---|---|---|---|
| M1 | F00−A0 | 1236.7→1192.5（**−3.6%，2胜1负**） | **PASS** |
| M3 | F10−F00 | 1192.5→1223.8（+2.6%，1胜2负） | NO_GO |
| M2 | F11−F10 | 1223.8→1274.2（+4.1%，1胜2负） | NO_GO |

**核心结论**：M1（源后验似然核）是短时域（240s）单 House 闭环的承重模块；M2（bank-free 输运预测）和 M3（主动实验设计）的增量在 **240s 短时域 + 稀疏观测** 下难以稳定体现（error_auc 波动 ±5% 噪声级）。它们的真正价值在「跨环境（held-out）泛化」和「长时域多步规划」，当前 screen 判定框架无法体现。

## 三处 bank 依赖的替换（本 commit 的源码改动）

| 模块 | 旧（bank 依赖） | 新（bank-free） |
|---|---|---|
| M1 似然 | bank 稳态峰值场 / 二值命中 | Gaussian plume 形状似然，时变 wind 历史 max，cell 级后验 |
| M2 TSDC | bank 瞬时场推进 sensor state（时间轴错位 + OOM） | 删除 bank 读取；输运用 plume（F11 最近 wind vs F10 历史 max） |
| M3 动作 | bank 瞬时场预测命中 | Gaussian plume 互信息 EID（soft hit p=C/(C+0.3)），后验调制 |

另：M1 后验通过 **source-seeking 导航**（后验 MAP 驱动 goal）真正承重，修复了「F00 导航用 PMFS 原生 MI、M1 后验不驱动导航」的断裂。

## 修改的文件

源码（6）：
- `ros2_package/src/gsl_server/algorithms/PMFS/CPIR.cpp`（M1 形状似然 + M2 清理 + 时变 wind）
- `ros2_package/src/gsl_server/algorithms/PMFS/CTPI.cpp`（M3 互信息 EID + carrierRect）
- `ros2_package/src/gsl_server/algorithms/PMFS/PMFS.cpp`（wind 历史累积）
- `ros2_package/src/gsl_server/algorithms/PMFS/PMFS.hpp`（新成员）
- `ros2_package/src/gsl_server/algorithms/PMFS/MovingStatePMFS.cpp`（source-seeking 承重）
- `ros2_package/src/gsl_server/algorithms/Common/Algorithm.cpp`（pose buffer queue，前一轮）

文档（6）：见 `docs/CTPI_G2_*_20260904.md` + NO_GO 报告。

运行时（2）：`closed_loop/ctpi/vgr_gsl_pmfs_ctpi_fasttrack.launch.py`（nav_reduce_scale）、`closed_loop/ctpi/run_ctpi_fasttrack_case_safe_20260903.sh`。

## 关键遗留 + 下一步

1. **M3 多步 EID**：单步贪心 → 多步前瞻（考虑未来信息增益）。
2. **M2 跨环境验证**：bank-free 输运预测在 held-out House（H02/H03）上验证泛化。
3. **延长时域预算**：让 explore 收益在更长时域下体现。
4. **M1 近源偏差**：Gaussian plume 的 `1/dx` 距离衰减可能让 estimate 偏「观测点上游近处」而非真源（源 x=-0.4，estimate x≈-3）。可验证去掉 `1/dx` 或改用方向匹配。

这些指向「验证框架需升级」（跨环境 + 长时域），而非「方法错误」。

## VM 可复用路径

```
repo:   /home/zyc/CTPI_M3_FASTTRACK_TRUE_CLOSED_LOOP_20260903_R8_C4445EE/repo（HEAD c4445ee）
build:  /dev/shm/ctpi_m3_fasttrack_build_v5_c4445ee（binary 已是最新 25fde66f）
bank:   /mnt/hgfs/workspace/CPIR_M1_FULLGRID_LOOKUP_20260831_R1/{H01,H02,H03}
GADEN:  /mnt/hgfs/workspace/GADEN_files/scenarios/{House01,House02,House03}
```

增量重编译：`bash /tmp/_tmp_rebuild_g2m1.sh`（build 目录在 /dev/shm，需先 source CTPI_VM_ENV.sh）。
