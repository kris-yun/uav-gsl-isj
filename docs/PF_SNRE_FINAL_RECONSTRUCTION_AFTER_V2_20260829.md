# PF-SNRE final reconstruction after Direct Set-NRE V2

Date: 2026-08-29
Branch: `research/pf-sbi-final-one-shot-20260829`
Status: FINAL METHOD RECONSTRUCTION BEFORE ONE-SHOT QUALIFICATION / CLOSED-LOOP PIPELINE

## 1. Frozen evidence and what it does / does not prove

Direct Set-NRE V2 remains formally `PF_DEI_DIRECT_SET_NRE_V2_NO_GO` under its preregistered H01 gate. Do not relabel that experiment after seeing outcomes.

Frozen H01 historical trajectories 0..9 x updates1..5:

- PMFS mean posterior-centroid error: 4.899306 m;
- V2 mean posterior-centroid error: 3.562315 m;
- relative improvement vs PMFS: 27.29%;
- all five update-index means improve;
- true-source carrier mass rank improves in 50/50 cases;
- posterior carrier-mass median normalized rank = 0.267943;
- posterior carrier-mass Top10 = 3/50;
- preregistered rank/Top10 gates failed.

This is strong development evidence, not a paper-level or closed-loop claim.

## 2. New independent reconstruction from the frozen V2 package

The following diagnostics were computed after V2 freeze and must therefore be treated as explanatory development analysis only, never retroactive validation.

### 2.1 Geometry-only prior centroid is a mandatory baseline

For H01, the area/free-cell geometry prior q0 has posterior-mean location error approximately 3.1283 m for the fixed historical true source. Therefore V2 (3.5623 m) is worse than q0 under this one-source posterior-mean metric, although it is much better than Classic PMFS.

Consequence: PMFS-vs-V2 expected-location improvement alone can be inflated when Classic PMFS is confidently wrong and the no-data map centroid happens to lie nearer the fixed true source. Every future source-localization evaluation must include both `PMFS` and `q0-only` spatial baselines and must vary true source location.

### 2.2 V2 nevertheless contains genuine source-dependent information

V2 is not merely q0 regression. In the frozen 50 cases:

- q0 true carrier mass rank is about 201/210 because the true carrier has one free cell while many carriers have 4;
- V2 posterior-mass median true rank is about 57/210;
- ranking the likelihood factor / posterior density per free-cell area (equivalently the NRE logit for uniform source proposal) gives median true rank about 35.5/210 and Top10 8/50;
- average V2 posterior mass within ~1.5 m of the true carrier is about 12%, versus about 6.2% for q0 and far below that for the frozen Classic PMFS posterior.

Thus the network learned source evidence, but the H01 historical case does not show exact-carrier identifiability.

### 2.3 Posterior mass rank and source-density rank are different objects

The region prior is

`q0(s) proportional to A_s`,

where `A_s` is free-cell area/count in carrier s. With learned likelihood ratio `r_s(D)`:

`q(s|D) proportional to A_s * r_s(D)`.

Carrier posterior **mass** therefore favors large carriers by design. The posterior density per unit source area is

`rho(s|D) = q(s|D) / A_s proportional to r_s(D)`.

Therefore exact-carrier posterior-mass TopK is not a pure identifiability measure when carrier areas differ. It mixes evidence with region size. Future diagnostics must separate:

1. `density/evidence rank`: rank `r_s(D)` or `q(s|D)/A_s`;
2. `posterior mass`: used for Bayesian spatial decisions and grid mapping;
3. `point localization loss`: distance of the declared source estimator to truth.

The V2 preregistered NO-GO remains valid because its gate was carrier-mass TopK. This reconstruction only changes the definition of future confirmatory metrics, before any new House outcomes are viewed.

## 3. Final scientific target

Stop treating the task as 210-way exact-carrier classification.

The inferential target is a **spatial source posterior field** over region-valued source support. The point estimate used for squared-distance localization is the posterior mean of carrier/free-cell coordinates; posterior mass and uncertainty remain available to the planner.

The final method family is:

**PF-SNRE — Physics-Factorized Set Neural Ratio Estimation**

Chinese: **物理因子化集合神经比率推断**.

Core generative factorization:

`(S,U,Z,Q) -> C_1:T -> R_1:T -> M_1:T`

with persistent 2D source carrier `S`, unresolved 3D placement `U`, stochastic transport realization `Z`, source strength `Q` (currently controlled/frozen in the benchmark), physical concentration `C`, persistent sensor state `R`, and measured ppm `M`.

The inferential network does not discover causality. The causal/physical content is in the closed simulator factorization. The network amortizes likelihood-ratio inference on top of that generator.

## 4. Final neural architecture: freeze V2, do not invent V3

No new TCN, Transformer, recurrent network, TrajCast, temporal-order module, score temperature, A0, PMFS blend coefficient, or outcome-selected hyperparameter is authorized.

Use the Direct Set-NRE V2 architecture and training semantics:

- source proposal independent and uniform over legal carriers within each simulated environment;
- negative candidate independent from the same proposal;
- strict nuisance leave-one-member-out pseudo-observation during training;
- nuisance members are an exchangeable set;
- visible sensing blocks are aggregated as a set; no member identity is propagated through time;
- no PMFS posterior enters network inputs or the sampler;
- final posterior is `q(s|D) proportional to q0(s) * exp(f_theta(s,D))`.

External method lineage for the network module: **CIGaRS I, Nature Astronomy 2026**, specifically set-based neural ratio estimation with conditioned Deep Set++ / SetNorm. This is the single external lineage for the learned set-NRE module. Do not mix TrajCast/PULSE/TCN into the novelty story.

## 5. Module boundaries for paper ablation

### B0 — Physics-closed generator (foundation, not an optional novelty switch)

Region-valued source support, legal 3D placements, stochastic GADEN transport, concentration, persistent sensor forward operator, measured ppm.

### M1 — Nuisance predictive-set representation

Preserve the finite distribution over unresolved placement/transport members rather than collapsing to one mean field.

### M2 — Conditioned Deep Set++ feature inference

Permutation-invariant member aggregation and visible-block aggregation with SetNorm/moment preservation.

### M3 — Neural ratio head

Balanced joint-vs-product NRE learns a likelihood-ratio factor rather than a hand-designed energy/CRPS score.

### A0 — Geometry-prior / region-to-grid adapter

Apply q0 carrier mass and distribute carrier posterior mass over its free cells. This is an inference adapter, not a headline innovation.

Ablation identities must be frozen before final outcomes:

- `ABLATE_NUISANCE_SET`: replace member set by its predictive mean while retaining the rest of the network interface;
- `ABLATE_LEARNED_RATIO`: replace M2+M3 by the already-frozen nonlearned comparator (CRPS or trajectory-energy baseline; no new score design);
- `ABLATE_PHYSICS_INPUT`: remove/permute candidate predictive ppm while retaining observation, candidate geometry and trajectory context, to prove the gain is physics-conditioned rather than a path/location shortcut;
- `ABLATE_Q0`: uniform carrier mass, diagnostic only, not a main contribution ablation.

M3/M4 from the earlier trajectory-coherence/adjacent-increment design are retired and must not be resurrected.

## 6. Why no further H01 model tuning is allowed

H01 has now influenced:

- the failure diagnosis;
- the V2 proposal correction;
- recognition of the mass-vs-density metric mismatch;
- recognition that q0-only is a mandatory spatial baseline.

Therefore H01 is development data. The V2 architecture, source proposal, hidden width, optimizer family, learning rate, step budget, transforms and block semantics are frozen. No H01-driven architecture or hyperparameter change is allowed from this point.

## 7. What must be proved before closed loop

A single future qualification must answer all of the following together, using existing physical banks before any new expensive simulation:

1. **Spatial-source sweep:** does PF-SNRE beat q0-only and fixed scores across many true carrier locations, not just the single historical H01 source?
2. **Cross-environment generalization:** does one architecture trained without the test House improve H01/H02/H03 held-out-House inference?
3. **Calibration / false confidence:** on simulated held-out source/member realizations, is the spatial posterior at least conservatively calibrated and free of new false-confident collapses?
4. **Physics dependence:** do no-physics and no-nuisance-set ablations remove the signal?
5. **Runtime deployability:** can the frozen model consume a trajectory-independent predictive provider and update within the PMFS source-update interval without House-specific neural retraining?

Only if these pass may the same one-shot contract continue to shadow and paired OFF/ON closed-loop.

## 8. Final metrics — do not reuse the old carrier-mass TopK gate as primary

Primary task metric:

- distance of the declared posterior spatial estimator to the true source (use the exact evaluator contract used for the paper/closed loop; posterior mean if that is the declared estimator).

Mandatory spatial baselines:

- Classic PMFS;
- geometry-only q0;
- frozen nonlearned physics score.

Mandatory inference diagnostics:

- likelihood/density true-source rank (`f_theta` or posterior mass divided by carrier free area);
- posterior mass within physical radii (e.g. 1 m, 2 m) when supported by map resolution;
- posterior entropy/max mass and false-confidence events;
- simulation-based calibration / credible-set coverage on source-sweep pseudo-observations;
- posterior-mass TopK only as a secondary region-resolution diagnostic.

## 9. Deployment contract

A successful final claim is **amortized across environments**, not per-House retraining.

New room may require:

- map / source-carrier construction;
- physics bank generation or trajectory-independent forward-field cache;
- source-independent wind and sensor calibration.

It must not require source-label neural retraining.

The existing 7404-shard bank took about 10 h total to build across three Houses. A new ~200-carrier room with 8 predictive members is therefore still an offline physics-precomputation cost on the order of hours on comparable hardware unless parallelized. This cost must be stated explicitly; zero neural retraining does not mean zero environment setup.

Current benchmark also fixes source strength Q. A real-world zero-retraining claim is conditional on controlled/calibrated Q unless Q is explicitly added to the nuisance distribution before real localization outcomes are viewed.

## 10. Final decision policy

There will be no sequence of V3/V4/V5 neural rescue experiments.

One integrated contract will:

1. freeze V2 architecture;
2. construct H02/H03 measured-domain training views from the existing bank only;
3. run held-out-source + held-out-House qualification and calibration;
4. if and only if the preregistered qualification passes, continue automatically to runtime parity/shadow;
5. if shadow passes, run the paired closed-loop matrix;
6. only after FULL closed-loop GO, run frozen ablations;
7. otherwise terminate this PF-SNRE line permanently and report the failure.

No user round-trip is required between these internal stages; the contract itself owns the STOP gates.