# 项目进度更新 — 2026-07-08

## 最新进展

### 1. 方法框架：GBI-GSL（广义贝叶斯气体源定位）

**核心创新：**
- 首次将GBI（Bissiri 2016, JRSS-B）引入UAV GSL
- 用loss function替代misspecified Gaussian plume likelihood
- Wind-confidence-gated自适应学习率 η
- Logistic检测概率模型（替代指数衰减）
- 双向cross-wind探索策略
- UAV自适应高度选择

### 2. 实验结果（10-seed）

| 场景 | OPGSL均值(m) | OPGSL标准差 | 成功率 |
|------|-------------|------------|--------|
| H01_gnd | 1.55 | 0.61 | 80% |
| H01_air | 1.99 | 0.27 | 70% |
| H02_air | 1.42 | 0.47 | 90% |

**基线对比（H01_gnd, 10-seed）：**
- OPGSL: **1.55m** 
- SurgeCast: 3.15m
- GrGSL: 4.27m

### 3. 正在进行
- 160次完整基准测试（4场景×4方法×10种子）
  - 场景：H01_gnd, H01_air, H02_air, H03_gnd
  - 方法：OPGSL, SurgeCast, GrGSL, PMFS
  - 预计耗时：~16小时
  - VM脚本：`/tmp/run_isj_v2.py`
  - 结果：`/tmp/v8_exp/isj_full/results.csv`

### 4. 代码状态
- VM代码：commit 9d819d3（GBI框架+双向cross-wind）
- 本地仓库：commit 4b196521
- GitHub：https://github.com/kris-yun/cp-sbd-gsl (私有)

### 5. 文档更新
- 开题报告已更新至GBI框架版本
- 项目交接文档：`docs/PROJECT_HANDOFF.md`
- 多Agent审查报告：`docs/MULTI_AGENT_REVIEW_20260703.md`

### 6. 关键文件路径
- GSL算法代码（VM）：`/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/`
- Launch文件（VM）：`/home/zyc/gsl_ws/src/vgr_bridge/launch/`
- 实验结果（VM）：`/tmp/v8_exp/`
- 开题报告（本地）：`D:\ZYC\A-gas\ASCi\开题报告_最终版_v2.docx`
