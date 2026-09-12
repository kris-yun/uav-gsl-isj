# PMFS M1R post-DPISC main-innovation decision

Date: 2026-09-13

## Decision

The causal action-response effect is real, but the causal source-localization
claim is not identified under the current single-UAV, single-gas benchmark.
The M1R 2/3 endpoint-improvement code remains a valid historical baseline; it
cannot be promoted to the main innovation, and no additional same-data
reweighting, threshold, temporal transform or active route is admitted.

The branch verdict is:

```text
CAUSAL_ACTION_RESPONSE_EXISTS
CAUSAL_SOURCE_LOCALIZATION_NOT_IDENTIFIED
M1R_2_OF_3_IMPLEMENTATION_PRESERVED
NO_SAFE_HOUSE_BLIND_SELECTIVE_WRAPPER
RETIRE_CURRENT_CAUSAL_LINE_AS_MAIN_ALGORITHM
```

## Evidence chain

1. M1R changes the live PMFS likelihood and produced historical seed-12
   endpoint improvements in H01 and H02, degradation in H03, and AUC
   improvements in all three.  This proves implementation and development
   utility only.
2. In the instrumented source-evidence replay, the true-source leaf predicted
   zero before Bernoulli clipping for every positive block in H01 (59/59) and
   H02 (88/88), and for 66/70 positive blocks in H03.  The source/context term
   improved fixed rival margins but all final margins remained strongly
   negative.
3. The oracle nonnegative-reweighting certificate could not uniquely identify
   the truth in H01 or H02.  H03 oracle feasibility did not supply a deployable
   selector.
4. The Mattingly-inspired deterministic temporal change transfer failed its
   frozen H03 test.  The one-station physical rank-2 probe then established a
   transport-consistent source response but failed complete-support source
   ranking.
5. DPISC distributed the physical action over three source-blind map stations.
   Its source effect again survived transport change (fast/slow cosine
   0.963078; main norm 0.087482 versus interaction norm 0.033385), but only one
   station was active in three worlds and none in SA-slow.  The held-out
   provider direction failed in slow transport, complete-support ranking
   failed, and paired scoring degraded its matched raw comparator in one world.

Together these results distinguish **causal effect** from **causal
identification**.  Position interventions change gas response, but the current
observation/provider pair does not map those effects to a unique source across
the tested transports.

## Why an adequacy fallback is not the missing repair

A truth-blind wrapper that activates M1R only when the candidate response family
fits the observation would be scientifically reasonable in principle.  Here it
does not retain the historical H01/H02 gains: the saved source-evidence audit
shows that the true-source response is outside or aliased in all three Houses.
An honest adequacy gate would therefore reject all three.  A gate constructed
to accept H01/H02 and reject H03 after seeing endpoint outcomes would be
House-specific rescue tuning and would not establish transportability.

Fallback to A0 on H03 would at most convert the 2/3 endpoint result to two
improvements and one tie.  It would not satisfy the preregistered requirement
that every environment improves in endpoint and time-integrated error, and it
would not repair the missing source evidence.

## What the verified 2026 distant-field papers imply now

- Mattingly et al. supports task-related change encoding.  That transfer has
  been tested in temporal and spatial form; neither produced cross-transport
  source identification.
- Herter et al. and Wu et al. require genuinely new physical measurement/input
  directions.  Position actions created a source effect, but the current
  provider did not supply correct global response shape.
- Shi et al. (HARPA) requires multiple associated observations sharing a source
  and restricted medium.  The distributed H03 route did not produce multiple
  active stations, so the common-source constraint had no physical support.
- Bloxham et al. obtains extra information from two real chemicals with
  different diffusion kernels.  A second chemical cannot be synthesized from
  the benchmark's one gas channel.

These papers remain valid theoretical provenance and failure constraints.  No
remaining module from this verified batch can be instantiated without changing
the measurement system or inventing information.

## Non-negotiable information required to reopen a causal main claim

At least one of the following external changes is required before another
causal localization module is scientifically admissible:

1. a real second chemical/sensor channel with a distinct physical transport or
   response kernel;
2. a controllable source excitation/modulation sequence;
3. simultaneous spatial receivers or multiple UAVs that observe associated
   plume events;
4. an independently qualified source-by-transport physical response ensemble
   covering the candidate support, evaluated on an independent release seed.

All four are outside the current authorized benchmark: they add hardware or
agents, control the unknown source, or require a protected/expensive response
bank plus a new independent seed.  Further H03 same-seed transformations cannot
substitute for them.

## Recommended paper-level pivot

If the measurement and data constraints remain fixed, the main algorithm should
move to the already separate **source/mismatch subspace-protection** line
(CCDE/GW_MAIN) and describe causality as an identifiability audit that motivated
the separation, not as an established causal source estimator.  That line has
an explicit source-versus-mismatch decomposition and positive pilot evidence,
but its own held-out gate remains mandatory.  It must not inherit a causal
label from M1R or reuse the failed DPISC result as performance evidence.

This is the shortest scientifically defensible continuation.  Reopening M1R
with another weight, threshold, temporal kernel, posterior blend or active
probe would repeat a falsified information premise.

