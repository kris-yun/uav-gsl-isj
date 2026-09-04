# CTPI-G2 M3 continuation handoff — proper non-myopic EID offline falsification

Date: 2026-09-04
Repository: `kris-yun/uav-gsl-isj`
Branch: `g2-bankfree-closedloop-20260904`
Input branch anchor before this handoff: `463aed33c7c10a7bcb1256bdab9aa6da16cc2a34`
Status: `READY_FOR_CODEX_CONTINUATION`
Current scientific blocker: **M3 active experiment design is not yet load-bearing.**

## 0. Read this first

Continue from the current branch state. **Do not restart M1/M2 design, do not repeat already completed M1/M2 validation, and do not tune M3 against observed closed-loop outcomes.**

Primary references already on this branch:

- `docs/AGENT_CTPI_G2_BANKFREE_RESUME_20260904.md`
- `docs/CTPI_G2_M3_OFFLINE_FALSIFICATION_20260904.md`
- `ros2_package/src/gsl_server/algorithms/PMFS/CTPI.cpp`

This handoff records both the latest agent result and an independent audit of what that result does and does not establish.

---

## 1. Current three-module scientific state

### M1 — interference-aware source inference

**State: load-bearing PASS.**

The current G2 continuation state reports H01 3-seed closed-loop improvement. In the 12-run decomposition, `F00 - A0` is the demonstrated M1 contribution. Do not change M1 science while repairing M3.

### M2 — bank-free online transport prediction

**State: cross-environment offline generalization PASS; downstream robot utility currently inconclusive, not failed.**

Current G2 M2 replaces the predictive bank with an online numerical/wind-conditioned transport predictor. The continuation record reports H01/H02/H03 offline predictive validation at least comparable to, and in several cases stronger than, the frozen bank reference. Keep M2 scientific equations/parameters frozen during M3 falsification except for interface exposure/refactoring that leaves predictions numerically unchanged.

### M3 — active experiment design / action selection

**State: current implementation NO-GO as a load-bearing module; redesign required.**

The G2 12-run decomposition reports `F10 - F00` with no reliable improvement (0/3 wins in the recorded H01 screening). The present task is therefore **not to rescue the old planner**, but to test a scientifically correct active experimental design mechanism offline before another true closed loop.

---

## 2. Verified current M3 implementation

`PMFS::evaluateCTPIActionInformation()` in `CTPI.cpp` currently does the following:

1. Marginalizes the cell-level source posterior to source carriers.
2. **Collapses every region-valued carrier to its 2×2 quadtree center** and treats that center as the physical source position for the planner-side plume prediction.
3. Builds a Gaussian-plume-like source/action response and converts it to a soft binary hit probability.
4. Computes one-step binary mutual information:

   `I(S;Y|a) = H(sum_s pi_s pHit_s(a)) - sum_s pi_s H(pHit_s(a))`.

5. Applies the manual exploitation multiplier:

   `score(a) = I(S;Y|a) * (1 + 20 * posteriorMass(a))`.

Therefore the latest agent's main code diagnosis is correct: **current M3 is myopic, uses a binary hit abstraction, and contains an ad-hoc 20× posterior modulation.** That 20× term is not a principled Bayesian experimental-design objective and must not survive the redesign.

### Additional correctness issue found in audit

The carrier-center collapse is inconsistent with the project source-state contract. The source state is **region-valued**: a source carrier `S` contains a physical placement `U`, and prediction/evidence should marginalize `U` rather than silently replacing it by the carrier centroid.

For M3, use a deterministic, auditable within-carrier marginalization (e.g. all free cells / a fixed quadrature set / a frozen deterministic placement set) shared across every compared policy. **Do not use the quadtree center as the physical source placement.**

---

## 3. Completed M3 offline falsification result

The current report records the following true-source-rank trajectories over 40 sampling steps in the present M2 bank-free surrogate environment:

| policy | 5 | 10 | 15 | 20 | 25 | 30 | 35 | 40 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| random | 179 | 168 | 149 | 140 | 128 | 119 | 101 | 92 |
| exploit | 125 | 110 | 95 | 75 | 65 | 47 | 39 | **35** |
| myopic-EIG | 119 | 103 | 92 | 72 | 55 | 45 | 39 | 37 |
| deterministic “non-myopic” | 120 | 104 | 95 | 86 | 71 | 63 | 55 | 50 |

The tested surrogate therefore shows:

- random is clearly weaker;
- the old myopic EIG has **no demonstrated incremental value over the tested exploit baseline**;
- the deterministic look-ahead called “non-myopic” is worse than both.

This is a useful falsification of the current planner idea, but it must be interpreted narrowly.

---

## 4. Audit corrections to the previous interpretation

### 4.1 Do not call the deterministic look-ahead a valid non-myopic Bayesian design

The current “non-myopic” implementation updates the future posterior using an **expected observation**. That is not the Bayesian Bellman expectation. It collapses mutually exclusive future observations into one synthetic observation and can bias the posterior update.

The correct finite-horizon value requires branching/integrating over future observations:

`E_Y[V(pi^Y)]`, not `V(pi^{E[Y]})`.

Therefore its poor result **does not falsify proper non-myopic EID**. It only falsifies that deterministic shortcut.

### 4.2 The offline result does not prove the closed-loop root cause

The result is consistent with a plausible explanation for why `F10 - F00` did not carry weight, but it does not causally prove that the 12-run failure was caused by “peak-field exploit optimality.” Treat that as a hypothesis until tested on held-out transport realizations.

### 4.3 Resolve the exploit-definition inconsistency before further conclusions

The existing M3 report calls exploit **“追后验峰值”** in the strategy table, but later interprets it as **“追浓度峰值”**. These are different policies.

Before any new benchmark, inspect the actual offline script and write the exact mathematical definition of exploit. Examples:

- posterior-MAP exploit: move/sample at `argmax_x p(S=x | D_t)`;
- predicted-concentration exploit: choose `argmax_a E[C|D_t,a]`;
- measured-concentration chase: choose according to the latest observed field/gradient.

Do not use one label for another. The root-cause story depends on this distinction.

### 4.4 “Instantaneous plume peak is downstream” is a testable hypothesis, not a universal fact

A filament/puff model can create downstream instantaneous maxima, but repeated release and source-near concentration mean the global instantaneous maximum is not guaranteed to be downstream at every time.

Add an explicit GADEN diagnostic instead of assuming it:

- `x_peak(t) = argmax_x C_t(x)`
- `d_peak(t) = ||x_peak(t) - U_true||`
- fraction of snapshots with peak inside the true source carrier;
- fraction within 1 cell / 2 cells / chosen physical radius;
- signed along-wind offset of `x_peak(t)-U_true`;
- stratify by House, wind state, and time after release if available.

This diagnostic validates or rejects the surrogate-mismatch hypothesis, but **does not itself count as M3 PASS**.

---

## 5. Correct M3 redesign: proper finite-horizon EID

### 5.1 Freeze scientific dependencies

For this M3 cycle:

- M1 equations/parameters: frozen.
- M2 equations/parameters: frozen.
- source-truth carrier contract: frozen.
- maps/worlds used for held-out evaluation: frozen before outcomes.
- no posterior-mass multiplier;
- no `J - lambda * distance` tuning;
- no hand-picked explore/exploit coefficient;
- travel distance may be used only as a deterministic tie-break unless a cost is derived and frozen *before* outcomes as part of a separate scientific hypothesis.

### 5.2 First determine what predictive observation law M2 actually provides

Do not silently treat a deterministic concentration prediction as a likelihood.

Inventory the current M2 interface and answer explicitly:

- Does it produce a calibrated Bernoulli hit probability `P(Y=1 | S,a,h_t)`?
- Does it produce only a deterministic concentration/response mean?
- Does it expose a stochastic predictive ensemble or variance/noise law?

Then use the smallest valid observation model consistent with the frozen M2 science.

#### Preferred path if a Bernoulli observation law already exists

Use exact binary Bayesian design. For posterior `pi`, action `a`, and likelihood `L_s(y|a)`:

`p(y|pi,a) = sum_s pi_s L_s(y|a)`

`pi_s^y = pi_s L_s(y|a) / p(y|pi,a)`

One-step information:

`I_pi(S;Y_a) = H(pi) - sum_y p(y|pi,a) H(pi^y)`.

Proper horizon-2 non-myopic value:

`Q2(pi,a) = I_pi(S;Y_a) + sum_y p(y|pi,a) max_b I_{pi^y}(S;Y_b)`.

For binary `y in {0,1}`, the outer expectation is exact: **no Monte Carlo is needed** and no expected-observation shortcut is allowed.

#### If M2 only supplies continuous concentration means

Do not call `E[C|S,a]` an observation likelihood. First specify and validate a predictive observation law `p(C | S,a,h_t)` using a frozen noise/dispersion model supported by held-out data. Only then compute:

`EIG(a) = E_C[ KL(p(S|C,a) || p(S)) ]`.

For horizon 2, integrate/sample future `C` branches using quadrature or common-random-number sampling. The same observation draws/budgets must be used across compared policies.

### 5.3 Source placement marginalization inside M3

For every carrier `S`, predictions must integrate over physical placement `U in S`:

`p(y | S,a,h_t) = integral p(y | U,a,h_t) p(U|S) dU`.

Use a deterministic finite approximation whose support and weights are frozen before outcomes. Record all excluded obstacle cells and normalization. This must be shared by myopic and non-myopic policies.

---

## 6. Correct offline falsification design

### 6.1 Four fixed policies

Compare, with identical candidate action sets and movement constraints:

1. `random`: uniformly/randomly chosen valid action using a frozen seed stream.
2. `exploit`: exact definition audited from code and frozen before outcome inspection.
3. `myopic-EID`: proper one-step Bayesian EIG with **no 20× posterior hack**.
4. `nonmyopic-EID-H2`: the proper observation-branched horizon-2 value above.

Do not introduce H3 until H2 is computationally correct and evaluated. H3 is not a rescue mechanism.

### 6.2 Eliminate self-play / same-model evaluation

The planner's M2 model and the outcome generator must not be the exact same deterministic peak field.

Preferred offline evaluation:

- planning model = frozen current M2;
- outcome realization = held-out GADEN instantaneous snapshots / independent filament realizations / independent transport realizations not used to build or calibrate the planner;
- paired worlds/seeds across all four policies;
- common random numbers where stochastic observations are sampled;
- no reuse of evaluation outcomes for coefficient tuning.

If actual GADEN snapshots are temporarily unavailable, create an **independent** stochastic/pulsed transport testbed and label it surrogate-only. Do not promote surrogate success to a GADEN claim.

### 6.3 Metrics

Record trajectories, not only terminal rank:

- true-source carrier rank;
- posterior probability on true carrier;
- posterior entropy / effective candidate count;
- localization error or source-risk under a fixed estimator;
- error AUC over step/time;
- time-to-resolution under a predeclared threshold;
- selected-action diversity/coverage and travel distance as diagnostics, not tuned rewards;
- computation time / rollout count / cache hit rate.

For each paired world, save raw per-step state, action scores, chosen action, observation branch/probability, posterior before/after, and RNG seed.

---

## 7. Predeclared M3 offline gate

The goal is to falsify the *proper* non-myopic claim before touching closed loop.

Use a predeclared gate with a primary temporal source-resolution metric (prefer error AUC or a source-risk AUC; rank can remain a secondary diagnostic). A reasonable confirmatory structure is:

- paired held-out worlds;
- `H2 nonmyopic - proper myopic` must improve the primary temporal resolution metric in the favorable direction;
- use an exact paired sign/randomization test when the unit count permits it;
- require no stable House-level reversal (e.g. all/near-all paired worlds in one House worsening);
- report effect size and paired wins/losses, not p-value alone;
- **freeze the gate before running the held-out outcomes**.

Do not choose thresholds after seeing the result. If proper H2 fails, mark this M3 non-myopic route `NO-GO` and do not rescue it by adding planner weights.

Only if the offline gate passes:

1. implement the exact same M3 objective in runtime code;
2. run a true closed-loop smoke validating the full causal chain;
3. run a small H01 screening with paired arms;
4. then fresh multi-House confirmatory closed loop.

---

## 8. Computational implementation guidance

Proper H2 can be made tractable without changing the science:

- vectorize source × action likelihoods;
- precompute within-carrier placement quadrature responses where history permits;
- cache `I_pi(a)` for repeated posterior branches only when numerically exact for that state;
- shortlist second-stage actions only if the shortlist rule is **outcome-independent and frozen**, and benchmark approximation error against full action search on small cases;
- for binary observations, branch exactly over `{0,1}`;
- for continuous observations, use shared quadrature/common-random-number draws and publish convergence vs sample budget;
- keep all pruning/tolerance values in the audit output.

A process being killed for compute is an engineering issue. It is not evidence against non-myopic EID.

---

## 9. VM / code continuation order for Codex

Proceed autonomously in this order:

1. Inspect VM/current checkout/build state; `/dev/shm` artifacts are ephemeral, so verify before reuse.
2. Confirm checkout is this branch and record exact commit.
3. Read the three reference files listed in Section 0 plus the actual M3 offline script used to produce the 4-policy table.
4. Reconstruct the exact definition of `exploit` and record it.
5. Inspect current M2 predictor API and state exactly what observation distribution it supports.
6. Add source-placement marginalization to the **offline M3 predictor/evaluator first**, with M1/M2 numerical science unchanged.
7. Implement proper myopic EID and proper H2 observation-branched non-myopic EID.
8. Add unit/parity tests: posterior normalization, zero-probability branches, entropy identities, H2≥immediate-term sanity where mathematically applicable, deterministic reproducibility, carrier marginalization.
9. Add the GADEN instantaneous peak-offset diagnostic.
10. Run cheap toy/synthetic correctness tests, then the frozen held-out offline falsification.
11. Write a result bundle with commands, commit, SHA256, seeds, worlds, raw trajectories, summary, and PASS/NO-GO.
12. **Stop before closed-loop science changes if the offline gate fails.** If it passes, proceed to runtime integration and smoke using the same objective.

---

## 10. Autonomy and forbidden changes

Codex may autonomously:

- repair ROS/CMake/build/overlay/runtime paths;
- recover ephemeral `/dev/shm` artifacts from reproducible sources;
- vectorize/cache/rewrite computation for equivalent numerical results;
- add tests, audit logs, profiling, serialization, plots and result packaging;
- make interface-only refactors that leave frozen M1/M2 predictions unchanged.

Codex must **not**:

- change M1 or M2 science to make M3 win;
- use a quadtree center as the true physical source placement when the state is region-valued;
- add posterior multiplier `20`, planner weights, `lambda` costs, or another hand-tuned explore/exploit blend;
- reinterpret deterministic expected-observation look-ahead as proper non-myopic EID;
- tune on held-out outcomes then call them confirmatory;
- change the pass gate after seeing results;
- claim GADEN downstream-peak behavior without measuring it;
- infer M3 success from entropy alone without actual source-resolution improvement.

---

## 11. Required next report

The next Codex report should answer, with artifacts rather than prose alone:

1. What exactly did the old `exploit` policy do?
2. What is the frozen M2 predictive observation law used by M3?
3. How is `U|S` marginalized rather than replaced by the carrier center?
4. Is proper H2 implemented as an expectation over future observations?
5. Does H2 beat proper myopic EID on held-out source-resolution trajectories under the predeclared gate?
6. Does the GADEN peak-offset diagnostic support or reject the “downstream instantaneous maximum” hypothesis?
7. If PASS, what exact runtime objective should replace the current `information * (1 + 20*posteriorMass)` code? If NO-GO, freeze the negative result without rescue tuning.

The scientific target is not “non-myopic because the literature says so.” The target is a **falsifiable, source-resolution-bearing M3 whose benefit survives independent transport outcomes and whose Bayesian look-ahead is implemented correctly.**
