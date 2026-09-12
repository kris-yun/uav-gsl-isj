# M1 estimated-transport attribution, 2026-09-11

Status: main causal innovation NOT validated. No closed-loop PASS.
Work continues from the active goal without new seeds, bank, or M2/M3.

## Reproducible indexing failure repaired

Original H01 SA forward stopped at 70.8 s. At the failing particle position
(-0.9181521045531363, 1.9199996714520273, -0.7181854996108992),
the map's canonical float32 indexing is (66,98,3), free; its navigation-plane
projection is (66,98,13), also free and present in the GMRF field.
The old float64 wind lookup selected (66,97), absent from field support.
This was a mixed-precision cell-index bug, NOT missing vertical coverage at
this specific point. Wind lookup now follows the same float32 convention as
the map; a test uses the exact failing coordinate.

Evidence preserved: the original 240 s diagnostic, SA trace_v2 failure, and
SA trace_v3 completion under `evidence/cstar_m1_estimated_transport_h01_*`.
SA trace_v3 reached all 1200 samples / 240 s.

## Running correctly still gives problematic source evidence

On the H01 SA-fast observed history, fixed SA estimated-transport prediction:

- Observed >0.1 ppm interval: 229.0–232.0 s, 16 samples.
- Predicted >0.1 ppm interval: 229.8–238.4 s, 44 samples.
- Threshold-positive overlap: 12 samples.
- Observed peak: 0.414115 ppm at 230.2 s.
- Predicted peak: 1.276040 ppm at 234.6 s.
- log1p response MSE: 0.0073375301853.
- Zero response MSE on those observations: 0.0008060542342.

Thus there is partial temporal support, but amplitude and late-tail error
dominate this working score. It is incorrect to report either "no causal
response" or "correct source recovered" from this evidence.
Cosine of the log1p curves is 0.319767. MSE decomposition is
observed energy 0.000806054 + predicted energy 0.008172955 minus cross term
0.001641479. Do not select a fitted amplitude to rescue this case.

The old-code SB completed with zero prediction; because its lookup code
differed, a corrected SB rerun is in progress (unified exec session 49638).
Wait for that exact result before declaring a same-code two-candidate ranking.

## Source-blind wind diagnostic across Houses

`audit_m1_wind_prequential.py` uses the latest field strictly BEFORE each
measurement timestamp, never a field already incorporating that measurement.
It reads only local measured wind and pose for evaluation, not gas/source.
Each case scores 1199 next observations; zero lookup failures.

| House / regime | GMRF component RMSE m/s | Last-local-wind RMSE m/s | Ratio |
|---|---:|---:|---:|
| H01 fast | 0.079173 | 0.028168 | 2.81 |
| H01 slow | 0.033229 | 0.013508 | 2.46 |
| H02 fast | 0.077845 | 0.034208 | 2.28 |
| H02 slow | 0.032073 | 0.012653 | 2.53 |
| H03 fast | 0.189084 | 0.068664 | 2.75 |
| H03 slow | 0.074079 | 0.029157 | 2.54 |

GMRF beats zero wind but loses to temporal local persistence in every case.
This is a local forecasting diagnostic under our explicit replay cadence,
NOT proof that persistence estimates off-route wind, a deployed ROS parity
result, or proof of causation by permanent observation accumulation.
Cadence, spatial movement and historical observation accumulation remain
separate mechanisms to distinguish. Do not replace the entire field with
the last measured vector on the strength of this table.

Raw input/output hashes and metrics:
`evidence/cstar_m1_wind_prequential_20260911.json`.

## Scientific implication and bounded next step

The shared issue currently evidenced is unreliable plug-in transport, not
an established common latent source representation. A causal source likelihood
conditioned on a single estimated field can confidently prefer a wrong/null
response when transport discrepancies dominate source contrasts.

M1's intended causal contribution must intervene on candidate source while
holding shared nuisance realizations consistent, then marginalize or bound
transport uncertainty BEFORE Bayesian source accumulation. The present
point-member diagnostic has not demonstrated that benefit. A good physical
forward implementation alone is not the novel causal mechanism.

Next: complete same-code ranking, separate wind timing/history errors using
source-blind tests, and assess physically propagated candidate/member response
uncertainty. Wind RMSE is NOT a concentration radius or log-evidence bound;
do not directly substitute it into V3. Compare ordinary Bayes and M1 using
the SAME provider and inputs, with matched abstention comparisons. Retain
the planned House123 seed12 closed loop; do not spend it on this unpassed
point-transport gate or change seeds to look for a win.

## Source audit correction

The inspected current native source uses PointSource::Emit() returning its
fixed sourcePosition, and deterministic accumulated release count. The shell
flag `variable_rate:=true` alone does NOT prove a variable-rate emitter was
used; prior comments that asserted that mismatch were too strong. Historical
binary binding is still missing. Current native source also reads temperature
and pressure through the wind_time_step parameter name; this deserves a
parameter-binding audit, not an assumption that the launch flags were used.
The concentration kernel depends on a ratio in which consistent air density
and filament-mass scaling cancel, so this source bug alone does not explain
the observed prediction amplitude error.
