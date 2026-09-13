# Literature trace and exact borrowing boundary

## Peer-reviewed 2026 anchors

1. Lang, D. & Hogg, D. W. *Principled Point-source Detection in Collections of
   Astronomical Images*. **The Astronomical Journal 171, 231 (2026)**.
   DOI: https://doi.org/10.3847/1538-3881/ae4505
   Borrowed principle: matched detection is valid only under explicit signal and
   noise assumptions. This supports the matched-source control, not novelty.

2. *Joint communication and sensing with structured beams carrying orbital
   angular momentum*. **Nature Communications (2026)**.
   URL: https://www.nature.com/articles/s41467-026-69493-y
   Borrowed principle: localization with a response dictionary is an ill-
   conditioned structured inverse problem; localization claims require resolving
   response ambiguity. We do not borrow its hardware, OAM representation or
   precomputed environment library.

3. Bhattacharjee, R., Rittler, N. & Chaudhuri, K. *Beyond Discrepancy: A Closer
   Look at the Theory of Distribution Shift*. **ALT 2026, PMLR 313**.
   URL: https://proceedings.mlr.press/v313/bhattacharjee26a.html
   Borrowed principle: transfer under distribution shift requires a shared
   projection/invariant structure; reducing discrepancy alone is not a guarantee.
   This motivates the cross-House falsification rule, not the estimator formula.

## Current 2026 preprint inspiration

4. Mustafa, A. et al. *Blind mitigation of foreground-induced biases on
   primordial B modes for ground-based CMB experiments* (2026).
   URL: https://arxiv.org/abs/2603.11026
   Status: preprint, not presented as a top-journal result.
   Borrowed principle: deproject selected foreground moments and check whether
   the physical association removes bias.

## Mature mathematical foundation

5. Remazeilles, M., Delabrouille, J. & Cardoso, J.-F. *CMB and SZ effect
   separation with constrained Internal Linear Combinations*. MNRAS 410,
   2481-2487 (2011). DOI: https://doi.org/10.1111/j.1365-2966.2010.17624.x

6. Erler, J. et al. *Introducing constrained matched filters for improved
   separation of point sources from galaxy clusters*. MNRAS (2019).
   URL: https://arxiv.org/abs/1809.06446

These establish constrained minimum-variance deprojection. They do not establish
MC-SCSP performance in gas-source localization; that is why the one-shot gate
and shuffled/legacy controls are mandatory.

