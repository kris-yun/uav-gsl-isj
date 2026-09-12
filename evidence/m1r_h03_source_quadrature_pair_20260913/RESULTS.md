# H03 seed12 固定源位置修复：NO-GO

实际执行日期：2026-09-13（北京时间）。实验前方案/源码标识沿用 20260912。结论：`NO_GO_NO_WEIGHT_TUNING_NO_HOUSE_SWEEP`。

先上传理论、文献与代码，再做两臂小实验的要求已完成。仅运行既有 H03、算法 seed12、sensor seed12，BASELINE 与 FIXED_SOURCE 各 240 秒模拟预算；没有补跑、扩 House/seed 或按结果调参。两臂均正常到达 `time_budget_timeout`，配置与实际 launch 参数检查通过。

## 冻结及上传身份

- 理论、六篇正式 2026 跨域文献的逐篇核验、检索原始记录、公式、代码、判据首次上传：[26ff5ed](https://github.com/kris-yun/uav-gsl-isj/commit/26ff5ed081bd5852418facbdd25ee7322fea781d)。
- 实际运行冻结：[3564bf8](https://github.com/kris-yun/uav-gsl-isj/commit/3564bf805d4c9f3656a7bf96cf5117b9a604d5d3)。增补已认证本机的源码包传递和评价器无效结果处理；算法、效用公式、阈值未改。VM 无 GitHub 凭据，由本机实际 `git ls-remote` 验证上传，VM 核验 receipt、归档 commit 和 SHA256；认证失败日志也保留。
- 同一新二进制 SHA256：`419e475b1b8ba483010a088fba2e24c0b4b13ddc8704f3506566513a9b412aa0`。旧二进制没有改动。
- [完整原始包](RAW.tar.gz) SHA256：`5a0d6d4f9bcab8e617da54cd11b745287676f02ff1fd128606fec131203a716f`，9,704,596 字节。包含两臂完整日志、原始超预算尾部、实际参数、新旧二进制、冻结源码、上传回执、编译记录和编译器身份。
- [实验前判据](../m1r_crossdomain_20260912/EXPERIMENT_FREEZE.md)、[理论推导](../m1r_crossdomain_20260912/SOURCE_COHERENCE_DERIVATION.md)、[全部文献索引及检索入口](../m1r_crossdomain_20260912/REFERENCE_INDEX.json)。文献结构启发不等于本模块新颖性或因果识别证明。

## 预先固定的效用结果

| 指标 | 原 M1R | 固定源四点修复 | 修复减对照 |
|---|---:|---:|---:|
| 末次有效源 MAP 误差，m | 7.162295 | 8.129408 | +0.967113 |
| 共同区间累计源 MAP 误差，m·s | 1423.737059 | 1442.330608 | +18.593548 |
| 源更新次数 | 4 | 4 | 0 |
| 源更新合计 wall time，s | 2.367478 | 18.284884 | +15.917406 |
| 完整 runner wall time，s | 301.770 | 297.891 | -3.879 |

两项主指标均越小越好，均退化。两臂源估计轨迹分别覆盖 `[2.10601,238.199]` 与 `[2.00292,234.429]` 秒；共同区间为 `[2.10601,234.429]`。按时间戳并集做分段线性积分，不外推，不补齐 0 或 240 秒。评价对象是 `POSTERIOR_MAP` 的 `estimate_x/y` 到真源的平面距离，不是机器人到源距离。独立 NumPy 插值和积分复算与冻结评价器一致。

各自不同长度轨迹的积分为 1450.738911 与 1442.755390 m·s；这些不是预注册共同区间的对照，不能用较短的处理组轨迹积分替代主指标并宣称改善。

[EVALUATION.json](EVALUATION.json) 保存所有有效性检查、原始轨迹哈希与完整数值。此次对照是同二进制的新开发实验；不能拿旧 9 月 8 日或 9 月 12 日不同运行的末次值替换本次对照。

## 实现复算通过，效果门失败

[SCORING_AUDIT.json](SCORING_AUDIT.json) 对真实日志逐项复算：4 次更新、830 个候选更新组，每组 U=4、K=1；完整前缀分别为 32/56/80/104 个事件。读取 224,320 条事件，完成 9,960 次评分比较，最大 `|Δlog L|=1.961154318549189e-15`，低于冻结的数值容差。共享 context、点坐标、1/4 权重及整段前缀后混合均通过。g++ 11.4.0 的 `__LDBL_MANT_DIG__=64` 与复算声明一致。

这确认日志中实际使用的评分算术与公式相符，不验证前向物理准确性、context 最初构造的全部物理假设、后验校准或因果识别。绝对区域四分点的生成由冻结源码及区域合法性检查保证；日志复算没有冒称覆盖未导出的所有几何元数据。

按候选组去重的调用元数据：处理组 legacy 830 + fixed-point 3320 = 4150；对照计数 834。处理组每区域 5 次 forward、对照 1 次，计算预算不匹配。源更新耗时还包含评分/导出等开销；约 7.72 倍的源更新时间不能全部归因于四次额外模拟。完整 runner wall time 含启动、终止和清理，也不能充当纯算法耗时。

## 失败诊断及边界

以下是保留全部更新的事后诊断，不改变主判据：

| 源更新 | 原 M1R 原生后验 MAP 误差，m | 修复组原生后验 MAP 误差，m |
|---|---:|---:|
| 1 | 6.408375 | 5.628363 |
| 2 | 7.182122 | 7.551640 |
| 3 | 7.264109 | 8.129408 |
| 4 | 7.162295 | 9.356200 |

第一次更新暂时靠近真源，后续更新又偏向错误位置。最后一次原生后验中，真源所在格质量约 `2.25e-173`（对照）与 `8.63e-152`（处理）；数值上增大仍几乎为零，不能称源识别成功或后验校准改善。

处理组第 4 次更新在相对 `236.429 s` 开始，wall 耗时 `4.768 s`；最后一条有效源估计轨迹在 `234.429 s`，没有记录这次更新后的估计。因此表中第 4 次原生后验只作诊断，不能替换预先定义的轨迹末次终点，也不将 wall time 直接当作模拟时间。原生后验的诊断值同样没有显示更好的末次定位。

本结果否定的是本次 H03 seed12 完整修复包的开发收益。两臂不能分离固定 U、四点几何、context 改变和额外计算各自的因果效应；不能推论固定未知源的物理语义错误，更不能推论所有 House 都无效。公式更一致并未使当前前向响应和工作证据可靠地支持真源，这是本次能支持的有限结论。

这项修复不作为有效主模块保留：默认开关仍为 false，实验代码和负结果原样存档，不加权重挽救、不扩跑。因果主创新及跨数据集有效性仍未成立。下一步必要证据应落在“可用前向/观测响应能否区分真实源与强假源”，不能再仅靠积分算术或跨域论文类比宣称解决。

## 复现

解压 `RAW.tar.gz` 后，以其中的 `M1R_H03_SEED12_PAIR_20260912_R1` 为 RUN_ROOT，运行冻结提交中的：

```text
python tools/evaluate_m1r_h03_source_quadrature_pair.py --baseline RUN_ROOT/BASELINE/H03_seed12_M1R --fixed-source RUN_ROOT/FIXED_SOURCE/H03_seed12_M1R --output EVALUATION.json
python experiments/ctpi_cstar/verify_m1r_source_quadrature.py --context-dir RUN_ROOT/FIXED_SOURCE/H03_seed12_M1R/context_bank --persistence historical_rolling --native-mantissa-bits 64 --output SCORING_AUDIT.json
```

复算器依赖 mpmath。原生后验诊断从各 `context_bank/source_update_NNNN/source_posterior.csv` 取最大 `source_probability` 行，计算 `(x,y)` 到 `(-0.45,1.90)` 的欧氏距离；时序和耗时来自 `source_update_timing.csv`。完整包内保留源码和运行身份，可逐层追溯，不需要重新生成 bank。
