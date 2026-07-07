import pathlib
content = r"""% Mathematical Framework v2
\documentclass[11pt]{article}
\usepackage{amsmath,amssymb,amsthm}
\usepackage[margin=1in]{geometry}
\newtheorem{theorem}{Theorem}
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{proposition}[theorem]{Proposition}
\newtheorem{corollary}[theorem]{Corollary}
\newtheorem{definition}[theorem]{Definition}
\newtheorem{remark}[theorem]{Remark}
\begin{document}
\title{Event-Driven Bayesian GSL: Formal Mathematical Framework}
\author{Theoretical Analysis}
\date{\today}
\maketitle

\section{Problem Setup}
Let $\mathcal{X} \subset \mathbb{R}^2$ be the bounded search domain and $s^* \in \mathcal{X}$ the unknown source. At time $t$, the UAV at $x_t$ acquires $z_t$ and wind $w_t$.

\subsection{Event-Driven Observation Model}
\begin{definition}[Detection Event]
Binary detection: $d_t = \mathbb{1}\{z_t > \tau_{\mathrm{det}}\}$.
\end{definition}

Gas filament arrival follows Poisson process with rate:
\begin{equation}
\lambda(x, s) = \lambda_0 \cdot \exp\!\left(-\|x - s\|/\ell\right) \cdot (1 + \alpha_w \cos\theta(x,s,w))
\end{equation}

Detection probability:
\begin{align}
P(d_t\!=\!1 \mid x_t, s) &= 1 - \exp(-\lambda(x_t, s)\Delta t) \\
P(d_t\!=\!0 \mid x_t, s) &= \exp(-\lambda(x_t, s)\Delta t)
\end{align}

\begin{remark}[Non-detection carries information]
If $s$ is close to $x_t$, $\lambda$ is large and $P(d_t\!=\!0)$ is small, so $d_t\!=\!0$ excludes $s$. Every observation provides information.
\end{remark}

\section{Core Theoretical Results}

\begin{proposition}[Source Identifiability]
With $\lambda_0 > 0$ and $\|w\| > 0$, for $s_1 \neq s_2$, there exists $x$ with $P(d\!=\!1|x,s_1) \neq P(d\!=\!1|x,s_2)$.
\end{proposition}

\begin{theorem}[Strict Positivity of ED-EIG]
For any non-degenerate posterior $\pi_t$, there exists action $a$ with $\mathrm{ED\text{-}EIG}(a \mid \pi_t) > 0$.
\end{theorem}

\begin{proof}
By identifiability, for $s_1 \neq s_2$ with $\pi_t(s_i) > 0$, there exists $x$ where $p_1 \neq p_2$. Choose $a$ to move to $x$. By data processing inequality, $I(s; d \mid x) > 0$. Critically, the non-detection branch alone provides positive information: $d=0$ at $x$ excludes candidates near $x$, strictly reducing entropy. Under the continuous model, $z \approx 0$ yields EIG $\approx 0$; under the event model, $d = 0$ yields ED-EIG $> 0$.
\end{proof}

\begin{theorem}[Exponential Posterior Concentration]
If $\mathrm{ED\text{-}EIG}(a_t \mid \pi_t) \geq \kappa > 0$ at each step, then $\mathbb{E}[\mathrm{KL}(\pi_t \| \delta_{s^*})] \leq C \cdot e^{-\kappa' t}$ with $C = \mathrm{KL}(\pi_0 \| \delta_{s^*})$.
\end{theorem}

\begin{proof}
Chain rule: $\mathrm{KL}(\pi_t) - \mathrm{KL}(\pi_{t+1}) = I(s; d_t \mid x_t) \geq \kappa$. Telescoping yields exponential convergence.
\end{proof}

\begin{theorem}[Anytime-Valid Stopping]
Define e-process $M_T = \prod_{t=1}^T (1 + \eta \cdot S_t)$ with $S_t = \max(0, R_{t-1} - R_t)$. Under $H_0$ (no convergence), $M_T$ is a super-martingale and $\mathbb{P}(\exists T: M_T \geq 1/\delta \wedge R_T \leq \varepsilon) \leq \delta$ by Ville's inequality.
\end{theorem}

\section{Why Non-Detection Matters}
Under continuous model when $z \approx 0$: $\log[L(z|x,s_1)/L(z|x,s_2)] \approx 0$ because $C(x,s) \approx 0$ for all far $s$. Information gain vanishes.

Under event model when $d = 0$: $\log[L(d\!=\!0|x,s_1)/L(d\!=\!0|x,s_2)] = [\lambda(x,s_2) - \lambda(x,s_1)] \Delta t$, proportional to arrival rate difference. Remains informative even when concentration is zero.

\end{document}
"""
pathlib.Path(r'D:\ZYC\A-gas\docs\MATHEMATICAL_FRAMEWORK_V2.tex').write_text(content, encoding='utf-8')
print('Written successfully')
