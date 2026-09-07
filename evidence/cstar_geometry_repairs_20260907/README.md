# Verified implementation repairs and cross-House diagnostics

This package supersedes the **metric interpretation**, not the immutable raw
predictions, of the four geometry-normalized exploratory M1 screens. It does
not authorize closed-loop experiments or claim that M1/M2 are qualified.

## Implementation findings

1. M1 evaluator multiplied normalized coordinates by 10. Its metre errors
   were wrong. `METRIC_RECOMPUTATION.json` uses raw candidate XY coordinates
   and binds the archived reports/posteriors. All four screens remain NO-GO.
2. The previous radial head subtracted two equal-width squared distances.
   The candidate quadratic terms cancel exactly, leaving a linear score
   whose nonconstant maximum is on the candidate convex hull. The new opt-in
   radial head preserves curvature with a nonnegative zS-dependent precision
   that vanishes at zS=0. This repairs localization capacity; it does not prove
   invariance, identifiability or novelty. The historical flag name
   `coordinate_equivariant` is not a proof of whole-network equivariance.
3. Two newer PGM readers included the header delimiter as pixel zero, shifted
   the raster, treated any positive pixel as free and rounded world cells.
   They now reuse the established validator's exact raster, YAML threshold
   and floor-from-cell-corner semantics. Pillow decoding and every free cell
   centre independently agree. `AUDIT_V2.json` in the route-map evidence
   directory still passes all recorded House123 trajectories. Frozen maps
   and routes were not edited.
4. M2 advanced only 0.2 field seconds per 0.2 sensor seconds despite the
   frozen replay ratio 2.5. An explicit environment-bound transport clock
   fixes this. A noise-free FOPDT observation can initialize the forecast
   sensor state; its hidden delay queue is still model-inferred. No raw
   sensor queue is read. Unsupported/saturated observations fail closed.
5. The optimized transport has the same edge fluxes/CFL substeps as the
   scalar reference; 30 random wall/wind fields and analytic mass checks
   agree. Stamped truncated or irregular prefixes now fail instead of
   silently resetting the field/sensor initial state.

## Scientific results

The corrected radial M1 screen has errors 2.740/4.234/6.786 m and NLL
8.204/8.818/12.460 on H01/H02/H03. It still fails the full controls in all
three Houses. Independent recomputation checks 2,700 prediction rows plus
252 baseline route cases in the sibling `cstar_controlled_screen_20260907_radial_repair`.

`M2_ALL_ROUTES_VERIFIABLE.json` is the authoritative physical-prior diagnostic:
84 routes per House, all 252 cases, no outcome-based case selection. It uses
evaluator source coordinates to test forward adequacy, not source localization.
The physical prior loses to persistence in every House even with identical
observation scales. Mean log-ppm MSE is 0.2381/0.6579/0.2813 versus persistence
0.02571/0.06397/0.03223. Initial field remains unknown; past pointwise wind
does not establish a spatial transport field. Small t=8 gains did not survive
evaluation over the whole set. Earlier small-case files are intermediate
diagnostics; use the full verifiable artifact for conclusions.

A separate source-blind local predictor is preserved under
`evidence/cstar_m2_local_prediction_20260907`. It beats persistence in mean
log-ppm error across all three Houses, but adding route information beats
the stronger history-only ablation only in H02/H03. Its declared all-House
route-increment screen remains NO-GO. It predicts marginal means, not a
normalized first-passage law; it is not a qualified full M2 or evidence of
closed-loop source-localization benefit. `M2_RECOMPUTATION.json` independently
recomputes both diagnostics' scores.

## Why M1 needs a different evidence design

`SOURCE_TRANSPORT_SUPPORT.json` counts two exact source positions and four
realizations per House. Same-source transport pairs exist, but **zero**
different-source pairs hold transport, release setting and sensor fixed.
Source separation can therefore reflect the correlated transport settings.
This is not a proof that gas contains no source information. The file lists
six missing crossed configurations using the existing Houses and sources;
new realized release sequences would also need a matching/modeling contract.
No new seeds or simulator jobs were created.

The VM is reachable. A read-only storage check in this continuation found
114 MB available on `/` (100% used) and 2.6 GB in `/dev/shm`. Additional raw
realizations require a declared scratch/output and preservation plan; no
existing experiment payload or bank was removed to make space.

The source-masked context law is candidate-independent for a fixed prefix
and route. Its scalar log score cancels in posterior normalization, yielding
ordinary Bayes. A three-candidate check has max difference 0.0. That score
transform alone cannot be called the causal innovation. The causal claim
still requires identified intervention structure and successful destructive
controls. Adding posterior consistency or event pooling did not establish it.

## Reproduction

Run the geometry, clock/state, environment-session and local-feature
selftests in `experiments/ctpi_cstar`. The environment factory binds the
online provider to the actual YAML, clock and sensor manifest without any
House-specific adjustment. `provider.predict` exposes the same explicitly
prefix-assimilated method used in the forward diagnostic.

M1 command:

```text
python experiments/ctpi_cstar/controlled_screen.py --out NEW_EMPTY_OUTPUT --geometry-normalized --coordinate-equivariant --radial-source-score
```

M2 physics command:

```text
python experiments/ctpi_cstar/diagnose_physical_prior_assets.py --assets evidence/cstar_controlled_assets_20260907_r2 --maps evidence/cstar_environment_20260906/maps_v1 --routes evidence/cstar_controlled_routes_20260907 --output NEW_OUTPUT.json --max-cases 84 --assimilate-prefix --clock experiments/ctpi_cstar/CSTAR_ENVIRONMENT_CLOCK_V1.json --condition-noise-free-sensor --sensor-manifest evidence/cstar_environment_20260906/probes_v1/H01/sensor_manifest.json --vectorized-transport
```

All observations are from existing development replay. These are neither new
datasets nor virgin held-out confirmation. House123 seed12 closed loop remains
unauthorized by the scientific gate.
