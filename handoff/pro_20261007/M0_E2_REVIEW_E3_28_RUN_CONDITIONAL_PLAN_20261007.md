# M0 E2 independent audit and conditional E3 final 28-run plan

Date: 2026-10-07 (user local; evidence sealed around 2026-10-08 UTC).

## E2 independent review verdict

**M0_E2_CRN_SENTINEL_QUALIFIED — confirmed.**

Source: user-submitted `M0_E2_CRN_SENTINEL_QUALIFIED_FULL_EVIDENCE_20261007.zip`, preserved in private ChatGPT Library `/UAV_GSL_PRO_HANDOFF_20261007/`.

A separate Linux extraction verified:
- outer ZIP CRC PASS (62 members);
- archive `verify_evidence_package.py` PASS, R0 freeze 39 files, 58 execution evidence files;
- `analyze_e2_clock_serialization_erratum.py`: M0_E2_CRN_SENTINEL_QUALIFIED, exactly 4 wrong-wind runs;
- unchanged `verify_e2_independent.py`: PASS, 1,620 native files, 39 frozen files, 10,200 concentration parity queries;
- five-way U0-versus-A/B paired clock, emission count, filament order, sigma-age, 1000-entry Gaussian table/call assignment certificate; all PASS;
- six-face containment, 3-sigma outlet margin >=6.622976970672608 m, zero-exit/delete control-flow certificate PASS;
- all 4 actual native wind-field readbacks match frozen hashes and dual-volume matched vector RMSE;
- 8 U0 E1 baseline + 4 E2 sentinel runs = 12/40 total, leaving exactly 28.

An initial `M0_E2_PREREQUISITE_HOLD` arose from an **audit code bug**, not a physical/runtime failure. The original analyzer compared a 9-significant-digit native TSV time string to a full-precision float64 representation of the same float32 clock. The corrected audit preserves byte-identical cross-arm clock comparison and compares native values at float32 representation, with no added tolerance. Old analyzer, old false HOLD, code diff/hash, independent unchanged verifier and Linux replay are retained.

**Scientific conclusion remains NOT_TESTED.** The observed single S0/r1 forward QC (A_on D_F 0.3574 vs A_off 0; A_on D_Y 0.1194 vs A_off 0) is descriptive only. No valid LORO posterior for wrong-wind arms until all 40 run library exists; no post-hoc favorable direction or frozen gate revision.

## E3 — exact final 28 runs, not a larger search

Execution is appropriate on a **fresh explicit user instruction** and must use a *separate execution authorization manifest*, not mutate R0's 40-row runlist (where launch_authorized=false is immutable evidence).

Already completed:
- 8 `U0` baseline IDs (all sources × 4 seeds);
- 4 wrong-wind sentinel IDs S0/r01:
  - `m0r0_A_on_S0_r01`
  - `m0r0_A_off_S0_r01`
  - `m0r0_B_shear_S0_r01`
  - `m0r0_B_speed_S0_r01`

The remaining 28 are exactly the original 40-runlist minus these 12:

```text
m0r0_A_on_S0_r02
m0r0_A_on_S0_r03
m0r0_A_on_S0_r04
m0r0_A_on_S1_r01
m0r0_A_on_S1_r02
m0r0_A_on_S1_r03
m0r0_A_on_S1_r04
m0r0_A_off_S0_r02
m0r0_A_off_S0_r03
m0r0_A_off_S0_r04
m0r0_A_off_S1_r01
m0r0_A_off_S1_r02
m0r0_A_off_S1_r03
m0r0_A_off_S1_r04
m0r0_B_shear_S0_r02
m0r0_B_shear_S0_r03
m0r0_B_shear_S0_r04
m0r0_B_shear_S1_r01
m0r0_B_shear_S1_r02
m0r0_B_shear_S1_r03
m0r0_B_shear_S1_r04
m0r0_B_speed_S0_r02
m0r0_B_speed_S0_r03
m0r0_B_speed_S0_r04
m0r0_B_speed_S1_r01
m0r0_B_speed_S1_r02
m0r0_B_speed_S1_r03
m0r0_B_speed_S1_r04
```

## E3 execution prerequisites

Before any additional run:
1. Preserve R0 39 frozen design files, E1 8 baseline native results, E2 four sentinel native results (with SHA/manifest).
2. Check source/generator/libgaden/decoder/actual asset hashes and original project/YAML path; do not use defective historical ROS parameter path.
3. Verify the exact 28 allowlisted run IDs, all 28 result leaves previously absent, no overwrite, source/gas/seed/route/time/RNG metadata identical where frozen.
4. Native E0 wind readback; physical wind admissibility and both ROI + Free-domain matched RMSE, unchanged.
5. Runtime resource preflight (disk and RAM, output budget) and isolated output roots.

Execute only the 28 fixed run IDs, in frozen order or deterministic runlist ordering. After each run validate clock/record indices, paired CRN assignments, source/filament birth order and sigma-age, six-face support and zero-deletion invariant, direct native sampling parity, actual wind hash, output manifest. Any failure -> prerequisite HOLD; STOP remaining runs. No partial-science verdict. Do not retry/reseed/patch automatically.

## After 40/40 legal runs, run frozen evaluation

Oracle observations **must always** be the fixed `U0` route observations `y[s,r]`. Wrong-wind simulations provide predictions only. Do not substitute wrong-wind y as truth.

Build inference candidate libraries at each fold holding out the **same seed r from both sources and all wind arms**:
- `HIT_FORWARD` Bernoulli hit probabilities Jeffreys smoothing, frozen 0.1 ppm threshold;
- `LOG_GAUSSIAN` with frozen log1p(ppm) variance floor;
- `WRONG_MODEL_BMA` as prior-art comparator with 4 wrong-wind models, **never as primary-gate rescue**.

Check 2 sources × 4 seeds × 2 matched-error pairs × two likelihood families, with preregistered gates exactly as R0:
- For a single pair, one common direction across both sources/families/forward+sensor damage;
- signed per-seed pair ΔD_F >=0.10, ΔD_Y>=0.10, ΔBrier>=0.10 **for both inference families** and worse arm ΔBrier vs U0>=0.05;
- same-seed intersection ≥3 of 4 for **each source**, no selecting different seeds per metric;
- matched global and ROI wind error, all containment/physical/parity/RNG qualifications;
- no pseudo-independent 8-sample significance; only 4 master seed blocks.
- report full per-source, per-seed, per-arm table including harm/rescue and sign reversals and all auxiliary outputs.
- Only one confirmed pair meeting both sources/two likelihoods already qualifies M0_PASS according to frozen `M0_GATE_CONTRACT.json`. Both pair pass -> TWO_PAIR tier. Do not alter contract for a specific result.

**Verdict logic**:
- `M0_PASS`: >=1 frozen pair full common-direction replicated gate (FSR pilot only; no PRIMARY_GO);
- `M0_PARTIAL_HOLD`: limited repeatable source effect/metric-chain break/split directions;
- `M0_STOP`: 40/40 qualified but no reproducible material source-posterior contrast;
- `M0_PREREQUISITE_HOLD`: any missing/failed qualifying run or audit.

STOP automatically at the verdict. NO neural learning, no extra source/seed/horizon/route, no public dataset fitting. FSR mainline proceeds **independently** and is not blocked by M0 STOP.

## Scope of this document

This is an audit + execution plan, not a claim that E3 was run. It does not itself grant an external runner execution authority. The user should explicitly authorize E3 in their Codex chat, and Codex must form a fresh allowlist.
