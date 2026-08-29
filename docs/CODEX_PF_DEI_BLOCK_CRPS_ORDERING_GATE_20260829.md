# CODEX — PF-DEI block-CRPS actual source-update ordering gate

Date: 2026-08-29
Branch: `research/cg-pc-ctt-v6-dynamic-transport-sbi`
Execution class: CHEAP EXISTING-BANK FALSIFICATION ONLY

## Objective

Test exactly one scientifically motivated replacement for the failed direct multivariate trajectory energy ordering: block-level marginal finite-ensemble CRPS at the five historical H01 PMFS source-update times.

This gate answers only whether a proper marginal ensemble score materially improves source ordering. It does NOT calibrate a posterior and does NOT authorize shadow or closed-loop.

## Hard prohibitions

Do NOT:

- run GADEN;
- generate a new physical bank;
- train any neural network;
- run shared/LOHO;
- tune a temperature, threshold, weighting coefficient, block length, member count, transform, or prior from source outcomes;
- use localization error in inference;
- use `true_gas_ppm` in inference;
- modify q0;
- start shadow or ON closed-loop.

Reuse only the hash-verified H01 seed0..9 existing physical views/bank and archived OFF sensor traces/source-update timing.

## Frozen primary representation

Work in measured-sensor space.

For every candidate source `s`, nuisance member `m`, and archived sample context, take the existing physical prediction `C_{s,m,t}` and pass it through the already frozen deterministic persistent sensor forward operator `T` using the exact same sensor state contract. Compare against archived `measured_gas_ppm` only.

Reconstruct the actual PMFS sensing-block boundaries from authoritative archived runtime/context files. Do not invent fixed windows if exact block boundaries are available.

For block `b`:

`Y_b = log1p(max(mean_t_in_b M_obs(t),0)/0.1)`

`X_{s,m,b} = log1p(max(mean_t_in_b T(C_{s,m})(t),0)/0.1)`.

The 0.1 ppm reference is the already frozen PMFS physical threshold, not a tuned hyperparameter.

## Frozen primary score

For M predictive nuisance members:

`CRPS_b(s) = mean_m |Y_b-X_{s,m,b}| - (1/(2 M^2)) sum_{m,n} |X_{s,m,b}-X_{s,n,b}|`.

At source update `u`:

`L_u(s) = sum_{b whose observations are visible by update u} CRPS_b(s)`.

Lower `L_u` is better. Tie break deterministically by stable carrier ID.

This is the PRIMARY arm and must be implemented before any optional diagnostic.

## Baselines to report without modification

At the identical seed/update pairs report:

1. previous frozen FULL multivariate trajectory-energy raw rank from the already generated A0-gate evidence package;
2. new block-CRPS raw rank;
3. q0 prior rank as a reference only.

Do not run A0 on block-CRPS in this task.

Optional secondary diagnostic, only after primary results are complete: sample-level marginal CRPS using the same measured-domain predictive distribution at every 0.2 s sample. Label it SECONDARY and do not select between primary/secondary by held-out result.

## Outputs per 10 seeds x 5 source updates

For block-CRPS output:

- true-source rank and normalized rank;
- Top1/Top5/Top10;
- severe failure indicator normalized rank > 0.5;
- true-vs-best-rival cumulative CRPS margin;
- selected carrier ID;
- number of visible sensing blocks;
- cumulative CRPS of true source and best rival;
- paired rank delta relative to frozen previous FULL raw rank.

Aggregate by update and overall 50 cases:

- Top1/Top5/Top10;
- median and mean normalized rank;
- severe count;
- block-CRPS better/tie/worse than previous FULL;
- paired rank-delta median/mean;
- update-1 statistics separately.

Also report per-seed rank trajectory across update1..5 to reveal monotonic improvement or instability.

## Predeclared interpretation gate

This is a development/falsification gate, not the final paper performance gate.

Call `PFMEI_BLOCK_CRPS_ORDERING_PROMISING` only if ALL of the following hold:

1. overall block-CRPS raw Top5 >= 15/50 (more than 2x the frozen 7/50 baseline);
2. overall severe failures <= 5/50 (frozen baseline 11/50);
3. paired rank comparison: block-CRPS better than frozen FULL in >=30/50 cases and worse in <=15/50 cases;
4. overall median normalized rank <=0.08 (frozen baseline 0.117225);
5. update-1 severe failures <=4/10 OR update-1 median rank <=100/210.

Otherwise return `PFMEI_BLOCK_CRPS_ORDERING_NOT_ENOUGH`.

These thresholds are frozen before execution and must not be changed after viewing results.

Even on PROMISING, do NOT proceed automatically. STOP and return evidence. Posterior calibration is a separate gate.

## Validation / parity requirements

Before scoring all cases, selftest on synthetic arrays:

- CRPS is invariant to nuisance-member permutation;
- identical observation and degenerate matching ensemble gives zero CRPS;
- finite-ensemble formula matches a slow reference implementation to <=1e-12 on small random arrays;
- no future block enters a source-update prefix;
- source truth is inaccessible until after all candidate scores are computed;
- `measured_gas_ppm` is the only observation channel;
- sensor forward parity remains within the already established archived tolerance.

## Expected cost

This should reuse existing bank views and be cheaper than the previous multivariate energy replay. Target wall time: seconds to a few minutes; investigate engineering/I/O if it exceeds ~10 minutes. Do not solve a slow implementation by reducing seeds, sources, members, or source-update cases.

## STOP contract

After generating the report/package and hashes, STOP. Return:

- verdict;
- primary aggregate table;
- update1..5 table;
- paired comparison versus frozen FULL;
- per-seed rank trajectories;
- selftest/parity results;
- wall time;
- package SHA-256;
- git HEAD and dirty status.

Do not create a posterior, beta calibration, neural network, shadow run, or closed-loop run in this task.
