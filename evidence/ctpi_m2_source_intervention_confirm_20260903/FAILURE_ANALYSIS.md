# CTPI M2 source-intervention CONFIRM failure analysis

Terminal verdict: `CTPI_M2_SOURCE_CONDITIONED_PREDICTIVE_GATE_NO_GO`.

The experiment is integrity-valid: all 30 preregistered CONFIRM worlds completed,
all 450 source/action events were evaluated once, every count level `K=0..8` was
covered, and the frozen table/code hashes matched the pre-CONFIRM authorization.
No CONFIRM outcome was used to refit the table.

## Gate result

The frozen M2 table improved pooled means but failed the preregistered paired
repeatability criterion:

- NLL: `0.293576 -> 0.282481`; tape wins/losses `18/12`, one-sided exact sign
  `p=0.180797`.
- Brier: `0.088573 -> 0.087080`; tape wins/losses `15/15`, one-sided exact sign
  `p=0.572232`.
- ECE-5: `0.041975 -> 0.024938`.
- H01 reversed in both pooled means (`NLL 0.314577 -> 0.323571`, `Brier
  0.093128 -> 0.096765`), although it did not meet the preregistered stronger
  definition of a stable reverse House.
- H02 improved on 7/10 tapes for both scores. H03 was weaker: 6/10 NLL and
  5/10 Brier wins.

Only `paired_sign_support` failed; the terminal verdict nevertheless remains
NO-GO because all preregistered criteria were conjunctive.

## Failure mechanism

The controlled-source intervention fixes the causal-label problem of the old
posterior-weighted candidate, but this implementation compresses the requested
law `P(Y_next | do(S=s), A=a, physical context)` to one global scalar lookup
`P(Y=1 | K)`, where `K` is the number of hitting members among eight. Source,
action, House, and transport-shape information survive only through this coarse
nine-level count.

That statistic was not sufficient for repeatable tape-level improvement. The
empirical CAL-to-CONFIRM event rates moved materially at intermediate levels:
`K=5: 0.650 -> 0.526`, `K=6: 0.553 -> 0.708`, and `K=7: 0.692 -> 0.846`.
The PAV fit pooled `K=4..6` to `0.620482`, so different physical contexts with
the same count received the same probability even when their reliability
differed.

The pooled CONFIRM NLL gain was concentrated in a few count levels: the summed
M2-minus-baseline NLL contributions were `-4.422` at `K=8` and `-2.544` at
`K=4`, while `K=7` contributed `+1.762` harm and `K=6` contributed `+0.397`
harm. Thus the average score improved, but the direction did not repeat across
world tapes and H01 reversed.

## Stop decision

This candidate is not authorized for M3, C++, ROS, or closed-loop evaluation.
The CONFIRM set is spent and must not be used to tune a replacement. The causal
source-intervention experimental design can be retained, but any future M2 must
pre-register a richer action/physical-context representation and use a new
held-out confirmation set.
