# CTPI M2 observation-world and predictive-law freeze

Date: 2026-09-02
Contract: `CTPI_M2_OBSERVATION_AND_FORECAST_FREEZE_V1`

This addendum resolves the choices that were intentionally left open in the
redesign preregistration.  It is frozen before either `M2_CAL` or `M2_CONFIRM`
is generated.  It does not authorize a predictive-bank rebuild, M3, C++, or
ROS execution.

## 1. Data unit and isolation

The frozen predictive bank remains
`/mnt/hgfs/workspace/CPIR_M1_FULLGRID_LOOKUP_20260831_R1`.  Its three
`bank_summary.json` SHA-256 values are:

- H01: `8bab8c2e5c39d091137beef5d2efe69eb2131be09c75efb1347f18411a776888`;
- H02: `f00daf24c70771d95f945de098fed29e17cc72a763b000bdd281038383bd2845`;
- H03: `736444246178d89432cfde5bc2f12699e7ec9d5600f2e11fa385e609fbfa68ab`.

No command in this phase may write below that root.

One new tape is one independently seeded coherent GADEN transport world at the
frozen true source, sampled along one already-frozen seed0--9 route.  Route
reuse fixes geometry and does not make the plume realization a reused
observation.  For each House, route `seed<i>` is paired with CAL world `i` and
with a separately seeded CONFIRM world `i`, for `i=0..9`.

The generator is the already-built native multistream executable:

- binary SHA-256: `ad0772d994875d009a1e8720928a9f40db56c20f6bf83a03b309049696a7ead4`;
- source SHA-256: `7a1570637eac1ca97758baddd05e7762b47fcd2e12afd77239698bd1132b01b4`;
- RNG entry point: `gaden_initialize_random_engines(uint64_seed)`.

Each world is generated separately.  A multistream call must not combine
different tape identities into one shared world.

## 2. RNG provenance

The machine manifest is generated deterministically by
`tools/ctpi_m2_make_provenance.py`.  The preimage is

`CTPI_M2_OBSERVATION_V1/<SET>/<HOUSE>/<INDEX>|retry=<N>`

and the uint32 seed is the big-endian first four bytes of SHA-256.  Retry is
incremented only on a numeric collision.  The following numeric keys are
reserved and forbidden:

`101, 211, 307, 401, 503, 601, 701, 809, 907, 1009, 1103, 1201, 5489`.

The first twelve cover every frozen train/reserved predictive-member key.  The
last is the conservative default `std::mt19937` seed used when no explicit RNG
hook is called.  All 60 new numeric seeds must be mutually distinct.  CAL and
CONFIRM also have different derivation domains.  A manifest collision or hash
mismatch is a hard stop.

## 3. Frozen observation operator

The native generator produces physical concentration on the 0.2 s route grid.
The observation tape applies the already-frozen zero-noise sensor forward
operator, not an M2 state model:

- `dt = 0.2 s`;
- dead time `0.4 s` (two samples);
- FOPDT time constant `1.2 s`;
- gain `1`, baseline `0`, initial input/state `0`;
- one completed stop is the first 80 stationary samples;
- event `Y=1` iff the maximum measured concentration in those 80 samples is
  strictly greater than `0.1 ppm`.

This preserves the event used by the frozen M1 evidence.  Sensor dynamics are
part of observation-world construction only.  M2 does not maintain a sensor
state and never re-assimilates the realized event.

Each tape must contain exactly 1500 physical samples, 1502 forward-sensor
samples including the causal two-sample tail, and exactly 15 completed-stop
events.  Only the first 1500 aligned measured samples enter those events.

## 4. Forecast timing and baseline

For transition `j`, every input is evaluated immediately before observing
`Y_j`.  Let `pi_j(s)` be the frozen M1 posterior from stops `<j`, and let
`K_j(s)` be the number of the eight predictive members that produce a raw
physical event at the candidate stop.  The baseline source-conditional law is

`p0_j(s) = (K_j(s) + 0.5) / 9`.

The scored truth-blind forecast is the posterior mixture

`q0_j = sum_s pi_j(s) p0_j(s)`.

The evaluator receives no true-source index.  True source coordinates exist
only in the sealed world-generation manifest and are not an evaluator input.

## 5. Frozen M2 calibration law

M2 is one global, House-independent monotone reliability table over member-hit
count `k=0..8`.  It is fitted once on pooled CAL transitions and then frozen.
No alternative formula is tried on CONFIRM.

For each CAL transition, use the pre-event M1 posterior as a fractional latent
source weight:

`W_k = sum_{j,s} pi_j(s) 1[K_j(s)=k]`

`A_k = sum_{j,s} pi_j(s) 1[K_j(s)=k] Y_j`.

The nine preliminary rates use a fixed Jeffreys beta prior:

`r_k = (A_k + 0.5) / (W_k + 1)`.

Weighted pool-adjacent-violators regression, with weights `W_k+1`, produces the
unique nondecreasing table `g_0..g_8`.  Adjacent violations are pooled from
left to right; equality is not pooled.  This is the complete M2 fit: there is
no temperature, House parameter, source label, task metric, or planner reward.

M2 supplies `p1_j(s)=g[K_j(s)]`; its scored mixture is
`q1_j=sum_s pi_j(s)p1_j(s)`.  It may return forecasts but may not mutate
`pi_j`, M1 evidence, or `sourceProbability`.

## 6. One-shot CONFIRM Gate

Every tape contributes its mean over its 15 transitions.  Pooled metrics use
all 450 confirmatory transitions.  NLL probabilities are clipped only at the
fixed numerical boundary `1e-12`; this is not fitted.

Calibration is fixed five-bin ECE with bins
`[0,.2), [.2,.4), [.4,.6), [.6,.8), [.8,1]`.

`CTPI_M2_PREDICTIVE_GATE_PASS` requires all of:

1. pooled M2 NLL is strictly below baseline NLL;
2. pooled M2 Brier is strictly below baseline Brier;
3. at least one of paired tape NLL or Brier has a one-sided exact sign-test
   `p <= 0.05` in the lower-is-better direction;
4. M2 ECE is no greater than baseline ECE (numerical tolerance `1e-12`);
5. no House has both a higher mean NLL and a higher mean Brier with at least
   8/10 tape losses on each metric;
6. every probability is finite and strictly between zero and one;
7. the calibrated table contains at least three values separated by `1e-6`;
8. every House has at least one transition with source variation above `1e-6`
   and at least one source whose forecasts vary across visited next actions by
   more than `1e-6`.

CONFIRM is opened exactly once after the CAL table, implementation commit, and
their SHA-256 values are recorded.  Failure emits
`CTPI_M2_PREDICTIVE_GATE_NO_GO` and forbids M3/C++/ROS.
