# JGR 2025：R0 数据可用性审计

审计对象：Zenodo 10433810 的全部 12 个文件，DOI 10.5281/zenodo.10433810。文件类型、字节数、SHA256、来源、许可、下载日期见 jgr2025_file_manifest.csv。全部校验通过。

## 已证实的数据契约

- 7 个流场 case：Mg=0；Mg=0.4/1.2/2 m/s 各对应 alpha=0/180°。Mg0point4_alpha0_TR.nc 是本任务指定的首要比较候选；较高背景风候选为 Mg1point2_alpha0_TR.nc 和 Mg2_alpha0_TR.nc。本轮只定位文件，不判定其滞回强弱。
- U/W/T 都是沿 y 及时间平均后的 X–Z 切片；U 为跨岸速度，W 为垂直速度，T 为位温(K)。没有公开 V、完整瞬态 XYZ 场、浓度羽流、气体源真值或 UAV 轨迹。
- Mg0 的每个变量有 6,635,520 个元素，对应 270×64×384；其余为 8,478,720，对应345×64×384。全变量有限性计数及范围见 jgr2025_variables.json。
- README 说明同一 x 的第一个64×nt区段是 Z–t 切片，但没有唯一确定 z/t 内层排列的代码或 coordinate。禁止仅凭数组长度套用任意 reshape 顺序。
- 论文 Sec3.3/4：海面278.15K；陆面相对海面温差幅值10K、周期24h；分析第三日，即48h spin-up后的24h。图示场在 y 方向以及中心1h窗口平均。这是论文定义，不能自动当作345个存储快照的已解码时间轴。
- README 给出80km×5km×1.6km、384×24×64；论文分析域X=10–70km。文件没有明确x/y/z/time坐标数组。README的c_s/w节点规则未在变量表逐变量完整标注，保留坐标重构不确定性。
- Shore_Surface_Exchanges_All.nc 的24个变量，每个58点；有归一化Delta_Theta、SGS海/陆热通量、归一化Qshore、岸边TKE。Mg1.2的Qshore/TKE存在，但对应SGS海/陆热通量未在文件中提供；Mg0的Qshore/TKE也未提供。见case_map。
- Enstrophy共3文件：Mg0有59点；alpha0及180文件各有3变量、每变量116点。与58点强迫及270/345快照不等长，不能按索引直接拼接。

## Supporting Information 与来源版本

已下载美国能源部OSTI的LLNL-JRNL-866510作者稿（58页）：https://www.osti.gov/servlets/purl/2532506 。PDF第49–58页含S1–S12附录，本轮提取为 supporting_materials/jgr2025_supporting_information_OSTI_manuscript_appendix.pdf，并保留完整稿与SHA256。

该稿首页标July9,2024、submitted manuscript；不是已验证的最终出版社SI。出版社最终SI链接的下载返回403；source_download_attempts*.json记录尝试。正文定义另与已发表HTML Sec3.3/4核对：https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2023JD040708 。作者稿附录与最终版的逐页一致性未确立。

## R0/R1边界

可用于设计跨岸/垂直平均环流及表面强迫比较。front location 可由U/T剖面后续定义诊断，但文件没有直接front标签；本轮不计算或分类。

R0条件可用，尚需快照时间起点、间隔、z/t内层顺序及坐标节点的明确证据，才能执行可复现matched-forcing配对。R1不能把本包作为完整瞬态3D风场送入气体扩散模拟；这不是假说成立/失败的结论。本轮未生成CFD或进行聚类。

优先缺口：作者的时间/reshape脚本、完整空间节点、最终出版社SI；若需瞬态3D气体传播验证，还缺对应原始三维场及气体源/羽流。
