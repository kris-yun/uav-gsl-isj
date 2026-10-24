# 给 Pro：冻结 O24 统一闭环筛查完整证据包

先读本文件，再读 `中文筛查报告.md` 和 `domain_audit/FOR_PRO_SOURCE_DOMAIN_MISMATCH_zh.md`。本包把运行结果、技术失败、版本归因与源候选域问题放在一起。

## 运行数量与结论口径

已登记 12/12 个预定槽位；完成并通过原生数值复算的运行 10 次；其中源域合法 6 次、源域排除诊断 4 次；预定槽位内技术中止 2 次。数值复算通过不等于源域资格通过。
另保留 A2_R02 正式目标启动前的零目标技术尝试，该次不计入定位运行数量。还附有本批之前、已经单独授权恢复的A2先导技术失败原始记录；它不占本批新增目标配额。不得把12槽都已登记说成12次都完成定位。

|预定槽位|源域|运行状态|原生声明|Top-5%误差m|物理搜索时间s|
|---|---|---|---|---:|---:|
|A2_R01_REFERENCE|LEGAL|PASS_NATIVE_DECLARATION_AND_OFFLINE_REPLAY|True|0.24249439619906538|467.092|
|B2_R01|EXCLUDED_DIAGNOSTIC_ONLY|PASS_NATIVE_DECLARATION_AND_OFFLINE_REPLAY|True|2.0043676027478705|353.034|
|B2_R02|EXCLUDED_DIAGNOSTIC_ONLY|PASS_NATIVE_DECLARATION_AND_OFFLINE_REPLAY|True|1.8800472318134067|250.234|
|B2_R03|EXCLUDED_DIAGNOSTIC_ONLY|PASS_NATIVE_DECLARATION_AND_OFFLINE_REPLAY|True|2.2065086754267917|366.331|
|B2_R04|EXCLUDED_DIAGNOSTIC_ONLY|TECHNICAL_ISOLATION_UNVERIFIED_ABORT_RETAINED|None|||
|B2_R05|EXCLUDED_DIAGNOSTIC_ONLY|PASS_NATIVE_DECLARATION_AND_OFFLINE_REPLAY|True|2.1052293321668816|565.779|
|A2_R02|LEGAL|PASS_NATIVE_DECLARATION_AND_OFFLINE_REPLAY|True|0.6132464565175773|459.202|
|A2_R03|LEGAL|PASS_NATIVE_DECLARATION_AND_OFFLINE_REPLAY|True|0.497209355450665|347.598|
|C3_R01|LEGAL|PASS_NATIVE_DECLARATION_AND_OFFLINE_REPLAY|True|0.4296188743522746|542.662|
|C3_R02|LEGAL|PASS_REPLAY_CENSORED_RUN_NOT_A_DECLARATION|False|0.6274102546954273|None|
|D4_R01|LEGAL|PASS_NATIVE_DECLARATION_AND_OFFLINE_REPLAY|True|0.7996592614320179|126.8|
|E3_R01|UNKNOWN|TECHNICAL_OR_PRE_GOAL_FAILURE_NO_SOURCE_POSTERIOR|False|||

## 必须保留的边界

1. 原生 action success 表示达到声明条件，不代表定位坐标正确。源方差门是1m²；数据耗尽与技术门单独记账，不以300秒强制截断正常搜索。
2. B2 真源三维合法，但作者公开配置与候选规则将其二维格排除。因此B2只作为域失配诊断，不计合格真源支持条件下的推断失败；约0.248m近邻候选仍存在，不能用域排除解释全部约2m误差。
3. A2/C3/D4/E3的源候选资格已核对；各配置采用固定现有气体回放。重复闭环不是独立气体世界，实际RNG记录不等于独立seed证明。
4. 固定二进制e63未修改。O24是a8的已登记移植与数值修复，不直接等同于作者当年全部论文性能复现；详见源码差异、信息权限和时钟对照。
5. B2_R04因sftp-server环境不可读触发保守隔离中止，不补跑或算定位失败。A2零目标启动误报来自包装脚本枚举竞态，修复只涉及进程归属核验；原日志保留。

## 建议Pro优先研究的问题

先审查官方导航域与物理源域复用的适用边界，再检查最近合法候选为何仍被其他源压过。解除源域限制属于普通结构适配A′；只有A′之后仍存在可重复源判别困难，才据此设计并验证新增B运算。不得把旧H26 B4、BIO A′前向错误或本轮技术中止算作O24推断缺陷。

## 文件组织与复算

- `full_runs/`：各预定槽位原始日志、全部候选预测图、后验、命中图、参数、原始CDR、RNG及成本。
- `pre_goal_technical_attempts/`：A2零目标启动失败原始档案。
- `review/domain_audit/`：官方地图/源坐标/规则、实际占据图、三维源合法性、0像素差异证明与独立脚本。
- `review/recovery/`：每次工程停止与恢复的原始证据、协议不变证明。
- `physical_asset_identity/`：既有世界身份、1803帧哈希及生成配置。`HISTORICAL_PRECHECK_MAP_METADATA.json`属于历史预检，不是本批实际输入地图。本批实际地图以各次运行ZIP中的 `runtime/navigation_map.s8` 和 `NAVIGATION_MAP_METADATA.json` 为准；B2专项另含与官方地图的0像素差异证明。完整原始世界保留在原路径，不复制巨大世界到本包。
- `support/`：冻结代码包、历史同输入源码评分审计和Git交付收据；`review/`同时附版本索引、归档SHA、空间清理收据和恢复脚本。
- 根目录 `MANIFEST_SHA256.json`：整个包逐文件SHA；内层运行ZIP另有逐成员SHA。

解压整个包后执行：`python review/reproduce_complete_bundle.py <完整解压目录>`。仅需Python、NumPy；域专项另需Pillow与PyYAML。不启动ROS/GADEN，不新增预测，不读取外部封存集。复算脚本只向新的临时目录写QA，不覆盖输入。

注册表中的 `O24_QUALIFIED_NATIVE_EVIDENCE.md`、`SCIENTIFIC_CONCLUSION_FOR_PRO.md` 及旧版本审计属于本批之前的阶段性材料，保留其原始适用范围；当前结果以本文件、`EPISODE_RESULTS.csv`、`RUN_EVIDENCE_INDEX.json`和逐运行QA为准。不能因旧报告当时只有A2阳性，就忽略本批新增的结果。

本轮全部正反结果保留，不按结果选择源、地图、阈值或风场；未宣称创新增益或论文30次统计性能复现。
