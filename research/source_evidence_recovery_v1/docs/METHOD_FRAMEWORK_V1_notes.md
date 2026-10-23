# METHOD_FRAMEWORK_V1：可编辑方法图与讲解备注

## 文件与来源

- 成品：`METHOD_FRAMEWORK_V1.pptx`，2 页，尺寸 1600 × 1000 px，延续原图 16:10 比例。
- 原文件：用户上传的 `pmfs原方法图.pptx`，实际导入后编辑；没有使用无法访问原图时的重绘替代方案。
- 原文件 SHA256：`95cb24f31f63a7003d598f20896c1207d95eb14f77a378dc80915c9491984af6`。
- 成品 SHA256：`740cd762775f31a0858eb953179a08c964db5532a5e362fa6b4d642cfc50fb13`。
- 第一页保留原图四分区结构和 685 个原有对象名称，包括原生栅格、障碍、路径及主要闭环连接结构。原有对象经有意编辑，不以名称保留比例代替视觉核验。
- 第一页包含 672 个原生形状、18 条原生连接线；第二页包含 52 个原生形状、16 条连接线。两页均 **0 张图片**。全部文本、框、栅格和箭头可以在 PowerPoint 中编辑。
- 原图未修改。中文补充采用 Noto Sans CJK SC，原图保留文字使用 Arial；原图的无衬线风格、圆角分区、浅色背景和白底保持一致。
- 预览：`METHOD_FRAMEWORK_V1_preview.png` 为总图；`METHOD_FRAMEWORK_V1_detail_preview.png` 为接口图。预览仅用于浏览，正式图在 PPTX 中仍为原生对象。

## 原 PMFS 图与新图的逐区映射

| 原图位置和内容 | 新图内容 | 保留 / 修改说明 |
|---|---|---|
| 左上 a：测量环境、二值事件、机器人位置、派生检出地图 | 原始输入与唯一观测账本 | 保留传感器、路径、障碍示意；输入明确包括候选源、局地风和动作历史；不把派生地图当作额外独立观测 |
| 右上 b：风场估计、二维 filament 前向仿真、候选源检出地图 | M1 源证据微分监督联合观测生成器 | 在原有“条件—前向—源响应”布局中换入风保持约束、源证据微分监督、历史联合似然及未来联合采样 |
| 左下 c：置信加权逐格比较、乘积归一化、源概率图 | M2 机制差分诊断与可撤销证据回放 | 原“实测—预测”比较行改为“实际观测—名义参考”；中心改为旧后缀撤销与新机制回放；右侧保留二维源概率图输出 |
| 右下 d：原生下一采样点价值函数 | M3 容错反证主动规划 | 保留原路径和主动下一动作输出；增加软联合码本、误拒风险约束、最坏反证功效和可恢复候选列表 |
| 底部闭环反馈 | 执行动作块、新气体/局地风观测、唯一 ID 入账 | 保留原生主动概率定位闭环；不把方法限制为固定路线概率估计 |

灰色代表 PMFS 保留的任务和输出目标；蓝色对应 M1；绿色对应 M2；橙色对应 M3 及主动闭环。图中地图均为结构示意，**不是实验结果**，颜色不表示本项目已取得的定位性能。

## 第 1 页讲解建议

> 我们保留 PMFS 的二维源概率地图与主动定位闭环，重构内部证据计算。M1 既生成未来联合观测，也学习“源位置变化如何改变当前观测证据”；M2 在源与机制解释冲突时撤销旧后缀贡献并重新回放；M3 根据完整软码本主动寻找有功效的反证动作，同时给低后验候选保留恢复机会。三者共用原始观测账本，所有观测只计入一次。

不要把图中的物理教师称为“原生 GADEN 已完成”。完整工程状态由 `IMPLEMENTATION_AUDIT.md` 和对应测试收据界定。受控后端的数学检查不等于真实 House / 湖岸泛化性能验证。

## 第 2 页接口说明

1. **M1 → M2**：`log_prob(history, source, mechanism)` 返回同一正规化联合模型的历史似然。机制诊断参考由同一个源条件模型产生。
2. **M1 → M3**：`sample_future(history, actions, source, mechanism, rng)` 生成未来气体与局地风的整块联合观测。不得以未来真实风或真实响应库替代此接口。
3. **M2 → M3**：源—机制联合后验及机制版本。机制改变后，旧列表排除结论应失效并恢复检查。
4. **M3 → 账本 → M1/M2**：执行承诺的合法动作块，采集真实观测，以唯一观测 ID 回流；反证测试判决只触发诊断/调度，不作第二份数据再次乘入后验。
5. **M2 → 二维地图**：对机制边际化，`P(s | H) = Σe P(s,e | H)`。此归一化是必要结构，不计作单独算法创新。

## 跨领域母算法及二次创新

| 模块 | 借鉴领域与实际母算法 | 气源定位二次创新 |
|---|---|---|
| M1 | 随机分析：ICML 2025 的 Malliavin/BEL 条件得分学习；逆图形学：SIGGRAPH Asia 2025 的分支边界采样 | 在源扰动方向保持局地风条件不变，并补偿硬分支项，监督竞争源的联合观测证据导数 |
| M2 | 计算生物学：ICML 2025 CDN 的观测/干预图差分与扰动靶点识别 | 源条件名义参照、物理机制与起点提议、后缀回放替换；诊断不是新证据 |
| M3 | 信息论与编码理论：ISIT 2025 的动作条件聚类与分阶段假设检验 | 学习的联合软码本、相关错误集合、风险—功效 LP、机制版本一致的列表恢复 |

这些是待真实数据验证的算法候选。示意图没有把母算法名称等同于已完整复现原作者软件。轻量实现、原生接口和完整复现的差别应继续在审计中公开。

## 核验记录

- 已读取原图全部内容、检查原始渲染，并逐页检查修改后的渲染。
- 已将最终 PPTX 重新导入，再渲染两页进行检查。
- 最终包结构、页数、尺寸、字体声明、文字布局和连接线检查：0 错误、0 警告。
- 具体收据：工程包内应包含 `pptx_editability_audit.json` 和 `METHOD_FRAMEWORK_V1_r2.pptx.validation.json`。
- 未在桌面版 Microsoft PowerPoint 中打开，未声称完成该项测试。

## 一手来源（亦写入 PPT 备注）

1. PMFS 原论文：https://arxiv.org/html/2304.08879v3
2. Conditioning Diffusions Using Malliavin Calculus：https://proceedings.mlr.press/v267/pidstrigach25a.html
3. Automatic Sampling for Discontinuities in Differentiable Shaders：https://yashbelhe.github.io/asd/index.html ，DOI 10.1145/3763291
4. Identifying Biological Perturbation Targets through Causal Differential Networks：https://proceedings.mlr.press/v267/wu25v.html
5. Multi-Stage Active Sequential Hypothesis Testing with Clustered Hypotheses：https://arxiv.org/html/2501.11459v2 ，DOI 10.1109/ISIT63088.2025.11195532

## 构建源码边界

工程包含 `docs/source/PMFS_ORIGINAL.pptx` 原图只读副本与 `docs/build_framework.mjs` 编辑源代码。后者是本次实际构建脚本，路径已改为项目相对路径，依赖 ChatGPT 的 `@oai/artifact-tool`、presentation finalizer 和渲染运行时；不是通用 npm 环境下零依赖的重新构建命令。须设置 `PPTX_CJK_FONT` 指向本机 NotoSansCJKsc-Regular.otf；可选 `PPTX_BUILD_DIR` 和 `PPTX_OUTPUT_DIR`。本工程 Python 训练和测试不依赖该图形构建环境。日常修改可直接在 PowerPoint 编辑成品所有对象。
