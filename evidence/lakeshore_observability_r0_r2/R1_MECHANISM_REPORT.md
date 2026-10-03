# R1 offline mechanism report

Decision: **R1_HOLD_WEAK_OR_UNSTABLE**.

Primary fails because N0 and F1/F2 all have88.89pp height Top1 spread, so the negative-control contrast is absent. At mid release10, N0 is100% Top1 at10m and11.11% at30/60/100m; F1/F2 are100% at10/30m and11.11% at60/100m. Rank1 versus5 is shared by controls. The present data show an extension of the detectable height to30m, not a front-specific low-level false-negative blind zone. M1 upwind-cone capture is100% and M2 blind fraction0. M3 F1 front-peak fraction41.67% versus N033.33% at mid release is weak secondary evidence only; HOLD does not certify the primary mechanism. Threshold sensitivities do not rescue primary. R2 is not run.

R0_GO precedes N0 parity PASS, native RNG repeatability PASS, wind QC PASS and 12-realization smoke PASS. Then parameters, gas generation and scorer sources were frozen before the 864-realization matrix. No PMFS, learned model, closed loop or House rerun was involved.

Adapter: ros2_gaden family, minimal native C++ CLI against unchanged pre-existing GADEN core 3.0 in PF_DEI_V3_GADEN_BUILD. Python bindings absent. Main source commit17adaf650a4f11d29aa049cf0661e9f9ea2e636f, main core9e93c36ae1af74f6a62c42f1c9d7b813153222ed, historically modified. Isolated build's Git links are broken; source/binary hashes are authoritative, its original commit is not asserted.

Geometry is explicit native Environment occupancy: flat solid layer -5..0m; free interior0..150m; outer lateral/top cells are outlets. No shoreline wall. Native ParseOpenFoamVectorCloud preprocesses every regular CSV. Native RunningSimulation generates/query filaments, no replacement concentration field or postprocessing lift. No runtime package/kernel was installed, upgraded or edited.

N0 u=2m/s. L1 u=.4+1.6*f(z). F1/F2 divergence-free streamfunction: u=.4+A*s(x)*(f(z)-mean(f)), w=-A*sprime(x)*I(z), I(0)=I(150)=0. Compensating upper return flow preserves continuity. H=100m, widths15m vertical/35m horizontal. w maxima.5/1m/s. This is an ideal mechanism ablation, not fitted transient weather. N0 random100 query-point error0; finite-difference divergence maxima1.071e-4/2.142e-4s^-1.

Methane:5/10/20filaments/s, initial centre20ppm, sigma100cm, growth gamma10000cm²/s, native noise.02,298K/1atm. These are frozen synthetic dispersion settings, not inferred from public weather. Native buoyancy is unchanged across conditions. Eight explicit plume seeds30001..30008; OMP1, separate process per realization;120s warmup then300s fixed1Hz queries. Gas fields evolve in memory; exported C data are native trajectory observations, with replay defined by frozen seeds and binaries.

M4 removes the held-out seed from all9 source templates, Beta(1,1) smoothing and Brier ranking. Exact ties receive average rank/fractional Top1/Top3 credit; all misses remain chance-level. Heights10/30/60/100m share one2m/s XY ladder, period220s. Hit threshold.001ppm, sensitivity.0005/.002ppm. No per-environment thresholds.

## Primary gate

| environment   |   release |   best_height |   worst_height |   top1_spread_pp |   median_rank_difference |   source_x_groups_same_direction |   seeds_same_direction |   N0_spread_pp | control_pass   | primary_pass   |
|:--------------|----------:|--------------:|---------------:|-----------------:|-------------------------:|---------------------------------:|-----------------------:|---------------:|:---------------|:---------------|
| N0            |         5 |            10 |             30 |          88.8889 |                      4   |                                3 |                      8 |        88.8889 | False          | False          |
| N0            |        10 |            10 |             30 |          88.8889 |                      4   |                                3 |                      8 |        88.8889 | False          | False          |
| N0            |        20 |            10 |             30 |          88.8889 |                      4   |                                3 |                      8 |        88.8889 | False          | False          |
| L1            |         5 |            10 |             30 |          88.8889 |                      4   |                                3 |                      8 |        88.8889 | False          | False          |
| L1            |        10 |            10 |             30 |          88.8889 |                      4   |                                3 |                      8 |        88.8889 | False          | False          |
| L1            |        20 |            10 |             30 |          88.8889 |                      4   |                                3 |                      8 |        88.8889 | False          | False          |
| F1            |         5 |            10 |             60 |          88.8889 |                      4   |                                3 |                      8 |        88.8889 | False          | False          |
| F1            |        10 |            10 |             60 |          88.8889 |                      4   |                                3 |                      8 |        88.8889 | False          | False          |
| F1            |        20 |            10 |            100 |          88.8889 |                      4   |                                3 |                      8 |        88.8889 | False          | False          |
| F2            |         5 |            10 |             60 |          88.8889 |                      4   |                                3 |                      8 |        88.8889 | False          | False          |
| F2            |        10 |            10 |             60 |          88.8889 |                      4   |                                3 |                      8 |        88.8889 | False          | False          |
| F2            |        20 |            10 |             60 |          88.8889 |                      2.5 |                                3 |                      8 |        88.8889 | False          | False          |

## Height results

| environment   |   release |   height |     top1 |     top3 |   median_true_rank |
|:--------------|----------:|---------:|---------:|---------:|-------------------:|
| F1            |         5 |       10 | 1        | 1        |                1   |
| F1            |         5 |       30 | 1        | 1        |                1   |
| F1            |         5 |       60 | 0.111111 | 0.333333 |                5   |
| F1            |         5 |      100 | 0.111111 | 0.333333 |                5   |
| F1            |        10 |       10 | 1        | 1        |                1   |
| F1            |        10 |       30 | 1        | 1        |                1   |
| F1            |        10 |       60 | 0.111111 | 0.333333 |                5   |
| F1            |        10 |      100 | 0.111111 | 0.333333 |                5   |
| F1            |        20 |       10 | 1        | 1        |                1   |
| F1            |        20 |       30 | 1        | 1        |                1   |
| F1            |        20 |       60 | 0.152778 | 0.392857 |                3.5 |
| F1            |        20 |      100 | 0.111111 | 0.333333 |                5   |
| F2            |         5 |       10 | 1        | 1        |                1   |
| F2            |         5 |       30 | 1        | 1        |                1   |
| F2            |         5 |       60 | 0.111111 | 0.333333 |                5   |
| F2            |         5 |      100 | 0.111111 | 0.333333 |                5   |
| F2            |        10 |       10 | 1        | 1        |                1   |
| F2            |        10 |       30 | 1        | 1        |                1   |
| F2            |        10 |       60 | 0.111111 | 0.333333 |                5   |
| F2            |        10 |      100 | 0.111111 | 0.333333 |                5   |
| F2            |        20 |       10 | 1        | 1        |                1   |
| F2            |        20 |       30 | 0.930556 | 1        |                1   |
| F2            |        20 |       60 | 0.111111 | 0.333333 |                3.5 |
| F2            |        20 |      100 | 0.111111 | 0.333333 |                5   |
| L1            |         5 |       10 | 1        | 1        |                1   |
| L1            |         5 |       30 | 0.111111 | 0.333333 |                5   |
| L1            |         5 |       60 | 0.111111 | 0.333333 |                5   |
| L1            |         5 |      100 | 0.111111 | 0.333333 |                5   |
| L1            |        10 |       10 | 1        | 1        |                1   |
| L1            |        10 |       30 | 0.111111 | 0.333333 |                5   |
| L1            |        10 |       60 | 0.111111 | 0.333333 |                5   |
| L1            |        10 |      100 | 0.111111 | 0.333333 |                5   |
| L1            |        20 |       10 | 1        | 1        |                1   |
| L1            |        20 |       30 | 0.111111 | 0.333333 |                5   |
| L1            |        20 |       60 | 0.111111 | 0.333333 |                5   |
| L1            |        20 |      100 | 0.111111 | 0.333333 |                5   |
| N0            |         5 |       10 | 1        | 1        |                1   |
| N0            |         5 |       30 | 0.111111 | 0.333333 |                5   |
| N0            |         5 |       60 | 0.111111 | 0.333333 |                5   |
| N0            |         5 |      100 | 0.111111 | 0.333333 |                5   |
| N0            |        10 |       10 | 1        | 1        |                1   |
| N0            |        10 |       30 | 0.111111 | 0.333333 |                5   |
| N0            |        10 |       60 | 0.111111 | 0.333333 |                5   |
| N0            |        10 |      100 | 0.111111 | 0.333333 |                5   |
| N0            |        20 |       10 | 1        | 1        |                1   |
| N0            |        20 |       30 | 0.111111 | 0.333333 |                5   |
| N0            |        20 |       60 | 0.111111 | 0.333333 |                5   |
| N0            |        20 |      100 | 0.111111 | 0.333333 |                5   |

## Secondary gate

```json
[
  {
    "environment": "F1",
    "release_results": [
      {
        "release": 5,
        "M1_capture_drop_pp": 0.0,
        "M1_pass": false,
        "M2_blind_source_count": 0,
        "M2_pass": false,
        "M3_front_peak_fraction": 0.4166666666666667,
        "M3_N0_front_peak_fraction": 0.3472222222222222,
        "M3_x_groups": 2,
        "M3_pass": true
      },
      {
        "release": 10,
        "M1_capture_drop_pp": 0.0,
        "M1_pass": false,
        "M2_blind_source_count": 0,
        "M2_pass": false,
        "M3_front_peak_fraction": 0.4166666666666667,
        "M3_N0_front_peak_fraction": 0.3333333333333333,
        "M3_x_groups": 2,
        "M3_pass": true
      },
      {
        "release": 20,
        "M1_capture_drop_pp": 0.0,
        "M1_pass": false,
        "M2_blind_source_count": 0,
        "M2_pass": false,
        "M3_front_peak_fraction": 0.3888888888888889,
        "M3_N0_front_peak_fraction": 0.3333333333333333,
        "M3_x_groups": 2,
        "M3_pass": true
      }
    ],
    "secondary_pass": true
  },
  {
    "environment": "F2",
    "release_results": [
      {
        "release": 5,
        "M1_capture_drop_pp": 0.0,
        "M1_pass": false,
        "M2_blind_source_count": 0,
        "M2_pass": false,
        "M3_front_peak_fraction": 0.3472222222222222,
        "M3_N0_front_peak_fraction": 0.3472222222222222,
        "M3_x_groups": 2,
        "M3_pass": false
      },
      {
        "release": 10,
        "M1_capture_drop_pp": 0.0,
        "M1_pass": false,
        "M2_blind_source_count": 0,
        "M2_pass": false,
        "M3_front_peak_fraction": 0.3333333333333333,
        "M3_N0_front_peak_fraction": 0.3333333333333333,
        "M3_x_groups": 1,
        "M3_pass": false
      },
      {
        "release": 20,
        "M1_capture_drop_pp": 0.0,
        "M1_pass": false,
        "M2_blind_source_count": 0,
        "M2_pass": false,
        "M3_front_peak_fraction": 0.4166666666666667,
        "M3_N0_front_peak_fraction": 0.3333333333333333,
        "M3_x_groups": 2,
        "M3_pass": true
      }
    ],
    "secondary_pass": false
  }
]
```

Full source/seed data are in M1/M2/M3_threshold_*.csv and M4_trials_threshold_*.csv. M1 conditions on gas hits. M2 reports paired trajectory-time sample fractions, not geographic area: repeated visits do not represent square metres. M3 compares peak source/front distance and predeclared15m band, requiring>=2 source-x groups, more front peaks than N0 and median peak closer to front than source, across>=2/3 release levels. This operationalizes a qualitative screening criterion, not a high-fidelity quantitative conclusion.

R2 is allowed only after matched primary+secondary PASS. R1 FAIL/HOLD stops active probing. Initial R0 whole-profile-slope interpretation error was corrected to README local-structure criterion before any gas results; event windows remained unchanged. JGR averaged XZ data provide only background ranges, never transient3D input.
