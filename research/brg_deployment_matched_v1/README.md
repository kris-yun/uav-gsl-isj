# BRG 下一步：部署匹配训练与一次闭环数据回灌

状态：新开发版本建议；不是旧 P1 重判，不是新科学 PASS；不自动授权远端执行。

## 决定

Plus 提出的先核查冻结权重、训练与部署输入、再决定修改方向是合理的。不能把长度差直接定为唯一根因，也不能据此保证 BRG 修好数据就一定胜过 GRU。

下一步只开一个 BRG/GRU 的部署匹配开发版本。模型母体、hidden size、层数、反馈轮数不改；实际观测流水线与事件输入补齐；只允许一次模型自采训练轨迹的回灌。不新增 plume，不扩大旧 House03 campaign，不利用 House03 选参数。

## 1. 本次实际依据及核查范围

读取：BRG_NATIVE615_P1_REVIEW_20260927.zip 与 BRG_P1_FAILURE_ANALYSIS_20260927.zip；核对两包的 SHA256、阅读执行代码、训练清单、运行配置与已有复算结果。未重新进行 988 步重放，未重新训练，未运行 ROS 或模拟器。

源码重点：
- execution/pmfs_brg/features.py：时间/风只记录、不输入；前三个观测通道保持幅度与 >0 标志。
- execution/pmfs_brg/data.py：OpenPaths 每序列10个时刻；LoggedEpisodes虽可读变长日志，原run_config实际使用OpenPaths。
- execution/tools/train.py：归档版本已经使用所有前缀交叉熵，验证选择却只读最终前缀；不得把“第一次加入prefix loss”当新贡献。
- execution/pmfs_brg/model.py：一次事件内部3轮BRG是内部计算，不是3条独立传感器证据；output为完整prefix logits。
- execution/pmfs_brg/runtime.py：旧事件时间只检查，不编码；posterior是替换，不是连续相乘；有128事件限额。
- execution/native_source/algorithms/PMFS/PMFS.cpp：每事件网络更新，只有source-update时安装q及planner方差。
- execution/native_source/algorithms/PMFS/PMFS_utils.cpp：集中度停止。
- provenance/native_support_resolution_v2/TRAINING_MANIFEST.json：216 train、72 dev plume；每环境只有六个真实源正标签，H02两个wind共用源位置。

实际全支持GPU训练入口未完整包含在原复核包。新版本应归档实际入口，不能误用旧CPU六标签映射；也不能据此指控过去已经错训。

## 2. 为什么不能只把序列长度从10改为100

冻结的旧任务可记为：
R_old(theta) = E_{h~d_fixed, y~raw_snapshot}[-log q_theta(s|h)]。

实际任务为：
R_loop(theta) = E_{h~d_{planner(q_theta)}, y~sensor_and_event_window}[-log q_theta(s|h)]。

差别有两个：观测变量不同；被访问的历史分布不同。长序列重复十张图不能补齐这两个差别。

在给定任务数据分布下，NLL风险分解为：
R(q)=H(S|H)+E_H KL(p(S|H)||q(S|H))。

这支持在真实部署历史上训练，并不保证有限样本网络校准，更不是闭环成功率定理。相同完整历史、相同物理模型和先验下，源无关策略的动作选择概率在后验赔率中抵消；变化的是实际遇到哪些历史及模型近似误差，不能把机器人动作当成另一条真源标签。

只用Native日志训练仍只覆盖d_native。取一轮预训练模型亲自选择的OPEN轨迹，监督其源预测后并入共享训练集合，可以直接覆盖部分d_model。这里借鉴数据聚合思想，但不是动作模仿学习，也不继承DAgger的完整保证。真源只用于离线损失，不用于采集时动作。

## 3. 输入：只做必要的新版本扩展

实际路径上的连续气体 -> 相同VGR sensor_model -> 同样10原始读数组成event -> 同样每停点5 event -> 网络。

源浓度、传感器滤波、窗口平均和原生阈值都按部署代码。传感器状态在移动中如何演化，照原VGR调用实现，不在每个stop重置。不得从10张稀疏图插值伪造高频气体。现有连续输出只有有限时间分辨率时，使用部署已有的因果取帧约定，二者完全相同，不宣称恢复了更高频物理。

必须补记录实际原始消息窗口起止，而不是猜“收到消息时间就是采样时间”。

旧3个观测通道、6个candidate cue保持。追加3个合法通道：
1. 相邻event采集结束时间差（s）；
2. 当前event实际窗口长度（s）；
3. 两event采样位置间位移（m）。

编码固定为 log1p([dt/1s, duration/1s, displacement/0.30m])/8。
这只是建议的新输入版本，不是物理定律；三种网络统一使用。

model.obs_dim由3改6，cue_dim保持6；BRG hidden32/rounds3；GRU hidden35/rounds1；ungated保持同BRG但关反馈。参数量重新报告；不在此轮另搜索宽度以凑表。

当前>0网络标志与Native 0.1阈值差异不能自动当成bug。本轮不改各自既定阈值，但必须在相同实际传感器输出上学习、在数据中同时记录两种标志。不得以阈值变更救旧结果。

重复消息由event_id去重；不同event即使同位置同浓度也不得直接删除。后者可能仍含信息。

## 4. 训练程序

先按物理source组分train/dev/eval，H02同一source不同wind不能分到不同集合；相邻源对尽量作为一组。plume的所有路径、切片、窗口均跟随同一个split。利用可访问、与合法模板兼容的已有OPEN多源数据；模板数不是正例源数。

具体可用源数由VM资产表决定，不能在本包捏造。训练开始前一次确定各split与采集case数，之后不按成绩换源。若只有原来12个物理位置能生成合法日志，必须写明范围：允许小规模可行性开发，但不得声称已补足跨位置训练。不得默认打开H03或额外生成plume来填数。

采集R0：每个选定train case按Native及一条预定可达coverage策略获得日志。轨迹由各自策略产生，不使用真源选路。全部模型共享数据。

训练轮0：同样种子、同样输入和监督、同样优化器，最多10 epochs，给三模型各一个warm checkpoint。保留原AdamW lr=1e-3、weight_decay=1e-4、clip=1。新协议可在执行前修改预算，但不依据测试效果。

只一次回灌：三个warm模型分别在相同train cases运行已有PMFS planner，各自走自己的路线；将三者日志取并集，连同R0共同提供给全部三模型。正误轨迹全部保留，不只采失败或成功；不得将dev/eval/H03日志加入训练。无动作expert oracle，只有离线source supervision。

训练轮1：从各自warm权重继续最多20 epochs。总优化预算10+20，不再开展第二轮回灌以求过线。模型沿整条日志从RESET至末尾处理；不能切窗后假装隐藏状态始终来自零。如果用TBPTT，前向状态跨块保留，仅detach梯度，记录截断长度。

对每条episode：L_e=mean_t[-log q(s_e|history_t)]；同一plume多个采集策略先平均，再plume平均，最后source平均。代码提供精确加权函数；这不把数据增广计为新独立样本。

训练仍是prefix CE——旧代码已经有这个目标。新增的是部署一致的长历史、源覆盖、合法时间输入和训练分布聚合。

检查点选择用独立dev的source-update前缀平均NLL，而不只最后第10步。可使用固定Native/coverage dev日志；将三种warm策略在dev上的日志另存为只用于验证的共同集合，以避免只在Native历史选权重。dev日志不进梯度或回灌。

## 5. 后验与重复证据

正确形式：q_t(s) ∝ q_{t-1}(s) p(o_t|s,history_{t-1},action_{t-1})。
这里似然条件包括历史；不要求观测独立。
当前网络输出完整prefix预测，runtime直接替换，不再乘q_{t-1}。保持这个语义。

在一个理想退化情形，若新读数完全由已知历史确定且所有source一致，它不应增加赔率。但相同数值并不证明它是这种冗余观测。因此本版不强制“零hit不更新”、不强制每步降熵，也不把新增数据随机重复多次当作独立证据。

## 6. 停止处理：先隔离可学习问题，不改变比较条件

在训练/验证日志采集模式中，将source-declaration记录为shadow事件，不结束300s日志（碰撞、安全与基础设施故障仍正常停止）。该模式不是正式闭环成功成绩，仅用于获得长历史与错误声明后的训练样本。

在新版本的四臂evaluation中，恢复原生终止逻辑，原阈值、0.5m几何评价、300s预算、source-map位置估计器均不变，所有方法一致。T=1，不校准温度、不放宽success radius、不为神经模型专设额外停留。这样不能靠多飞时间换成功。

var(q)很小只说明模型自信。例如q全部在10m外，variance仍为0。若q恰好是真实条件分布，可以计算某一声明区域的后验质量；当前softmax并无这种保证。

未来要改停止规则，必须在另一个明确模块中用OPEN独立轨迹校准并同臂比较，不在这一版同时修改。单点temperature scaling不解决错误位置，也不自动保证任意停止时刻的校准。

## 7. 直接回到一次小闭环比较

完成以上两个训练轮后，先在按源组留出的OPEN evaluation上选四个源各两条realization（8 cases），四臂32 runs。选择只依资产与几何，不读结果。若预先划分无法支持四源，就停止调度并报告实际覆盖，不改用House03补位。

Native / candidate-GRU / BRG / BRG-ungated，各自闭环，所有动作可根据各自q变化。同例共享plume、初始位置、物理时钟、传感器与预算。首次功能检查包含在32条，不额外重复。

主要报告：每个case的0.5m几何成功、最终估计误差、错误声明与声明时间、实际时间/路程、源位置覆盖。NLL只在truth属于候选support时使用。不比较不同模型各自已经走出的同一组日志来冒充counterfactual闭环性能。

这是开发预算决定，不设置p值或科学PASS：
- BRG仍不及GRU，且门控消融无额外价值：不再为BRG身份继续调模型。GRU可作为实用开发结果保留。
- BRG只降错误声明但没提高预算内定位，不称定位成功。
- 相对Native和普通GRU均有方向收益，错误声明不恶化且不只由单一源贡献：才提交是否扩大campaign的决策；8例不证明主创新。
- 基础设施错误单独登记；有效的算法负结果不能再归类为实现HOLD。

旧H03 P1不改判，不训练、不选参数。以后H03再评估应承认它已参与开发诊断，不能称整个研究从未接触的盲测。

## 8. 交付与边界

本包提供：数学推导、实际修改列表、时间输入与分组损失工具、17项确定性测试、已核对的源码摘录。不是新的训练权重，不是已编译的ROS补丁，不宣称任何定位增益。

测试只验证局部输入/损失/分组语义，不能验证完整VGR、全支持GPU入口或新训练效果。Codex需在已有工作区接入并归档实际执行代码，不使用过期六类loader。

停止因果归因过度延伸：这一轮若提高表现，说明一组部署匹配训练修改有用，未隔离三项各自因果贡献；不得宣称BRG生物机制由此得到证明。

## 文献（原始来源）

1. Salehi et al., Nature Communications 17, 4072 (2026), DOI 10.1038/s41467-026-72146-9。视觉注意与反馈母算法；不保证当前GSL改造优于GRU。
2. Ross, Gordon & Bagnell, AISTATS 2011, PMLR 15:627–635, https://proceedings.mlr.press/v15/ross11a.html 。借鉴策略诱导数据分布与聚合思想；本方法不模仿动作，未证明DAgger条件。
3. Guo et al., ICML 2017, PMLR 70:1321–1330, https://proceedings.mlr.press/v70/guo17a.html 。温度校准是普通方法；不是新机制或闭环停止保证。
