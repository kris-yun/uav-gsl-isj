# START HERE — OFFLINE HANDOFF TO AUXILIARY PRO

Date: 2026-09-24

You do NOT need GitHub access to continue from this package.

## Authority
The primary ChatGPT thread is the scientific mainline lead.
You are the auxiliary theory/literature expert.
Do not change frozen gates, declare PASS/HOLD/STOP, launch experiments, or revive stopped routes.

## Current verified state
- PASI: `PASI_D0_FAIL_STOP_PATH_ACTION_MAINLINE`
- R0: `R0_PASS_STOCHASTIC_BENCHMARK_USABLE`, independently recomputed by the mainline lead.
- The old 2-realization C/D estimate was noisy: legacy C/D vs R0-16 variability Spearman ≈ 0.504644.
- Stable R0 objects are much clearer in encounter/support statistics than in full amplitude/path statistics.
- 10×30 binary encounter-probability field convergence:
  - K=8 vs K=16 median relative error ≈ 0.081, q75 ≈ 0.097.
  - K=12 vs K=16 median ≈ 0.043, q75 ≈ 0.052.
- Exploratory 18-source held-out Bernoulli encounter likelihood:
  - top-1 ≈ 90%, top-3 ≈ 99–100%.
  This is object-selection evidence only, NOT a confirmation gate.
- Simple binary encounter Bayesian likelihood is not novel enough; 2025 GSL/olfaction prior art already uses spatially dependent encounter statistics.

## Your ONLY two theory tracks now

### Track A — Temporal encounter/event-process theory
Do NOT propose simple hit/no-hit Bernoulli maps.
Deeply investigate:
- marked temporal point processes;
- renewal / semi-Markov event processes;
- survival / hazard / first-passage formulations;
- predictive-state/event-history representations;
- event sequence information beyond independent encounter probability.

Goal:
derive a genuinely new source-conditioned temporal encounter process that maps to a PMFS source probability map and is clearly beyond existing encounter-probability olfactory search.

### Track B — Causal emergence / multiscale identifiability
Deeply investigate:
- causal emergence;
- effective information;
- stochastic coarse-graining;
- information-theoretic macrostate discovery;
- multiscale identifiability / equivalence classes.

Goal:
derive whether 0.30 m source cells should be treated as noisy microstates and whether a coarser source basin can have greater reproducible source information.

## For EACH track deliver
1. strongest 2025/2026 peer-reviewed theory anchors;
2. public code if available;
3. exact mathematical object;
4. nearest GSL/olfaction prior art;
5. what is genuinely new in our GSL adaptation;
6. explicit equations / second-order innovation;
7. how it produces a PMFS-style source probability map;
8. minimum offline falsification using >=143 arbitrary source hypotheses;
9. source/seed split requirements informed by R0;
10. PASS and STOP conditions;
11. strongest red-team criticism;
12. why it is not TNQC/HCMC/M4/SLL/Bi-Green/MZ/PASI in disguise.

Do NOT choose the final winner. Give a comparative evidence matrix; the primary thread will choose.

## Important measurement constraint
The current R0 observation operator has only 10 time snapshots × 30 probes.
Therefore:
- snapshot nonzero probability is NOT automatically a continuous-time encounter count;
- “first observed detection” is NOT automatically a true first-passage time;
- inter-event / burst-duration theory requires an observation protocol that actually resolves those events.
You must explicitly separate what can be supported by existing data from what would require a new higher-frequency observation export.

## Output requested
- TRACK_A_EVENT_PROCESS_MEMO.md
- TRACK_B_CAUSAL_EMERGENCE_MEMO.md
- COMPARATIVE_MATRIX.md
- RED_TEAM_AND_PRIOR_ART.md
- one concise recommendation to the primary lead, but no route promotion.


---

# INCLUDED FILE: docs/PRO6_PROJECT_HANDOFF_20260924.md

# Project Handoff for Second Pro — 2026-09-24

Repository: `kris-yun/uav-gsl-isj`

Coordination branch for reading/planning only:
`research/pro6-sync-handoff-20260924`

This branch was created from:
`27087e158fe709c905c22eb9e65280223d68fb7d`

The active scientific execution branch is:
`research/path-action-source-inference-v0`

**Do not push to the active PASI branch while Codex is executing the fresh S3 gate.**

---

## 1. Research objective

The project is UAV gas source localization (GSL) with GADEN simulation first and real-flight validation later.

The paper target is one publishable main scientific innovation plus two auxiliary innovations.

Hard requirements:

- preserve the PMFS-style **source-location probability map** as the final representation/output;
- internal inference may be radically redesigned;
- main innovation must come from a clearly identifiable far-domain scientific mother theory, preferably 2025/2026;
- avoid small engineering patches;
- avoid generic Bayesian/statistical tuning, SBI, and ordinary experimental-design contributions;
- first prove an offline source-identification mechanism;
- only then derive the second-order innovation and code;
- only after offline confirmation authorize Codex closed-loop experiments;
- require cross-source and cross-environment evidence;
- record STOP/HOLD/NO-GO explicitly and never rescue a failed frozen gate by post-hoc tuning.

The current bottleneck is no longer “make the plume forward model more accurate.”

The accumulated evidence says that **stochastic plume realization variability is strongly source/location conditioned**, so a representation that is robust for one source can destroy useful information for another.

---

## 2. Frozen data / benchmark facts

Primary simulator: GADEN.

Houses:
- House01 / H01
- House02 / H02
- House03 / H03

Common search budget: 300 s.

House02 frozen W2:
- wind name: `3,5-1_slow`
- GADEN binary SHA256:
  `4127b9ba4f42186ba2d6d33c84fba8d4b92749da59b83750fa4847dbd9957ce1`
- occupancy SHA256:
  `9402690152be4568ced8f2256e9098d82691aaaa1f22a1887eeac55d0e5d098d`
- W2 wind_iteration_1 SHA256:
  `54d7bc338ea681611f66004a3230f29feffc495446814607141b0623ef1dd9a8`
- extractor SHA256:
  `206cc92384866dcb7d966c6f8f9ec87862e15c7fee460a43c04014b58e3cae91`

Frozen House02 arbitrary-source bank:
- 630 free PMFS support cells;
- prediction seeds:
  - C = `2026092401`
  - D = `2026092402`
- 10 frozen times;
- 30 frozen pooled probes;
- exact source→sensor predictions already exist and are reusable infrastructure.

Important contract:
historical HCMC House02 replays used W1=`3,5-1_fast`; they are **not** valid W2 plume evidence. Their candidate manifest may be reused for geometry only.

---

## 3. The key empirical discovery that should guide all future work

Across all 630 source hypotheses, independent C/D plume-realization variability is strongly source dependent.

Approximate relative C/D discrepancy distribution:
- minimum ~1.5%
- 25th percentile ~9.3%
- median ~15.3%
- 75th percentile ~24.4%
- 90th percentile ~34.5%
- maximum ~57.5%

Relative variability is negatively associated with mean observed plume mass:
Spearman approximately `-0.50`.

Two important source regimes already exposed:

### S1
`(-2.242730141, -2.200880051, 0.20)`

Low stochastic variability:
- target A/B raw relative L2 ~8.1%
- raw exact-forward ranks were 1/1.

Absolute concentration was useful source information.

### S2
`(-4.342730045, 2.899120331, 0.20)`

More stochastic:
- target A/B raw relative L2 ~21.2%
- Gate1A exact-forward ranks A/B = 1/7.

Here absolute amplitude behaved much more like realization nuisance.

Therefore:

> There is no globally valid rule saying “absolute plume mass is signal” or “absolute plume mass is nuisance.”

The next successful method must model **source-conditioned stochastic uncertainty**, not delete one observable component globally.

---

## 4. Current active candidate: PASI

Working name:
**Source-Conditioned Stochastic Path Action / Path-Action Source Inference (PASI)**.

Mother-theory direction:
nonequilibrium statistical physics / stochastic path probability / Onsager–Machlup and large-deviation action ideas.

Core shift:

Instead of:
`source -> one mean plume -> distance to observation`

use:
`source -> source-conditioned stochastic path distribution -> probability/action of the entire observed path`.

Frozen exploratory proxy for candidate source (s):

[
\mu_{s,k}=\frac{x^C_{s,k}+x^D_{s,k}}{2}
]

[
v^{local}_{s,k}=\frac{(x^C_{s,k}-x^D_{s,k})^2}{2}
]

[
\bar v_k=\frac{1}{N}\sum_s v^{local}_{s,k}
]

[
v_{s,k}=v^{local}_{s,k}+\bar v_k
]

[
A(s;y)=\sum_k
\left[
\frac{(y_k-\mu_{s,k})^2}{v_{s,k}+10^{-12}}
+\log(v_{s,k}+10^{-12})
\right].
]

No mass normalization is used.

Interpretation:
- low-noise source/path component -> deviations penalized strongly;
- high-noise component -> deviations discounted appropriately;
- the log-variance term prevents the model from winning by assigning arbitrarily large uncertainty.

Exploratory discovery data only:
S1_A, S1_B, S2_A, S2_B all had path-action truth rank 1.
This is **not confirmation**, because the formula was discovered after inspecting those cases.

---

## 5. Current fresh confirmation gate — S3

S3 was selected before generating new target data.

Selection rule:
- exclude source candidates within 2 m of S1 or S2;
- among remaining candidates select the one closest to the 630-source median in both:
  - C/D relative realization discrepancy;
  - log mean plume mass.

Frozen S3:

- source id: `pmfs_3_12`
- xyz: `(-4.342730045, -3.700880051, 0.20)`
- C/D relative discrepancy ~15.39%
- global median ~15.27%
- distance from S1 ~2.58 m
- distance from S2 6.60 m

Fresh targets:
- S3_W2_E seed `2026092403`
- S3_W2_F seed `2026092404`

Active branch:
`research/path-action-source-inference-v0`

Frozen execution handoff:
`CODEX_PASI_D0_S3_HANDOFF_20260924.md`

Theory/contract freeze:
`01_idea/PATH_ACTION_SOURCE_INFERENCE_FREEZE_20260924.md`

Scorer:
`research/path_action_source_inference_v0/score_pasi_d0_s3.py`

Runner:
`research/path_action_source_inference_v0/run_pasi_d0_s3_w2_vm.sh`

Package script:
`research/path_action_source_inference_v0/package_pasi_d0_s3_review.sh`

At the time this handoff was written, Codex is already executing this fresh S3 gate.

**Do not duplicate S3 or change its formula.**

Frozen outcomes:

PASS:
`PASI_D0_PASS_FRESH_S3_PATH_ACTION_SIGNAL`

FAIL:
`PASI_D0_FAIL_STOP_PATH_ACTION_MAINLINE`

No rescue after result reveal.

---

## 6. What the second Pro should do now

While Codex runs S3, do **not** run a competing scientific experiment on the same gate.

Use the second Pro for independent work that cannot contaminate S3:

1. audit the PASI scientific argument;
2. search 2025/2026 far-domain literature for path-action / path-space inference / state-dependent stochasticity / large-deviation source-conditioned likelihood;
3. establish a precise prior-art boundary versus:
   - ordinary heteroscedastic Gaussian likelihood;
   - generalized least squares;
   - Mahalanobis scoring;
   - Gaussian processes;
   - stochastic plume ensemble likelihood;
   - Onsager–Machlup parameter inference;
   - source localization work that already uses ensemble uncertainty;
4. challenge whether the current diagonal action proxy is genuinely a second-order adaptation of a big theory or only a standard heteroscedastic NLL;
5. derive what a **real paper-level PASI** would need if S3 passes:
   - path-level temporal dependence, not just diagonal features;
   - source-conditioned stochastic geometry;
   - online approximation compatible with PMFS;
   - an auxiliary module architecture;
6. formulate the next frozen gate, but do not execute it before S3 is independently reviewed;
7. if S3 fails, propose the next far-domain route using the hard empirical constraint:
   **source-conditioned heteroscedastic stochastic path distributions**.

The second Pro must not restart old routes from scratch.

---

## 7. Immediate decision tree

### If S3 FAILS

Freeze:
`PASI_D0_FAIL_STOP_PATH_ACTION_MAINLINE`.

Do not:
- tune the global noise floor;
- change local variance;
- mix raw and normalized scores;
- pick another S3-like source to rescue the formula;
- train a neural model to fit the failed score.

Then use the 630-source heteroscedasticity result as the new scientific constraint and search the next mother theory.

### If S3 PASSES

First:
- independently recompute result from review package;
- verify package/target hashes;
- verify no contract drift.

Then authorize a D1 **second fresh source** chosen before target generation and deliberately in a different stochastic regime (e.g. low- or high-variability quantile), while keeping the path-action formula frozen.

Only after second-source confirmation:
- cross-wind or cross-House offline gate;
- then derive practical online approximation;
- only then PMFS closed loop.

A House02-only S3 PASS is not enough for a main-innovation claim.

---

## 8. Publication architecture if PASI ultimately survives

Tentative only:

### Main innovation
Source-conditioned stochastic path-action inference for PMFS source probability maps.

### Auxiliary innovation A
Efficient estimation / regularization of source-conditioned stochastic path geometry from sparse forward realizations.

### Auxiliary innovation B
Memory- or uncertainty-aware active observation/planning derived from the path-action geometry.

Do not build auxiliary modules before the main offline mechanism survives cross-environment testing.

---

## 9. Non-negotiable process rules

- sequential scientific gates;
- no result-driven tuning;
- no closed loop before offline confirmation;
- no old idea relabeling;
- every claimed innovation must have explicit theoretical ancestry;
- every route must end in PASS/HOLD/STOP/NO-GO;
- freeze code + formulas + data provenance + commit hashes;
- preserve negative results;
- keep PMFS probability-map output.


---

# INCLUDED FILE: docs/FAILED_ROUTE_LEDGER_20260924.md

# Failed / Held Route Ledger — Do Not Restart from Scratch

Date: 2026-09-24

Purpose: prevent a second researcher/model from repeating already-falsified directions.

This is a research-decision ledger, not a chronological diary.

---

## 1. TNQC V5 — Transport-Nuisance Quotient / projection

Status: **NO-GO / HOLD closed**

What was tested:
- frozen 300 s offline protocol;
- six cases H01/H02/H03 × seed0/1;
- integrity passed.

Representative result:
- aggregate decision HOLD;
- fused-vs-native changes were near zero or slightly worse;
- typical deltas approximately -0.007% to -0.061%;
- one H02 case exactly unchanged.

Why it failed:
- quotient/projection did not separate true source from confounded transport strongly enough;
- the improvement magnitude was far below a publishable main innovation;
- projection/quotient ideas also have prior art.

Reusable lesson:
- algebraic nuisance removal is insufficient if the nuisance and source information are entangled in the same observables.

Do not restart as:
- another normalization;
- another quotient;
- another PMFS local reweighting.

---

## 2. Active Deconfounding

Status: **NO-GO**

What was tested:
- fixed transport values;
- grid-off controls;
- equal-budget strategies.

Result:
- 0/6 passed.

Why it failed:
- selected interventions/conditions did not reliably separate true from false source hypotheses.

Reusable lesson:
- active intervention alone does not repair an uninformative or confounded source representation.

Do not restart as generic active experimental design.

---

## 3. DRPE / posterior reweighting

Status: **HOLD then retired**

Theory parent:
NeurIPS 2025.

Idea:
retain native likelihood, learn posterior/reweighting correction.

Problems:
- phase-1 reference behavior was not convincingly reproduced;
- native baseline reproduction itself was fine;
- similar ideas already exist in olfaction;
- 2025 origin did not meet the desired 2026-level novelty target.

Reusable lesson:
- learned posterior correction without a stronger new physical/statistical object is too close to method-level reweighting.

---

## 4. MIPO Active Observability

Status: **retired before further testing**

Evidence:
- branch/evidence around `research/mipo-active-observability-v1`;
- 18 valid anchors;
- 141,120 rows.

Why retired:
- the specific observability idea already had relevant prior art;
- insufficient novelty as the paper-level main idea.

Reusable lesson:
- do not spend simulation budget on a specific mechanism after novelty boundary already fails.

---

## 5. HCMC v1

Status:
`HCMC_V1_INDEPENDENT_OFFLINE_NO_GO`

What mattered:
- some old/offline data appeared promising;
- fresh independent data did not preserve the signal.

Representative native six-case errors were roughly:
4.60, 4.27, 6.93, 4.36, 7.95, 7.96 m.

Why it failed:
- apparent mechanism did not survive independent validation.

Reusable lesson:
- no route is trusted because it works on previously inspected data.
- fresh independent plume/source evidence is mandatory.

---

## 6. Dynamic export / parity route

Status:
`DYNAMIC_EXPORT_STOP_PARITY_NOT_ESTABLISHED`

Key findings:
- offline candidate forward budget was actually 200 × 0.2 s = 40 s;
- ON/OFF had ~154 candidates;
- native PMFS final hit map is a static frequency map;
- historical intermediate estimated-wind grids had been overwritten, preventing exact replay.

Why stopped:
- exact parity contract could not be established.

Reusable lesson:
- do not build a main claim on historical intermediate state that cannot be exactly reconstructed.

---

## 7. M4-v2 / C0.5 compositional operator

Status: **HOLD**

Positive signal:
- on held-out S2×W2, operator field error beat monolithic model;
- reproduced for multiple training seeds / independent plumes.

Failure:
- source-ranking diagnostic already had truth rank 1 for both compared arms;
- therefore better field prediction did not yield source-identification gain;
- wind-swap effect was weak/inconsistent.

Reusable lesson:
- field-prediction quality is not a sufficient objective.
- every candidate must be judged on arbitrary-source identity/ranking.

---

## 8. M4-v3 / D0

Status:
`D0_FAIL_STOP_M4_V3`

Failures:
- held-out wind-response cosine only ~0.341–0.383, below frozen >0.5 gate;
- source superposition error >1e-5;
- one field-error comparison worse than monolithic.

Action:
- no extra seeds;
- no closed loop.

Reusable lesson:
- if basic physical operator properties fail, stop before localization tests.

---

## 9. Source-Lineage Lagrangian v2

Branch:
`research/source-lineage-lagrangian-v2`

Decision:
`L1_FAIL_STOP_SOURCE_LINEAGE_MAINLINE`

Important result:
- deterministic 3D physics improved one-step centroid prediction over 2D by ~74–75%;
- learned lineage residual added only ~0–2%;
- lineage destruction did not remove the apparent gain.

Physical diagnosis:
- GADEN filament stochastic noise produced a one-step random-walk floor approximately matching the observed residual error.

Why it failed:
- deterministic physics was already near the stochastic floor;
- the learned lineage component was not load-bearing.

Reusable lesson:
- once prediction reaches the simulator's stochastic floor, another deterministic learner cannot create source information.

Also note:
generic backward transport / Schrödinger-bridge source localization became occupied by 2026 prior art, so do not restart generic backward-transport as the main novelty.

---

## 10. Causal Biorthogonal Green / Non-Hermitian source-sensor duality

Branch:
`research/causal-biorthogonal-green-v1`

Gate:
exact-physics source-identifiability oracle on 630 arbitrary source candidates.

Decision:
`GATE1A_FAIL_STOP_SOURCE_TO_SENSOR_GREEN_FAMILY`

Frozen result:
- S2_W2_A truth rank mean/C/D = 1 / 2 / 1;
- S2_W2_B = 7 / 7 / 4.

Independent review confirmed:
- no W1/W2 mismatch;
- no scientific-contract-changing infrastructure patch;
- B's top errors remained geographically close to truth.

Scientific diagnosis:
- exact deterministic forward physics identifies the correct local source basin;
- independent stochastic plume realization can still reorder nearby 0.3 m source cells.

Why the family stopped:
- if exact frozen source→sensor physics itself is not realization-robust enough under the gate, a learned Green compression cannot be claimed as the main solution.

Reusable infrastructure:
- 630-source exact-forward C/D bank;
- fixed 30 probes × 10 times;
- W2 contracts;
- exact arbitrary-source benchmark.

Do not rerun the 630×2 bank unless a contract changes for a justified future experiment.

---

## 11. Mori–Zwanzig / realization-invariant source signature

Branch:
`research/realization-invariant-source-signature-v0`

### D0 positive signal
Per-time L1 spatial mass fraction followed by temporal aggregation changed:
- S2 A/B raw = 1/7
- projected static signature = 2/3.

Same-source A/B discrepancy decreased substantially.

### D1 positive signal
Full off-diagonal temporal covariance improved S2 ranks to 1/2, while diagonal/no-memory controls did not.

### D2 positive signal
Target-blind finite-memory rule:
- memory 0: B rank 7
- memory 1: 4
- memory 3: 3
- memory >=4: 2
- automatic horizon = 7.

Decision at this stage:
`D2_ADVANCE_FINITE_MEMORY_SOURCE_LIKELIHOOD`.

### D3 fresh second-source falsification

Truth S1:
`pmfs_10_17 = (-2.242730141,-2.200880051,0.20)`

Result:
- S1_A raw / D0 / diagonal / D2 = **1 / 9 / 6 / 5**
- S1_B = **1 / 1 / 1 / 1**

Decision:
`D3_FAIL_STOP_MZ_SOURCE_INFERENCE_MAINLINE`

Critical interpretation:
- MZ-style memory itself was not disproved;
- the mainline failed because it globally removed absolute plume mass before inference.

For S1:
- absolute concentration was stable and informative.

For S2:
- absolute amplitude was much more realization-sensitive.

630-source audit then showed stochastic variability ranges roughly 1.5%–57.5%.

Therefore:
**global realization invariance is the wrong abstraction.**

Do not rescue with:
- raw + normalized mixing after seeing D3;
- source-dependent hand weights;
- changing memory horizon;
- another normalization.

Reusable lesson:
the stochastic distribution itself must be source conditioned.

---

## 12. Current transition: Path-Action Source Inference (PASI)

Status at handoff creation:
**active fresh S3 confirmation in progress**.

Why this route is different:
it does not attempt to make every source share the same invariant representation.

Instead it scores an observation under each candidate's own stochastic uncertainty.

This is the first post-D3 route designed explicitly around the 630-source heteroscedasticity diagnosis.

See:
- `docs/PRO6_PROJECT_HANDOFF_20260924.md`
- `01_idea/PATH_ACTION_SOURCE_INFERENCE_FREEZE_20260924.md`
- `CODEX_PASI_D0_S3_HANDOFF_20260924.md`

Do not restart any route above unless there is a genuinely new scientific object that directly addresses its recorded failure mechanism.


---

# INCLUDED FILE: docs/RESEARCH_GOVERNANCE_MAIN_VS_AUX_20260924.md

# Research Governance — Mainline vs Auxiliary Pro

Date: 2026-09-24

Project:
UAV gas source localization with GADEN -> offline falsification -> PMFS closed loop -> later real flight.

## 1. Role ownership

### Mainline lead: primary ChatGPT thread

The primary thread owns all scientific decisions.

Only the primary thread may:

1. define / revise the scientific problem;
2. define the benchmark and evaluation ruler;
3. freeze experimental contracts;
4. set PASS / HOLD / STOP / NO-GO thresholds;
5. decide whether a route is promoted, held, or killed;
6. decide which mother theory becomes the next mainline;
7. authorize new simulations;
8. authorize cross-house / cross-wind tests;
9. authorize PMFS closed-loop experiments;
10. integrate literature, theory, data and reproducibility evidence into the final paper architecture.

The primary thread must independently recompute all decisive experimental results before promotion.

### Auxiliary role: second Pro account

The second Pro is an **auxiliary theory/literature expert**.

It may:

1. deeply search 2025/2026 literature;
2. map prior art and novelty boundaries;
3. derive candidate mathematical formulations;
4. compare alternative formulations of the same frozen scientific object;
5. identify mathematical weaknesses and hidden assumptions;
6. propose possible second-order innovations;
7. propose falsification tests on paper;
8. inspect whether a proposed innovation is genuinely different from failed routes;
9. prepare paper-safe theoretical language and derivations.

It may NOT:

1. change the active R0 benchmark;
2. change R0 thresholds;
3. decide R0 PASS/HOLD/STOP;
4. declare a main innovation established;
5. create a competing scientific mainline before primary-thread authorization;
6. launch new GADEN/PMFS experiments without authorization;
7. rescue a failed frozen gate;
8. promote a literature idea directly to “the main innovation”;
9. overwrite active execution branches.

---

## 2. Current mainline state

PASI is frozen:

`PASI_D0_FAIL_STOP_PATH_ACTION_MAINLINE`

The active work is:

`R0 stochastic benchmark refoundation`

R0 asks:

> Which source-conditioned stochastic plume statistics are reproducibly estimable from finite independent realizations under the current 10×30 observation operator?

R0 is already frozen and being executed.

The auxiliary Pro should not redesign R0 now.

---

## 3. What the auxiliary Pro should do before R0 returns

The primary thread owns the ruler.

The auxiliary Pro should use the waiting time to build a **conditional theory library**, not choose a winner.

### Track A — finite-realization stochastic identifiability

Deeply review current work on:

- finite-sample stochastic-process inference;
- trajectory identifiability;
- sample complexity of variance/covariance/path statistics;
- sparse trajectory inference;
- model indistinguishability;
- uncertainty of source-/state-conditioned stochastic descriptors.

Deliver:
- what can realistically stabilize with K=16;
- what likely requires much larger K;
- which statistics have known finite-sample guarantees or robust estimators.

### Track B — turbulent plume statistical objects

Deeply review:

- concentration intermittency;
- encounter statistics;
- zero/nonzero / blank duration statistics;
- first-passage / first-arrival statistics;
- burst duration and inter-encounter intervals;
- heavy-tailed concentration distributions;
- spatial/temporal correlation;
- plume meandering vs relative dispersion;
- robust descriptors across independent realizations.

Deliver:
a map from each physical stochastic object to:
- theoretical origin;
- recent 2025/2026 evidence;
- likely sample complexity;
- whether it can carry source identity;
- whether it has already been used in GSL/olfaction.

### Track C — conditional mother-theory derivations

Do not select a main theory yet.

Prepare mathematically serious derivations for three possible R0 outcomes:

#### If R0 shows full path distributions are stable
Explore:
- path-space likelihood;
- stochastic action / large deviations;
- source-conditioned path geometry;
- distributional distance / likelihood-ratio formulations.

#### If R0 shows only encounter/intermittency statistics are stable
Explore:
- point-process / renewal-process representations;
- event-based source inference;
- survival / first-passage theory;
- stochastic geometry of odor encounters.

#### If R0 shows only basin-scale spatial quantities are stable
Explore:
- coarse source-basin probability;
- multiscale localization;
- information geometry / coarse-grained state representations;
- theories that explicitly distinguish identifiable macrostate from unidentifiable microstate.

For each conditional direction, derive:
1. mother theory;
2. the exact new mathematical object;
3. GSL-specific second-order adaptation;
4. how it maps to a PMFS probability map;
5. what data would immediately falsify it;
6. novelty boundary against existing GSL/olfaction.

---

## 4. What the auxiliary Pro may derive now

The second Pro is encouraged to derive **candidate second-order innovations** in advance, but only conditionally.

A valid derivation must be written as:

> IF R0 establishes X as reproducible, THEN candidate innovation Y is mathematically justified because ...

Not:

> We should now switch to Y.

Each derivation must identify which empirical premise it depends on.

No premise may be assumed before R0.

---

## 5. Output format required from auxiliary Pro

The auxiliary Pro should return at most three compact deliverables:

### A. Literature evidence matrix

Columns:
- stochastic object;
- far-domain theory;
- 2025/2026 anchor papers;
- code availability;
- finite-sample requirements;
- prior use in GSL/olfaction;
- novelty risk.

### B. Conditional derivation notebook / memo

One section for each R0 outcome:
- full path stable;
- encounter statistics stable;
- only coarse basin stable / path unstable.

Each section includes equations and a possible second-order innovation, but clearly marked **conditional**.

### C. Red-team memo

For every candidate derivation:
- strongest reason it may fail;
- nearest prior art;
- minimum offline falsification;
- STOP condition.

No long brainstorm list.

---

## 6. Handoff after R0

When R0 completes:

1. primary thread independently recomputes R0;
2. primary thread assigns PASS/HOLD/STOP;
3. primary thread identifies the empirically stable stochastic object;
4. primary thread sends one narrow object to auxiliary Pro;
5. auxiliary Pro deepens literature and second-order derivation only for that object;
6. primary thread chooses whether to promote it into the next experimental mainline.

This preserves one scientific authority and prevents parallel drift.

---

## 7. Rule of evidence

Literature can motivate a theory.

Only frozen independent data can promote it.

The auxiliary Pro is therefore a **theory multiplier**, not an experiment governor.


---

# INCLUDED FILE: docs/PRO6_R0_SYNC_20260924.md

# PRO6 SYNC UPDATE — PASI STOP -> R0 STOCHASTIC BENCHMARK REFOUNDATION

Date: 2026-09-24

Repository: https://github.com/kris-yun/uav-gsl-isj

Repository visibility: **PUBLIC**

Coordination branch:
https://github.com/kris-yun/uav-gsl-isj/tree/research/pro6-sync-handoff-20260924

Current active benchmark branch:
https://github.com/kris-yun/uav-gsl-isj/tree/research/stochastic-benchmark-refoundation-20260924

Important: if your session cannot connect GitHub, do not interpret that as the repository being private. Use the self-contained context in this document and ask the user to paste the needed file only if absolutely necessary.

---

## 1. Superseded part of your previous analysis

Your previous PASI audit contained useful theory criticism, especially:

- the frozen PASI score is mathematically a source-conditioned diagonal Gaussian likelihood/NLL;
- it is not yet a genuine Onsager–Machlup / Freidlin–Wentzell derivation;
- two realizations per source are statistically inadequate for stable source-conditioned variance estimation.

Keep those conclusions.

However, the following previous branch of work is now obsolete:

- “if S3 PASS, pre-register D1-HQ high-variability source confirmation.”

S3 did **not** pass.

The frozen result is:

`PASI_D0_FAIL_STOP_PATH_ACTION_MAINLINE`

Do not execute or refine the D1-HQ PASI continuation.

---

## 2. PASI D0 fresh-S3 result

Branch:
`research/path-action-source-inference-v0`

Final commit:
`d43db8ff581b7e855c953fea972fa28e00fd5bf3`

Frozen ranks:

| target | raw | homoscedastic | heteroscedastic residual | PASI path action |
|---|---:|---:|---:|---:|
| S3_W2_E | 4 | 3 | 3 | 3 |
| S3_W2_F | 13 | 14 | 13 | 13 |

Rank sums:
- raw 17
- homoscedastic 17
- heteroscedastic residual 16
- PASI 16

Decision:
`PASI_D0_FAIL_STOP_PATH_ACTION_MAINLINE`

No tuning or rescue is authorized.

---

## 3. New meta-diagnosis

The critical new finding is not simply “PASI failed.”

S3 was originally selected because its legacy C/D prediction pair suggested a typical source stochasticity:

- C/D relative L2 discrepancy ~0.1539.

But after generating two completely fresh same-source targets E/F:

- E/F relative L2 discrepancy ~0.5344;
- E/F cosine ~0.9283.

For the same S3, same House02, same W2, same simulator/occupancy/extractor contract, four realizations now show pairwise relative discrepancies approximately:

- C-D 0.154
- C-E 0.264
- C-F 0.323
- D-E 0.143
- D-F 0.422
- E-F 0.534

Thus a source classified as “median stochasticity” from only C/D was not actually demonstrated to be median.

This reveals a project-level methodological problem:

> recent routes have repeatedly converted under-sampled realization structure into scientific mechanism.

The existing 630-source C/D bank is strong deterministic-transfer infrastructure, but **two realizations per source are not statistically sufficient to infer source-conditioned variance, covariance, tail structure, or stochastic path measures.**

This likely explains the recurring pattern:

- discovery set gives a strong signal;
- mechanism narrative looks convincing;
- first fresh realization immediately breaks it.

---

## 4. Why two realizations are statistically inadequate

PASI used:

[
hat v_{s,k} = (C_{s,k}-D_{s,k})^2 / 2.
]

With two independent samples, the sample variance has only one degree of freedom.

Even under an ideal Gaussian assumption, the variance estimator has coefficient of variation:

[
sqrt{2/(n-1)} = sqrt{2} approx 141%, quad n=2.
]

The plume process is additionally intermittent, sparse and likely heavy-tailed.

Therefore:

- the two-seed C/D bank must not be treated as a stable per-source stochastic distribution;
- source “low/mid/high stochasticity” labels from C/D are only sampling strata;
- they require multi-realization calibration.

---

## 5. Current active task: R0 benchmark refoundation

Active branch:
`research/stochastic-benchmark-refoundation-20260924`

Frozen protocol:
`research/stochastic_benchmark_refoundation/R0_PROTOCOL_FREEZE_20260924.md`

Codex handoff:
`CODEX_R0_STOCHASTIC_BENCHMARK_HANDOFF_20260924.md`

R0 is already prepared for Codex execution.

R0 is not a new algorithm and does not rescue PASI.

### Frozen R0 design

Panel:
- 18 source locations.

Sampling construction:
- 3 legacy C/D variability strata: low/mid/high;
- 3 legacy plume-mass strata: low/mid/high;
- 2 spatially separated representatives per cross-stratum;
- all at least 2 m from S1/S2/S3.

New data:
- 16 completely new realizations per source;
- 18 × 16 = **288 new GADEN realizations**;
- new seeds 2026093001 ... 2026093288;
- C/D are NOT included in the 16-realization R0 estimator.

Environment:
- House02
- W2 = 3,5-1_slow
- same GADEN / occupancy / extractor
- same 10 times × 30 pooled probes.

---

## 6. What R0 tests

R0 asks:

> Is source-conditioned stochasticity itself a reproducible object under the current observation operator?

Primary descriptor:

median pairwise relative L2 distance among same-source realizations.

For K = 2,4,8,12,16 report:
- median pairwise relative L2;
- q90 relative L2;
- median pairwise cosine;
- q10 cosine;
- total plume-mass distribution;
- zero fraction;
- first-arrival statistics.

Two independent 8-vs-8 reproducibility tests:
- replicates 1–8 vs 9–16;
- odd vs even replicates.

Across the 18 sources report:
- Spearman correlation of source stochasticity;
- low/mid/high stochasticity tercile agreement;
- mass reproducibility.

K-convergence:
- K8 vs K16;
- K12 vs K16.

---

## 7. Frozen R0 decisions

### PASS
`R0_PASS_STOCHASTIC_BENCHMARK_USABLE`

Requires all:
- complete 18×16;
- both split variability Spearman >= 0.70;
- both split stochasticity-tercile agreement >= 0.50;
- K8->16 median change <= 0.25;
- K8->16 q75 <= 0.40;
- K12->16 median <= 0.15;
- K12->16 q75 <= 0.25.

Interpretation:
16-realization source stochastic summaries are reproducible enough to support a new stochastic benchmark.

### HOLD
`R0_HOLD_MORE_REALIZATIONS_REQUIRED`

If PASS fails but:
- both split Spearman >=0.40;
- K12->16 median <=0.25;
- K12->16 q75 <=0.40.

Interpretation:
the object may be real, but 16 realizations are still insufficient.

### STOP
`R0_STOP_PER_SOURCE_DISTRIBUTION_MAINLINE_UNSTABLE`

If HOLD fails.

Interpretation:
under the current observation operator, per-source stochastic path distributions are not stable enough to support the next mainline.

---

## 8. Your task now

Do NOT search for the next main innovation yet.

Your job is to act as an independent methodological/theory reviewer of R0 while Codex executes it.

### Task A — audit the R0 design

Check whether:
- 18 sources adequately cover the legacy 3×3 variability/mass strata;
- 16 new realizations is a sensible first calibration size;
- the two 8/8 splits are a defensible reproducibility test;
- median pairwise relative L2 is an acceptable primary descriptor;
- the convergence thresholds are too weak, too strong, or statistically incoherent;
- source-level stochastic ranking should also use bootstrap / rank uncertainty / Kendall tau / ICC / variance components.

Do not change the frozen R0 being executed.
Any alternative is a recommendation for R1 only.

### Task B — identify which stochastic object should be tested after R0

Do not crown a theory.

Instead map possible R0 outcomes to possible scientific objects.

Examples:
- if amplitude/intermittency statistics are stable but full path geometry is not -> encounter/intermittency statistics may be the right object;
- if source-conditioned pairwise path distributions are stable -> path-ensemble/large-deviation ideas remain viable;
- if only basin-scale quantities are stable -> shift source-identifiability question to spatial basin/probability mass;
- if nothing is stable -> abandon per-source distribution mainlines under this observation operator.

### Task C — literature audit

Use current 2025/2026 literature to find work on:
- turbulent plume intermittency;
- heavy-tailed concentration statistics;
- encounter statistics;
- finite-sample inference of stochastic dynamics;
- sample complexity of source-/state-conditioned stochastic models;
- identifiability of stochastic processes from sparse trajectories.

The goal is not to find a method yet.
The goal is to determine what statistics can reasonably be expected to converge from 16 realizations and what physical object should be trusted.

### Task D — prepare a decision tree only

Prepare:

**If R0 PASS**
- what one mother-theory family should be investigated next;
- what held-out multi-realization validation would be required.

**If R0 HOLD**
- how many additional realizations should be added and by what convergence criterion;
- no new method.

**If R0 STOP**
- what scientific object should replace per-source path distributions;
- at most one candidate theory family.

Do not execute anything.

---

## 9. Proposal-safe framing after PASI failure

Stable scientific problem:

> UAV gas-source localization is limited not only by transport-model mismatch but by the finite-sample identifiability of highly intermittent stochastic plume observations. Before treating source-dependent variance, memory or path distributions as localization information, one must establish which source-conditioned statistics are reproducible across independent plume realizations and at what spatial resolution they uniquely identify the source.

This statement does not depend on PASI succeeding.

---

## 10. Files to read if GitHub access works

Public repository:
https://github.com/kris-yun/uav-gsl-isj

Coordination branch:
https://github.com/kris-yun/uav-gsl-isj/tree/research/pro6-sync-handoff-20260924

R0 branch:
https://github.com/kris-yun/uav-gsl-isj/tree/research/stochastic-benchmark-refoundation-20260924

Key R0 files:
- research/stochastic_benchmark_refoundation/R0_PROTOCOL_FREEZE_20260924.md
- research/stochastic_benchmark_refoundation/R0_SOURCE_PANEL_18.tsv
- research/stochastic_benchmark_refoundation/R0_SEED_MATRIX_18x16.tsv
- research/stochastic_benchmark_refoundation/analyze_r0_stability.py
- CODEX_R0_STOCHASTIC_BENCHMARK_HANDOFF_20260924.md

If GitHub tools are unavailable, use this document as the authoritative fallback context and do not ask the user to reconstruct the whole project history.


---

# INCLUDED FILE: docs/PRO6_POST_R0_PASS_ASSIGNMENT_20260924.md

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


---

# INCLUDED FILE: PROMPT_GPT6PRO_AUXILIARY_THEORY_20260924.md

你现在是这个 UAV 气源定位项目的辅助理论专家，不是主线负责人。

主线负责人是另一个主 ChatGPT 线程。它负责：
- 科学问题定义
- R0 benchmark 规范
- PASS/HOLD/STOP
- 选择主创新母理论
- 冻结实验
- 独立复算
- 是否允许 Codex 继续实验

你不能自行修改这些决定。

GitHub:
https://github.com/kris-yun/uav-gsl-isj

协调分支：
research/pro6-sync-handoff-20260924

优先阅读：
docs/RESEARCH_GOVERNANCE_MAIN_VS_AUX_20260924.md
docs/PRO6_R0_SYNC_20260924.md

当前状态：

PASI 已经 frozen FAIL：
PASI_D0_FAIL_STOP_PATH_ACTION_MAINLINE

现在正在由 Codex 执行：
R0 stochastic benchmark refoundation

R0 的问题是：

**在当前 10×30 observation operator 下，哪些 source-conditioned stochastic plume statistics 可以从有限 independent realizations 中稳定估计？**

R0 已经冻结。
你不要修改 R0 source panel、seed、指标或阈值，也不要自行启动新实验。

你现在主要做两类工作：

## 第一类：深挖文献

重点深挖 2025/2026：

1. finite-sample stochastic process inference
2. stochastic model identifiability
3. sparse trajectory inference
4. sample complexity of variance/covariance/path statistics
5. turbulent plume intermittency
6. encounter statistics
7. zero/nonzero duration
8. first-arrival / first-passage
9. burst / inter-encounter intervals
10. heavy-tail / mixture statistics
11. plume meandering vs relative dispersion
12. stochastic path-space inference
13. event-based inference
14. information/coarse-graining when microstate is unidentifiable

优先 peer-reviewed top journals/conferences，优先 2025/2026，记录代码。

特别回答：

**K=16 independent realizations 理论上最可能先稳定哪些 stochastic statistics？哪些量即使 K=16 也很危险？**

## 第二类：做“条件式二次创新推导”

你可以提前推导二次创新，但不能提前选主线。

所有推导必须写成：

**IF R0 establishes X, THEN Y becomes justified.**

分别准备三种条件：

### A. 如果 R0 证明 full path distribution / covariance 等稳定
你可以推导：
- path-space likelihood
- large-deviation / action
- stochastic path geometry
- distributional likelihood-ratio
等真正带 path coupling 的方法。

### B. 如果 R0 证明只有 encounter / intermittency statistics 稳定
你可以推导：
- point process
- renewal process
- survival / first-passage
- event-based source inference
等。

### C. 如果 R0 证明 exact-cell stochastic statistics 不稳定，但 source basin 稳定
你可以推导：
- coarse-grained source macrostate
- multiscale source probability
- information geometry / identifiable macrostate
等。

每个候选二次创新必须写清楚：

1. 母理论是什么
2. 2025/2026 理论来源
3. GSL 中真正新的数学对象是什么
4. 与 TNQC/HCMC/M4/SLL/Bi-Green/MZ/PASI 的区别
5. 如何输出 PMFS source probability map
6. 最便宜的离线 falsification
7. 什么结果直接 STOP
8. 已有 GSL/olfaction 是否有人做过类似点

你不是来列十个点子的。

最终最多给 3 个“条件式候选”，分别对应 R0 的不同结果。

## 你的角色边界

你可以：
- 查文献
- 推公式
- 找代码
- 做 prior-art audit
- 做 novelty audit
- 做 red-team
- 提条件式二次创新

你不可以：
- 改 R0
- 自己宣布 PASS/HOLD/STOP
- 自己开新主线
- 自己让 Codex 跑实验
- 救已经 FAIL 的 PASI
- 因为看到某篇漂亮论文就把它升成主创新

最终交付：

1. Literature evidence matrix
2. K=16 sample adequacy 理论分析
3. 三种 R0 结果对应的 conditional second-order derivations
4. 每个 derivation 的 red-team / nearest prior art / STOP test
5. 给主线负责人的一页推荐：等 R0 结果出来后，哪种 empirical pattern 应该映射到哪类理论

不要重新复盘整个项目历史。
主线程会负责最终裁决。


---

# INCLUDED FILE: evidence/stochastic_benchmark_refoundation/PASI_D0_INDEPENDENT_REVIEW_20260924.md

# PASI D0 Independent Review and Meta-Diagnosis — 2026-09-24

Reviewed branch:
`research/path-action-source-inference-v0`

Reviewed result commit:
`d43db8ff581b7e855c953fea972fa28e00fd5bf3`

Frozen scientific decision remains:

`PASI_D0_FAIL_STOP_PATH_ACTION_MAINLINE`

This document does **not** rescue PASI. It diagnoses why several recent candidate mainlines have shown promising discovery-set signals and then failed immediately on fresh stochastic plume realizations.

## 1. Package integrity

Reviewed archives:

### PASI D0 S3 package
- bytes: 142,204
- SHA256:
  `36283a86ca5ca61e0782e5a84b45a0c77f02e998d743bfb20b7570214a84931b`

### Gate1A prediction package
- bytes: 1,281,180
- SHA256:
  `9f2c4e93c3833b00dd82d3f53a21e2286f23afdf3e5087328fc094cada1ba2be`

Both archives' internal `SHA256SUMS.txt` manifests independently verify.

## 2. Independent recomputation

Using the original 630-source C/D prediction bank, frozen probe operator, and the two new S3 target cubes, the four scores were independently recomputed.

Truth:
- `pmfs_3_12`
- `(-4.342730045, -3.700880051, 0.20)`

Exact reproduced ranks:

| target | raw | homoscedastic | heteroscedastic residual | path action |
|---|---:|---:|---:|---:|
| S3_W2_E | 4 | 3 | 3 | 3 |
| S3_W2_F | 13 | 14 | 13 | 13 |

Rank sums:
- raw: 17
- homoscedastic: 17
- heteroscedastic residual: 16
- path action: 16

Therefore the frozen decision is correctly:
`PASI_D0_FAIL_STOP_PATH_ACTION_MAINLINE`.

## 3. Crucial diagnostic: the S3 stochastic regime estimate was wrong

S3 was selected before fresh targets because prediction C/D appeared to show a typical realization-variability regime.

For S3 prediction C/D:
- cosine similarity: ~0.99353
- relative L2 discrepancy: ~0.15391

But fresh same-source targets E/F show:
- cosine similarity: ~0.92831
- relative L2 discrepancy: ~0.53436

Thus the fresh same-source realization difference is more than 3 times the C/D estimate.

The source was not actually demonstrated to be a stable “median stochasticity regime”; one randomly sampled pair C/D merely looked median.

No wind/config drift was found: C/D/E/F share House02, W2, the same GADEN binary, occupancy, extractor and source location.

## 4. Four-realization S3 audit

S3 now has four realizations for diagnosis:
- C = 2026092401
- D = 2026092402
- E = 2026092403
- F = 2026092404

Pairwise relative path discrepancies:
- C-D: ~0.154
- C-E: ~0.264
- C-F: ~0.323
- D-E: ~0.143
- D-F: ~0.422
- E-F: ~0.534

F also shows substantially earlier and larger plume mass than C/D/E.

## 5. Two realizations are insufficient for stochastic-distribution claims

PASI used

[
v^{local}_{s,k}=\frac{(x^C_{s,k}-x^D_{s,k})^2}{2}
]

as candidate-specific stochastic variance.

With two samples, a sample variance has only one degree of freedom.

Even under Gaussian assumptions, the variance-estimator coefficient of variation at n=2 is approximately

[
\sqrt{2/(n-1)}=\sqrt{2}\approx141\%.
]

The plume is additionally sparse and intermittent, so two draws cannot support strong claims about source-conditioned path distributions.

The 630×C/D bank remains excellent deterministic-transfer infrastructure, but is statistically inadequate for estimating per-source stochastic variance, covariance, heavy-tail structure or path action.

## 6. Why recent routes repeatedly looked good before fresh validation

The emerging common pattern is:

- Bi-Green: exact deterministic physics identifies a local source basin but fresh plume realization reorders nearby exact cells.
- MZ: S2-based invariance looked strong, but fresh S1 showed that global nuisance removal deleted useful information.
- PASI: S1/S2 plus the same two-seed C/D bank suggested source-conditioned variance; fresh S3 showed that the source stochastic regime itself was badly estimated.

The project has therefore been adaptively interpreting under-sampled realization structure as mechanism.

## 7. Exact-cell rank is also exposing an identifiability-scale issue

PASI errors remain spatially local.

For E:
- best path-action candidate is 0.30 m from truth;
- truth rank 3.

For F:
- best path-action candidate is ~0.67 m from truth;
- truth rank 13;
- many high-ranked candidates remain in the local basin.

The frozen PASI FAIL remains valid. Do not change its gate after the result.

For future candidates, pre-register and report separately:
1. exact-cell truth rank;
2. MAP spatial error;
3. top-k spatial radius / basin concentration;
4. proper probabilistic score when a probability map exists.

## 8. Scientific conclusion

The current bottleneck is one level below mother-theory selection:

> the project does not yet have a statistically adequate offline benchmark for testing methods whose claimed mechanism depends on stochastic plume distributions.

Before choosing the next main innovation, the stochastic evaluation foundation must be repaired.

## 9. Frozen action

PASI remains stopped.

Do not rescue PASI by:
- adding seeds and reinterpreting the same D0;
- changing variance floor;
- fitting richer covariance after seeing S3;
- changing thresholds.

Additional realizations are authorized only as a **new benchmark-characterization study**, not a PASI rescue.


---

# INCLUDED FILE: research/stochastic_benchmark_refoundation/R0_PROTOCOL_FREEZE_20260924.md

# R0 Frozen Protocol — Multi-Realization Stochastic Benchmark Calibration

Date: 2026-09-24

Branch:
`research/stochastic-benchmark-refoundation-20260924`

Status:
**EXECUTE BENCHMARK CALIBRATION ONLY**

This is not a new gas-source-localization method and does not rescue PASI.

## 1. Question

Can the current House02/W2 observation operator support reproducible source-conditioned stochastic plume descriptors, or have recent routes been over-interpreting two-seed realization structure?

R0 asks whether stochastic descriptors converge across independent realizations before any new mother theory is selected.

## 2. Frozen environment

House:
`House02`

Wind:
`W2 = 3,5-1_slow`

Use the exact same GADEN, occupancy, wind and extractor contracts as PASI/Gate1A.

Observation operator:
- 10 frozen times: 100,150,...,550;
- 30 frozen pooled probes;
- pooled array shape: 10×30.

Legacy Gate1A C/D:
- C = 2026092401
- D = 2026092402

Legacy C/D are used only to construct the initial stratified source panel and later audit whether a two-seed estimate was representative.

**They are not included in the R0 16-realization estimator.**

## 3. Frozen 18-source panel

Panel file:
`research/stochastic_benchmark_refoundation/R0_SOURCE_PANEL_18.tsv`

Selection is deterministic:

1. remove every candidate within 2.0 m of S1/S2/S3;
2. using legacy C/D only, compute:
   - relative path discrepancy;
   - mean path mass;
3. split each variable into three eligible-source terciles: low/mid/high;
4. form the 3×3 cross-strata;
5. in each stratum choose:
   - one candidate closest to the within-stratum robust metric center;
   - one candidate spatially farthest from that central candidate.

Total:
3 × 3 × 2 = **18 sources**.

The old C/D strata are sampling strata only. R0 explicitly tests whether they remain meaningful under many new realizations.

## 4. Frozen 288 new simulations

Seed matrix:
`research/stochastic_benchmark_refoundation/R0_SEED_MATRIX_18x16.tsv`

Each source receives 16 completely new, unique RNG seeds.

Total:
18 × 16 = **288 new plume realizations**.

Seed range:
`2026093001 ... 2026093288`

No seed is reused between panel sources.

## 5. Frozen stochastic descriptors

For each source and each K in:

`K = 2, 4, 8, 12, 16`

compute:

- median pairwise relative L2 path discrepancy;
- 90th percentile pairwise relative L2;
- median pairwise cosine;
- 10th percentile pairwise cosine;
- median / q10 / q90 total observed plume mass;
- median zero fraction;
- median first-arrival time index.

Primary source-stochasticity descriptor for the R0 decision:

**median pairwise relative L2 path discrepancy**.

For realizations a,b:

[
d(a,b)=
\frac{\|a-b\|_2}
{\left\|\frac{a+b}{2}\right\|_2+10^{-12}}
]

## 6. Frozen reproducibility tests

Two independent 8-vs-8 split structures are required:

### Split A
replicates 1–8 versus 9–16.

### Split B
odd replicates versus even replicates.

For each split report across the 18 sources:

- Spearman correlation of source median pairwise relative-L2 variability;
- Spearman correlation of median total mass;
- exact agreement of low/mid/high variability tercile assignment.

This tests whether “which sources are more stochastic” survives different realization samples.

## 7. Frozen K-convergence tests

For each source compare its primary variability statistic from:

- K=8 versus K=16;
- K=12 versus K=16.

Relative change:

[
\Delta_K(s)=
\frac{|D_K(s)-D_{16}(s)|}{|D_{16}(s)|+10^{-12}}
]

Aggregate:
- median (Delta_K);
- 75th percentile (Delta_K);
- maximum diagnostic.

## 8. Frozen R0 decision

### PASS

Decision:

`R0_PASS_STOCHASTIC_BENCHMARK_USABLE`

All must hold:

1. complete 18×16 data;
2. both 8/8 split variability Spearman ≥ 0.70;
3. both split low/mid/high variability-tercile agreement ≥ 0.50;
4. K8→K16 median relative change ≤ 0.25;
5. K8→K16 q75 relative change ≤ 0.40;
6. K12→K16 median relative change ≤ 0.15;
7. K12→K16 q75 relative change ≤ 0.25.

Interpretation:
16-realization source stochastic summaries are reproducible enough to support a new stochastic benchmark.

PASS does **not** validate PASI, Gaussianity, Onsager–Machlup, or any main innovation.

### HOLD

Decision:

`R0_HOLD_MORE_REALIZATIONS_REQUIRED`

If PASS fails but all hold:

- complete 18×16;
- both variability split Spearman ≥ 0.40;
- K12→K16 median relative change ≤ 0.25;
- K12→K16 q75 relative change ≤ 0.40.

Interpretation:
statistics are partly stabilizing but 16 realizations are not enough. Increase K before searching for the next mainline.

### STOP

Decision:

`R0_STOP_PER_SOURCE_DISTRIBUTION_MAINLINE_UNSTABLE`

If even HOLD fails.

Interpretation:
under the current observation operator, per-source stochastic descriptors remain too unstable for a practical source-conditioned path-distribution mainline.

Do not rescue by changing thresholds after the result.

## 9. Diagnostic outputs that do not control PASS

R0 also reports:

- legacy C/D variability vs 16-realization variability Spearman;
- median total-mass split reproducibility;
- pairwise heavy-tail/intermittency summaries;
- zero-hit and arrival-time statistics.

These diagnose why two-seed routes failed but do not alter the frozen R0 decision.

## 10. After R0

### If PASS
Only then choose the next mother theory based on the observed stochastic object and define separate:
- development sources/seeds;
- locked validation sources/seeds;
- final test sources/seeds.

### If HOLD
Generate more realizations for the same frozen panel. Do not change source panel or theory.

### If STOP
Do not build the next main innovation around per-source stochastic path distributions with this observation operator. Search a different scientific object.

No PMFS closed-loop work is authorized by R0.


---

# INCLUDED FILE: evidence/stochastic_benchmark_refoundation/R0_INDEPENDENT_REVIEW_AND_OBJECT_SELECTION_20260924.md

# R0 Independent Review and Post-PASS Scientific Interpretation

Date: 2026-09-24

Reviewed branch:
`research/stochastic-benchmark-refoundation-20260924`

Reviewed result commit:
`e527beea07c33cdbc362d156545409245f029968`

Independent decision:
**R0_PASS_STOCHASTIC_BENCHMARK_USABLE — CONFIRMED**

This review independently recomputes the frozen R0 metrics from the 288 compact pooled realizations. It then asks a separate post-PASS question: which stochastic objects are actually stable enough to justify the next mainline search?

---

## 1. Package integrity

Review package:
`R0_STOCHASTIC_BENCHMARK_REVIEW_20260924.tar.gz`

- bytes: 245604
- SHA256:
  `030c7aa814c4edfe0c6912bb4fc7faf36970142911e0f6c28822f2dd39049c1e`

All 595 files listed in the internal SHA256 manifest independently verify.

The package contains:

- 18 frozen source identities;
- 288 unique new RNG seeds;
- 16 independent 10×30 pooled realizations for every source;
- frozen R0 protocol and code;
- final clean Git state at commit `e527beea07c33cdbc362d156545409245f029968`.

No infrastructure-only patch was reported.

---

## 2. Independent recomputation of frozen R0

The committed result JSON was not trusted.

All primary metrics were independently recomputed from the 288 `pooled.npy` arrays.

### Split reproducibility

Primary source stochasticity:
median pairwise relative-L2 same-source discrepancy.

Independent result:

| split | variability Spearman | mass Spearman | variability-tercile agreement |
|---|---:|---:|---:|
| replicates 1–8 vs 9–16 | **0.721362** | 0.979360 | **0.666667** |
| odd 8 vs even 8 | **0.742002** | 0.966976 | **0.722222** |

Therefore:
- minimum variability Spearman = **0.721362**;
- minimum tercile agreement = **0.666667**.

Both satisfy the frozen PASS gate.

### K-convergence

Independent recomputation:

K8 -> K16 relative change:
- median = **0.154564**
- q75 = **0.263679**
- max = 0.634599

K12 -> K16:
- median = **0.104050**
- q75 = **0.189217**
- max = 0.379987

All frozen PASS thresholds are met.

### Legacy two-realization audit

Legacy C/D discrepancy versus 16-realization source stochasticity:

Spearman = **0.504644**.

This confirms the previous diagnosis:

> two realizations contain some signal about source stochasticity but are too noisy to be treated as a stable source-conditioned stochastic law.

---

## 3. What R0 PASS does and does not establish

R0 PASS establishes:

1. source-conditioned stochastic plume behavior is not pure realization noise;
2. with repeated realizations, source-level stochastic descriptors become reproducible;
3. a multi-realization stochastic benchmark is scientifically usable;
4. the old C/D two-sample labels were materially noisy.

R0 PASS does **not** establish:

- Gaussianity;
- PASI;
- a stable 300-D covariance;
- a full path probability law;
- Onsager–Machlup / large deviations;
- exact 0.30 m source-cell identifiability;
- cross-House generalization.

The next mainline must therefore be based on the stochastic objects that R0 actually shows are stable.

---

## 4. Which objects are most reproducible?

Using the same two independent 8/8 splits, additional diagnostics were computed.

Approximate source-order Spearman reproducibility:

| descriptor | first8 vs last8 | odd8 vs even8 |
|---|---:|---:|
| median pairwise relative-L2 | 0.721 | 0.742 |
| q90 pairwise relative-L2 | 0.822 | 0.719 |
| median pairwise cosine | 0.893 | 0.829 |
| median total plume mass | **0.979** | **0.967** |
| median zero fraction | **0.997** | **0.977** |
| median first-arrival index | ~**1.000** | ~**1.000** |

The last statistic is discrete and tied, so its near-perfect rank correlation should not be overinterpreted.

The main scientific observation is stronger:

> encounter/support statistics are more reproducible across realization subsets than raw amplitude variability.

---

## 5. Encounter-probability profile convergence

For each source define the empirical binary encounter field over the frozen 10×30 observation coordinates:

[
P_s(t,q)=Pr[C_s(t,q)>0].
]

Estimate (P_s) from the first K realizations and compare to the K=16 estimate.

Relative profile error versus K=16:

| K | median | q75 | max |
|---:|---:|---:|---:|
| 2 | 0.204 | 0.262 | 0.320 |
| 4 | 0.147 | 0.163 | 0.309 |
| 8 | **0.081** | **0.097** | **0.141** |
| 12 | **0.043** | **0.052** | **0.088** |

At K=8 the encounter field is already substantially more stable than the primary amplitude-based stochasticity descriptor.

This suggests that the stochastic object most justified by R0 is **not a full concentration path density**, but the source-conditioned structure of intermittent encounters / support occupancy.

---

## 6. Split profile reproducibility

First-8 versus last-8 empirical profiles:

### Full 10×30 binary encounter-probability field

Across the 18 sources:

- median cosine ~0.988;
- median relative profile discrepancy ~0.161.

### Time-only encounter profile

- median cosine ~0.998;
- median relative discrepancy ~0.068.

### Probe-only encounter profile

- median cosine ~0.997;
- median relative discrepancy ~0.085.

### Mean concentration trajectory

Its direction is also highly reproducible, but absolute magnitude shows larger split variability.

Thus binary encounter structure is not simply a noisy surrogate for ppm magnitude; it is a particularly stable component of the observation process.

---

## 7. Exploratory source-identity diagnostic — NOT a confirmation gate

This analysis was performed after R0 PASS only to determine which object deserves theory search.

It is **not** a new mainline result and it uses only the 18 calibration sources.

Protocol:

- use 8 realizations/source to estimate a 10×30 Bernoulli encounter-probability field;
- score each held-out single realization under all 18 source-specific Bernoulli fields;
- swap train/test halves and repeat.

Results:

### first8 -> last8

Bernoulli encounter likelihood:
- top-1 source = **90.3%**
- top-3 = **99.3%**

Raw mean-path SSE:
- top-1 = 88.2%
- top-3 = 97.9%

### last8 -> first8

Bernoulli encounter likelihood:
- top-1 = **89.6%**
- top-3 = **100%**

Raw mean-path SSE:
- top-1 = 81.9%
- top-3 = 97.2%

Interpretation:

> source-conditioned encounter/support structure carries strong single-realization source identity on the R0 calibration panel.

This is encouraging but cannot be used as the paper innovation because:
- only 18 source candidates are involved;
- the analysis is post-R0 exploratory;
- simple encounter likelihood has prior art in olfactory search.

---

## 8. Prior-art boundary

The next mainline must not claim:

“first use of encounter probability for turbulent olfactory search.”

2025 Physical Review Fluids work by Heinonen et al. already extracts spatially dependent odor-encounter statistics from realistic turbulent DNS and uses them to construct Bayesian olfactory-search policies.

Therefore a Bernoulli encounter map alone is **not** a defensible main innovation.

The R0 result should instead be used to search for a higher-level far-domain theory that explains:

1. why intermittent support is a more reproducible observable than exact concentration amplitude;
2. how source identity should be represented when fine source cells are stochastically indistinguishable;
3. how the appropriate source scale can emerge from observation statistics rather than be fixed ad hoc.

---

## 9. Mainline scientific conclusion after R0

The project should now stop asking:

> Which full stochastic plume distribution should we fit?

The R0-supported question is narrower and better identified:

> Which source-conditioned **encounter/intermittency structures** are reproducibly identifiable across plume realizations, and at what spatial source scale do they carry unique source information?

This simultaneously addresses:

- the stochastic-realization problem;
- the exact-cell versus local-basin problem;
- the need to preserve a PMFS-style source probability representation.

---

## 10. Authorized next activity

Do not return to PASI.

Do not yet run PMFS closed loop.

The next activity should have two parts:

### Theory search

Search far-domain 2025/2026 theory for:
- event/point-process representations of intermittent stochastic systems;
- first-passage / renewal / survival structure;
- multiscale identifiability / coarse-graining;
- information-theoretic emergence of observable macrostates.

### New offline gate

The next actual source-ranking gate must again use at least >=143 arbitrary candidate source hypotheses.

Because R0 shows encounter fields converge much faster than full path variance, a multi-realization candidate bank can be designed around encounter statistics rather than full concentration covariance.

The exact theory and gate should be frozen only after novelty/prior-art review.


---

# INCLUDED FILE: CODEX_R0_STOCHASTIC_BENCHMARK_HANDOFF_20260924.md

# CODEX HANDOFF — R0 Stochastic Benchmark Refoundation

Date: 2026-09-24

Branch:
`research/stochastic-benchmark-refoundation-20260924`

Mission:
execute the frozen 18-source × 16-realization stochastic benchmark calibration.

This is **not** a PASI rescue and not a new localization algorithm.

## 1. Checkout

```bash
cd /path/to/uav-gsl-isj
git fetch origin
git checkout research/stochastic-benchmark-refoundation-20260924
git pull --ff-only
git status --short
git rev-parse HEAD
```

Require a clean worktree before execution.

## 2. Read before running

Read:

`research/stochastic_benchmark_refoundation/R0_PROTOCOL_FREEZE_20260924.md`

Do not alter:

- 18-source panel;
- 288 seed matrix;
- House02/W2;
- GADEN settings;
- probe operator;
- 10 times;
- 16 realizations/source;
- metrics;
- PASS/HOLD/STOP thresholds.

No neural model.
No source-localization score.
No PASI rerun.
No PMFS closed loop.

## 3. Syntax checks

```bash
python3 -m py_compile   research/stochastic_benchmark_refoundation/select_r0_panel.py   research/stochastic_benchmark_refoundation/pool_r0_cube.py   research/stochastic_benchmark_refoundation/analyze_r0_stability.py

bash -n research/stochastic_benchmark_refoundation/run_r0_multi_realization_vm.sh
bash -n research/stochastic_benchmark_refoundation/package_r0_review.sh
```

## 4. Execute

```bash
bash research/stochastic_benchmark_refoundation/run_r0_multi_realization_vm.sh
```

The runner must:

1. verify exact simulator/wind/occupancy/extractor contracts;
2. reproduce and verify the frozen 18-source panel;
3. verify 288 unique seeds;
4. generate exactly 16 new realizations per source;
5. preserve full 10×83×119 concentration cubes on VM;
6. create compact 10×30 pooled arrays;
7. compute R0 statistics;
8. produce exactly one frozen decision:
   - `R0_PASS_STOCHASTIC_BENCHMARK_USABLE`
   - `R0_HOLD_MORE_REALIZATIONS_REQUIRED`
   - `R0_STOP_PER_SOURCE_DISTRIBUTION_MAINLINE_UNSTABLE`

The analysis may exit:
- 0 = PASS
- 10 = HOLD
- 20 = STOP
- 30 = infrastructure/incomplete data stop

These are scientific/contract exits, not reasons to edit thresholds.

## 5. No post-result changes

After seeing R0:

Do not:
- change source panel;
- remove “bad” seeds;
- alter K;
- relax Spearman/convergence thresholds;
- choose another stochastic descriptor to convert HOLD/STOP into PASS.

If an infrastructure-only repair is unavoidable, commit it separately before scientific result generation and report it.

## 6. Commit result

After execution:

```bash
git add evidence/stochastic_benchmark_refoundation/r0/
git status --short
git commit -m "evidence: record R0 multi-realization stochastic benchmark"
git push origin research/stochastic-benchmark-refoundation-20260924
```

Do not modify frozen protocol/code after result generation.

## 7. Package for independent review

```bash
bash research/stochastic_benchmark_refoundation/package_r0_review.sh
```

Upload:

`/home/zyc/R0_STOCHASTIC_BENCHMARK_REVIEW_20260924.tar.gz`

The package intentionally contains all 288 compact pooled arrays plus manifests, but not hundreds of full concentration cubes. Full-cube hashes remain in the evidence inventory.

## 8. Report back only

1. branch;
2. final commit SHA;
3. R0 decision;
4. minimum split variability Spearman;
5. first8-vs-last8 variability Spearman;
6. odd8-vs-even8 variability Spearman;
7. minimum variability-tertile agreement;
8. K8→K16 median / q75 relative change;
9. K12→K16 median / q75 relative change;
10. legacy C/D vs R0-16 variability Spearman;
11. package path;
12. package bytes;
13. package SHA256;
14. any infrastructure-only patch.

Then stop. Do not start a new theory or closed loop.


---

# INCLUDED FILE: 01_idea/PATH_ACTION_SOURCE_INFERENCE_FREEZE_20260924.md

# Candidate Mainline — Source-Conditioned Stochastic Path Action

Date: 2026-09-24  
Branch: `research/path-action-source-inference-v0`

Status: **EXPLORATORY SIGNAL FROZEN — FRESH S3 CONFIRMATION REQUIRED**

## 1. Failure inherited from the stopped MZ route

D3 falsified the global mass-normalization assumption.

Across the 630-source bank, independent prediction-realization variability is source-conditioned and heteroscedastic:

- relative C/D discrepancy range: ~1.5% to 57.5%;
- median: ~15.3%;
- Spearman correlation between relative variability and mean plume mass: ~-0.50;
- S1: low-variability regime (~7.9%);
- S2: more stochastic regime (~18.0%).

Therefore one observable component can be source-discriminative in one region and realization-dominated in another.

The new problem is:

> Compare source hypotheses under source-conditioned stochastic path distributions without globally deleting amplitude, morphology, or memory information.

## 2. Far-domain mother theory

The candidate mother idea is the **path-action / large-deviation viewpoint of nonequilibrium statistical physics**, especially Onsager–Machlup-type path probabilities.

The key conceptual shift is:

- deterministic fitting asks how close an observed trajectory is to a single mean path;
- path-action inference asks how probable the **entire observed path** is under each candidate stochastic process.

For heteroscedastic stochastic dynamics, deviation in a low-noise direction should be penalized strongly, while the same numerical deviation in a high-noise direction should be penalized weakly.

Recent relevant theory directions include:

- 2026 goal-oriented learning of stochastic differential equations using error bounds on path-space observables (Zou, Lie, Marzouk; arXiv:2603.20467);
- 2026 Onsager–Machlup work for stochastic transition paths / early warning;
- classical Onsager–Machlup / Freidlin–Wentzell / large-deviation action theory.

Prior-art boundary: parameter inference with Onsager–Machlup ideas exists outside GSL. The candidate novelty, if it survives fresh validation, is a **source-position-indexed stochastic path action used directly as the PMFS source likelihood**.

## 3. Frozen exploratory proxy

For each candidate source (s), the existing two independent prediction realizations C/D define

[
\mu_{s,k}=\frac{x^C_{s,k}+x^D_{s,k}}{2},
]

[
v^{local}_{s,k}=\frac{(x^C_{s,k}-x^D_{s,k})^2}{2}.
]

A source-independent unresolved-noise floor is computed before looking at a target:

[
\bar v_k = \frac{1}{N}\sum_s v^{local}_{s,k}.
]

The frozen variance used for the first confirmation gate is

[
v_{s,k}=v^{local}_{s,k}+\bar v_k.
]

No mass normalization is applied.

For observed raw concentration path (y), define the discrete heteroscedastic path-action proxy

[
A(s;y)=\sum_k
\left[
\frac{(y_k-\mu_{s,k})^2}{v_{s,k}+10^{-12}}
+
\log(v_{s,k}+10^{-12})
\right].
]

This is a diagonal Gaussian path-action / negative-log-likelihood proxy. It is **not yet claimed as the final Onsager–Machlup functional**.

## 4. Exploratory-only result on already-seen S1/S2 targets

Because the formula was discovered after inspecting S1/S2 failures, these targets are discovery data only.

Nevertheless, as an exploratory sanity check:

- S1_A: rank 1;
- S1_B: rank 1;
- S2_A: rank 1;
- S2_B: rank 1.

The result remains 1/1/1/1 when the global noise-floor multiplier is varied from 0.05 through 4.0. The confirmation formula is frozen at multiplier 1.0 because it is the unmodified additive local+global variance definition.

This robustness sweep is not confirmatory evidence.

## 5. Fresh S3 source selection — target blind

S3 is selected before generating any new target.

Selection rule:

1. exclude candidates within 2.0 m of S1 or S2;
2. compute for every candidate:
   - relative C/D discrepancy;
   - log mean path mass;
3. compute the global medians and median absolute deviations of those two quantities;
4. select the eligible candidate minimizing squared robust standardized distance to both medians.

This chooses a typical stochastic regime rather than an extreme/easy case.

Frozen result:

- source id: `pmfs_3_12`;
- xyz: `(-4.34273, -3.70088, 0.20)`;
- prediction C/D relative discrepancy: ~0.15391;
- global median discrepancy: ~0.15269;
- distance to S1: ~2.58 m;
- distance to S2: 6.60 m.

## 6. Fresh target seeds

Generate exactly two new independent W2 targets:

- S3_W2_E: seed `2026092403`;
- S3_W2_F: seed `2026092404`.

Prediction bank remains unchanged:

- C = 2026092401;
- D = 2026092402.

No target from S1 or S2 may be used to alter the formula after this freeze.

## 7. Frozen controls

For each target report:

1. raw exact-forward SSE rank;
2. homoscedastic Gaussian path score rank;
3. heteroscedastic residual-only rank (same variance, omit log variance);
4. full frozen path-action rank.

## 8. Fresh confirmation gate

PASS requires both E and F:

- full path-action truth rank <= 3;
- full path-action rank sum <= raw rank sum;
- full path-action rank sum <= homoscedastic rank sum;
- full path-action rank sum < heteroscedastic-residual-only rank sum OR full path-action is rank 1 on both targets.

PASS:

`PASI_D0_PASS_FRESH_S3_PATH_ACTION_SIGNAL`

Any failure:

`PASI_D0_FAIL_STOP_PATH_ACTION_MAINLINE`

No rescue or coefficient tuning after target ranks are observed.

## 9. Scope

Even a PASS establishes only a fresh offline mechanism signal in House02/W2.

Before any PMFS closed loop, the route must still survive:

- another source / different stochastic regime;
- cross-House or cross-wind evidence;
- a practical online approximation that does not require full exact-GADEN ensembles per candidate.


---

# INCLUDED FILE: 01_idea/MZ_NONMARKOVIAN_SOURCE_INFERENCE_THEORY_FREEZE_20260924.md

# Main-Innovation Theory Freeze — Mori–Zwanzig Non-Markovian Source Inference

Date: 2026-09-24  
Branch: `research/realization-invariant-source-signature-v0`

Status: **CANDIDATE MAIN INNOVATION — D3 PENDING**

## 1. Scientific failure that motivates the new mainline

The previous exact source-to-sensor Green-family gate failed under independent stochastic plume realization:

- S2_W2_A truth rank: 1;
- S2_W2_B truth rank: 7.

The failure was local rather than global: the highest-ranked wrong candidates remained near the true source. This showed that deterministic source-to-sensor transport carries source-basin information but is not realization-robust at 0.30 m support-cell resolution.

The main scientific problem is therefore not merely forward-model accuracy:

> How can source identity remain inferable when the unresolved stochastic plume realization changes?

## 2. Far-domain mother theory

### 2.1 Mori–Zwanzig projection

The mother principle is Mori–Zwanzig model reduction:

A high-dimensional dynamical system is projected onto a reduced set of resolved observables. The eliminated degrees of freedom do not disappear; after projection they appear as:

1. resolved / instantaneous dynamics;
2. history-dependent memory;
3. orthogonal unresolved fluctuation / noise.

The research thesis is that PMFS-style gas-source inference should not treat stochastic plume observations as conditionally independent instantaneous evidence when the unresolved plume degrees of freedom induce finite temporal memory.

### 2.2 2026 turbulence anchor

X. M. de Wit et al.,
**Data-driven Mori–Zwanzig modeling of Lagrangian particle dynamics in turbulent flows**,
Proceedings of the National Academy of Sciences 123(13), e2525390123 (2026).
DOI: `10.1073/pnas.2525390123`.

This is the closest far-domain physical anchor. It applies Mori–Zwanzig to Lagrangian turbulence, where reduced particle trajectories lack access to the full turbulent field, and learns a history-dependent reduced dynamical system that is point-wise useful at short times and statistically stable at long times.

### 2.3 2025 biomolecular anchor

B. Liu et al.,
**Memory kernel minimization-based neural networks for discovering slow collective variables of biomolecular dynamics**,
Nature Computational Science 5, 562–571 (2025).
DOI: `10.1038/s43588-025-00815-8`.

MEMnets is built on integrative generalized master equation theory. It identifies collective variables by minimizing an upper bound on the time-integrated memory kernel rather than assuming Markovian reduced dynamics.

Reference implementation:
`https://github.com/xuhuihuang/memnets`

The code is a theory/reference parent, not a package to copy directly into GSL.

## 3. Our second-order innovation

A direct transplant of MEMnets or a generic autoregressive model is not the innovation.

The proposed GSL-specific second-order idea is:

> **Mori–Zwanzig non-Markovian source inference:** project the stochastic gas observation history into a realization-robust source-conditioned observation coordinate, represent unresolved plume fluctuations through finite temporal memory, and use the resulting history-dependent likelihood to update a PMFS-style source probability map.

The hidden source position is a fixed cause, not a slow dynamical state. Therefore our problem differs fundamentally from molecular CV discovery and from turbulent trajectory forecasting.

The source hypothesis enters the inverse likelihood, while the unresolved plume realization enters the memory/noise model.

## 4. Data-derived projection discovered before model training

The D0 data-only probe showed that absolute plume mass is strongly realization dependent.

Frozen projection at each observation time:

[
p_t(i)=\frac{c_t(i)}{\sum_j c_t(j)}
]

with the zero vector retained when total observed mass is zero.

This converts each time slice from absolute ppm into a spatial mass-fraction observation.

It is not claimed as the main innovation.

Its role is nuisance removal / resolved-coordinate construction.

Empirical evidence:

- raw exact-forward A/B rank: 1 / 7;
- temporal mean: 1 / 5;
- global normalization controls: no robust improvement;
- per-time mass-fraction then time aggregation: 2 / 3.

Same-source target A/B discrepancy:

- raw cosine ~0.9774;
- projected cosine ~0.9952;
- raw relative L2 ~21.2%;
- projected relative L2 ~10.1%.

## 5. D1 memory evidence

Using the frozen 630 arbitrary-source bank, temporal stochastic covariance was estimated only from independent prediction realization differences C-D.

Truth ranks:

| temporal model | A | B |
|---|---:|---:|
| identity / no memory | 2 | 8 |
| diagonal variance only | 1 | 7 |
| full off-diagonal temporal memory | **1** | **2** |

The full-memory result remains 1/2 when estimated from:

- all candidates;
- even-index candidates only;
- odd-index candidates only;
- all candidates except the true source.

Measured mean residual temporal correlation:

- lag 1 ~0.580;
- lag 2 ~0.478;
- lag 3 ~0.376;
- lag 4 ~0.297;
- lag 5 ~0.216;
- lag 6 ~0.133;
- lag 7 ~0.055;
- lag 8 and later approximately zero.

This supports finite memory rather than independent white realization noise.

## 6. D2 sequential finite-memory likelihood

The memory horizon is selected without looking at target A/B ranks:

> retain positive lags preceding the first non-positive mean temporal correlation of C-D realization differences.

Frozen all-source estimate:

- first non-positive lag: 8;
- retained memory horizon: 7.

Rank curve:

| memory horizon | A | B |
|---:|---:|---:|
| 0 | 1 | 7 |
| 1 | 1 | 4 |
| 2 | 1 | 5 |
| 3 | 1 | 3 |
| 4 | 1 | 2 |
| 5–9 | 1 | 2 |

The automatically selected horizon 7 gives A/B = **1/2**.

Split estimates and truth-excluded estimation also give 1/2.

Decision:

`D2_ADVANCE_FINITE_MEMORY_SOURCE_LIKELIHOOD`

## 7. Prior-art boundary

Do NOT claim novelty for:

- Langevin plume models;
- generalized Langevin equations for gas dispersion;
- temporal filtering;
- autoregressive concentration prediction;
- MEMnets itself;
- generic non-Markovian modeling;
- simply using concentration history.

Lagrangian stochastic / generalized-Langevin-type dispersion modeling already exists in atmospheric/gas transport.

The only defensible candidate claim, if D3 and later cross-environment gates survive, is the inverse-localization construction:

> source-conditioned PMFS likelihood under a Mori–Zwanzig-style projection in which unresolved stochastic plume degrees of freedom induce explicit finite memory.

## 8. D3 falsification is load-bearing

D3 tests a second true source S1 at the same House02/W2 condition.

Truth:
- source id `pmfs_10_17`;
- xyz `(-2.242730141, -2.200880051, 0.20)`.

Only two new target realizations are required. The frozen 630-source C/D prediction bank is reused.

No result-driven tuning is permitted.

D3 PASS requires both new target realizations to have memory rank <=3 and the memory model to dominate/preserve the pre-frozen raw, D0-static, and diagonal controls according to `CODEX_D3_S1_W2_HANDOFF_20260924.md`.

D3 failure freezes:

`D3_FAIL_STOP_MZ_SOURCE_INFERENCE_MAINLINE`

D3 pass freezes only:

`D3_PASS_SECOND_SOURCE_MEMORY_GENERALIZES`

A D3 pass is still not sufficient for the final main innovation. Cross-House / cross-environment evidence is mandatory before closed-loop authorization.

## 9. Working three-module architecture if the mainline survives

This is a hypothesis architecture only; auxiliary modules are not yet frozen.

**Main innovation:** Mori–Zwanzig non-Markovian source likelihood.

**Auxiliary candidate A:** realization-robust source projection / plume-mass nuisance removal.

**Auxiliary candidate B:** memory-aware observation/action policy, to be selected only after the main offline source-inference mechanism survives cross-environment testing.

The final representation remains a PMFS-style source probability map.

## 10. Current action

Do not broaden literature search and do not develop auxiliary modules now.

The only authorized next scientific result is D3 S1-W2 second-source falsification.
