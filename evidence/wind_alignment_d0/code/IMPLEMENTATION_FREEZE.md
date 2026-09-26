# Implementation choices frozen before truth

The supplied ZIP contains specifications and recovered sequences, but no execution code. The scripts in this directory implement the supplied formulas and decision rules.

P0 uses the exact historical C-arm kernel and continuous default minstd_rand0 stream, including normal-distribution cache. A Linux process fork at each candidate boundary copies that complete RNG state to each of the eleven wind siblings. Only the parent advances the original historical stream. The forward score kernel is unchanged. Wind siblings change only the queried spatial wind vectors. P0 must be byte identical, with zero score error.

The sensor-height bank contains 87 candidates times 11 states. P1 reuses state0. An independent complete replay verifies all maps and score files byte for byte. The preflight and both complete runs generate 2175 maps in total; 1044 distinct scientific maps include P0 and the 957-map bank.

Permutations use Python random.Random(2026092601), sites in original event insertion order, and sequential random.shuffle calls for each site's five indices. Exactly 200 assignments are stored before truth. No sequence moves between sites.

Scores use the supplied twenty events, raw float32 maps, arithmetic mean over ten state IDs (or fifty for site pooling), eps=1e-6 only in Elog, and negative raw-probability squared error in Brier. Higher scores are better. Candidate rank ties use ascending candidate_id, matching the historical proper-score evaluator.

Permutation percentiles use strict better-than comparisons; ties are reported separately. The dynamic gate requires the matched rank to be strictly better than at least 95% of permutations in one metric, with the other rank no worse than its permutation median, and both metrics strictly better than P1 and C1. Decision priority is dynamic, height, mixture, null. Height requires both P1 ranks improve over historical and no dynamic effect. Mixture requires both C1 and P2 improve versus P1 for both metrics and no dynamic effect. This is the supplied rule; no threshold is changed.

The truth evaluator, all candidate and permutation scores, and their hashes are committed before truth is opened. Previous scientific STOP and HOLD decisions are preserved.
