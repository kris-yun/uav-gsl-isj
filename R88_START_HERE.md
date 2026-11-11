# R88 三模块实验：实际修复包与 Codex 入口（2026-11-10）

**这是 R87 的严格安全补丁，不是重训练/重命名原来的 R81 Ensemble Transformer。** 请先下载完整包，再按包内 `R88_SEND_TO_CODEX.md` 执行。保持旧 `main` 不动。

## 下载（用户私有 Google Drive）
- [R88 完整正式执行包（894,025 bytes，36个文件）](https://drive.google.com/file/d/13RsMa7LEy-tCF-wR1GnQ0EBJbyyXrc46/view?usp=drivesdk)
  - SHA256: `17498f41a5e1d27115d1c2ccc636bd86ef53ed80822f9bd32c5b8462019444a3`
- [R88 代码精简包（48,047 bytes）](https://drive.google.com/file/d/1RZ6Yky69fNbCsFTqrgI1of0kvUvkIFAL/view?usp=drivesdk)
  - SHA256: `014790caea39b913c04f8f090208a42414910b8b77a1a7bd1fb9203e84021283`

## 实际修复
1. 原R81完整8,837候选×每条外折观测logE/后验/1m球/MAP/MBR/rank与XYZ的**独立 G0 前置硬门**；没有R81权重和原官方参考不得启动新臂；检查源码 `r87/parity.py`。
2. 正式 A2–A7 使用120个训练源LOO拟合的 **Platt-8NN**；A5/A7 图残差叠加在Platt上，不再拿未校准8NN当底座。
3. M3 A1/A6/A7 **各自训练与保存OOF权重**，检验内层源分组，不能共用w。
4. 固定主要XYZ/同决策比较和预注册CI：新方法－原方法<0为改善，**置信区间上界<0**，源级bootstrap、Holm和Bonferroni；正式A0–A7另加等容量C0。
5. 代码冷解压后运行 `python verify_release.py` 已通过全部哈希、单元测试和接口测试。

## 新M1真实留源结果（仅事件，不是XYZ）
| 视图 |8NN NLL| Platt |GraphOnPlatt|
|---|---:|---:|---:|
|primary|0.133169|0.124186|0.123798|
|alt|0.136725|0.126645|0.126324|

图相对Platt的源级95%CI均跨零；不能借此宣称三模块在XYZ上已成功。正式原ET权重仍在Codex本机，不在此包。必须完成G0原方法对齐才能产生正式A0—A7后验和结论。

## 交付顺序
- 阅读 `README_START_HERE.md`, `CHANGES_R87_TO_R88.md`, `G0_R81_REFERENCE_SCHEMA.md`, `M3_OOF_SOURCE_PROOF.md`, `PROTOCOL_8_ARM.md`, `R88_SEND_TO_CODEX.md`。
- 在独立目录运行 `python verify_release.py`。
- 由Codex从**真正R81官方原实现**导出 full-grid 冻结参考和ET成员（禁止生成假官方参考），导出已冻结R74相同观测后验，分别拟合A1/A6/A7留源OOF。
- G0 PASS 才跑 A0—A7＋C0＋R74，统一8837格/欧氏MBR，并对全部强基线报告固定球与MAP。
- 用 `experiments/evaluate_preregistered.py` 生成源级统计。OLD160/NEW12均是已见开发数据，不能称独立TEST。所有失败保留。

**本GitHub分支是只读交接，不修改原 `main`，完整代码和数据在上述Drive ZIP中。**