# D0 gate and strong baselines

Targets are already OPEN development data. This D0 is a mechanism bridge, not
fresh confirmation.

## Candidate support

Every target is ranked against the same six sources in its environment.

## Models

### B0 — PMFS presence only
Bernoulli likelihood from the newly exported PMFS presence map.

### B1 — ICRA-2026 concentration-rank analogue
Use the PMFS unconditional multiplicity mean as the candidate estimated gas
feature. Flatten the 10 x 30 target concentrations and the candidate prediction
(repeated over the ten observation times). Compute EDF ranks exactly as Eq. 5
of Jin et al. (ICRA 2026); rank candidates by squared EDF-rank discrepancy.
Any variance constants common to candidates do not affect ranking.

### B2 — calibrated value diagnostic
Compare target concentration to candidate unconditional multiplicity after a
single positive least-squares scale fit. This is a calibrated-sensor diagnostic,
not the novelty baseline.

### M — Marked-Encounter PMFS
`ell_occ + ell_mark` from `01_SCIENTIFIC_OBJECT.md`.

### U — GADEN-reference upper diagnostic
Use the 12 existing GADEN references/source to estimate the conditional mark
pattern. This is NOT deployable; it only answers whether failure of M is due to
the PMFS multiplicity proxy rather than absence of mark information.

## Primary mechanism endpoint

The six sources are three frozen 0.3 m neighbour pairs.

For target truth s* and its predeclared paired neighbour k, compute:

`Delta_pair = [ell_M(s*)-ell_M(k)] - [ell_B0(s*)-ell_B0(k)]`

which reduces to the incremental mark log-odds.

Aggregate target -> source -> environment; do not let a source with more targets
receive higher weight.

## Decision

`ME_PMFS_D0_MARK_FORWARD_SIGNAL` iff ALL:
1. environment-level mean Delta_pair > 0 in all 3 environments;
2. M mean true rank <= B0 in all 3 environments;
3. M strictly improves mean true rank in >=2/3 environments;
4. M Top-1 is non-adverse in every environment;
5. M mean rank is better than or equal to B1 in every environment;
6. no target that B0 ranked first is pushed below rank 3 by M.

Interpretation: the information PMFS discards at the binary update can be
recovered from its own filament multiplicity and adds source discrimination.

`ME_PMFS_D0_MARK_INFORMATION_FORWARD_INADEQUATE` iff:
- the GADEN-reference upper diagnostic U improves over B0, but M fails the
  signal gate.

Interpretation: marked observations are useful, but raw PMFS filament
multiplicity is not yet a faithful amplitude forward; a learned/physical mark
head is required.

`ME_PMFS_D0_NULL_OR_ADVERSE` iff neither M nor U provides consistent
incremental mark evidence.

`ME_PMFS_D0_HOLD_PARITY_OR_ASSET` only for native parity/data-contract failure.

No threshold can be changed after the candidate mark bank is generated.
