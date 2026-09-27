# Bounded OPEN closed-loop campaign

## Evaluation data

Use the already-generated House03 F1 plume bank as OPEN DEVELOPMENT data.

It is no longer a fresh confirmation after the AOD analysis and BRG method
selection. Do not call this a new fresh test.

Use:
- the frozen 12 House03 truth sources;
- 8 independent plumes/source = 96 cases;
- full 624-candidate support;
- the already-built legal House03 p/rawu model bank;
- one common initial pose per plume/case;
- the same wind/plume replay and observation contract for every arm.

No new plume.

## Four arms

1. `native_pmfs`
2. `candidate_gru`
3. `brg`
4. `brg_ungated`

All learned arms receive identical p/rawu/geometry/measurement inputs.

Each arm chooses its own path. Do NOT force common trajectories.

## Budget

Freeze:
- maximum search time = 300 s;
- geometric success radius = 0.5 m;
- same PMFS update cadence, dwell, controller and reachability settings.

The repository's native PMFS `GSLResult::Success` is triggered by posterior
variance, not by ground-truth geometric accuracy. Therefore record BOTH:

A. algorithm declaration result/time;
B. evaluator geometric result.

Primary development success is geometric:
final declared/available source estimate within 0.5 m of truth by 300 s.

Also record the first robot-navigation time within 0.5 m when available, but do
not substitute it for source-estimate success.

## Failures

Keep as failures:
- timeout;
- no hit;
- wrong declaration;
- navigation failure;
- service/TCP error;
- missing source estimate;
- nonfinite state.

No silent fallback from a learned arm to native PMFS.
