# Cross-domain mother-idea audit round 2 — post-HCMC/HCCE failure

Date: 2026-09-23
Branch: `research/cross-domain-mother-idea-audits-20260923`

Status: **NO MAIN METHOD PROMOTED**

This round follows the stricter failure-informed protocol:

1. test a necessary physical phenomenon first;
2. require source identity under transport intervention;
3. use destructive controls before localization;
4. do not name a method unless the mechanism survives.

The controlled development asset is the existing CStar House01/02/03 × SA/SB × fast/slow bank, with identical same-house routes and 1200 samples/episode.

---

## A. Path-space / large-deviation-style fluctuation signature

A lightweight path-space proxy used blockwise scaled-cumulant / fluctuation features of hit/no-hit and switching activity after removing the block mean.

Cross fast↔slow source identity:
- 10/12 across block sizes 10, 25, 50, 100.

However, destructive nulls that preserve each episode's hit-rate and marginal event count but randomize temporal order remain too strong:

- block 10: 43.5% of 200 nulls achieve >=10/12;
- block 25: 14.5%;
- block 50: 12.0%;
- block 100: 9.0%.

Verdict:

`PATH_SPACE_LARGE_DEVIATION_PROXY_NO_GO`

Interpretation: the apparent identity is dominated by low-order encounter statistics rather than a robust path-space large-deviation mechanism.

---

## B. Delay-dynamics / Koopman-style operator fingerprint

A source-blind autoregressive/delay-dynamics fingerprint of the measured gas sequence was compared across transport interventions.

Cross fast↔slow source identity:
- AR order 5: 8/12;
- order 10: 7/12;
- order 20: 7/12.

Temporal-order-destruction nulls remain substantial:
- order 5: 16% of 50 nulls achieve >=8/12;
- orders 10/20: 28% achieve >=7/12.

Verdict:

`KOOPMAN_DELAY_FINGERPRINT_NO_GO`

The necessary phenomenon "same source retains a stable operator-level gas-dynamics fingerprint across transport intervention" is not sufficiently supported.

---

## C. Nonequilibrium time irreversibility / probability currents

### Gas-only time-irreversibility feature

Antisymmetric transition-current features over gas-state trajectories yield:
- 9/12 cross-transport source identity;
- fully randomized temporal-order null: only 2.5% of 200 nulls achieve >=9/12.

Time direction is genuinely load-bearing:
- reverse target only: 4/12;
- reverse template only: 4/12;
- reverse both: returns to 9/12.

Thus the data contain a real source-related time-arrow signal.

### Candidate-relative wind × gas joint probability current

State = candidate-relative wind-alignment bin × gas event.

Best fixed three-bin construction:
- 11/12 cross-transport source identity;
- gas-blind geometry/wind control: 6/12;
- reverse target only: 4/12;
- whole-row temporal permutation: 0/100 nulls achieve >=11/12;
- gas circular shifts reduce identity to 7–10/12 depending shift.

This demonstrates genuine wind–gas temporal coupling beyond hit-rate.

However representation robustness is insufficient:
- across principled 2/3/4/5 alignment-bin families and lag families, performance ranges from 5/12 to 11/12;
- a bin-free continuous time-reversal-odd cross-current
  (A_s(\tau)=E[a_s(t)h(t+\tau)-h(t)a_s(t+\tau)])
  yields only 8–9/12;
- corresponding null fractions are approximately 7–18% for the stronger lag families.

Verdict:

`TIME_IRREVERSIBILITY_PHENOMENON_POSITIVE_BUT_NOT_MAINLINE_READY`

Keep as a possible auxiliary physical observable. Do not promote as the main innovation.

---

## D. Transition Path Theory / committor proxy

A source-conditioned advective reachability coordinate was defined from:
- candidate source position;
- robot pose;
- local wind direction/speed;
- source distance.

For each episode, an empirical future-hit committor curve estimated probability of entering a gas-hit state within a future horizon.

Parameter-family screen:
- horizons 5–100 samples;
- 3–6 coordinate bins;
- cross fast↔slow source identity: mostly 9–10/12.

But the required transport coordinate is not load-bearing.

When pose/wind is randomly permuted relative to the gas sequence while preserving the gas trace and all episode-level encounter statistics:
- real = 10/12;
- 200/200 decoupled nulls = 10/12;
- trivial hit-rate nearest-template baseline = 10/12.

Verdict:

`TPT_COMMITTOR_PROXY_NO_GO`

The observed committor signal is an exact hit-rate shortcut under this proxy.

This does **not** reject true Transition Path Theory on replayed PMFS particle transitions. It rejects the observed-only local-wind committor transfer.

---

## E. Resolvent / input-output response proxy

External mother idea:
fluid-mechanical resolvent/input-output analysis separates forcing from the flow operator and response.

Necessary-phenomenon proxy:
- candidate-relative transport forcing from local wind, pose and source coordinate;
- gas output = normalized log concentration;
- estimate a regularized finite impulse-response kernel;
- compare response-kernel shape across fast/slow.

Parameter family:
- kernel length 10 or 20 samples: 11/12 source identity;
- ridge alpha 0.1 / 1 / 10: still 11/12;
- length 40/80: 10/12.

However candidate/source forcing is not necessary:
- source-conditioned forcing: 11/12;
- source-independent wind-speed forcing: 11/12;
- geometry-only forcing: 6/12 (L10), 8/12 (L20).

Furthermore gas↔wind time shifts do not reliably destroy the result:
- L10: shifts 25/100/300/600 -> 10/9/10/9;
- L20: shifts -> 11/10/11/8.

Verdict:

`RESOLVENT_SOURCE_FORCING_TRANSFER_NOT_ESTABLISHED`

There is evidence of a source-dependent wind→gas response signature, but the source-conditioned forcing mechanism itself is not load-bearing and temporal decoupling is not decisive. Do not promote.

---

## F. What remains scientifically promising after these kills

The standalone PMFS candidate replay now changes what can be tested honestly.

For H01_R2026092201:
- 152/152 evaluated candidates reproduce Native sampled source point, support hit probabilities and Native score exactly;
- replayed full final hitMap matches the compiled Native PMFS kernel bitwise for every candidate;
- 30,400 candidate-internal steps are available;
- sparse occupied-cell events and aligned cell transitions are available.

This enables two mother theories that could not previously be tested faithfully:

### 1. Perron–Frobenius / transfer-operator transport

Use the actual candidate particle/cell transition dynamics, not the measured gas time series as a proxy.

Necessary phenomenon to test:
- source-conditioned transport operators or their first-passage/reactive-flux observables must contain source identity beyond the final time-averaged hitMap;
- the effect must survive independent plume realizations and CStar source/transport intervention;
- if a static hitMap or geometry-only control explains the same ranking, reject.

### 2. True transition-path / first-passage physics

Use replayed per-cell first-passage/transition data.

Necessary phenomenon:
- correct candidate source should produce a source-to-observation arrival/reachability structure compatible with observed gas-hit cells and encounter ordering;
- rank/ordering tests should avoid assuming PMFS internal time is synchronized to robot time;
- temporal aggregation should be shown to destroy useful source information.

These require the replay contract to be extended beyond the single H01 case before promotion.

---

## Current conclusion

No mother idea in this round is promoted to a main innovation.

The strongest actual discovery is methodological:

> observed sensor-sequence proxies repeatedly produce attractive source-identity numbers that collapse to hit-rate, wind-regime, or representation shortcuts. The next credible main-line search should operate on the newly recovered source-conditioned transport dynamics **before** they are collapsed to the Native static hitMap.

