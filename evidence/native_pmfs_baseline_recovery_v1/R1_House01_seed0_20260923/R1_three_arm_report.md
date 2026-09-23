# R1 House01 seed0 three-arm candidate-forward replay

Scores and maps were frozen before truth was opened (`92d9092d1a2f7ddda1fd798ac81672e416c7c71970e6154fb4ab5ce67f069740`).
The comparison uses one observation snapshot and its 87 exported Native candidate regions.

| Arm | Candidate count | Truth candidate | Rank | Truth score | Top-5 IDs | Wind min / median / max | Score SHA256 |
|---|---:|---|---:|---:|---|---|---|
| A | 87 | quadtree_23_14_1_3 | 47 | 0.0313918468406821858291 | quadtree_20_23_1_4, quadtree_19_27_2_2, quadtree_21_25_1_4, quadtree_19_25_1_2, quadtree_2_31_3_1 | 0 / 4.3619293137453496e-06 / 0.0088374465703964233 | `58669e69f56e1fa5f0ec5f4f701aa845cb4c3f5cf43cb62fd5e9090e371ac973` |
| B | 87 | quadtree_23_14_1_3 | 14 | 0.0323057873538337434263 | quadtree_17_26_2_2, quadtree_19_14_1_1, quadtree_21_14_2_2, quadtree_18_14_1_2, quadtree_19_15_2_4 | 8.7336429714923725e-06 / 0.059760719537734985 / 0.45101875066757202 | `73f80445277c1c5b1cceb355f40a0c48c6b5bea13da16b48b5583c79bd079354` |
| C | 87 | quadtree_23_14_1_3 | 47 | 0.203714791133794876713 | quadtree_10_32_5_4, quadtree_18_36_2_1, quadtree_9_31_5_1, quadtree_12_36_5_1, quadtree_28_27_1_1 | 8.7336429714923725e-06 / 0.059760719537734985 / 0.45101875066757202 | `780366a446f4c27496b60939aec098d50d7ba6c516ac7f8b387b3b75f9469419` |

Arm A: GMRF observer wind with frozen R2 PMFS parameters. Arm B: ground-truth wind with frozen R2 PMFS parameters. Arm C: ground-truth wind with official humble PMFS forward and hit-map parameters.

Top-5 centroid is secondary. The smoke capture has no 300 s endpoint. Candidate map hashes and repeat checks are in `r1_scores_frozen_manifest.json`.

Truth-source candidate rank is the primary scientific comparison. No arm was selected or retuned after truth evaluation.
