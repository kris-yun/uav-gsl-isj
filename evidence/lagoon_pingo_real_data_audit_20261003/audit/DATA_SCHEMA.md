# Lagoon Pingo 数据与同步审计

**REAL_LAGOON_HOLD**：两个核心原始文件完整下载并通过官方MD5校验；按Stage A的STOP规则暂停后续机制与预测分析。

NetCDF：13个flight行、独立的13个flight_frec行、55,747个共享tfs格点，94个数据变量。共享网格间隔约0.050s（约20.0Hz），属性median_sampling_rate=1不能直接解释为各传感器原生采样频率。请看SAMPLING_RATE.csv，分别列网格非空点间隔和各时间变量的唯一时间戳间隔。

名义同flight行的CH4+未修正U/V/W+位置+datetime交集为14,264个观测格点；CH4在20Hz共享格点上是稀疏数据，不能把每个观测乘0.05s当飞行或同步持续时间。逐flight的时间端点跨度、CH4非空点间隔和格点占据量分别报告，后者仅用于数据结构QA。修正风ucorr/vcorr/wcorr在flight_frec轴，文件未提供与flight轴的标签映射，因此真正通过审计的修正CH4+3D wind时长为“未建立”，不能用同一ordinal行号自动认定。

flight/flight_frec均是没有坐标值的维度。FLIGHT_INVENTORY.csv使用明确的ordinal索引，不伪造发布方架次编号。架次绝对时间范围来自datetime非NaT值；timezone未声明，不擅自标UTC。共同网格重复次数、timestamp数及Time/Time Stamp相对datetime的差值已输出；这些差值不能自动当作已知传感器响应延迟。

U/V/W和ucorr/vcorr/wcorr无单位及坐标系属性，未说明ENU/NED/机体系、yaw旋转、无人机运动修正和传感器延迟补偿。文件提供vx_computed/vy_computed等名称，但名称不是算法或校准证据。官方Zenodo元数据说明已处理同步；其给出的处理代码链接目前web404/git repository not found，无法核查具体契约。保留发布方声明，但不把声明当作独立时间/坐标校准证明。

Time与datetime的中位差在flight0约0.03s、flight1约56.739s、flight2约60.975s。它们可能是原始时钟差而已经在tfs中被补偿，也可能尚未补偿；缺少处理代码不能判定。不能简单把这些差值称为实际残留同步误差，更不能直接做基于物理lag的推断。

## 空间与水陆几何

位置优先有效范围内RTK，否则OSD，按WGS84经纬度投影至EPSG:32633。原文件UTM zone33/letterX与此一致，另报告与原UTM列的差值；WGS84基准来自DJI位置类型推定，文件未单独声明完整CRS定义。OSD.height为相对起飞参考高度，不等于各航迹点的地面以上高度。未使用DEM，因此AGL保持NaN。

已输出全部有位置样本的SAMPLE_CONTEXT.csv.gz与UAV_TRACKS_BY_FLIGHT.png、SITE_MAP.png。surface_context=UNCLASSIFIED，d_shore=NaN，crossings=未知；没有把未知填成0或把轨迹形状猜成岸线。

官方2024年8月影像在Zenodo中可用，元数据已保存，尚未建立经过视觉QC的2024水陆mask。首阶段按协议仅下载两个核心数据文件。旧DataverseNO DOI10.18710/IMPEG8的README明确是May2020春末存在icings，不能直接作为2024夏季water/land真值。由于Stage A门未过，未继续下载大影像或构造岸线机制证据。

## 独立源证据

Excel有5张表；Fieldnotes中找到7个显式经纬度记录，已投影并按site_id关联可匹配的chamber flux缓存值。Excel原文件未改动。其他仅有沿transect距离的点不擅自补坐标。Fieldnotes还提示display time可能与真实时间相差约10min，且ebullition样本注明2024-09-13；它们可以作为有限空间evasion证据，但不能当同期、精确点源定位真值。未使用UAV CH4定义源区，不运行源posterior评价。

## Stage C/D处理

CH4 ACF/whiff/blank、current-versus-history、water/transition/land history gain均NOT_RUN_GATE_CLOSED，不报告伪数值。没有以不明风轴和传感器同步假设训练预测器。缺少可核查契约是证据HOLD；当前没有证明数据本身不可用，不判REAL_LAGOON_FAIL。

解锁需要：发布方flight↔flight_frec映射、风分量框架与运动修正/单位说明、时钟/lag/时区说明或可访问的处理代码。确认同步和wind契约后再以2024影像建立水陆mask、signed d_shore、crossings，然后按预定整flight留出做后续统计。

来源：[Zenodo](https://zenodo.org/records/19597182)；[旧几何数据](https://doi.org/10.18710/IMPEG8)。原始SHA256见metadata/SHA256SUMS.txt。
