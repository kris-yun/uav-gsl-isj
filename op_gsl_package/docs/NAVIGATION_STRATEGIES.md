# Cross-Domain Navigation Strategies for GSL

> 7 far-field domains searched for navigation/exploration strategies. Focused on solving: "robot starts 6m from source, binary hit/miss sensor, MAP navigation traps robot in accumulated-hit region."

---

## Problem Diagnosis (From Step 2 Experiments)

- Backward Lagrangian: 1.20m ≈ Green's function 1.21m → **Likelihood model is NOT the bottleneck**
- Both methods work well IF the robot is near the source
- The failure mode is: robot starts far, accumulates hits in wrong area, MAP follows wrong posterior
- **Root cause: Exploration strategy, not inference model**

---

## Strategy 1: Infotaxis (Insect Olfaction)

**Source**: Vergassola et al. 2007 Nature 445; Loisy & Eloy 2021 arXiv:2112.10861

**Formula**: At each step, choose action a that minimizes expected posterior entropy:
```
a* = argmin_a E_y[ H(θ | y, a) ]
    = argmin_a Σ_{y∈{hit,miss}} P(y|a) · H(θ | y, a)
```

**Key insight**: Infotaxis explores unvisited INFORMATION, not unvisited SPACE. Early in the search (high entropy), it naturally explores broadly. When hits start coming, it concentrates.

**Transfer**: Replace current `argmax posterior` navigation with `argmin expected entropy`. Reuse existing posterior — just change action selection.

**Reference**: Heinonen et al. 2025 arXiv:2502.21258 — quasi-optimal in realistic turbulence.

---

## Strategy 2: Bacterial Run-and-Tumble (Chemotaxis)

**Source**: Berg & Purcell 1977; Basu et al. 2023 arXiv:2311.17854

**Formula**: Compare recent hit rate to running average:
```
if hit_rate(recent) > running_avg:
    keep heading (RUN)
else:
    random new heading (TUMBLE)
```

**Key insight**: NO model, NO posterior, NO position memory. Just temporal gradient of binary signal. Never gets trapped because there's nothing to exploit.

**Transfer**: Simplest possible fix — replace MAP navigation with run-and-tumble when hit_rate is low.

---

## Strategy 3: Lévy Walk + Area-Restricted Search (Foraging Theory)

**Source**: Viswanathan et al. 1999 Nature — optimal for sparse targets

**Formula**: Heavy-tailed step length distribution:
```
P(step > L) ~ L^(-β),  β = 1.5 for exploration
```
Most steps are small (exploitation), occasional huge jumps (exploration).

**Key insight**: Lévy walks are mathematically optimal for finding sparsely distributed targets with no prior. The occasional 5-10m jumps escape local traps.

**Transfer**: When no hits for N steps, switch to Lévy exploration. When hits resume, switch to short-step exploitation (Area-Restricted Search).

---

## Strategy 4: Extremum Seeking Control (Control Theory)

**Source**: Krstic & Wang 2000; Aminde et al. 2024 arXiv:2405.15879

**Formula**: Inject sinusoidal dither, extract gradient via demodulation:
```
E[f(θ + a·sin(ωt)) · sin(ωt)] = (a/2) · f'(θ)
```

**Key insight**: Provably convergent to local extremum. NEVER stalls because dither keeps system moving. Amplitude `a` controls exploration-exploitation.

**Transfer**: Use hit-rate over sliding window as continuous signal. Start with large amplitude (broad search), shrink as convergence.

---

## Strategy 5: Expanding Square Search (Search-and-Rescue)

**Source**: IMO maritime SAR patterns; Gupta et al. 2018 arXiv:1801.01228

**Formula**: Leg lengths: 1L, 1L, 3L, 3L, 5L, 5L, 7L, 7L...
Directions cycle: N, E, S, W

**Key insight**: Deterministic coverage guarantee. Every point within radius R is scanned within R/leg_spacing legs.

**Transfer**: Use as Phase 1 exploration before any gas is detected. Switch to Bayesian once hits arrive.

---

## Strategy 6: Novelty-Driven Exploration (RL)

**Source**: RND (Burda et al. 2019); Yang et al. 2024 arXiv:2401.09750

**Formula**: Intrinsic reward = prediction error of learned model:
```
r_novelty = ||f_predictor(s) - f_target(s)||²
```
Simpler version: `r_novelty = 1 / (1 + visit_count[cell])`

**Key insight**: Visit-count based novelty alone is powerful — ensures robot covers unvisited space before revisiting.

**Transfer**: Add visit-count map. Navigation score = 0.7 * posterior + 0.3 * novelty_bonus.

---

## Strategy 7: Surge-Cast (Insect Olfaction State Machine)

**Source**: Standard biomimetic GSL; used by GrGSL

**Formula**: State machine:
- HIT → surge upwind
- MISS → cast crosswind (expanding amplitude)

**Key insight**: Cast behavior sweeps LATERALLY, not backtracking. Prevents getting stuck in same area.

**Transfer**: Already partially implemented in GrGSL. Can be used as navigation layer with our Bayesian posterior for MAP estimation.

---

## Recommended Hybrid: 3-Phase Architecture

```
Phase EXPLORE (no hits):  Expanding Square + Lévy jumps
    → Guaranteed coverage, escape traps
    → Transition: when hit_rate > 0 (first hit detected)

Phase SEEK (rare hits):   ESC + Run-and-Tumble
    → Model-free gradient following
    → Dither prevents stalling
    → Transition: when hit_rate > 0.3 (consistent hits)

Phase LOCALIZE (many hits): Bayesian posterior + MAP + EIG height
    → Existing forward model for precise localization
    → EIG for adaptive altitude
    → This is where our method shines
```

**Key principle**: Use simple model-free methods for exploration (where model accuracy doesn't matter), reserve the sophisticated Bayesian framework for localization (where model accuracy matters most).
