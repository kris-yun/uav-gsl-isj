# PMFS causal-event repair: House123 seed12 closed-loop result

Status: **REAL_CLOSED_LOOP_NO_GO_NO_MULTISEED**.

Follow-up: the contrastive event-evidence repair subsequently passed the M1
House123 seed12 development gate while M2 remained NO-GO.  See
`PMFS_CER_RATIO_M1_PASS_M2_NOGO_20260908.md`.

This document supersedes the `PARTIAL_IMPLEMENTATION_NOT_CLOSED_LOOP` status in
`PMFS_JOINT_DEVELOPMENT_20260908.md`.  The code path was built from the current
development checkout, entered the real PMFS/GMRF/navigation loop, and completed
the predeclared House01/02/03 seed12 screen.  It did not pass the module-utility
gate, so no additional seeds are authorized by this result.

## Failure-first scientific construction

The repair targeted two concrete PMFS failure modes rather than adding another
planner weight.

### M1: causal event likelihood

Native PMFS first propagates one stop measurement over many spatial cells and
then compares a simulated field with that correlated map.  Treating those
derived cells as independent evidence can multiply one intervention outcome
many times.  M1 instead conditions on the executed sensing intervention and
uses each completed `StopAndMeasure` outcome once:

`p(s | D_t) proportional to p(s) product_i p(y_i | s, do(a_i), h_(i-1))`.

Here `a_i` is the actual stop cell, `y_i` is the block-level hit/miss, and block
IDs must increase strictly.  The spatially propagated PMFS map remains available
to the existing estimator/controller, but it is not counted as additional M1
source evidence.  This is a causal data-interface correction; ordinary Bayes
alone is not claimed as a new causal-identification theorem.

### M2: transport-nuisance marginalization

A single simulated plume realization makes source evidence depend on an
arbitrary transport draw.  M2 holds the source candidate fixed and averages the
event likelihood over three event-keyed, reproducible transport members:

`p(D_t | s) = (1/K) sum_k product_i p(y_i | s, k, do(a_i), h_(i-1))`.

The members use the native obstacle-aware GMRF/PMFS filament simulator.  They
are persistent within a source update and are keyed by seed, source update and
member ID, so OpenMP scheduling cannot silently change the paired contrast.

The three tested arms were therefore:

- `A0`: native PMFS (`pfdi_mode=off`)
- `M1`: one native transport member plus event likelihood (`cer_m1`)
- `M1M2`: three-member transport mixture plus event likelihood (`cer_m1_m2`)

## Environment and executable binding

All nine arms used seed12, a 240 s simulation budget, the corrected qualified
House-specific navigation/GMRF geometry, the current GADEN realization paths,
and the same executable SHA-256:

`4234e75b61d86668b063fd5fc6c9f4478cf8149d90b54f95de467d416f55a114`.

The reusable-environment preflight passed.  The corrected maps were accepted
and legacy map paths were rejected.  Independent live stationary probes for all
three Houses produced positive-stamp frames; comparison with raw wind files had
maximum absolute error `7.180059963252106e-09`.  Earlier controlled verification
covered 8640 frames with zero numeric discrepancy.  These checks establish the
environment/input binding, not algorithmic efficacy.

Every arm ended with `time_budget_timeout`, which is the intended 240 s horizon
termination rather than a crash.  Source traces reach approximately 238--240 s.

## Closed-loop results

Positive improvements mean lower error/AUC than the comparator.

| House | A0 final (m) | M1 final (m) | M1M2 final (m) | M1 final gain | M1 AUC gain (m s) | M2 incremental final gain | M2 incremental AUC gain (m s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| H01 | 6.8572 | 6.8572 | 7.0874 | 0.0000 | +24.9231 | -0.2302 | -66.9402 |
| H02 | 3.2146 | 2.8763 | 3.2146 | +0.3383 | +20.1777 | -0.3383 | +12.5823 |
| H03 | 7.7410 | 8.3056 | 7.3570 | -0.5646 | +38.8456 | +0.9486 | -39.2214 |

M1 versus A0 improved final error in only 1/3 Houses, although distance-error
AUC improved in 3/3.  Its mean final improvement was `-0.0754 m` and mean AUC
improvement was `+27.9821 m s`; the joint final-plus-AUC gate failed.

M2 incremental versus M1 improved final error in 1/3 Houses and AUC in 1/3.
Its mean final improvement was `+0.1267 m` but mean AUC improvement was
`-31.1931 m s`; the incremental gate failed.

Formal verdict: **NO_GO_NO_MULTISEED**.  Seed12 is an exposed development screen,
not independent confirmation and not a causal-identifiability proof.

## What the negative result isolates

The event-level intervention interface fixed a real dependence error and the M1
AUC result shows that it changes the trajectory in a consistently useful early/
integrated direction.  It nevertheless worsened H03 final error and did not
improve H01 final error.  The remaining mismatch is in the observation law:

- the online observation is a block-mean concentration after the configured
  asymmetric FOPDT sensor, thresholded at `0.1`;
- the native simulated `hitMap` is a spatial filament-visit frequency;
- the current M1/M2 code uses that frequency directly as the Bernoulli
  probability of the block-level sensor outcome.

Those variables are not calibrated equivalents.  In particular, repeated
misses can become overconfident evidence against a true source when the
simulator predicts intermittent exposure that the delayed block sensor does not
turn into a threshold crossing.  Three Monte-Carlo transport draws reduce draw
variance but cannot repair this structural sensor/forward-law mismatch.  This
explains why M2 can improve H03 final error while degrading its path AUC, and do
the reverse in H02.

## Next admissible mechanism

Do not tune planner weights or expand this version to more seeds.  The next M1/
M2 implementation should preserve the event-level causal factorization but
replace `hitMap[cell]` with the probability of the exact observed statistic:

1. simulate obstacle-aware concentration/exposure at the executed stop;
2. pass it through the same causal FOPDT sensor and block averaging operator;
3. marginalize persistent release and transport nuisance before thresholding;
4. calibrate the predictive hit probability without source truth or House ID;
5. require leave-one-House-out predictive support and calibration improvement
   over persistence before another closed-loop run.

For a defensible causal main claim, crossed source interventions under shared
transport must additionally show that the recovered source evidence is invariant
to transport shifts and sensitive to source changes.  Until that premise gate
passes, the present code is an auditable mechanism probe, not a successful main
innovation.

## Evidence

- Formal gate: `evidence/cstar_cer_house123_seed12_20260908_R2/CSTAR_CER_HOUSE123_SEED12_GATE.json`
- Nine raw run folders: `evidence/cstar_cer_house123_seed12_20260908_R2/H0*_seed12_*`
- Environment preflight: `evidence/cstar_joint_environment_20260908/PREFLIGHT.json`
- Live environment evidence: `evidence/cstar_joint_live_20260908`
- Evaluator: `tools/cstar_evaluate_cer_house123.py`
