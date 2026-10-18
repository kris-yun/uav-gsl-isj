# PMFS-O24 从冻结提交出发的独立源响应研究原型（2026-10-18）

**基底**：`kris-yun/uav-gsl-isj` commit `631145657461c41840f6844f118de57d1e747ea4`（`PMFS-O24-PORT-GMRF`）。

**当前资格**：`A_PRIME_INTERFACE_IMPLEMENTED / O24_OFFLINE_PARITY_PASS / PHYSICAL_A_PRIME_BLOCKED / B_NOT_VALIDATED`。

## 本包做到了什么

1. `o24_parity.py`：对原 14.5 MB ZIP（包括内嵌旧四回合）的 **5,335 张二维候选图 / 34 次源更新**完成原生 O24 评分和源概率复算，最大后验绝对误差约 `1.21e-15`。验证置信度 `α=0` 的格对分数严格无贡献，投影后在数值容差内保留原生输出。**不声称提高定位精度，也不把源级 2D hit map 改叫物理 ppm。**
2. `response_contract.py`：实现未来普通 A′ 所需的物理源—受体矩阵的类型、跨候选源时钟/窗口一致性门、外部风信息权限门、物理浓度单位门、带非负源强 profile 的普通高斯似然和面积先验回填。**没有建立真实 3D 候选源浓度响应列，也没有接入 ROS。**
3. `PMFSResponseOperatorPrototype.hpp`：不依赖 ROS 的 C++17 评分接口，含 O24 原生 hit 评分与未来“已匹配 ppm 响应”的普通 profile。`test_native_adapter.cpp` 编译通过，只对小型合成输入验证。
4. `identifiability.py`：计算已知源强的白化源对距离与未知非负源强下的正射线夹角。当候选列仅为常数倍时，未知源强的场景可能不可定位，即使已知源强的距离显著。
5. `mechanism_probe.py` 与 `pod_precheck.py`：分别做极小反例和 O24 *已保存二维 hit map* 的普通 SVD / 中心化 POD / 置信度加权中心化 POD 对照。**全部是机制/压缩诊断，不是 NEMO、3D 传播或闭环性能实验。**

## 运行复现（不启动 ROS）

```bash
python3 -m pip install numpy
python3 test_contract.py
c++ -std=c++17 -O2 -Wall -Wextra test_native_adapter.cpp -o test_native_adapter
./test_native_adapter
python3 o24_parity.py --zip "/path/to/PMFS_O24_最终冻结_A2隔离补跑与五回合完整证据_V2_20261018.zip" --with-history --out O24_PARITY.json
OPENBLAS_NUM_THREADS=1 python3 pod_precheck.py --zip "/path/to/PMFS_O24_最终冻结_A2隔离补跑与五回合完整证据_V2_20261018.zip" --out POD_PRECHECK.json
```

本交付不复制用户的 ROS ELF、录制 CDR 或气体物理帧。本包在不修改冻结基线的情况下可执行。结果文件是保存数值的离线审计，不是新增 5,335 次前向传播。

## 必要数据门（A′）

当前 O24 包里有原生浓度窗口读数和多个候选源的**二维二值占格图**；**没有已验证的“同一物理世界/风场/传感器时空窗口下，为至少两个候选源独立生成的、单位源强连续 ppm 响应列 K”**。原始 GADEN 物理世界帧只在记录中指向外部位置，压缩包未附赠成对不同源的反事实世界。

所以代码拒绝把 `native_candidate_maps.f32` 输入 `response_contract.py` 的 ppm 模式。必须先找已有 House/S2X 等资产，不得根据真源保存帧私下合成竞争源反事实。缺失时 `A_PRIME_PHYSICS_BLOCKED`，停止真正的 B/NEMO 训练与定位收益主张。

## 最关键的否定性结论

先前“矩阵 `[[100,100],[2,0]]` 的一维 SVD 丢失 99% 源差”**不证明有独立于经典 PCA 的新算法必要性**：常见的**中心化 POD**在这个二源反例上可精确保留源差。真实 O24 的二维压缩中，按现有 `α` 做加权中心化 POD 已经显著优于未加权 POD 的同库 logscore 拟合。这都是普通方法收益，不能写作 2026 NEMO 或跨学科创新已成立。

真正 B 必须在合法 ppm 响应银行上同物理输入、同训练预算，超过完整 A′、经典中心化/白化 POD、共模/源强剖面普通方法以及原始 NEMO，才有可能宣称机制增益。详细见 `DECISION_zh.md`。

## 隔离保证

- 不修改 O24/冻结 commit / main 的任何已有文件。
- 没有启动 Codex、ROS/GADEN/OpenFOAM、机器人目标、训练任务或云服务。
- 历史 `O24G_A2_R02` 永久保留为 **通信域 HOLD**，即使其数值文件也能重放，绝不升级为合格定位样本。
- 原始 O24-A2-ISO-R03：0.568900 m，97.3838 s。属于官方公开源码移植的单次合格补跑，仍非论文30次复现或新算法收益。