# Next Codex experiment directive — FSR mainline + M0 bounded auxiliary
Date: 2026-10-07 (user-facing task continuity; FSR R9.3 audit sealed 2026-10-08 UTC)
Status: **execution plan**, not scientific PASS or authorization to run full CFD/GADEN.

## Non-negotiable science target
First-paper endpoint is UAV localization of hypothetical industrial-facility gas releases in realistic lakeshore terrain, with source coordinate and 2D posterior map as primary outputs. Plume transport/path, shape and concentration are secondary physical state targets; specific gas type is not prematurely fixed beyond per-experiment frozen simulator parameters.

FSR (枫树岭水库) is the MAIN real-terrain, controlled-forcing self-built benchmark. M0 is a small, non-lakeshore, idealized mechanism screen. M0 failure does **not** cancel FSR dataset construction.

## Grounded current state
- M0 E0 and 8 U0 E1 runs qualified, source-blind route and LORO correct 8/8. No wrong-wind experiment yet. Four E2 S0/r01 wrong-wind runs are the only immediate M0 next step; all 28 others remain unauthorized.
- FSR R8 real terrain, water/land and local vertical frame geometry anchored.
- FSR R9.3 verdict **R9_3_HOLD_ALTERNATIVE_MESH_LOCAL_DETERMINANT_AND_FULL_DOMAIN_BUDGET**. B alternative local S2 checkMesh PASS at 40,960 cells, B S4 fails four determinant cells. A sigma fails both. Local mesh has bottom 1,024 real R8 triangles and 40 vertical prisms. This is NOT a full-domain CFD-ready mesh.
- R9.3 original full domain needs ~1.47–1.63 million cells for 29 layers at native triangular terrain, compared with existing 250k-cell contract. 40 layer ~2.03–2.25 million. Four-case 61 snapshot payload for basic U/T/p_rgh alone ~19.4 GiB, excluding other fields. VM memory/IO full CFD not qualified.
- Root causes include severe S4 slope 66–69 degrees at four determinant failures and skinny bottom triangles created by rectangular crop boundary; blind global refinement or merely repairing the four cells cannot solve full-domain resource issue.

## FSR Track F0 — minimum physically credible local lake-shore pilot (highest priority)

**F0 is a design+preflight deliverable, no CFD/GADEN scientific runs. Do not mistake this for unlimited R9.4/R9.5 meshing iteration.**

### F0.1 Select a *scientifically* justified local lake-shore domain
Select a **contiguous true-coordinate reservoir shore segment** from frozen R8 data. Choose by predeclared geomorphology:
- a real water patch, real shoreline and adjacent land slope;
- a plausible hypothetical industrial facility source region on land;
- enough lake fetch and inland/upstream/downstream margins to study surface contrast;
- future source positions and source-blind UAV analysis ROI inside a larger simulation domain;
- physical outflow and inflow boundary positions justified by advective travel length and sensor-time horizon.

The 480×480 m S2 local mesh is a candidate **only if** the geometry, buoyant-flow fetch and analysis ROI support tests pass. S2 local checkMesh PASS is not sufficient. S4 shall remain a difficult geometry stress-test, not be silently discarded to improve science outcomes. Do not choose a site solely because its mesh passed.

R8 frozen scientific geometry may be cropped for a **new explicitly named local-pilot benchmark** with provenance retained; do not replace/modify the original R8/R9.3 domain and STOP record. Any local-pilot analysis horizon differs from the eventual main benchmark and must be frozen before plume results.

### F0.2 Pre-register physical and resource contracts **before** new full meshing
Produce one compact case specification covering:
- shoreline extent coordinates in R8 system, original raw triangle/land/water provenance and physical reason for choice;
- source legality, equal-height candidate source grid, source included in candidate posterior domain;
- analysis ROI and actual outer simulation boundary/guard, wind inflow/outflow/wall/top patches;
- geometry fidelity (water elevation/shoreline/land elevations/boundary drift), no geomorphological fudging;
- physical vertical resolution at UAV/sensor heights, AGL measurement, near-shore horizontal resolution, plan for nonorthogonality/determinant/sliver triangles;
- exactly two costed mesh designs: (i) direct geometry-preserving hybrid/locally refined version informed by R9.3 B; (ii) separate, physically qualified coarsening/variable-layer design whose geomorphology distortion is bounded. Neither may zero-pad winds or invent terrain;
- exact cells, RAM, disk, CFD solver run-time and snapshots. If >250k original cap is needed, request **new user authorization**; do not silently raise it. Treat available RAM, not host total, as execution constraint;
- solver selection and thermal physics (verify installed OpenFOAM version and solver before claiming availability).

**Compute sanity**: 13,773 land triangles already lie wholly in S2 original nearshore ROI. With a 17-layer lower-atmosphere assumption this land-only ROI is ~234k cells *before water, outer domain or upper air*. Hence “simplify far field” alone cannot fulfill the old 250k hard cap.

### F0.3 Engineering qualification
Evaluate at most **two predeclared complete small-domain mesh candidate designs** (not 2 local patches masquerading as full CFD). The candidate may reuse R9.3 B and repair determinant/concavity via geometry-preserving local topology or hybrid elements.

Mandatory checks:
- full native checkMesh, positive volumes, determinant>=original frozen tolerance or explicit new pilot contract, zero negative ground/open-face clearances, patch integrity, closed watertight boundaries, bottom terrain lineage, no sliver-related singularities;
- independent geometry error table (shoreline, land, water, side boundary, AGL);
- no severe solver-unusable nonorth, singular slivers or topology issues;
- actual free RAM/disk budget for 3D *buoyant* flow, including thermodynamics, turbulence closure if used, and outputs.

If candidates fail, publish FSR_LOCAL_PILOT_MESH_HOLD + quantified reasons and propose one physically motivated alternative. No arbitrary meshQuality relaxation or repeated parameter lottery.
**No official CFD simulation until complete pilot case and runtime qualification PASS.**

## FSR Track F1 — first physically meaningful wind comparisons (only after F0 passes)
Do not run all original four cases or 61-field/snapshot matrix.

First two controlled cases:
- identical **background inflow**, top stratification and turbulence, geometry/roughness and boundary specification;
- a neutral water-land surface-temperature difference reference `DeltaT=0`;
- one physically plausible, pre-registered nonzero water-land surface contrast `DeltaT != 0`, bounded by published conditions or appropriately labeled remote-sensing proxies; temperature and turbulence BCs must be thermodynamically consistent.

If F1 passes, later add opposite-sign contrast and altered background wind as separate controlled factors. **Do not claim a genuine lake-breeze front or wind reversal solely because DeltaT changed sign.** Short/finite local-domain thermally modified flow is not proof of a mesoscale lake breeze.

Before GADEN test:
- numerical convergence/continuity/Courant, physically sane 3D wind at multiple heights;
- water-land sensible-heat and momentum boundary semantics verified;
- nearshore profiles/vertical shear and alongshore velocities;
- neutral-vs-thermal difference attributable to controlled surface contrast, not changed inflow or crop;
- domain-size/sensitivity check or justified boundary margin against artificial upstream/downstream effects;
- frozen field/time export for GADEN and provenance.

If solver or budget FAIL => FSR_WIND_PREFLIGHT_HOLD. No gas simulations.

## FSR Track F2 — minimal GADEN source benchmark (only after F1 PASS)
- 2 fixed hypothetical industrial source positions, known coordinates, equal release/gas and controlled height unless scientifically motivated to vary;
- 2 wind regimes (neutral and thermal) × 2–4 independent gas realizations;
- fixed source-blind, physically feasible UAV sampling route;
- separate simulation domain and analysis ROI; record physical outflow flux and boundary effects; **do not blindly require zero exit at a real open outflow** (M0 zero-deletion criterion is a clean-box gate, not a general lake-shore flow law);
- publish native gas observations, full trajectories, true source coordinates, wind export, meteorology metadata, source releases and field lineage.

Metrics: 2D source posterior and true-source ranking/error, source prior cell support, Top1, plume center/path/front/shape and concentration as secondary, with declared short prediction horizon and no unverified forecast claims.

Comparator readiness: PMFS native 2D baseline, simple Gaussian/Bayesian inverse and 3D wind/transport oracle only as upper bound. Same observation route, candidate grid, prior and compute budget. No early neural/world-model claims.

## M0 bounded auxiliary Track M-E2 (may run in separate worktree in parallel)
Authorized next step **on explicit user/Codex instruction**:
four pre-registered wrong-wind rows
- m0r0_A_on_S0_r01
- m0r0_A_off_S0_r01
- m0r0_B_shear_S0_r01
- m0r0_B_speed_S0_r01
Reference m0r0_U0_S0_r01 from E1.

Read handoff/pro_20261007/M0_E0_E1_REVIEW_AND_E2_SENTINEL_AUTHORIZATION_PLAN_20261007.md.
Check exact effective native YAML, independent readback, cross-wind CRN assignment/clock/index/sigma, all-side support, zero deletion and hash. Preserve frozen 39-file R0 and 8 E1 runs, use separate authorization manifest (do not edit frozen preview runlist).
Result E2 sentinel QUALIFIED or prerequisite HOLD. **STOP after four**; no automatic remaining 28. If E2 qualifies, seek next explicit authorization for remaining 28; no seed/threshold/model changes.

M0 decisive conclusion only after all 40 valid runs and both inference families pass/fail the frozen damage gate. M0 PASS only permits FSR mechanism check and algorithm invention, not PRIMARY_GO. M0 STOP does not stop the independent FSR dataset.

## Time and stop controls
Parallel independent worktrees/branches, don't overwrite source datasets, protected R8 geometry or R9.3 logs. No CFD/GADEN changes to existing experimental evidence.
Priority: 70–80% research/engineering effort FSR F0/F1; M0 bounded 20–30%.
Stop on invalid domain/mesh/resources; no retries, expanded loops or automatic patching after a frozen failure.
Deliver small report with exact lineage and separate status tags:
- FSR_LOCAL_PILOT_DESIGN_ACCEPTED / FSR_LOCAL_PILOT_HOLD
- M0_E2_CRN_SENTINEL_QUALIFIED / M0_E2_PREREQUISITE_HOLD

The reviewer must explicitly approve first scientific CFD, and separately approve post-E2 remainder.
