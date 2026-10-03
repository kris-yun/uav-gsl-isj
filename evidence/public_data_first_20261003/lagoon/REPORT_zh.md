# Lagoon Pingo：公开合同解锁复审（2026-10-03）

判定继续为 **REAL_LAGOON_HOLD_METADATA_CONTRACT**。这是同步与风数据谱系尚不能核验的 HOLD，不是数据科学价值失败。本轮只查 Track A；没有配对 flight 行、推断滞后、运行 Stage C/D、下载大影像或进行源反演。

## 本轮新增的权威文件证据

[Zenodo正式记录](https://zenodo.org/records/19597182)及concept记录19597181目前指向同一版本v1。完整发布清单只有10个文件：4个NetCDF、1个验证Excel、5个影像；没有README、processing notebook、独立补充文档或映射表。元数据提供的代码地址仍为 [johanage/lagoon-pingo-analysis](https://github.com/johanage/lagoon-pingo-analysis)。文件列表、大小、官方MD5和地址已逐项保存，不把描述中的 draft/files URL 当额外隐藏文件。

原来的 merged NC 和 Excel 未改。本轮补下载3个publisher processed sensor产品，放在独立的 unlock_20261003/raw_sensor_contract_inputs，而不是混入其他数据集。总新增201,131,206 bytes，三个文件均通过发布方MD5与大小校验，并计算本地SHA256。

| 官方文件 | bytes | 行轴 | 轴标签/合同 |
|---|---:|---|---|
| svalbard_aeris_all_flights.nc | 17,372,006 | flight=6 | 仅netCDF dimension scale，无可用flight coordinate |
| svalbard_flightrecords.nc | 90,533,646 | flight=27 | 仅netCDF dimension scale，无可用flight coordinate |
| svalbard_trisonica_corrected_split_flights.nc | 93,225,554 | flight_tris=13 | 仅netCDF dimension scale，无可用flight coordinate |

这些行数不一致表明发布产品包含选择、拆分或合并过程，需要作者给出转换规则。它们本身不能证明哪个传感器行对应哪个 merged flight。底层HDF5的dimension scale占位值不是发布方架次编号。

corrected_split_flights产品只包含U/V/W等变量，没有ucorr/vcorr/wcorr；后者出现在merged产品的另一个flight_frec轴。因此需要明确两个文件之间的计算和合并谱系，不能仅凭文件名“corrected”就将U/V/W等同于最终运动修正风。U/V/W及merged corrected变量均没有物理单位/坐标系属性，不能确定ENU/NED/body、分量正方向、yaw/安装角旋转和速度补偿。文件中的时间编码给出calendar及nanoseconds since reference，但无UTC/timezone契约；flightrecords包含[local]字段名，不能自行当UTC。

## 官方代码、作者材料与镜像检索

本轮再次请求官方仓库网页，HTTP404；raw main/master README也HTTP404。HTTP404不能区分私有化、删除或改名，因此报告仅称“当前公开不可访问”。GitHub API有部分HTTP403，但响应明确是API rate limit；这些403不用于证明仓库不存在。成功访问作者 [johanage公开repositories列表](https://github.com/johanage?tab=repositories)，列出的14个公开仓库没有该仓库；GitHub lagoon-pingo repository检索返回0条。这仍不能排除未索引或非公开镜像。

找到了作者Johan Fredrik Agerup的 [Inverse Days 2025官方摘要集](https://fips.fi/wp-content/uploads/2025/12/book_of_abstracts_inverse_days2025v2.pdf)，以及 [Svalbard Science Conference 2025官方摘要集](https://www.forskningsradet.no/contentassets/4ad2ee6d040d49aa8d20e7227f79d1ff/book-of-abstracts-ssc-2025.pdf)。前者对应Moskus Lagoon天然甲烷通量反演，描述稳态advection–diffusion、经验Bayes与UKI；没有flight维映射、运动修正、lag或时区的定义。摘要说明作者已有反演分析，不提供本轮解锁所需合同。没有将较早Lagoon地球物理/生物学论文当成2024 UAV处理契约。

另一个作者的 [AlouetteUiO/active](https://github.com/AlouetteUiO/active)公开borehole预处理流程属于独立field campaign。本轮没有找到Lagoon明确引用该流程的声明。不得把同作者borehole的时钟补偿和旋转矩阵直接套到Lagoon。

## 必须仍保持未知的内容

1. 精确flight↔flight_frec及standalone flight/flight_tris↔merged映射；包含原始文件名、截取区间、选择/拆分规则及稳定flight ID。
2. U/V/W与ucorr/vcorr/wcorr的单位、坐标轴、分量正负、旋转顺序、yaw/安装角、无人机速度补偿和缺失/QC处理。
3. Aeris、Trisonica、DJI的时区/时钟偏移、同步参照、重采样/插值规则、传感器响应及tube/lag补偿；说明merged tfs是否已消除全部原始时钟差。

只有发布方代码、补充方法或明确metadata能建立这些契约；可以用时间/数值相似性做QA，但不能以其替代作者的映射声明。没有按“都是13行”配对。

## 进入公开数据资格矩阵的结论

这是天然滨水/分布源场景，merged有13个未标号行，CH4约1Hz非空点和3D风/位置均在文件中；独立重复、路线source-aware程度尚未完成资格核验。Excel7个坐标提供独立flux/evasion空间证据，不能作为唯一点源真值。OSD.height是相对起飞高度，不是逐点地形AGL；当前没有独立地面/塔风文件。

**当前不能合法计算精确点源定位误差；不能用它证明风表征造成定位偏差。** 将来解锁后适合有限源区一致性及plume/transport外部场景验证；是否适合同期通量验证还要逐记录核实日期和时间。数据价值保留，但本轮不计入“至少两个独立真实数据集重复出现共同失败机制”的证据数量。

原始数据留在C盘独立Lagoon目录。所有新增下载receipt、header schema和合同判定位于unlock_20261003；资格行见QUALIFICATION_ROW.csv，缺项按未知保留。
