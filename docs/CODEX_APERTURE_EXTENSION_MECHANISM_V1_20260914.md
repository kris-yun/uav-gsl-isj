# Spatial-aperture extension mechanism v1

Date: 2026-09-14  
Branch: `codex/dual-uav-two-point-premise-20260913`

Status: **FROZEN BEFORE APERTURE RESPONSE QUERY**

## 1. Question

The 222.8 s support-extension test improved some singular-spectrum values but
left temporal exposure and local information energy below the frozen gates.
This stage tests exactly one remaining physical mechanism:

> Does a larger source-response aperture provide the missing spatial support?

The aperture is increased from the deployed 2 m plus/minus separation to the
maximum 5 m separation permitted by the frozen map-feasibility cap. This is a
mechanism test, not yet a main-innovation claim.

## 2. Frozen conditions

- House02, sources `S_truth`, `S_k01`, `S_k10`, `S_k22`.
- Design winds `W_fast`, `W_slow` only; `W_altfast` and every other wind are
  forbidden.
- Same map-only deterministic farthest-start/DFS route rule and 12 candidates.
- Altitude 0.4 m, speed 0.35 m/s, cadence 0.2 s, horizon 222.8 s.
- Endpoint separation is exactly 5.0 m, with the midpoint on the center route.
- Ordered plus/minus channels are retained separately.
- Independent FOPDT response: dead 0.4 s, rise 1.2 s, recovery 1.2 s.
- Only the pre-existing raw-cache frames 0–445 are queried; no new GADEN is
  generated.
- No source identity, source coordinates, gas values, previous scores, or
  learning outputs may enter route construction.

## 3. Freeze and gate

The 5 m candidate bytes, geometry policy, response-query code, and scoring code
must be committed before aggregate source-response scoring. The candidate
generator may use only occupancy, connectivity, 5 m endpoint feasibility, and
the recorded design-wind vectors for its fixed aperture orientation.

For each route and both design winds, reuse the frozen support-extension score:

- rank = 3;
- `sigma3/sigma1 >= 0.05`;
- `Q_energy >= 0.01`;
- no exact source-response collision;
- every source exposed in at least two equal temporal thirds;
- full 222.8 s rich-support score strictly exceeds that route's 150 s prefix.

The mechanism passes only if one route passes all gates on both design winds.
If none passes, record `APERTURE_EXTENSION_MECHANISM_NO_GO`; the physical
support premise remains unconfirmed and no main-innovation claim is allowed.
If a route passes, record only `APERTURE_IS_LOAD_BEARING_CANDIDATE`; a separate
held-condition learning/planning gate is still required.

## 4. Forbidden rescue actions

Do not tune the rank tolerance, energy threshold, FOPDT constants, horizon,
source list, wind list, route count, exposure floor, channel compression, or
post-select a source/wind after viewing responses. Do not read `W_altfast`.
