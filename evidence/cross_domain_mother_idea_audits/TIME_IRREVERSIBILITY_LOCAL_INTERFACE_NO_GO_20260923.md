# Time-irreversibility mother idea — PMFS local-interface kill test

Date: 2026-09-23
Status: **MOTHER PHENOMENON POSITIVE / PMFS SOURCE-UPDATE INTERFACE NO-GO**

This note closes only the proposed transfer of nonequilibrium time-irreversibility / arrow-of-time evidence into PMFS through candidate-local dynamics at the current StopAndMeasure position. It does not claim that time irreversibility is absent from plume trajectories.

## 1. Pre-registered transfer requirement

The parent audit established a real trajectory-level time-order signal (9/12 cross-transport source-identity matches; one-sided reversal 4/12) but rejected a global candidate occupancy observable. The only remaining justified test was therefore like-for-like and causal:

> at the actual source-update location, compare the measured temporal sequence available before that update with each source hypothesis' internal temporal sequence at the same frozen robot position.

No future robot pose, future GADEN field, source truth, or off-trajectory oracle is permitted in the score.

## 2. Exact PMFS interface block

The accepted raw-context package contains the six independent-plume runs and their source-update timing plus 0.2 s sensor traces. Immediately before source simulation, PMFS completes one StopAndMeasure block of 10 gas + 10 wind measurements (~2 s). The launch log then classifies that block as GAS HIT or NOTHING and starts the candidate simulations.

| Run | Source update sim time (s) | Last block avg_gas | Native block decision | Physical gas in same-position causal block? | Measured local dynamics |
|---|---:|---:|---|---|---|
| H01_R2026092201 | 195.5002 | 4.2e-45 | NOTHING | **No** | identically zero |
| H01_R2026092202 | 196.5986 | 2.8e-45 | NOTHING | **No** | identically zero |
| H02_R2026092211 | 189.5003 | 3.4 | GAS HIT | **Yes** | real plume signal |
| H02_R2026092212 | 190.8144 | 7.6e-16 | NOTHING | **No** | identically zero |
| H03_R2026092221 | 216.2998 | 5.9e-07 | NOTHING | **No** | nonzero decay while true gas is zero (sensor memory) |
| H03_R2026092222 | 217.6996 | 1.8e-07 | NOTHING | **No** | nonzero decay while true gas is zero (sensor memory) |

The same conclusion holds when the causal window is expanded only within the exact frozen current robot position before the update: only H02_R2026092211 contains true plume signal. H01 is zero throughout the same-position dwell; H02_R2026092212 is zero before the update; both H03 runs have zero true gas at that frozen position while the asymmetric sensor output decays from prior exposure.

Therefore only **1/6** source-update interfaces contains a physical local temporal signal that can support a plume time-arrow statistic. In 5/6, a candidate-local irreversibility score would either compare against a constant-zero target or learn the sensor's relaxation dynamics rather than plume transport.

## 3. H01 current-cell discrimination check

For H01_R2026092201 the frozen PMFS candidate-support export contains 152 source hypotheses and 212 historical observed-support cells per candidate.

At the exact source-update robot cell (-7.10, -7.43):

- 152 candidate predictions are available;
- **147/152 (96.7%)** have simulated hit probability exactly 0;
- only 5/152 have nonzero hit probability;
- the truth-nearest candidate (`quadtree_23_16_1_1`, source-point distance 0.23348 m from truth) also predicts 0 at the current cell.

Thus the measured zero sequence cannot discriminate the truth-nearest hypothesis from almost the entire candidate set. Any ranking obtained by matching candidate time-series irreversibility to this zero target would primarily reward absence of local activity, not the trajectory-level arrow-of-time mechanism.

This also explains why native PMFS can still update while the proposed local-dynamic transfer cannot: native candidate scoring compares each hypothesis against the **212-cell historical spatial support**, whereas the proposed transfer deliberately restricts the dynamic observable to the current frozen location to preserve causality and like-for-like semantics.

## 4. Decision

**NO-GO as the main PMFS innovation.**

The mother phenomenon remains scientifically real at the whole-trajectory level, but it fails the localization-interface gate required for a causal PMFS integration. The failure is structural, not a hyperparameter failure:

1. trajectory-level irreversibility is not present at the source-update location in 5/6 accepted independent-plume runs;
2. H03 demonstrates a concrete confound where measured time direction is produced by asymmetric sensor relaxation while true local gas is zero;
3. H01 shows current-cell zero predictions for 96.7% of source hypotheses, so local candidate dynamics are nearly non-discriminative even before choosing a particular irreversibility estimator;
4. using earlier measurements at different robot positions would reintroduce a spatial/trajectory observable and violate the frozen-position like-for-like contract that motivated this rescue test.

Accordingly, do **not** build a posterior factor, named method, or closed-loop experiment around time irreversibility. Move to the next mother-idea knife.

## 5. Reproducibility inputs

Accepted raw context:
- `ACCEPTED_RAW_CONTEXT.tar.gz`
- run-local `sensor_trace.csv`
- `context_bank/source_update_timing.csv`
- `launch.log`
- H01 `context_bank/source_update_0001/candidate_manifest.csv`
- H01 `context_bank/source_update_0001/candidate_support_alignment.csv`

Parent candidate-dynamics audit:
- branch `research/standalone-candidate-replay-20260923`
- H01 static candidate replay parity: 152/152
- parent mother-idea audit: `evidence/cross_domain_mother_idea_audits/TIME_IRREVERSIBILITY_AUDIT_20260923.md`
