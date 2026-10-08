# M0 R0 design review — 2026-10-07

## Verdict

**DESIGN_ACCEPTED_FOR_STAGED_EXECUTION**

The frozen design is scientifically coherent enough to proceed to runtime qualification, but execution should remain staged.

This is not M0_PASS and not PRIMARY_GO.

## What was verified

Reviewed:
- frozen scientific contract;
- domain / ROI / guard contract;
- base wind;
- two perturbation pairs;
- source and RNG contract;
- source-blind UAV route;
- inference comparators;
- machine gate;
- resource budget;
- static-design verification;
- GitHub branch at commit `742c80aa53fda6f47a2d0028b98f9c7dfae2de83`.

Independent archive hash verification:
- `python freeze_design.py --verify` -> PASS;
- 39 frozen files verified;
- status remains `M0_R0_DESIGN_FROZEN`;
- execution remains unauthorized inside the frozen package.

## Scientific strengths

1. **Correct counterfactual object**
   Observation is fixed under U0 while candidate predictions are evaluated under wrong winds. This separates forward plume damage from inference damage and avoids the invalid design where both observation and model are moved together.

2. **Real guard-domain architecture**
   Simulation domain and analysis ROI are separated. Boundary qualification uses all six simulation faces, 3-sigma support margin and zero-deletion rules rather than a mean-wind-selected task-map edge.

3. **Matched error is audited twice**
   Each perturbation pair must match vector RMSE both over the simulation Free domain and inside the ROI. This prevents the large guard from trivially diluting localized errors.

4. **Pair A is source-blind**
   The on/off intervention masks depend on the ROI / analytic-flow geometry, not true source identity or posterior. Both source candidates receive the same mask.

5. **Pair B tests structure, not just magnitude**
   Local shear destruction is compared against an equal-RMSE horizontal-speed perturbation using the same vertical support.

6. **No-leak inference**
   Leave-one-master-seed-out templates exclude the held-out seed from both candidates and every wind library.

7. **Prior art is treated as comparator**
   WRONG_MODEL_BMA is explicitly not claimed as novelty and cannot rescue the primary gate.

8. **Gate is conservative and pre-frozen**
   Same direction, same seed intersection, both sources and both inference families are required. Secondary metrics/BMA cannot rescue a failed primary gate.

## Important review notes before launch

### A. Do not launch all 40 runs at once

Recommended execution checkpoints:

**E0 — runtime-only qualification, 0 scientific runs**
- build the five native wind assets;
- native decoder readback;
- occupancy semantic readback;
- actual generator/libgaden/source hashes;
- physical + matched-RMSE audit;
- disk/RAM budget;
- output path allowlist;
- archive all argv/runtime manifests.

Failure -> prerequisite HOLD.

**E1 — only 8 U0 baseline runs**
Then stop and audit:
- all-six-face support 4/4 for both sources;
- zero deletions / 3-sigma support;
- Pair-A baseline on/off relevance;
- source-blind route detectability;
- U0 LORO inference preflight;
- concentration sampling parity;
- actual runtime/resource budget.

Any failure -> prerequisite HOLD. Do not run wrong-wind arms.

**E2 — CRN sentinel using already-budgeted intervention rows**
If E1 passes, do not immediately launch the remaining 32.
Launch the four wrong-wind arms for one pre-frozen source×seed already present in the 40-row runlist.
Use these runs only to confirm:
- actual cross-arm output clocks / record indices;
- release counts and filament ordering;
- sigma-age sequence;
- RNG call-assignment certificate;
- zero outlet deletion;
- native wind hashes/readback;
- support qualification.

These are not extra runs and must remain part of the final 32 if execution continues.

Failure -> prerequisite HOLD.
Pass -> launch the remaining 28 intervention rows.

This checkpoint does not change scientific hypotheses, thresholds, seeds or run budget; it only avoids spending all 32 runs before verifying runtime CRN.

### B. Pair-A relevance gate is acceptable only as an experimental qualification

The on/off mask is fixed before plume results, and the oracle baseline is only used to check that the intended manipulation actually intersects the transport corridor.

This must remain a **mechanism-experiment qualification**, not an input to the final GSL algorithm.
FSR/final method cannot use the true plume to define transport relevance.

### C. M0 is deliberately non-lakeshore

The open six-face box, analytical shear field and no-ground geometry are appropriate for mechanism isolation.
No future text may call M0 a lake-breeze, CFD, boundary-layer or real-UAV benchmark.

M0 PASS means only:
“the matched-error task-anisotropy phenomenon survived a clean prescribed-flow mechanism test.”

FSR is still required for lakeshore confirmation.

### D. Portable verifier issue

The frozen archive itself passes `freeze_design.py --verify`.

However, `verify_static_design.py` contains provenance checks keyed to absolute Windows paths, so an independent Linux extraction fails at the provenance-path lookup even though the archive hashes pass.

This is not a scientific-design failure, but it is a portability/reviewability issue for a future Pro/Linux reviewer.

Do **not** modify the frozen R0 directory in place.
If desired, add a separate portable archive verifier outside the frozen evidence directory or document that `freeze_design.py --verify` is the platform-independent archive check.

## Decision

Proceed only with **E0 + E1 (8 U0 baselines)**.

Do not authorize the full 32 intervention set until E1 is independently reviewed.

If E1 passes, use E2 CRN sentinel, then complete the remaining 28.

No changes to:
- source positions;
- 20–120 s scoring window;
- 0.1 ppm hit threshold;
- four seeds;
- route;
- perturbation masks;
- RMSE tolerances;
- PASS/HOLD/STOP margins.

## Possible outcomes

- baseline/runtime failure -> `M0_PREREQUISITE_HOLD`;
- all qualification passes + no task-anisotropic effect after all 40 -> `M0_STOP`;
- partial directional/material effect -> `M0_PARTIAL_HOLD`;
- at least one frozen pair fully replicates across both sources and both inference families -> `M0_PASS`, then design FSR pilot only.

No neural rescue and no public-dataset rescue after a valid M0_STOP.
