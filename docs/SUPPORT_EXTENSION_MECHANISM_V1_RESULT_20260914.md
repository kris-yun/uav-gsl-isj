# Support-extension mechanism v1 result

Date: 2026-09-14  
Branch: `codex/dual-uav-two-point-premise-20260913`

## Verdict

`SUPPORT_EXTENSION_MECHANISM_NO_GO`

The 222.8 s read-only extension was a clean physical diagnostic, but it did
not establish the required source-response support. The deployable ordered
plus/minus FOPDT configuration passed the complete gate on **0 of 12 routes**
when both `W_fast` and `W_slow` were required to pass together. The main
innovation claim remains **not authorized**.

## What was actually tested

- Same House02 occupancy, four frozen source interventions, and two design
  winds as the 150 s stage.
- Same map-only deterministic route rule, 12 routes, 0.4 m altitude,
  0.35 m/s speed, 2 m plus/minus aperture, 0.2 s cadence.
- Same independent FOPDT parameters and ordered two-channel measurement; no
  channel differencing.
- Horizon extended to 222.8 s using only pre-existing raw-cache frames 0–445.
- No new GADEN data, no held wind, no source-aware route selection.

The trace integrity audit passed for all 96 traces and 107,040 rows, with zero
hash, timing, coordinate, occupancy, separation, or independent FOPDT errors.

## Physical result

The strongest route was `AO_00`: both winds reached rank 3 and had
`sigma3/sigma1` above 0.05, but the worst `Q_energy` was only about
`2.85e-4` and the union exposure gate still failed. `AO_05` reached larger
`Q_energy` on the two winds, but still failed the required exposure/support
conditions and did not satisfy the joint two-wind gate. No route passed all
conditions.

The extension therefore increased some source-response separation without
repairing the missing temporal exposure and information-energy support. The
previous 150 s NO-GO was not a sensor-lag-only artifact, and a longer horizon
alone is not sufficient under this route/formation configuration.

## Scientific interpretation

This is a physical support failure, not evidence that another learner or
posterior objective should be tuned. The next single mechanism must change the
spatial measurement support itself; the next frozen test is therefore a
larger, map-feasible receiver aperture, with all source and wind conditions
held unchanged.

No causal-localization, cross-dataset, or main-innovation claim is authorized
by this stage.
