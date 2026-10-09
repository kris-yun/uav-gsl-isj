# R2 — 2025/2026 GSL failure-first screen: strong new collisions, no premature GO
Date: 2026-10-08
Objective: user's FIRST paper on UAV source-coordinate localization, with known source, 2D posterior, FSR lake terrain as future self-built benchmark. No new simulation/algorithm has been run.

## Main outcome — NO novel first-paper mechanism qualified
A strong actual PMFS failure mode was found in Kim et al. (2026) arXiv:2608.16221 (preprint, not verified peer-reviewed). Their controlled REAL indoor Experiment 1 has secondary gas accumulation outside primary flow; PMFS binarization can miss primary flow or include secondary pooling, preventing convergence (0% success, n=10); DGSE-S continual concentration + inferred wind-concentration-source conditional inference reached 100%. Experiment 2 PMFS 60%, DGSE-S 100% (n=10 each). Their paper also ran common 50 observation points and 20 trials in six GADEN domains vs PMFS, and reports costs with different hardware. This is REAL experimental failure, but their very solution **already occupies** the obvious novelty: replacing hits with continuous concentration, reconstructing intermediate wind/concentration, then source posterior. Its restriction is steady indoor single source known layout; untested lake thermally forced complex terrain is a distinct application/physics hypothesis, NOT automatically a new mechanism.
URL https://arxiv.org/html/2608.16221v1 ; source sections V-E and VI.

## Strongest model-design collision
Wang & Ma, "NeuPlume" EGUsphere **preprint** 2026 DOI 10.5194/egusphere-2026-2769:
- existing CNF latent field + diffusion prior + DPS under sparse observations, joint emission rate, effective release height, wind/turbulence and full plume; thus latent 3D field and Bayesian field UQ NOT untouched novelty.
- physical instance limited to passive near-neutral, flat, single source, no wind-direction shear, obstacle-induced recirculation or buoyant rise. Retraining new scenario library is required.
- it targets release parameters and plume field, not necessarily unknown horizontal source coordinate + mobile route GSL (do not conflate tasks).
- reviewer reports/author replies exist; this is not proven peer-reviewed acceptance.
https://egusphere.copernicus.org/preprints/2026/egusphere-2026-2769/

## Real industrial source known truth, explicitly bad windows
Daniels, Nychka, Hammerling, "A Bayesian hierarchical model for methane emission source apportionment" arXiv 2506.03395 v2 (March 2026 preprint):
- METEC realistic petroleum equipment with 337 controlled methane releases, 5 known candidate equipment sources, 10 fixed concentration sensors; wind context. This outranks a claim that FSR is the first real industrial dataset.
- paper explicitly excludes inference for candidate sources without downwind sensors and reports windows where inversion is non-informative; 69.4% windows have downwind sensors for all five sources.
- accounts for autocorrelated errors and intermittent emission via spike-and-slab prior; quantifies time-spike misalignment as forward bias (M in 0,12.5,25,37.5,50%), so generic temporal mismatch correction is not new.
- limitation: potential source LOCATIONS are known; it apportions emissions rather than geolocating an arbitrary unknown source via UAV. Source-level errors vary, and forward turbulence params fixed. A sparse source-unknown task is different; must not misrepresent this as their failure.
https://arxiv.org/html/2506.03395v2

## Additional strong collisions
- 2025 Atmospheric Environment DOI 10.1016/j.atmosenv.2025.121044 uses backward Lagrangian WRF/FLEXPART source-receptor matrix and outputs source location probability heatmap and time-varying intensity. Thus backward transport/source provenance is already a standard studied method, not standalone novelty.
- 2026 Phys Rev Fluids DOI 10.1103/kgb6-k3zm "Localization of sources in weakly nonlinear fluid systems using linear and quadratic sensitivity analysis" addresses physical nonlinear inverse source using second-order sensitivities; but user GADEN passive tracer obeys approximately linear transport for a frozen wind, so quadratic concentration/source term need not exist. Do not force this theory onto GSL without nonlinear physical regime.
- 2026 SmartIoT DOI 10.1109/SmartIoT70864.2026.00009 addresses irregular temporal sampling and active hybrid sensors; 2026 IEEE ISOEN DOI 10.1109/isoen68725.2026.11665201 tests robot search with measured wind fluctuations + first-order lag. No novelty from simply inserting timestamps or an ordinary lag filter.
- 2025 J Haz Mat DOI 10.1016/j.jhazmat.2025.137474 already proposes 3D multi-robot source localization for indoor PM; not gas-vapor lake and not source posterior, but defeats generic "first 3D multi-UAV environmental source" rhetoric.

## 4-axis novelty check
| Candidate | Problem overlap | Mechanism overlap | Insight overlap | Domain difference | Verdict |
|---|---|---|---|---|---|
| Continuous-concentration replacing PMFS hit map | high | FULL with Kim DGSE-S | full | only indoor→lake | REJECT new main claim |
| Wind→field→source probability pipeline | high | FULL with Kim, partial NeuPlume | high | lake forcing not verified | REJECT |
| Latent 3D plume world model | partial | HIGH NeuPlume | high | source-coordinate/thermal transport differences possible | HOLD not selected; historical P0 0/21 STOP |
| Temporal wind/sensor lag correction | high | partial to high, MDLQ/ISOEN | high | outdoor UAV vs fixed sensors | reject generic add-on; possible 3rd paper controls |
| Transport-path provenance/correcting recirculation-induced source confusion | plausible | prior backward particle models; other physical methods | partial | lake thermally driven 3D | CONDITIONAL physical hypothesis only; no evidence of source-posterior damage in FSR |
| Source evidence in unobservable wind windows | high | already MDLQ excludes noninformative columns | full | mobile source-unknown task differs | can serve benchmark gate, NOT novel core |

## Original evidence boundary
M0_STOP: all 40 scientific runs qualified, wind/plume and detector response differ but posterior damage max 8.85e-8 vs frozen 0.10. P0 0/21 transfer; equal-height R0C1 2/4. No source-location posterior damage demonstrated in physically qualified FSR thermal cases yet. Do not claim it.

## Distinctive dataset leverage, not proven data superiority
FSR can in principle hold same REAL terrain + water/land roughness/thermodynamic boundary + qualified 3D transient wind + known multiple true source coordinates + source-blind UAV routes + native GADEN state + source posterior in matched controlled counterfactuals. The actual records are incomplete pending FSR CFD/GADEN validation. No simulated FSR output should be treated as meteorological observation; no "first" / "already available 3D physical benchmark" claim.

## Highest-value next NO-SIM action
Existing House/H01/H02 evidence metadata **audit only** whether there is an independently repeatable scenario with:
1) source-ranked PMFS failure even under truth-containing candidate grid (not only source-vs-source binary task);
2) secondary gas transport branches / recirculation measured from real simulation state, not inferred from arbitrary map heat;
3) stronger continuous-concentration baseline and ordinary physical 3D likelihood evaluated on same source-blind route, source/seed-split;
4) output changes in truth rank/MAP and posterior, not field RMSE alone.
If 1–3 impossible or baseline removes failure, terminate with no novelty; no new method/training. Don't re-open stopped PMFS3D/R0C1/M0 by a renamed metric.

Separately require FSR engineering audit on actual latest run before any solver or new case. Once complete FSR CFD/GADEN exists, preregister >=multi-source physically legal candidate grid, neutral/thermal matched forcing × independent release realization, and investigate a source-error-dependent failure. No transport-memory world model until positive source evidence and collision gap.

## Next research stance
**No selected algorithm innovation.** Priority is exact replication and baseline collision tests around Kim's *measured* PMFS binary-hit failure, not proposing a clone of DGSE-S. The author's indoor steady scenario limitation is a setting boundary, not itself proof of method failure in complex lake.
