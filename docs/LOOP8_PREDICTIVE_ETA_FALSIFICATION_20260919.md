# Loop 8 — Predictive/η Candidate Falsification

Date: 2026-09-19
Branch: research/remote-paradigm-loop-20260919
Status: INTERNAL SCREENING

## Test

A stricter source-independent predictive proxy was evaluated on the existing 12 controlled histories.

- H01/H02/H03 × {SA, SB} × {fast, slow}
- predictor: current-window -> next-window ridge mapping, fit only on fast-wind histories over 0–180 s
- source probe: nearest-centroid, trained on fast-wind 120–180 s
- held test: slow-wind 180–240 s
- tested windows: 5 s, 10 s, 20 s
- compared: direct temporal vector, predictive vector, fixed tail/η statistics, predictive+tail, direct+tail

Evidence file:
`evidence/remote_paradigm_loop_20260919/LOOP8_PREDICTIVE_ETA_PROXY.json`

## Aggregate result

| Window | Direct | Predictive | η/tail | Predictive+η |
|---|---:|---:|---:|---:|
| 5 s | 44/66 | 41/66 | 40/66 | 40/66 |
| 10 s | 18/30 | 20/30 | 20/30 | 19/30 |
| 20 s | 8/12 | 8/12 | 8/12 | 8/12 |

## Decision

### M1 predictive representation
**DOWNGRADE.**

The current evidence does not show a robust advantage over a matched direct temporal representation:
- loses at 5 s;
- modestly wins at 10 s;
- ties at 20 s.

This is not enough for a paper-defining main innovation.

### M2 extreme-event-aware intermittency
**DOWNGRADE AS CURRENT AUXILIARY.**

The previously observed H01 rescue by fixed tail observables is real but does not generalize as an additive gain in this stricter held-wind probe.
Appending tail statistics to the predictive representation does not improve aggregate held performance.

The Nature Communications 2026 η-learning idea remains scientifically interesting, but current project data do not yet justify it as one of the final two auxiliary innovations.

## Consequence

The current 1+2 candidate:
- predictive latent representation;
- η-learning intermittency preservation;
- online conformal calibration

is **not promoted**.

The search loop must reopen at M1 rather than tuning this architecture.

## Next search priorities

Only consider M1 paradigms that:
1. have a 2025/2026 top-main-venue or top-journal anchor;
2. provide a scientific object more specific than “better temporal features”;
3. make a falsifiable prediction on the existing H01/H02/H03 controlled data;
4. do not require route/OED innovation;
5. preserve source-probability-map output;
6. can be implemented lightly and transferred across VGR/GADEN, DNS and real wind-tunnel data.

Immediate new families to screen:
- Koopman / spectral latent dynamics;
- Platonic/shared physical representation across domains;
- sparse interpretable latent codes / superposition;
- distributional-consistency inverse inference;
- event-process / intermittent point-process representation.
