# PMFS P0/P1统一合同审核包

先读 `GO_NOGO_zh.md`，再读中文源码审计和指南修订意见。

标准库独立复核：

```text
python verify_core_parity.py --out <新的结果目录>
```

脚本校验675份证据哈希、冻结输入、在线capture输入字节、87个C候选图及repeat、独立重算源评分、粗叶归一化和真源rank。不会执行包内历史shell/C++/launch，不启动前向模拟、ROS或训练。粗叶诊断图明确不是在线最终源图。官方源码/配置固定版本的Git blob检查记录另见 `PINNED_SOURCE_BLOB_CHECKS.json`。

`SOURCE_MANIFEST.json`记录源路径／链接及SHA256，`NUMERICAL_CONTRACT.json`保存本轮数值复算前声明的容差。`SOURCE_MANIFEST`包含源文件而非生成结果；全包生成文件校验见 `SHA256SUMS.txt`。
包内 `.gitattributes` 禁用此审核目录的自动行尾转换，保留原始证据字节；上游源码的既有尾部空格不作格式修复。

冻结的20事件87粗叶是数值核心诊断，不是B1/C1完整场景，也不能扩充为20次独立实验。旧A/B三臂结果已按R2源码随机流纠正，旧47/14排名不再使用。
