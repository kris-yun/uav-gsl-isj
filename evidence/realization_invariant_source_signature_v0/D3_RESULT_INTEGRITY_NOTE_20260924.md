# D3 result reporting integrity note

The frozen D3 runner and scorer were executed without a scientific-contract change. The original `D3_S1_W2_RESULT_20260924.json` is preserved byte-for-byte.

The JSON `pass_rule` object is a reporting defect: `score_d3_second_source.py` writes all four values as literal `true`, independent of the ranks. It is not the predicate used to set `decision`. The executable `passed` expression above that block evaluates the frozen inequalities from the ranks.

From the unmodified result: A raw/D0/diagonal/D2 ranks are 1/9/6/5; B ranks are 1/1/1/1. Hence the actual frozen predicates are: both D2 ranks <=3: **false**; D2 rank sum 6 <= raw sum 2: **false**; 6 <= D0 sum 10: **true**; 6 < diagonal sum 7: **true**. The frozen decision is therefore `D3_FAIL_STOP_MZ_SOURCE_INFERENCE_MAINLINE`.

No scorer, projection, memory horizon, rank, threshold, JSON result, or target was changed after observing D3. This note prevents the incorrect display flags from being mistaken for evidence of a pass.
