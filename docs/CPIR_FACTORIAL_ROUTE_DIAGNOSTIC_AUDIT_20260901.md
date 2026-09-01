# CPIR factorial route-diagnostic audit (2026-09-01)

## Terminal decision

`CPIR_FACTORIAL_ROUTE_DIAGNOSTIC_NO_GO`

- M1: `M1_CAUSAL_PHYSICAL_INTERVENTION_PASS`
- M2: `M2_PERSISTENT_SENSOR_MAIN_MODULE_NO_GO`
- M3: `M3_STOP_RESOLVED_MAIN_MODULE_NO_GO`
- VM Release parity: **not authorized**
- closed-loop smoke and formal 9-pair runs: **not authorized and not started**

The route diagnostic supports M1 on the frozen historical tapes, but M2 and
M3 do not meet the preregistered requirement of an independent, repeatable
robot-task increment. The three-module paper/runtime architecture must
therefore not proceed. No parameter or formula was changed after outcomes were
read, and no rescue experiment was started.

This is deliberately a one-way diagnostic. The frozen full-grid runtime bank
has a separately frozen M2 motion-coverage failure, and its observation
operator is not identical to the continuous-route bank. A positive route-bank
result could not authorize runtime parity or closed loop. A preregistered
module failure is retained as negative evidence.

## Frozen execution

- authoritative starting commit: `57cd4e41bb02f5e3e85b3d3a7986c9e4ff72632d`
- final evaluator commit: `e2bb4a003baa4b2438dd63c9d83f145fcdc1b7f4`
- exact git archive SHA-256:
  `90f3759c21fa9b2bb29267904f02e97f67ca4af2b4e3e755dd2990da791f5f57`
- preregistration SHA-256:
  `2fd5d0f7c4463a3f8f853ecddb7292be1962e9b1a0eae379c50f1de627b3af58`
- route-bank summary SHA-256:
  `17364eb744f4fc53c4b52eee0362f09bdee3e8655b74c9d5e5a2eb0a3a9e2d47`
- route-bank manifest SHA-256:
  `c68e4bcbd196a85d74ff9a44db01b2090f4487fc84943f82fcd0d17a18629bed`
- output root:
  `/home/zyc/CPIR_FACTORIAL_ROUTE_DIAGNOSTIC_20260901_e2bb4a0_R3`
- evidence package:
  `/home/zyc/CPIR_FACTORIAL_ROUTE_DIAGNOSTIC_20260901_e2bb4a0_R3_NO_GO.tar.gz`
- evidence-package SHA-256:
  `8a1a50c240dcabf7c1ff23ea0b21be80680087197b24a80881acbfe3c133e9fc`

All four bank-free selftests passed. Stage 1 verified 10 trajectory-schedule
hashes per House, 1,680/1,608/1,648 route shards for H01/H02/H03, and consumed
25,200,000/24,120,000/24,720,000 float32 physical values. It froze all
factorial and STOP-PERMUTE posteriors before Stage 2 read A0 or truth:

- semantic freeze SHA-256:
  `a32d1d343f446bb02f86e0d14e604dc5fffaf5d5add449d2eb134a10505b65de`
- Stage-1 manifest file SHA-256:
  `a284dd44158bca847d1dbb2689153264ba54e29a0764a1fb1dd9e6785da92cb8`
- Stage-2 summary SHA-256:
  `9ba3c3b01b477d868873bf1175f066998bfdc8063e85252c294bf660e7a9b1a8`
- independently verified artifact-list V2 SHA-256:
  `b6f9f9786124126077e0ff0352abd85d686bcfa56505db344d2dbb98642e11ec`

The original aggregate hash file included a self-entry and is not used as an
integrity authority. It was preserved; `ARTIFACT_SHA256SUMS_V2.txt` excludes
all aggregate hash files and passed `sha256sum -c`.

Two pre-truth implementation failures were preserved rather than overwritten:

1. commit `3860702` stopped on the difference between total physical stops
   (16/17) and the common five-update window (15); Stage-1 log SHA-256 is
   `3c9c3a023827b4ef51ac353d4688c38ed6b1225698eeb728f8f03d18b2f36d08`;
2. commit `d14c285` stopped because the prediction matrix was trimmed to 15
   stops while the observation vector still retained its trailing stops;
   Stage-1 log SHA-256 is
   `887ab15229afe2c303fd5998a9775667bbc87d42679ccc0391a8b52595099c92`.

The R2 preregistration amendment fixes the analysis window to stops 0--14,
which are exactly the common prefixes visible at the five source updates for
all 30 tapes. Stops completed after source update 5 cannot affect any frozen
posterior or the M2 mechanism Gate. Both failed attempts stopped before A0,
truth, or an outcome metric was read.

## Time process

The evaluator wrote 900 per-update rows: 30 cases x 5 updates x A0/F00/F01/F10/F11/STOP-PERMUTE.
The table below gives the pooled mean over 30 cases. Update time is the mean of
the exact paired update times; AUC used each case's exact times.

| Arm | Update | mean t (s) | error (m) | true-source normalized rank | entropy (nat) | max posterior |
|---|---:|---:|---:|---:|---:|---:|
| A0 | 1 | 67.69 | 4.150 | 0.720 | 3.270 | 0.190 |
| A0 | 2 | 121.11 | 4.490 | 0.690 | 2.330 | 0.330 |
| A0 | 3 | 175.84 | 4.990 | 0.720 | 2.260 | 0.320 |
| A0 | 4 | 228.80 | 5.230 | 0.730 | 1.930 | 0.380 |
| A0 | 5 | 281.34 | 5.182 | 0.767 | 1.570 | 0.460 |
| F00 | 1 | 67.69 | 2.780 | 0.620 | 5.210 | 0.020 |
| F00 | 2 | 121.11 | 2.730 | 0.560 | 5.220 | 0.020 |
| F00 | 3 | 175.84 | 2.750 | 0.440 | 5.450 | 0.010 |
| F00 | 4 | 228.80 | 2.560 | 0.360 | 5.540 | 0.010 |
| F00 | 5 | 281.34 | 2.627 | 0.300 | 5.400 | 0.010 |
| F01 | 1 | 67.69 | 2.600 | 0.590 | 5.160 | 0.020 |
| F01 | 2 | 121.11 | 2.730 | 0.530 | 4.510 | 0.050 |
| F01 | 3 | 175.84 | 2.810 | 0.450 | 4.360 | 0.060 |
| F01 | 4 | 228.80 | 2.740 | 0.400 | 4.190 | 0.070 |
| F01 | 5 | 281.34 | 2.468 | 0.326 | 4.060 | 0.070 |
| F10 | 1 | 67.69 | 3.070 | 0.640 | 5.090 | 0.020 |
| F10 | 2 | 121.11 | 2.960 | 0.570 | 5.200 | 0.020 |
| F10 | 3 | 175.84 | 3.010 | 0.450 | 5.440 | 0.010 |
| F10 | 4 | 228.80 | 2.680 | 0.370 | 5.490 | 0.010 |
| F10 | 5 | 281.34 | 2.680 | 0.310 | 5.360 | 0.010 |
| F11 | 1 | 67.69 | 2.910 | 0.610 | 5.030 | 0.030 |
| F11 | 2 | 121.11 | 2.910 | 0.530 | 4.570 | 0.040 |
| F11 | 3 | 175.84 | 3.060 | 0.450 | 4.340 | 0.050 |
| F11 | 4 | 228.80 | 2.930 | 0.380 | 4.090 | 0.080 |
| F11 | 5 | 281.34 | 2.552 | 0.324 | 3.960 | 0.070 |

All 900 per-update rows and all 180 case-metric rows were independently
checked for finite errors/AUC/entropy and legal probability/rank/time ranges;
zero invalid rows were found. A0's final posterior and update-5 posterior were
identical (`max_abs=0`).

## Module Gates

### M1: PASS within this evidence class

F00 versus A0 had an independent, repeatable downstream gain:

- final error: `5.182322 -> 2.627136 m`, 22 wins / 8 losses,
  one-sided exact sign `p=0.008062`, all three House means lower, no stable
  reverse;
- time-to-2m: `278.410 -> 208.039 s`, 15 wins / 3 losses / 12 ties,
  `p=0.003769`, improvement in two Houses and no stable reverse;
- final normalized source rank: `0.766500 -> 0.300362`, 30/30 wins,
  `p=9.31e-10`, all three Houses improve.

Final error was not significantly worsened. Error AUC improved in the pooled
data (`1497.730 -> 945.451 m*s`) but was not selected for the Gate because H02
had a stable AUC reverse. M1's PASS is route-diagnostic evidence, not a
full-grid runtime authorization.

### M2: NO-GO

The direct predictive Gate failed:

- event NLL: raw `1.116567`, persistent `1.106199`; tape-level sign
  `p=0.066900`;
- Brier: raw `0.346406`, persistent `0.344102`; tape-level sign
  `p=0.017345`;
- five-bin ECE worsened: `0.322469 -> 0.335062`;
- for true hits, mean predicted hit probability was `0.613007 -> 0.621350`,
  while hit NLL worsened `1.022083 -> 1.025822`;
- for true no-hits, mean predicted no-hit probability was
  `0.508493 -> 0.503539`, while no-hit NLL improved
  `1.292898 -> 1.256201`.

The downstream F11-versus-F01 Gate also failed every eligible metric:

- final error worsened `2.468041 -> 2.552024 m`;
- error AUC worsened `941.731 -> 996.317 m*s`;
- time-to-2m worsened `210.261 -> 243.714 s`;
- no downstream metric was a clear, cross-House increment.

H03 was a preregistered stable reverse: final error
`0.952646 -> 2.111487 m` (1 win / 9 losses; worsening `p=0.010742`), AUC
`523.419 -> 844.378 m*s` (1/9; worsening `p=0.010742`), and time-to-2m
`70.362 -> 236.811 s` (0 wins / 8 losses / 2 ties; worsening
`p=0.003906`). This is not a marginal failure and must not be rescue-tuned.

### M3: NO-GO

F01 versus F00 had a small pooled apparent gain, but it was not repeatable:

- final error `2.627136 -> 2.468041 m`, 20/10, `p=0.049369`;
- AUC `945.451 -> 941.731 m*s`, 20/10, `p=0.049369`;
- H01 was a stable reverse for both final error
  (`2.996322 -> 4.045048 m`, 2/8) and AUC
  (`1097.504 -> 1348.065 m*s`, 2/8);
- pooled final normalized source rank moved in the wrong direction:
  `0.300362 -> 0.326398`.

The destructive control did not validate stop identity. Compared with
STOP-PERMUTE, F01 was not significantly better in final error
(`2.541040 -> 2.468041 m`, `p=0.649446`) or AUC
(`925.157 -> 941.731 m*s`, `p=0.574723`), and rank also moved in the wrong
direction (`0.324944 -> 0.326398`).

## Consequence

Neither final error nor error AUC has the required monotone
`A0 -> F00 -> F01 -> F11` progression. The formal three-module Gate is NO-GO.
The correct scientific state is one supported module (M1, diagnostic evidence)
and two rejected modules (M2/M3), not a rescued three-module story. The frozen
full-grid coverage blocker remains open independently, so no parity or
closed-loop execution is justified.
