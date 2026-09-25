# SPX-G0 — Source-Panel × Probe-Protocol Crossed Audit

Date: 2026-09-25

Status: **ZERO-PLUME / CAUSAL-DISAMBIGUATION AUDIT — NOT A NEW MAIN-INNOVATION TEST**

Upstream frozen results:
- JTD E2 = STOP;
- NPG G0 = STOP.

## 1. Why this audit is necessary

G1A and E2 H02 `3,5-1_slow` differ in at least two major factors:
1. source panel / source locations;
2. 30-probe observation protocol.

Therefore the observed reversal of FULL-vs-BP/MBD cannot yet be causally attributed to source/transport regime alone.

Both projects retained full concentration cubes, so this confound can be crossed without any new plume simulation.

## 2. Fixed physical environment

House02 only.
Wind only: `3,5-1_slow`.
Same ten time indices: 100,150,...,550.
Same z = 0.20 m.

No other wind or House is used.

## 3. Source regimes

### CENTRAL
the frozen 168-source G1A panel, 16 realizations/source.

### OFFSTRIP
the six E2 H02 `3,5-1_slow` sources, 16 already-open realizations/source:
- 12 E2 references;
- 4 E2 fresh targets, now historical/open for this audit.

No source selection from outcomes.

## 4. Probe protocols

### P_G1A
the exact 30-probe Gate1A observation protocol from `gate1a_contract.json`.

### P_E2
the exact 30-probe House02 E1/E2 observation protocol from `E1_HOUSE_PROBE_CONTRACTS.tsv`.

## 5. Required 2×2 crossed extraction

Re-extract every available raw cube using BOTH probe protocols:

1. CENTRAL × P_G1A  (historical G1A observation protocol)
2. CENTRAL × P_E2   (new cross-extraction)
3. OFFSTRIP × P_G1A (new cross-extraction)
4. OFFSTRIP × P_E2  (historical E2 observation protocol)

Verify exact equality against historical tensors for cells 1 and 4 wherever applicable.

0 new plume.

## 6. Avoid candidate-count confounding

Do NOT compare 168-way and 6-way normalized posteriors as the primary endpoint.

Primary units are fixed 0.3 m adjacent SOURCE PAIRS and two-class likelihood ratios.

CENTRAL primary pairs:
- the 84 disjoint horizontal nearest-neighbor pairs already frozen in NPG-G0.

OFFSTRIP primary pairs:
- the three frozen E1/E2 source pairs.

For each pair, candidate support is only the two pair members.

Thus the primary comparison is independent of 168-vs-6 posterior normalization.

## 7. Frozen model family

For each source pair × probe protocol:
- four deterministic folds;
- 12 reference realizations/source and 4 held-out realizations/source per fold;
- five two-time blocks;
- StandardScaler fit on pair references only;
- PCA=2/block fit on pair references only;
- source-specific FULL OAS Gaussian;
- BLOCK-PRODUCT;
- MATCHED-BLOCK-DIAG built from FULL covariance;
- same jitter rule as G1A/E2.

No SHUFFLED null is needed for the primary crossed diagnosis.
No model tuning beyond the frozen preprocessing/model contract.

## 8. Primary pairwise utility quantities

For each held-out realization from true source s against partner n:

`margin_MODEL = log p_MODEL(y|s) - log p_MODEL(y|n)`

and proper two-class truth NLL after uniform two-source normalization.

Define:
- `delta_BP = NLL_BP - NLL_FULL`;
- `delta_MBD = NLL_MBD - NLL_FULL`.

Positive means FULL cross-block modeling helps.

Aggregate first within realization, then direction/source, then pair.

## 9. Crossed causal contrasts

For every CENTRAL pair, because both probe protocols are available on the SAME raw cubes, compute paired probe contrast:

`probe_effect = delta(P_E2) - delta(P_G1A)`.

For every OFFSTRIP pair compute the same paired probe contrast.

Primary qualitative diagnosis uses BOTH delta_BP and delta_MBD.

## 10. Frozen interpretation labels

Return exactly one:

### `SPX_G0_SOURCE_REGIME_DOMINANT`
if CENTRAL pair-mean delta remains predominantly positive under both probe protocols AND all/most OFFSTRIP pairs remain non-positive under both probe protocols, while paired probe switching does not reverse the regime-level sign pattern.

Operational thresholds:
- for each comparator separately, >=60% of CENTRAL pairs positive under both P_G1A and P_E2;
- at least 2/3 OFFSTRIP pairs non-positive under both probes;
- median CENTRAL probe_effect magnitude is smaller than the CENTRAL-vs-OFFSTRIP difference in pair-mean delta.

### `SPX_G0_PROBE_PROTOCOL_DOMINANT`
if pairwise utility follows probe protocol more strongly than source regime:
- switching probes reverses or materially changes sign for >=40% of CENTRAL pairs;
- and OFFSTRIP pair signs move in the same direction;
- and probe_effect magnitude exceeds the source-regime contrast.

### `SPX_G0_SOURCE_PROBE_INTERACTION`
if neither main-factor label fits and the effect depends on the source×probe combination.

### `SPX_G0_DATA_CONTRACT_STOP`
if required raw cubes or exact cross-extraction cannot be verified.

These are diagnosis labels, NOT mainline GO/HOLD/STOP decisions.

## 11. Robustness outputs

Report:
- pair-level delta_BP/delta_MBD under all four cells;
- sign agreement across probes;
- Spearman correlation of pair utilities across probes for CENTRAL;
- bootstrap CI for CENTRAL median/mean paired probe effect;
- OFFSTRIP all three pair values individually;
- FULL/BP/MBD pair accuracy and Brier as diagnostics;
- source-direction asymmetry;
- heavy-tail trimmed means.

Do not use target outcomes to change pair definitions or thresholds.

## 12. Consequence

This audit decides what the NEXT scientific problem actually is.

If SOURCE_REGIME_DOMINANT:
future far-domain search may target transport-/state-dependent information gating.

If PROBE_PROTOCOL_DOMINANT:
future mainline must first solve observation/sensor-layout dependence; source-regime stories are premature.

If SOURCE_PROBE_INTERACTION:
future theory must model relational source–sensor–flow context rather than source-only or observation-only codes.

No new mother-theory candidate is authorized before SPX-G0 completes.

---

# Amendment A — after independent Pro transport audit

This amendment is authoritative and narrows SPX-G0. It does not change the zero-plume requirement.

## A1. Asset-recovery gate before any scientific scoring

Before cross-extraction, confirm that the VM/archive contains readable numerical assets, not only hashes or historical paths:

1. all required CENTRAL G1A raw concentration cubes;
2. all required OFFSTRIP E2 H02/W0 raw concentration cubes;
3. exact P_G1A and P_E2 probe contracts;
4. the actual H02/W0 wind-vector arrays used by the simulator;
5. the actual H02 occupancy array/grid and coordinate transform;
6. source xyz, probe xyz, time index, z-height and pooling metadata sufficient to reproduce both historical tensors exactly.

Produce `SPX_G0_ASSET_AUDIT.json` with:
- located path;
- bytes;
- SHA256;
- numeric shape/dtype for arrays;
- whether the asset is sufficient for cross-extraction or later physical-context computation.

If the required raw cubes or exact probe contracts are not recoverable, return:
`SPX_G0_DATA_CONTRACT_STOP`
and stop. Do not generate new plume, interpolate a substitute operator, or infer arrays from filenames.

Wind/occupancy are required to be inventoried now. They are NOT yet used to create a transport predictor in SPX-G0.

## A2. Primary scientific object is fixed to H02/W0 adjacent-pair discrimination

SPX-G0 does NOT attempt to explain all historical JTD failures.

Its primary object is only:

> under the same House02 / 3,5-1_slow physical environment, does the sign/value of FULL-vs-BP/MBD adjacent-pair discrimination follow source regime, probe protocol, or their interaction?

The three frozen OFFSTRIP 0.3 m pairs and the 84 frozen CENTRAL disjoint 0.3 m pairs remain the only primary pair units.

This is intentionally a local-neighbor problem.

The H02 W2 distant-aliasing failure and generic Gaussian overconfidence are explicitly OUT OF SCOPE for the SPX-G0 primary decision. They remain frozen postmortem facts for any later theory.

## A3. Candidate-support and prior are not allowed to confound the primary result

Primary scoring remains two-source conditional scoring for each frozen pair with uniform two-source prior.

Do not compare 168-way CENTRAL posterior scores directly with 6-way OFFSTRIP posterior scores as a causal contrast.

Full-support scores may be exported as secondary diagnostics only, separately within each panel.

## A4. Exact historical reproduction is mandatory

Before any crossed-cell scientific result is accepted:

- CENTRAL × P_G1A must reproduce the historical G1A extracted tensors for matched runs to numerical tolerance <=1e-12 absolute where serialization permits;
- OFFSTRIP × P_E2 must reproduce the historical E2 extracted tensors to the same tolerance.

If not, return `SPX_G0_DATA_CONTRACT_STOP`.

## A5. Deployment-context inventory

SPX-G0 must include a non-scoring table marking which context variables are realistically available at deployment:

- candidate/source geometry: AVAILABLE if map known;
- probe/sensor geometry: AVAILABLE;
- local onboard wind observations: POTENTIALLY AVAILABLE;
- full simulator wind field: ORACLE unless a real estimator is specified;
- occupancy/building geometry: AVAILABLE only if mapped;
- target-environment dense source stochastic bank: NOT ALLOWED as deployment context.

No later mother theory may use an ORACLE variable without an explicit realistic estimator.
