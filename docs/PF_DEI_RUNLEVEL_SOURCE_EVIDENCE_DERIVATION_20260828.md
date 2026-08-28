# PF-DEI run-level source-evidence derivation

Date: 2026-08-28

Status: **TRUTH-BLIND MECHANISM / SOURCE-FORWARD ADEQUACY DIAGNOSTIC**  
No localization performance, C++, Active Probe or 60-arm authorization.

## 1. New evidence after exact deconvolution

The exact historical counterfactual is now complete for 30/30 OFF runs and 4049/4049 PMFS blocks.

- native/ideal block decisions differ on 159/4049 blocks = 3.93%;
- native HIT -> ideal NOTHING: 88;
- native NOTHING -> ideal HIT: 71;
- first block after an inter-stop transition: 32/484 = 6.61% flip;
- House flip counts: H01 58/1357, H02 29/1346, H03 72/1346;
- the inverse/forward round trip is at floating-point error scale;
- six-decimal inverse serialization bound is about 6.014e-6 ppm;
- no source truth, localization error or performance label entered the diagnostic.

Therefore sensor memory is a real deterministic observation-aliasing mechanism, but the small and bidirectional net block-decision effect is not sufficient evidence that sensor dynamics alone explains the earlier cross-seed source-ranking failure.

An especially useful qualitative check is that H02 has fewer block flips than H01 even though the earlier V6-A source-transfer result was worse for H02.  Flip count is therefore not a monotone proxy for source-evidence failure.

## 2. Stronger consequence of exact invertibility

For the frozen historical sensor configuration, the measured sequence `M` is an almost exact source-independent invertible transform `T(C)` of the physical concentration sequence `C`, apart from the known dead-time boundary/serialization limitations.

If a source inference is formulated correctly on the complete sequence, source likelihood ratios are invariant under this transform:

`p(M|S) = p(C=T^{-1}(M)|S) * |J_{T^{-1}}(M)|`.

Because the Jacobian is independent of candidate source `S`, it cancels in any source ratio/posterior normalization.

Therefore **A1 ideal and correctly modelled A2 native are not two scientifically independent source-information problems in this frozen configuration**.  Their source evidence should agree after canonicalization to physical concentration.

A large A1/A2 source-ranking difference would indicate an inference/implementation failure to represent the known sensor operator, not intrinsic information loss by the sensor.

This changes the next test:

> First test the candidate source/transport forward family in canonical physical-concentration space.  Use A1/A2 parity as a hard contract, not as two separately trained models whose differences could be caused by training noise.

## 3. What remains unresolved

The decisive remaining hypothesis is now:

`TRANSPORT_FAMILY_OR_SOURCE_FORWARD_INSUFFICIENT`

versus

`LOCAL_OBSERVATION_ALIASING_DOMINANT`.

The old occupancy/frequency model is already inadequate.  The new question is whether the **closed physical GADEN concentration forward family**, evaluated over a whole run and marginalized over source-independent transport nuisance, gives source evidence that transfers chronologically and beats a source-independent prior-predictive null.

If it does, then the old failure was primarily observation representation/local attribution.

If it does not, the sensor-locality error is real but not the final blocker; transport/source forward misspecification remains.

## 4. Why the immediate diagnostic should not train SBI yet

A neural ratio estimator would introduce architecture, optimization and calibration failure modes before the physical source-forward family itself has been shown to carry transferable information.

The immediate test should therefore use a fixed, non-trained, multivariate proper scoring rule on simulator ensembles.

The reference uses the **energy score**.

For one observed complete sequence `y` and an ensemble of `M` coherent transport realizations `X_m` for candidate source `s`,

`ES_s(y) = mean_m ||X_m-y||_RMS - 0.5 * mean_{m,n} ||X_m-X_n||_RMS`.

Lower is better.

Important properties for this diagnostic:

- the full chronological sequence is one multivariate object;
- no independence assumption is made over the ~80 within-stop samples or across source-update contexts;
- each transport member must be a coherent physical forward realization over the evaluated time segment;
- ensemble spread is credited through the second energy-score term rather than treating the closest member as truth;
- there is no learned temperature/blend/House threshold.

Raw physical ppm is the normative score space.  No result-dependent feature transform is allowed.

Tiny reconstructed negatives are projected to zero only when they lie within the already source-proven deconvolution serialization bound; larger negatives are an error.

Reference:

`experiments/cg_pc_ctt/pf_dei_runlevel_energy_reference.py`

## 5. Source-independent absolute null

For geometry prior `q0(s)` and transport nuisance weights `w_m`, define the prior-predictive source-independent ensemble mixture with weights

`q0(s) * w_m`.

Its energy score is `ES_null(y)`.

For a source selected from an earlier prefix, held-out absolute gain is

`G_abs = ES_null(y_holdout) - ES_selected(y_holdout)`.

Positive is better than the source-independent prior-predictive null.

This null does not know the true source and uses exactly the same GADEN physical forward simulations.

## 6. Forward-chaining source transfer without context independence

Do not return to leave-one-context multiplication.

Use a single chronological run and deterministic blocked forward chaining.  Default diagnostic partition: five equal-duration/sample-count chronological bins, snapped only as required to keep complete sample records.

For split `k`:

- training prefix = all observations from run start through bin `k`;
- heldout segment = the immediately following non-overlapping bin;
- select the source with minimum prefix energy score;
- score that selected source on the heldout segment;
- report heldout absolute gain versus the source-independent null;
- report rival margin: minimum rival heldout score minus selected-source heldout score;
- report heldout rank of the prefix-selected source.

No true source is used.

Per-run diagnostic summary is frozen before observed source-evidence results:

`predictive_pass = mean(heldout absolute gain) > 0 AND mean(heldout rival margin) > 0`.

This is deliberately a mechanism/adequacy criterion, not the final localization GO endpoint.

Aggregate actionability for proceeding to a learned SBI model requires:

- at least 20/30 runs predictive-pass;
- at least 5/10 in each House;
- candidate permutation invariance;
- source-independent null live;
- no House/seed-specific threshold or score rescaling.

If this fixed non-trained source-forward diagnostic cannot carry source evidence, training a neural SBI model is not authorized merely to fit around the failure.

## 7. Correct A1/A2 parity contract

For the same historical run:

### A1 canonical ideal arm

Observed sequence:

`C_hat(t)` from exact truth-blind sensor inversion.

Candidate ensemble:

`C_{s,m}(t)` from native GADEN physical forward.

### A2 correctly modelled native arm

Observed sequence:

historical `M(t)`.

Candidate ensemble:

`T(C_{s,m})(t)` from the exact native persistent sensor.

Before applying the normative source score, both A2 observed and A2 candidate sequences are canonicalized through the same source-proven inverse `T^{-1}` on the common recoverable interval.

Thus A2 canonical source scores must equal A1 source scores to the propagated numerical/serialization tolerance.

Required contract:

- source-score max absolute difference <= precomputed numerical/serialization bound propagated to the chosen sequence score;
- identical selected source/rank order except exact numerical ties;
- identical source-independent null score within the same bound.

A2 parity is an implementation test, not a performance target.

## 8. Decision tree after the 30-run physical source-forward diagnostic

### Case P — physical source-forward becomes adequate

If >=20/30 and every House >=5/10 pass:

`PHYSICAL_RUNLEVEL_SOURCE_FORWARD_ACTIONABLE = YES`.

Then the previous observation-locality/frequency representation is the primary identified blocker.  A learned run-prefix SBI/NRE may be justified as a compact online approximation of the already demonstrated physical source evidence.

Do not yet claim localization improvement.

### Case T — physical source-forward remains inadequate

If <20/30 or a House <5/10:

`FINITE_TRANSPORT_OR_SOURCE_FORWARD_STILL_INSUFFICIENT = YES`.

Do not tune the energy score, source grid, House thresholds or sensor model from this result.  Proceed directly to a pre-frozen, source-independent physics-randomized GADEN transport-family expansion.  If broadening physics restores adequacy, the finite transport family is the blocker.

### Case I — A1/A2 parity fails

`RUNLEVEL_INFERENCE_OPERATOR_NOT_QUALIFIED`.

Fix implementation/canonicalization before interpreting transport.

## 9. Performance remains closed

No true source/localization error is opened in this diagnostic.

Only after an adequate native-sensor-aware source model is frozen may a separate task test the existing development GO endpoint:

- pooled expected-location error improvement >=10%;
- >=20/30 paired improvements;
- no House pooled degradation >5%;
- zero new false-confident collapse;
- runtime contracts pass.
