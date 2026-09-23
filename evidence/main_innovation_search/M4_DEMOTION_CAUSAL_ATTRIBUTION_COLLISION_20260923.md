# Candidate ranking update — M4 demoted after causal source-attribution collision

Date: 2026-09-23

A NeurIPS 2025 CauScien workshop paper already frames atmospheric pollution source attribution as causal inference, treats sources as interventions/treatments, uses mechanistic dispersion with meteorology, and discusses counterfactual source interventions.

Therefore:
- `source = do(S=s)` is not by itself a main novelty;
- generic causal plume/source attribution is not open.

M4 survives only as:
- learned compositional mechanism factorization;
- unseen source×wind recombination;
- structural auxiliary to M6 CF-PFM.

Updated priority:

1. **M6 / CF-PFM — current lead main candidate**
2. M3 stochastic world model — only if stochasticity is needed
3. M4 compositional intervention — auxiliary unless C0 is unusually strong
4. M5 — HOLD/auxiliary

M4 C0 should still be run because a positive recombination result could justify it as a strong auxiliary module.
