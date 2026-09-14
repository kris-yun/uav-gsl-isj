# Sensing-support upper-bound diagnostic — final result

Date: 2026-09-14  
Branch: `codex/dual-uav-two-point-premise-20260913`

## Scope and freeze

The diagnostic reused the 12 pre-response-frozen map-only routes (`AO_00`–`AO_11`), four frozen source interventions, `W_fast` and `W_slow` only, the fixed 150 s horizon, 0.2 s cadence, 0.4 m altitude, 0.35 m/s speed, 2 m plus/minus formation, and the original FOPDT parameters. No new GADEN simulation was started. The held wind was not queried or read.

The ordered plus/minus channels were preserved for C2 and C3; no signed difference, averaging, posterior, or new likelihood was introduced.

## Integrity

The endpoint query produced 96 traces and 72,000 rows. Independent audit results are:

- candidate route hash failures: 0;
- maximum center-to-endpoint midpoint error: `4.44e-16 m`;
- maximum 2 m separation error: `8.88e-16 m`;
- maximum independent endpoint FOPDT error: `0.0`;
- trace audit: `PASS`.

The C0 scorer reproduced the previous frozen reference with status `PASS`.

## Design-wind results

No route passed all frozen gates in any new configuration:

| configuration | measurement | passing routes | best route | best-route worst sigma3/sigma1 | best-route worst Q_energy |
|---|---|---:|---|---:|---:|
| C0 | center + FOPDT | 0/12 | AO_00 | `4.42e-17` | `1.78e-16` |
| C1 | center + raw oracle | 0/12 | AO_00 | `5.52e-17` | `2.19e-16` |
| C2 | ordered plus/minus + FOPDT | 0/12 | AO_00 | `6.83e-4` | `4.96e-7` |
| C3 | ordered plus/minus + raw oracle | 0/12 | AO_00 | `1.21e-3` | `1.55e-6` |

The best C2/C3 cases improve the weakest source-response direction relative to C0, but remain below the frozen `sigma3/sigma1 >= 0.05` and `Q_energy >= 0.01` gates; the source-exposure gate also remains unmet for at least one source. Thus the improvement is diagnostic evidence, not a passing deployable route.

## Final interpretation

`PRIMARY_BOTTLENECK_ATTRIBUTION = SENSING_SUPPORT_150S_PREMISE = NO_GO`

The 150 s sensing-support limitation survives removal of center-sensor FOPDT dynamics and addition of a complete ordered two-channel measurement. This result does not authorize a causal-localization, cross-dataset, or main-innovation claim. A later experiment may examine horizon/support extension as a new frozen stage; this commit does not open that stage.

`DEPLOYABLE_C2_ROUTE_STATUS = NONE_C2_NO_GO`  
`HELD_WIND_STATUS = NOT_RUN_NOT_READ`
