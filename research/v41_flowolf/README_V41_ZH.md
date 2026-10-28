# V41 斑马鱼体心风嗅三模块可执行代码｜先读

**代码状态**：V41_ALGORITHM_PROTOTYPE_EXECUTABLE；`S2_NATIVE_NEW_ACTION_NOT_RUN`；`S2_CAUSAL_FORWARD_PARITY_UNQUALIFIED`；`BIO_INCREMENTAL_GAIN_UNPROVEN`。

这是从 V35–V40 理论衍生的 **可执行算法候选**，而非经过原生 S2 气团场证明有效的 SCI 二区成果。以前 V40 的 `V40_TESTS.py` 只验证命题；V41 首次将 **M1 动作提案 + M2 统一概率后验 + M3 信息/可靠性门控 + 合法动作执行** 接成单一在线控制循环，并提供和普通方法共享模型的合成闭环。此处的仿生来源是 Lunsford et al., PNAS 2026（体心位置×局地流向编码）；并不声称它提出了本无人机方程。

## 1. 项目结构

- `v41_flowolf/encoder.py`：M1，因果有效感受位置（仪器延迟/记忆的**代理足迹**）、感受器身份、局地相对风和真实接触值，计算过去相对动作 Gram 的欠采样方向，生成源无关物理状态。基础计算 O(N)×短时常数窗口；无真源、无未来风。气团释放年龄不由这个足迹推断。
- `v41_flowolf/control.py`：M1 动作候选（平移、横风展开、身份偏置与互补方向重构）+ M3 有限候选评分（经典共同 q/源高的 Fisher 投影、成对强度轮廓差、普通 EIG）+ 安全和不确定前向时的可靠性退避。
- `v41_flowolf/inference.py`：M2 **共享普通底座**，对候选 `s,q` 统一使用因果高斯仪器似然、边缘化得到二维源概率（无体心特征二次计证）。q 为离散正强度网格，不能等价称为任意 q(t) 已解决。多个释放模式/风误差/非高斯噪声尚未实现。
- `v41_flowolf/physics.py`：普通风条件高斯羽流（合成软件测试专用）、完整时滞/一阶传感器预测接口。
- `v41_flowolf/legacy_forward.py` 和 `legacy_v34/`：**复用原 V34 普通** `CompiledLocalPuffs` 源条件模拟，统一供 BIO 和普通基线，不是 S2 原生真值或已经修复的 E3/B4 前向。
- `v41_flowolf/native.py` + `public_geometry.py`：S2 原始 `AgentSession` 接口适配；控制器仅拿历史观测与**公共**障碍/DEM；完整原始气团数据和 3Agent 同步并未在此运行。
- `demo_v41.py`：同数据/同控制源域的普通 EIG、投影 E-opt、普通覆盖、BIO 和删除模块的合成联动测试。
- `run_v41_s2.py`：在 Codex 本机找到完整原始包后使用的入口。默认严格可靠性门，不把未经独立校准的传播模型评分当作可信定位证据。
- `tests/test_v41.py`：源码单元/接口/安全/闭环测试。

## 2. 立即运行

Python 3.10+，依赖 `numpy scipy pytest`。

```bash
python -m pytest tests/test_v41.py -q
python demo_v41.py --steps 20 --seed 9001 --out V41_SYNTHETIC_20.json
```

可以在真实安装的原始 S2 目录运行**原生接口 smoke**：

```bash
python run_v41_s2.py \
  --root /PATH/FSR_S2_120m_CH4_DATA_ONLY_V1_20261026 \
  --world W001 --sources-npy /PATH/frozen_PUBLIC_source_support.npy \
  --start-json /PATH/frozen_PUBLIC_3uav_starts.json \
  --mode bio --seconds 5 --seed 9001 --out /PATH/S2_W001_V41_smoke.json
```

这里 `/PATH` 是必须由 Codex 查明、并检查源支持是否来自公开部署约束的**实际路径**，不是我编造的源文件。不得把 `labels/sources.csv` / future puff / 真实风场带入控制端。真实物理完整气团必须与数据包 SHA256 `210771b27161b74d73c5e4d8c620a85f1652f402c80b81a68c12d41a03fceffe` 核对（在 ZIP 层由 Codex 验证）。

`run_v41_s2.py` 的默认 `strict_model_gate=True`：**即使实际气体接触已得到，没有独立源条件前向误差界时，也只执行物理覆盖/安全补测**。它可以测 E0 接触，但绝不能报 E2 定位增益。可传 `--exploratory-uncertified` 打开模型依赖动作，仅供调试，必须标记 UNQUALIFIED；没有预先注册的独立误差资格时，该模式任何正结果都不能投稿为最终有效收益。S2 五世界仅三水平源，单一冻结诊断风，不得当成跨天气统计。

## 3. 与普通方法的公平性

- 都调用相同 `joint_posterior`、`ForwardModel.response`、源域/先验、共同随机数和动作/距离合法性函数；没有用真源标签选择动作。
- `ordinary_eig` / `ordinary_projected` 是**最多8个普通候选**的预算型启发式，不能叫“最优完整 EIG”。`ordinary_eig_full` / `ordinary_projected_full` 是相同动作库全候选版本（计算更贵），要另报真实 CPU 及前向调用次数。
- BIO 的新组件是“身份-气流-气味+历史相对运动缺口”**候选提案**；Fisher、Schur、经典 q 轮廓差和贝叶斯更新是普通统计运算。强模型修复属于各方法共享底座，不能归功于 BIO。
- 消融：`bio_noidentity`,`bio_noflow`,`bio_nogap`。每种模式都要在同一世界噪声 seed/初始位置/仪器资格、相同 source support、CPU/前向预算下分组报告；不可只选新策略胜利的 seed。

## 4. 重要理论/工程边界

1. M3 当前仅对**单一连续源模型**的共同未知 q 和局部源高进行 Fisher 投影。V40 理论中“任意释放历史 q(t)、风误差、传播模式集、全局误差证书”的完全求解，**尚未实现**；只能报告该局部启发式和可信度状态，不能称已经全模型鲁棒。
2. 合成气体模型与推断模型一致，不能作为真实间歇羽流泛化证据。合成均值高斯和 S2 原生 full-tail Gaussian+LOS 不等价。
3. 身份保留/位置组合的动作有可运行实现，但并不证明超越普通完整 EIG。若原生 BIO 与普通方法同观测、同路径或同源定位，就如实判 HOLD。
4. `NativeGeometry` 只读公共地形静态资格，不是实飞旋翼下洗、通讯、安全认证。多 `AgentSession` 顺序 step 是否在原生读数完全同步，必须 Codex 显式对照单机标准接口；未通过之前标 `NATIVE_MULTI_SESSION_PARITY_UNKNOWN`。
5. 理论上最容易遗漏的是 E3/B4 中**真实源附近预测响应近零**：该问题未被 V41 合成统计或编码解决。普通前向模型须在 S2 原生真实正检出窗独立通过覆盖审计，才允许执行 E2 定位判断。

## 5. Codex 接受和提交步骤

1. 先在这个 GitHub 分支真实运行所有 Python 测试、记录 python/numpy/scipy 版本与 26项测试；必要时先修**代码 bug**，不可根据真实标签优化方法参数。
2. 在本地完整 S2 包执行 `--seconds 5` 的原生 API 契约对齐和 3机同步核查，保留逐 0.1s 源格式的日志；有真实问题先修 API，不改仿真参数/传感器模型。B0/BIO 均用相同读取器。
3. 只要 E0 真实回放可用，继续 60s 五世界原生接触实验；模型前向不合格也仍可完成 E0。
4. 源条件生成核、释放历史及风模型合格后再执行 E1 与 E2（V40 Codex 合同）；比较 full-EIG/普通 E-opt，记录前向耗时和全源域后验，报告正常组 harm。
5. 所有 PASS/FAIL/UNKNOWN 结果附精确原始数据 SHA、执行命令、commit、独立评价程序及全轨迹；绝不报告伪造的真实定位误差。

版本：2026-10-28 V41 开发，代码 **已本地完成合成闭环与单元测试**；无原始 S2 完整气团，**原生 E0/E1/E2 未执行**。