# R1 House01 seed0 three-arm candidate-forward replay

Scores and maps were frozen before truth was opened (`cd38dcbf240f5f82f80c0e52f96b4af68d26e8b5f3fa15625838a1ab79a98b7e`).
The comparison uses one observation snapshot and its 87 exported Native candidate regions.

| Arm | Candidate count | Truth candidate | Rank | Truth score | Top-5 IDs | Wind min / median / max | Score SHA256 |
|---|---:|---|---:|---:|---|---|---|
| A | 87 | quadtree_23_14_1_3 | 48 | 0.0313918468406821858291 | quadtree_19_25_1_2, quadtree_19_27_2_2, quadtree_24_25_1_1, quadtree_2_32_4_4, quadtree_20_23_1_4 | 0 / 4.3619293137453496e-06 / 0.0088374465703964233 | `47b53f18c2cd2a43c91d4640c80a9637ce321e1b59d77ed4f3eea957900d8a3f` |
| B | 87 | quadtree_23_14_1_3 | 18 | 0.0313918468527773394093 | quadtree_19_19_2_4, quadtree_19_15_2_4, quadtree_18_14_1_2, quadtree_19_14_1_1, quadtree_21_14_2_2 | 8.7336429714923725e-06 / 0.059760719537734985 / 0.45101875066757202 | `1d2b7ed2c70300ef24389a5b3664fc3a68c8aebf9597b13dc969ea33a5589ead` |
| C | 87 | quadtree_23_14_1_3 | 47 | 0.203714791133794876713 | quadtree_10_32_5_4, quadtree_18_36_2_1, quadtree_9_31_5_1, quadtree_12_36_5_1, quadtree_28_27_1_1 | 8.7336429714923725e-06 / 0.059760719537734985 / 0.45101875066757202 | `780366a446f4c27496b60939aec098d50d7ba6c516ac7f8b387b3b75f9469419` |

Arms A/B link the frozen R2 PMFS source and event-keyed candidate RNG; A uses GMRF observer wind and B uses ground-truth wind. Arm C links the official humble PMFS source with ground-truth wind.

Top-5 centroid is secondary. The smoke capture has no 300 s endpoint. Candidate map hashes and repeat checks are in `r1_scores_frozen_manifest.json`.

Truth-source candidate rank is the primary scientific comparison. No arm was selected or retuned after truth evaluation.
