content = r"""\documentclass[11pt]{article}
\usepackage{amsmath,amssymb,amsthm}
\usepackage[margin=1in]{geometry}
\newtheorem{theorem}{Theorem}
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{proposition}[theorem]{Proposition}
\newtheorem{corollary}[theorem]{Corollary}
\newtheorem{definition}[definition]{Definition}
\newtheorem{remark}[theorem]{Remark}
\begin{document}
\title{ED-Bayes: Formal Mathematical Framework v3}
\author{Upgraded per ISJ Editor Review}
\date{\today}
\maketitle

\section{Problem Setup}
Let $\mathcal{X}\subset\mathbb{R}^2$ be the bounded search domain.
Unknown source $s^*\in\mathcal{X}$. At step $t$, UAV at $x_t$ acquires binary detection $d_t=\mathbb{1}\{z_t>\tau\}$ and wind $w_t$.

Poisson filament arrival rate:
\begin{equation}
\lambda(x,s)=\lambda_0\exp(-\|x-s\|/\ell)(1+\alpha_w\cos\theta(x,s,w))
\end{equation}

Binary event likelihood:
\begin{equation}
P(d=1|x,s)=1-e^{-\lambda\Delta t},\quad P(d=0|x,s)=e^{-\lambda\Delta t}
\end{equation}

\section{Identifiability}

\begin{definition}[Fisher Information Matrix]
For source candidate $s$ and observation position $x$:
\begin{equation}
\mathcal{I}(s;x)=\mathbb{E}\left[\left(\frac{\partial\log P(d|x,s)}{\partial s}\right)\left(\frac{\partial\log P(d|x,s)}{\partial s}\right)^\top\right]
\end{equation}
\end{definition}

\begin{definition}[Identifiability Coefficient]
\begin{equation}
\kappa_{\mathrm{id}}(s,r)=\inf_{\|s'-s\|\leq r}\lambda_{\min}\left(\int_{\mathcal{X}}\mathcal{I}(s';x)\,dx\right)
\end{equation}
\end{definition}

\begin{lemma}[Non-degenerate Identifiability]
Under $\|w\|>0$, $\lambda_0>0$, for any $s\in\mathcal{X}$ and $r<r_{\max}=\ell\cdot\log(\lambda_0/\epsilon)$:
$\kappa_{\mathrm{id}}(s,r)>0$.
Moreover, $\kappa_{\mathrm{id}}$ decays as $\exp(-r/\ell)$.
\end{lemma}

\section{Event-Driven Expected Information Gain}

\begin{theorem}[ED-EIG Quantitative Lower Bound]
\label{thm:eig_bound}
Let $\pi_t$ be non-degenerate with $\pi_t(s_i)\geq\underline{p}>0$ for $i=1,2$.
For any probe position $x$:
\begin{equation}
\mathrm{ED\text{-}EIG}(x|\pi_t)\geq
\underline{p}(1-\underline{p})\cdot\frac{(\lambda(x,s_1)-\lambda(x,s_2))^2\Delta t^2}{2}\cdot e^{-\max(\lambda(x,s_1),\lambda(x,s_2))\Delta t}
\end{equation}
When $\lambda\Delta t\in[0.5,3]$, ED-EIG achieves maximum.
When $\lambda\Delta t\to 0$: bound scales as $O(\Delta t^2)$.
\end{theorem}

\begin{remark}[Comparison with Continuous Model]
Under continuous model $z=\bar{C}+\varepsilon$, when $z\approx 0$:
$I(s;z|x)\approx 0$.
Under event model, when $d=0$:
$I(s;d=0|x)\geq(\lambda(x,s_2)-\lambda(x,s_1))\Delta t\cdot e^{-\lambda_{\max}\Delta t}>0$.
Binary model maintains positive information in zero-concentration regimes.
\end{remark}

\section{Non-Detection Information}

\begin{theorem}[Non-Detection Information Bound]
\label{thm:nondet}
Let $\pi_t$ be the current posterior. At position $x$ observing $d=0$:
\begin{equation}
I(s;d=0|x,\pi_t)=\mathrm{KL}(\pi_t\|\pi_t^{(0)})=\int\pi_t(s)\log\frac{\pi_t(s)}{\pi_t^{(0)}(s)}ds
\end{equation}
where $\pi_t^{(0)}(s)\propto\pi_t(s)e^{-\lambda(x,s)\Delta t}$.
Moreover:
\begin{equation}
I(s;d=0|x,\pi_t)\geq\frac{(\mathbb{E}_{\pi_t}[\lambda]-\mathbb{E}_{\pi_t^{(0)}}[\lambda])^2}{2\sup_s\lambda(x,s)}
\end{equation}
When $x$ is near high-probability region: $I\sim O(\lambda_{\max}\Delta t)$,
far exceeding continuous model's $I\sim O(z^2)\approx 0$.
\end{theorem}

\section{Posterior Convergence}

\begin{definition}[Posterior Distinguishability]
$D(\pi)=\max_{s_1,s_2\in\mathrm{supp}(\pi)}\|\lambda(\cdot,s_1)-\lambda(\cdot,s_2)\|_{L^2(\mathcal{X})}$
\end{definition}

\begin{theorem}[Adaptive Exponential Contraction]
\label{thm:contraction}
Let $\pi_t$ be the ED-Bayes posterior, $R_t=\mathrm{diam}(\mathrm{supp}(\pi_t))$.
There exist $c_1,c_2>0$ such that:
\begin{equation}
\mathbb{E}[R_t^2]\leq R_0^2\cdot\exp\left(-c_1\sum_{k=0}^{t-1}D(\pi_k)^2\cdot\Delta t\right)+c_2/\sqrt{N}
\end{equation}
Rate adapts to posterior geometry:
\begin{itemize}
\item Early ($D$ large): fast exclusion, rate $\sim e^{-c_1 D_0^2 t}$
\item Late ($D\to 0$): fine discrimination, rate $\sim e^{-c_1 d^2 t}$
\item Floor: bounded by sensor resolution $c_2/\sqrt{N}$
\end{itemize}
\end{theorem}

\section{Anytime-Valid Stopping}

\begin{theorem}[Posterior e-process]
\label{thm:eprocess}
Define likelihood ratio process:
\begin{equation}
M_t=\prod_{k=1}^{t}\frac{P(d_k|x_k,\hat{s}_k)}{P(d_k|x_k,s_0)}
\end{equation}
$M_t$ is an exact martingale under $H_0$: $\mathbb{E}_{s_0}[M_t]=1$.
By Ville's inequality: $\mathbb{P}_{s_0}(\exists t: M_t\geq 1/\alpha)\leq\alpha$.
\end{theorem}

\section{Fundamental Limits}

\begin{proposition}[Convergence Phase Transition]
When $R_t<\ell$, a phase transition occurs:
\begin{itemize}
\item $R_t>\ell$: exponential contraction
\item $\delta<R_t<\ell$: polynomial contraction
\item $R_t\sim\delta$: grid-limited floor
\end{itemize}
Critical distance $r^*=\ell\cdot\log(2)/\log(1+\lambda_0\Delta t/\ell)$
is the theoretical localization accuracy lower bound.
\end{proposition}

\end{document}
"""

with open("D:/ZYC/A-gas/docs/MATHEMATICAL_FRAMEWORK_V3.tex", "w", encoding="utf-8") as f:
    f.write(content)
print("MATHEMATICAL_FRAMEWORK_V3.tex written")