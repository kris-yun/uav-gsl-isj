import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.111.128', username='zyc', password='123456')

# Read file
stdin, stdout, stderr = client.exec_command('cat /home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp')
# We need to read the paper, not code
client.close()

# Read local paper
with open(r'D:\ZYC\A-gas\ASCi\sci\paper-isj-final-en\main.tex', 'r', encoding='utf-8') as f:
    content = f.read()

# Update contributions section
old_contributions = r"""\subsection{Contributions}

\begin{enumerate}
\item \textbf{Wind-confidence-driven adaptive GBI with heterogeneous loss weights.} We propose an adaptive learning rate $\eta$ that is a \emph{credibility-scheduled parameter} driven by wind confidence $c_w$: high $\eta$ (0.6--0.9) when gas is detected with stable wind, low $\eta$ (0.15--0.5) for non-detection events. We prove exponential-rate posterior concentration under the logistic detection model (Theorem~\ref{thm:contraction}).

\item \textbf{Dual-channel stopping with anytime-valid guarantees.} We construct a dual-channel stopping mechanism combining (i)~a Hoeffding e-process on MAP residuals providing distribution-free anytime-valid guarantees via Ville's inequality (Theorem~\ref{thm:eprocess}), and (ii)~a DDM with urgency gating for robust termination under non-stationary conditions (Proposition~\ref{prop:ddm}).

\item \textbf{Logistic detection model calibrated to indoor filament dynamics.} We formalize gas detection as discrete events with a logistic probability model, replacing both the continuous Gaussian observation model and the exponential decay model. We establish a formal connection to the randomly missing measurement framework~\cite{7,8}.

\item \textbf{GP-based adaptive height selection for unknown source altitude.} We introduce a Gaussian process-based altitude selection mechanism that enables the UAV to locate sources at unknown heights.
\end{enumerate}"""

new_contributions = r"""\subsection{Contributions}

\begin{enumerate}
\item \textbf{Surprisal-weighted generalized Bayesian inference (sw-GBI) with information-theoretic optimality.} We propose an adaptive loss weight $\eta_t = -\log P(y_t \mid \hat{s}_{\mathrm{MAP}})$ that equals the surprisal of each observation under the current MAP hypothesis. Building on the Gibbs posterior framework of Bissiri et al.~\cite{bissiri2016}, we prove that this weighting achieves the optimal KL growth rate (Theorem~\ref{thm:surprisal_optimality}), leveraging the GRO framework of Gr\"{u}nwald et al.~\cite{grunwald2024safe}. Unlike Thompson Sampling, our method is purely deterministic and parameter-free, adapting to non-stationary wind conditions without exploration bonuses.

\item \textbf{E-process stopping rule matching the information-theoretic lower bound.} We construct an anytime-valid stopping mechanism using likelihood-ratio e-values (Theorem~\ref{thm:eprocess}), and prove that the expected sample complexity $E[T] = O(\log(1/\alpha))$ matches the Fano lower bound up to constants (Theorem~\ref{thm:near_optimality}). This is the first principled stopping rule for gas source localization with theoretical guarantees, distinguishing our approach from all existing methods that use fixed-step or ad hoc termination.

\item \textbf{Robustness to model misspecification via adaptive tempering.} We prove that under $\epsilon$-parameter misspecification of the diffusion model, the sw-GBI posterior bias is bounded by $C\epsilon$, while the standard Bayesian posterior ($\eta=1$) diverges (Theorem~\ref{thm:robustness}). This provides the first theoretical justification for why adaptive tempering outperforms standard Bayes in realistic gas dispersion scenarios where the model is inherently misspecified.

\item \textbf{Wind-enhanced binary observation efficiency for GSL.} We analyze the Fisher information efficiency of binary sensing under wind-modulated detection, showing that the classical $2/\pi$ bound is improved by wind direction information (Lemma~\ref{lem:binary_efficiency}). This establishes the theoretical foundation for event-driven gas sensing and distinguishes our binary observation model from generic quantization results.
\end{enumerate}"""

if old_contributions in content:
    content = content.replace(old_contributions, new_contributions)
    print("Contributions section updated successfully")
else:
    print("WARNING: Could not find old contributions section")
    # Try partial match
    if "Wind-confidence-driven adaptive GBI" in content:
        print("Found partial match, attempting replacement...")

with open(r'D:\ZYC\A-gas\ASCi\sci\paper-isj-final-en\main.tex', 'w', encoding='utf-8') as f:
    f.write(content)
print("File saved")
