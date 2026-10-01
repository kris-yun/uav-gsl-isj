# PMFS3D-R1P5 remote-theory audit — 2026-10-01

Status: **THEORY WATCH ONLY / NOT A NOVELTY CLAIM**

## Why theory is deferred until R1P5

R1 shows that Oracle-3D does not increase the true-source log score in the four development cases. The observed 3-D gain is suppression of wrong hypotheses. Before importing any far-domain theory, R1P5 must establish that this is broad and cross-seed stable rather than a one-competitor artifact.

## Candidate mother idea: counterexample-guided reasoning

### 2026 anchor

**Yang et al., "ExVerus: Verus Proof Repair via Counterexample Reasoning", ICML 2026, PMLR 306.**

- Official proceedings: https://proceedings.mlr.press/v306/yang26bt.html
- Code artifact: https://github.com/claudeyj/exverus

The useful abstraction is not "negative weighting". ExVerus uses behavioral counterexamples produced and validated by a verifier; those counterexamples are then generalized into constraints/invariants that block failing proof candidates.

Potential GSL transfer, only if R1P5 passes:
- source candidate = hypothesis;
- 3-D transport forward operator = verifier;
- observed confident cells = behavioral constraints;
- candidate-specific contradictions = counterexamples;
- repeated validated contradictions eliminate or constrain false source hypotheses;
- surviving hypotheses are normalized back into a PMFS-compatible source probability map.

This would be a **hypothesis falsification/elimination architecture**, not another additive likelihood term.

### 2025 supporting theory

**Hallahan, Jhala & Piskac, "Counterexample-Guided Inference of Modular Specifications", PACMPL/OOPSLA 2025, DOI 10.1145/3720505.**

- DOI: https://doi.org/10.1145/3720505
- Bibliographic record/abstract: https://researchconnect.suny.edu/en/publications/counterexample-guided-inference-of-modular-specifications/

This paper is relevant because it formalizes an inference loop parameterized by a verifier, counterexample generator and synthesizer, with soundness/completeness results under stated finite assumptions. It is a theoretical analogy, not evidence that the same guarantees hold for GSL.

## Critical prior-art collision: ordinary negative evidence is old in OSL

Do **not** claim novelty for:
- absence of gas detection;
- non-detection likelihood;
- reducing source probability because an expected detection was absent.

Robot infotaxis explicitly includes time intervals with no detection in its likelihood, and Bayesian odor-source likelihood mapping has long updated source maps using both detection and non-detection events.

Examples:
- Robot infotaxis implementation: https://pmc.ncbi.nlm.nih.gov/articles/PMC2856589/
- OSL review describing detection/non-detection Bayesian updates: https://onlinelibrary.wiley.com/doi/10.1002/tee.23364

Therefore any future claim must be materially narrower and stronger:

> structured, candidate-specific 3-D transport contradictions used as counterexamples to falsify source hypotheses,

not simply "use negative evidence".

## Initial direct-collision screen

Keyword searches for combinations of:
- counterexample-guided + odor source localization
- counterexample-guided + gas source localization
- falsification + odor source localization

did not surface an obvious direct OSL method implementing a verifier/counterexample elimination loop. This is **not** proof of novelty. A full Scite/Scholar/IEEE/Scopus-style prior-art screen is required before paper-level promotion.

## Promotion rule

Only if R1P5 returns:
`PMFS3D_R1P5_SELECTIVE_FALSE_SUPPRESSION`

may the next phase define a counterexample object and a non-additive hypothesis-elimination algorithm.

If R1P5 is HOLD or STOP, this theory remains an analogy and is not used to rescue the line.
