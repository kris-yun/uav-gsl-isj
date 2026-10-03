# WiscoDISCO Real-Scene Feature Audit

## 决策

`REAL_SCENE_FEATURE_GATE_NOT_ESTABLISHED`：不授权新GADEN或CFD。旧R1/R1A/R1B判定原封不动；当前参数化锋面主创新路线STOP。这里的“未建立”不等于湖岸没有强结构：温度结构及个别联合风/温湿度对比很强，但尚不能识别源附近层与UAV层之间持久、湖岸特有的状态边界。

## 最强的实际观测

42个公开原始文件全部审计：12RAAVEN、24M210、6天lidar wind_profiles。M210严格iMetFlag0下，16个剖面可计算10..100m正温差；其中6个在3个日期出现>=1C（本数值只作描述，不作为事后GSL门槛）。最大7.179C，其他强剖面1.678..4.057C。这些是真实逐层观测中的温度对比，不是同一时刻的垂直场。6个强剖面里仅2个最大温差端点间隔<=300s，另4个相隔360..450s。

| file                              |   max_inversion10_100_C |   inversion_bottom_m |   inversion_top_m |   inversion_pair_elapsed_s |   thermal_transition_proxy_m |
|:----------------------------------|------------------------:|---------------------:|------------------:|---------------------------:|-----------------------------:|
| WiscoDisco21_M210_20210521_F1.txt |                   4.057 |               16.935 |            78.865 |                    270.000 |                       26.011 |
| WiscoDisco21_M210_20210521_F4.txt |                   2.640 |               11.414 |            25.542 |                     90.000 |                       18.478 |
| WiscoDisco21_M210_20210522_F4.txt |                   7.179 |               11.137 |            59.635 |                    360.000 |                       17.101 |
| WiscoDisco21_M210_20210522_F6.txt |                   1.678 |               47.720 |            96.170 |                    360.000 |                       67.376 |
| WiscoDisco21_M210_20210524_F3.txt |                   3.691 |               19.767 |            86.880 |                    450.000 |                       94.190 |
| WiscoDisco21_M210_20210524_F5.txt |                   2.518 |               16.583 |            95.530 |                    360.000 |                      102.607 |

5月22日F4的7.179C来自完整飞行18:27:55/11.14m到18:33:55/59.63m，跨越6分钟且23.06m的温度stdev约3.00C。因此不能排除湖风入侵随时间变化，不能把这个数直接当作稳定层结。原R0冻结18:30..19:00窗口仍为1.271C，没有改旧窗口或判定。thermal_transition_proxy只是最大相邻正温度梯度的位置，层高标准差常有4..10m，且未把位温稳定区、局地逆温或该代理量认定为湖风层/TIBL顶。真层高各行保留空值。

## 风向解耦

RAAVEN原生alt是MSL。12个文件仅2个起飞前/着陆后30s地面参考满足IQR<=2m、差<=5m；二者均在5月24日。另9个文件有稳定着陆参考，全部只作post-anchor敏感性。多数起飞前记录比着陆参考低约140m；这是记录/基准一致性问题，本审计不猜其故障来源。派生高度是相对起落地点的AGL估计，仍不含沿轨迹地形高度修正。两个参考一致也不是测量精度的独立认证。

主分析28个300s窗口，其中13个至少覆盖两个请求高度，有5个>=30deg。主分析无合格10/30m风观测，无任何完整四高度窗口。风向取逐样本方向的圆均值；同时报告风矢量均速和圆集中度R，避免把低风速/宽角分布当作可靠确定风向。

| file                                       | utc                       |   max_requested_direction_diff_deg |   direction_60m_deg |   direction_100m_deg |   actual_height_60m |   actual_height_100m |   mean_height_sampling_time_gap_s |   direction_resultant_R_60m |   direction_resultant_R_100m |
|:-------------------------------------------|:--------------------------|-----------------------------------:|--------------------:|---------------------:|--------------------:|---------------------:|----------------------------------:|----------------------------:|-----------------------------:|
| WiscoDisco_CU-RAAVEN_20210524_141137_B1.nc | 2021-05-24 14:20:00+00:00 |                            102.425 |             136.871 |              239.296 |              58.298 |               98.756 |                            14.505 |                       0.916 |                        0.560 |
| WiscoDisco_CU-RAAVEN_20210524_141137_B1.nc | 2021-05-24 14:35:00+00:00 |                             31.150 |             147.305 |              178.455 |              53.284 |               98.256 |                            46.577 |                       0.992 |                        0.958 |
| WiscoDisco_CU-RAAVEN_20210524_141137_B1.nc | 2021-05-24 15:25:00+00:00 |                             39.798 |             147.795 |              187.593 |              54.909 |              100.770 |                           153.877 |                       0.976 |                        0.973 |
| WiscoDisco_CU-RAAVEN_20210524_141137_B1.nc | 2021-05-24 15:40:00+00:00 |                             45.982 |             154.605 |              200.587 |              61.991 |               99.124 |                             0.033 |                       0.955 |                        0.912 |
| WiscoDisco_CU-RAAVEN_20210524_173749_B1.nc | 2021-05-24 17:40:00+00:00 |                             64.506 |             239.805 |              175.299 |              60.594 |               95.979 |                            31.087 |                       0.813 |                        0.988 |

最大102.425deg窗口在100m带只有8.7s观测、平均矢量风速0.895m/s、R0.560；应低置信解读。其他31..65deg样例亦来自移动、先后或多次穿层取样，300s分组只是任务预算窗口，不能写成维持300s的同时垂直风差。5月22日单着陆基准敏感性可见强差异，但不能与主分析等权堆成独立确认。

额外QA发现，作者wind_direction与由u/v计算的方向中位差为0，但每文件约0.36..1.15%的wind_flag0、速度>=0.5m/s样本差>1deg，少数差很大。产生原因未确认，不假装独立一致性验证全部通过。主分析自始使用u/v计算方向，没有据此回改结果；逐文件诊断在RAAVEN_UV_vs_published_direction_QA.csv，可用direction_qa.py复现。该质量边界也是谨慎解读偶发最大值的原因。

lidar原生低门为42/59/76/93m；10/30m无覆盖。42/59m的速度通常极低，近场质量没有作者给出的可直接应用SNR阈值，因此59m按近60m诊断列保留，主比较仅76/93m。该主比较日中位数1.87..3.12deg，偶有大差；其17m高度间距不能推论20..80m风向差很弱或很强。

| date       |   n_profiles |   n_valid_76_93 |   median_diff76_93 |   p90_diff76_93 |   fraction_ge30 |   max_diff76_93 |
|:-----------|-------------:|----------------:|-------------------:|----------------:|----------------:|----------------:|
| 2021-05-21 |          272 |             272 |              1.874 |           7.064 |           0.000 |          20.575 |
| 2021-05-22 |          279 |             268 |              3.002 |          18.143 |           0.045 |          81.164 |
| 2021-05-23 |          271 |             271 |              1.904 |           9.097 |           0.026 |         136.996 |
| 2021-05-24 |          268 |             254 |              3.115 |          22.056 |           0.043 |         126.301 |
| 2021-05-25 |          280 |             280 |              2.087 |           5.694 |           0.000 |          12.950 |
| 2021-05-26 |          278 |             278 |              2.623 |           7.733 |           0.011 |          66.044 |

原生中位采样间隔309..319s。5月23日有4个连续采样点跨约957s均>=30deg，5月24日有相邻点跨319s；只证明这些离散时刻的差异，不能宣称间隔期间连续存在或满足5..300s准稳态。stare日期/高度契约仍未解决，本轮排除。

## 温湿度标记与低风速积聚

5月24日17:40UTC主分析窗口，实际均高60.59/95.98m，方向差64.51deg，矢量风速8.23/5.21m/s，T为18.84/23.75C，RH为78.92/65.21%，两高度平均采样时间差31.09s。它是本轮值得保留的联合可观测对比，但低高度约12s、高高度约26s风样本、传感器不同变量QC，以及水平位置变化均限制解释。

RH下降可能只是升温造成，不能作为独立湿空气边界证据。本审计另计算比湿q和位温theta，严格遵守各自温湿压质量标志；例如M210强温差剖面的上下比湿变化跨正负，不能把RH单调变化硬解释为统一湖面空气标签。没有独立水面/陆面气团真值标签或留事件外分类验证，不报告“温湿度已能识别湖风气团”。

单柱低风速、M210臭氧值没有同时二维水平矢量图，无法求真实辐合；臭氧也不是受控泄漏源的示踪真值。因此“持久岸线辐合积聚”和“浓度热点不等于源”在这些文件中均不可确认。

## 四候选门审计

| candidate                        | task_time                                                                                 | altitude_magnitude                                             | replication                                                                              | UAV_observable_state                                             | allow_GADEN   |
|:---------------------------------|:------------------------------------------------------------------------------------------|:---------------------------------------------------------------|:-----------------------------------------------------------------------------------------|:-----------------------------------------------------------------|:--------------|
| A_shallow_layer_height           | PARTIAL:90s means;only2of6 strongest pairs<=300s; no fixed-height persistence established | THERMAL_PROXY_PRESENT;true lake-breeze/TIBL top NOT_IDENTIFIED | YES_for_thermal_proxy_not_same_identified_lake_state                                     | T/RH/P observable;air-mass/layer-top classifier NOT_VALIDATED    | False         |
| B_near_source_vs_UAV_direction   | SEQUENTIAL_MOBILE_SAMPLES;not persistent simultaneous vertical shear                      | 60..100m contrast yes;near-source10..30m unknown               | PRIMARY_ONE_DATE;May22 post-anchor sensitivity only                                      | own-height wind yes;near-source wind unavailable to UAV          | False         |
| C_convergence_stagnation_hotspot | NOT_IDENTIFIED                                                                            | CONVERGENCE_NOT_MEASURED                                       | NOT_ESTABLISHED                                                                          | single-point low speed/O3 do not determine convergence or source | False         |
| D_temperature_humidity_marker    | mean height sampling time gap31.09s;no simultaneous independent state labels              | STRONG_JOINT_OBSERVABLE_PROXY                                  | thermal/RH contrasts recur;joint marker-state classification not independently validated | YES_variables;NO_validated_lake_air_land_air_labels              | False         |

A/D是可观测变量层面最值得保留的线索，B有个别大幅度但近源风/跨日期主证据缺失，C目前不具所需观测几何。没有把普通逆温、任意风切变当作湖岸独有，也没有因为变量大就推断GSL失效。

## 文献独立支持及缺口

正式Wisco论文明确报告5月22日海洋层由约250m/21UTC下降到约100m/22UTC；属于一个事件的两个时刻，不是层顶经常落30..80m的频率证据。[ESSD原文](https://essd.copernicus.org/articles/14/2129/2022/)

2025JGR研究支持非定常陆海热力循环及流动历史效应，但不能补齐本次近源风和任务内持续时间。[作者机构记录](https://collaborate.princeton.edu/en/publications/unsteady-land-sea-breeze-circulations-in-the-presence-of-a-synopt/)

FastEddy湖风锋论文是2024年Atmosphere文章，独立Salt Lake事件与5m水平LES提供情景支持，未用于给Wisco填造低空层顶、持久辐合或GSL误差。[NCAR机构记录](https://impacts.ucar.edu/en/publications/application-of-the-ncar-fasteddysupsup-microscale-model-to-a-lake/)

LMOS原始事件数据本轮不在输入集，没有假装完成其数值复核。现有JGR公开结果为统计X-Z切片，不用它构造新气体模拟；原数据审计对维度/时间重构的限制保持。独立论文不能替代本任务中缺测的场量。比湿为派生诊断，Bolton饱和水汽压公式来源[NCAR说明](https://www.ncl.ucar.edu/Document/Functions/Contributed/satvpr_water_bolton.shtml)。

## 输出与研究处置

EVENT_UAV10_100_FEATURE_TABLE.csv给出每个M210事件及最近lidar（<=180s）匹配；10/30m风向、确认逆温层高度及湖风层顶缺测处为空，不插值。平台空间分离显式标注。另有全日期lidar表、RAAVEN300s表、日统计、地面基准QA、质量门统计、热力原始均值/SD、臭氧背景、JSON门审计和PNG。

没有新的机制通过真实数据门。本任务完成后，湖岸保留应用/验证场景，第一篇主创新回到task-sufficient source/plume world model、robust source inference与active sensing的方法问题。这里不设计或运行新算法。若后续要重新论证一个气象特征，所缺的是同步近源与空中风、边界身份/高度及重复任务尺度证据；不会通过继续调这套参数化锋面补门。

开题Word未改动。建议措辞保持：“针对湖岸水陆热力差异可能形成的低空分层、局地辐合及空间非均匀风场，研究其对有限移动观测源判别信息的影响。”不写机制已证明。

复现：解压新目录后python experiments/lakeshore_observability/real_scene_audit/audit.py；默认原数据目录为C:/work/LAKESHORE_GSL_DATA_20261002，可按压缩包README指引指定raw输入目录。pandas/numpy/xarray/scipy/h5py用于读原始数据；matplotlib/tabulate用于报告。全部输入SHA在INPUT_MANIFEST中，旧R1/R1A/R1B清单验证写入DELIVERY_VALIDATION。分析契约在结果计算前记录，但本工作是探索审计，不声称一个预注册的、新数值PASS标准。
