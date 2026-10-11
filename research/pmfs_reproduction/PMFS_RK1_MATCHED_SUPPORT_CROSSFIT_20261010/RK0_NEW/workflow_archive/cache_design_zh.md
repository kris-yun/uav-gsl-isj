# RK0：旧气体库的响应状态压缩缓存设计

本文件只给出准备方案；尚未调用 `build_cache`，未生成新气体、二维候选预测或VM任务。`cache_native.py` 只有可导入接口，没有自动执行入口，实际batch由主进程在冻结合同后启动并监控。

## 主要选择

使用**跨所有参考源/realization、所有planned-time曝光的共享stationary kernel**。不使用按该受体配对时刻、源编号或bank单独训练的kernel作为U/S主结果。后者将被检验的时间/源条件重新塞入U/S，不能说明仅二维中心格或粗z/σ状态是否足以解释响应。

参考仅为 `C7_0,C7_1,K2_0,K2_1`。每bank有50个branch0事件对应49个唯一原始帧。计算缓存时每帧只算一次；拟合时按50个planned-time的帧曝光multiplicity加权，重复帧的numerator和denominator同时乘2。它是**相关采样曝光权重，不是额外独立气体样本**。第51个membership替代仅做原生数值/分支审计，不增加拟合权重。

51个member实际上只有**10个唯一XYZ位置**，与10个stop逐一对应，8bank坐标完全一致。计算按stop_id=0…9组织10列，保留51→10显式alias和每bank实际帧/物理时间；不能丢掉50块事件或把10个stop说成50个独立位姿。

## 共享核的严格定义

每个参考粒子记录保留完整`(x,y,z,σ_cm)`，`g`是原origin/.25m格架上的XY状态，包含导航障碍及原frame外所有cell，不裁447/1530 mask。对每个固定实际受体`r`，原生贡献为`φ(record,r)`：包括3σ严格截断、3D LOS、头文件中的摩尔常数和cm→m换算。

以参考计划曝光权重w定义：

\[
h_U(g,r)=\frac{\sum_{record:g(record)=g} w(record)\,\phi(record,r)}{\sum_{record:g(record)=g}w(record)}.
\]

**所有粒子记录进入分母，包括LOS阻断、超出3σ或数值为0的记录。** 不能用positive-contribution CSV的行数代替分母。S的定义相同，仅把g扩为`(XYcell,z/σ_class)`，最多4类；class阈值、未覆盖bin回退和最少覆盖标准由主冻结合同规定，helper不做选择。U/S输出原生物理ppm均值，不做center-hit-frequency→ppm人为换算。

主分析可用当前帧的oracle N(g)或N(g,class)计算\(\hat c(r)=\sum_gN(g)h(g,r)\)，F保留原始粒子响应。这里当前帧计数本来就由真实模拟粒子获得，应明确属于oracle响应压缩诊断，不能被称为可部署源定位方法。

未覆盖状态不能默默设置h=0：必须按照合同采用明确的上一级回退或HOLD门，并报告covered/uncovered粒子质量；否则S更细但更稀疏的表现会被覆盖不足混淆。helper只保留完整粒子和zero响应，不拟合h、不选回退、不读留出源角色作决策。

## 一个坐标细节

原PMFS `Grid2DMetadata::coordinatesToIndices` 是float→integer截断，负索引区间向0截断；几何无限格架通常用floor。这两者对原frame外negative cell不同。若RK0选择几何floor保证规则格宽，应在合同中明确为状态划分定义，不能写成与原生PMFS负索引实现完全一致。原生GADEN环境LOS的坐标查表仍必须保留截断实现，不能顺带改成floor。

## 已有正贡献表的作用与缺项

`M3/operator_contrast/FILAMENT_CONTRIBUTION_DECOMPOSITION.csv`保存的是实际受体×对应时刻的正贡献，共9,339行，其中4个reference有3,218行；29,827是旧408次查询的**3σ eligible对数**，不是正贡献条数。

这张表适合锚点复用，但没有交叉“所有参考帧×所有受体位置”的响应，也没有全部零分母。无法直接从它构造共享h。缓存需要每个reference唯一frame的全部粒子对10个受体位置的贡献；cross-frame共享并非新仿真，只是重新读取旧粒子状态。

## 计算规模、可实施算法

4个参考49帧共224,296个唯一frame粒子records。乘10个唯一位置为**2,242,960**响应pair；按51member盲重复才是11,439,096。曝光权重只影响后续统计，不增加kernel计算。8bank全部已有状态共457,736条unique-frame粒子records。

1. 原文件SHA通过后，逐帧解压GADEN3.0 ZLIB记录，保留原粒子serial顺序。
2. 3σ距离截断向量化为float32，严格按`0+x²+y²+z²`累计顺序计算，使用严格`distanceSqr < limit²`。
3. 仅对eligible pairs调用已有的原生语义LOS和单粒子`math.exp`。LOS保留endpoint free检查、float32位置及`floor_float(distance/cell)`步数，原先steps≤1不进行中途检查。
4. 单粒子贡献保存float32；每pose的F总量按原粒子序float32逐项累加，不使用NumPy pairwise reduction替代原生顺序。
5. 每帧输出`contributions(N,10)`，零pair显式为0。原`filaments(N,4)`同时输出，供后来完整分母/分类重建；按稀疏正贡献加速与否不改变这个完整记录定义。

旧独立Python读取408个实际受体查询仅约4.48秒；全部2.243m crosspairs约为原始粒子距离扫描的5倍，加上更大的LOS集合，保守预计几十秒到数分钟。10分钟硬上限由主进程执行，超限STOP而不是改阈值或改核。

最朴素全部reference贡献float32矩阵也仅约8.97MB；原粒子数据约3.59MB。逐帧处理的暂存矩阵不足0.1MB，3D occupancy约0.33MB（解析文本另占几MB），压缩NPZ/ledger总体远低于1GiB。可以直接保留dense zeros避免稀疏分母出错；没有必要为省几十MB引入高维核密度或协方差拟合。

## 原生数值锚点与停止门

首先计算C7_0第一个实际query所用的frame611与10pose，仅以该实际receiver的C++ total作为第一门；其原生ppm为0.9068903923034668。通过`ATOL=3e-7, RTOL=5e-6`（原M2已经冻结的跨平台容差）后才计算其余reference缓存。

每个frame完成后，所有与之对应的原生实际member total都要回查：4bank×51member=204个锚点。记录最大绝对差、ULP差和每query差，不把平均一致当成通过。旧正贡献表可额外对照paired positive记录，但不决定任何新参数，也不代替完整分母。

源码支持依据：`M2/independent_raw_query_verify/source/Simulation.cpp`的`CalculateConcentration`、`CheckLineOfSight`、`CalculateConcentrationSingleFilament`；数学实现复用已经独立核验的`verify_raw_receiver_queries.py`。任何float/LOS/单位锚点不通过先STOP，不在结果后切换算子。

## helper接口与产物

`build_cache(m2:Path, out:Path, contract:dict)`只负责reference响应，不负责U/S/F拟合或评分。`out`必须新建或为空；parent监督10分钟/1GiB。

每帧文件：`out/<bank>/iteration_<frame>.npz`。

- `filaments`：`(N,4)`float32。
- `contributions`：`(N,10)`float32，含全部零。
- `native_totals`：`(10,)`float32、原粒子累加顺序。
- `planned_time_exposure_weight`、native header常数、eligible/LOS/positive计数。

return包括`frames[{bank,frame,cache_relative_path,snapshot_SHA256,cache_SHA256,exposure_weight,filament_records,native_query_checks}]`、`poses`按stop0…9、`pose_aliases`和资源/数值元数据。另存：`CONTRIBUTION_CACHE_LEDGER.csv`、`FIT_EXPOSURE_MULTIPLICITY.csv`、`CACHE_NATIVE_CPP_TOTAL_ANCHORS.csv`、`PRE_CACHE_INPUT_SHA256.json`、`FIRST_NATIVE_ANCHOR.json`、`CONTRIBUTION_CACHE_RESULT.json`。

批次开始前仅做过读取metadata和CSV的规模统计、代码AST语法检查。未运行`build_cache`、未使用VM，也没有训练共享核或查看新增U/S/F分数。
