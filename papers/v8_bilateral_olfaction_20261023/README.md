# UAV GSL V8 — 研究讨论稿

**双侧镜像嗅觉与主动反证驱动的无人机气体源概率定位**

本工程是原`UAV_GSL_overleaf_minimal.zip`的独立重构副本，沿用原《自动化学报》类文件。日期：2026-10-23。不是投稿定稿；没有重新训练算法或运行大规模仿真。

## 阅读入口

- `main.pdf`：实际XeLaTeX编译的论文。
- `main.tex`：主文件；正文为`sections/`中的六个章节文件，第3、4章共用一个方法文件。
- `verification/V8_Review_and_Verification.pdf`：修改对照、证据边界、参考文献逐项核验、团队论文阅读与审稿视角完整性审查。
- `CHANGELOG.md`：原稿与新稿的章节/公式/图文修改对应。
- `verification/KEY_UNPROVEN_CLAIMS.md`：尚待验证的命题。
- `verification/evidence/`：已发生结果的只读收据及SHA清单。
- `references.bib`：可维护书目；`references.tex`为按正文首次引用顺序生成的AAS文献表。
- `editable_figures/`：原PPTX与新增TikZ源图。图中是算法示意，不是优胜曲线。
- `provenance/`：原稿主文件及修改来源记录。

## Overleaf编译

上传完整工程，选择`main.tex`为主文件，编译器选**XeLaTeX**。标准TeX Live/Overleaf的`ctex`、`xeCJK`及Fandol字体即可；没有Windows专属字体路径。PDF图已生成，论文编译不依赖LibreOffice或Python。

本地标准TeX Live完整安装可运行：

```bash
latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex
```

修改参考文献后，先运行`python3 scripts/build_references.py`再编译。脚本只支持本工程提供的花括号BibTeX字段格式，不宣称为通用BibTeX实现。新增引用会检查未定义键。

图3—5可在`editable_figures/`中单独以XeLaTeX编译相应`.tex`，再复制输出至`figures/`对应文件。图2校正层依赖保留的`fig2_pmfs_original.pdf`。已有PDF图足以完成Overleaf论文编译，无须重新导出PPTX。

## 研究边界

冻结方法/原生记录提交：`061ecf5ddea0a59dcf932b5038ad646b7af454a4`。两源、四个独立DEV世界、粗采样理想浓度条件下，普通单点与完整双点均4/4，M1为2/4、平均MAP误差2.427061 m；通道选择提前饱和，动态镜像通道数为0。原生M2/M3闭环和完整S2湖岸验证未完成。软件71项测试和1200项读出回归来自冻结记录，不是本轮再次运行。

原始ZIP未覆盖。旧CREL/TSDC/PIP仅保存在溯源文件中，不再作为新稿正式三创新。所有团队论文仅用于结构学习，交付包不转发其全文。

独立“小论文撰写要求PDF”未找到，不能宣称逐条遵循。当前保留AAS格式作为中文研究底稿；双盲、AI辅助使用限制、目标期刊最终规范及科研作者责任仍需定稿时检查。公开代码链接可能透露研究身份，本稿不是已经认证的匿名送审文件。

## 独立源码分支

仓库：`kris-yun/uav-gsl-isj`；分支：`paper/v8-bilateral-olfaction-research-20261023`；工程目录：`papers/v8_bilateral_olfaction_20261023/`。该分支以冻结提交`061ecf5ddea0a59dcf932b5038ad646b7af454a4`为父提交，仅新增论文、图形和审查记录。原方法代码与实验结果不在本次改动范围。PDF与完整工程随交付包提供；源码分支保留编译所需PDF图及可编辑源。

核验报告可在`verification/`目录以XeLaTeX编译`V8_Review_and_Verification.tex`。如果更新核验表或叙述，先从工程根目录运行`python3 scripts/build_review.py`（需要Pandoc），再编译报告。正文编译不需要Pandoc。
