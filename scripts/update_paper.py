import os

# Update introduction.tex
intro = r"""\section{Introduction}
\label{sec:intro}

\IEEEPARstart{U}{nmanned} aerial vehicles (UAVs) equipped with gas sensors are promising platforms for autonomous gas source localization (GSL), with applications in industrial leak detection, environmental monitoring, and disaster response~\cite{ref1,ref2}. The fundamental challenge is that gas dispersion is driven by turbulent transport, creating intermittent, filamentary plume structures~\cite{ref3,ref4}.

\subsection{Limitations of Existing Methods}

\textbf{Upwind-tracking methods} (e.g., SurgeCast~\cite{ref5}) track plumes upwind. These achieve excellent performance when the UAV starts within a strong plume (0.4m error), but degrade $8\times$ when the initial signal is weak---a common scenario with arbitrary starting positions.

\textbf{Plume-model methods} (e.g., PMFS~\cite{ref6}, GrGSL~\cite{ref7}) fit parametric dispersion models. When actual dispersion deviates from model assumptions, these methods systematically fail (3--8m error).

\textbf{Information-theoretic methods} (e.g., Infotaxis~\cite{ref8}) maximize expected information gain. While theoretically elegant, they suffer from two fundamental limitations: (1) search degeneration when gas readings are near zero (EIG $\approx 0$), and (2) suboptimal performance in strong-signal regimes where the posterior has already concentrated but the search granularity remains coarse.

\subsection{The Signal Model Mismatch}

A deeper, under-recognized problem unifies these failures: \textbf{existing methods model gas concentration as a continuous signal, but filament-based dispersion produces discrete, event-like detections}. When $z_t \approx 0$ (the common case in weak-signal regimes), continuous-model methods gain almost no information. Critically, the \emph{absence} of detection at a known position carries strong information about source location---it excludes nearby candidates---but no existing method explicitly exploits this.

\subsection{The Search Granularity Problem}

A second, complementary problem emerges in strong-signal regimes. When the posterior has concentrated around the source, information-theoretic methods (Infotaxis) continue computing global expected information gain over the entire domain, wasting computational effort on already-excluded regions. Meanwhile, upwind-tracking methods (SurgeCast) exploit local wind direction for precise convergence but require continuous plume contact. No existing method adapts its search granularity to the posterior state.

\subsection{Our Approach: Event-Driven Posterior-Adaptive GSL}

We address both problems through a three-layer framework:

\begin{enumerate}
\item \textbf{Event-Driven Observation Model (Layer 1).} We model gas detection as binary events from an inhomogeneous Poisson process, replacing the continuous Gaussian assumption. Non-detections carry positive information for source exclusion, preventing search degeneration in weak-signal regimes.

\item \textbf{Posterior-Adaptive Search (Layer 2).} We define a search granularity parameter $\gamma_t = H(\pi_t)/H(\pi_0)$ that measures posterior concentration. The expected information gain is adaptively weighted: $\mathrm{EIG}_\gamma(a) = (1-\gamma)\cdot\mathrm{EIG}_{\mathrm{local}}(a) + \gamma\cdot\mathrm{EIG}_{\mathrm{global}}(a)$. When $\gamma \to 1$ (dispersed posterior), the search prioritizes global information gain; when $\gamma \to 0$ (concentrated posterior), it prioritizes local upwind refinement.

\item \textbf{Anytime-Valid Stopping (Layer 3).} We construct an e-process based on posterior credible region contraction that provides distribution-free stopping guarantees via Ville's inequality, replacing the unreliable MAP-residual approach.
\end{enumerate}

\subsection{Contributions}

\begin{enumerate}
\item \textbf{Event-driven observation model for GSL.} We formalize gas detection as discrete filament-arrival events, showing that non-detections carry positive information for source exclusion. This resolves the signal model mismatch that causes existing methods to fail in weak-signal regimes.

\item \textbf{Posterior-adaptive search granularity.} We prove that the adaptive EIG satisfies $\mathrm{EIG}_\gamma \geq \min(\mathrm{EIG}_{\mathrm{local}}, \mathrm{EIG}_{\mathrm{global}}) > 0$ for any non-degenerate posterior, preventing search degeneration while enabling efficient local refinement when the posterior concentrates.

\item \textbf{Exponential posterior concentration.} Under the event-driven model, the Bayesian posterior concentrates at rate $e^{-\kappa t}$ rather than $O(1/t)$, because the Bernoulli likelihood satisfies stronger identifiability conditions.

\item \textbf{Anytime-valid stopping.} We construct an e-process based on credible region contraction with proven super-martingale property and anytime-valid guarantee (Theorem~\ref{thm:anytime}).
\end{enumerate}
"""

path = r'D:\ZYC\A-gas\ASCi\sci\paper-isj-zh\sections\introduction.tex'
with open(path, 'w', encoding='utf-8') as f:
    f.write(intro)
print('Written introduction.tex: ' + str(len(intro)) + ' chars')

# Update main.tex abstract
main = r"""\documentclass[journal]{IEEEtran}
\usepackage[UTF8]{ctex}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{graphicx}
\usepackage{cite}
\usepackage{algorithmic}
\usepackage{algorithm}
\usepackage{array}
\usepackage{url}
\usepackage{booktabs}
\usepackage{multirow}
\usepackage{bm}
\usepackage{amsthm}

\newtheorem{definition}{Definition}
\newtheorem{proposition}{Proposition}
\newtheorem{theorem}{Theorem}
\newtheorem{lemma}{Lemma}
\newtheorem{remark}{Remark}

\hyphenation{op-tical net-works semi-conduc-tor}

\begin{document}

\title{Event-Driven Posterior-Adaptive UAV Gas Source Localization with Anytime-Valid Stopping}

\author{
\IEEEauthorblockN{Author Name}
\IEEEauthorblockA{Affiliation}
}

\markboth{IEEE Sensors Journal}%
{Author: Event-Driven Posterior-Adaptive UAV GSL}

\maketitle

\begin{abstract}
Unmanned aerial vehicle (UAV) gas source localization (GSL) faces two complementary challenges: (1) existing methods assume continuous concentration signals, but turbulent filament-based dispersion produces intermittent, event-like detections---causing search degeneration when $z_t \approx 0$; and (2) information-theoretic methods use coarse global search even after the posterior has concentrated, wasting effort on already-excluded regions. We propose Event-Driven Posterior-Adaptive GSL (EDPA-GSL), a three-layer framework that addresses both challenges. \textbf{Layer 1} models gas detection as binary events from an inhomogeneous Poisson process, where non-detections carry positive information for source exclusion. \textbf{Layer 2} adapts search granularity to posterior concentration via $\mathrm{EIG}_\gamma = (1-\gamma)\cdot\mathrm{EIG}_{\mathrm{local}} + \gamma\cdot\mathrm{EIG}_{\mathrm{global}}$ with $\gamma = H(\pi_t)/H(\pi_0)$, unifying information-theoretic exploration and upwind refinement as extreme cases. \textbf{Layer 3} provides anytime-valid stopping via an e-process on posterior credible region contraction. We prove: (i) the event-driven EIG is strictly positive for any non-degenerate posterior; (ii) the posterior concentrates at exponential rate $e^{-\kappa t}$ under the event model; and (iii) the e-process provides distribution-free stopping guarantees via Ville's inequality. Experiments on VGR and PMFS datasets demonstrate [X]$\times$ improvement over SurgeCast in weak-signal regimes while maintaining competitive performance in strong-signal regimes.
\end{abstract}

\begin{IEEEkeywords}
Gas source localization, unmanned aerial vehicles, event-driven inference, anytime-valid inference, Bayesian posterior, e-processes
\end{IEEEkeywords}

\input{sections/introduction}
\input{sections/related_work}
\input{sections/methodology}
\input{sections/experiments}
\input{sections/references}

\end{document}
"""

path2 = r'D:\ZYC\A-gas\ASCi\sci\paper-isj-zh\main.tex'
with open(path2, 'w', encoding='utf-8') as f:
    f.write(main)
print('Written main.tex: ' + str(len(main)) + ' chars')
