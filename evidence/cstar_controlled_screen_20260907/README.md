# Bounded M1 causal / M2 strong-null screen, 2026-09-07

**M1_CONTROLLED_SCREEN_NO_GO. Production closed loop remains unauthorized.**
This is the current CSTAR/PICR prototype, not a verdict on every causal method
or on all earlier algorithms named M1. A 200-update screen is a bounded
falsification experiment, not proof of asymptotic impossibility.

Training/config source: `060ca43`. Independent verifier source: `2050d06`.
Real VM: `/home/zyc/CSTAR_CONTROLLED_SCREEN_20260907`, Python/Torch identities
in RUN_START.json. Twelve offline model fits = four controls x three folds;
these are **not** the prohibited twelve production closed-loop arms.
No new seed, route, source placement, raw-query read, horizon, threshold or
split was introduced. The same seed12 initialization and 200 sampled paired
updates were used for all four model variants in each fold. No outcome-driven
rerun, extended budget, hyperparameter search or checkpoint selection occurred.

## M1 results

NLL and localization error are lower-is-better; errors are XY MAP errors.
Each row averages all 15 prefixes x four held-out parents (not 60 independent
experimental worlds). Full candidate supports are 6,866 / 6,811 / 7,258 cells.

| Held-out House | PICR NLL | Unconstrained NLL | Context-only NLL | PICR error m | Unconstrained error m | Context-only error m |
|---|---:|---:|---:|---:|---:|---:|
| H01 | 23.840 | 24.225 | 15.962 | 2.522 | 2.732 | 1.784 |
| H02 | 24.560 | 19.187 | 34.162 | 2.688 | 2.669 | 2.148 |
| H03 | 26.449 | 31.404 | 24.142 | 6.182 | 6.329 | 5.832 |

H01/H03 superficially improve over the unconstrained encoder. However **0/3
Houses pass all preregistered causal-screen checks**:

- H01: absolute same-source zS distance shrinks, but different-source separation
  also shrinks; the same/different ratio worsens (1.383 versus 1.375). It loses
  to context-only. zS swap does not worsen localization as required.
- H02: invariance ratio improves substantially (0.108 versus 0.397), yet NLL
  and localization get worse. Invariance alone did not yield usable inference.
- H03: same-source zS distance increases (0.826 versus 0.412), source separation
  shrinks, and label-permuted training does better than true-label PICR
  (NLL 17.825, error 5.383 m). zS swapping also improves both task metrics.
- Every House loses in NLL to its uniform posterior (8.834 / 8.826 / 8.890).
  This is a proper-score comparison; uniform MAP tie-breaking is not a valid
  localization-success argument.
- With measured gas and local wind zeroed, normalized mean posterior entropy
  remains 0.461 / 0.658 / 0.482, with zero abstentions. The prototype can be
  confidently wrong without those source-related measurements.

These are evidence of poor held-out calibration and context dependence, not a
code-startup failure. Training-house NLLs are approximately 3.75--5.55 whereas
held-out NLLs are 23.84--26.45, demonstrating a substantial generalization gap.
Context-only retains wind/pose/time; it is not an oracle and does not read source
truth. Its performance and the destructive controls prevent claiming that gas
information and causal disentanglement are load-bearing improvements.

Scientific limitations remain: only four exact sources occur in each training
fold. Cross-source records are not matched do(source) interventions under the
same nuisance: generator transport settings, and sometimes gas type, differ
between source groups. Thus the cross-source separation loss is discriminative,
not evidence of isolated source causality. The same-source fast/slow pairing is
provenance-qualified, but stochastic release draws are not matched. The full
theoretical adversary/reconstruction/dual-constraint model was not implemented
by this reference screen. These limitations must not be hidden by a PASS label.

## M2 strong-null result

Fit only the two training Houses: a conditional first-hit histogram given the
current gas threshold indicator, with one total Dirichlet pseudocount over 21
outcomes. No source, route, future gas or future wind is a model input.

| Held-out House | NLL | Brier | Exact first-hit label accuracy | Unconditional train-histogram NLL |
|---|---:|---:|---:|---:|
| H01 | 0.03560 | 0.00336 | 100.00% | 0.64000 |
| H02 | 0.11464 | 0.02429 | 98.81% | 0.71904 |
| H03 | 0.35031 | 0.09227 | 95.24% | 1.07183 |

The prior post-hoc 98% diagnostic survives proper train-only fitting and
held-out scoring. This is a strong null, not learned CPO success. Only 5/84
shared contexts have route-dependent first-hit labels under the frozen target.
The required causal-plume/FOPDT and verified-physics prior bindings, and a
learned CPO comparison, remain absent. No simple empirical/plume formula was
renamed a verified physical prior, and CPO was not trained in this screen.

## Checks and next decision

Independent artifact recomputation verifies 2,700 stored M1 prediction rows
(held-out, training diagnostics and destructive controls), all 252 M2 cases,
checkpoint hashes, exact 200-step budgets, train-only fitting, zS-zero uniformity,
zS-swap execution and the reported gate Boolean. Mandatory reference, model,
environment, provenance and review regression tests all pass. Verification PASS
does not change the scientific NO-GO.

Do not deploy these PICR checkpoints or expand seeds to rescue them. A new
revision needs to address source information versus context dependence,
cross-source nuisance confounding and uncertainty calibration; M2 needs a
defensible route-sensitive prediction objective or evidence that it beats the
strong null and both required physical priors. Preserve the current negative
results; do not silently change their loss, event threshold, route or horizon.

Portable verification from the full archive root (Python + NumPy):

```text
python -B experiments/ctpi_cstar/verify_controlled_screen.py --results evidence/cstar_controlled_screen_20260907
```

This rechecks stored predictions without loading/training models or modifying
the archive. Full model reproducibility additionally requires the Torch version
in RUN_START.json. The archive includes every checkpoint, not only a winning fit.
