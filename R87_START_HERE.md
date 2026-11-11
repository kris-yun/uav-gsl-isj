# R87 三模块耦合 · Codex 执行入口（2026-11-10）

**完整代码与原生开发数组**：Google Drive（用户账号私有）
https://drive.google.com/file/d/1pKG2D0ORaQqrjFwSifJMD6lvMOSC3y9v/view?usp=drivesdk

**SHA-256**: `39944d5e6355da41a8dcb99b009a428506e0a950b788cb25e2c9b066822c114b`
**大小**：832,660 bytes，23项ZIP文件，已在独立目录解压并重跑全部接口测试。
此GitHub分支只是稳定的下载与交接入口；原R81源码/权重尚存于Codex本地而非本GitHub仓库，勿覆盖旧main。

## 技术路线（一次只测这一个组合）
M1：训练源跨集合图源条件接触（STGNP 2023思想，非官方全模型；强普通8NN/Platt参照）。
M2：条件离散HSMM持续状态（Koslik 2025 + Jackson 2026参考）+ 同一原R81 Ensemble Transformer上状态条件Hurdle发射，使用完整带噪观测共享Q/b NLL。
M3：留源折外凸后验Stacking（Yao et al. 2018思想）+ 全域8837候选MBR，混合已冻结R74，不乘两套同气体证据。

## 已完成的**真实**实验
House01：160物理源×两次释放，两条同释放受体视图，四折留源。M1接触事件NLL：
primary：8NN .133169，Platt **.124187**，低容量GraphResidual .133012；
alt：8NN .136725，Platt **.126645**，GraphResidual .136863。
**图残差没有胜过普通校准，不能宣称其升级成立。**
严格不能与R81 NEW12约1m的正式ET+NLL / PES定位比较。

## R81正式集成要求
1. 下载ZIP后阅读 README_START_HERE.md、THEORY.md、PROTOCOL_8_ARM.md、R87_SEND_TO_CODEX.txt。
2. 从本地R81真实checkpoint导出同四折/种子/受体视图的完整ET成员缓存，并与原R81共享Q/b似然独立对齐（每个缓存必须有parity文件）。禁止R86 2epoch小网络或KNN伪装ET。
3. 原160源内120/40外折，120源内96/24选择Epoch，M3只能在真正留源OOF拟合，不得用外折标签。
4. A0原ET；A1 ET+M3；A2独立接触状态Hurdle；A3普通持续；A4 KL约束持续；A5图条件＋A4；A6 A4+M3；A7完整三模块。统一完整8837格、同源、同概率先验、同欧氏MBR，另报球读出/MAP、改对改错及rank。
5. 先验证模块效果，不新增GADEN仿真，不读取保护集；完整负结果不可删除。
6. 本次ZIP已有可运行M1真实四折和积分等数值代码；**尚无原ET正式八臂的XYZ结果**。Codex必须完成后单独封存，不得沿用R86约2m数字。
