# Persistent-source PMFS R1 development decision

Decision: `MECHANISM_NULL_OR_ADVERSE`.

Source-blind scores were frozen and committed before the historical truth JSON was loaded.
Four source-blind output files are byte-identical across the deterministic repeat.
No scientific formula or supplied scorer/evaluator code was modified.

| Arm | Truth rank / 87 | Truth score | Top-1 center error (m) |
| --- | ---: | ---: | ---: |
| R | 52 | 0.078324927782763426 | 3.549493167970311 |
| C | 53 | 0.078659373907497512 | 7.1037598698007356 |
| P | 54 | 0.081789156313764239 | 3.549493167970311 |

R-minus-P truth rank improvement: -2.
Spearman R-vs-P: 0.99216300940438873.
Median / maximum absolute candidate-rank displacement: 1 / 16.

| Leaf area (cells) | Candidate count | Median P-R score | Median R-P rank |
| --- | ---: | ---: | ---: |
| 1 | 5 | 6.0734220062278138e-05 | 1 |
| 2 | 15 | -9.0722793960607007e-06 | 1 |
| 3 | 9 | 4.5130053128450908e-05 | -1 |
| 4 | 13 | 0.00010683516879961275 | 0 |
| 5 | 10 | -6.7880518750452784e-06 | -0.5 |
| 6 | 5 | 0.00010100879793032563 | 0 |
| 8 | 5 | 4.8502474221050196e-05 | -2 |
| 10 | 7 | 0.00016040230145300538 | 1 |
| 12 | 2 | 0.0084544008496180156 | 0.0 |
| 15 | 4 | 0.002904147422398072 | 1.0 |
| 16 | 3 | 3.6105259767391931e-05 | -1 |
| 20 | 7 | 0.00062802389626413963 | 1 |
| 25 | 2 | 0.001695742085137327 | 1.5 |

## Five 1x1 diagnostic leaves

| Candidate | P-R score | R-P rank |
| --- | ---: | ---: |
| quadtree_14_31_1_1 | -0.0019105309342788424 | 2 |
| quadtree_7_27_1_1 | 6.0734220062278138e-05 | -1 |
| quadtree_24_25_1_1 | 0.039617320572178483 | 1 |
| quadtree_28_27_1_1 | -0.0018211705995205829 | 3 |
| quadtree_19_14_1_1 | 8.3544956570397177e-05 | -1 |

All raw area-group and per-candidate metrics are preserved in truth_evaluation.json.
Development-only result; no main-innovation or closed-loop promotion.
The frozen NULL/ADVERSE result is retained without rescue. No further experiment is started.
