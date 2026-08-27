# CG-PC-CTT V4 — Observation-Conditioned Causal Residual Assimilation (OC-CRA)

Date: 2026-08-27
Status: **DESIGN FREEZE DRAFT / NO PERFORMANCE CLAIM**
Parent: `research/cg-pc-ctt-v3-observation-quotient-theory`

The name is a working research name. “Causal” means a source-specific residual channel conditioned on measured transport/context. It does **not** claim a general proximal-identification theorem.

## 0. Evidence boundary

Frozen V3-ORR confirmatory verdict remains `CG_PC_CTT_MULTI_SEED_NOT_GO`:

- 18/30 matched pairs improved;
- pooled reduction 4.02%;
- paired sign p=0.181;
- House01 degraded;
- V3-ORR introduced zero false-confident collapses.

Seeds 0..9 and every artifact from that matrix are now **development/post-hoc evidence only**. They may never again be described as held-out.

### New post-hoc structural diagnostics

These diagnostics are used only to identify mechanism; they are not confirmatory results.

1. **First-RELEASE hold counterfactual.** Re-evaluating the saved posterior from the first accepted V3-ORR update and holding that state to the endpoint gives approximately:
   - 21/30 improved;
   - pooled reduction 17.61%;
   - House01 +2.61%, House02 +24.59%, House03 +24.78%;
   - one-sided sign p≈0.0214;
   - bootstrap 95% interval for pooled reduction approximately [9.73%, 24.59%];
   - zero false-confident collapses.
   This policy was not preregistered and therefore is **not** evidence of GO. It shows that later state replacement is a major failure mechanism.

2. **Naive cumulative RELEASE-product diagnostic.** Multiplying the saved per-RELEASE V3 evidence instead of replacing the previous accepted state gives approximately:
   - 21/30 improved;
   - pooled reduction 9.98%;
   - House01 -5.99%, House02 +14.40%, House03 +18.95%.
   Therefore preserving history is necessary but not sufficient; reliability discrimination is still required.

3. Across 22 observed transitions from one RELEASE posterior to a later RELEASE posterior, 14 increase truth-evaluated error and 8 reduce it. Harmful transitions have substantially larger posterior displacement in this development matrix. This motivates cumulative evidence and cross-window consistency, but no displacement threshold may be tuned from these outcomes.

4. **Important audit correction:** `odd_events=0` in an ABSTAIN row does not prove that odd events were absent. `ObservationResolvedV3::compute()` returns immediately when the even fold is non-identifying, before the odd-fold audit counters are filled. V4 logging must fill all fold counts before any early return.

5. In all 105 V3 source-update audits, `nuisance_rank == event_count/8`. The runtime contract uses `maxUpdatesPerStop=8`; the candidate forward probability is identical for the eight repeated blocks at one physical stop. This is direct evidence that block-level columns are pseudo-replicated spatial prediction dimensions. V4 must use the **physical stop** as the primary inferential unit.

## 1. 2026 cross-domain theory actually used

V4 is not another gate stack. It combines four explicit transferable ideas.

### 1.1 Prior-corrector rather than prior replacement

Wang et al., **Learning missing physics from legacy simulators with alternating neural integrators**, Nature Communications (2026), DOI `10.1038/s41467-026-74002-2`.

Transfer: PMFS is a useful but imperfect executable legacy inference system. The new module must **reuse and correct** it at the scale supported by new evidence; it must not zero the PMFS posterior and start again from a uniform prior.

### 1.2 Bayesian assimilation and conditional causal information

Andreou, Chen & Bollt, **Assimilative causal inference**, Nature Communications (2026), DOI `10.1038/s41467-026-68568-0`.

Transfer: treat source inference as forecast/prior + observation analysis. Information is justified by observation-induced reduction/likelihood under explicit observational uncertainty. Nuisance/context influence must be conditioned rather than counted as source evidence.

### 1.3 Model-error versus observation-error covariance

2026 Earth-system data-assimilation synthesis in npj Artificial Intelligence (`10.1038/s44387-026-00107-0`).

Transfer: transport-member variability and sensor/observation uncertainty are distinct covariance objects. A pseudoinverse of transport covariance alone is not an observation model.

### 1.4 A temporal marker inside one spatial stop

Somer, Mannor & Alon, **Temporal tissue dynamics from a spatial snapshot**, Nature (2026), DOI `10.1038/s41586-025-09876-1`.

Transfer: repeated measurements at one spatial stop are not eight independent spatial constraints. They form one temporal observation unit. V4 first uses their hit fraction as the source-coupled statistic and records mean/log-SD/slope as a fixed temporal marker for adequacy/ablation. No unvalidated temporal feature is allowed to enter source ranking merely because it sounds biologically inspired.

## 2. Runtime statistical units

### 2.1 Block

One completed `StopAndMeasure` block. Current runs use ten raw sensor samples per block.

### 2.2 Physical stop — primary inferential unit

A maximal contiguous sequence of blocks collected without changing the measurement grid cell. Let stop `j` contain `B_j` blocks.

For block outcomes `y_jb in {0,1}` and block-average concentration `c_jb`, define:

`r_j = (1/B_j) sum_b y_jb`

`u_jb = log(1 + max(c_jb,0))`

and the fixed diagnostic marker

`M_j = [mean(u), sd(u), r_j, slope(u versus causal block time)]`.

**Primary V4 source scoring uses `r_j`; it does not multiply eight correlated blocks as eight independent spatial observations.**

A revisit to the same grid cell after movement is a new physical stop; a repeated block without movement is not.

### 2.3 Source-update window

A set of new physical stops plus stops retained after an earlier abstention. Once an accepted window is converted into the cumulative evidence ledger, its raw stops are removed from the reservoir; the ledger itself is never cleared.

## 3. Candidate prediction at physical stops

For source candidate `s`, keyed transport member `m`, and physical stop `j`, let

`p[s,m,j]`

be the existing PMFS forward hit frequency at that stop position. The eight block-level copies at one stop must be exactly equal up to numerical tolerance. Any within-stop prediction drift is a runtime-contract failure.

Members remain frozen:

- `m=0..3`: transport/resolution calibration;
- `m=4..7`: outcome scoring.

No source id enters the transport RNG key.

## 4. Effective uncertainty: do not delete the stable complement

On the stop-level prediction vectors, estimate transport nuisance covariance from calibration-member differences:

`C_tr = mean_{s,m<n} 0.5 * (p[s,m]-p[s,n]) (p[s,m]-p[s,n])^T`.

Define a source-balanced stop probability

`pbar_j = mean_{s,m=0..3} p[s,m,j]`.

Because one physical stop is treated as one inferential observation, use conservative effective sample size 1 for the observation covariance:

`C_y[j,j] = pbar_j*(1-pbar_j) + eps_freq^2`,

with frozen empirical frequency floor

`eps_freq = 0.5/201`.

Then

`C_eff = C_tr + C_y`

and use the symmetric positive-definite inverse of `C_eff`.

This replaces the V3 Moore-Penrose rule that set low-transport-variance directions to zero precision. It also avoids claiming that eight correlated blocks provide eightfold observation precision.

No House/seed outcome may set an eigenvalue cutoff or covariance ridge.

## 5. Observation-conditioned spatial quotient

Use the fixed geometry carrier and physical adjacency. For adjacent candidates `(i,j)`, with calibration-member stop-level differences `d_m`, compute the cross-member pair strength using `C_eff^-1`:

`eta_ij = [||sum_m d_m||^2_Ceff^-1 - sum_m ||d_m||^2_Ceff^-1] / [M(M-1)]`.

Also compute every leave-one-member-out value.

A local edge is resolved only when

`eta_ij > numerical_zero AND min_LOO eta_ij > numerical_zero`.

No outcome-fitted gamma, K, temperature, or House threshold is allowed.

Unresolved physical edges define connected components `C_t`; these are **resolution cells**, not claims that every pair inside the component has identical distributions.

## 6. Stop-level proper scoring

For scoring members `m=4..7`, define one log score per physical stop:

`l_j(s,m) = r_j log p[s,m,j] + (1-r_j) log(1-p[s,m,j])`.

Each stop has weight 1 regardless of `B_j`.

For a fold `F`,

`ell_F(s) = logmeanexp_m sum_{j in F} l_j(s,m)`.

Project candidate scores to the current resolution components using geometry-prior weights.

**V4 removes the V3 normal-rank transform from the evidence ledger.** Rank normalization discarded absolute likelihood magnitude and made “all candidates are bad” look like usable evidence.

## 7. Physical-stop split-half reproducibility

Assign **physical stops**, not blocks, alternately to folds E/O by monotone stop id.

A fold must contain at least two distinct physical stops. Therefore release needs at least four accumulated stops. This is a structural replication requirement, not an outcome-tuned confidence threshold.

Let the combined score select best resolution component `B` and best rival component `R` outside it.

Directional reproducibility requires

`ell_E(B) > ell_E(R)`

AND

`ell_O(B) > ell_O(R)`.

This is the exact condition that the V3 theory stated but the V3 runtime failed to implement.

## 8. Cross-fitted absolute source adequacy

Define source-null fold evidence as the source-balanced predictive family:

`ell_F(null) = logmeanexp_s ell_F(s)`

with geometry/source-balanced weights fixed before outcomes.

To avoid winner-selection bias:

1. select best component `B_E` using only E;
2. evaluate `B_E` on O and require `ell_O(B_E) > ell_O(null)`;
3. select best component `B_O` using only O;
4. evaluate `B_O` on E and require `ell_E(B_O) > ell_E(null)`.

Both held-out gains must be positive.

This is the V4 answer to “all members agree on the same wrong model”: the selected source-specific component must predict the opposite fold better than the source-agnostic predictive family. No p-value or learned adequacy threshold is used online.

## 9. Cumulative causal/stable evidence ledger

For an accepted window, form a component-projected source-specific increment from the two proper-score folds, relative to their candidate-independent null constants:

`delta_t(s) = Project_Ct[ (ell_E(s)-ell_E(null)) + (ell_O(s)-ell_O(null)) ]`.

Maintain

`G_t(s) = G_{t-1}(s) + delta_t(s)`.

Rules:

- accepted raw stops are converted once into `delta_t` and then removed from the raw reservoir;
- rejected/insufficient stops remain in the reservoir;
- `G_t` is never cleared by RELEASE;
- a later window can correct earlier evidence only cumulatively; it cannot erase the previous state by replacement;
- no event is counted twice.

The causal/stable macro distribution is

`q_C(s) proportional to q0(s) * exp(G_t(s))`,

where `q0` is the frozen geometry-only design prior.

## 10. Resolution-cut composition with native PMFS

V4 does **not** use `q_C` as a standalone replacement localizer.

Native PMFS is always allowed to compute its normal current posterior `q_N(cell)`.

### No accepted causal state

If V4 has never accepted a window:

`q_V4 = q_N`.

Thus ABSTAIN means exact baseline behavior, not reset to the design prior.

### Accepted causal state exists

The **latest accepted resolution partition** determines the scale at which the causal module has authority.

For each accepted resolution component `C`, compute causal component mass

`Q_C(C) = sum_{s in C} q_C(s)`

and native PMFS component mass

`Q_N(C) = sum_{free cells i in C} q_N(i)`.

Then preserve the native conditional distribution within the component:

`q_V4(i) = Q_C(C(i)) * q_N(i) / Q_N(C(i))`.

If `Q_N(C)=0` exactly, distribute `Q_C(C)` according to the frozen geometry prior **inside that component only**.

Interpretation:

- causal/stable evidence controls only the macro component mass it can justify;
- PMFS keeps the fine conditional structure inside an unresolved component;
- there is no blend coefficient, temperature, or posterior interpolation weight;
- V4 is a prior-corrector / cut composition, not a second full localizer.

If a new window abstains after earlier acceptance, the cumulative causal macro state is retained while the current native PMFS conditional shape may continue to evolve inside the latest accepted components.

## 11. Required runtime instrumentation before development runs

Every source update must save, before any truth evaluation:

- physical stop id, position/cell id, block count;
- per-stop `r_j`, log-concentration mean/SD/slope;
- even/odd stop ids and counts;
- candidate/component ids;
- `ell_E(s)`, `ell_O(s)`;
- `ell_E(null)`, `ell_O(null)`;
- cross-fitted component adequacy gains;
- best component and best rival per fold;
- directional reproducibility result;
- resolution component ids and sizes;
- `C_tr`, `C_y` diagnostics, condition number, numerical inverse audit;
- per-window `delta_t(s)` hash;
- cumulative `G_t(s)` hash;
- native component mass `Q_N(C)`;
- causal component mass `Q_C(C)`;
- final cut-composed component mass;
- exact reason for ABSTAIN/ACCEPT;
- event/stop reservoir counts before and after update.

All fold counters must be filled before any early return.

## 12. Frozen falsification tests

Before any development outcome is inspected, the implementation must pass:

1. eight repeated blocks at one stop collapse to one prediction coordinate;
2. duplicating a block at the same stop cannot create a new spatial information dimension;
3. candidate order invariance;
4. member order invariance within calibration/scoring families;
5. exact coordinate-alias invariance;
6. lower transport variance with finite observation noise must retain finite precision, not zero precision;
7. contradictory E/O source-vs-rival ordering => exact ABSTAIN;
8. a source component selected on E that fails to beat source-null on O => exact ABSTAIN, and vice versa;
9. ABSTAIN before first acceptance returns exact native PMFS posterior;
10. ABSTAIN after acceptance retains cumulative causal macro mass and does not clear the ledger;
11. two accepted disjoint windows produce `G_2 = delta_1 + delta_2` exactly;
12. replaying an already assimilated window is rejected by id/hash and cannot double count;
13. source/member destruction must erase source-specific gain;
14. shared systematic bias synthetic must fail cross-fitted source adequacy;
15. output posterior mass is conserved under resolution-cut composition;
16. no truth, House id, route id, plume seed, or native outcome ranking is used as a reliability oracle.

## 13. Development and new confirmation protocol

### Development

The old Houses × seeds 0..9 matrix is revealed development evidence.

After code and selftests are frozen, run **one fixed development batch using all 30 old ON seeds exactly once**. Reuse the archived OFF results for development comparison. Do not repair the method after individual seed results arrive.

Development target uses the same practical criteria as before (diagnostic only, not confirmatory):

- pooled improvement >=10%;
- at least 20/30 pairs improved;
- no House degradation >5%;
- zero new false-confident collapses;
- all runtime invariants above pass.

If this fixed V4 fails, do not keep tuning on seeds 0..9.

### New confirmation

If and only if V4 passes the single development batch, freeze source SHA, binary SHA and launch SHA, then use entirely unseen seeds (proposed `10..19`) for a fresh House01/House02/House03 × OFF/ON matrix.

The old 0..9 results remain development-only forever.

## 14. What V4 is not allowed to become

- no House-specific threshold;
- no seed-specific rule;
- no hand-selected rescue cases;
- no `if PMFS error looks large` oracle;
- no posterior temperature;
- no PMFS/V4 blend weight;
- no top-5%-metric optimization inside the method;
- no reintroduction of block-level pseudo-replication;
- no new bridge/proximal theorem claim unless its identification assumptions are independently qualified;
- no second full localizer that discards PMFS.

## 15. Current scientific interpretation

The frozen V3 result does not show that the transport/source-sensitive signal is absent. The strong first-RELEASE post-hoc counterfactual shows that useful early source information exists in many runs. The failure is structural: repeated blocks were treated as spatial evidence, absolute model adequacy was missing, fold reproducibility was not actually enforced, and later accepted windows replaced rather than accumulated prior accepted evidence.

V4 therefore changes the object of the method from **posterior replacement** to **observation-conditioned residual assimilation at a justified spatial resolution**.
