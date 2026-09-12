# Distributed paired intervention: theory and traceable 2026 sources

Date: 2026-09-13

## Decision after the two H03 failures

The passive causal reweighting scorer is retired, and the one-station rank-2
probe is frozen `NO_GO`.  The latter established a real, transport-consistent
source response but failed over the complete 820-candidate support because the
measurements were concentrated at one local encounter.  This experiment tests
one change only: distribute the already physical paired intervention over the
map and require all informative stations to share one source identity.

The method is called **distributed paired intervention source constraint
(DPISC)**.  It is a second-order construction from four 2026 distant-field
principles; none of the cited papers proposes this UAV gas-localization module.

## Traceable sources and the part actually transferred

1. Mattingly et al., *E. coli chemosensing accuracy is not limited by stochastic
   molecule arrivals*, **Nature Physics** (2026),
   [DOI 10.1038/s41567-025-03111-4](https://doi.org/10.1038/s41567-025-03111-4).
   The transferable idea is to extract task-relevant change rather than assume
   that absolute molecule counts are the useful internal variable.  DPISC uses
   controlled spatial contrasts.  It does not reuse the previously failed
   `Delta log1p` time transform and does not claim bacterial receptor biology.

2. Herter et al., *Fluctuation-response relations for open quantum systems in
   nonequilibrium steady states*, **Nature Communications** (2026),
   [DOI 10.1038/s41467-026-69142-4](https://doi.org/10.1038/s41467-026-69142-4).
   Their physical quadratures motivate the strict distinction between a new
   measurement channel and algebra applied after one aliased observation.
   DPISC obtains independent directions by physically moving the sensor.  It
   imports no quantum formula or fluctuation-response theorem.

3. Wu et al., *Scattering matrix tomography with optical field modulation*,
   **Nature Communications** (2026),
   [DOI 10.1038/s41467-026-72537-y](https://doi.org/10.1038/s41467-026-72537-y).
   The transferred design rule is that controlled inputs can identify response
   structure that passive outputs do not contain.  Here the controlled input is
   the UAV position sequence.  The unknown gas source is never treated as a
   controllable optical input, and optical rank results are not imported.

4. Shi et al., *High-rate phase association with travel time neural fields*
   (HARPA), **Nature Communications** (2026),
   [DOI 10.1038/s41467-026-74092-y](https://doi.org/10.1038/s41467-026-74092-y).
   The transferred idea is that spatially separated observations must be tied
   to one shared event/source latent rather than matched independently.  DPISC
   shares source identity across stations while allowing one local positive
   response scale per station.  Continuous plume samples are not presented as
   seismic phases, and HARPA does not supply a uniqueness theorem for this task.

The local literature audit also considered Bloxham et al.
([DOI 10.1038/s41467-026-71148-x](https://doi.org/10.1038/s41467-026-71148-x)).
Its gain requires two real chemicals with different diffusion kernels.  The
current benchmark has one gas channel, so no synthetic second channel is added.

## Causal estimand and module

At station `k` and direction `l`, the UAV executes equally spaced
`A -> B -> B -> A`.  With endpoint sensor outputs `Y`, the observed contrast is

```text
Z_kl = (Y_A1 - Y_B1 - Y_B2 + Y_A2) / 2.
```

The weights sum to zero and their first time moment is zero.  They therefore
remove a station-cycle nuisance that is affine in time.  This cancellation is
an explicit assumption to be falsified; it does not remove arbitrary turbulent
or nonlinear sensor dynamics.

For a candidate source `s`, the frozen H01+H02-selected provider predicts the
same physical action response `V_sk`.  DPISC profiles one nonnegative station
scale and uses normalized residual

```text
a_hat_sk = argmin_(a >= 0) ||Z_k - a V_sk||^2
L_k(s)   = ||Z_k - a_hat_sk V_sk||^2 / ||Z_k||^2
L(s)     = sum over active stations L_k(s).
```

One source `s` is shared across all stations.  The station scales are separate
because continuous release, plume intermittency and travel time make absolute
intensity incomparable across distant station times.  A station enters the sum
only if one of its physical endpoints exceeds the existing PMFS threshold
`0.1 ppm`; a no-hit station is treated as censored rather than negative source
evidence.  At least two active stations are required.  These choices are fixed
before new gas responses are generated.

The causal object is the action contrast
`E[Z_kl | do(position sequence q_kl), source s, transport u]`.  In simulation,
the crossed SA/HF worlds hold route, wind files, release law, RNG seed and
sensor law fixed while changing source position.  This supports attribution of
the response difference inside the declared simulator intervention.  It does
not identify `do(source)` from passive real-world data and does not remove the
need for ordinary same-information comparator tests.

## Why this is a new test rather than rescue tuning

- The route is built from the free-space map and the already source-blind
  H03 map-cover route.  It reads no gas, source coordinate, posterior or error.
- Three map-spread stations replace the failed one-station support.  Every
  station has three physical directions with rank 2 and condition below 1.2.
- The provider, sensor, source support, gas threshold, transport settings,
  source worlds and RNG seed are unchanged.
- No posterior blend, distance penalty, likelihood temperature, House-specific
  threshold, parameter search, extra seed or new House is allowed.
- The same endpoint samples are scored without contrasts as a comparator.  The
  paired operator must be non-degrading in all four worlds and strictly useful
  in at least one; otherwise the causal contrast is not load-bearing.

The repository's earlier V5 Active Probe selected future stops by information
gain from the source forward model and then fed those observations back into a
posterior.  It was rejected because a misspecified forward family could choose
misleading actions and fresh passive replay had no accepted source evidence.
DPISC does not optimize an information-gain action and does not modify a
posterior.  It fixes a source-independent map-cover measurement matrix first,
then asks whether physically executed action contrasts are identifiable over
the complete support.  If this premise fails, renaming it active sensing is
forbidden and the branch ends.

DPISC is a candidate main innovation only if the preregistered H03 premise
passes.  Cross-dataset validity would still require a later frozen H01/H02
evaluation; this H03 development experiment cannot establish that claim.
