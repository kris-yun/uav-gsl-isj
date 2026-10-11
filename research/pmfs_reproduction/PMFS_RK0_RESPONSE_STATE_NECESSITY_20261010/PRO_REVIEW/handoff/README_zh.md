# M2/M3 独立审查交接包（2026-10-10）

先读 `PRO_M2M3_独立审查与主创新决策_20261010.md`。这不是已验证主算法或新导航成绩。

## 已完成与未完成

已完成：原1510项哈希独立检查；M2只读锚点/受体复算；M3子核验及派生表复算；同bank同评分的中心/PID读出比较；模糊分子分母对照；原预设带的评分差分解。

未完成：新增CFD/GADEN/原生前向、网络训练、克隆状态算法实现、独立新任务验证。Codex下一关是建议方案，不是已执行结果。

## 三个优先文件

- `PRO_M2M3_独立审查与主创新决策_20261010.md`：证据边界、复算、母机制和候选淘汰。
- `Codex_下一关_响应核与隐状态必要性_待批准.md`：先检验固定响应核是否已经足够，再决定是否需要克隆状态。
- `候选A_计算规则草案_未实现.md`：明确输入、状态、转移、响应、输出和不可冒领的理论性质。

## 重算本轮新增结果

依赖 Python、numpy、pandas、opencv-python。脚本不安装依赖，不启动ROS/SSH/仿真，不写原证据。请使用独立输出目录。

将用户原 `PMFS_M2_M3_COMBINED_ROOT_CAUSE_20261010_REVIEW.zip` 解压，并确认参数路径下直接含 `M2_FROZEN`、`M3_NEW`。

```bash
python scripts/independent_readout_audit.py \
  --combined-root /path/to/extracted/combined \
  --m2-zip /path/to/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010_REVIEW.zip \
  --out /path/to/new_audit_output

python scripts/same_bank_readout_contrast.py \
  --combined-root /path/to/extracted/combined \
  --out /path/to/new_audit_output
```

第二个脚本直接读取原参考bank的受体高度全格查询，使用相同原生相似度对比PID阈值与中心占用，不重新计算气体积分。它是探索性oracle字段诊断，不是部署算法额外获取447个测点。

主要输出：`SAME_BANK_SAME_SCORER_MARGINS.csv`；`READOUT_PAIRWISE_MARGINS.csv`；`DOMAIN_GAP_AND_PRESET_BAND.csv`。

## 原验证器并非在本环境原样PASS

原 `verify_combined.py` 卡在OpenCV版本字面值；可移植逐值复核又发现NumPy标量运算引起高度直方图边界标签约2.16e-7米差异。体素编号、计数、比例及核心结论没有变化。原证据文件未改，未扩大原数值容差。详细范围见 `new_diagnostics/PORTABLE_VERIFICATION_SCOPE.json`。

`verification_logs`保留M2核验输出、M3阶段运行日志与原始验证失败。完整物理重算表仍在本会话运行目录；轻量交接包不再复制用户38MB原证据，也不声称包含所有1000秒气体bank。

## 文献

真实DOI与作者稿入口在主报告末尾；CSCG基础早于2025，不能称为2025首次发明；HIBI已核实2026期刊信息，Kim等2026气源顺序推断所查版本仍为投稿预印本。候选不是已确认主创新。
