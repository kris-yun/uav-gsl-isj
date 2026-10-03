# MSR0 气象信息充分性审计与第一门实验

正式结论：**MSR0_STOP_2D_MET_SUFFICIENT**。含义仅为：在当前合格S2/S2X的固定路径与现有风况中，没有证据表明二维风压缩是源定位的主要信息瓶颈。**不是已经证明二维风普遍充分，更不是三维风无物理价值。**第一门无正信号，不生成新forward，不执行源坐标第二门，不执行Wisco桥接，不设计Task-Sufficient Meteorological Transport State。

## 1. 数据覆盖与资格

保留四个主case：H01/s0=cfg00、H01/s1=cfg02、H02/s0=cfg04、H02/s1=cfg06；s0/s1是冻结气象/气体context别名，绝非source标签。每个主case内都有两个source、每source四个独立gas realization。另审计已有cfg01/03/05/07慢风，共 **8 contexts×2 sources×4 realizations=64**。没有新生成任何plume，只使用现有资格PASS、记录时钟与逐文件原始字节证明。runlist的历史FROZEN_NOT_RUN字面状态被实际QC/归档执行证据替代，不能据该字面状态否定数据。

真实连续source坐标、generator二进制、geometry、wind bundle、gas type/释放参数、seed、1803条native记录、record-index时间映射和固定路径均核验。此次读取并验证 **19968** 个native payload，合计 **3,169,668,402** 字节；每项SHA256与既有完整归档证据匹配。64条完整查询的原生风/时钟与风专用查询 **最大差0**。每个House复用T0按最大连通自由区域几何构造的路径，100–700s、2s间隔、301点；低室内网格高度约0.231/0.249m，**不是实际UAV飞行**。同House下所有context/source使用完全同一路径/钟。

一个重要限制：同一House的两个主case也改变gas type（13↔10），所以主case之间的气体差异不能作为单独气象干预。合法比较必须固定gas、release、noise、growth、temperature、pressure、generator、geometry、sourceXYZ和时钟。跨House几何/路径也不同，禁止对原始gas trace作直接风场归因。

28个context组合中，16个跨House排除、8个同House但gas/参数不同排除，只有 **4个匹配fast/slow气象配对**，按两个source展开8个合法响应比较。排除依据与所有可计算风距离保存在MSR0_CONTEXT_DISTANCES.csv，不根据gas结果挑pair。

现有合格source bank每context仅两个已配置坐标×4realizations。历史87、1584、630候选等PMFS/旧GADEN bank并非当前generator/clock/common-route读出，五份旧metadata现查SHA均与既有审计一致；D0B x/label prefix阵列和D0-lite单context在线轨迹亦不提供当前任意source网格bank。MSR0_FORWARD_BANK_COVERAGE.csv明确区分两源小bank与任意网格覆盖。**不能用两源分类代替连续未知源反演。**

## 2. 源盲表示与二维基线

实际PMFS代码的GADEN分支可获取整个自由二维网格在anemometer高度的u/v，不能弱化成全航程均风。本轮没有本固定路径的原始PMFS运行记录，用原生0.1m自由层完整UV重建同类信息，并附路线UV，是对二维表示有利的较细网格控制；未运行或改动PMFS算法/GMRF。

- Phi0：完整水平slice UV+路线UV。
- Phi1：保留Phi0，只加路线w。
- Phi2：加固定z±0.2m的三分量梯度、最短风向差/高度与风速差/高度。
- Phi3：加固定x/y±0.2m梯度及7点局地空间方向/速度变化。
- Phi_ORACLE：再加固定[-0.4,0,0.4]m的3×3×3局地风patch。它是更丰富的信息参照，固定距离检索成绩不是真正的Bayes性能上界。

风专用C++程序只接受occupancy、wind字节、固定探针，不打开任何gas/source manifest。路线和邻域由几何冻结，障碍/越界位置设缺失mask，对同House contexts用共同合法mask，不以零风伪造有效观测。表示距离按预冻结等块relative RMS计算，无gas结果定标。11个wind_iteration按native timeline连接查询钟，但CFD-state的物理时间语义未证明，**没有称其为turbulence/TKE**。

2D相近阈值0.10（对称relative RMS）是预冻结的工程气象邻域定义，附0.05/0.20敏感性；不是绝对gas效应/JSD物理门。气体门始终使用同context随机变化的q95，不使用旧0.01门。

## 3. 自然噪声底与混叠第一门

gas距离是同301时空点上log1p(ppm)差的RMS。每context/source四条独立realization形成6个within配对，输出median/q90/q95；两context相同source合并12个within配对定义本比较q95。Between使用4×4条完整trace配对的中位距离，另检查四次平均trace差超过同噪声底，以避免仅随机差异造成正信号。这些配对共享realization，**不能把6/16配对或301观察点当独立样本数**；每context/source仅4个独立实现，q95尾部本身不精确。

| context_i     | context_j     | source_id            |   d_Phi0 |   D_between_median |   D_within_pooled_q95 |   alias_ratio | gas_exceeds_floor   | collision_Phi0   |
|:--------------|:--------------|:---------------------|---------:|-------------------:|----------------------:|--------------:|:--------------------|:-----------------|
| House01_cfg00 | House01_cfg01 | House01_configured_1 |    0.895 |              0.375 |                 0.227 |         1.653 | True                | False            |
| House01_cfg00 | House01_cfg01 | House01_configured_2 |    0.895 |              0.172 |                 0.161 |         1.066 | False               | False            |
| House01_cfg02 | House01_cfg03 | House01_configured_1 |    1.035 |              0.177 |                 0.193 |         0.920 | False               | False            |
| House01_cfg02 | House01_cfg03 | House01_configured_2 |    1.035 |              0.105 |                 0.135 |         0.777 | False               | False            |
| House02_cfg04 | House02_cfg05 | House02_configured_1 |    0.757 |              0.183 |                 0.250 |         0.731 | False               | False            |
| House02_cfg04 | House02_cfg05 | House02_configured_2 |    0.757 |              0.168 |                 0.208 |         0.807 | False               | False            |
| House02_cfg06 | House02_cfg07 | House02_configured_1 |    0.831 |              0.257 |                 0.512 |         0.503 | False               | False            |
| House02_cfg06 | House02_cfg07 | House02_configured_2 |    0.831 |              0.325 |                 0.570 |         0.570 | False               | False            |

4个合法pair的Phi0距离约 **0.757、0.831、0.895、1.035**，都远高于0.05/0.10/0.20三档近邻定义。三个阈值均 **0个2D collision**。H01 cfg00↔01的source1气体差异比within q95约 **1.653倍**，但其二维风距离0.895，二维已经明显区分这两种风况，故不是二维压缩信息遗漏。该pair source2的between中位ratio约1.066，但ensemble平均trace差未超过噪声底，也不满足冻结的稳健气体条件。

因此没有“二维几乎相同、但相同源响应明显不同”的合法pair，也就无须进入“3D解除已有collision”的源反演第二门。不能把不同gas或不同House的碰撞补进来救gate。

## 4. 表示诊断与可辨识性

| Phi        |   Spearman_context_pair_rho |   nearest_neighbor_transport_mismatch |   alias_collision_count_source_pairs |   alias_resolved_vs_Phi0 |
|:-----------|----------------------------:|--------------------------------------:|-------------------------------------:|-------------------------:|
| Phi0       |                      -0.400 |                                 0.220 |                                    0 |                        0 |
| Phi1       |                      -0.200 |                                 0.220 |                                    0 |                        0 |
| Phi2       |                      -0.200 |                                 0.220 |                                    0 |                        0 |
| Phi3       |                      -0.400 |                                 0.220 |                                    0 |                        0 |
| Phi_ORACLE |                      -0.400 |                                 0.220 |                                    0 |                        0 |

Spearman只基于4个context级干预，gas/House背景异质、样本极小，仅描述，不能从这些负相关宣称二维/三维风对输运无因果价值。所有Phi最近合法邻居gas mismatch都约0.220，因为每context只剩 **1个兼容的非自身替代context**，不是证明各Phi检索效果相同。context retrieval accuracy输出null/NOT_IDENTIFIABLE；不报告这种候选退化条件下的虚假100%。False-neighbor按“气象相近而超噪声底”定义为0，不代表所有非相近的最近邻gas差异也为0。无Phi0 collision可解除，各Phi解除数均0。

这里最主要的覆盖限制是：同条件可比的现有风况只有fast/slow，二维改变也很大；尚无正交的“二维近同而三维不同”气象对照。因此STOP必须保持当前实验范围的含义，不能把缺少这种对照写成普遍充分性定理。

## 5. 源坐标、量化下界与跳过阶段

MSR0_LOCALIZATION.csv为40个主case×Phi×source显式NOT_EXECUTED行，meter error/MAP/posterior/rank留空，**没有用Top1或两源分类替代定位**。LOCO/leave-one-house-out、paired context bootstrap、15%meter-error GO均未执行，因为第一门无正信号。也没有借用旧T0的神经分类结果。

MSR0_QUANTIZATION_FLOOR.csv单独给出几何自由slice的XY候选中心距离；这是几何诊断，不代表这些候选已有合法source-height/forward覆盖。两源bank自带真实配置坐标，量化差0是设计事实，不能当模型定位效果。各House代表source如下：

| context       | source_id            |   geometry_slice_xy_quantization_floor_m |   geometry_slice_xyz_distance_m |   existing_two_source_bank_floor_m |
|:--------------|:---------------------|-----------------------------------------:|--------------------------------:|-----------------------------------:|
| House01_cfg00 | House01_configured_1 |                                    0.020 |                           0.170 |                              0.000 |
| House01_cfg00 | House01_configured_2 |                                    0.030 |                           0.532 |                              0.000 |
| House02_cfg04 | House02_configured_1 |                                    0.043 |                           0.065 |                              0.000 |
| House02_cfg04 | House02_configured_2 |                                    0.043 |                           0.352 |                              0.000 |

MSR0_WISCO_BRIDGE.csv标为未执行。本轮禁止在没有有效仿真低维表示时重新选择Wisco事件或用弱42/59m支持结果；没有使用真实气体source truth或Wisco定位误差。由于仿真信息价值第一门尚无正信号，本轮是STOP，而非SIM_SIGNAL_NO_LAKESHORE_BRIDGE的HOLD。

## 6. 完成边界与复现

R1/R1A/R1B/R3/TIBL-R0/FRONT-LAG的旧STOP/HOLD全部不变。不寻找第五个湖岸微机制、不做新CFD/GADEN、不补268k bank、不训练网络、无闭环/world model。本轮新输出位于独立C:/work/MSR0_METEOROLOGICAL_STATE_SUFFICIENCY_20261003及独立代码/evidence目录。

本轮核心可交付结论是：**现有合格数据中，不能发现被冻结判据支持的二维气象混叠；停止把三维气象压缩当作已经得到证据支持的第一篇核心瓶颈。**不存在source-coordinate改善结果，也不能声称已证实二维风普遍足够。

分析复现只需ZIP中evidence数据：python experiments/msr0_meteorological_state_sufficiency/score.py，然后package.py。NumPy/pandas/scipy/tabulate即可，无神经框架。原生重新查询另需原始C:/GADEN_OCB_R2_ARCHIVE与已审计VM库，prepare.py默认只读这些旧inputs，--resume可从已完成字节审计继续。ZIP含查询风、气体、route/probe、source truth合同、原始metadata/逐文件SHA、代码；它是**可独立重算本轮统计的分析证据包**，没有重复塞入3.17GB native payload，原件仍在既有独立C盘archive。

实现修复只涉及临时存储、完整性与打包路径，见IMPLEMENTATION_HISTORY.json；数据/参数/距离/阈值/门均未改。原生积分/采样来自原有native PlaybackSimulation，64条风钟逐点比对差0；没有自造替代气体模型。

分支：`research/lakeshore-observability-r0-r2-20261003`。开始时commit：`f5c52a8c0cc28e9169838e7802d3a8f77600655f`。最终commit及全包文件SHA在ZIP的MANIFEST.json。
输入清单SHA256：`09158b3fcba41a1b17d5e834889766e1870efd34e9c4b4b92fc71febdd6c332d`。
冻结配置SHA256：`f67ce7404742f39f8ffb4b15b6d1872e88e65d00be7c0bae84b20a2d170b35af`。
