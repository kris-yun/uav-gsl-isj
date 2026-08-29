# PF-DEI H01 10-seed post-replay decision

Date: 2026-08-29
Status: POST-REPLAY SCIENTIFIC DECISION / PRE-CLOSED-LOOP

## 1. Evidence integrity

Uploaded package: `H01_HISTORICAL_10SEED_EXISTING_BANK_REPLAY_20260829.tar.gz`.

External SHA-256: `95862f5799a0fb74a8e5906d5473086660231ced23b3d591113c149434e0d4be`, matching its sidecar.

Internal `FILE_SHA256_MANIFEST.csv`: 33/33 regular files verified, zero size/hash mismatch.

The mapping contract is `H01_HISTORICAL_SEED_STREAM_MAPPING_PASS`: historical H01 seed0..9 map uniquely by schedule SHA-256 to existing H01/train stream indices 0..9. The reused native bank audit is PASS: 7404 shards, 311,500,812 samples, 1,246,832,496 bytes. No new GADEN run and no neural training were used.

## 2. Final-prefix fixed-trajectory result

FULL true-carrier raw score ranks for seed0..9:

`[1, 2, 7, 7, 14, 5, 14, 18, 3, 29]`.

Aggregate:

- Top-1: 1/10
- Top-5: 4/10
- Top-10: 6/10
- median rank: 7/210
- mean rank: 10/210
- median normalized rank: 0.028708
- final severe failures with normalized rank >0.5: 0/10.

This supports useful source ordering on historical H01 trajectories, but it is not yet a closed-loop GO result.

## 3. Existing ablations and what can/cannot be concluded

### M2 nuisance marginalization — supported

`-M2` ranks:

`[3, 4, 11, 9, 32, 11, 32, 32, 9, 22]`.

Compared with FULL:

- FULL better: 9/10
- tie: 0/10
- `-M2` better: 1/10
- mean rank: FULL 10.0 vs `-M2` 16.5
- one-sided sign probability for >=9 wins under p=0.5: 11/1024 ~= 0.0107.

Therefore finite predictive-distribution marginalization has clear H01 historical support and remains a core module.

### M3 trajectory coherence — not supported by this final-prefix test

`-M3` ranks:

`[3, 3, 8, 8, 12, 5, 11, 17, 1, 20]`.

FULL better 4, tie 1, `-M3` better 5; mean rank is 10.0 for FULL and 8.8 for `-M3`. Do not claim an M3 benefit from this result. Whether coherence matters at the actual online source-update boundaries remains to be tested before removing it from runtime.

### M4 adjacent temporal increments — no demonstrated final-prefix value

`-M4` final ranks are exactly identical to FULL for all 10 seeds. The arbitrary 25/50/75% prefixes differ only slightly in a few cases. The current adjacent-increment M4 must not be used to justify a temporal-network innovation.

### M1 sensor canonicalization — old ablation is invalid

The replay's original `-M1` compared measured `M_obs` directly against physical `C_sim`. Those are different observation domains, so the apparent 5/10 Top-5 and small rank improvement cannot be interpreted scientifically.

The corrected one-module removal is:

- FULL: inverse `M_obs -> C_obs`, compare `C_obs` with physical `C_sim`;
- `-M1`: keep `M_obs`, forward-filter each `C_sim` through the same frozen source-independent persistent sensor `T`, compare `M_obs` with `T(C_sim)`.

A 10-seed evaluation-only check using archived physical truth verifies this forward recurrence against measured traces: worst absolute mismatch is about `7.18e-7 ppm`, with RMSE about `2.7-2.9e-7 ppm`, i.e. serialization-level parity.

The C++ runtime has been corrected accordingly in `PFDEIEngine.hpp`. Historical V1 replay output is preserved rather than overwritten.

## 4. Major new blocker: online prefixes

FULL raw true-source ranks at arbitrary fixed fractions were:

- 25%: `[5,5,8,20,156,149,153,155,153,148]`, median 148.5, Top-5 2/10;
- 50%: `[3,14,24,21,20,22,40,46,4,4]`, median 20.5, Top-5 3/10;
- 75%: `[1,5,11,15,20,26,38,36,3,33]`, median 17.5, Top-5 3/10;
- 100%: `[1,2,7,7,14,5,14,18,3,29]`, median 7, Top-5 4/10.

Therefore terminal ranking is substantially better than early ranking. A closed-loop controller cannot be qualified from terminal replay because it would react at intermediate source updates and could be driven into the wrong basin before terminal evidence accumulates.

The 25/50/75% points are not the PMFS decision times, so they are diagnostic only. The next decisive test must use the five actual historical source-update times for each seed (roughly 66 s, 117-125 s, 172-178 s, 223-234 s, 276-287 s depending on seed).

## 5. Major new blocker: A0 evidence-to-posterior mapping

The replay reports raw physical-score true-source rank and the A0 posterior argmax separately. They are not equivalent. Example seed0 has true source raw score rank 1, while the A0 selected carrier is `quadtree_26_14_2_2`, not the true `quadtree_22_16_2_2`.

This is plausible under the current contract because A0 uses:

`q(s) proportional q0(s) * exp(z_rank(s))`,

and the geometry prior is area-weighted. In H01 the true carrier contains one free PMFS cell, whereas common competing 2x2 carriers contain four free cells, giving a 4x prior-mass ratio. The Gaussian rank adapter is not a calibrated physical likelihood, so its evidence scale may be too weak to overcome a legitimate area prior even when the physical score ranks the true carrier first.

Do not "fix" this by deleting `q0`, multiplying z by an outcome-tuned temperature, or forcing the raw top candidate. The next replay must report, at every actual source update:

- raw physical-score true-carrier rank;
- geometry-prior true-carrier rank;
- A0 posterior true-carrier rank;
- A0 rank shift relative to raw score;
- posterior entropy/max mass/truth mass;
- posterior expected-location error when evaluation truth coordinates are supplied separately.

The inference-to-probability calibration problem must be solved before closed-loop ON if A0 systematically destroys useful physical ordering.

## 6. Neural-network decision after this replay

Do **not** launch the previously considered TrajCast-style autoregressive trajectory network.

Reason: its empirical premise was that M3 coherent member trajectories and M4 ordered temporal increments provide source information beyond level/distribution evidence. On the historical H01 final-prefix replay, M3 has no positive ablation support and M4 is exactly neutral. This also agrees with the earlier SCTT order/shuffle warning.

The only currently strong modular evidence is M2 nuisance-distribution marginalization. If a neural amortizer is eventually needed, its scientific target should be robust distribution/set-conditioned source evidence or tail-risk reduction, not temporal autoregression, unless actual source-update replay provides new pre-outcome evidence for M3/M4.

## 7. Immediate next gate — existing data only

Use `experiments/cg_pc_ctt/pf_dei_h01_source_update_replay.py` on the already materialized H01 seed0..9 physical views and the existing FULL60 archive.

This script:

- reads exact `source_update_timing.csv` boundaries;
- uses only samples causally available by each update;
- implements clean M1 removal as `M_obs` vs `T(C_sim)`;
- reports raw score, q0 and A0 posterior ranks separately;
- optionally reports posterior expected-location error using evaluation-only truth coordinates;
- runs FULL, `-M1`, `-M2`, `-M3`, `-M4` without changing any scorer parameter.

Expected compute: seconds to a few minutes; previous 10-seed five-mode full replay took about 35.6 s after the bank view was materialized. No new GADEN and no neural training are authorized.

## 8. Stop/continue rule

Do not start formal closed-loop ON until this source-update replay is examined.

- If raw physical ordering is already poor at actual source updates, the direct backend is not online-ready; do not rescue it with neural training.
- If raw ordering is useful but A0 systematically degrades it, solve/freeze the evidence-calibration layer using outcome-independent simulation/null calibration before ON.
- If M3/M4 remain neutral or harmful at actual updates, remove/weakly describe them rather than building a temporal network around them.
- If M2 remains consistently beneficial, retain predictive nuisance marginalization as the strongest currently supported inference module.
