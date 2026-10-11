# 联合审核包主核验器说明与代码审查

核验器：`verify_review_bundle.py`。
最终 Windows 长路径修正版 SHA256：`4f87116904abb8b12515b578bfdd31fbae6272c20fdad502c0c59a6c2592f3f5`。

本脚本不执行物理仿真、不创建浓度响应缓存、不启动虚拟机、不调用旧 `verify_combined.py`，也不修改包内证据。其任务是核查交付包完整性，并可选独立复算既有数值。

## 默认核验范围

主 `SHA256SUMS.json` 为相对成员路径到 SHA256 的字典，完整覆盖所有文件，仅排除清单自身。核验器、README、导读生成脚本和全部嵌套清单也必须纳入主清单。主清单缺成员、额外成员、哈希不符、重复 JSON 键或重复规范化路径均失败。

嵌套的 `SHA256SUMS.json`、`SHA256_MANIFEST.json`、`SHA256.json`、`SCORING_CONTRACT_SHA256.json` 及 `*_SHA256SUMS.json`，仅在其自身父目录范围内核验已声明成员。不会搜索外部路径或猜测旧来源路径。来源血统 JSON 中的外部资产哈希由主清单保护文件完整性，不冒充包内成员清单。

拒绝路径穿越、盘符/UNC/绝对路径、点路径段、Windows 尾随点或空格、控制字符、符号链接、junction/reparse point。Windows 反斜线相对路径会规范化为正斜线，规范化后重复也拒绝。

## `--deep` 的实际范围

`--deep` 调用包内 `RK0_NEW/verify_rk0_independent.py` 的 `verify(RK0_NEW, PARENT_M2M3_FROZEN/M2_FROZEN)` 函数，独立核查已有缓存、响应核与结果。它不运行该脚本的生产器，也不新增 LOS 核计算。

当同时指定显式包外新 `--out` JSON 文件时，还执行 `PRO_REVIEW/independent_scalar_readout_check.py` 的 `run(parent,out)` 纯算术复核。两份预先保存的 canonical CSV 被复制至包外新 scratch，使原脚本按原路径读取参考表；脚本及包内表不改动。Scratch 名为输出 JSON 文件 stem 加 `_pro_scalar_scratch`，复核产生的表仅写到该新目录。没有 `--out` 时，PRO 复算明确标记未执行，RK0 深核验仍执行。

深核验之后重新校验所有成员哈希与覆盖范围，保证包内证据保持不变。禁止字节码生成。标准输出是 JSON；`--out` 是包外新 JSON 文件，不能使用包内路径或覆盖已有文件。

示例：

```text
python -B verify_review_bundle.py --package . --deep --out ../rk0_fresh_verification.json
```

成功退出码为 0，失败为 1。核验未通过时，显式安全的包外 `--out` 仍会记录失败 JSON。

## 本次软件验收

最终源码在 `REVIEW_BUNDLE_VERIFIER_QA_V3.json` 的 22 项 fixture 软件检查全部通过；物理调用和生产器调用均为 0。覆盖原 19 项默认完整性、嵌套清单、深核验函数边界、PRO 包外 scratch、路径安全、清单漏项、重复路径、外部输出与禁止覆盖，并增加真实超过 300 字符的 Windows 成员路径及嵌套清单、普通路径与 extended-path 包内输出拒绝一致性、超过 260 字符的包外新输出路径。小 fixture 只验证核验器的软件行为，不代表真实 RK0 数值已在此处再次核验。

Windows 文件操作统一使用 canonical `\\?\` extended path（UNC 使用对应 extended UNC），且根目录、嵌套清单及显式外部输出使用相同规范再做包含检查。前缀在严格 resolve 之前添加，因此长路径 lstat/walk/hash 不受默认 MAX_PATH 限制；清单成员仍禁止绝对或 extended 路径，不削弱原来的成员路径安全规则。

另有既有真实成员清单的只读兼容检查：11 份清单、2586 项成员声明通过，记录于 `EXISTING_MANIFEST_VERIFIER_QA.json`。未调用旧版本限制的联合复核器，也未改动旧证据。最终完整交付包仍应由主进程打包后实际运行本核验器验收。

旧 16 项和 V2 的 19 项软件 QA 记录保留，不被覆盖。真实第一版 ZIP 的 Windows 长路径失败记录也应保留；它是核验器路径兼容性问题，不是数值或科学判决变化。最终版本以 V3 的冻结源码哈希为准，科学核验脚本、响应核和实验结果均未修改。
