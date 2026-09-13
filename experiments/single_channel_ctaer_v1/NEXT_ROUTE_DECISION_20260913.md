# Single-channel main-route decision after CTAER

Date: 2026-09-13

## Decision

Freeze CTAER without changing its 30 s window, tau grid, score or top-decile
gate.  Do not run another transformation on the exposed H03 seed11 trace.

The only next evidence step is one independent, continuous-release ethanol/VOC
flight in which classic PMFS controls the route and CTAER is evaluated as an
offline shadow on exactly the same measurements.  This removes the reviewer
confound that the proposed method received an extra path, sensor, source
shutdown, or response library.

## Why no further H03 module is admissible

| Route | Decisive evidence | Decision |
|---|---|---|
| M1R | endpoint improved in H01/H02 and degraded in H03; AUC improved 3/3 | retain implementation evidence, not cross-dataset main claim |
| LMBT backward transport | chronological wind lost to reversed-wind control | retired |
| CTT transport consensus/coherence | no stable incremental source ordering | retired |
| MC-SCSP / metric-corrected GW-MAIN | H03 localization worsened despite correct geometry | retired |
| original CCDE wind deprojection | held-out H01/H03 seeds 11/12/13 failed physical-vs-shuffled specificity | retired |
| TAORL | H03 rank 3,089 and MAP error 4.985 m; formal top-decile gate failed | component signal only |
| CTAER | H03 rank 804 and MAP error 4.956 m; 5/6 checks passed but 11.065% missed 10% | strongest component, frozen |

CTAER false-mode diagnosis is decisive.  The false MAP candidate has positive
forward-over-reverse evidence in 80% of windows, the same fraction as the true
candidate.  It beats the true candidate in six of ten windows and ties in one;
its median window evidence is `0.11808` versus `0.02604` at truth.  The false
mode is therefore stable rather than an outlier that robust pooling can remove.

## CCDE status correction

The older project instruction that CCDE held-out verification was pending is
superseded by the immutable archive already committed at
`experiments/single_channel_scsp_v1/evidence/source/CCDE_HELDOUT_EVIDENCE_V3_20260807.tar.gz`.
Its retained terminal verdict is `CCDE_WIND_MOMENT_NOT_PHYSICALLY_SPECIFIC` on
six held-out H01/H03 seeds.  Repeating CCDE is not an admissible next test.

## Claim that remains alive

The defensible hypothesis is narrow:

> Candidate-wise forward-versus-reverse ordinal response contrast can remove
> reversible route/signal ambiguity from a passive, single-channel mobile gas
> trace.

H03 supports this as a strong development signal, not as a passed main
innovation.  A new physical-domain result is required.  Even one successful
flight supports only an independent cross-domain replication; plural
cross-dataset effectiveness still requires multiple independently positioned
releases or another untouched benchmark.

## One next mechanism/evidence boundary

No new estimator module is selected.  The next discriminating object is new
data under the frozen CTAER formula.  A failure stops the causal line.  A pass
authorizes a separately preregistered small multi-placement confirmation; it
does not authorize formula tuning on the first flight.

