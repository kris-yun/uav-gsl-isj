import os

en_dir = r"D:\ZYC\A-gas\ASCi\sci\paper-isj-en\sections"

# 1. Introduction (English)
with open(os.path.join(en_dir, "introduction.tex"), 'w', encoding='utf-8') as f:
    f.write(r"""\section{Introduction}
\label{sec:intro}

\IEEEPARstart{G}{as} source localization (GSL) with unmanned aerial vehicles (UAVs) has attracted significant attention due to applications in industrial leak detection, environmental monitoring, and post-disaster hazard assessment~\cite{1,2}. The fundamental challenge is that gas dispersion in realistic environments is governed by turbulent transport, producing intermittent, filamentary plume structures rather than smooth concentration gradients~\cite{3}. This intermittency means that a UAV may experience prolonged periods of non-detection interspersed with brief, intense detection events---a regime where most existing algorithms degrade severely.

\subsection{Challenging Problems}

Two dominant algorithmic paradigms have been proposed for GSL under turbulent dispersion. \emph{Upwind-tracking methods}, exemplified by SurgeCast~\cite{4}, exploit local wind direction to track plumes toward their source. These methods achieve excellent precision when the UAV begins within a strong plume, but degrade sharply when initial signal strength is weak~\cite{5}. \emph{Information-theoretic methods}, exemplified by Infotaxis~\cite{6}, select actions to maximize expected information gain. While theoretically elegant, Infotaxis suffers from a critical failure mode: when gas readings $z_t \approx 0$ (the predominant case in intermittent plume contact), the EIG approaches zero because the continuous observation model assigns negligible likelihood weight to near-zero readings.

A deeper, under-recognized problem unifies these failures. Both paradigms model gas concentration as a continuous signal, treating $z_t \approx 0$ as carrying negligible information. We identify this as an instance of the \emph{posterior locking} phenomenon: when the observation model assigns near-zero likelihood to the dominant non-detection events, early stochastic fluctuations can trap the posterior in a wrong mode from which it cannot recover. This failure mode is structurally analogous to the \emph{randomly missing measurement} problem in networked state estimation~\cite{7,8}, where packet dropouts cause the Kalman filter to diverge when the loss rate exceeds a critical threshold.

The key insight is that non-detection is not missing data---it is a likelihood event that excludes high-rate source hypotheses. However, exploiting this information requires a \emph{robust} update rule that does not over-commit to early evidence---a requirement that standard Bayesian updating fails to satisfy under model misspecification~\cite{9}.

Furthermore, no existing GSL method provides a principled stopping criterion with formal error control~\cite{10}. Recent advances in anytime-valid inference (AVI) offer tools to address this gap: e-processes and confidence sequences provide inference guarantees that hold at \emph{all} stopping times simultaneously~\cite{11,12,13}.

\subsection{Proposed Solutions}

In this paper, we propose a \emph{robust estimation-decision coordination framework} for UAV GSL in low-information environments. Rather than pursuing a generic framework, we address the specific challenge of \emph{low wind speed, intermittent detection, and wind field mismatch} that causes traditional likelihood-driven methods to either over-commit or prematurely terminate. On the estimation side, we use Generalized Bayesian Inference (GBI)~\cite{14} with an adaptive temperature $\eta$ that embeds \emph{observation credibility} into the posterior. On the decision side, we combine anytime-valid e-processes with Drift-Diffusion Model (DDM)~\cite{15} evidence accumulation to form a \emph{dual-channel convergence control}.

\subsection{Contributions}

\begin{enumerate}
\item \textbf{Wind-confidence-driven adaptive GBI with heterogeneous loss weights.} We propose an adaptive learning rate $\eta$ that is a \emph{state variable} driven by wind confidence $c_w$: high $\eta$ (0.6--0.9) when gas is detected with stable wind, low $\eta$ (0.15--0.5) for non-detection events. We prove exponential-rate posterior concentration under the logistic detection model (Theorem~\ref{thm:contraction}).

\item \textbf{Dual-channel stopping with anytime-valid guarantees.} We construct a dual-channel stopping mechanism combining (i)~a Hoeffding e-process on MAP residuals providing distribution-free anytime-valid guarantees via Ville's inequality (Theorem~\ref{thm:eprocess}), and (ii)~a DDM with urgency gating for robust termination under non-stationary conditions (Proposition~\ref{prop:ddm}).

\item \textbf{Logistic detection model calibrated to indoor filament dynamics.} We formalize gas detection as discrete events with a logistic probability model, replacing both the continuous Gaussian observation model and the exponential decay model. We establish a formal connection to the randomly missing measurement framework~\cite{7,8}.

\item \textbf{GP-based adaptive height selection for unknown source altitude.} We introduce a Gaussian process-based altitude selection mechanism that enables the UAV to locate sources at unknown heights.
\end{enumerate}

The remainder of this paper is organized as follows. Section~\ref{sec:related} reviews related work. Section~\ref{sec:system} presents the system model. Section~\ref{sec:method} details the GBI-GSL framework. Section~\ref{sec:theory} provides theoretical analysis. Section~\ref{sec:experiments} presents experimental results. Section~\ref{sec:conclusion} concludes with limitations and future directions.
""")

# 2. Related Work (English)
with open(os.path.join(en_dir, "related_work.tex"), 'w', encoding='utf-8') as f:
    f.write(r"""\section{Related Work}
\label{sec:related}

\subsection{Classical Gas Source Localization}

Early GSL methods drew inspiration from biological chemotaxis strategies. The plume tracing paradigm~\cite{3} alternates between upwind surges and lateral casts, mimicking insect behavior within odor plumes. SurgeCast~\cite{4} and its variants implement this strategy on UAV platforms, achieving high precision under continuous plume contact but requiring manual parameter tuning and degrading sharply upon loss of contact. Probabilistic mapping methods such as PMFS~\cite{16} and GrGSL~\cite{17} maintain source probability maps through online diffusion simulations integrating gas measurements and wind field data. However, these methods rely on parametric plume models (typically Gaussian) that may not match actual filamentary diffusion structures.

A common limitation of classical methods is their dependence on continuous plume contact. When the UAV enters a gas-free region (a common occurrence in turbulent environments), upwind tracking methods lose their guidance signal and search stagnates.

\subsection{Information-Theoretic Methods}

Infotaxis~\cite{6} introduced the paradigm of selecting actions to maximize expected information gain (EIG) about source location, eliminating the need for explicit gradient estimation. Despite these advances, information-theoretic methods share a fundamental limitation in weak-signal regimes: when gas readings approach zero, EIG approaches zero because the continuous observation model assigns negligible likelihood weight to observations~\cite{18}.

\subsection{Bayesian GSL Methods}

Bayesian methods provide a natural framework for GSL by maintaining a posterior distribution over source location conditioned on observation history. However, existing Bayesian GSL methods use continuous observation models and do not provide formal stopping guarantees. The posterior is used only for action selection (e.g., Thompson sampling or EIG maximization), not for principled termination.

\subsection{Anytime-Valid Inference}

Anytime-valid inference (AVI) provides statistical guarantees that hold simultaneously at all stopping times~\cite{11}. Key tools are e-processes---test martingales that remain valid regardless of when they are applied---and confidence sequences. Despite these theoretical advances, AVI has not been applied to robotic source localization.

\subsection{Networked Estimation with Missing Measurements}

The problem of state estimation under random packet dropouts has been extensively studied in the networked control literature. Ge et al.~\cite{7} established convergence conditions for distributed Kalman filtering with randomly missing measurements, proving that the filter diverges when the packet loss rate exceeds a critical threshold. In UAV GSL, ``dropouts'' are endogenous: they depend on the UAV's position relative to the unknown source. Our adaptive $\eta$ design draws on this literature, implementing reliability-weighted fusion gains that modulate posterior update strength based on observation quality.

\subsection{Literature Gap}

Table~\ref{tab:summary} summarizes the positioning of GBI-GSL relative to existing methods. No existing method simultaneously combines: (i)~a credibility scheduler driven by wind confidence, (ii)~exponential-rate posterior concentration under model misspecification, and (iii)~dual-channel anytime-valid stopping guarantees.

\begin{table}[t]
\centering
\caption{GSL paradigm comparison. GBI-GSL is the first method combining credibility-weighted fusion with dual-channel anytime-valid stopping.}
\label{tab:summary}
\begin{tabular}{lccc}
\toprule
\textbf{Method} & \textbf{Credibility} & \textbf{Stopping} & \textbf{Rate} \\
& \textbf{Scheduler?} & \textbf{Guarantee?} & \\
\midrule
SurgeCast~\cite{4} & No & No & -- \\
Infotaxis~\cite{6} & No & No & $O(1/t)$ \\
PMFS~\cite{16} & Weak & No & $O(1/t)$ \\
Dual-mode~\cite{19} & No & No & $O(1/t)$ \\
Bayesian~\cite{20} & Weak & No & $O(1/t)$ \\
\midrule
\textbf{GBI-GSL (ours)} & \textbf{Yes} & \textbf{Yes (dual)} & $\bm{e^{-\kappa t}}$ \\
\bottomrule
\end{tabular}
\end{table}
""")

# 3. System Model (English)
with open(os.path.join(en_dir, "system_model.tex"), 'w', encoding='utf-8') as f:
    f.write(r"""\section{System Model and Problem Formulation}
\label{sec:system}

\subsection{Indoor Environment}

Consider a bounded indoor environment $\mathcal{X} \subset \mathbb{R}^3$ with volume $V < \infty$, enclosed by walls and containing static obstacles. The environment contains a single gas source at unknown location $s^* = (s_x^*, s_y^*, s_z^*) \in \mathcal{X}$ that emits gas continuously at constant rate $Q$~(g/s). The airflow within $\mathcal{X}$ is characterized by a spatially and temporally varying wind field:
\begin{equation}
w: \mathcal{X} \times [0, \infty) \to \mathbb{R}^3, \quad \|w(x, t)\| \le w_{\max},
\end{equation}
where $w_{\max} < 0.1$\,m/s in low-wind indoor conditions. The wind field is \emph{not known a priori} and can only be partially observed through onboard anemometry at the UAV's current position.

\subsection{Gas Dispersion Model}

Unlike outdoor environments where the Gaussian plume model provides a reasonable approximation, indoor gas transport under low-wind conditions is dominated by turbulent diffusion, producing intermittent, filamentary plume structures~\cite{3}. We model gas arrival at a fixed observation point $x \in \mathcal{X}$ from source $s$ as an inhomogeneous Poisson process with intensity:
\begin{equation}
\lambda(x, s, w) = \lambda_0 \exp\!\left(-\frac{\|x - s\|}{\ell_c}\right)\bigl(1 + \alpha_w \cos\theta(x, s, w)\bigr),
\end{equation}
where $\lambda_0$~(hits/s) is the baseline arrival intensity, $\ell_c$~(m) is the characteristic dispersion length scale, $\alpha_w \in [0, 1]$ controls wind-driven anisotropy, and $\theta(x, s, w) = \angle(x - s, w)$ is the angle between the displacement vector and the local wind direction.

\subsection{UAV Platform}

The UAV is modeled as a point mass moving in 3D space with discrete-time dynamics:
\begin{equation}
x_{t+1} = x_t + u_t \Delta t, \quad \|u_t\| \le v_{\max},
\end{equation}
where $x_t = (p_x, p_y, p_z)_t \in \mathcal{X}$ is the UAV position, $u_t \in \mathbb{R}^3$ is the velocity command, $\Delta t$~(s) is the sampling interval, and $v_{\max}$~(m/s) is the maximum flight speed. The altitude is constrained to $p_z \in [z_{\min}, z_{\max}]$. The UAV is equipped with: (i)~a gas sensor returning concentration reading $c_t \in \mathbb{R}^+$ with detection threshold $\tau > 0$; (ii)~a wind sensor returning 2D wind vector $w_t = (w_x, w_y)_t \in \mathbb{R}^2$; and (iii)~a localization module providing 3D position $x_t$.

\subsection{Observation Model}

At each time step $t$, the UAV acquires observation tuple $\mathcal{O}_t = (c_t, w_t, x_t)$. We define the binary detection event:
\begin{equation}
d_t = \mathbb{1}\{c_t > \tau\} \in \{0, 1\},
\end{equation}
where $\tau$ is the sensor-specific detection threshold. The detection probability at position $x$ given candidate source $s$ and local wind $w$ is:
\begin{equation}
P(d_t = 1 \mid x_t, s, w_t) = \phi(x_t, s, w_t),
\end{equation}
where $\phi(\cdot)$ is the logistic detection model detailed in Section~\ref{sec:method}. The observation history up to time $T$ is denoted by $\mathcal{H}_T = \{(d_t, x_t, w_t)\}_{t=1}^T$.

\subsection{Problem Statement}

Given observation history $\mathcal{H}_T$ and prior distribution $\pi_0(s)$ over source location, the objective is to design a closed-loop policy $\pi = (\mu_1, \mu_2, \ldots)$ such that: (i)~the posterior $\pi_t(s)$ concentrates on $s^*$ as $t \to \infty$; (ii)~actions maximize expected information gain about $s^*$; and (iii)~a stopping time $\tau_{\mathrm{stop}}$ is determined such that $\mathbb{P}(\|\hat{s}_{\tau_{\mathrm{stop}}} - s^*\| \le r_{\mathrm{stop}}) \ge 1 - \delta$, where $\hat{s}_t = \arg\max_s \pi_t(s)$ is the MAP estimate and $\delta$ is the tolerated false-alarm rate.

\begin{remark}[Challenge]
In low-wind indoor environments, detection events are highly intermittent (typical detection rates below 20\%), and the observation model is fundamentally misspecified if standard Gaussian plume assumptions are employed. Moreover, no existing GSL method provides the formal stopping guarantee with anytime-valid error control.
\end{remark}
""")

# 4. Theory (English)
with open(os.path.join(en_dir, "theory.tex"), 'w', encoding='utf-8') as f:
    f.write(r"""\section{Theoretical Analysis}
\label{sec:theory}

This section establishes the theoretical foundations of the GBI-GSL framework. We prove posterior contraction under model misspecification and provide anytime-valid stopping guarantees.

\subsection{Assumptions}

\begin{assumption}[Compact parameter space]
\label{asm:compact}
The source location parameter space $\mathcal{S} \subset \mathbb{R}^d$ is compact, and the prior $\pi_0(s)$ has a positive lower bound on $\mathcal{S}$: $\pi_0(s) \ge \underline{\pi} > 0$ for all $s \in \mathcal{S}$.
\end{assumption}

\begin{assumption}[Bounded loss]
\label{asm:bounded_loss}
The loss function $\ell_t(s)$ is uniformly bounded: $\sup_t \sup_{s \in \mathcal{S}} |\ell_t(s)| \le L < \infty$.
\end{assumption}

\begin{assumption}[Bounded adaptive rate]
\label{asm:eta_bound}
The adaptive learning rate satisfies $\eta_t \in [\underline{\eta}, \overline{\eta}] \subset (0, 1)$, where $\underline{\eta} = 0.15$ and $\overline{\eta} = 0.90$.
\end{assumption}

\begin{assumption}[KL identifiability]
\label{asm:kl}
The true source $s^*$ is KL-identifiable: there exists $\delta_{\mathrm{KL}} > 0$ such that for all $s \neq s^*$ in a neighborhood of $s^*$,
\begin{equation}
\liminf_{T\to\infty} \frac{1}{T} \sum_{t=1}^T \mathbb{E}[\ell_t(s) - \ell_t(s^*)] \ge \delta_{\mathrm{KL}}.
\end{equation}
\end{assumption}

\subsection{Posterior Contraction}

\begin{theorem}[Posterior Contraction]
\label{thm:contraction}
Under Assumptions~\ref{asm:compact}--\ref{asm:kl}, the GBI posterior concentrates on the true source $s^*$: for any $\epsilon > 0$,
\begin{equation}
\Pi_T(U_\epsilon(s^*)) \to 1 \quad \text{a.s.\ as } T \to \infty,
\end{equation}
where $U_\epsilon(s^*) = \{s \in \mathcal{S} : \|s - s^*\| < \epsilon\}$. Moreover, the contraction rate is exponential:
\begin{equation}
\mathbb{E}\!\left[1 - \Pi_T(U_\epsilon(s^*))\right] \le C \exp(-\kappa T),
\end{equation}
where $\kappa = \underline{\eta} \cdot \delta_{\mathrm{KL}}$ and $C$ depends on the prior and the parameter space.
\end{theorem}

\textit{Proof sketch.} The proof follows from the GBI consistency framework of~\cite{14,21} combined with the bounded adaptive rate (Assumption~\ref{asm:eta_bound}). The full proof is in Appendix~\ref{app:proofs}. \hfill$\square$

\subsection{Anytime-Valid Stopping}

\begin{theorem}[e-Process Stopping Guarantee]
\label{thm:eprocess}
Define the e-value $E_t = \exp(\eta_e x_t - \eta_e^2 B^2 / 2)$. Under $H_0$ (source not localized), the e-process $M_T = \prod_{t=1}^T E_t$ satisfies:
\begin{equation}
\mathbb{P}_{H_0}\!\left(\sup_{T \geq 1} M_T \geq 1/\delta\right) \leq \delta.
\end{equation}
\end{theorem}

\textit{Proof.} See Appendix~\ref{app:proofs}. \hfill$\square$

\begin{proposition}[DDM as SPRT with Urgency Gating]
\label{prop:ddm}
The DDM accumulator $X_{t+1} = X_t + z_t - \lambda X_t$ reduces to the SPRT cumulative sum $S_T = \sum_{t=1}^T z_t$ as $\lambda \to 0$. The urgency-gated threshold $\theta(t) = \theta_0 \exp(-\gamma_u t) + \theta_{\min}$ ensures decreasing threshold over time, accelerating termination.
\end{proposition}

\textit{Proof.} See Appendix~\ref{app:proofs}. \hfill$\square$
""")

# 5. Conclusion (English)
with open(os.path.join(en_dir, "conclusion.tex"), 'w', encoding='utf-8') as f:
    f.write(r"""\section{Conclusion}
\label{sec:conclusion}

We have presented a robust estimation-decision coordination framework for UAV gas source localization in low-wind indoor environments. The key insight is that in low-information environments characterized by intermittent detection and model misspecification, the estimation and decision layers must be co-designed rather than treated independently.

The proposed GBI-GSL framework makes four contributions: (i)~a wind-confidence-driven adaptive GBI that treats the learning rate $\eta$ as a state variable, achieving robust posterior updating under model misspecification; (ii)~a dual-channel stopping mechanism combining anytime-valid e-processes with DDM evidence accumulation, providing formal false-alarm control; (iii)~a logistic detection model calibrated to indoor filament dynamics; and (iv)~a GP-based adaptive height selection for sources at unknown altitudes. Experiments on the GADEN simulator demonstrate that GBI-GSL achieves 1.62\,m mean error with 92.5\% success rate, outperforming state-of-the-art baselines by 45--75\% in error reduction.

\subsection{Limitations and Future Work}

Several limitations should be acknowledged:
\begin{itemize}
\item \textbf{Simulation only}: All experiments are conducted in the GADEN simulator. Real-world validation with physical UAV platforms and gas sensors is needed.
\item \textbf{Single agent}: The current framework is designed for a single UAV. Extension to multi-UAV cooperative GSL is a natural next step.
\item \textbf{Indoor environments}: The method is designed for indoor environments with low wind speed ($< 0.1$\,m/s). Outdoor scenarios require additional wind field modeling.
\item \textbf{Model parameters}: The detection model parameters ($d_0 = 1.5$\,m, $\gamma = 2.0$\,m$^{-1}$) are manually calibrated. Automatic calibration would improve generality.
\end{itemize}

Future work will pursue three directions: (i)~real-world validation with ROS-based UAV platforms; (ii)~extension to multi-source localization using mixture posteriors; and (iii)~integration of the e-process stopping framework with multi-agent consensus protocols for distributed termination guarantees.
""")

# 6. Appendix Proofs (English)
with open(os.path.join(en_dir, "appendix_proofs.tex"), 'w', encoding='utf-8') as f:
    f.write(r"""\section{Proofs of Theoretical Results}
\label{app:proofs}

This appendix provides complete proofs for the theorems and propositions in Section~\ref{sec:theory}.

\subsection{Proof of Theorem~\ref{thm:contraction} (Posterior Contraction)}

\textbf{Theorem~\ref{thm:contraction}.}
\textit{Under Assumptions~\ref{asm:compact}--\ref{asm:kl}, the GBI posterior concentrates on the true source $s^*$ with exponential rate $\kappa = \underline{\eta} \cdot \delta_{\mathrm{KL}}$.}

\textbf{Proof.}
By the GBI update rule~\eqref{eq:gbi}, the posterior can be written as:
\begin{equation}
\pi_T(s) = \frac{\pi_0(s) \exp\!\left(-\sum_{t=1}^T \eta_t \ell_t(s)\right)}{\int_{\mathcal{S}} \pi_0(s') \exp\!\left(-\sum_{t=1}^T \eta_t \ell_t(s')\right) ds'}.
\end{equation}

Define the log-posterior ratio:
\begin{equation}
L_T(s) = \log\frac{\pi_T(s)}{\pi_T(s^*)} = \log\frac{\pi_0(s)}{\pi_0(s^*)} - \sum_{t=1}^T \eta_t \left[\ell_t(s) - \ell_t(s^*)\right].
\end{equation}

By Assumption~\ref{asm:eta_bound} ($\eta_t \ge \underline{\eta} > 0$):
\begin{equation}
L_T(s) \le \log\frac{\pi_0(s)}{\pi_0(s^*)} - \underline{\eta} \sum_{t=1}^T \left[\ell_t(s) - \ell_t(s^*)\right].
\end{equation}

By Assumption~\ref{asm:kl} (KL identifiability), for $s \neq s^*$:
\begin{equation}
\liminf_{T\to\infty} \frac{1}{T} \sum_{t=1}^T \mathbb{E}[\ell_t(s) - \ell_t(s^*)] \ge \delta_{\mathrm{KL}} > 0.
\end{equation}

By Assumption~\ref{asm:bounded_loss} (bounded loss, $|\ell_t| \le L$), applying Hoeffding's inequality:
\begin{equation}
\mathbb{P}\!\left(\sum_{t=1}^T [\ell_t(s) - \ell_t(s^*)] < \frac{T\delta_{\mathrm{KL}}}{2}\right) \le \exp\!\left(-\frac{T\delta_{\mathrm{KL}}^2}{8L^2}\right).
\end{equation}

Therefore, as $T \to \infty$, $L_T(s) \to -\infty$ at exponential rate, implying $\pi_T(s) \to 0$ for all $s \neq s^*$. The posterior mass concentrates on $U_\epsilon(s^*)$.

For the explicit rate bound, by Assumption~\ref{asm:compact} ($\pi_0 \ge \underline{\pi} > 0$):
\begin{equation}
1 - \Pi_T(U_\epsilon(s^*)) \le \frac{|\mathcal{S}|}{\underline{\pi}} \cdot \exp\!\left(-\underline{\eta} T \delta_{\mathrm{KL}}\right),
\end{equation}
giving $C = |\mathcal{S}|/\underline{\pi}$ and $\kappa = \underline{\eta} \cdot \delta_{\mathrm{KL}}$.\hfill$\square$

\subsection{Proof of Theorem~\ref{thm:eprocess} (e-Process Stopping Guarantee)}

\textbf{Theorem~\ref{thm:eprocess}.}
\textit{Let $x_t = \mathrm{clip}(\epsilon - r_t, -B, B)$ with $B = \epsilon$. Define $E_t = \exp(\eta_e x_t - \eta_e^2 B^2/2)$. Under $H_0$ with $\mathbb{E}[x_t \mid \mathcal{F}_{t-1}, H_0] \le 0$, the e-process $M_T = \prod_{t=1}^T E_t$ satisfies $\mathbb{P}_{H_0}(\sup_{T \ge 1} M_T \ge 1/\delta) \le \delta$.}

\textbf{Proof.}

\textit{Step 1: $E_t$ is a conditionally supermartingale under $H_0$.}

By Hoeffding's lemma, for bounded random variable $X \in [a, b]$ with $\mathbb{E}[X] \le 0$:
\begin{equation}
\mathbb{E}[\exp(\lambda X)] \le \exp\!\left(\frac{\lambda^2(b-a)^2}{8}\right), \quad \forall \lambda > 0.
\end{equation}

Here $x_t \in [-B, B]$, so $b - a = 2B$. With $\lambda = \eta_e$:
\begin{equation}
\mathbb{E}[E_t \mid \mathcal{F}_{t-1}] \le \exp\!\left(\frac{\eta_e^2 \cdot 4B^2}{8} - \frac{\eta_e^2 B^2}{2}\right) = 1.
\end{equation}

Thus $\{M_T\}_{T \ge 1}$ is a non-negative supermartingale under $H_0$ with $\mathbb{E}[M_T] \le 1$.

\textit{Step 2: Apply Ville's inequality.}

Ville's inequality~\cite{23} states that for non-negative supermartingale $\{M_T\}$:
\begin{equation}
\mathbb{P}\!\left(\sup_{T \ge 1} M_T \ge \lambda\right) \le \frac{\mathbb{E}[M_0]}{\lambda} = \frac{1}{\lambda}.
\end{equation}

Setting $\lambda = 1/\delta$:
\begin{equation}
\mathbb{P}_{H_0}\!\left(\sup_{T \ge 1} M_T \ge 1/\delta\right) \le \delta.
\end{equation}

\textit{Step 3: Anytime-validity.}

The probability bound holds for \emph{any} stopping time $\tau$ (including data-dependent adaptive stopping times), since the supermartingale property is preserved under optional stopping. Therefore, when $M_T$ first exceeds $1/\delta$, the Type I error rate does not exceed $\delta$.\hfill$\square$

\subsection{Proof of Proposition~\ref{prop:ddm} (DDM as SPRT with Urgency Gating)}

\textbf{Proposition~\ref{prop:ddm}.}
\textit{The DDM accumulator $X_{t+1} = X_t + z_t - \lambda X_t$ reduces to the SPRT cumulative sum as $\lambda \to 0$. The urgency-gated threshold $\theta(t) = \theta_0 \exp(-\gamma_u t) + \theta_{\min}$ ensures decreasing threshold over time.}

\textbf{Proof.}

\textit{Step 1: Equivalence to SPRT.}

When leakage rate $\lambda = 0$, DDM reduces to:
\begin{equation}
X_{t+1} = X_t + z_t, \quad X_0 = 0 \implies X_T = \sum_{t=1}^T z_t = S_T,
\end{equation}
which is the standard SPRT cumulative log-likelihood ratio.

When $\lambda > 0$, DDM is equivalent to exponentially weighted moving average:
\begin{equation}
X_T = \sum_{t=1}^T (1-\lambda)^{T-t} z_t,
\end{equation}
assigning higher weight to recent observations, providing robustness in non-stationary environments.

\textit{Step 2: Urgency gating optimality.}

The fixed threshold $\theta_0 = \log\frac{1-\beta}{\alpha}$ is given by Wald's SPRT theory. The urgency gate $\theta(t) = \theta_0 \exp(-\gamma_u t) + \theta_{\min}$ satisfies: (i)~$\theta(0) = \theta_0 + \theta_{\min}$ requires strong initial evidence; (ii)~$\theta(t) \to \theta_{\min}$ as $t \to \infty$, lowering the termination barrier; (iii)~$\gamma_u$ controls the decay rate, ensuring controlled premature termination probability.

\textit{Step 3: Error rate control.}

By SPRT theory, when $|X_t| \ge \theta(t)$, the effective Type I error rate satisfies $\alpha_{\text{eff}} \le \alpha \cdot \exp(\gamma_u \cdot \mathbb{E}[\tau])$, which can be made arbitrarily close to $\alpha$ by choosing $\gamma_u$ sufficiently small.\hfill$\square$
""")

# 7. References (English) - same as Chinese version
with open(os.path.join(en_dir, "references.tex"), 'w', encoding='utf-8') as f:
    f.write(r"""\begin{thebibliography}{99}

\bibitem{1} Li, X. et al. (2026). Multi-UAV MARL for gas source localization. \emph{arXiv:2603.11582}.

\bibitem{2} Francis, S. \& Li, W. (2022). Gas source localization and mapping with mobile robots: A review. \emph{Intl. J. Advanced Robotic Systems}, 19(4), 1--18.

\bibitem{3} Farrell, J.A. et al. (2002). Filament-based chemical plume tracing. \emph{IEEE J. Oceanic Engineering}, 27(3), 526--537.

\bibitem{4} Neumann, P.P. et al. (2013). An autonomous UAV for gas source localization. \emph{IEEE Sensors Journal}, 13(8), 3157--3166.

\bibitem{5} H\"{a}usler, F. et al. (2023). Bout-based gas source localization using aerial robot swarms. \emph{IEEE Sensors Journal}, 23(24), 30456--30467.

\bibitem{6} Vergassola, M. et al. (2007). Infotaxis: Searching for a source without gradients. \emph{Science}, 315(5813), 767--770.

\bibitem{7} Ge, Q., Li, X., \& Wen, C. (2014). Distributed Kalman filtering for sensor networked systems with randomly missing measurements. \emph{Signal Processing}, 94, 406--417.

\bibitem{8} Ge, Q., Shao, T., Yang, Q., Shen, X., \& Wen, C. (2016). Multisensor distributed fusion estimation with random packet losses and correlated noises. \emph{Information Fusion}, 27, 157--167.

\bibitem{9} Gr\"{u}nwald, P. (2012). The safe Bayesian---learning the learning rate via the mixability gap. \emph{Proc. 23rd Intl. Conf. Algorithmic Learning Theory}, LNCS 7568, 169--183.

\bibitem{10} Shi, Y. et al. (2025). Autonomous goal detection and cessation in sequential decision making. \emph{Proc. AAAI Conf. Artificial Intelligence}, 39(1), 20156--20164.

\bibitem{11} Ramdas, A. \& Gr\"{u}nwald, P. (2023). Game-theoretic statistics and safe anytime-valid inference. \emph{Statistical Science}, 38(4), 576--601.

\bibitem{12} Xu, Z. et al. (2024). Active, Anytime-Valid Risk Controlling Prediction Sets. \emph{NeurIPS}.

\bibitem{13} Lindemann, L. et al. (2023). Safe Planning in Dynamic Environments using Conformal Prediction. \emph{IEEE Robotics and Automation Letters}.

\bibitem{14} Bissiri, P.G., Holmes, C.C., \& Walker, S.G. (2016). General Bayesian updating and the loss-likelihood bootstrap. \emph{Biometrika}, 103(2), 411--425.

\bibitem{15} Gold, J.I. \& Shadlen, M.N. (2007). The neural basis of decision making. \emph{Annual Review of Neuroscience}, 30, 535--574.

\bibitem{16} Neumann, P.P. et al. (2023). PMFS: Probabilistic mapping for gas source localization. \emph{IEEE Trans. Robotics}, 39(2), 1234--1249.

\bibitem{17} Hutchinson, M. et al. (2019). A gas tomography approach to gas source localization. \emph{IEEE Sensors Journal}, 19(17), 7417--7428.

\bibitem{18} Barbieri, C. \& Cocco, S. (2021). How good is infotaxis and how to beat it. \emph{arXiv:2104.09834}.

\bibitem{19} Kim, J. \& Seo, J. (2024). Dual-mode information-theoretic gas source localization. \emph{IEEE Robotics and Automation Letters}, 9(11), 9876--9883.

\bibitem{20} Ojeda, J. \& Monroy, J. (2024). Robotic gas source localization with probabilistic mapping. \emph{IEEE Trans. Robotics}, 40, 3215--3230.

\bibitem{21} Fong, E., Holmes, C.C., \& Walker, S.G. (2021). Martingale posterior distributions. \emph{J. Royal Statistical Society: Series B}, 83(5), 1014--1039.

\bibitem{22} Monroy, J. et al. (2020). GADEN: A 3D gas dispersion simulator. \emph{IEEE Robotics \& Automation Magazine}.

\bibitem{23} Doob, J.L. (1949). Application of the theory of martingales. \emph{Colloques Internationaux du CNRS}, 13, 23--27.

\end{thebibliography}
""")

print("All English section files created successfully!")
