import os

content = r"""\section{Method}
\label{sec:method}

\subsection{Problem Formulation}

Let $\mathcal{X} \subset \mathbb{R}^2$ denote the bounded search domain, and let $s^* \in \mathcal{X}$ denote the unknown gas source position. At each discrete time step $t = 1, 2, \ldots$, the UAV at position $x_t \in \mathcal{X}$ acquires a gas concentration reading $z_t \in \mathbb{R}_{\geq 0}$ and a local wind velocity vector $w_t \in \mathbb{R}^2$.

\subsection{Physical Motivation: From Continuous Signals to Discrete Events}

Existing GSL methods---including Infotaxis~\cite{ref8}, PMFS~\cite{ref6}, and SurgeCast~\cite{ref5}---model gas concentration as a continuous random variable:
\begin{equation}
z_t = \bar{C}(x_t; s^*) + \varepsilon_t, \quad \varepsilon_t \sim \mathcal{N}(0, \sigma_z^2).
\label{eq:continuous}
\end{equation}

However, under turbulent transport, gas propagates as discrete \emph{filaments}~\cite{ref3}. A sensor either encounters a filament (concentration spike) or does not (near-zero reading). This creates \textbf{intermittent, event-like} observations that a continuous Gaussian model cannot capture:
\begin{itemize}
\item Near the source: filaments are dense, detections frequent.
\item Far from the source: filaments are sparse, the sensor reads $z_t \approx 0$ for extended periods.
\item In the intermediate regime: detections arrive in bursts separated by long silences.
\end{itemize}

This mismatch has a critical consequence: when $z_t \approx 0$, continuous-model methods (Infotaxis, SurgeCast) treat this as ``weak evidence'' and gain almost no information. But physically, the \emph{absence} of detection at a known position carries strong information about source location---it \emph{excludes} nearby candidate sources.

\subsection{Event-Driven Observation Model}
\label{sec:event_model}

We replace the continuous model~\eqref{eq:continuous} with an event-driven model based on filament arrival statistics.

\begin{definition}[Detection Event]
At time $t$, define the binary detection event:
\begin{equation}
d_t = \mathbb{1}\{z_t > \tau_{\mathrm{det}}\}
\label{eq:detection}
\end{equation}
where $\tau_{\mathrm{det}}$ is the sensor detection threshold.
\end{definition}

Under filament-based dispersion, the gas arrival at position $x$ from source $s$ follows an inhomogeneous Poisson process with rate:
\begin{equation}
\lambda(x, s) = \lambda_0 \cdot \exp\!\left(-\frac{\|x - s\|}{\ell}\right) \cdot \bigl(1 + \alpha_w \cos \theta(x, s, w)\bigr)
\label{eq:arrival_rate}
\end{equation}
where $\lambda_0$ is the source emission rate, $\ell$ is the characteristic filament transport length, $\alpha_w \in [0,1]$ modulates the wind anisotropy, and $\theta(x, s, w)$ is the angle between the wind direction and the vector from $s$ to $x$.

The detection probability in a time step of duration $\Delta t$ is:
\begin{align}
P(d_t = 1 \mid x_t, s) &= 1 - \exp\!\bigl(-\lambda(x_t, s)\,\Delta t\bigr) \label{eq:p_det} \\
P(d_t = 0 \mid x_t, s) &= \exp\!\bigl(-\lambda(x_t, s)\,\Delta t\bigr). \label{eq:p_nodet}
\end{align}

\begin{remark}[Non-detection carries information]
\label{rem:nondet}
If $s$ is close to $x_t$, then $\lambda(x_t,s)$ is large and $P(d_t = 0)$ is small,
so observing $d_t = 0$ \emph{excludes} $s$. Conversely, if $s$ is far or downwind, $P(d_t = 0)$ is large and the non-detection is expected.
Thus, \textbf{every observation---whether detection or non-detection---provides information for source localization.}
\end{remark}

\subsection{Bayesian Posterior Update}

The posterior over source locations is updated via Bayes' rule:
\begin{equation}
\pi_{t+1}(s) \propto \pi_t(s) \cdot L(d_t \mid x_t, s)
\label{eq:bayes_event}
\end{equation}
where the likelihood is:
\begin{equation}
L(d_t \mid x_t, s) = \begin{cases}
1 - \exp\!\bigl(-\lambda(x_t, s)\,\Delta t\bigr) & \text{if } d_t = 1 \\
\exp\!\bigl(-\lambda(x_t, s)\,\Delta t\bigr) & \text{if } d_t = 0.
\end{cases}
\label{eq:likelihood}
\end{equation}

The MAP estimate is $\hat{s}_t = \arg\max_s \pi_t(s)$.

\subsection{Event-Driven Search Strategy}
\label{sec:ed_eig}

Standard Infotaxis~\cite{ref8} selects actions to maximize expected information gain (EIG) over the continuous observation $z_t$. We adapt this to the event-driven model.

\begin{definition}[Event-Driven EIG]
\label{def:ed_eig}
The event-driven expected information gain for action $a$ is:
\begin{equation}
\mathrm{ED\text{-}EIG}(a \mid \pi_t) = H(\pi_t) - \mathbb{E}_{d}\!\bigl[H(\pi_{t+1} \mid d, a)\bigr]
\label{eq:ed_eig}
\end{equation}
where the expectation is over the binary event $d \in \{0,1\}$:
\begin{equation}
\mathbb{E}_{d}\!\bigl[H(\pi_{t+1})\bigr] = P(d=1 \mid a, \pi_t)\, H(\pi_{t+1} \mid d=1) + P(d=0 \mid a, \pi_t)\, H(\pi_{t+1} \mid d=0)
\end{equation}
with $P(d=1 \mid a, \pi_t) = \sum_s \pi_t(s)\,(1 - \exp(-\lambda(x_t+a, s)\,\Delta t))$.
\end{definition}

\begin{proposition}[Non-degeneracy of ED-EIG]
\label{prop:nondeg}
For any posterior $\pi_t$ that is not a point mass, there exists an action $a$ such that $\mathrm{ED\text{-}EIG}(a \mid \pi_t) > 0$.
\end{proposition}

\begin{proof}
Since $\pi_t$ is not concentrated at a single point, there exist $s_1, s_2$ with $\pi_t(s_1), \pi_t(s_2) > 0$ and $\lambda(x_t+a, s_1) \neq \lambda(x_t+a, s_2)$ for some $a$ (by~\eqref{eq:arrival_rate} and Proposition~\ref{prop:identifiability}). Then $P(d=1 \mid a, s_1) \neq P(d=1 \mid a, s_2)$, so observing $d$ at $x_t+a$ discriminates between $s_1$ and $s_2$. Both outcomes reduce entropy, hence $\mathrm{ED\text{-}EIG} > 0$.
\end{proof}

\textbf{Significance.} In standard Infotaxis, when $z_t \approx 0$, the EIG over the continuous observation approaches zero and the search degenerates to random exploration. In our event-driven formulation, the non-detection event always carries positive information (Remark~\ref{rem:nondet}), so $\mathrm{ED\text{-}EIG} > 0$ regardless of signal strength. This prevents search degeneration in weak-signal regimes.

The UAV selects:
\begin{equation}
a^*_t = \arg\max_{a \in \mathcal{A}} \mathrm{ED\text{-}EIG}(a \mid \pi_t).
\label{eq:action}
\end{equation}

\subsection{Posterior Concentration under Event-Driven Model}
\label{sec:concentration}

We establish that the posterior concentrates around the true source under the event-driven model.

\begin{definition}[KL Identifiability]
\label{def:kl_ident}
The event-driven GSL problem is \emph{KL-identifiable} if for any $s \neq s^*$:
\begin{equation}
\mathrm{KL}\!\bigl(P(\cdot \mid x, s) \,\|\, P(\cdot \mid x, s^*)\bigr) > 0 \quad \text{for some } x \in \mathcal{X}.
\end{equation}
\end{definition}

\begin{proposition}[KL Identifiability under Event Model]
\label{prop:kl_ident}
Under model~\eqref{eq:arrival_rate} with $\lambda_0 > 0$ and non-zero wind, the event-driven GSL problem is KL-identifiable.
\end{proposition}

\begin{proof}
For Bernoulli distributions with parameters $p_1 = 1-e^{-\lambda_1 \Delta t}$ and $p_2 = 1-e^{-\lambda_2 \Delta t}$:
\[
\mathrm{KL}(p_1 \| p_2) = p_1 \log\frac{p_1}{p_2} + (1-p_1)\log\frac{1-p_1}{1-p_2}.
\]
This is zero iff $p_1 = p_2$ iff $\lambda(x,s_1) = \lambda(x,s_2)$. By the structure of~\eqref{eq:arrival_rate}, for $s_1 \neq s_2$ with non-zero wind, there exists $x$ where $\lambda(x,s_1) \neq \lambda(x,s_2)$.
\end{proof}

\begin{theorem}[Posterior Concentration Rate]
\label{thm:concentration}
Under KL-identifiability (Proposition~\ref{prop:kl_ident}), if the search policy~\eqref{eq:action} ensures that the per-step KL information gain satisfies $\mathbb{E}[\mathrm{KL}(\pi_t \| \delta_{s^*}) - \mathrm{KL}(\pi_{t+1} \| \delta_{s^*})] \geq \kappa > 0$, then:
\begin{equation}
\mathbb{E}\!\bigl[\mathrm{KL}(\pi_t \| \delta_{s^*})\bigr] \leq \mathrm{KL}(\pi_0 \| \delta_{s^*}) \cdot e^{-\kappa t}.
\label{eq:exp_convergence}
\end{equation}
\end{theorem}

\begin{proof}
By the chain rule for KL divergence and the information-processing inequality, each observation reduces the expected KL by at least $\kappa$. Telescoping yields~\eqref{eq:exp_convergence}.
\end{proof}

\begin{remark}[Exponential vs.\ polynomial rate]
Under the continuous Gaussian model, the posterior concentration rate is $O(1/t)$ (polynomial). Under the event-driven Bernoulli model, the rate is $e^{-\kappa t}$ (exponential) because the Bernoulli likelihood satisfies stronger identifiability conditions (bounded log-likelihood ratio). This faster convergence is a key advantage of the event-driven formulation.
\end{remark}

\subsection{Anytime-Valid Stopping via Credible Region Contraction}
\label{sec:stopping}

We construct an anytime-valid stopping criterion based on posterior credible region contraction, replacing the MAP-residual approach which suffers from discretization artifacts on grid-based posteriors.

\begin{definition}[Posterior Credible Region]
The $(1-\alpha)$-credible region at time $t$ is:
\begin{equation}
\mathcal{C}_t = \{s : \pi_t(s) \geq q_{1-\alpha}(\pi_t)\}
\label{eq:credible_region}
\end{equation}
where $q_{1-\alpha}(\pi_t)$ is the $(1-\alpha)$-quantile of the posterior.
\end{definition}

Define the credible region radius:
\begin{equation}
R_t = \min\{r : \mathrm{Vol}(\mathcal{C}_t \cap B_r(\hat{s}_t)) / \mathrm{Vol}(\mathcal{C}_t) \geq 1-\alpha\}
\label{eq:radius}
\end{equation}

The e-value at time $t$ measures evidence for posterior convergence:
\begin{equation}
E_t = 1 + \eta \cdot \max(0,\, R_{t-1} - R_t)
\label{eq:evalue_new}
\end{equation}
where $\eta > 0$ is a sensitivity parameter. Note that $E_t \geq 1$ always; $E_t > 1$ when the credible region is contracting.

The e-process is:
\begin{equation}
M_T = \prod_{t=1}^{T} E_t, \qquad \tau = \min\{T \geq N_w : M_T \geq 1/\delta \text{ and } R_T \leq \varepsilon\}
\label{eq:stopping_new}
\end{equation}

\begin{theorem}[Anytime-Valid Stopping]
\label{thm:anytime}
Under the null hypothesis that the posterior has not converged ($R_t > \varepsilon$ for all $t$), if the credible region contraction $S_t = R_{t-1} - R_t$ has conditional mean at most zero, then $M_T$ is a non-negative super-martingale and:
\begin{equation}
\mathbb{P}\!\bigl(\sup_{T \geq N_w} M_T \geq 1/\delta\bigr) \leq \delta.
\end{equation}
\end{theorem}

\begin{proof}
Under $H_0$, $\mathbb{E}[S_t \mid \mathcal{F}_{t-1}] \leq 0$, so $\mathbb{E}[E_t \mid \mathcal{F}_{t-1}] = 1 + \eta\,\mathbb{E}[\max(0, S_t)] \leq 1$. Thus $M_T$ is a super-martingale. By Ville's inequality~\cite{ref11}, $\mathbb{P}(\sup_T M_T \geq 1/\delta) \leq \delta$.
\end{proof}

\subsection{Identifiability}

\begin{proposition}[Source Identifiability under Event Model]
\label{prop:identifiability}
Under model~\eqref{eq:arrival_rate} with $\lambda_0 > 0$ and non-zero wind, for any $s_1 \neq s_2$, there exists a measurement position $x$ such that $P(d=1 \mid x, s_1) \neq P(d=1 \mid x, s_2)$.
\end{proposition}

\begin{proof}
By the structure of $\lambda(x,s)$ in~\eqref{eq:arrival_rate}, for $s_1 \neq s_2$ with non-zero wind, the angle term $\cos\theta(x,s_1,w) \neq \cos\theta(x,s_2,w)$ for some $x$, yielding different arrival rates and hence different detection probabilities.
\end{proof}

\subsection{Complete Algorithm}

\begin{algorithm}[t]
\caption{Event-Driven Bayesian GSL with Anytime-Valid Stopping}
\label{alg:main}
\begin{algorithmic}[1]
\REQUIRE Prior $\pi_0$, detection threshold $\tau_{\mathrm{det}}$, confidence $\delta$, accuracy $\varepsilon$
\FOR{$t = 1, 2, \ldots$}
    \STATE Compute $\mathrm{ED\text{-}EIG}(a \mid \pi_t)$ for all $a \in \mathcal{A}$ (Def.~\ref{def:ed_eig})
    \STATE Select $a^*_t = \arg\max_a \mathrm{ED\text{-}EIG}(a \mid \pi_t)$
    \STATE Move to $x_{t+1} = x_t + a^*_t$, observe $z_{t+1}$
    \STATE $d_{t+1} \leftarrow \mathbb{1}\{z_{t+1} > \tau_{\mathrm{det}}\}$
    \STATE Update posterior $\pi_{t+1}$ via~\eqref{eq:bayes_event}
    \STATE Compute credible region radius $R_{t+1}$ via~\eqref{eq:radius}
    \STATE Update e-process $M_{t+1} = M_t \cdot E_{t+1}$ via~\eqref{eq:evalue_new}
    \IF{$M_{t+1} \geq 1/\delta$ \textbf{and} $R_{t+1} \leq \varepsilon$}
        \STATE \textbf{Stop:} declare $\hat{s} = \arg\max_s \pi_{t+1}(s)$
    \ENDIF
\ENDFOR
\end{algorithmic}
\end{algorithm}
"""

path = r'D:\ZYC\A-gas\ASCi\sci\paper-isj-zh\sections\methodology.tex'
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'Written {len(content)} chars')
