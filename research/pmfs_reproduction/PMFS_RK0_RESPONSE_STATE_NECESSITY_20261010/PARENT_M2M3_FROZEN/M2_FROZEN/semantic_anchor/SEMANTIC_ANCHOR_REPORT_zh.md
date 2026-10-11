# 原生单格概率语义锚点：源码支持该反例

判决：`SOURCE_LEVEL_COUNTEREXAMPLE_SUPPORTED_NOT_B4_ROOT_CAUSE`。实际完成隔离 C++ 函数运行；没有新增候选传播、GADEN、ROS、导航或后验更新。原生调用与公式给出的候选排序在全部指定 n 和全部命中数 k 下相符。

## 科学问题与明确假设

反例假设同一受体上每次观测是独立 Bernoulli 检出，真实频率为 0.6，错误候选频率为 0.9，并假设两候选频率准确已知。这是单格合成语义检验，不是 B4 真实观测的统计假设；B4 的相关停留事件不能被本反例宣布独立。候选频率在 `sourceProbFromMaps` 的实际 vector<float> 输入中为 0.6f、0.9f。

固定先验 0.3、逆观测 hit=0.6f/miss=0.1f、D=0.4；真实调用 `HitProbability::setProbability(0.3)` 初始化。零空间偏移、单个合法自由格；kernelSigma=1.5、kernelStretchConstant=1.5，confidenceSigmaSpatial=1、confidenceMeasurementWeight=1。零偏移且单格时没有额外空间传播单元。maxUpdatesPerStop=200 只是构造设置；被调用的 stateless 更新函数不检查该停止规则，本测试不是实际停留流程。

原生 forward hitMap 的来源在源码中是“每时步至少一个丝团占据该格”的计数，除以 timesteps；它不是 PID 的 ppm 浓度，也不自动等于真实阈值化传感器事件频率。本反例通过明确假设消除了这层差异，检验后续更新/比较在理想频率输入下的语义。

## 原生计算与实数公式

实数公式为 L_n=logit(0.3)+k[logit(0.6f)-logit(0.3)]+(n-k)[logit(0.1f)-logit(0.3)]。原生的 `applyFalloffLogOdds` 先将 lerp/clamp 结果存为 float；`prob/(1-prob)` 以 float 运算，`std::log(float)` 返回 float，然后提升至 double。不能只把 0.6f/0.1f 常量取成 binary32 后就称为完整 C++ 浮点模拟。

原生 `EstimateHitProbabilities` 累积 double logOdds；其 `probability()` 实际为 `1-1/(1+exp(L))`。0.6f/0.1f 在 [0.001,0.999] 之内，本实验没有逆观测裁剪；logOdds 不裁剪，概率和 confidence 会在有限浮点精度下到达 0/1。

零偏移时 omega 每步增加 1/sqrt(2π)，confidence=1-exp(-omega)。原生单格评分为 1-D·confidence·|p-q|。记录了真实有限 confidence 的评分，也另行调用原生单格函数记录 confidence=1 的条件评分；共同的正 confidence 保持候选排序。初始 confidence=0 时两评分均为1。

## 实际结果

表中例子均为 k=0.6n，采用预定 hit-first 顺序；native/binomial 错误概率通过所有 k=0..n 的原生最终评分和精确 Binomial(n,3/5) 权重求和，未抽取 Monte Carlo seed。

| n | k | 原生 p | 原生 confidence | 真候选 score | 错候选 score | 原生排序错误概率 | 原始 Bernoulli 排序错误概率 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 3 | 0.552589221 | 0.863947087 | 0.98361583 | 0.879942196 | 0.33696 | 0.33696 |
| 10 | 6 | 0.78066971 | 0.981489605 | 0.929069832 | 0.953151434 | 0.633103258 | 0.167289754 |
| 20 | 12 | 0.9672782 | 0.999657365 | 0.853139066 | 0.973097931 | 0.595598725 | 0.0509519532 |
| 50 | 30 | 0.999940949 | 0.999999998 | 0.84002363 | 0.960023611 | 0.843831669 | 0.00568768579 |
| 100 | 60 | 0.999999999 | 1 | 0.84000001 | 0.959999991 | 0.936210823 | 0.00010718028 |
| 200 | 120 | 1 | 1 | 0.84000001 | 0.95999999 | 0.986859855 | 1.2148966e-07 |

n=200 的 120 次命中例子中，原生 p/confidence 已为 1，原生评分偏好错误候选。按检出频率解释，p_map 没有收敛到 0.6，而偏向1；原始 Bernoulli 事件评分仍能区分 0.6 与0.9。实数公式临界检出频率为 0.518666003483，真实频率0.6位于其上方。

这支持“静态 binary filter 后验值不能未经观测过程对齐就自动当作检出频率”的合成反例。它不否定静态二元隐变量问题中的正确 binary filtering；不能直接升级为 B4 根因或算法创新。

## 浮点与顺序核验

主顺序逐步 logOdds 相对交接实数公式最大差 1.12450034635e-05；概率最大差 1.90522467725e-06。显式考虑 float 比值与 float log 后，logOdds 最大差仅 9.66338120634e-13。

对每个 n,k 又执行 miss-first 顺序，最终 logOdds 最大差 1.3073986338e-12，评分最大差 1.55431223448e-15，所有782条最终 count/order 记录中候选排序无分叉。没有枚举所有中间排列；原生 binomial 值严格指 canonical hit-first 的 count 判定加精确权重，不能宣称所有排列的逐位结果完全相同。交接公式错误概率与本次精确权重复算最大差低于1e-12。

## 源码、执行与证据血统

新编译的冻结 PMFSLib.cpp SHA256：`064af4f492a248b7ac41d9874dbe1f9447921b2957071602b065bac366faa292`。测量更新、PropagateProbabilities、applyFalloffLogOdds 函数与 VM recovery checkout 对应函数完全一致；完整文件存在 EstimateWind 的 fail-closed 日志/检查差异，未调用它。Simulations 链接对象来自 M1 冻结 native capture 版本，完整原有函数体作为前缀保持冻结；只额外提供 Gaussian 状态访问方法，本测试没有用它们。Math helper 所调用五函数与冻结源码一致。逐函数 SHA 与完整源码 SHA 见 SOURCE_FUNCTION_PARITY.json / vm_evidence/SOURCE_HASHES.json。

编译26.274秒，峰值 RSS 1,185,017,856字节；纯函数运行0.399秒，exit=0，stderr为空。EstimateHitProbabilities 实际调用 106820 次，sourceProbFromMaps 调用 215204 次。这些是单格枚举的函数调用次数，不是新物理测量或候选传播调用。首次准备因只读 SDK 文件路径错误在源码 hash 读取阶段退出，未编译/运行；日志保留，第二个独立目录纠正路径后完成。

native_steps.csv 保存主 hit-first 每步原生状态；native_counts.csv 保存两种顺序全部782条终态；native_formula_steps.csv 保存每步公式配对；SEMANTIC_ANCHOR_RESULT.json 与 semantic_summary.csv 为概要。verify_semantic_anchor.py 默认只读核验，重算单格评分、精确 binomial 权重、顺序一致性和 SHA。

没有显示网格细分测试、没有实际 B4 数据上的相同观测算子比较、没有新参考 bank、本实验不形成新的源后验或定位成绩。其结论仅是交接 B 项要求的“源码支持该反例”。
