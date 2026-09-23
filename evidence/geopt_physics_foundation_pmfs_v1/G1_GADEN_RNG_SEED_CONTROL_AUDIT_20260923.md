# M6 G1 Random-Realization Seed Control Audit

Date: 2026-09-23  
Status: **BLOCKER BEFORE CLAIMING INDEPENDENT NEW GADEN REALIZATIONS**

## Finding

Current public `MAPIRlab/gaden_core` does not expose an obvious random-seed parameter in `RunningSimulation::Parameters`.

In released `include/gaden/internal/MathUtils.hpp`:

- `GaussianRandom()` uses a thread-local `std::mt19937 engine` with default construction;
- `uniformRandom()` uses another thread-local default-constructed `std::mt19937`;
- `PrecalculatedGaussian` has no public `setSeed()`.

Therefore a user-facing label such as `seed=11` must **not** be assumed to create an independent plume realization in current gaden_core.

## Consequence

Before G1 data generation, Codex must identify the exact simulator/generator used for the previous independent seed2/seed3 realizations.

Required proof:

1. exact repository / commit / binary;
2. exact seed-setting code path;
3. how the seed reaches filament stochastic motion;
4. repeated same-seed generation is byte/statistically reproducible;
5. different-seed generation changes filament/concentration fields while keeping source/wind/config fixed.

## Allowed outcomes

### A — existing seeded generator is available

Use its explicit seed interface.

Only then predeclare new seeds, e.g. 11/12.

### B — current gaden_core lacks seed control

Do not merely rename repeated processes as independent seeds.

Create a minimal, audited seed-control patch or use the earlier verified seeded generator.

Any patch must:
- alter only RNG initialization;
- not change plume physics;
- record seed in metadata;
- be committed separately;
- include same-seed reproducibility and different-seed divergence checks.

### C — no independent realization control can be established

M6 G1 may perform a single-realization engineering smoke test, but it may NOT pass the scientific independent-realization gate.

Status becomes HOLD until proper stochastic replication exists.

## Hard rule

The G1 training/evaluation report must distinguish:

- source-position intervention;
- stochastic plume realization seed;
- model-training seed.

These are different variables and must never be conflated.

Status:

`RNG SEED CONTROL MUST BE PROVEN BEFORE 12×2 GENERATION`.
