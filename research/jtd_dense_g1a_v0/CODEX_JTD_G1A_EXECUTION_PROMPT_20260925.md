# CODEX TASK — JTD-G1A 168-Source Dense Frozen-Bank Assessment

Branch: `research/jtd-dense-g1a-v0`

Authoritative files:
- `research/jtd_dense_g1a_v0/JTD_ROUTE_DECISION_AFTER_PRO_REVIEW_20260925.md`
- `research/jtd_dense_g1a_v0/JTD_G1A_DENSE_CHARTER_20260925.md`

Upstream scientific status:
- G0 discovery GO remains;
- B0 bridge FAIL remains;
- B1 K_min=4 remains supportive only;
- E1 cross-environment = HOLD;
- do not execute standalone E1D.

## Hard scope

- 0 new plume;
- use the full compatible 168×16 House02 `3,5-1_slow` dense bank;
- no source cherry-picking;
- no House01 DEV;
- no House03;
- no closed loop;
- no neural model;
- no tuning of G0 representation/likelihood.

## Stage A0 — compatibility audit before scoring

Verify all physical/observation/model-contract items in the charter.
Freeze a compatibility report and input hashes before running scientific scoring.
Explicitly compute the intersection between the original G0 18-source panel and the 168-source bank.

If A0 fails: return `JTD_G1A_DATA_CONTRACT_STOP` and stop.

## Stage G1A — models

Run the same fourfold 12-reference/4-target evaluation for:
- FULL;
- BLOCK-PRODUCT;
- MATCHED-BLOCK-DIAG;
- DIAG-COV;
- 200 SHUFFLED destructive-null models/fold.

Use domain-separated SHA256 randomization keys; do not reuse the historical arithmetic seed formula.

Store complete normalized posterior/log-posterior outputs for all 168 candidates and every target for FULL/BP/MBD/DIAG.

## Metrics

Compute every probabilistic, dense-spatial, breadth, heavy-tail and nearest-neighbor diagnostic specified in the charter.

Primary comparisons:
- FULL vs BP;
- FULL vs MBD.

SHUFFLED is continuity/diagnostic only.

## Independent checks

Independently recompute:
- source-level primary Delta_BP and Delta_MBD;
- 5,000-source bootstrap sensitivity intervals;
- G1-G6;
- all source-count breadth criteria;
- 0.5m/1.0m posterior mass and expected-distance metrics;
- tail-removal diagnostics.

## Required deliverables

- `JTD_G1A_A0_COMPATIBILITY.json`;
- `JTD_G1A_RESULT.json`;
- target-level FULL/BP/MBD/DIAG metrics CSV;
- source-level summary CSV;
- fold summary CSV;
- complete posterior/logposterior arrays;
- nearest-neighbor diagnostic CSV;
- Gaussian wrong-neighbor decomposition CSV;
- SHUFFLED aggregate/null summaries and derangement-key manifest;
- bootstrap/sensitivity outputs;
- independent recomputation JSON;
- code/input/output SHA256 manifests;
- branch/final commit;
- review package path/bytes/SHA256.

Final decision exactly one:
- `JTD_G1A_GO_DENSE_PROBABILISTIC_UTILITY_AND_CROSSBLOCK_CONTRIBUTION`
- `JTD_G1A_HOLD_SCORE_UTILITY_TRADEOFF`
- `JTD_G1A_STOP_DENSE_UTILITY_OR_MECHANISM_NOT_CONFIRMED`
- `JTD_G1A_DATA_CONTRACT_STOP`

Stop immediately after G1A.