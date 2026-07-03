# Step 3 ！ Improve SDM (current only 5% vs DQA-AS)

## Context
- MEMP: 40% improvement ！ good
- BPFM: 54% improvement ！ good  
- SDM: 5% improvement ！ needs work

## Task (single focused batch)

1. Read `workspace/uav_diagsense/src/sdm/sdm_estimator.py` and `sdm_planner.py`

2. Tune parameters to try stronger deconvolution:
   - Increase `sparsity_weight` (try 0.1, 0.2)
   - Decrease `blur_sigma_cross` (try 0.5)
   - Increase `blur_sigma_along` (try 5.0)
   - Increase `n_iter` (try 40)

3. If tuning doesnt help, consider a simpler fix:
   - Apply deconvolution EVERY step (not every 5 steps)
   - Or apply deconvolution only when entropy is low (posterior is peaked)

4. Rerun fair comparison:
   - Save to `D:\ZYC\A-gas\automation\results\iter8_sdm_tuned.csv`
   - Save summary to `D:\ZYC\A-gas\automation\results\iter8_sdm_tuned.md`

5. If SDM still < 10% improvement after tuning, document why and stop.

Acceptance:
- New CSV with tuned SDM results
- Summary with parameter changes documented
- Honest verdict on whether SDM is viable
