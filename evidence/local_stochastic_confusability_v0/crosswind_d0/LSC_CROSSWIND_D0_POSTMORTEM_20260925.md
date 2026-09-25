# LSC Cross-Wind D0 Postmortem — Why the Mainline Failed

Date: 2026-09-25

Frozen scientific decision remains:
`LSC_CROSSWIND_D0_FAIL_STOP_MAINLINE_GENERALITY`.

This document is a post-hoc mechanism diagnosis only. It does not change thresholds, add seeds, rescue G1, or reopen the LSC mainline.

## 1. Integrity

The pre-data infrastructure patch only:
- selected the frozen first eight D1R W0 replicates required by the protocol;
- made SciPy Spearman-return handling compatible with the VM;
- added execution/package scripts.

No W1/W2 plume outcome informed those changes.

Therefore the cross-wind failure should be treated as scientific evidence rather than an execution artifact.

## 2. What actually failed

G2, G3 and G4 passed:
- every new wind/direction retained a negative distinguishability-vs-confusion sign;
- hard edges were generally harder than easy edges;
- train-half energy-distance ordering was reproducible across realization halves.

Only G1 failed:
- pooled direction A rho = -0.4631 instead of <= -0.50;
- pooled direction B rho = -0.3569 instead of <= -0.50.

This is not best interpreted as 'LSC does not exist'.

It means the frozen **environment-independent generality claim** was not supported.

## 3. Strong post-hoc diagnostic: source-confusion geometry changes with wind operator

Average the A/B energy estimates for each of the same ten source-neighbor edges.

Cross-wind edge-ordering Spearman:
- W0 `3,5-1_slow` vs W1 `3,5-1_fast`: +0.612;
- W0 vs W2 `4,5-3_slow`: -0.430;
- W1 vs W2: -0.539.

Thus changing only fast/slow within the same `3,5-1` flow family preserves substantial edge ordering, whereas moving to the `4,5-3` flow topology reverses which source pairs are distinguishable.

The fresh-error ordering shows the same qualitative pattern.

## 4. Wind inventory is consistent with an anisotropy rotation

House02 global speed-weighted mean wind directions from the frozen inventory are approximately:
- W0 `3,5-1_slow`: -120.9 deg;
- W1 `3,5-1_fast`: -118.5 deg;
- W2 `4,5-3_slow`: +159.6 deg.

W0 and W1 share essentially the same global direction while W2 changes the transport orientation by roughly 80 degrees modulo 180.

On the frozen 2x4 source panel there are horizontal x-edges and vertical y-edges.

A/B-averaged diagnostic:

W0:
- x-edge energy 13.05, fresh error 0.0625;
- y-edge energy 6.56, fresh error 0.3125.

W1:
- x-edge energy 12.49, fresh error 0.1458;
- y-edge energy 7.27, fresh error 0.4063.

W2:
- x-edge energy 11.52, fresh error 0.3542;
- y-edge energy 11.77, fresh error 0.1563.

The hard/easy orientation therefore flips under the W2 transport topology.

This is strongly consistent with wind-aligned anisotropic source identifiability: source offsets more transverse to transport can be easier to distinguish than offsets more aligned with transport.

The inventory direction is a global diagnostic, not proof of the local flow direction at every source/probe, so this physical interpretation remains a hypothesis to be checked against local 3D wind fields.

## 5. This is not primarily a sample-noise explanation

The new-wind experiment is small (10 edges/wind; four fresh realizations/source/direction), and binary pair errors are quantized in steps of 0.125. This limits correlation precision.

However, limited power is not enough to explain the failure:
- energy split reproducibility is high (W1 0.952, W2 0.770);
- fresh-error A/B ordering is itself reasonably reproducible, especially W2;
- the same edge ordering reverses systematically between the `3,5-1` and `4,5-3` wind families.

Therefore adding seeds after reveal would not address the central scientific mismatch and is correctly forbidden by the frozen protocol.

## 6. Root mathematical diagnosis

The D1R/W0 discovery implicitly studied the environment-conditioned statistical experiment

  P_E(Y | S=s, M),

not an environment-free source signature.

The local distinguishability geometry is

  d_E(s_i,s_j) = D(P_E(Y|s_i), P_E(Y|s_j)).

The cross-wind data show that d_E depends materially on E.

There is no evidence for one fixed source-confusion geometry d(s_i,s_j) that should survive arbitrary physical wind/operator changes.

## 7. Why this pattern recurs across the project

Several historical routes first found a real conditional signal and then failed when the conditioning distribution changed:
- M4: forward/field signal did not transfer into stable wind-response/source-ranking mechanism;
- Green/operator routes: one realization could rank the truth well while another did not;
- multi-view/LSC: strong within-environment stochastic structure did not become a cross-environment invariant.

The recurring error is therefore not simply 'the model is too weak'.

It is a scientific-object error:

> environment-conditioned regularities have repeatedly been promoted as candidate invariants before operator variation was included in the discovery gate.

## 8. New governance rule

From now on, no main-innovation candidate may advance from a single-wind discovery, regardless of how strong its within-wind signal is.

Every first mechanism gate must include at least:
- independent plume realizations;
- at least two genuinely different transport topologies/operators, not merely fast/slow scaling;
- task-relevant source proper score or source-pair odds;
- explicit environment/wind conditioning when the proposed object is not claimed invariant.

Field MSE, covariance fit, source-profile stability, or within-wind rank alone cannot promote a mainline.

## 9. Scientific consequence

LSC as an environment-invariant main mechanism is STOP.

The useful surviving fact is different:

> the inverse source-identifiability geometry is itself an environment-conditioned object that rotates/deforms with the transport operator.

This supports future zero-simulation work on **environment-conditioned source-contrast/operator identifiability**, but it does not authorize a new algorithm or new GADEN acquisition.

Any successor route must predict the change of d_E with E rather than assume d_E is fixed.