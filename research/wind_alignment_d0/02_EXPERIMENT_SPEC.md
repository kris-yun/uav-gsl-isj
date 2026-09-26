# Exact D0 experiment

## Frozen case and truth discipline

House01 / seed0 / R1 source update 1 only.

Candidate geometry: the same frozen 87 C-arm Native candidates.
Events: the same frozen 20 raw events.
Truth must remain unopened until all arm scores, permutation scores, hashes and
implementation are frozen.

Historical reference:
- Elog truth rank = 47/87
- Ebrier truth rank = 46/87
These numbers are evaluation references only; do not use them to tune forward
construction.

## P0 — replay parity

Using the same official/R1 C-arm forward kernel and deterministic RNG contract,
regenerate all 87 forward maps using the exact historical full spatial wind
field:
`state 0, z=0`.

Required before continuing:
- map geometry identical;
- every candidate identity identical;
- regenerated maps reproduce the historical C-arm maps to the tightest
  numerically justified tolerance;
- historical Elog/Ebrier scores reproduce.

If P0 fails: `WIND_ALIGNMENT_D0_HOLD_REPLAY_PARITY`.

## P1 — height-only arm

Change only the spatial wind field queried for forward simulation:
`state 0, z=0.30 m`.

Everything else remains P0-identical:
candidate geometry, PMFS parameters, deterministic source/transport RNG,
timesteps, delta time, scoring and events.

This arm isolates the z contract defect.

## P2 — 11-state forward bank at sensor height

Generate one deterministic candidate forward map for each:
`candidate (87) × wind state (0..10)` at `z=0.30 m`.

Use common deterministic random numbers across wind-state arms for a given
candidate so state effects are not confounded by a changed transport seed.

No GADEN plume simulation is allowed. These are only PMFS read-only candidate
forward replays driven by the existing House01 wind fields.

## Event-conditioned mixture

For event e with recovered state sequence
`k_e1,...,k_e10`, define at its robot cell x_e:

`p_match(s,e) = mean_j p(s, k_ej, x_e)`.

Use the already frozen proper scores:

`Elog_match(s) = sum_e h_e log p_match + (1-h_e) log(1-p_match)`

with eps=1e-6 only for numerical safety, and

`Ebrier_match(s) = -sum_e (h_e-p_match)^2`.

Higher is better.

This is explicitly a mixture diagnostic; do not call it a time-ordered plume.

## Controls

### C1 — site-pooled state mixture

At each of the four robot sites, pool the 50 state IDs from that site's five
events. Every event at that site receives the same pooled-state mixture.
This preserves local multi-state wind statistics but destroys event-specific
alignment.

### C2 — within-site permutation

Before truth is opened, generate 200 deterministic permutations with fixed seed
`2026092601`.

Within each site separately, permute the five recovered 10-state sequences
across its five events. Do not move a sequence to another site.

For every permutation compute all 87 Elog/Ebrier candidate scores and freeze
them. No forward rerun is needed.

## Source-blind outputs before truth

- `P0_parity.json`
- `forward_bank_manifest.json`
- `candidate_scores_source_blind.csv` containing P1, P2-match and C1
- `permutation_scores_source_blind.csv`
- all map hashes
- code hashes
- `SCORES_SHA256.txt`

Only then open the already historical truth.

## Truth evaluation

For P1 / P2-match / C1 and every permutation report:
- truth rank / 87 for Elog and Ebrier;
- truth score;
- top-1 candidate and center error;
- top-10.

Also report:
- P1 vs historical rank change;
- P2-match vs P1 rank change;
- P2-match vs C1 rank change;
- percentile of the matched truth rank among the 200 within-site permutations
  (lower rank is better);
- percentile of the matched truth score among permutations
  (higher score is better).

## Frozen decision labels

`WIND_ALIGNMENT_D0_HEIGHT_BASELINE_DEFECT`
- P1 improves both proper-score truth ranks relative to the historical static
  arm, while P2-match does not establish an alignment-specific effect beyond
  C1/permutations.
- Interpretation: repair baseline; do not call it innovation.

`WIND_ALIGNMENT_D0_DYNAMIC_SIGNAL`
- P2-match improves truth rank over **both P1 and C1 for Elog and Ebrier**;
- and for at least one proper score, the matched truth rank is better than at
  least 95% of the 200 within-site permutations;
- the other proper score must not be adverse relative to its permutation
  median.
- Interpretation: positive offline mechanism signal only. Next stage is a
  true time-ordered switching-transport test, still no closed loop.

`WIND_ALIGNMENT_D0_MIXTURE_ONLY`
- multi-state C1 and P2 both improve versus P1, but matched P2 does not beat
  C1/permutation controls.
- Interpretation: broad wind-state averaging helps; event alignment is not
  established. Not a main innovation.

`WIND_ALIGNMENT_D0_NULL_OR_ADVERSE`
- no reproducible source-identity improvement from P1 or P2, or proper-score
  directions materially contradict.

`WIND_ALIGNMENT_D0_HOLD_REPLAY_PARITY`
- P0 cannot reproduce the historical forward contract.

No threshold may be changed after truth is opened.
