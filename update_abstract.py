with open(r'D:\ZYC\A-gas\ASCi\sci\paper-isj-final-en\main.tex', 'r', encoding='utf-8') as f:
    content = f.read()

# Update title
old_title = r"\title{Robust Estimation-Decision Coordination for UAV Gas Source Localization in Low-Wind Indoor Environments}"
new_title = r"\title{Event-Driven Bayesian Inference for UAV Gas Source Localization: A Surprisal-Weighted Generalized Bayesian Approach}"

if old_title in content:
    content = content.replace(old_title, new_title)
    print("Title updated")
else:
    print("Title pattern not found")

# Update abstract
old_abstract = r"""\begin{abstract}
Gas source localization (GSL) in low-wind indoor environments is challenged by intermittent, filamentary plumes that render continuous observation models ineffective, causing existing methods to lock onto incorrect posterior modes. We propose GBI-GSL, a UAV-based framework that addresses this through: (i) a wind-confidence-driven adaptive Generalized Bayesian Inference method with credibility-scheduled learning rate; (ii) dual-channel convergence control via anytime-valid e-processes and Drift-Diffusion Model evidence accumulation; and (iii) Gaussian process-based adaptive altitude selection. On the GADEN simulator across four scenarios (160 runs), GBI-GSL achieves 1.62\,m mean error and 92.5\% success rate, outperforming SurgeCast (2.74\,m, 30\%), GrGSL (4.86\,m, 12.5\%), and PMFS (3.43\,m, 50\%). Statistical tests confirm significance at $p < 0.01$ in most scenarios.
\end{abstract}"""

new_abstract = r"""\begin{abstract}
Intermittent, filamentary plumes in indoor environments cause existing gas source localization (GSL) methods to fail due to their reliance on continuous observation models. We propose a surprisal-weighted generalized Bayesian inference (sw-GBI) framework for UAV-based GSL that: (i)~employs binary event-driven observations where non-detection events carry localization information, (ii)~adapts the posterior tempering rate $\eta_t$ to the surprisal of each observation, achieving information-theoretically optimal KL growth (proven via the GRO framework), and (iii)~provides anytime-valid stopping with sample complexity matching the Fano lower bound. We prove that sw-GBI is robust to model misspecification ($\epsilon$-bias bounded by $C\epsilon$) while standard Bayes diverges. On the GADEN simulator across three indoor environments (10 seeds each), sw-GBI achieves $1.81\pm0.75$\,m mean error with 100\% success rate, significantly outperforming PMFS ($4.93\pm2.05$\,m), GrGSL ($5.22\pm3.22$\,m), and matching SurgeCast's precision while demonstrating superior generalization across environments.
\end{abstract}"""

if old_abstract in content:
    content = content.replace(old_abstract, new_abstract)
    print("Abstract updated")
else:
    print("Abstract pattern not found")

# Update keywords
old_keywords = r"""\begin{IEEEkeywords}
Gas source localization, unmanned aerial vehicles, generalized Bayesian inference, model misspecification, anytime-valid inference, indoor environments
\end{IEEEkeywords}"""

new_keywords = r"""\begin{IEEEkeywords}
Gas source localization, unmanned aerial vehicles, generalized Bayesian inference, surprisal weighting, anytime-valid inference, model misspecification, indoor environments
\end{IEEEkeywords}"""

if old_keywords in content:
    content = content.replace(old_keywords, new_keywords)
    print("Keywords updated")
else:
    print("Keywords pattern not found")

with open(r'D:\ZYC\A-gas\ASCi\sci\paper-isj-final-en\main.tex', 'w', encoding='utf-8') as f:
    f.write(content)
print("File saved")
