import os

content = r"""\section{Introduction}
\label{sec:intro}

\IEEEPARstart{U}{nmanned} aerial vehicles (UAVs) equipped with gas sensors are promising platforms for autonomous gas source localization (GSL), with applications in industrial leak detection, environmental monitoring, and disaster response~\cite{ref1,ref2}. The fundamental challenge is that gas dispersion is driven by turbulent transport, creating intermittent, filamentary plume structures~\cite{ref3,ref4}.

\subsection{Limitations of Existing Methods}

\textbf{Upwind-tracking methods} (e.g., SurgeCast~\cite{ref5}) track plumes upwind. These achieve excellent performance when the UAV starts within a strong plume (0.4m error), but degrade $8\times$ when the initial signal is weak---a common scenario with arbitrary starting positions.

\textbf{Plume-model methods} (e.g., PMFS~\cite{ref6}, GrGSL~\cite{ref7}) fit parametric dispersion models. When actual dispersion deviates from model assumptions, these methods systematically fail (3--8m error).

\textbf{Information-theoretic methods} (e.g., Infotaxis~\cite{ref8}) maximize expected information gain. While theoretically elegant, they lack a principled stopping criterion and suffer from search degeneration when gas readings are near zero.

\subsection{The Signal Model Mismatch}

A deeper, under-recognized problem unifies these failures: \textbf{existing methods model gas concentration as a continuous signal, but filament-based dispersion produces discrete, event-like detections}. When $z_t \approx 0$ (the common case in weak-signal regimes), continuous-model methods gain almost no information. Critically, the \emph{absence} of detection at a known position carries strong information about source location---it excludes nearby candidates---but no existing method exploits this.

\subsection{The Stopping Problem}

A critical, under-studied challenge is deciding \emph{when to stop}. Existing methods use ad-hoc criteria (fixed steps, ``MAP hasn't moved for $K$ steps'') without formal guarantees. Premature termination causes false declarations; prolonged searches waste battery. Conformal prediction (CP)~\cite{ref9} has been proposed, but its exchangeability assumption is violated in sequential Bayesian inference.

\subsection{Our Approach: Event-Driven Bayesian GSL}

We address both problems through an \textbf{event-driven Bayesian framework} that aligns the observation model with the physical reality of filament-based dispersion:

\begin{enumerate}
\item \textbf{Event-driven observation model.} We model gas detection as binary events from an inhomogeneous Poisson process, replacing the continuous Gaussian assumption. Non-detections carry positive information for source exclusion, preventing search degeneration in weak-signal regimes.

\item \textbf{Event-driven information gain.} We define ED-EIG (Event-Driven Expected Information Gain) that assigns positive information to both detection and non-detection outcomes. We prove $\mathrm{ED\text{-}EIG} > 0$ for any non-degenerate posterior (Proposition~\ref{prop:nondeg}), ensuring the search never degenerates.

\item \textbf{Exponential posterior concentration.} Under the event model, the Bayesian posterior concentrates at rate $e^{-\kappa t}$ (exponential) rather than $O(1/t)$ (polynomial), because the Bernoulli likelihood satisfies stronger identifiability conditions.

\item \textbf{Anytime-valid stopping.} We construct an e-process based on posterior credible region contraction that provides distribution-free stopping guarantees via Ville's inequality, without requiring exchangeability.
\end{enumerate}

\subsection{Contributions}

\begin{enumerate}
\item \textbf{Event-driven observation model for GSL.} We formalize gas detection as discrete filament-arrival events, showing that non-detections carry positive information for source exclusion. This resolves the signal model mismatch that causes existing methods to fail in weak-signal regimes.

\item \textbf{Non-degeneracy of event-driven search.} We prove that the event-driven EIG is strictly positive for any non-degenerate posterior (Proposition~\ref{prop:nondeg}), preventing search degeneration that plagues standard Infotaxis.

\item \textbf{Exponential posterior concentration.} We prove the Bayesian posterior concentrates at rate $e^{-\kappa t}$ under the event model (Theorem~\ref{thm:concentration}), the first exponential-rate result for GSL.

\item \textbf{Anytime-valid stopping.} We construct an e-process based on credible region contraction with proven super-martingale property and anytime-valid guarantee (Theorem~\ref{thm:anytime}).
\end{enumerate}
"""

path = r'D:\ZYC\A-gas\ASCi\sci\paper-isj-zh\sections\introduction.tex'
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'Written {len(content)} chars to introduction.tex')
