# R0 PASS Update for Auxiliary Pro

Date: 2026-09-24

Primary-thread independent review has confirmed:

`R0_PASS_STOCHASTIC_BENCHMARK_USABLE`

Review commit:
`7b92b9a1265513baaba794a74999abfb7ae9f4b6`

Read:
`evidence/stochastic_benchmark_refoundation/R0_INDEPENDENT_REVIEW_AND_OBJECT_SELECTION_20260924.md`

## Mainline interpretation now fixed by primary thread

R0 does **not** justify a full 300-D path distribution mainline.

The empirically strongest stable object is:

**source-conditioned encounter / support structure**

Key independent findings:

- two 8/8 variability split Spearman: 0.721 / 0.742;
- median total mass split Spearman: 0.979 / 0.967;
- median zero-fraction split Spearman: 0.997 / 0.977;
- first-arrival ordering is extremely stable but discrete/tied;
- 10×30 binary encounter-probability field converges rapidly:
  - K=8 vs K=16 relative profile error median ~0.081, q75 ~0.097;
  - K=12 vs K=16 median ~0.043, q75 ~0.052.

Exploratory 18-source held-out analysis:
- Bernoulli encounter likelihood top-1 ~90%, top-3 ~99–100% in both 8/8 directions.

This exploratory result is **not** a mainline gate and does not satisfy the >=143-candidate requirement.

## Prior-art constraint

Simple encounter-probability Bayesian olfactory search is already occupied.

In particular 2025 Physical Review Fluids work by Heinonen et al. extracts spatially dependent encounter statistics from realistic turbulent DNS and builds Bayesian olfactory-search policies.

Therefore do NOT propose:
- “binary encounter likelihood”;
- “use hit/no-hit instead of ppm”;
- “Bayesian source map from encounter probability”
as the main innovation.

## Your narrowed auxiliary task

Deeply investigate two far-domain theory families only:

### A. Event-process theory
- marked point processes;
- renewal processes;
- survival / first-passage;
- sparse event coding;
- predictive state representations for event sequences.

Question:
Can these provide a genuinely new **source-conditioned temporal encounter process** beyond existing independent encounter likelihoods?

### B. Multiscale identifiability / emergence
- causal emergence;
- effective information;
- stochastic coarse-graining;
- information-theoretic identifiable macrostates;
- multiscale source equivalence classes.

Question:
Can these explain/derive why exact 0.30 m source cells may be stochastic microstates while a coarser source basin has higher reproducible information?

Prioritize 2025/2026 peer-reviewed top work and code.

For each family return:
1. strongest 2025/2026 theory anchors;
2. exact mathematical object;
3. nearest GSL/olfaction prior art;
4. what would be genuinely new;
5. how it maps to PMFS probability map;
6. a >=143-candidate offline falsification design;
7. STOP condition.

Do not choose the winner. The primary thread will decide after comparing both families against the R0 data.
