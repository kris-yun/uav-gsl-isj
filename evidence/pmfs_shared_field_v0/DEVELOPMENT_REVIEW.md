# PMFS shared whole-field evidence: development result

Decision: **DEVELOPMENT_STOP_NO_INCREMENT_BEYOND_CONTROLS**.

This is a valid OPEN method-development comparison, not an infrastructure
failure, fresh confirmation, Native PMFS closed-loop run, or a universal
refutation of robust classification.

## What was actually run

House02 / 3,5-1_slow; all CENTRAL168 sources x16 existing realizations.
Two paired probe layouts,30 probes each. Each of the60 alternative tasks
uses only the first/last frozen snapshot from one probe. Uniform168-cell
prior. Complete run IDs/seeds and cube hashes joined both layouts.

Four outer folds12/4, three inner folds8/4. Shared and independent DRO each
searched rho={0,.05,.15,.35}; nominal temperature searched {.5,1,2,4}.
All arms share reference-only positive terciles,16 nominal symbols, total
Dirichlet pseudocount1 and source support. No target-selected bin or source.

All four folds selected **shared rho=0, independent rho=0, T=1**. The proposed
shared-field predictor therefore reduces to the same smoothed nominal
ensemble. Its paired truth-log2 gain against nominal, independent DRO and
identity shuffle is exactly0; the temperature comparison differs only by
floating-point roundoff (~4e-15 bit). Source-panel sensitivity intervals for
the exact equalities are[0,0]. Identity-shuffle is vacuous at the selected
rho0; it provides no affirmative mechanism evidence.

## Same-input comparison

| method | truth NLL(bits) | Brier | top1 | mean MAP distance(m) |
|---|---:|---:|---:|---:|
| nominal ensemble |6.77806550|0.98614670|1.865699%|2.67375122|
| independent DRO |6.77806550|0.98614670|1.865699%|2.67375122|
| nominal +temperature |6.77806550|0.98614670|1.865699%|2.67375122|
| shared whole-field |6.77806550|0.98614670|1.865699%|2.67375122|
| identity-shuffled shared |6.77806550|0.98614670|1.865699%|2.67375122|

Secondary metrics cannot rescue the zero primary improvement. Inner selection
curves, including the nonzero-radius fits, are preserved. We do not force a
nonzero radius or evaluate an extra post-result model to manufacture a
shared-identity effect.

108 fitting records passed the declared saddle-gap/constraint certificate;
maximum gap1.94565e-6 nats. Independent reconstruction verified all161,280
heldout tasks per model, bin thresholds, parameter selection, histogram
probabilities, complete metrics and source bootstrap. Metric discrepancy0;
table discrepancy<=4.11e-15. Total development wall time~88 seconds excludes
implementation, packaging and independent verification.

## Delivered algorithm and evidence

`solver.py` implements the supplied conditional-entropy minimax problem with
a sparse categorical channel, exact KL-Bregman projection and independent
dual risk oracle. The mathematical method was not changed to overcome the
last candidate's single-filament closure issue. Here the sample unit is a
whole existing run.

`probability_map.py` exports the fixed168-source map from any valid two-ppm
query in the frozen protocol. The map is a robust decision distribution,
not a guaranteed calibrated posterior. It is not an installed ROS patch.
No simultaneous multi-probe trajectory or repeated-prefix multiplication
is implied. The current known-model bank is not lawful unknown-world wind
context and does not establish unfamiliar-environment or flight capability.

Every evaluated full probability map is represented losslessly by the fold,
model,protocol,symbol tables in `PROBABILITY_MAP_TABLES.npz` and run symbols
in `OBSERVATION_CODES.npz`: `Q[:,protocol,symbol]`. Row-level CSV and NPZ
contain all806,400 model x source x realization x protocol metric rows.
The ZIP includes both complete raw10x30 CENTRAL tensors; original3D cubes
remain unchanged on the VM and their hashes/run provenance are retained.

## Interpretation and stop

The reference-only selection found no reason to retain robust ambiguity in
this finite-bin,two-time,R12 development task. No incremental utility beyond
the ordinary ensemble was established. This implementation's main-innovation
claim stops. The result does not prove that all continuous or differently
specified robust methods are impossible. No successor experiment is started.

No new plume, network, H01 DEV/House03 access, old STOP rescue or bin/radius
change after result inspection. Code and original assets are preserved.
