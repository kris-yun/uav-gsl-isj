# CTT temporal audit upload completeness — 2026-08-30

Status: `SOURCE_UPLOAD_COMPLETE`

Branch: `research/ctt-causal-temporal-audit-v3-v7-20260830`

Purpose: provide Codex1 an explicit inventory of the V1--V7 causal-temporal falsification source chain. This document concerns source-code completeness only; it does not upgrade any NO-GO verdict and does not authorize closed loop.

## Source integrity table

| File | Original frozen SHA-256 | Bytes | Upload/recovery status |
|---|---|---:|---|
| `train_eval_ctt_temporal_nre.py` | `4bb98dc592ddaafabc50bc45b01d8a583aca97252c5b96e6c2b95a041e94444e` | 13480 | `SOURCE_RECOVERY_HASH_MATCH`; original V1 source recovered byte-for-byte, `py_compile` PASS, uploaded |
| `v2_energy_temporal_nre.py` | `ab3f9bfac72c91f8ec39a4e77b21fe61fc97467b15c2836c6b75c41138dbd6e9` | 8158 | original audit source uploaded |
| `v3_physics_order_temporal_nre.py` | `889c417cd0fc5b3aca3a8b983fde8e42d03600d42a73a62701c817e44707f0e7` | 12590 | original audit source uploaded |
| `v3_parallel_median_eval.py` | `a60e58e39dbf10d7cade20ddaf9c2a9ecf707ed37a9b696000cf228bc4d853d8` | 2920 | original evaluator uploaded |
| `v4_physics_certified_interval_temporal_nre.py` | `a82035cbd01b4e5ace11cff0012073dcb5116f0f9247569ca5f0213ca92ef2da` | 22744 | `SOURCE_RECOVERY_HASH_MATCH`; recovered byte-for-byte, `py_compile` PASS, uploaded |
| `v4_parallel_median_eval.py` | `c1e85d267938a47e7c29ca9fe8d865b71b3d520ac45ee03c42729ae7a96b200b` | 539 | original evaluator uploaded |
| `v5_physics_certified_partial_order_temporal_ranker.py` | `fceb56acd63c9b63f7cb4851332f99294d903b99f5f5407d3882cf1327394cc2` | 13182 | `SOURCE_RECOVERY_HASH_MATCH`; recovered byte-for-byte, `py_compile` PASS, uploaded |
| `v5_parallel_eval.py` | `9ac096f19a5cbfe42501d3985ff6e9632dc17eb34413ab6bd58ae34ffc81dd92` | 567 | original evaluator uploaded |
| `v6_physics_certified_isotonic_temporal_evidence.py` | `6152e6850ec25b91f234c120c237997cc37992f6cb4fae843a671dc0f2b28448` | 15029 | `SOURCE_RECOVERY_HASH_MATCH`; recovered byte-for-byte, `py_compile` PASS, uploaded |
| `v6_parallel_eval.py` | `85aa98fa40fb5dd56c3c0629c42c7116ab9c07c18a70b5674f91a49d6f9409f3` | 564 | original evaluator uploaded |
| `v7_physics_certified_nnls_temporal_evidence.py` | `7dd0cef9ae4b1a7db74230ee250527cfd45b93dc9913a9d0bf2f4aef01399434` | 13768 | `SOURCE_RECOVERY_HASH_MATCH`; recovered byte-for-byte, `py_compile` PASS, uploaded |
| `v7_parallel_eval.py` | `d44b03a2cb34f9dbd5c7bee7dd76ab1b9d67bfd9c17400b4a51c9cf519a0dce0` | 560 | original evaluator uploaded |

The authoritative file-content hashes above are also recorded in `experiments/cg_pc_ctt/ctt_temporal_audit_20260830/CTT_TEMPORAL_AUDIT_FILE_SHA256.tsv`.

## Important hash distinction

GitHub reports a blob SHA for repository objects. That value is **not** the SHA-256 of the file bytes. Codex1 must clone/fetch the reviewed commit and calculate SHA-256 on the actual file contents before comparing with the table above.

## Evidence completeness

Source completeness is `FULL` for the 12 Python files.

Historical result-evidence completeness in this Git branch is `PARTIAL`:

- combined frozen V3--V7 evidence archive recorded at freeze time: `CTT_TEMPORAL_AUDIT_V3_V7_EVIDENCE_20260830.tar.gz`, SHA-256 `3b28577f8d617645a2573d75dd1dbbe9d6cdc7c33e8b7af585f7a99aaa98eade`;
- that combined archive is not checked into this branch/current artifact set;
- V3-only evidence archive exists separately as `CTT_TEMPORAL_V3_H01_FRESH_GATE_EVIDENCE_20260830.tar.gz`, SHA-256 `27a6e9aa89526f41a452b61caa9a0e45f0b4799224ac1cbd43c580059b5c7cce`.

Codex1 must not replace missing evidence by retraining, changing held subsets, or generating fresh pseudo-reproduction data. It should report `EVIDENCE_COMPLETENESS=PARTIAL` unless the exact combined archive is later supplied and hash-verified.

## Scientific disposition

The source chain is preserved so the failure mechanism can be audited. It must not be interpreted as a menu from which to select a post-hoc winner. V3--V7 collectively support the conservative engineering/scientific decision:

`CLOSED_LOOP_NOT_AUTHORIZED`

The next scientific implementation should replace generic residual-TCN temporal representation with explicit candidate-conditioned transport-phase / first-passage / hazard and persistent-sensor event/no-event inference before any new closed-loop authorization gate is considered.
