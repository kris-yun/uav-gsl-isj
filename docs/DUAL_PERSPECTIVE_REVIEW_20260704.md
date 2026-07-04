% ============================================================
% ISJ审稿人 + 葛泉波教授 双视角深度审核报告
% 日期: 2026-07-04
% 审核对象: Anytime-Valid Stopping for UAV GSL via Bayesian Posterior e-Processes
% ============================================================

% ===================== 视角A: ISJ资深副主编 =====================

\documentclass{article}
\usepackage[UTF8]{ctex}
\usepackage{booktabs}
\usepackage{amsmath}
\usepackage[margin=1in]{geometry}
\begin{document}

\title{双视角深度审核报告：ISJ副主编 $\times$ 葛泉波教授}
\subtitle{UAV GSL 论文投稿可行性评估}
\date{2026-07-04}
\maketitle

% ============================================================
\part{ISJ资深副主编视角}
% ============================================================

\section{六维评分}

\begin{table}[h]
\centering
\begin{tabular}{lcc}
\toprule
维度 & 当前 & 目标 \\
\midrule
科学问题锐利度 & 5/10 & 8/10 \\
方法创新性 & 5/10 & 8/10 \\
理论深度与严谨性 & 4/10 & 8/10 \\
实验充分性 & 3/10 & 8/10 \\
叙事说服力 & 4/10 & 8/10 \\
ISJ匹配度 & 6/10 & 8/10 \\
\midrule
\textbf{总评} & \textbf{4.5/10} & \textbf{8/10} \\
\bottomrule
\end{tabular}
\end{table}

\section{致命问题}

\subsection{问题1: 科学问题太宽泛 (5/10)}
`无formal stopping guarantee'' 是真实的gap，但不是一个 \textbf{锐利的科学问题}。
类比：`SGD没有formal收敛证明''是真实的gap，但不是一个能撑起论文的科学问题。

\textbf{审稿人会问：} `So what? 领域这么多年没有formal stopping也没出问题。
你解决了什么实际痛点？''

\textbf{更好的科学问题应该是：}
`在intermittent plume contact条件下（UAV距源远、信号弱），
现有GSL方法的搜索策略退化为随机游走（Infotaxis）
或完全失效（SurgeCast），
\textbf{且没有任何方法能判断自己是否已经足够接近源而应该停止搜索}。''

这个问题更锐利：有明确的失败场景（弱信号）、有具体的后果（搜索退化+无法停止）、
有实际应用价值（工业巡检中UAV从任意位置出发，多数情况初始无gas接触）。

\subsection{问题2: 理论循环依赖 (4/10)}
Theorem 1 假设 $\inf_t I(x_t, s^*) \geq \kappa > 0$，
但Infotaxis在  \approx 0$ 时所有动作的EIG $\approx 0$，
搜索退化为随机 → 不能保证 $\kappa > 0$。

这不仅是gap，是 \textbf{proof不成立}。审稿人会直接reject。

\textbf{修复方向：}
要么(a)证明在某个具体的搜索策略下$\kappa > 0，
要么(b)设计一个\textbf{保证最小信息增益}的搜索策略，
要么(c)弱化结论，只在plume contact regime下声称收敛。

\subsection{问题3: 实验数据作废 (3/10)}
\begin{itemize}
\item 所有run由FAST EXIT终止，非e-process
\item e-process在原始数据上触发率0\%
\item 只有3 seeds，无法支撑统计声明
\item SurgeCast在2/3环境优于我们
\end{itemize}

审稿人看到这些会直接reject without review。

\subsection{问题4: `Simpler-is-better''不是贡献 (4/10)}
说`加模块反而变差''不是创新，是self-critique。
审稿人会问：`你花了整篇论文告诉我们你加的东西都没用，
那你到底贡献了什么？''

\textbf{需要的叙事转变：}从`我们试了很多，最简单的好''
转变为`我们发现了一个新的物理insight（事件驱动vs连续信号），
基于此设计的方法自然简洁，不需要额外模块''。

\section{审稿人必问Top-10}

\begin{enumerate}
\item \textbf{[必问/致命]} `SurgeCast在House02远超你(0.41 vs 1.91)。
你怎么claim你的方法更好？'' — 当前`consistency''辩护站不住。
\item \textbf{[必问/致命]} `你的e-process在原始实验中0\%触发率。
论文中的数据是不是cherry-picked？'' — 信任危机。
\item \textbf{[必问/严重]} `Theorem 1的$\kappa > 0？
Infotaxis在无gas时EIG=0。'' — 理论不成立。
\item \textbf{[必问/严重]} `只有3 seeds，没有统计检验。
这个experimental protocol在2026年不可接受。'' — 实验不达标。
\item \textbf{[必问/中等]} `e-process和conformal prediction有什么本质区别？
你只是换了工具。'' — 需要更clear的定位。
\item \textbf{[可能问]} `你的方法需要wind信息。
这和SurgeCast有什么根本区别？'' — 需要clear回答。
\item \textbf{[可能问]} `为什么只在VGR数据集上测试？
GADEN呢？'' — 数据集不够。
\item \textbf{[可能问]} `Infotaxis是2007年的方法。
你的贡献到底是什么？'' — 创新性不足。
\item \textbf{[可能问]} `anytime-valid stopping在其他robotics领域已有应用。
你的domain-specific贡献是什么？'' — 需要domain-specific theory。
\item \textbf{[可能问]} `代码和数据是否可复现？'' — GitHub是私有的。
\end{enumerate}

% ============================================================
\part{葛泉波教授视角}
% ============================================================

\section{一句话诊断}

\textbf{`学生把一个工程实现问题（模块加不好）包装成了科学发现（simpler-is-better），
但审稿人不会被骗。真正的科学问题被掩盖了：气体信号的事件本质
与算法的连续信号假设之间的mismatch。''}

\section{创新点评估}

\subsection{当前`创新点''}
\begin{enumerate}
\item e-process用于GSL停止 — \textbf{增量贡献}，
e-process是现成工具(Ville 1939, Ramdas 2023)，
直接套用不算创新。\textbf{评分: 5/10}
\item 后验收敛速率 — \textbf{标准结果}，
贝叶斯渐近理论(Doob定理)的应用，非原创。\textbf{评分: 4/10}
\item 可识别性证明 — \textbf{trivial}，
在wind $\neq 0。\textbf{评分: 3/10}
\item `Simpler-is-better'' — \textbf{不是贡献}，
是实验发现（而且基于作废的数据）。\textbf{评分: 2/10}
\end{enumerate}

\subsection{缺什么}
\begin{itemize}
\item \textbf{缺一个domain-specific的核心insight} — 
师兄做`无人机身份保持''，核心insight是`重叠时ID会变''，
方法针对性强。我们的核心insight是什么？
\item \textbf{缺一个从物理到算法的bridge} — 
气体是filament-based（事件性、间歇性），但我们的算法假设连续信号。
这个mismatch应该被 \textbf{显式地解决}，而不是被忽略。
\item \textbf{缺理论深度} — 
e-process的超鞅性质是标准结果，不是我们的贡献。
我们需要一个 \textbf{GSL-specific的理论结果}。
\end{enumerate}

\section{科学问题重新审视}

\subsection{当前问题: `无formal stopping''}
真实但太宽泛。不是好的切入点。

\subsection{更好的问题: `intermittent contact regime下GSL失效''}
\begin{itemize}
\item \textbf{具体}: UAV距源远+初始无gas → 
SurgeCast失效(3.26m), Infotaxis退化(随机)
\item \textbf{有应用价值}: 工业巡检、灾难响应，
UAV从远处出发是常态
\item \textbf{有物理基础}: filament-based扩散的intermittent特性
创造了这个regime
\item \textbf{有方法学insight}: 
非检测（无gas）也是信息 → 事件驱动贝叶斯
\end{itemize}

\subsection{最优对标: `气体溯源中的事件驱动贝叶斯推理''}
叙事：`气体到达是离散事件（不是连续信号）。我们首次把这一物理事实
嵌入贝叶斯推理框架，利用非检测作为反面证据，并用anytime-valid e-process
提供停止保证。''

\textbf{优势：}
\begin{itemize}
\item 核心insight（事件驱动 vs 连续信号）是domain-specific的
\item 物理模型（filament → Poisson过程）到算法（事件似然）的bridge清晰
\item e-process作为停止保证是技术支撑，不是核心claim
\item 非检测有信息的insight是反直觉的，有论文吸引力
\end{enumerate}

\section{方法方向建议}

\textbf{推荐方向: Event-Driven Bayesian GSL (ED-Bayes)}

\textbf{不推荐HD-Bayes (Hawkes):} 参数估计需要大量数据，
在线估计不稳定，增加复杂度但不一定有收益。
Hawkes聚类假设尚未验证。

\textbf{不推荐WA-DC (双通道):} 核心贡献不清晰，
`用wind做定位''不是新idea（PMFS/SurgeCast都在用）。

\textbf{ED-Bayes的优势：}
\begin{enumerate}
\item 简洁 — 只替换likelihood模型，不改变整体框架
\item 物理一致 — filaments到达就是Poisson过程
\item 非检测有信息 — 解决`无gas时搜索退化''的根本问题
\item 理论可证 — Bernoulli/Bernoulli过程的后验收敛有成熟理论
\item e-process自然适配 — 停止基于后验可信区域，不依赖MAP残差
\end{enumerate}

\section{投稿可行性判断}

\textbf{当前状态: 必拒。}没有任何一个维度达标。

\textbf{达到投稿标准需要:}
\begin{enumerate}
\item 重新设计方法框架（事件驱动贝叶斯） — 2周
\item 修复理论证明（消除循环依赖，加GSL-specific理论） — 1周
\item 在PMFS+VGR数据集上重新跑实验（10 seeds, proper stopping） — 1周
\item 重写论文（新叙事+新数据） — 2周
\item 总计约6周
\end{enumerate}

\textbf{最关键的3件事：}
\begin{enumerate}
\item \textbf{替换likelihood模型} — 从连续高斯到事件Bernoulli
\item \textbf{修复停止准则} — 从MAP残差到后验可信区域
\item \textbf{在弱信号场景证明优势} — House01上2.5×SurgeCast
\end{enumerate}

\end{document}
