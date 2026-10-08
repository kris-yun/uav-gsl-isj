# W0C Stage-0 HOLD review and next decision — 2026-10-07

## Accepted verdict

Codex result is accepted as:

`W0C_STAGE0_NO_CLEAN_BASE_HOLD`

The causal matched-error hypothesis has **not** been tested.

Frozen result:
- 64 existing baseline runs checked;
- 16 House×wind×gas×source cells;
- only 2 individual realizations passed;
- 0 cells passed all 4 realizations;
- new GADEN runs = 0;
- perturbations generated = 0.

This is a prerequisite failure, not evidence for or against task-anisotropic wind error.

Existing verdicts remain:
- R0C1 STOP
- R0D HOLD
- P0 STOP
- W0-PRE/PRE2 exploratory only

## Important methodological correction

The V1 one-sided edge screen was correctly rejected because H02-WD has near-zero net horizontal wind, so a mean-wind-selected edge can miss large mass on other sides.

The V2 all-side screen is the authoritative frozen Stage-0 gate.

Do not:
- shorten 100–700 s post hoc;
- relax 5%/10%;
- select the two favorable runs;
- move sources inside the old House after seeing failure;
- pad the existing wind field and call it oracle.

## Interpretation of the failure

The existing House datasets were built for earlier GSL experiments, not for the new causal transport-sensitivity test.

The R0C source contract controlled local obstacle/floor/ceiling clearance, but it did not control **transport-path / domain support**.

Therefore House H01/H02 should no longer be assumed to be clean causal environments for W0C.

A second caution:
the V2 boundary proxy uses the union of the outer 3 rows/columns of a 32×32 footprint.
That border occupies 348/1024 ≈ 34.0% of the footprint cells.
Requiring <=5% mean mass in this large border is intentionally conservative.
Failure therefore means “clean truncation risk cannot be excluded under the frozen protocol”, not “34–84% of physical plume mass definitely left the domain”.

Do not weaken the existing W0C gate. Instead design a fresh benchmark whose support is guaranteed by construction.

## Recommended next route

### Do not expand old House as the main repair

Expanding H01/H02 would require a physically valid expanded oracle wind field, source requalification and new plume baselines.
That effort has little paper value because House is not the target lakeshore scene.

### Use a two-level confirmation strategy

1. **M0 clean-support mechanism box** — cheap causal screening
   - simple large 3D domain;
   - analytically controlled base wind / vertical shear;
   - source and observation ROI fully inside an inner analysis region;
   - explicit outer simulation guard band;
   - no CFD required;
   - same source/gas/RNG under matched-RMSE wind perturbations;
   - purpose: decide whether task-anisotropic transport error exists at all.

2. **FSR pilot** — lakeshore confirmation
   - only if M0 passes;
   - real FSR geometry;
   - controlled literature-supported CFD forcing;
   - source placement and domain extent designed with transport support from the start;
   - repeat only the perturbation contrasts that survive M0.

This preserves FSR as the main paper-specific benchmark while preventing the full CFD build from being used to test a hypothesis that may still fail.

## Key benchmark-design change: guard-domain architecture

For every future causal benchmark distinguish:

- **simulation domain**: larger physical domain where wind/plume evolve;
- **analysis ROI**: inner region where source candidates, UAV route and GSL metrics are evaluated;
- **guard band**: buffer between analysis ROI and simulation boundary.

Qualification is then based on the plume remaining well supported inside the *simulation* domain while all task scoring remains in the ROI.

This is cleaner than trying to infer truncation from a small 32×32 task map whose edge band occupies a large fraction of the area.

## Public-data role

No public dataset can replace the matched counterfactual causal gate, because public data do not provide the same source/gas/RNG under two deliberately matched wind errors.

Use public data later for external validation:
- Merced / PG&E / Blackpool: real controlled-release UAV GSL;
- Lagoon Pingo / WiscoDISCO: water/shoreline meteorology and transport realism.

## Immediate actions

1. Push the local `codex/w0c-matched-error-20261007` branch for provenance; do not continue that branch scientifically.
2. Freeze `W0C_STAGE0_NO_CLEAN_BASE_HOLD` in the handoff record.
3. Design M0 clean-support mechanism box.
4. In parallel, continue FSR execution preflight/mesh work, but do not run a full scientific matrix yet.
5. Pro later reviews whether M0+FSR is the strongest route or whether another first-paper hypothesis should replace it.
