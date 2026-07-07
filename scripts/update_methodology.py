import re

f = r'D:\ZYC\A-gas\ASCi\sci\paper-isj-zh\sections\methodology.tex'
with open(f, encoding='utf-8') as fh:
    content = fh.read()

# Update the search strategy section to remove Layer 2 adaptive EIG
# Replace the ED-EIG section with a cleaner version
old_ed_eig = r"""\subsection{Event-Driven Search Strategy}
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
\end{definition}"""

new_ed_eig = r"""\subsection{Event-Driven Search Strategy}
\label{sec:ed_eig}

Standard Infotaxis~\cite{ref8} selects actions to maximize expected information gain (EIG) over the continuous observation $z_t$. We adapt this to the event-driven model, where the key insight is that \emph{non-detection} ($d=0$) carries positive information for source exclusion.

\begin{definition}[Event-Driven EIG]
\label{def:ed_eig}
The event-driven expected information gain for action $a$ is:
\begin{equation}
\mathrm{ED\text{-}EIG}(a \mid \pi_t) = H(\pi_t) - \mathbb{E}_{d}\!\bigl[H(\pi_{t+1} \mid d, a)\bigr]
\label{eq:ed_eig}
\end{equation}
where the expectation is over the binary event $d \in \{0,1\}$:
\begin{equation}
\mathbb{E}_{d}\!\bigl[H(\pi_{t+1})\bigr] = P(d\!=\!1 \mid a, \pi_t)\, H(\pi_{t+1} \mid d\!=\!1) + P(d\!=\!0 \mid a, \pi_t)\, H(\pi_{t+1} \mid d\!=\!0)
\end{equation}
with $P(d\!=\!1 \mid a, \pi_t) = \sum_s \pi_t(s)\,(1 - \exp(-\lambda(x_t+a, s)\,\Delta t))$.
\end{definition}

\begin{proposition}[Non-degeneracy of ED-EIG]
\label{prop:nondeg}
For any non-degenerate posterior $\pi_t$ (i.e., $H(\pi_t) > 0$), there exists an action $a$ such that $\mathrm{ED\text{-}EIG}(a \mid \pi_t) > 0$.
\end{proposition}

\begin{proof}
By source identifiability (Proposition~\ref{prop:identifiability}), for any two candidates $s_1, s_2$ with $\pi_t(s_i) > 0$, there exists a measurement position $x$ where $P(d\!=\!1 \mid x, s_1) \neq P(d\!=\!1 \mid x, s_2)$. Choosing $a$ to move to $x$, the mutual information $I(s; d \mid x, \pi_t) > 0$ by the data processing inequality. Critically, the non-detection branch alone contributes positive information: observing $d\!=\!0$ at $x$ excludes candidates near $x$ (where $\lambda$ is large), strictly reducing entropy. This ensures $\mathrm{ED\text{-}EIG} > 0$ even when no gas is detected---unlike the continuous model where $z \approx 0$ yields $\mathrm{EIG} \approx 0$.
\end{proof}"""

if old_ed_eig in content:
    content = content.replace(old_ed_eig, new_ed_eig)
    print('Updated ED-EIG section with non-degeneracy proof')
else:
    print('ED-EIG section pattern not found, checking...')

# Write back
with open(f, 'w', encoding='utf-8') as fh:
    fh.write(content)
print('Done')
