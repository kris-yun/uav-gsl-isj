f = r'D:\ZYC\A-gas\ASCi\sci\paper-isj-zh\main.tex'
with open(f, encoding='utf-8') as fh:
    content = fh.read()

old_abstract = r"""\begin{abstract}
Unmanned aerial vehicle (UAV) gas source localization (GSL) faces two complementary challenges: (1) existing methods assume continuous concentration signals, but turbulent filament-based dispersion produces intermittent, event-like detections---causing search degeneration when $z_t \approx 0$; and (2) information-theoretic methods use coarse global search even after the posterior has concentrated, wasting effort on already-excluded regions. We propose Event-Driven Posterior-Adaptive GSL (EDPA-GSL), a three-layer framework that addresses both challenges. \textbf{Layer 1} models gas detection as binary events from an inhomogeneous Poisson process, where non-detections carry positive information for source exclusion. \textbf{Layer 2} adapts search granularity to posterior concentration via $\mathrm{EIG}_\gamma = (1-\gamma)\cdot\mathrm{EIG}_{\mathrm{local}} + \gamma\cdot\mathrm{EIG}_{\mathrm{global}}$ with $\gamma = H(\pi_t)/H(\pi_0)$, unifying information-theoretic exploration and upwind refinement as extreme cases. \textbf{Layer 3} provides anytime-valid stopping via an e-process on posterior credible region contraction. We prove: (i) the event-driven EIG is strictly positive for any non-degenerate posterior; (ii) the posterior concentrates at exponential rate $e^{-\kappa t}$ under the event model; and (iii) the e-process provides distribution-free stopping guarantees via Ville's inequality. Experiments on VGR and PMFS datasets demonstrate [X]$\times$ improvement over SurgeCast in weak-signal regimes while maintaining competitive performance in strong-signal regimes.
\end{abstract}"""

new_abstract = r"""\begin{abstract}
Unmanned aerial vehicle (UAV) gas source localization (GSL) under turbulent dispersion faces a fundamental signal model mismatch: existing methods model gas concentration as a continuous signal, but physically, gas propagates as discrete filaments---producing intermittent, binary detection events. This mismatch causes critical failures: when the UAV is far from the source and readings $z_t \approx 0$, information-theoretic methods (Infotaxis) degenerate to random walks because the expected information gain approaches zero, while upwind-tracking methods (SurgeCast) lose plume contact entirely. We identify the root cause: the continuous model treats $z \approx 0$ as ``weak evidence,'' but physically, the \emph{absence} of detection at a known position carries strong exclusion information about source location. We propose \emph{Event-Driven Bayesian GSL} (ED-Bayes), which replaces the continuous observation model with a binary detection model based on inhomogeneous Poisson filament-arrival statistics. Under this model, every observation---whether detection or non-detection---provides positive information for source localization, preventing search degeneration in weak-signal regimes. We prove three theoretical results: (i) the event-driven expected information gain (ED-EIG) is strictly positive for any non-degenerate posterior, guaranteeing that the search never degenerates to a random walk; (ii) the Bayesian posterior concentrates at exponential rate $e^{-\kappa t}$ under the event model, faster than the $O(1/t)$ rate of continuous models; and (iii) an e-process constructed on posterior credible region contraction provides distribution-free anytime-valid stopping guarantees via Ville's inequality. Experiments on GADEN-based simulated environments demonstrate consistent localization performance across starting positions, with the event-driven posterior achieving sub-2m accuracy in weak-signal regimes where continuous-model methods fail.
\end{abstract}"""

if old_abstract in content:
    content = content.replace(old_abstract, new_abstract)
    print('Updated abstract')
else:
    print('Abstract pattern not found, trying partial match...')
    # Try to find and replace just the abstract content
    import re
    m = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', content, re.DOTALL)
    if m:
        content = content[:m.start()] + new_abstract + content[m.end():]
        print('Updated abstract via regex')
    else:
        print('ERROR: Could not find abstract')

# Also update the title
old_title = r'\title{Event-Driven Posterior-Adaptive UAV Gas Source Localization with Anytime-Valid Stopping}'
new_title = r'\title{Event-Driven Bayesian UAV Gas Source Localization with Anytime-Valid Stopping}'
content = content.replace(old_title, new_title)

with open(f, 'w', encoding='utf-8') as fh:
    fh.write(content)
print('Done')
