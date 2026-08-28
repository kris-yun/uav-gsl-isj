# PF-DEI sensor-memory root-cause audit

Date: 2026-08-28  
Input: truth-blind `observed_block_manifest.csv` (30 OFF runs, 4,049 completed blocks)

## Verdict

The proposed trajectory-dependent observation-aliasing mechanism is **confirmed as a deterministic mechanism capable of changing PMFS decisions**. It is not, by itself, proof that every qualifying event is a false physical hit or that sensor memory is the dominant localization failure. Those stronger claims require matched ideal/native replay on the same physical concentration sequence.

## Calculation

For the frozen archived sensor configuration (`tau=1.2 s`, `dt=0.2 s`, `B=10`, zero noise, gain 1, zero baseline), take the last measured state of the previous completed stop as `M0` and the time gap to the first sample of the next stop as `g`. With zero current input, the residual contribution to the next block mean is

`LB = M0 * exp(-g/tau) * (1/B) * sum(k=0..B-1) exp(-dt*k/tau)`.

The geometric factor is `0.5283568986066902`. A transition is called qualifying only when `LB > thresholdGas=0.1 ppm`; no true source, true gas, localization error, or performance label enters this calculation.

## Results

| House | transitions | memory-only bound > 0.1 ppm | fraction | archived HIT among qualifying |
|---|---:|---:|---:|---:|
| H01 | 161 | 0 | 0.0% | n/a |
| H02 | 163 | 37 | 22.70% | 37/37 |
| H03 | 160 | 65 | 40.63% | 65/65 |
| Total | 484 | 102 | 21.07% | 102/102 |

Gap statistics: median `1.2 s`, minimum `0.6 s`, maximum `22.2 s`; the median equals the sensor time constant.

## Interpretation

The result proves that a block event is not generally a function of only the current block concentration. The PMFS event depends on the causal history through the persistent sensor state:

`trajectory -> prior exposure -> sensor state R_t -> measured ppm M_t -> block HIT/NOTHING`.

Consequently, multiplying independent per-context source likelihoods is not physically justified unless the hidden sensor state is conditioned on or marginalized through a run-level forward model.

However, `LB > threshold` is a sufficient-history condition, not a proof that the next block's physical concentration was zero. Current input can add to the state, and the bound deliberately does not use forbidden true concentration. The scientifically decisive follow-up is a matched replay with identical candidate source, transport, trajectory, and physical concentration sequence under (A1) ideal sensor and (A2) native persistent sensor. If A1 recovers source ordering while A2 does not, sensor memory is dominant; if both fail, transport/model mismatch remains unresolved.

## Artifacts

- `artifacts/pf_dei_forward/sensor_memory_bound_transitions.csv` — all 484 transitions.
- `artifacts/pf_dei_forward/sensor_memory_bound_summary.json` — machine-readable summary.
- Script: `reference/analyze_pf_dei_sensor_memory_bound.py`.

Raw measured samples remain correlated observations; this audit does not treat them as independent replicates.
