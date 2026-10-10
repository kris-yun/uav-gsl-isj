# M2 观测与评分合同建议（生成前冻结；本文件未运行新物理仿真）

## 1. 研究问题与可证伪边界

已完整阅读交接思想。当前检验的是同一物理源条件预测在经过实际观测算子后，是否改变真/错候选比较；不是重开旧 pseudoreplication、Blackwell、普通校准停止路线。M1面积统一后仍偏好错误源是先前结果。Bernoulli/Brier或重建测量图只是诊断工具；单纯更温和、更分散或只赢原生PMFS不能成为主创新。源标签事后选定、同一GADEN模型的独立seed、有限参考和仅B4任务均保留适用边界。

## 2. 原始实际观测定义

固定B4 PID `sensor_model=30`、`use_PID_correction_factors=false`、消息 `raw_units=3`。`FakeGasSensor::simulate_pid` 用 **float 累加** 服务返回各气体ppm，无MOX升/降时间常数；`Algorithm::ppmFromGasMsg` 将ppm消息转float，`StopAndMeasureState` 按实际接收顺序float累加后除样本数。最后 `concentration > 0.1`（严格大于）决定命中，不是每个时刻先阈值再多数表决。

已由B4 native log确认50有效块全部为 **1条gas、2条wind**，来自10次停留。因此本次块平均恰好等于那一条float PID；实际窗口时长分布为39×0.50、5×0.40、3×0.60、2×0.70、1×0.51秒。配置0.4秒不能替代真实块成员；有空gas窗口重置。

49块由 `measurement_events → consumer_messages → 原始GasSensor CDR → GasPosition请求/响应 → physical_clock_trace` 唯一匹配；每条float均值与native保存值逐位一致。第41块（零基block40）有两个相同ppm边界成员，无法仅由消费CSV证明哪个在状态更新前加入gas_v；两者原bank均在frame1011，但物理目标时刻不同。保留51行完整分支schedule；**不把一个块计两次**，预先固定早/晚两种50块版本。若新bank两分支事件、地图或源排序不同，应报告敏感性并保留HOLD，不事后选有利分支。

查询高度真实为 `-0.20000000298023224m`，以服务请求XYZ为准。gas consumer CSV的map_z=0是trace占位，不能拿来当传感器高度。源高-0.5m。实际服务物理目标时间322.916615474–534.086066109秒，较块末时钟不同；风一直为10。对新bank按真实保存header时间选 `t_frame <= t_query < t_next` 的原生零阶保持，不按文件名/索引×0.5，不按旧bank帧号索引新bank。

## 3. 对齐观测与测量图

每个新reference/heldout bank均在同一冻结服务物理目标时间与服务XYZ查询原生浓度，经过上述PID float响应、完整原块float平均和0.1阈值得到50个事件。受体轨迹不由新源标签选择。源位置点源双方同类型；GADEN PointSource::Emit精确返回配置位置。本轮不额外做2D点源前向，原M1均匀1×1结果不可与新3D点源作维度因果对比。

测量图重建使用 `MAP_REPLAY_EVENT_COVARIATES.csv` 的50个机器人x/y、块风速与TO方向，锁定实际occupancy、可见性、0.25m网格、prior=.3、kernelSigma/stretch=1.5、localWindow=2、confidenceSigma=1、confidenceWeight=1。每次调用原 `PMFSLib::EstimateHitProbabilities`。风是共同冻结条件，所有候选使用同一wind共变量，不按真假源调整。先以原50块事件重建完整测量图、logOdds/omega/confidence为锚点，再允许新source-conditioned事件建图。若锚点数值不一致，不把新map称为“与实测同过程”。

reference构造只用每候选rep0/rep1；rep2/rep3是独立物理realization盲评，从其事件生成独立任务。两个reference图可平均成预测belief-map，和观测belief-map比较其网格均值/置信加权平方差，或报告原 `1-D*confidence*|p_observed-p_predicted|` 格乘积的log和；后者仅是相同空间的相似度诊断，不是447个独立传感器或合格联合似然。记录每个格来自哪些原始块，勿求逆50/447维样本协方差。

## 4. 原始事件评分预注册

每候选两reference。第j块有k次命中，**固定Jeffreys Beta(0.5,0.5)** 平滑 `p_j=(k+0.5)/(2+1)`，只可能为1/6、1/2、5/6。无结果依赖epsilon、先验调整、温度或附加seed。

Bernoulli log评分 `L=sum_j[y_j log(p_j)+(1-y_j)log(1-p_j)]`（越大越好）；Brier `B=(1/50)sum_j(y_j-p_j)^2`（越小越好）。均报告原50块、10次停留的分解和每个独立heldout完整50维实现，不把50块/447格当独立实验。两指标不同意时如实报告；不从多个统计量挑出最有利的一个。不将log和称为joint likelihood，不归一化成已校准源后验。

`score_source_blind.py`只接受匿名candidate→reference event和opaque task→event，不接受坐标、真假角色、heldout生成者标签。输出先SHA冻结；另一个步骤再读身份密钥判断源排序。冻结后才评判原B4及四个heldout任务。root需进一步隔离角色表/盲评文件和日志暴露，匿名不等于分析人员完全未见空间角色。

## 5. 未对齐物理hit定义及不可比留空

可实现的控制：同一3Dbank、同受体高度、同冻结时刻，定义 `physical_hit = I[原生SampleConcentrations(x,y,z)>0 ppm]`。这是理想非零浓度到达，受原模拟有限支持/截断算子影响，不是PID超过0.1的块检出。沿冻结受体轨迹的预测可独立报告；若资源允许，可在全部447合法格中心按50时刻查询，平均得到时间占用频率h_i，再报告和累计测量图直接比较的原相似度。时间样本与reference realization是不同层级，勿把100个相关时刻当100独立释放。

不能把这一3D非零浓度hit叫做原生2D羽丝中心占格频率；若full-grid查询或观测算子不资格化，未对齐full-map结果留空/HOLD。2D/3D × PID/命中率四格表不强填。连续浓度是新增信息增强条件，不能将其改善归于同信息比较。当前8份仅用于有限原型入口，仍缺至少一个未参与规则选择任务、不同几何/风、实际传感器及独立物理模型验证。

## 6. 本子任务实际完成

只读文档、源码、原CDR/服务/时钟链核验和schedule生成，未运行GADEN、前向、ROS、导航或新算法。输出状态：49块完整链PASS，block40成员身份HOLD并已预注册双分支；3D参考执行与主创新判决由root新运行证据决定。本文件是建议合同，实际总合同以生成前root冻结文件为准，不覆盖已冻结合同或历史结果。
