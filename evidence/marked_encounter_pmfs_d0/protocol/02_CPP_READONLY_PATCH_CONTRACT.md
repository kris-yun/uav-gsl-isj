# Read-only PMFS patch contract

Modify only the isolated forward/export path.

## Required new quantity

Inside `simulateSourceInPosition`, during each recording timestep and BEFORE
the `updated[index]` binary-hit suppression:

```
multiplicityMap[index] += 1.0f;
```

for every active filament currently occupying that cell.

Keep the existing hit code completely unchanged.

At the end:

- `hitMap[i] / timesteps` remains the exact native presence frequency.
- `multiplicityMap[i] / timesteps` is the unconditional mean filament count.
- `conditionalMark[i] = multiplicityMean[i] / hitMap[i]` where hitMap>0.

## Parity requirement

With mark export OFF:
- native `hitMap` must be byte-identical to the existing forward path;
- all native candidate scores must remain byte-identical;
- deterministic RNG draw count/order must not change.

The multiplicity counter MUST NOT:
- call RNG;
- change filament movement;
- change emission;
- change `updated`;
- blur or normalize the native hit map differently.

## D0 forward bank

Use exactly the three already-OPEN environments:

- House01 / `1,3-2,4_fast`
- House02 / `3,5-1_slow`
- House02 / `4,5-3_slow`

Six frozen sources/environment from `E1_HOUSE_SOURCE_PANELS.tsv`.

For each candidate:
- all 11 existing numbered wind states in that environment;
- 8 deterministic PMFS transport replicas/state;
- common random numbers across candidates where the existing replay contract
  supports them;
- exact existing Native PMFS timesteps, dt, warmup and noise settings.

Total expected read-only forward realizations:
`3 * 6 * 11 * 8 = 1584`.

No GADEN player. No ROS closed loop. No truth-dependent tuning.

For each candidate/probe export source-blind aggregated:
- `presence_prob`
- `multiplicity_mean_unconditional`
- `multiplicity_mean_conditional`
- replicate/state counts and hashes.
