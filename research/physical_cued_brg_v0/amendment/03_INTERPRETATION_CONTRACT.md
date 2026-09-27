# Interpretation contract — no new offline gate

This is an OPEN development closed-loop campaign.

Always report:
- source-weighted geometric success rate;
- paired success delta;
- source-stratified resampling interval;
- final error distribution;
- search/declaration time;
- path length;
- hit/measurement counts;
- wrong declarations;
- service/navigation failures;
- compute latency/cost.

Interpret the four-arm result as follows.

## Case A — BRG beats native AND both same-input controls

If BRG has higher source-weighted geometric success than:
- native PMFS,
- matched candidate GRU,
- BRG-ungated,

with no material final-error deterioration, then:

`BRG_MAIN_CANDIDATE_ADVANCE`

Meaning:
candidate-conditioned recurrent feedback has development evidence beyond both
classic PMFS and generic learned candidate scoring.

This authorizes a later sealed confirmation / real-flight preparation.
It is not itself fresh confirmation.

## Case B — learned models beat native, but BRG does not beat controls

`LEARNED_SCORER_ONLY_BRG_NOT_ESTABLISHED`

Meaning:
p/rawu + learned candidate evidence may help, but the 2026 feedback mechanism
has not shown independent value. Do not claim BRG as the main innovation.

## Case C — BRG does not improve over native

`BRG_V0_CLOSED_LOOP_NO_GO`

Stop this BRG v0 architecture. Do not rescue it by adding another network,
attention block or target-domain adaptation on the same campaign.

AOD remains independently preserved as the confirmed physical observation
result.

## Why AOD is not a fifth closed-loop arm here

The archived B2/AOD score is a ranking/SSE rule, not a calibrated belief map.
Turning it into a planner-driving probability distribution would require a new
temperature/noise model and would introduce another method change.

Therefore AOD is used as the validated physical cue basis (`rawu`), while the
same-input GRU and ungated models isolate whether BRG feedback itself matters.
