# Exploratory offline probe: predictive memory vs source-specific memory

Date: 2026-09-30

Status: **POST-HOC DISCOVERY ANALYSIS / NOT A PREREGISTERED GATE**

Parent evidence:
- R0: `OCB_R2_MECH_CROSS_TIME_STABLE`
- R1: `OCB_R2_R1_BROAD_MEMORY_REQUIRED`
- R1 evidence commit: `d489ff95973bcd4929fe7988cdeb82352b99b582`

## Why this probe was run

R0/R1 prove that intact cross-time pairing contains source-discriminative
information and that this information extends beyond adjacent two-slot blocks.

That result alone does **not** prove a Mori-Zwanzig-style non-Markovian closure.
A first-order Markov process can still have long-lag correlations.

Before promoting Mori-Zwanzig / generalized Langevin memory as the paper's
mother theory, this exploratory probe asks two stricter questions:

1. Does using a longer observed history improve prediction of the next
   30-D snapshot, beyond using the current snapshot only?
2. Is that predictive-memory gain itself reliably more compatible with the
   true source than with the matched alternative source?

## Data and parity

The analysis directly reused the 64 frozen `10 x 30` OCB-R2 discovery tensors
stored under:

`evidence/ocb_r2/mechanism_census_r0/inputs/*.pooled.npy`

The same 8 contexts, 2 sources/context and 4 realizations/source were used.
For every held-out target, the candidate bank used the other three
realizations (K=3). No confirmation/H03 data were accessed and no new
simulation or extraction was run.

## Parameter-free predictive-memory diagnostic

For a target trajectory Y and one candidate-source reference bank:

1. At prediction time t, compare the target history to each of the three
   reference histories with normalized Hamming distance.
2. Select the nearest reference realization. If several references tie, average
   their future errors.
3. Predict the next 30-D snapshot from the **same realization identity**.
4. Define the shuffled null as the mean future error over all three possible
   future realization identities. This is the exact expectation after breaking
   the current/history-to-future pairing while preserving the future snapshot
   multiset.
5. The predictive memory gain is:

   `M_s(H) = error_shuffled - error_intact`

   where H is the number of history slots used for matching.

Positive `M_s(H)` means intact realization history predicts the next snapshot
better than the marginal-preserving shuffled future.

This is deliberately simple: no learning, no bandwidth, no neural network and
no tuned hyperparameter.

## Result A — broad history improves future predictability inside the true source

All 16 source×context groups had positive truth-source predictive-memory gain
for H=1 through H=4. Fifteen of sixteen remained positive for H=5.

Median truth-source gain:

| history | overall | House01 | House02 | positive groups |
|---|---:|---:|---:|---:|
| H1 | 0.01358 | 0.01204 | 0.01821 | 16/16 |
| H2 | 0.01589 | 0.01589 | 0.02031 | 16/16 |
| H3 | 0.01815 | 0.01815 | 0.02183 | 16/16 |
| H4 | 0.01817 | 0.01817 | 0.02396 | 16/16 |
| H5 | 0.02014 | 0.01931 | 0.02792 | 15/16 |

History increment relative to current-snapshot matching:

### H3 - H1

- pooled median: `+0.00612`
- House01 median: `+0.00643`
- House02 median: `+0.00368`
- positive source×context groups: `14/16`
- positive contexts: `7/8`
- exact 8-context sign-flip reference: `0.01172`

### H5 - H1

- pooled median: `+0.00772`
- House01 median: `+0.00772`
- House02 median: `+0.00971`
- positive source×context groups: `12/16`
- positive contexts: `8/8`
- exact 8-context sign-flip reference: `0.00391`

Exploratory interpretation:

> the projected 30-D observation history contains predictive information about
> the future beyond the current snapshot alone, and the effect is broad enough
> to persist when several history slots are used.

This is consistent with a memory-closure interpretation, although it is not a
formal proof of Mori-Zwanzig dynamics.

## Result B — a naive source-specific nearest-history memory score is NOT stable

To test whether the same simple diagnostic is directly useful for source
identification, define:

`J_H = M_truth(H) - M_alternative(H)`

If a simple candidate-specific memory operator were already sufficient,
`J_H` should be consistently positive.

It was not.

### H3

- pooled median: `+0.00317`
- House01 median: `+0.00407`
- House02 median: `-0.00466`
- positive groups: `9/16`
- positive contexts: `5/8`
- exact context sign-flip reference: `0.38672`

### H5

- pooled median: `+0.01056`
- House01 median: `+0.01278`
- House02 median: `-0.00097`
- positive groups: `10/16`
- positive contexts: `5/8`
- exact context sign-flip reference: `0.10547`

The same instability appears in the direct lag-prediction version. For example
the lag-3 source-specific differential has House01 positive but House02
slightly negative.

## Scientific implication

This split result is important.

R0/R1 already showed that **path dependence is source-discriminative** when it
is evaluated as a distributional trajectory object with fair-U Energy Score.

The present probe additionally shows that **history is predictively useful**
inside the true source.

However a very simple nearest-history predictive closure does not extract a
stable source-specific likelihood correction across both Houses.

Therefore:

1. Mori-Zwanzig / non-Markovian closure is now a plausible **physical
   explanation** for why history matters after projection.
2. It is **not yet justified as the final source-inference formulation**.
3. The strongest current inference evidence still favors a **path-distribution
   / dependence-ratio** view: the useful information is robust in the joint
   trajectory distribution, while naive next-step memory prediction loses the
   source-specific effect.
4. Do not implement a first-order or nearest-history MZ model and call it the
   main innovation.
5. The next R2 should explicitly distinguish:
   - predictive closure memory;
   - source-discriminative path likelihood ratio.

A good R2 formulation should test whether a low-complexity broad-memory
density-ratio / block-path score can reproduce the R0/R1 source differential.
Only after that succeeds should a more expressive MZ-memory kernel, copula
flow, or related model be developed.

## Boundary

This analysis is post-hoc on discovery data and must not be used as a
confirmation PASS. It is a theory-selection diagnostic only. H01/H02
confirmation and H03 remain sealed.


## Additional comparison — path-distribution signal remains much cleaner than naive predictive closure

As a second post-hoc diagnostic, the already-frozen R1 lag effects were
combined with **fixed equal weights**; no lag was selected by target result.

For lags 1–3:

`I_PATH_1_3 = (I_LAG1 + I_LAG2 + I_LAG3) / 3`

Results:

- pooled median: `+0.01214`
- House01 median: `+0.01247`
- House02 median: `+0.01007`
- positive source×context groups: `16/16`
- positive contexts: `8/8`

For lags 1–5:

`I_PATH_1_5 = mean(I_LAG1 ... I_LAG5)`

Results:

- pooled median: `+0.00914`
- House01 median: `+0.00914`
- House02 median: `+0.00747`
- positive groups: `15/16`
- positive contexts: `7/8`

This contrast is informative:

- a simple nearest-history **predictive** memory correction is not stably
  source-discriminative across both Houses;
- a simple multi-lag **path-distribution** dependence functional is stable
  across both Houses.

Therefore the next method should not begin from a first-order prediction model.
The current evidence more directly supports a source-conditioned broad-memory
path/dependence factor, with Mori-Zwanzig retained as a physical explanation
for projection-induced memory unless a later conditional-memory gate supports
a stronger closure claim.
