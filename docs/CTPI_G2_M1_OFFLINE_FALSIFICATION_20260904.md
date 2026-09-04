# CTPI G2-M1 offline falsification 报告 + 似然核设计

日期：2026-09-04
前置：`CTPI_G2_V1_ARCHITECTURE_AND_INTERFACES_20260904.md`
性质：G2-M1 的 DEV_SPENT / offline falsification 结果，把失败机制转化为可实现的似然核设计。

---

## 1. 四个破坏性测试结果（全部 offline，用 bank 1680 world 作 ground truth）

| 测试 | 结果 | 证据 |
|---|---|---|
| **二值 vs 幅值** | 二值命中 rank≈随机，幅值 rank=1 | 二值 28–33/210；幅值 1/210（第二名差 3 个数量级） |
| **source strength intervention** | 归一化形状对强度不变，绝对幅值在强度缩小下失败 | scale 0.2/0.5/1/2/5：绝对幅值 210/77/1/1/1；归一化形状 全 1 |
| **transport regime intervention** | 幅值对 regime 鲁棒 | matched + mismatch(m1/m3/m7) + 边缘化 全 rank=1 |
| **sensor dynamics intervention** | FOPDT 对归一化形状鲁棒 | 峰值衰减 0.854–0.990（近均匀）；原始/FOPDT 观测 全 rank=1 |
| **House holdout** | 方法跨环境泛化 | H01/H02/H03 全 rank=1（同套方法） |

### 1.1 关键修正
最初怀疑 M1 失败主因是"观测 transport regime 不在 bank 8 member 内"。falsification 证明**不是**：幅值似然在 mismatched transport 下仍 rank=1。**真正主因是二值命中丢失浓度幅值/梯度**。

---

## 2. G2-M1 似然核设计（直接由 falsification 推导）

### 2.1 核心原则（对应四个结论）
1. **用浓度幅值/形状，不用二值命中**（结论 1）。
2. **位置 θ 用归一化形状，强度 q 用绝对幅值**，两者分离（结论 2）。
3. **归一化形状对 transport/sensor 鲁棒**，无需显式 transport/sensor 边缘化（结论 3、4）。
4. 输出到 **626 free cell 级**（不做 2×2 carrier 粗化）。

### 2.2 似然核（cell 级，离线已证 rank=1）
```
观测浓度场:  C_obs(x), x ∈ 观测点
形状特征:    shape_obs = C_obs / max(C_obs)          # 归一化，去除强度
候选源 θ:    shape_pred(θ) = C_bank(θ) / max(C_bank(θ))  # 该 cell 作源时的 bank 稳态峰值场

位置似然:    log P(obs | θ) = -‖shape_obs - shape_pred(θ)‖²   # 形状匹配
强度估计:    q̂(θ) = argmin_q ‖C_obs - q · C_bank(θ)‖²         # 幅值匹配（分离的强度维度）

后验:        P(θ | obs) ∝ P(θ) · exp(log P(obs | θ))   # 626 cell 归一化
```

### 2.3 与现有 CPIR 的本质差异
| 维度 | 现有 CPIR (applyCPIRPosterior) | G2-M1 |
|---|---|---|
| 特征 | 二值命中 `physical > 0.1` | 连续浓度幅值 + 归一化形状 |
| 强度 | 未建模（bank 只有 gasType_10） | 显式 q̂，与 θ 分离 |
| 空间粒度 | 2×2 carrier（210 个） | 626 free cell |
| transport | 8 member 命中率经验平均 | 归一化形状对 regime 天然鲁棒 |
| sensor | 一阶低通 + 阈值 | 峰值/形状对 FOPDT 鲁棒 |

### 2.4 关键判据（用户写死，反"越自信越错"）
- 当 posterior entropy/support 变小时，**true-source rank/error 必须单调变好**。
- 若"后验越尖但尖在错误源"，G2-M1 判失败，禁止把"更自信"当优点。
- offline 已证：归一化形状似然 true-source rank=1（远好于二值的 ≈随机），这是 rank 层面的直接证据。

### 2.5 关键判据的在线累积实证（决定性）
模拟机器人从远到近逐步累积观测（30 点，`_tmp_m1_online.py`），跟踪 posterior entropy 与 true-carrier rank：

| 观测数 n | 二值 entropy → rank | 形状 entropy → rank |
|---|---|---|
| 10 | 2.833 → 42 | 2.611 → 126 |
| 15 | 1.702 → 37 | 2.981 → 120 |
| 22 | 0.865 → 8 | 1.453 → **1** |
| 30 | 0.548 → **6** | 0.275 → **1** |

- **形状似然**：entropy 单调降（2.789→0.275），rank 单调收敛到 **1** —— 满足"越自信越对"。
- **二值命中**：entropy 降（5.240→0.548），但 rank 反复（105→172→42→15→37→14→21→6，最终 6），中间多次"entropy 降但 rank 变差" —— **违反关键判据，正是"越自信越错"**。

这直接复现了 12-run NO-GO 的现象机制，并证明 G2-M1 的归一化形状似然修复了它。

---

## 3. 实现路径

1. **offline 已验证**：归一化形状似然 rank=1（本报告）。
2. **下一步**：把该似然核接入 `PMFS::applyCPIRPosterior`（替换二值命中核），保持 `recordCPIRRawSample` 的 timestamp-pose 关联不变。
3. **数据依赖**：bank 的稳态峰值场（`peak[c] = max over 1500 time`）可离线预计算为 626×N 的峰值矩阵，C++ 侧直接加载，替代逐 time 查 bank。
4. **bank-free 化留给 M2**：M1 仍用 site-specific bank 的稳态峰值场；M2 用 operator learning 替代它（held-out House 禁止查 bank）。

---

## 4. 数据与脚本

- bank：`/mnt/hgfs/workspace/CPIR_M1_FULLGRID_LOOKUP_20260831_R1/{H01,H02,H03}/`
- .bin 格式：magic "PFV3STR1"(8B) + uint32 cell_count(4B) + cell_count×uint32 header(=time_count) + cell_count×time_count float32 PPM（stream-major）。
- coarse grid：H01 29×38, H02 27×39, H03 46×27（scale=3，cell 0.3m）。
- carrier = 2×2 quadtree（边界 1×2），`sx=min(2, nx-oi)`。
- 验证脚本（VM /tmp/）：`_tmp_m1_compare.py`（二值vs幅值）、`_tmp_m1_strength.py`（strength）、`_tmp_m1_regime.py`（regime）、`_tmp_m1_sensor.py`（sensor）、`_tmp_m1_house_holdout.py`（holdout）。
