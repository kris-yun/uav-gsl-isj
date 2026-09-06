# CSTAR 原始 realization 来源核验 — 2026-09-07

## 当前结论及离闭环的距离

`CSTAR_RAW_REALIZATION_PROVENANCE=PASS`

| 检查 | 结果 |
| --- | --- |
| 已冻结三屋环境证据 | 离线重验 PASS，66/66 原始哈希匹配；未重跑环境 |
| 合格 realization | 12/12 |
| exact-source groups | 6/6，每屋 2 组 |
| 输运机制配对 | 6 |
| general nuisance 配对 | 0 |
| M2 qualified route cases | **0，NOT_YET_ROUTE_CONTROLLED** |
| M1/M2/M3 科学收益 | **本轮未评估** |

已完成本轮 provenance 停止点，允许下一阶段先冻结 truth-blind controlled routes。
**现在还不能直接进入生产闭环。** 尚需受控轨迹/结果抽取、M1/M2 有限训练和破坏性
对照、冻结 checkpoint 与在线接线 smoke。没有重新导出地图、生成仿真、训练网络、
跑 cstar_v1 或 12-run。下一阶段不应再重复环境 gate。

## 执行身份

- 输入 GitHub HEAD：`b258edafd776f1dad70254adcad8dfba688dc6f4`。
- 最终实际运行 auditor：`2662193`（完整 SHA 见 `runtime_git_sha.txt`）。
- 隔离 VM checkout：`/home/zyc/CSTAR_RAW_PROVENANCE_20260906`。
- Python/Torch 完整版本和新旧 mandatory selftest stdout/stderr 随包保留。
- 未修改旧环境 checkout、原始 House 数据、保护 bank 或冻结 split 文件。

## 核验使用什么，而没有使用什么

1. 保存并解析全部 12 份原始 ROS2 generator launch，另保存对应 ROS1 launch 与
   preprocessing launch。源位置来自生成器参数，不是从目录名推出来。
2. 每份 iteration_0 只解码 **136 字节旧版文件头**，核对源位置、gas type、
   dimensions、cell size 和环境范围；未解码任何丝团/浓度 body。
   保存原始压缩前缀、原始 header 和字节数，不把派生 JSON 自己当生成时证据。
3. 132 个既有风输入按 archived GADEN WindSequence 的格式规范化为实际使用的
   float32 速度向量，再计算指纹。单纯换路径名或换编码不会被算成输运扰动。
   全部风文件通过布局、有限值和数值完整性检查。
4. auditor 再次从真实 XML、header、occupancy 和原始风文件独立计算物理指纹，
   与 normalized entries 比较；不是信任 builder 填的 fingerprint 标签。
5. 六组均为同 House、同几何、同 exact source、同 gas type、同 release 参数及
   文件头内实际存储的 filament 摩尔数/载气摩尔密度和
   同 raw sensor stage，而规范化的风输入序列不同。

## 不能扩大解释的边界

- **这是生成器机制级配对，不是 M1 因果收益证明。** `variable_rate=true`；同一释放
  机制不等于同一随机释放序列。本轮没有恢复或证明两次生成的 random seed 相同，
  也没有检查实际释放轨迹。不能将结论改写为逐条随机轨迹完全控制的 transport effect。
- raw GADEN 文件没有经过测量传感器。相同 sensor fingerprint 表示“raw 阶段无测量
  sensor”，不是 FOPDT 轨迹已经验证；FOPDT 要在未来受控抽取中审计。
- 生成配置及 header 的一致性支持原始机制身份；没有新增声称找到了逐次生成命令、
  完整随机种子记录或每一步释放日志。不同源组仍可能携带不同风场配置或气体类型，
  后续 context-only / label permutation / zS destructive controls 不能省略。
- H01 fast 的 environment coordinate slots 是 float-in-double-slot，slow 是 native
  double；H02/H03 为 native double。两种解释均对齐冻结几何。此编码差异不计入
  transport fingerprint，也没有为此修改旧输入链。
- frozen inventory 的 `payload_read=false` **只说明当时的目录盘点不读 payload**。
  历史闭环以及之前 1.6s 环境 probe 已经读取过部分 realization。故本次 split 可称
  “在新受控抽取前冻结”，不能称“所有原始数据从未被观察过的全新确认集”。
  split 本身保持原样，所有后续 prefix/route/outcome 继续继承每个 outer fold 的父身份。

## 修正了上游 auditor 的哪些实现漏洞

- 原测试仅一屋四条记录即可得到总体 PASS，且不检查 outer_folds 内容。
  现在要求 12 个唯一 realization、H01/H02/H03，并逐 fold 核对真正 train/heldout 集合。
- 原代码只要求字符串 fingerprint 非空；即使证据 literal 没有绑定其物理含义也可能
  通过。现在从原始内容重新推导 source/gas/release/transport/sensor 并拒绝伪造标签。
- 收紧 source authority 类型：transport/sensor 配置不能充当 source authority。
- 任何整体 gate 未通过时，不释放可供下一阶段抽取的 eligible 列表。

mandatory selftests 包含完整三屋 synthetic happy path，并拒绝目录名来源、伪造
transport/sensor 指纹、缺失物理绑定、fold 泄漏、一屋冒充完整矩阵。这些测试数据
仅为实现回归，未混入科学证据。

## 文件索引

- `CSTAR_RAW_REALIZATION_PROVENANCE_V1.json`：12 条 normalized input，证据路径/SHA。
- `CSTAR_RAW_REALIZATION_PROVENANCE_AUDIT_V1.json`：12 条重算结果、6 对资格、所有统计、
  完整 eligible realization ID 列表（只允许以后先冻结 route，不允许立即读取 gas outcome）。
- `metadata/`：原始 launch、136-byte header、压缩前缀、机器可读检查记录。
- `WIND_INPUT_IDENTITY.json`：132 个真实风文件及规范化向量 SHA；没有打包全场数据。
- `source_snapshot/`：实际 auditor、collector、原始 decoder 源码、未改 split 原始字节。
- `selftest_*.log`、`environment_integrity_66.log`：全部回归及旧环境完整性。
- `SHA256SUMS`：本目录的归档字节完整性（不包含自身或临时 Python cache）。
- `superseded_config_only_release/`：保留初版仅基于配置的 release 指纹报告。
  最终 R2 加上实际 header release 常数后重算，仍为 12/12、6/6 PASS；初版不再作授权依据。

完整物理 re-audit 需要 VM 上原始风文件与 House geometry，不能只靠小型归档证明
大体积外部 payload 的当前内容。离线归档可以检查所有打包证据的 SHA 和 normalized
统计；完整核验命令如下（不训练、不抽取 gas body）：

```bash
cd /home/zyc/CSTAR_RAW_PROVENANCE_20260906
python3 experiments/ctpi_cstar/audit_raw_realization_provenance.py \
  --manifest evidence/cstar_raw_provenance_20260906/CSTAR_RAW_REALIZATION_PROVENANCE_V1.json \
  --output /tmp/CSTAR_RAW_PROVENANCE_REAUDIT.json
```
