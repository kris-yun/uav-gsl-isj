# METHOD_FRAMEWORK_V2：编辑与讲解说明

## 交付及来源

本次直接导入 `docs/METHOD_FRAMEWORK_V1.pptx`，在原生对象上编辑第 1 页和原第 2 页，并在两者之间增加训练／部署隔离页。最终三页均为 PowerPoint 原生形状、文本框和连接线。没有将整图截图贴入幻灯片。

用户提供的 PMFS 原图仍保存在 `docs/source/PMFS_ORIGINAL.pptx`。V1 保留的原图四区布局、地图格点、障碍物、轨迹及主要箭头继续沿用；原第 2 页变成 V2 第 3 页。

| 文件 | SHA-256 |
|---|---|
| PMFS_ORIGINAL.pptx | `95cb24f31f63a7003d598f20896c1207d95eb14f77a378dc80915c9491984af6` |
| METHOD_FRAMEWORK_V1.pptx | `740cd762775f31a0858eb953179a08c964db5532a5e362fa6b4d642cfc50fb13` |
| METHOD_FRAMEWORK_V2.pptx | `8190ba5336a6bb943997b7cf211a0905b2b76ce60a088742309ea5b55a213f95` |

## 第 1 页：任务闭环

保留 PMFS 的二维源位置概率地图和主动概率定位任务。灰色为输入与任务目标，蓝色为 M1，绿色为 M2，橙色为 M3。外部闭环表示原始气体和局地风观测按唯一 ID 回流账本。

M1 标为“合法历史投影的源证据蒸馏”，它是 V1 源证据微分监督路线的信息集适配。物理状态库是**仅训练使用的教师资产**，不能在部署时读取真实未来风场。按候选源过滤历史后，以完整历史与过去历史的 log-evidence 之差构造条件证据；学生学习共享的归一化联合观测分布。

M2 诊断网络只提出机制及变点候选，撤销旧后缀后重新计算证据。诊断预测不能再乘一次作为新观测。源—机制联合后验对机制边缘化，得到二维源概率地图。

M3 从同一 M1 模型获取未来联合样本，以相关软码本、误拒风险和反证功效选择动作块。低后验候选保留可恢复入口。风险界依赖模型与所选不确定集合的有效性，图中没有宣称在任意真实失配下获得无条件保证。

地图颜色和源点均为方法示意，不能作为实验定位结果展示。

## 第 2 页：训练信息、部署信息与数据资格

教师允许在训练期访问仿真物理特权、源标签及完整状态；必须先按每个候选源计算学生历史下的过滤分布，再监督源对证据。双项公式避免把已经用于过滤的历史重复计数。连续源梯度只在教师可微、支持条件和边界项合格时开启；否则使用明确的端点证据版本。

部署学生接收合法历史、相对源与障碍几何、动作和机制候选。实现采用因果 GRU 与轨迹级混合潜变量，输出气体—局地风的归一化联合分布。`log_prob` 和 `sample_future` 来自同一模型；未来采样在整段轨迹保持同一模式，不逐时刻独立重抽潜变量。缺测气体／风通过掩码删除当步读出密度项，而不是补成真实测量；GRU按mask更新，不声称对缺测值影响的整段隐藏状态做了精确积分。

House02 当前可联通记录没有局地风，时间资格是 `record_index`。该资产允许离线数值学习与接口检查；不能直接作为原生主动定位模型的部署资格。其他 House、独立风场与独立 plume realization 的学习需要按数据合同重新资格检查。

图中明确保留 **原生 3D 教师训练资格 BLOCKED**。S2 独立场景及 ROS／GADEN／飞行是后续资格验证阶段，不能把受控 demo 的结果写成其收益。

## 第 3 页：模块接口与独立消融

M1 的历史似然接口供 M2 更新和回放，未来联合分布接口直接供 M3 软码本和动作规划。M2 的联合后验供 M3 维护挑战列表。新的反证判决只触发诊断与规划，原始观测仍只入账一次。

应保留三类独立消融：

- M1：同容量联合 NLL、直接特权蒸馏、正确投影但仅 NLL、投影源对证据及合格连续梯度。
- M2：相同冻结 M1 下，回放关闭／开启，保持同一账本和先验。
- M3：相同 M1／M2 下，与普通联合 EIG 比较，固定行动预算和合法动作集合。

## 算法出处及创新边界

V1 的 M1 母路线保留随机微分／不连续边界采样；V2 用部分可观测特权学习的belief投影，以及Compositional SBI的有条件／先验修正score组合思想纠正教师目标；SBI原文不含HMM，此处不直接套其完全观测Markov分解。这里的 Bayes 积分、Fisher identity、logsumexp、GRU 和混合密度都是已知方法。拟研究的二次创新是气源条件过滤、联合传感器观测、源对证据监督及恢复／规划接口的具体链条；论文贡献必须由独立消融成立。

已核验的新增母文献详见 `docs/literature/MOTHER_METHOD_AUDIT.md`，具体可实施算子详见 `docs/literature/PROJECTED_SOURCE_EVIDENCE_OPERATOR.md`。

核心一手链接：

- [HIB，CoRL 2024，PMLR 2025 出版](https://proceedings.mlr.press/v270/he25a.html)：历史表示的瓶颈和特权对齐；不等于源似然比保证。
- [MIST-WM，ICML 2026](https://proceedings.mlr.press/v306/feng26aa.html)：任务门控和因子条件轨迹对；静态气源不能照搬可干预因子保证。
- [Privileged POMDP，NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/hash/74d188c51d97fcfbc0269f584d6a53b7-Abstract-Conference.html)：历史不可唯一恢复隐藏状态时，oracle 动作蒸馏可失败；先处理合法 belief。
- [Compositional SBI，ICLR 2025](https://arxiv.org/html/2411.02728v2)：局部score组合要校正条件／先验，HMM不在原方法范围；本项目改为源条件潜态bank的两次边缘证据差。
- [TWIST，ICRA 2024](https://twist-sim2real.github.io/)：同动作想象轨迹蒸馏的直接迁移基线。
- [LANO，AAAI 2026](https://ojs.aaai.org/index.php/AAAI/article/view/37001)：部分场补全基线，不能把场误差下降等同于源定位收益。

## 可编辑性和验证收据

三页总计 **764 个原生形状、41 条原生连接线、0 张图片**。V1 第 1 页的 690 个不同原生对象名称在 V2 第 1 页全部保留；V1 第 2 页的 53 个不同对象名称在 V2 第 3 页全部保留。名称检查佐证直接编辑，不能单独代替视觉检查。

已逐页渲染并检查三页。结构包、版面、字体策略、artifact-tool 重新导入检查均通过：**0 错误、0 警告**。输出尺寸沿用 V1 的 1600×1000 设计坐标（16:10）。保留 Arial／Noto Sans CJK SC 字体策略；目标电脑若缺中文字体应先安装同等字体并检查换行。

收据：

- `docs/METHOD_FRAMEWORK_V2_validation.json`：原始 finalizer 收据；其中最终文件名是验证时的 `METHOD_FRAMEWORK_V2_r4.pptx`。
- `docs/METHOD_FRAMEWORK_V2_editability_audit.json`：原始底稿、对象计数与字节一致性记录。
- 经验证的 r4 文件逐字节提升为 `docs/METHOD_FRAMEWORK_V2.pptx`，SHA-256 完全相同。

没有在原生 Microsoft PowerPoint 应用内执行打开／编辑测试。未宣称所有目标系统的字体渲染完全一致。

## 重新生成

生成脚本：`docs/build_framework_v2.mjs`。它必须在已配置 artifact-tool 的主运行时执行，读取真实 V1 底稿；不是项目科学推断的运行依赖。

```bash
PPTX_NAME=METHOD_FRAMEWORK_V2_new_revision.pptx \
PPTX_CJK_FONT=/absolute/path/NotoSansCJKsc-Regular.otf \
"$CODEX_PRIMARY_RUNTIME_NODE" docs/build_framework_v2.mjs
```

脚本需要 `CODEX_PRIMARY_RUNTIME_NODE_MODULES`、`CODEX_PRIMARY_RUNTIME_PYTHON` 和已安装的 Presentations finalizer。每次用新输出文件名，随后完成渲染检查和校验；不要绕过 finalizer 覆盖未验证文件。

附带预览：`METHOD_FRAMEWORK_V2_preview.png`、`METHOD_FRAMEWORK_V2_training_preview.png`、`METHOD_FRAMEWORK_V2_interfaces_preview.png`。预览只用于查看，正式可编辑交付是 PPTX。


**实现归因补充：** HIB 的 cosine/IB 对齐、MIST-WM 的门控/InfoNCE 与探索技能均未在 V2 实现；它们仅作为动机或待实现强基线，不计为已完成的直接母算法迁移。
