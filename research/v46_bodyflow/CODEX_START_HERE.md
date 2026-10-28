# V46：先读此入口

本轮研究入口位于 `research/v46_bodyflow/`，属于新的独立研究分支；仓库根目录历史 TNQC/其他版本入口不自动覆盖本合同。原冻结源码和历史证据一律保留。

目标是核验 **M1 体心位置—流向极性—因果气味历史的双通路运动读出**。M2 是源判别支撑，M3 是时间/模型/安全与唯一计证辅助。不能用旧 V43 源强离散修复的增益冒充新 M1；不能把本目录 Green/ZOH 证书冒充 VGR 或实飞。

先执行已可运行的工作：

```bash
python3 tests/test_chain.py
python3 run_reference.py --output results/reference_run.json
python3 preflight_native.py --manifest protocol/native_manifest.json \
  --output results/native_preflight.json
```

第三个命令在模板未填或真实数据/接口缺失时会输出 `UNRESOLVED_DATA_OR_INTERFACE`，不会用解析环境偷偷替代。请据 `protocol/CODEX_EXECUTION_CONTRACT.md` 查找已有数据、补齐原生接口并生成可核查收据后再运行；这类缺口不是“本方法失败”的证据。

公开固定阵列字段审计已实际完成。如需重现：

```bash
python3 audit_orebro.py --download \
  --data-dir data_external/Orebro3DSEN \
  --output results/orebro_qualification_audit.json
```

它固定官方提交 `d5a55a0fc5e77b95456fbb7be62bc8154508dbee`，只验证已有记录支持什么，不执行新轨迹定位比较。

接下来按合同完成：已有 VGR/House 原生公共时钟接口 → 共享正确推断底座 → 一次小规模接线回归 → 冻结验证清单 → **300 s 时由原函数 `ExpectedValue(sourceProbability, 0.05)` 给出的水平位置误差**和完整失败归因。双方二维概率图须采用共同地图、同一函数实现与相同单位；共同 XY MAP 误差为并列预定指标，不能替换主要原生终点。不要擅自改成 5 min/10 min 的多个时间终点，不把首次接触前共用覆盖产生的结果归于 M1。

交付时写明代码 commit、数据哈希、实际命令、原始日志、全部失败、未完成项；禁止用“预计通过”代替运行收据。

## GitHub独立包的补充入口

本目录含完整 `proof_checks/` 和旧固定观测fixture。先运行 `python3 verify_all.py`，再按合同接原生环境。此命令跑十个数学/软件入口，不生成原生定位成绩。主文、理论PDF、课题组原文和第三方原始CSV不随公共代码分支发布。
