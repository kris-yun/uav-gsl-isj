# UAV Gas Source Localization — ME-ACI V11 paper/analysis branch

> **This is the paper-positioning and offline-analysis branch.**  
> Repository: `kris-yun/uav-gsl-isj`  
> Branch: `meaci-v11-paper-three-contributions`  
> Qualified runtime branch: `meaci-v11-reversible-cumulative`  
> **Do not change the frozen V11 runtime equations or planner from this branch.**

## Current scientific status

ME-ACI V11 has passed the current preregistered three-House unseen-seed qualification using the official PMFS final top-5% probability-weighted source-location error:

| House / seed | PMFS OFF | V11 ON | Improvement |
|---|---:|---:|---:|
| H01 / 825101 | 7.3619 m | 5.7601 m | +21.76% |
| H02 / 825201 | 2.4220 m | 1.4232 m | +41.24% |
| H03 / 825301 | 7.5100 m | 6.8596 m | +8.66% |
| pooled | 17.2938 m | 14.0429 m | **+18.80%** |

All three Houses improved.  The frozen catastrophic-regression criterion was not triggered and no new false-confident collapse was observed.

**Interpretation:** V11 is a frozen positive **online source-inference** candidate.  The present evidence does not yet justify population-level statistical generalization from only three held-out pairs, and it does not prove universal planner-mediated improvement.

## Final method structure: one framework, three technical modules

The authoritative contribution contract is:

**[`docs/V11_THREE_MODULES_REFRAMED.md`](docs/V11_THREE_MODULES_REFRAMED.md)**

The final paper architecture is:

```text
completed gas / wind / pose events
        |
        v
ACIT  — Amplitude-Conditioned Inverse Transport
        |   constructs source-abduction evidence
        v
STRI  — Spatiotemporal Replication Identifiability
        |   decides whether evidence is identifiable enough to release
        v
R-GAF — Reversible Generalized Assimilation Filter
        |   assimilates new evidence and allows later falsification
        v
PMFS source state / source estimate
```

### Module 1 — ACIT

**Amplitude-Conditioned Inverse Transport（幅值条件化逆输运）**

Treat candidate source locations as physical causes and plume hit/miss events as downstream effects.  Condition on observed hit count to suppress unknown release/sensor amplitude in the binary event-ordering comparison, and marginalize the frozen 54-member transport nuisance family.

Main role: **how source evidence is constructed under plume/model mismatch.**

### Module 2 — STRI

**Spatiotemporal Replication Identifiability（时空复现可辨识）**

Release source evidence only when both disjoint temporal folds contain hit/miss contrast and hits occur at at least two distinct occupied sensing cells.

Main role: **when source evidence is reproducible/identifiable enough to trust.**

Existing H02/825201 offline counterfactual shows that removing only the multi-site spatial replication condition can force an early top candidate about 4.79 m from truth even though the nearest physical candidate is about 0.293 m away.

### Module 3 — R-GAF

**Reversible Generalized Assimilation Filter（可逆广义同化滤波器）**

Let `g_t(s)` be the cumulative V11 generalized source score.  Define the generalized evidence innovation

```text
Delta g_t(s) = g_t(s) - g_{t-1}(s).
```

R-GAF performs the recursive update

```text
q_t(s) proportional to q_{t-1}(s) * exp(Delta g_t(s)).
```

Because the increments telescope, this is exactly equivalent to V11's full-history fixed-prior reconstruction:

```text
q_t(s) proportional to q_0(s) * exp(g_t(s)).
```

This gives three explicit properties:

1. sequential/batch equivalence;
2. no double counting of retained history;
3. later evidence can demote an earlier preferred source basin.

The verifier is:

```text
analysis/verify_rgaf_telescoping.py
```

On archived H01/H02/H03 V11 score pairs, the recursive reconstruction agrees with stored V11 posterior masses to approximately `1e-15` maximum absolute error.

## Theory lineage

The paper-positioning branch records the following 2025–2026 far-domain theoretical lineage without claiming theorem transfer:

- Andreou, Chen & Bollt, **Assimilative causal inference**, *Nature Communications* (2026): cause-from-effect inverse/assimilation framing.
- Park, Balakrishnan & Wasserman, **Robust universal inference for misspecified models**, *Biometrika* (2026): separated-data relative-fit reasoning under misspecification.
- Fong & Yiu, **Asymptotics for a class of parametric martingale posteriors**, *Biometrika* (2026): modern sequential/predictive posterior theory.
- Wu et al., **Adaptive Nonparametric Perturbations of Parametric Models with Generalized Bayes**, *JMLR* (2026): generalized updating for misspecified scientific models.
- **Deep Bayesian Filter**, ICML 2025: explicit recursive assimilation/filter-module design precedent.
- **Replicable Distribution Testing**, NeurIPS 2025: replicability as a statistical design principle.

Exact claim boundaries and module-specific use of these works are documented in `docs/V11_THREE_MODULES_REFRAMED.md`.

## Important terminology boundary

The final V11 released score uses candidate-relative normal-rank aggregation.  Therefore use:

- `conditional inverse-transport score`;
- `generalized/decision posterior`;
- `generalized evidence innovation`;
- `reversible generalized assimilation`.

Do **not** call the final rank aggregate:

- exact Bayesian likelihood;
- Bayes factor;
- calibrated posterior probability.

## Branch files relevant to the paper

- `docs/V11_THREE_MODULES_REFRAMED.md` — **authoritative three-module contribution contract**.
- `docs/V11_THREE_CONTRIBUTION_POSITIONING.md` — earlier contribution decomposition and offline mechanism evidence.
- `docs/AUXILIARY_2025_2026_SCREEN.md` — screen of additional conformal/planner modules and why they are not inserted into frozen V11 now.
- `analysis/verify_rgaf_telescoping.py` — verifies the R-GAF recursive/telescoping identity from archived candidate-score CSVs.
- `analysis/v11_offline_contribution_audit.py` — offline contribution/ablation analysis.

## Next experiment

Do not modify ACIT, STRI, R-GAF, the 54-member family, PMFS planner, cadence, evaluator or 300-s budget.

The next stage is **independent multi-seed validation** of the frozen V11 method, followed by paired uncertainty/statistical analysis.  Any conformal calibration or new active-planning module must be treated as a separate future study rather than silently added to the already-qualified V11 treatment.
