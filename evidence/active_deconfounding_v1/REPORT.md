# Active source–transport deconfounding V1 — frozen development screen

**NO_GO_WITHIN_FROZEN_OFFLINE_SCREEN**

V5 remains HOLD; FUSED closed loop and online planner edits were not performed.

| Case | Greedy source-MI separation | Two-step separation | Passing held-out worlds | Representative offset m |
|---|---:|---:|---:|---:|
| House01_seed0 | 0 | 0 | 0/8 | 0.1354 |
| House01_seed1 | 0 | 0 | 0/8 | 0.1354 |
| House02_seed0 | 0 | 0 | 0/8 | 0.5502 |
| House02_seed1 | 0 | 0 | 0/8 | 0.5502 |
| House03_seed0 | 0 | 0 | 0/8 | 1.0332 |
| House03_seed1 | 0 | 0 | 0/8 | 1.0332 |

Necessary case gate: 0/6; House coverage: {'House01': False, 'House02': False, 'House03': False}. No ROS promotion.

## Interpretation

Separation is squared Hellinger distance between two-observation source response sets, with one nuisance world shared across both observations. A 0 means a false source can match the true representative at the selected action pair under at least one allowed alternative world.

The nuisance bank was fixed and pushed before new responses. All four strategies share candidate positions, feasible path budget and two observations. Greedy strategies are evaluated with two actions; gains are not created by giving the new method an extra sample.

These are already-seen six development contexts. Grid-off nuisance and a separate simulator replica test interpolation/randomness robustness inside the same native model; they do not establish external model validity or unseen-seed localization.

The source truth is used only after action files are written and hashed. The metric uses the native leaf representative covering truth, not a new forward run at the exact true continuous location. Offsets are disclosed above.

The native baseline reproduces the variance-confidence-visibility objective with regenerated point responses and original first-level weights. It does not reproduce region-source sampling, navigation state or exploration RNG; grid paths certify only point-robot connectivity. This limits positive claims.

Local confidence-weighted nuisance projection is a sensitivity diagnostic, not a calibrated Fisher information calculation. Zero source contrast is separately reported, never scored as successful deconfounding.

## Failure details

- House01_seed0: FEWER_THAN_6_OF_8_HELDOUT_WORLDS_CLEARLY_BEAT_SOURCE_MI; TRUE_SOURCE_HAS_ZERO_SEPARATION_FROM_A_FALSE_SOURCE; SELECTED_PAIR_PREDICTS_NO_HITS_FOR_TRUE_REPRESENTATIVE_IN_ALL_HELDOUT_WORLDS. Zero nominal source contrasts 27/123; fixed native-false rival `quadtree_20_34_1_1`. Indistinguishable selected-pair rivals are 2.751–2.751 m from truth; true-response zeros over all candidate action/world combinations: 88/96.
- House01_seed1: FEWER_THAN_6_OF_8_HELDOUT_WORLDS_CLEARLY_BEAT_SOURCE_MI; TRUE_SOURCE_HAS_ZERO_SEPARATION_FROM_A_FALSE_SOURCE; SELECTED_PAIR_PREDICTS_NO_HITS_FOR_TRUE_REPRESENTATIVE_IN_ALL_HELDOUT_WORLDS. Zero nominal source contrasts 28/121; fixed native-false rival `quadtree_16_27_1_1`. Indistinguishable selected-pair rivals are 6.151–6.151 m from truth; true-response zeros over all candidate action/world combinations: 84/96.
- House02_seed0: FEWER_THAN_6_OF_8_HELDOUT_WORLDS_CLEARLY_BEAT_SOURCE_MI; TRUE_SOURCE_HAS_ZERO_SEPARATION_FROM_A_FALSE_SOURCE; SELECTED_PAIR_PREDICTS_NO_HITS_FOR_TRUE_REPRESENTATIVE_IN_ALL_HELDOUT_WORLDS; SAME_ACTION_PAIR_AS_GREEDY_SOURCE_MI. Zero nominal source contrasts 19/123; fixed native-false rival `quadtree_12_9_1_1`. Indistinguishable selected-pair rivals are 2.228–2.228 m from truth; true-response zeros over all candidate action/world combinations: 92/96.
- House02_seed1: FEWER_THAN_6_OF_8_HELDOUT_WORLDS_CLEARLY_BEAT_SOURCE_MI; TRUE_SOURCE_HAS_ZERO_SEPARATION_FROM_A_FALSE_SOURCE; SELECTED_PAIR_PREDICTS_NO_HITS_FOR_TRUE_REPRESENTATIVE_IN_ALL_HELDOUT_WORLDS. Zero nominal source contrasts 22/119; fixed native-false rival `quadtree_12_10_1_1`. Indistinguishable selected-pair rivals are 2.228–2.228 m from truth; true-response zeros over all candidate action/world combinations: 92/96.
- House03_seed0: FEWER_THAN_6_OF_8_HELDOUT_WORLDS_CLEARLY_BEAT_SOURCE_MI; TRUE_SOURCE_HAS_ZERO_SEPARATION_FROM_A_FALSE_SOURCE; SELECTED_PAIR_PREDICTS_NO_HITS_FOR_TRUE_REPRESENTATIVE_IN_ALL_HELDOUT_WORLDS. Zero nominal source contrasts 37/160; fixed native-false rival `quadtree_26_7_1_1`. Indistinguishable selected-pair rivals are 3.177–3.177 m from truth; true-response zeros over all candidate action/world combinations: 87/96.
- House03_seed1: FEWER_THAN_6_OF_8_HELDOUT_WORLDS_CLEARLY_BEAT_SOURCE_MI; TRUE_SOURCE_HAS_ZERO_SEPARATION_FROM_A_FALSE_SOURCE; SELECTED_PAIR_PREDICTS_NO_HITS_FOR_TRUE_REPRESENTATIVE_IN_ALL_HELDOUT_WORLDS. Zero nominal source contrasts 43/160; fixed native-false rival `quadtree_27_2_1_1`. Indistinguishable selected-pair rivals are 3.177–3.177 m from truth; true-response zeros over all candidate action/world combinations: 96/96.

The selected two-step pair predicts zero hits for the true representative in all 8 held-out worlds in every case. Wrong sources several metres away can also predict zero hits. Thus the chosen pairs do not break this no-hit ambiguity. Other candidate actions do predict some true-source hits in five cases; this is not a claim that every possible action is uninformative.

Local source-vs-fixed-native-false contrast retains about 92–100% of its weighted energy after projection against the three nuisance columns. These diagnostics do not establish broad local transport-span confounding as the cause of the historical failures. They are consistent with a failure of the selected finite-budget actions and/or of the response representation, without uniquely identifying the cause.

## Compute and reproducibility

Forward calls: 34580; summed measured forward compute: 544.38 s; action scoring: 49.91 s.

The complete raw bank, paths, per-world comparisons, source confounding rows, executable/library hashes and input SHA256 records are retained in the evidence archive. These costs are offline preparation costs; no real-time planner feasibility is claimed.

Provenance limit: the first House01/seed0 wrapper executable hash was not retained before the obstacle-only validation correction. Its wrapper source commit and response hash are retained. The frozen native library hashes are recorded; the later five cases have the standalone executable hash as well. This limitation is not a reason to promote or rerun the study.

Stop here. Do not alter the nuisance range, rescue the same screen with a new gate, or open ROS experiments.
