# R1B 湖风锋空间失配确认报告

最终判定：`R1B_HOLD_MISMATCH_NOT_FRONT_LOCKED`。六项门槛全部通过的场景 0/6；不计front-lock时通过的场景 4/6；全部uniform负对照是否>=90%：True。

保持原`R1_HOLD_WEAK_OR_UNSTABLE`及`R1A_RESIDENCE_SUFFICIENT_STOP_UPLIFT_ATTRIBUTION`。未运行R1.1、R2、PMFS、闭环、主动感知或高保真CFD。未恢复垂直抬升主线，未改源网格、阈值或锋面位置来过门。判定未通过时停止后续lake-front机制主线；HOLD也不能作为PASS继续。

## 旧1944数据的探索复核

| scene   | arm                   |   threshold_factor |   height |   prefix_s |    top1 |   mean_error_m |   signed_x_bias |
|:--------|:----------------------|-------------------:|---------:|-----------:|--------:|---------------:|----------------:|
| F1      | horizontal_diagnostic |            1.00000 |       10 |        300 | 1.00000 |        0.00000 |         0.00000 |
| F1      | oracle                |            1.00000 |       10 |        300 | 1.00000 |        0.00000 |         0.00000 |
| F1      | profile               |            1.00000 |       10 |        300 | 0.81944 |        5.41667 |         5.41667 |
| F1      | uniform               |            1.00000 |       10 |        300 | 0.82407 |        5.27778 |         5.27778 |
| F2      | horizontal_diagnostic |            1.00000 |       10 |        300 | 1.00000 |        0.00000 |         0.00000 |
| F2      | oracle                |            1.00000 |       10 |        300 | 1.00000 |        0.00000 |         0.00000 |
| F2      | profile               |            1.00000 |       10 |        300 | 0.69907 |        9.02778 |         9.02778 |
| F2      | uniform               |            1.00000 |       10 |        300 | 0.70833 |        8.75000 |         8.75000 |

该复核仅为exploratory，不回改旧判定。单次Beta先验的合并模板复现用户给出的F1/C06及F2/C08数值。实现中先对三档释放率的21个训练样本合并，再计算(1+hits)/23；三档各贡献七个seed、等权。先按每档加先验再平均会引入三份先验并产生小差别，第一版输入草案与最终输入冻结均保留，澄清发生在没有任何新32001+气体输出前。

## 冻结与执行

完整阅读协议commit f4d322a82ea21c1097108d71cb2cdc37e4233c76。六个全锋面、六个uniform、六个profile场；固定9源x20/50/80、y-20/0/20、z1；release5/10/20、独立新seeds32001..32008，总3888个realization、4,665,600行。原二次评分和新矩阵均使用相同的release-unknown estimator。均匀场匹配原生z10查询所在网格的300s轨迹平均u；profile在每个原生高度匹配同一轨迹平均u，没有使用气体结果来匹配风。

主终点固定z10、300s、阈值.001ppm。30/60/120s前缀、30m、.5/2x阈值均作为次要/敏感性保存，没有选择它们来替代主gate。每次测试从所有9候选和三档release模板移除配对seed。Brier取300个时间点平均，保留候选分数、rank、margin、分数相同候选的等权预测。误差为候选欧氏误差的期望；错误率=1-fractional Top1，bias为预测x减真x的期望。固定路径源映射为template指纹分类，不是闭环定位或跨天气泛化。

## 主结果

| scene    | arm     |   oracle_top1 |   baseline_top1 |   penalty_pp |   mean_error_m |   error_fraction |   mean_x_bias |   direction_fraction |   consistent_seed_count | all_six   |
|:---------|:--------|--------------:|----------------:|-------------:|---------------:|-----------------:|--------------:|---------------------:|------------------------:|:----------|
| XF90_F1  | uniform |        0.9861 |          0.6204 |      36.5741 |        11.3889 |           0.3796 |       11.3889 |               1.0000 |                       8 | False     |
| XF90_F1  | profile |        0.9861 |          0.6204 |      36.5741 |        11.3889 |           0.3796 |       11.3889 |               1.0000 |                       8 | False     |
| XF90_F2  | uniform |        0.9907 |          0.4352 |      55.5556 |        16.9444 |           0.5648 |       16.9444 |               1.0000 |                       8 | False     |
| XF90_F2  | profile |        0.9907 |          0.4352 |      55.5556 |        16.9444 |           0.5648 |       16.9444 |               1.0000 |                       8 | False     |
| XF120_F1 | uniform |        1.0000 |          0.7546 |      24.5370 |         7.3611 |           0.2454 |        7.3611 |               1.0000 |                       8 | False     |
| XF120_F1 | profile |        1.0000 |          0.7546 |      24.5370 |         7.3611 |           0.2454 |        7.3611 |               1.0000 |                       8 | False     |
| XF120_F2 | uniform |        1.0000 |          0.6991 |      30.0926 |         9.0278 |           0.3009 |        9.0278 |               1.0000 |                       8 | False     |
| XF120_F2 | profile |        1.0000 |          0.6991 |      30.0926 |         9.0278 |           0.3009 |        9.0278 |               1.0000 |                       8 | False     |
| XF150_F1 | uniform |        1.0000 |          1.0000 |       0.0000 |         0.0000 |           0.0000 |        0.0000 |               0.0000 |                       0 | False     |
| XF150_F1 | profile |        1.0000 |          1.0000 |       0.0000 |         0.0000 |           0.0000 |        0.0000 |               0.0000 |                       0 | False     |
| XF150_F2 | uniform |        1.0000 |          0.9907 |       0.9259 |         0.2778 |           0.0093 |        0.2778 |               1.0000 |                       1 | False     |
| XF150_F2 | profile |        1.0000 |          0.9907 |       0.9259 |         0.2778 |           0.0093 |        0.2778 |               1.0000 |                       1 | False     |

方向比例的分母是全部错误，包括只在y错而x不变的错误。>=6/8seed要求同seed oracle-baseline Top1差>0且平均x-bias与总体错误主方向相同。每个场景必须由同一个baseline arm满足全部六项，不能从两个arm中拼凑门槛。negativecontrol为每场景uniform truth+同uniformmodel的release-unknown评分。

## 错误区域是否随front移动

- F1 / uniform: most-affected x=[20.0, 20.0, 'undefined (no errors)']; error-weighted centroids=[23.65853658536585, 20.0, None]; locked=False
- F1 / profile: most-affected x=[20.0, 20.0, 'undefined (no errors)']; error-weighted centroids=[23.65853658536585, 20.0, None]; locked=False
- F2 / uniform: most-affected x=[20.0, 20.0, 20.0]; error-weighted centroids=[32.295081967213115, 20.0, 20.000000000000004]; locked=False
- F2 / profile: most-affected x=[20.0, 20.0, 20.0]; error-weighted centroids=[32.295081967213115, 20.0, 20.000000000000004]; locked=False

F1/XF150主终点没有任何错误，因此不存在受影响源区域。原始JSON的most_affected_source_x=50仅是所有错误率同为0时的并列中心计算值，不能解释为错误区域移动到了50m；上表明确标为undefined。F2三位置的最易误判源均为x20，错误率随front移向150m显著减少，并未发生要求的区域移动。

由于协议未给出移动的数值公式，在新气体生成前冻结保守的离散源网格实现：按y/release/seed平均错误率最高的source-x定义受影响区域；并列最高用x均值。对同一强度和同一arm，90->120->150三场景均有错误、区域非递减且首尾至少移动30m才通过。错误率加权centroid同时报告但不替换gate。三锋面均位于有限源网格的下游，这一实验几何限制明确保留；若区域总固定在同一源位置，就无法排除固定源位置/传播距离解释。不扩密、不移动源网格补救。

## 边界与下一步

误差方向一致或单场景模型失配本身不足以证明front-relative机制。只有>=4/6场景满足全部要求并通过负对照才允许PASS。若FAIL/HOLD，本任务在确认门处结束；不会继续CFD或主动感知。非methane气体robustness只在PASS后执行，本次状态见FINAL_DECISION及交付说明。当前全部结果是298K固定native methane参数下的机制测试，不是实测湖岸定位误差，也不外推VOC。真实热力湖岸机制最终需要独立热力CFD/LES复核。

## 复现与核验

新生成/评分脚本在experiments/lakeshore_observability/r1b；config与PRE_GAS_SHA256SUMS锁定分析输入。原R1及R1A共4974条MANIFEST均逐一复核无改动。运行前后runtime binary SHA一致，新seed原生再跑导出CSV字节一致，18风场nativequery随机点与实际pathquery通过。ZIP带完整新观察、log、候选分数、次要终点、JSON判定、两张PNG及旧exploratory评分所用1944观察和关键依赖。MANIFEST.csv和SHA256SUMS列出每个有效成员；ZIP自身SHA在旁边sha256文件。

已有文件离线重评分：python experiments/lakeshore_observability/r1b/score.py；旧探索重评分：同脚本加posthoc。需numpy/pandas（报告需要matplotlib/tabulate）。原生重新生成还需相同VM已有adapter/library及SSH访问；ZIP不包含虚拟机或GADEN动态库。不要在原冻结交付目录随意重跑prepare并覆盖输入，复现请解压到新目录。
