# TROQL/OQIC external gate V1 — development result

Date: 2026-09-14

## Outcome

`TROQL_OQIC_EXTERNAL_DEVELOPMENT_NO_GO`

The frozen V1 development gate did not authorize opening the confirmation files.
The same-source null edge (`Exp01` versus `Exp02`) remained unresolved, as required,
but the different-source development edge (`Exp02` versus `Exp03`) did not meet the
pre-registered per-direction replication count.

## Frozen observations

- Calibrated absolute-margin threshold: `0.11455466659057079`.
- Required count above threshold: at least `18/20` in each direction.
- Null edge counts: `1/20` and `0/20`; edge unresolved.
- Source edge counts: `14/20` and `16/20`; edge unresolved.
- Source edge median margins: `0.14238744420771066` and
  `0.13844564437731505`.

The V1 rule therefore behaved safely on the null pair but was too weak under its
own frozen source-resolution criterion. A positive median, or a majority of
positive blocks, is not substituted for the failed gate.

## Integrity and claim boundary

- Result artifact: `experiments/troql_oqic_external_v1/DEVELOPMENT_GATE.json`.
- Result SHA-256: `5741f148ec3ab2f60ee79f1fd2a4b86022205622297546e0f1070d5ddfda6613`.
- Frozen policy SHA-256: `8364148adcb393d586aa7efff0aee1fafae9da788bfea9633a660d79006a1e06`.
- Frozen scorer SHA-256: `a24be01a0f672c2c2f63ca38af2d7974e67bb5b58865363dd3bd04c24e00c692`.
- `Exp06`, `Exp07`, `Exp08`, and `Exp09` were not opened by the scorer.
- No protected project bank, held wind, unseen seed, or new House was used.

This result does not authorize a cross-dataset identifiability claim, an online
PMFS claim, or a closed-loop localization-improvement claim.

## Mechanism diagnosis

The failed V1 criterion compounds a 95% pointwise nuisance cutoff with a 90%
per-direction exceedance requirement. That tests whether nearly every replicate
is individually beyond an extreme nuisance quantile; it is not a calibrated test
of whether the replicated source-edge distribution dominates the nuisance-edge
distribution. A subsequent development revision may replace only this evidence
release rule with a frozen distributional-dominance certificate. It must leave
the representation, development/confirmation split, raw hashes, and claim
boundary unchanged, and it must be committed before any confirmation input is
opened.
