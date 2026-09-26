# Exact scoring ablation

## Frozen inputs

Use the historical House01/seed0 R1 source-corrected snapshot and **C-arm** Native forward maps.

Required:
- `measurement_events.csv`
- `measured_map_at_update.csv`
- `C_candidate_scores.csv`
- all 87 `.f32` C-arm candidate maps referenced by `C_candidate_scores.csv`
- historical `r1_scores_frozen_manifest.json` for hash verification

Expected source-blind input hashes:
- measurement_events.csv: `f05114b558132a1c62d1ecf705d9bdd2f066905b9c48881b3457b9f0d9cd15e9`
- measured_map_at_update.csv: `dee2f4e154860ae74bf9fd5375b4721864cdd96dc775badfbdc4ee56f2019eab`
- C_candidate_scores.csv: `780366a446f4c27496b60939aec098d50d7ba6c516ac7f8b387b3b75f9469419`

The 87 map hashes must match `arms.C.candidate_map_sha256` in the historical manifest.

## No forward rerun

Do not build or run PMFS. The same frozen hit map for each candidate is scored four ways.

### M — Native full-map product

Recompute exactly:
`log M(s) = sum_{free cells i} log(1 - c_i * 0.3 * |m_i - p_i(s)|)`.

Parity gate: exponentiating `log M` must reproduce the historical C-arm `source_score` for every candidate within `1e-10` absolute tolerance (or tighter if possible). If parity fails, STOP execution.

### S — sensor-site-only PMFS factor

Use the **same PMFS per-cell factor** but multiply only over the four unique robot cells that produced raw observations.

This changes only the evidence support; it does not change the forward model or the PMFS per-cell fit function.

### Elog — raw-event Bernoulli log score

For each of the 20 raw hit/miss events at robot cell `x_t`, use the candidate's frozen simulated hit frequency `p_s(x_t)`:

`Elog(s)=sum_t [h_t log p_s(x_t) + (1-h_t) log(1-p_s(x_t))]`.

Clip only for numerical safety at `eps=1e-6`, and report the number of clipped evaluations.

### Ebrier — raw-event Brier score

`Ebrier(s) = -sum_t (h_t - p_s(x_t))^2`.

Higher is better. This is a second proper-score diagnostic that has no log clipping.

## Source-blind freeze

Before opening truth, write and hash:
- `candidate_scores.csv`
- `event_support_audit.json`
- `native_parity.json`
- scoring script

Only after hashes are frozen may truth be read.

## Truth evaluation

Historical truth:
- source = (-0.40, -2.90)
- truth-containing leaf = `quadtree_23_14_1_3`

Report for M/S/Elog/Ebrier:
- truth rank / 87;
- top-1 candidate and center error;
- truth score;
- Spearman rank correlation against M.

Also report:
- M->S, M->Elog, M->Ebrier truth-rank improvement;
- rank displacement median/max;
- top-10 candidates for every arm;
- whether Elog and Ebrier agree on the direction of truth-rank change.

## Decision labels

`EVIDENCE_PSEUDOREPLICATION_SIGNAL_STRONG`
- S, Elog and Ebrier all improve truth rank versus M;
- Elog and Ebrier each improve by at least 10 ranks;
- at least two of S/Elog/Ebrier do not worsen top-1 center error.

`EVIDENCE_PSEUDOREPLICATION_SIGNAL_POSITIVE`
- Elog and Ebrier both improve truth rank versus M, with no contradiction in top-1 spatial error; or
- S alone gives a clear improvement of at least 10 ranks while event scores are non-adverse.

`EVIDENCE_PSEUDOREPLICATION_NULL_OR_ADVERSE`
- otherwise.

No parameter tuning after truth is opened.
