# CG-PC-CTT V4 — Observation-Conditioned Stable Likelihood Assimilation (OC-SLA)

Date: 2026-08-27  
Status: **DESIGN V2 / NO PERFORMANCE CLAIM / NO C++ AUTHORIZATION YET**  
Parent: `research/cg-pc-ctt-v4-residual-assimilation`  
Supersedes the mathematical runtime plan in `CG_PC_CTT_V4_OC_CRA_DESIGN_FREEZE_DRAFT_20260827.md`.

`Stable` means source-specific predictive structure that survives keyed transport realizations and cross-predicts unseen physical stops. `Causal` may be used only in the operational source-intervention sense. This version does **not** claim a general proximal-identification theorem.

## 0. Evidence boundary

The frozen V3-ORR result remains `CG_PC_CTT_MULTI_SEED_NOT_GO` (18/30 improved, pooled +4.02%, H01 degraded). Seeds 0..9 and all artifacts from that matrix are permanently development/post-hoc evidence.

The following post-hoc facts motivate V4 but are not confirmatory claims:

1. V3 frequently rescued poor PMFS states but also destroyed good states.
2. Holding the first accepted V3 state was much better than allowing later replacement, showing that state replacement is a major failure mode.
3. In every one of the 105 V3 source-update audits, `nuisance_rank == event_count/8`. The runtime used eight completed blocks at one physical stop, while the candidate forward prediction was identical for those eight blocks. The block columns were therefore pseudo-replicated spatial prediction dimensions.
4. V3 theory required split-half source-direction agreement and absolute adequacy, but the fast-track runtime did not implement those conditions.
5. V3 reset the macro posterior from a geometry prior instead of correcting the useful PMFS state.

V4 is designed to repair those structural failures. No House/seed-specific threshold may be derived from seeds 0..9.

## 1. Central invariant

**Stable evidence may change PMFS only at a spatial scale that the current observations can resolve, and only when a source component selected without a held-out physical stop predicts that held-out stop better than PMFS's own pre-update predictive mixture.**

If this condition is not earned, V4 returns exact native PMFS behavior.

This turns the module from a posterior replacement/deconfidence operator into a bounded rescue/corrector.

## 2. Statistical unit: physical stop, not block

### 2.1 Physical stop identifier

The runtime must attach a monotone `physical_stop_id` to every completed measurement block. In the current PMFS loop, all repeated blocks collected before a movement share the same movement/iteration id. Use that explicit id; do not infer a new stop merely from floating-point position equality.

A revisit to the same grid cell after a movement is a new physical stop.

### 2.2 Stop observation

Let physical stop `j` contain `B_j` completed blocks. For block hit indicators `y_jb` and block-average concentrations `c_jb`, define

`r_j = (1/B_j) sum_b y_jb`

and diagnostic-only temporal marker

`u_jb = log(1 + max(c_jb,0))`

`M_j = [mean(u), sd(u), r_j, slope(u versus causal block time)]`.

Primary V4 source scoring uses only `r_j`. The other marker coordinates are logged for adequacy/ablation and cannot enter source ranking in V4 without a separately frozen validation.

Each physical stop has statistical weight one, regardless of whether it contains 8 blocks or another fixed number. Repeating a block at the same stop may refine `r_j`, but it may not create another spatial information dimension or another unit of source-likelihood weight.

### 2.3 Window accounting

One source-update window contains only the new physical stops acquired since the previous source update.

**No raw-stop reservoir is carried across an ABSTAIN.** The native PMFS update has already used those observations; reusing them later in V4 would create adaptive double use. Every window is consumed exactly once whether accepted or rejected.

History is preserved only through the accepted stable-evidence ledger defined below.

## 3. Candidate prediction at a physical stop

For source carrier `s`, keyed transport member `m`, and stop `j`, let

`p[s,m,j]`

be the existing PMFS forward hit frequency sampled at that stop position.

The repeated block-level copies belonging to one stop must be numerically identical for every `(s,m)`. Any within-stop prediction drift is `RUNTIME_CONTRACT_FAIL`.

Members remain frozen:

- `m=0..3`: transport/resolution calibration;
- `m=4..7`: outcome scoring.

The source id is absent from the exogenous transport RNG key.

## 4. Frequency discretization constant

PMFS `simulateSourceInPosition` records occupancy for `T = settings.iterationsToRecord` transport timesteps and divides the hit count by `T`. Therefore the empirical frequency grid is determined by **T, not the number of source candidates**.

Use the continuity floor

`eps_T = 0.5 / (T + 1)`.

For the currently frozen `T=200`, this equals `0.5/201`, but the meaning of `201` is `T+1`; it is not a 201-candidate constant.

All predictive probabilities used in log scores are clamped to `[eps_T, 1-eps_T]`.

## 5. Effective uncertainty for spatial resolution

On stop-level calibration predictions estimate transport nuisance covariance

`C_tr = mean_{s,m<n} 0.5 * (p[s,m]-p[s,n]) (p[s,m]-p[s,n])^T`.

The within-stop block correlation is not independently identified. To avoid inventing `B_j` independent observations, use the worst-case Bernoulli single-observation variance as an outcome-blind observation covariance:

`C_y = (1/4 + eps_T^2) I`.

Then

`C_eff = C_tr + C_y`.

`C_eff` is strictly positive definite and is inverted symmetrically. This has two intended effects:

1. low transport variance no longer receives zero precision merely because a Moore-Penrose inverse deleted the stable complement;
2. repeated correlated blocks cannot create eightfold observation precision.

`pbar*(1-pbar)` may be logged as a diagnostic, but V4 does not use it to reduce the conservative observation variance.

## 6. Observation-conditioned spatial quotient

Use the fixed persistent physical carrier geometry and physical adjacency. For adjacent source carriers `(i,j)`, with calibration-member stop-level differences `d_m`, compute

`eta_ij = [||sum_m d_m||^2_Ceff^-1 - sum_m ||d_m||^2_Ceff^-1] / [M(M-1)]`.

Compute all leave-one-calibration-member-out values.

A local boundary is resolved only when

`eta_ij > numerical_zero`

AND

`min_LOO eta_ij > numerical_zero`.

`numerical_zero` is floating-point error control only. No H02/House/seed outcome sets a scientific threshold.

Unresolved local boundaries induce connected components `C_t`. These are **resolution cells**: the macro spatial units over which current stable evidence is allowed to act.

## 7. Stop-level proper log score

For scoring members `m=4..7`, define

`a_j(s,m) = r_j log p[s,m,j] + (1-r_j) log(1-p[s,m,j])`.

Marginalize keyed scoring members at one stop:

`a_j(s) = logmeanexp_m a_j(s,m)`.

This is a unit-weight fractional Bernoulli **proper log score**, not a claim that the repeated correlated blocks are independent Bernoulli trials.

V4 removes the normal-rank transform from the evidence path. Magnitude is necessary to distinguish a genuinely predictive source model from a merely least-bad ranking.

## 8. Pre-update native predictive null

At `beginTADMUpdate`, before the current native source-probability simulation update, snapshot the native PMFS source belief and aggregate it onto the persistent source carriers:

`pi_N^-(s)`.

This snapshot is a forecast/baseline distribution, not a reliability oracle. It contains no truth and is fixed before V4 scores the current window.

For held-out stop `h`, define native prior-predictive score

`N_h = logsumexp_s[ log pi_N^-(s) + a_h(s) ]`.

This is the key protection for already-good PMFS states. If native PMFS already concentrates on the same component that stable evidence would select, its predictive mixture approaches the component predictive score and V4 earns little or no residual authority.

## 9. LOSO cross-predictive consensus

The current cadence normally provides three new physical stops per source update. V4 therefore uses **Leave-One-Physical-Stop-Out Cross-Predictive Consensus (LOSO-CPC)** rather than the V3 block-parity split.

Require `J >= 3` distinct physical stops in the current window. No old raw stops are borrowed to satisfy this condition.

For every held-out stop `h`:

1. use only the other stops `-h` to score each resolution component;
2. source weights inside a component are the frozen geometry-prior conditional weights;
3. obtain the numerically tied best-component set `T_h`;
4. evaluate the selected component on held-out stop `h`;
5. compare the held-out component score with `N_h` from the pre-update native predictive null.

Training component score:

`A_-h(C) = logsumexp_{s in C, q0(.|C)} [ sum_{j != h} a_j(s) ]`.

A unique consensus component `B` exists only if the intersection of all numerical best sets `T_h` contains exactly one component.

Held-out component score:

`A_h(B) = logsumexp_{s in B, q0(.|B)} a_h(s)`.

Held-out residual predictive gain:

`g_h = A_h(B) - N_h`.

A window is cross-predictively adequate only when

`g_h > numerical_zero` for **every** held-out stop.

Thus each physical stop validates a source component chosen without using that stop, and the chosen macro component must be directionally consistent across all leave-one-stop-out training subsets.

This is stronger and better aligned to the actual 3-stop cadence than the V3 rule “each parity contains hit and miss”. It adds no tuned confidence threshold.

### Interpretation boundary

This is **cross-fitted source-specific predictive adequacy relative to native PMFS**, not a universal theorem that the forward model is absolutely correct. Structured misspecification shared by both the source family and baseline can still escape this test and remains a stated limitation.

## 10. Independent cumulative stable-evidence ledger

Maintain an independent source-carrier distribution `q_C`, initialized once from geometry-only prior `q0`.

For an accepted consensus component `B`, update only the binary contrast `B` versus its complement. Unsupported fine distinctions are not accumulated.

For each held-out stop `h`, compute using the **pre-window** `q_C^-` conditional weights:

`S_h(B)   = logsumexp_{s in B,   q_C^-(.|B)}   a_h(s)`

`S_h(notB)= logsumexp_{s notin B,q_C^-(.|notB)} a_h(s)`.

Because the common `B` is selected by each `-h` training subset without stop `h`, define the cross-predictive stable increment

`A_t = sum_h [ S_h(B) - S_h(notB) ]`.

Update only component odds:

`logit Q_C^+(B) = logit Q_C^-(B) + A_t`.

Preserve the previous causal conditional distribution inside `B` and inside `notB`.

Consequences:

- accepted evidence is cumulative;
- no RELEASE clears history;
- a later accepted window can correct earlier macro odds without replacing the whole state;
- no unvalidated ranking among candidates inside one unresolved component is accumulated;
- every raw physical-stop window is scored at most once.

Store an immutable window hash; replay of an already consumed window is a contract failure.

## 11. KL/I-projection mass-floor composition with native PMFS

`q_C` is **not** a second full localizer. Native PMFS always computes its normal current posterior `q_N` using its existing map and Bayesian machinery.

If no V4 window has ever been accepted:

`q_V4 = q_N` exactly.

After at least one accepted window, retain the most recently validated source set `B*` (stored by stable carrier ids) and let

`alpha = Q_C(B*)`

`beta  = Q_N(B*)`.

V4 output is the distribution closest to native PMFS in KL divergence subject only to the causal/stable mass floor

`Q(B*) >= alpha`.

Closed form:

### If native already supplies at least the earned stable mass

If `beta >= alpha`:

`q_V4 = q_N` exactly.

V4 is forbidden to deconcentrate or weaken a good native state merely because the stable channel is diffuse.

### If stable evidence has earned more mass than native supplies

If `beta < alpha`:

For `i in B*`:

`q_V4(i) = alpha * q_N(i) / beta`.

For `i notin B*`:

`q_V4(i) = (1-alpha) * q_N(i) / (1-beta)`.

If `beta=0`, use the frozen geometry-prior conditional distribution inside `B*` for the `alpha` mass. Native conditional proportions are preserved everywhere they have positive support.

This is an information projection / minimum-change correction, not a blend:

- no blend coefficient;
- no temperature;
- no baseline-error threshold;
- no House/seed rule.

It directly targets the V3 failure mode: stable evidence may rescue a native posterior that underweights a validated macro region, but it cannot flatten a native posterior that already supports that region more strongly.

If a later window abstains, the raw window is consumed and `q_C` is unchanged. The previously earned `B*` mass floor remains active while native PMFS continues to update its conditional shape.

## 12. Runtime logging required before development

Every source update must write, before any truth evaluation:

- physical stop ids and source PMFS iteration ids;
- block count per stop and same-stop prediction-drift audit;
- `r_j`, mean/log-SD/slope diagnostics;
- `T`, `eps_T` and probability-clamp audit;
- source/member/stop prediction tensor hash;
- `C_tr`, fixed `C_y`, `C_eff` eigenvalues and condition number;
- resolution component ids and stable carrier ids;
- pre-update native carrier prior `pi_N^-` hash;
- per-stop source scores `a_j(s)`;
- every LOSO training best-set `T_h`;
- consensus component id/set;
- every held-out `A_h(B)`, `N_h`, and `g_h`;
- ACCEPT/ABSTAIN reason;
- pre/post `q_C` hash and binary log-odds increment `A_t`;
- consumed window id/hash;
- current native `beta`, stable floor `alpha`, whether the I-projection was active;
- output mass and exact native-equality audit when `beta>=alpha`;
- source-update wall time.

All counters and score fields must be populated before an early return whenever mathematically defined.

## 13. Falsification/selftests before C++ authorization

The Python reference must pass all of the following before C++ runtime work begins:

1. eight repeated blocks at one stop collapse to one physical-stop prediction coordinate;
2. duplicating blocks at the same stop cannot create a new spatial information dimension;
3. explicit `physical_stop_id`, not float position equality, controls stop identity;
4. `eps_T = 0.5/(T+1)` changes with transport timesteps and is independent of candidate count;
5. candidate-order invariance;
6. member-order invariance within calibration/scoring families;
7. exact coordinate-alias invariance;
8. finite observation covariance preserves finite precision in low-transport-variance directions;
9. three consistent stops selecting one component and beating native predictive null => ACCEPT;
10. one contradictory held-out stop causing selection disagreement or nonpositive residual gain => ABSTAIN;
11. identical/shared source predictions => held-out residual gain numerically zero => ABSTAIN;
12. native predictive prior already concentrated on selected component => no artificial residual gain;
13. accepted disjoint windows update binary stable odds cumulatively and never clear prior accepted evidence;
14. replay of a consumed window id/hash => reject without state change;
15. ABSTAIN consumes the raw window but does not modify `q_C`;
16. before first acceptance, V4 output is bitwise/numerically identical to native PMFS;
17. if `beta>=alpha`, I-projection returns native PMFS exactly;
18. if `beta<alpha`, only the validated component mass is raised and native conditional proportions are preserved;
19. output probability is nonnegative and mass-conserving;
20. source/member destruction removes cross-predictive residual gain;
21. no truth, House id, route id, plume seed, final localization error, or native outcome ranking is used as a reliability oracle.

Failure of any invariant blocks C++ implementation.

## 14. Development and fresh confirmation

### Development

Seeds 0..9 are revealed development evidence. After the V4 Python reference, selftests, C++ adapter, source SHA and runtime contract are frozen, run **one fixed development batch** on the old 30 ON cases. Reuse archived OFF results only for development comparison. Do not repair individual seed failures one by one.

Development target (diagnostic only):

- pooled reduction >=10%;
- at least 20/30 improved;
- no House degradation >5%;
- ON introduces zero new false-confident collapses;
- all runtime invariants pass.

If this one frozen V4 development batch fails, do not continue tuning on seeds 0..9.

### New confirmation

Only after development PASS, freeze code/binary/launch hashes and run a fresh confirmatory matrix on entirely unseen seeds (proposed 10..19) for H01/H02/H03 OFF/ON.

The old 0..9 matrix remains development-only forever.

## 15. What V4 is not allowed to become

- no House-specific threshold;
- no seed-specific rule;
- no baseline-error oracle;
- no hand-selected rescue cases;
- no posterior temperature;
- no PMFS/V4 blend weight;
- no top-5%-metric optimization inside the method;
- no raw-stop reuse after ABSTAIN;
- no block-level pseudo-replication;
- no normal-rank evidence ledger;
- no full posterior replacement from a uniform prior;
- no proximal-identification theorem claim without separately qualified assumptions.

## 16. Current authorization

**AUTHORIZED NOW:** Python reference + invariant selftests + code/interface audit only.

**NOT YET AUTHORIZED:** C++ integration, smoke performance judgement, House/seed performance runs, new confirmatory matrix.

C++ work becomes authorized only after the V2 reference mathematics and all selftests pass unchanged.