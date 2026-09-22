# Current-data mother-idea cycle — 2026-09-23

Branch: `research/cross-domain-mother-idea-audits-20260923`

Status: **NO MAIN INNOVATION PROMOTED YET**

Data used:
- old R2 six development cases;
- six now-unblinded independent stochastic-plume cases;
- CStar House01/02/03 × SA/SB × fast/slow controlled intervention asset.

The current cycle follows the post-HCMC/HCCE rule:
1. mother theory;
2. necessary phenomenon;
3. source/transport intervention kill test;
4. anti-shortcut controls;
5. only then dense localization;
6. method naming is forbidden before those gates.

## A. Path-space / large-deviation fluctuation structure

Mother-theory category:
nonequilibrium path ensembles, large deviations, dynamical partition functions.

Necessary phenomenon tested:
after removing the mean encounter level, same-source fast/slow encounter trajectories should retain a closer path-fluctuation generating-function signature than different-source trajectories.

Implementation used only as a kill-test proxy:
- binary gas encounter trajectory;
- non-overlapping blocks;
- centered block occupancy plus transition activity;
- fixed SCGF values at lambda = {-2,-1,-0.5,0.5,1,2};
- cross-transport nearest-source identity.

Result:
- real CStar identity = **10/12** for block lengths 10,25,50,100 samples.

Critical control:
preserve every episode's hit count but globally shuffle temporal order.

Fraction of 200 shuffled repetitions matching/exceeding real 10/12:
- block 10: **43.5%**
- block 25: **14.5%**
- block 50: **12.0%**
- block 100: **9.0%**

Decision:
`PATH_LARGE_DEVIATION_DIRECT_PROXY_NO_GO`

The apparent 10/12 is not sufficiently separated from a hit-rate-preserving temporal null and does not justify a path-space localization construction.

## B. Delay-dynamics / Koopman-style operator fingerprint

Mother-theory category:
operator-theoretic dynamical systems / Koopman representations.

Necessary phenomenon tested:
same-source fast/slow sensor dynamics should have a more stable finite-delay linear operator fingerprint than different-source dynamics after per-episode amplitude normalization.

Proxy:
- log(1+gas);
- per-episode standardization;
- Yule-Walker / ridge finite-delay dynamics;
- compare coefficient vectors across opposite transport;
- delay orders 5,10,20.

Results:
- d=5: **8/12**
- d=10: **7/12**
- d=20: **7/12**

Hit-distribution-preserving temporal-shuffle null:
- best member d=5 has **16%** of 50 nulls matching/exceeding the real result.

Decision:
`KOOPMAN_DELAY_FINGERPRINT_PROXY_NO_GO`

Do not create a Koopman GSL method from this data.

## C. Nonequilibrium time-irreversibility signal

Mother-theory category:
time-reversal symmetry breaking / entropy-production signatures.

Necessary phenomenon:
source identity should leave temporal probability-current structure beyond marginal gas amount.

Proxy:
- per-episode quantile coarse-graining of log gas into four states;
- antisymmetric transition currents P(i->j)-P(j->i);
- lags 1,2,5,10,25;
- cross-transport source identity.

Result:
- CStar source identity: **9/12**
- global temporal shuffle null mean: 5.88/12
- null matching/exceeding 9/12: **2.5%**

Interpretation:
there is genuine temporal-arrow structure beyond the marginal gas distribution.

However:
- the trivial encounter-rate comparator previously obtains **10/12** on the same CStar task;
- therefore irreversibility currently adds scientific mechanism evidence but not a competitive source-localization signal.

Decision:
`IRREVERSIBILITY_SIGNAL_RETAIN_AUXILIARY_ONLY`

Not a main-line candidate.

## D. Nonequilibrium response-law category — first surviving necessary phenomenon

External mother-theory motivation:
nonequilibrium fluctuation/response theory asks how a driven stochastic system transforms under perturbation rather than demanding an invariant state signature.

This directly targets the HCCE failure:
fast/slow transport should change the plume; the scientific question is whether the response is source-consistent.

### D1. Intervention kill test

For each candidate source point s and measured trajectory:
- compute the local positive downwind alignment
  a_s(t)=max(0, uhat(t) dot rhat_s->robot(t));
- pass it through the **pre-existing fixed gas-sensor FOPDT dynamics**
  dead time 0.4 s, tau=1.2 s, dt=0.2 s;
- score by correlation with log(1+measured gas).

The FOPDT constants are from the frozen project sensor model, not selected from CStar labels.

No PMFS candidate plume field is used.

CStar direct source identity:
- **11/12**

Only H02-SA-slow is misidentified.

Destructive controls over 500 repetitions:
- circularly shift gas relative to wind/pose:
  - null mean 6.46/12
  - fraction >= real: **0.6%**
- randomly shuffle wind samples while preserving pose/gas:
  - null mean 7.97/12
  - fraction >= real: **3.2%**

Therefore correctly aligned candidate-relative wind -> sensor response carries source-specific intervention information.

### D2. Dense old+new candidate-bank screen

The exact same fixed response proxy was then evaluated source-blind over final PMFS leaves:
- old six use source_update_0005 and history only up to that update;
- new six use the sole source_update_0001 and history only up to that update;
- candidate point = recorded native_source_x/y;
- candidate scores -> average percentile ranks -> leaf density;
- development endpoint uses the same Python ceil/stable-tie clone for all methods.

Aggregate endpoint:
- old six: **41.17%** reduction, **5/6** non-worse;
- independent-plume six: **26.35%**, **5/6**;
- all 12: **33.47%**, **10/12**.

This is the first current-data signal in this cycle that survives both old and independent plume development sets and also passes the CStar source/transport identity test.

### D3. Anti-metric audit: important warning

Dense candidate identity is still too weak:

Across all 12:
- mean percentile rank of candidate nearest truth: **0.512**
- mean score vs negative source-distance Spearman: **0.269**
- mean distance from truth of single top-scoring candidate: **4.39 m**

Several cases have a poor truth-nearest rank despite an improved top-5% centroid.

Therefore this response proxy is **not promoted**.

Current verdict:
`RESPONSE_LAW_MOTHER_THEORY_SURVIVES / CURRENT_DENSE_PROXY_MAINLINE_HOLD`

Interpretation:
- the mother-theory necessary phenomenon is materially stronger than HCMC/HCCE at this stage;
- the simple candidate-relative response proxy still suffers the endpoint-vs-source-identity problem;
- do not rescue it by tuning lag, distance power, wind-speed weighting, or response kernel against these 12 cases.

The next response-theory test, if pursued, must use a source-specific response object that improves direct candidate truth identity, not merely the top-5% centroid.

## Current ranking after this cycle

Rejected:
1. path-space SCGF direct proxy;
2. Koopman delay fingerprint direct proxy.

Auxiliary-only:
3. time irreversibility / probability currents.

Mother theory retained, implementation not promoted:
4. nonequilibrium response theory.

Pending Codex deterministic candidate replay:
5. Perron-Frobenius / transfer-operator transport remains the highest-priority mother theory requiring replayed candidate dynamics.

No method name has been assigned to item 4 or 5.
