# T02 静态空间源信息诊断

日期：2026-10-01

分支：`research/source-spatial-information-t02-20261001`

前置冻结提交：`04215e6b`（协议、代码、8/8 metadata contract）。

## 机制标签：`STATIC_SIGNAL_PRIMARILY_SPATIAL_PATTERN`

**仅为已批准规则下的机制诊断，不是主创新 PASS，也不是纯 XY 可辨识结论。**

## 表示层汇总

| 表示 | exact p≤0.05 的context | 高于null中位数 | source-stability |
|---|---:|---:|---|
| TOTAL_RATE_1D | 6/8 | 8/8 | True |
| STATIC_SPATIAL_30D | 8/8 | 8/8 | True |
| AMPLITUDE_REMOVED_SPATIAL_30D | 8/8 | 8/8 | True |
| COMPOSITIONAL_SPATIAL_30D | 8/8 | 8/8 | True |
| LOCATION_DESTROYED | 7/8 | 8/8 | True |

## 每个 context 的标准化证据

| Context | House | TOTAL Z | STATIC Z | CENTERED Z | COMPOSITION Z | LOCATION Z | STATIC−LOCATION Z |
|---|---|---:|---:|---:|---:|---:|---:|
| X00 | House01 | 4.42769133 | 4.19950396 | 4.14628450 | 4.23866652 | 4.30921548 | -0.10971152 |
| X01 | House01 | 4.37669004 | 4.39707849 | 4.38872591 | 4.37837862 | 4.36602458 | 0.03105391 |
| X02 | House01 | 3.73807056 | 4.40460649 | 4.41225463 | 4.44942831 | 3.49269619 | 0.91191030 |
| X03 | House01 | 3.77783319 | 4.44155026 | 4.44544049 | 4.37718489 | 3.49566435 | 0.94588592 |
| X04 | House02 | 2.37222308 | 4.46472980 | 4.46929029 | 4.46878474 | 3.46345590 | 1.00127390 |
| X05 | House02 | 1.20415946 | 4.44303945 | 4.46014582 | 4.43061043 | 1.81540847 | 2.62763098 |
| X06 | House02 | 3.90464084 | 3.94031680 | 3.87402753 | 3.76508139 | 3.81347650 | 0.12684031 |
| X07 | House02 | 4.34280673 | 4.36110787 | 4.34572707 | 4.19450294 | 4.17611017 | 0.18499770 |

## 三个问题的直接回答

1. **总量是否足以解释所有 context？未建立。** TOTAL 单独在6/8 context达到 exact p≤0.05，符合整体稳定规则，但 H02 X04/X05 分别 p=0.142857/0.171429；同样两个 context 的 STATIC、CENTERED、COMPOSITION 都是 p=0.028571。总量有明显信息，不能说它没有作用；本轮也没有计算条件互信息来证明严格 sufficiency。

2. **去掉总体水平后是否仍保留源信号？是。** CENTERED 与 COMPOSITION 均在8/8 context达到 p=0.028571；同一评分器及全部70标签分配完成核验。它们仍保留各自的空间形状与部分 histogram 结构，不能声称移除了所有 nuisance。

3. **去掉probe身份是否下降？按冻结Z差规则，是。** 7/8为正，median差 0.54845400，exact one-sided sign-test p=0.03515625。
LOCATION_DESTROYED 仍在7/8 context显著，而且仍符合整体 source-stability 标准。因此 probe identity 有增量，但不是唯一承载；value multiset/histogram 仍然有较强源信息。

“PRIMARILY_SPATIAL_PATTERN”遵循人工事前确认的诊断归类，不是因果贡献比例估计。TOTAL稳定与该标签并不矛盾，批准的层级规则在两种去幅值表示稳定且位置打乱下降时采用该标签。

## 复核与封存

完整两遍输出的16个文件逐字节相同，包含全部exact null、LOCATION draw数组和aggregate-null字节哈希。
独立直接求和核对8×4×70=2,240个Energy值；STATIC全部560个exact-null Energy/Z 与T0.1B原记录完全一致。LOCATION保持64,000个profile multiset，sum/mean/norm不变；预选draw的全部70标签结果与直接距离计算一致。

全零样本数：0/64。预冻结的全零映射规则未触发。
每个context穷举70标签分配；5个表示的跨context联合null采用固定seed的 1,000,000次分层Monte Carlo，不能称穷举70^8。surrogate不增加物理样本数。

## 理论边界与下一步权限

本轮仍是每context仅两个配置源、每源4个独立plume。H01 z=0.4/−0.3 m，H02 z=0.2/−0.1 m；因此该诊断不能分离XY与释放高度的贡献。数据为已使用的discovery，不是新确认集；不宣称全source-map连续定位成立。

本轮没有模拟、PMFS、网络、confirmation/H03或闭环；未改观测规则、source、seed或scorer。未执行12条fixed-z实验，也未新建其运行清单。

后续即使3个source在几何上不共线，也只说明source位移设计矩阵rank=2；不能仅凭几何rank宣称连续逆问题可辨识。另一个fixed-z实验失败也不单独证明必须3D：需要区分高度、观测可达性、信噪比和具体采样合同。本轮不执行这些后续设计。

**完成后 STOP，保留全部历史结果。**
