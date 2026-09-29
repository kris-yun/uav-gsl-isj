# V12-M RC-SD-TFEI Held-out Generalization Report

Date: 2026-08-25  
Final verdict: **V12_M_HELDOUT_GENERALIZATION_NO_GO**

## What was tested

- Frozen production binary SHA-256: `100ca267c1dc6f098f1080f669733bf7cf655d8a05ce8d5afe3ef9b9458a51ce`.
- Three previously unseen seeds: H01 `418310734`, H02 `661532441`, H03 `538848658`.
- Six complete closed-loop arms: each House used paired PMFS OFF 300 s and V12-M ON 300 s.
- Same binary, source-update cadence, planner configuration, time budget, and seed within each pair.
- ON used a precomputed, truth-blind, SHA-frozen 8-transport physical response bank for its House.
- All six arms ended with `time_budget_timeout`, produced exactly five complete source updates, and passed the frozen runtime-integrity contract.
- Truth was read only after all six arms passed integrity.

The primary metric is the exact external counterpart of PMFS
`Utils::ExpectedValue(sourceProbability, 0.05)`: sort all free cells by posterior
probability, retain `ceil(0.05 N)`, renormalize their probability mass, estimate
the source coordinate, and calculate Euclidean error to the source.

## Primary result

| House | Held-out seed | PMFS OFF (m) | V12-M ON (m) | Relative change | Improved? |
|---|---:|---:|---:|---:|---|
| H01 | 418310734 | 6.3923 | 6.3082 | +1.32% | yes |
| H02 | 661532441 | 3.0210 | 3.0137 | +0.24% | yes |
| H03 | 538848658 | 7.6312 | 8.0256 | -5.17% | no |

Pooled OFF error sum: `17.0445 m`.  
Pooled ON error sum: `17.3475 m`.  
Pooled improvement: **-1.78%** (worse), versus the frozen requirement of at least +10%.

The method satisfies only the weak `2/3 Houses numerically improve` condition;
the improvements are negligible and the pooled outcome is negative. It therefore
cannot be claimed as a generalization success or a valid main-innovation result.

## Decisive failure mode

All three ON posteriors are false-confident:

| House | ON variance (m^2) | ON error (m) | posterior mass within 1 m |
|---|---:|---:|---:|
| H01 | 0.000371 | 6.308 | 1.71e-94 |
| H02 | 0.047597 | 3.014 | 5.32e-58 |
| H03 | 0.045105 | 8.026 | 9.17e-244 |

The carrier-level audit shows that the likelihood is already directionally wrong
at the first update and cumulative evidence makes it irreversible:

| House | truth-carrier rank at update 1 | rank at update 5 | top-minus-truth cumulative log-evidence gap at update 5 |
|---|---:|---:|---:|
| H01 | 194/210 | 210/210 | 218.68 |
| H02 | 183/201 | 125/201 | 451.19 |
| H03 | 64/206 | 89/206 | 564.54 |

This rejects the proposition that the frozen response family yields calibrated
source likelihoods under the real closed-loop observations. The stable-channel
linear algebra and response-bank engineering work, but the physical likelihood
contract does not identify the true cause across Houses.

## Formula/code finding

The production path does not implement the originally stated fusion
`p_PMFS(s) * L_SD(s) * L_D(s)`. In `Simulations.cpp` it builds

`logPosterior = log(geometry carrier area / total free cells) + cumulative V12 evidence`

and then assigns the resulting grid directly to `sourceProbInternal`. Thus the
native PMFS posterior is replaced by a geometry-prior V12 posterior rather than
used as the Bayesian prior. This is a contract-level discrepancy, not a minor
gate or runtime problem. Because the V12 likelihood is misspecified on held-out
observations, direct replacement creates the observed false-confidence collapse.

## What is and is not established

Established:

- V12 activates in the real House01/02/03 closed loop.
- It uses completed online events and influences subsequent planning.
- Response banks are truth-blind, hash-frozen, validated, and loaded rather than rebuilt.
- Online update overhead after bank load is about 9–25 ms, so speed is not the failure.
- Cross-fit mixture, replay identity, mass conservation, and serialization contracts pass.

Not established:

- Source-causal likelihood validity.
- Calibration or recoverability of the true source carrier.
- At least 10% improvement over native PMFS.
- Safe uncertainty: all held-out ON cases are confidently wrong.
- Main-innovation generalization.

## Scientific decision

Do not tune or rescue V12-M on these revealed seeds. Freeze it as a completed
negative result. The next version must be a new preregistered method with a
truth-blind premise gate that requires the true-generating candidate family to be
recoverable under held-out physical realizations before any closed-loop injection.
It must also make the Bayesian contract explicit: either multiply a calibrated
incremental likelihood into a frozen PMFS prior, or formally justify replacing
PMFS. Posterior temperature, confidence clipping, or a safety gate alone would
hide rather than repair the failed source-evidence ordering.

The benchmark logger's `final_error` is not used here: for this runner it can fall
back to terminal UAV pose. The primary numbers above come from the frozen final
source posterior and the PMFS `ExpectedValue(..., 0.05)` definition.
