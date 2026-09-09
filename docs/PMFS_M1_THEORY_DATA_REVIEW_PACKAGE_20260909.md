# PMFS M1 theory–data review package (2026-09-09)

## Question being decided

Which causal theory is actually supported by the observed PMFS evidence and is
most plausible for a cross-House/cross-dataset M1? The answer must be based on
the existing frozen runs, not on a paper title alone.

## Data evidence used

All results below are paired A0 comparisons under the certified environment
contract and sensor/replay seed 12. Algorithm seeds are not independent plume
realizations.

| Version | Gate/result | H01 | H02 | H03 | What the data reveal |
|---|---|---:|---:|---:|---|
| M1S seed11 | House123 majority pass | both + | both + | both − | event-time causal chain can work, but H03 over-concentrates |
| M1S seed10 | H01 NO_GO | both − | not run | not run | same method is not multi-seed stable; transport nuisance is unintegrated |
| M1P seed10 | H01 NO_GO | final +, AUC − | not run | not run | terminal-only physical-stop unit fixes overcounting but discards useful temporal information |
| M1E seed9 | House123 2/3 pass | both + | final −, AUC + | both + | transport marginalization helps, but does not guarantee every House |
| M1F seed6 | House123 1/3 pass | both + | final +, AUC − | final −, AUC + | event-time score is useful but member scale still dominates some windows |
| M1G seed5 | H01 pass; H02/H03 0/2 | both + | both − | both − | geometric pooling does not solve candidate-dependent bias |
| M1H seed4 | House123 1/3 pass | both + | final +, AUC − | both − | variance penalty rejects disagreement, not shared systematic error |

The most diagnostic H03 observation is that A0 reached approximately 0.45 m
from the source around 50 s, while M1H diverted after the first post-warmup
update. M1H later had 54.3% of samples above 0.5 ppm versus 68.6% for A0.
This is a closed-loop data-shift feedback, not merely high posterior variance.

## Failure decomposition

The runs expose four different failure layers:

1. **Estimand-unit mismatch (M1S):** eight internal 2 s blocks at one physical
   stop were treated as eight independent interventions. M1P corrected the
   unit but lost temporal information.
2. **Unintegrated transport Monte Carlo (M1S seed10 vs seed11):** the method's
   outcome can reverse across algorithm seeds under the same sensor seed.
3. **Candidate-dependent member scale (M1F/M1G):** geometric or arithmetic
   pooling changes scale but does not identify the source component.
4. **Shared candidate-dependent bias (M1H):** member variance can be small when
   all transport members are wrong in the same way.

Therefore the rejected premise is not event-level causality. The rejected
premise is that transport can be removed as a candidate-independent nuisance.

## Theory selection

### Primary theory: hierarchical partial invariance

**Bayesian Hierarchical Invariant Prediction (BHIP), CLeaR 2026** is the best
primary anchor. It reframes invariant causal prediction as hierarchical Bayes
and explicitly tests mechanism invariance under heterogeneous data. This fits
the observed pattern: H01/H02/H03 do not share one global transport mechanism,
so M1 must estimate a stable source component while shrinking, rather than
discarding, environment-specific deviations.

### Mechanism decomposition: latent confounded shift

**Causal Fine-Tuning under Latent Confounded Shift, ICML 2026** supplies the
second anchor. It separates stable and shift-sensitive components under latent
confounding. In PMFS, the stable component is source-responsive evidence; the
shift-sensitive component is transport/sensor/geometry interaction. This maps
directly to the M1S/M1H reversals.

### Observation correction: proxy calibration

**Proxy-Guided Measurement Calibration, CLeaR 2026** explains why the current
filament-frequency likelihood is not the same as the realized concentration
event. Its content/bias separation motivates the required FOPDT → block mean →
threshold forward observation operator before any new closed-loop claim.

### Dynamic identifiability

**Disentangling Dynamical Systems, CLeaR 2026** supports local,
state-dependent causal structure. It justifies preserving event-time windows
and conditioning on local transport/sensor state instead of imposing one
global invariant equation.

### Safety bound, not performance tuning

**Sharp Bounds for Treatment Effect Generalization under Outcome Distribution
Shift, CLeaR 2026** provides a sensitivity parameter `Lambda` for violations of
transportability. In M1 this is only a preregistered interval/abstention guard;
it must not be tuned to rescue a failed seed.

## Proposed M1 estimand

For candidate `c`, transport member/context `u`, and event window `i`:

```text
eta_u_i(c) = tau_i(c) + a_i(z_i) + gamma_i(c)^T z_u_i + epsilon_u_i(c)
```

`tau_i(c)` is the transferable source component. `a_i` is shared observation
context. `gamma_i(c)` explicitly retains candidate-by-transport interaction
instead of assuming it is zero. `z` contains observed wind, geometry and
sensor-memory proxies only.

The forward law must be:

```text
transport exposure -> FOPDT state -> block mean -> event probability
```

The sequential posterior uses the hierarchical marginal likelihood over the
frozen event window. If the `Lambda` sensitivity intervals of competing
candidates overlap, the update is held non-concentrated rather than allowing
entropy collapse from unidentified evidence.

## What can and cannot be claimed now

**Supported now:**

- event-time causal implementation is real and auditable;
- M1 has produced genuine gains in individual Houses and 2/3 House majority
  gains in some single-seed versions;
- the global candidate-independent transport-invariance premise is falsified;
- BHIP + latent-shift decomposition + proxy calibration is the theory-consistent
  repair direction.

**Not supported now:**

- universal House123 effectiveness;
- multi-seed or big-data effectiveness;
- the claim that any one 2026 paper proves gas-source localization;
- a new closed-loop result before attribution replay.

## Required GPT review checklist

An independent reviewer should answer:

1. Does the data table support partial invariance rather than abandonment of
   causal event evidence?
2. Is the proposed `tau + a + gamma` decomposition identifiable from the
   available transport members and observed proxies?
3. Does the sensor-consistent forward law address the M1S/M1P and M1H failure
   evidence without truth or House-specific tuning?
4. Is the `Lambda` interval used only as a sensitivity/abstention guard?
5. What exact replay result is required before claiming cross-House M1?

The answer must remain conditional until the frozen H01/H02/H03 attribution
replay passes these checks.

