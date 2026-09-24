# MZ Innovation Likelihood v1 — Scientific Charter

Date: 2026-09-24
Branch: `research/mz-innovation-likelihood-v1`
Status: **CANDIDATE — M0 REQUIRED; NO CLOSED LOOP**

## 1. Scientific problem fixed by previous NO-GO results

The previous M4/SLL sequence establishes three facts:

1. Full 3-D filament transport is close to Markovian at one-step scale: deterministic
   3-D physics reaches the injected random-walk noise floor (~2.1–2.3 cm XY over
   adjacent saved snapshots).
2. Projecting the same transport onto the sensor-plane / sparse UAV observables creates
   strong temporal memory. In the frozen audit, the pooled lag-1 correlation of the
   projected 2-D residual was about 0.60 in x and 0.31 in y, while the full 3-D XY
   residual was approximately white.
3. Generic history features, stochastic blur, path signatures, and passive sparse
   single-UAV density scores did not reliably recover source rank.

Therefore the unresolved scientific problem is not another deterministic plume predictor.
It is inference under a **partially observed non-Markovian transport process**.

## 2. Mother theory

Primary 2026 anchor:

X. M. de Wit, A. Gabbana, M. Woodward, Y. T. Lin, F. Toschi, D. Livescu,
“Data-driven Mori–Zwanzig modeling of Lagrangian particle dynamics in turbulent flows,”
PNAS 123(13), e2525390123, 2026.
DOI: 10.1073/pnas.2525390123.

The Mori–Zwanzig projection gives a generalized Langevin form for resolved observables:

[
z_{t+1}=F(z_t)+\sum_{k=1}^{K}K_k\phi(z_{t-k})+\eta_t,
]

where the three terms are:
- resolved / Markov dynamics;
- memory induced by eliminated degrees of freedom;
- orthogonal dynamics (innovation/noise).

Important novelty boundary:
Mori–Zwanzig itself is NOT novel, and MZ has already appeared in robotics/belief
abstraction. The project must not claim “MZ for robots” as innovation.

## 3. Secondary innovation being tested

Do NOT use MZ only to make plume prediction MSE smaller.

For each source hypothesis s, define a candidate residual sequence

[
r_t(s)=\log(1+y_t)-\log(1+\hat y_t(s)).
]

Apply the frozen MZ memory closure learned only from correct-source training data:

[
\eta_t(s)=r_t(s)-\hat r_t^{\rm mem}(s).
]

Then use the orthogonal-dynamics innovation action as source evidence:

[
E_{MZ}(s)=\sum_t \eta_t(s)^2/\sigma_\eta^2,
qquad
P(s|y_{1:t})\propto P_0(s)\exp[-E_{MZ}(s)/2].
]

Scientific claim under test:

> the correct source hypothesis is the one whose projected observation residual can be
> explained by the universal memory/noise statistics of the unresolved 3-D plume,
> whereas a false source leaves structured, high-energy innovations.

If validated, this becomes a PMFS-compatible source likelihood, not a replacement for
the final source probability map.

## 4. M0 — existing-data necessary-condition gate

M0 generates NO new plume simulation.

Raw bank already on VM:
`/home/zyc/c0_5_real_gaden_bank_20260923`

Cells used:
- training only: S1_W1_A/B, S2_W1_A/B
- held out: S1_W2_A/B, S2_W2_A/B

Two historical House02 PMFS navigation geometries are frozen independently of this
C0.5 target bank.

At every one of the 566 GADEN save times, reconstruct the exact GADEN concentration
at the frozen UAV pose from raw filaments:
- actual z = 0.30 m;
- 3-sigma cutoff;
- obstacle line-of-sight;
- center concentration `ppm0 * (sigma0/sigma)^3`.

No target concentration grid is used.

### Memory model

- resolved scalar: `log1p(gas_ppm)`;
- memory horizon: **6 saved samples** (~3 s), frozen before W2;
- one scalar linear causal memory kernel;
- ridge = `1e-6`;
- W1 correct-source A<->B residuals from both nav paths are pooled for fitting;
- training innovation variance is frozen before W2.

A shuffled-temporal training null uses seed 20260924.

### W2 evaluation

For each nav seed (0,1), each true source (S1,S2), and each held-out realization (A,B):

- when A is the observation, candidate forward uses B;
- when B is the observation, candidate forward uses A;
- score both candidate sources S1 and S2;
- no same-realization comparison is allowed.

This gives 8 held-out source decisions.

Baselines:
1. Markov residual energy (no memory);
2. MZ innovation energy;
3. shuffled-memory null.

## 5. Frozen M0 gates

### Gate A — source identification
MZ must choose the correct source in **8/8** held-out W2 decisions.

### Gate B — load-bearing memory
Let margin = wrong-source energy minus true-source energy (larger is better).

Across the 8 cases:
- median MZ margin must be positive;
- median MZ margin must improve on the Markov margin by >=10%;
- MZ margin must exceed shuffled-memory-null margin in >=6/8 cases.

### Gate C — orthogonal innovation
For correct-source held-out residuals, MZ must reduce absolute lag-1 residual
autocorrelation by >=30% in median relative to raw residual.

## 6. Decisions

- Gate A fail:
  `M0_FAIL_STOP_MZ_INNOVATION_MAINLINE`
- A passes but B/C fail:
  `M0_MECHANISM_ONLY_NO_GO_AS_MAIN`
- A/B/C all pass:
  `M0_PASS_AUTHORIZE_LOCAL_5SOURCE_BANK`

Even M0 PASS does NOT authorize ROS/closed loop.
It authorizes only a small local-neighbor source bank around the known House02 source,
because the actual PMFS failure is near-source identifiability.

## 7. Anti-leakage rules

Forbidden before M0 decision:
- W2-based memory-horizon selection;
- W2-based ridge selection;
- source-specific kernel coefficients;
- candidate-specific variance;
- using true source coordinates as input features;
- using future gas/wind samples;
- using target concentration fields;
- post-hoc threshold/feature selection.

## 8. Real-UAV interface if the mechanism survives

Online inputs remain:
- UAV pose/time;
- local gas observation history;
- local/downwind-map-frame wind observation/history or deployment-valid estimate;
- occupancy map;
- frozen source candidates.

No oracle CFD/GADEN future wind, filament state, or true concentration field is allowed.

The final output remains a PMFS-style source probability map.
