# Mackenzie Channel Seep 2：公开数据资格及条件风反演审计

数据具备资格：四条有已知源参考坐标的真实固定 curtain 路径足以建立点源反演输入与水平误差评分。正式判定MACKENZIE_HOLD_SOURCE_INVERSION_NOT_ROBUST：本轮没有证明“平均风失效、局地风稳定修复”，也未达到协议要求跨架次/平台稳定的MACKENZIE_GO_REAL_POINT_SOURCE门。

## 原始包、场景和采样资格

[官方数据 DOI](https://zenodo.org/records/20019779) 的唯一29,554,312-byte ZIP已完整下载，MD5与发布方一致，SHA256为4c0bdd1adebe8f794f2ee533761ea9e064c3a59011793651378851544883ff49。10个文件全部解压并逐文件记录SHA；原始CSV及notebook未改。

[作者论文](https://amt.copernicus.org/articles/19/3983/2026/)及四个CSV确认2025-08-01的CP1/CP2/OP1/OP2，天然点状逸散源参考位置69.319583N,-135.477520E。CP为手动航线，OP为已编程航线；两者均事先知道源并安排下风curtain，不能用于未知源自主搜索结论。论文近/远下风距约CP87/163m、OP77/149m。坐标旋转后的样本中位距离不一定等于论文航线标称距离。

CP实际CSV2125/2250行，2Hz，CH4单位ppb转ppm；WS_corr采用m/s，WD_corr依据作者notebook和DMB的+19°北向修正。OP实际10306/6373行，约10Hz；不能把100Hz传感器名义率称作公开CSV率。论文两套平台均为二维水平风传感器。CP有VertWind辅助列，不足以把整个包宣传为两套运动修正3D风。

原论文有GS1 1.5m、GS2 2.7m地面风，但完整公开包没有它们的时间序列；不能拿图或UAV均值冒充ground-only输入。ground-only arm明确NOT_RUN_DATA_UNAVAILABLE。

## 作者方法复核与明确偏差

EPSG32608投影、Prep_Curtains两段旋转的等价直接旋转、CH4转换、P(z)=101987−12.26z Pa、T=292.4627K、methane质量密度、背景扣除与GPI镜像高斯核均复核。AST提取作者forward函数与适配函数数值完全一致。固定已知源的GPI拟合使用scipy least_squares代替lmfit及1s数据约简，见AUTHOR_FIXED_SOURCE_GPI_REPRODUCTION.csv；这是可移植的作者方法重跑，不宣称逐位复现其论文表格或所有原始传感器修正。

作者GPI/main.py使用CP背景2.031797、OP背景2.064857ppm；CKMB/DMB与论文OP背景约2.0291ppm，且CKMB/DMB用CH4_dry，GPI读CH4。这里保留GPI输入选择，单独测试论文背景；没有把不同处理链的输出混为同一方法。上游完整lag、raw sonic motion correction并不在4个curtain CSV中。

CP1日期时间未带时区，CP2 DateTime截为mm:ss且跨小时；OP TIME_UTC实际是Excel serial day而非秒，TimeStamp为整数Unix秒并重复。不借这些字段猜跨平台对齐或sensor lag。空间模型采用发布方同一CSV行，不作传播时滞结论。

## 固定路径未知源比较

真源只用于作者固定源通量复现及所有未知源拟合完成后的评分；未知源输入只取接收位置、气体、矢量风、高度。原文件中的source-relative x_prime/y_prime不用于未知源拟合。候选域由观测GPS包络与观测平均风确定，向上风延伸10–400m；等权源网格31×31，沿风13m步长，source height=0。均匀/局地/每架次线性高度风三个arm使用同一气体、源域、非负释放率和扩散网格。

current-local只把接收时刻本地风代入稳态高斯核，不知道传播路径的历史风；height-dependent只拟合本条轨迹的风—高度关系，不是独立三维气象场。两者均不等同于已经恢复了真实source–receptor propagation state。


### 冻结主配置

|航线|风表征|条件定位误差m|源网格边界|
|---|---|---:|---|
|CP1+CP2|flight_mean|5.08|False|
|CP1+CP2|uav_current_local|42.60|False|
|CP1+CP2|height_dependent|35.85|False|
|OP1+OP2|flight_mean|16.71|False|
|OP1+OP2|uav_current_local|56.73|True|
|OP1+OP2|height_dependent|56.73|True|

### 扩散支持范围敏感性

|航线|风表征|条件定位误差m|源网格边界|
|---|---|---:|---|
|CP1+CP2|flight_mean|55.52|True|
|CP1+CP2|uav_current_local|42.60|False|
|CP1+CP2|height_dependent|29.69|False|
|OP1+OP2|flight_mean|44.21|False|
|OP1+OP2|uav_current_local|56.73|True|
|OP1+OP2|height_dependent|44.21|False|

主配置的CP联合mean误差5.08m，扩大扩散参数支持后变成55.52m且贴源域边界。OP联合mean16.71→44.21m；local56.73m且贴边。背景切换对本网格MAP不改，但扩散支持改变风排序。不能择取最有利配置声称某风表征优越，不能把边界最优点当稳健定位。

单curtain中sigma_y=tau_y*x、sigma_z=tau_z*x；自由source distance与tau可以互相补偿，释放率进一步参与。近远联合强加同Q和扩散参数后可给条件点估计，但两架次稳态一致性的假设并未由数据保证。主配置RSS相对最小值+5%支持域只作可辨识性诊断：不是Bayesian posterior，也不是95%可信区间。CP均风联合支持域northing span约155m，不能把5m点误差误读成5m确定度。

NEAR_FAR_CONSISTENCY.csv报告各风arm单独近远源估计分离，INFERRED_PLUME_CENTERLINES.csv给出均风直线中心线交点，HEIGHT_WIND_PROFILES.csv给出真实高度分箱风。全空间plume truth、持续停滞区、岸线传播滞后和真实未知源搜索均不能由此证明。

## 结论

可以合法评分固定轨迹源参考点误差；当前高斯反演的源距离与扩散可辨识性、时变传播及传感器处理仍限制该评分的解释。缺失地面日志阻断ground-only比较。Mackenzie不构成Svalbard中“local wind修复mean wind”的独立正向复现。本轮保持MACKENZIE_HOLD_SOURCE_INVERSION_NOT_ROBUST，不生成CFD/GADEN。
