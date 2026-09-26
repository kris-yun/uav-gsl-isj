# PMFS evidence pseudoreplication R1 decision

Decision: `EVIDENCE_PSEUDOREPLICATION_NULL_OR_ADVERSE`.

Freeze commit (pushed before the truth evaluator): `957781a646b748bcaec99c37d1759aa3218fdb48`.

The supplied scorer and evaluator are unchanged. The same 87 historical Native C-arm maps were rescored.
No forward simulation, GADEN, new plume, training, parameter tuning, additional House or closed loop was run.
Git storage attributes were corrected before truth evaluation to preserve exact CSV bytes; no scoring implementation patch was needed.

| Arm | Truth rank / 87 | Truth score | Top1 center error (m) | Spearman vs M |
| --- | ---: | ---: | ---: | ---: |
| M | 47 | 0.20371479113379398 | 6.2296391003338192 | 1 |
| S | 46 | -0.14746066186687923 | 5.3109698667693142 | 0.95216834701271269 |
| Elog | 47 | -17.523523873804326 | 3.5772756688407901 | 0.9107372164101486 |
| Ebrier | 46 | -2.369066904213966 | 5.3109698667693142 | 0.94994361200676514 |

Native parity max absolute error: 9.1593399531575415e-16 (tolerance 1e-10).
Deterministic repeat: PASS for all four source-blind files.
Raw events / hits / misses / unique robot sites: 20 / 1 / 19 / 4.
Free cells / confidence >0 / >0.01 / >0.1: 626 / 276 / 130 / 84.
Elog clipping evaluations: 760 (frozen epsilon 1e-06).

| Arm | Truth rank improvement vs M | Median / max absolute rank displacement | Top1 candidate |
| --- | ---: | ---: | --- |
| S | 1 | 1 / 25 | quadtree_11_1_3_4 |
| Elog | 0 | 4 / 43 | quadtree_17_26_2_2 |
| Ebrier | 1 | 1 / 25 | quadtree_11_1_3_4 |

Elog / Ebrier truth-rank direction agreement: False.
All top-10 candidate lists and exact raw metrics are retained in truth_evaluation.json.
Development-only NULL/ADVERSE is retained. Execution stops here; no rescue or next mechanism experiment is started.
