# CTT House03 M2/M3 premise freeze

Status: frozen before M2/M3 result inspection.

## Inputs

- CTT M1 is frozen at `M1_DIRECT_GO` plus `M1_ORDERING_GO`.
- Physical state library: House03 wind-context trace bank V2.
- Test wind contexts: 1 and 2 only.
- Latent transport states: members 0--5.
- Synthetic observations: held-out members 6 and 7.
- No real source coordinate or final localization error is an input.
- The physical field retains all 200 native 0.2 s bins.  M2/M3 observe it only
  at the actual PMFS event-ledger times inside a 40 s causal window.  The
  canonical premise path/times are the first 20 events of the already-revealed
  House03 update-4 ledger (about 2 s spacing).  They are fixed independently of
  every synthetic source and transport member.  The earlier dense-pose V1
  result is retained as a diagnostic but is not eligible to advance.

## Frozen observation model

For trace occupancy state `O_tk` at the virtual sensor cell, use a binary
symmetric detector with fixed flip probability `epsilon=0.05`:

`P(y_t=1 | O_tk) = 0.95` if occupied and `0.05` otherwise.

This parameter is not estimated from truth or closed-loop error and will not be
tuned after a premise result.

## M2

- `J1 = log p_iid(y|N,s)`: independent mixture over the six physical transport
  members, normalized by the exact Poisson-binomial count probability.
- `J2 = log p_HMM(y|N,s)`: forward likelihood under the causal-front transition
  matrix, normalized by its exact count probability.
- Transition overlap is the exact binary-front Bhattacharyya coefficient;
  zero-overlap rows use a self-loop.
- Matched distractors are the same eight nearest carriers used by M1.
- Primary increment: matched-source margin `J2-J1`, clustered by complete
  context, true carrier and held-out transport member.
- Control: deterministic time permutation of the observation sequence must
  erase at least 75% of the original increment.  `J1` is the independent-path
  control.

Pass requires positive mean increment, paired-bootstrap lower 95% bound above
zero, and positive median in both test contexts.

## M3

- `J3 = log p_HMM(N|s)` is computed by an exact count-augmented forward DP.
- Complete score is `J2+J3 = log p_HMM(y|s)`; no event is counted twice.
- Shifted-window control uses a +3-observation-slot misalignment
  without circular wrap.
- Candidate-constant count control must have exactly zero relative margin.

Pass requires positive conditional margin increment, paired-bootstrap lower
95% bound above zero, and positive median in both test contexts.  A failed M2
or M3 is preserved and blocks the 300 s closed loop.
