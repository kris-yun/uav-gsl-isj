# Multi-expert mainline review after repeated route failures

Date: 2026-09-23
Branch: `research/cross-domain-mother-idea-audits-20260923`

Status: **DISCUSSION / ROUTE SELECTION ONLY — NO METHOD NAME, NO V1, NO PROMOTION**

## 1. Why this review was needed

Several routes produced attractive endpoint improvements but failed when the scientific mechanism was tested harder:

- HCMC: strong old-discovery endpoint; true independent-plume NO-GO and definability failure.
- HCCE: strong old+new endpoint and destructive controls; failed source × transport identity (2/12) while a trivial encounter-rate comparator achieved 10/12.
- HCTLA: current independent accepted package lacks the required multiple source updates.
- HCDG / ACIA / IDG: insufficient null or intervention separation.
- Mori-Zwanzig direct proxy: history features did not produce source-specific memory benefit.
- time-irreversibility / local arrow-of-time route: repeated partial tests did not establish that time direction itself is load-bearing; this route is now **closed** and should not be retried by changing lags/bins.
- direct large-deviation/SCGF proxy on CStar: cross-transport source identity was 10/12, but hit-rate-preserving temporal shuffles matched/exceeded it too often (9%–43.5%, depending on block size); **closed as a direct mainline**.
- delay/Koopman fingerprint proxy: best source identity 8/12 and weak shuffle separation; **closed as a direct mainline**.

The objective here is to reason from the physics and available information before selecting another mother idea.

---

# 2. Expert-role deliberation

## A. Turbulent-transport / fluid-mechanics view

Key correction:

Within one PMFS source update, **all source candidates share the same occupancy geometry and the same fixed estimated 2D wind grid**. The candidate source location changes the injection point; it does not define a different transport law.

Therefore the naive statement

> “each source has its own transfer operator”

is wrong for the current PMFS model.

The correct decomposition is closer to

[
ho_t^{(s)} = mathcal P^t b_s
]

or, for repeated emission,

[
ho_t^{(s)} = sum_{	au=0}^{t}mathcal P^{t-	au} b_s,
]

where:
- (mathcal P) is the common transport dynamics induced by estimated wind + geometry;
- (b_s) is the source-dependent injection.

Consequence:
**do not promote Perron–Frobenius operator matching as source-specific operator matching.**
Use transfer-operator theory only as the common transport backbone.

## B. Statistical-physics / stochastic-process view

The offline replay now gives exactly the type of object that static hitMap aggregation destroyed:

- filament trajectories;
- cell transitions;
- candidate-internal transport age;
- per-step occupancy.

The candidate-internal clock is **not real robot time**. That makes many ordinary temporal-alignment ideas invalid.

But it has a physically meaningful interpretation:

> elapsed transport age after emission from a candidate source.

That naturally points to **first-passage / hitting / transition-path statistics**:

- probability of ever reaching a cell/region;
- distribution of first-arrival age;
- mean first-passage time;
- residence / reactive flux;
- committor-like probability of reaching an observed region before escape.

These objects do not require pretending that internal step 37 corresponds to robot time (t+7.4,s).

## C. Control / observability view

Source localization is an inverse problem for the injection (b_s), not for the common transport operator.

The equivalent control-theoretic question is:

> which possible injection is observable from the cells/regions the robot has sampled?

First-passage / reactive-flux statistics have a direct relation to backward reachability and observability of the source through transport.

This suggests an early mechanism test:
- do true-source-near injections produce distinct source-to-observation reachability / passage profiles?
- are those profiles more source-specific than the final time-averaged occupancy map?

If not, no localization method should be built.

## D. Robotics / causal-deployability view

The route is deployable in principle because it can use:
- PMFS occupancy map;
- PMFS estimated 2D wind grid;
- source hypotheses;
- the same candidate forward model.

It does **not** require:
- future wind;
- future gas;
- GADEN oracle full field;
- future robot trajectory.

The deterministic post-run replay is a research instrument. A later online implementation could compute compact passage summaries internally without writing files, but only after scientific validation.

## E. Generalization / intervention view

The HCMC/HCCE failures mean a single-case positive result is insufficient.

A candidate passage statistic must eventually satisfy:

1. source-specific on the H01 replay mechanism pre-screen;
2. positive on old + independent stochastic-plume development cases after replay expansion;
3. source identity under CStar source × transport intervention;
4. not explained by static hit probability, encounter rate, source-to-origin geometry or leaf size.

## F. Reviewer / novelty view

The mother science is genuinely external to GSL:
- transition-path theory;
- committor functions;
- first-passage transport;
- reactive flux.

Targeted scite search did not identify a direct GSL/OSL method using candidate-wise committor / first-passage / reactive-flux structure for source posterior construction. Search noise contains biological olfaction and unrelated first-passage uses, so this is **not yet an exhaustive novelty proof**.

Do not claim “first use of first-passage ideas in olfaction”.
A future precise novelty claim would need to be much narrower.

---

# 3. Current mother-theory shortlist after the meeting

## Highest priority for the next kill test: transition-path / first-passage transport

Why:
- directly matches source-as-injection physics;
- uses the newly recovered dynamic information;
- avoids invalid real-time synchronization;
- naturally separates common transport dynamics from source-specific injection;
- can be tested before a localization posterior is built.

Recent external anchors:
- 2025 SIAM J. Applied Mathematics, **Mean First Passage Times for Transport Equations**, DOI `10.1137/24M1647667`.
- 2026 J. Chemical Physics, **A continuous-space analytical framework for committor functions from molecular dynamics**, DOI `10.1063/5.0337005`.
- 2026 **Reactive Flux Matching: Mechanism Discovery and Adaptive Sampling of Rare Events**, arXiv `2606.06295`.
- 2025 JFM, **Transport and mixing in control volumes through the lens of probability**, DOI `10.1017/jfm.2025.10631`.

Useful public code ecosystems:
- `deeptime-ml/deeptime` (Markov models / transition-path analysis);
- `LuzieH/pytpt`;
- other public TPT implementations exist, but code is a reference rather than a reason to promote the route.

## Secondary: common transfer operator / Markov transport

Retain only as the mathematical backbone used to estimate transport between cells.
Do not treat the operator itself as source-specific.

## Deferred: fluctuation-response

Scientifically strong, but frozen accepted artifacts lack historical time-varying PMFS estimated-wind grids. Requires prospectively logged causal perturbation/response data.

## Deferred: resolvent forcing-response

Conceptually attractive because source is a forcing and plume is a response. However a clean frequency/time-resolved response experiment needs a better controlled dynamic observation contract than the current single estimated-wind snapshot.

## Closed for now

- time irreversibility / arrow-of-time route;
- direct SCGF / large-deviation feature route;
- direct Koopman fingerprint/conjugacy proxy;
- static invariant-feature families already audited.

Do not reopen these by changing lag/bin/window hyperparameters unless genuinely new data changes the scientific question.

---

# 4. First-passage route: necessary phenomenon before any method exists

No method name is allowed yet.

For candidate source (s), replay provides many particles/filaments emitted from (s).
For every free cell or observed region (x), define source-conditioned passage objects such as:

[
P_s(	au_x < infty),
]

[
F_s(x,t)=P_s(	au_xle t),
]

and, when defined,

[
E_s[	au_xmid	au_x<infty].
]

The first kill test is not localization error.

### Necessary mechanism A — incremental temporal value

Using the same candidate simulations:

- baseline: final time-averaged occupancy / hit probability only;
- dynamic: first-arrival / passage-age summaries.

The dynamic passage representation must improve direct truth-candidate identity **beyond the static occupancy representation**.

If it does not, the recovered dynamics add no source information and the route is killed.

### Necessary mechanism B — time-order destruction

Construct a control that preserves:
- each candidate's final per-cell occupancy count;
- candidate geometry;
- source point;
- static hitMap.

but destroys internal first-arrival order / transport age.

If the proposed passage signal survives this control, it is only a repackaging of the static hitMap and is killed.

### Necessary mechanism C — truth-distance monotonicity

On the H01 replay pre-screen:
- candidate passage score should correlate with source distance / truth-leaf membership;
- nearest-truth candidate percentile must be reported;
- no top-5% endpoint is needed at this stage.

### Necessary mechanism D — definability

Constant or near-constant measured hit fields must not make the candidate passage representation mathematically undefined.
If observation evidence is insufficient, the result must become broad/abstaining rather than zero posterior mass.

---

# 5. Data request for the existing H01 replay

The current release already contains all necessary raw dynamics, but for lightweight analysis a derived source-blind table is preferable.

For every candidate × free cell, derive offline:

- ever_hit (0/1);
- first_hit_internal_step;
- last_hit_internal_step;
- number_of_internal_steps_hit;
- number_of_distinct_arrival_episodes if well-defined;
- first-arrival quantiles across individual filaments if filament-level IDs allow it.

No truth is needed to create this table.

Then join only after freezing it with:
- measured hit probability;
- measured confidence;
- candidate source coordinate;
- truth coordinate for evaluation only.

This derived table should be generated from the already verified replay, not from a new live PMFS run.

---

# 6. Decision

The panel does **not** declare a new main innovation.

It declares one next scientific audit:

> **Does source-conditioned transport age / first-passage structure contain source identity that is absent from the final time-averaged occupancy map?**

Only if the answer is yes across the required intervention/generalization gates should a localization construction or method name be created.
