# M0 complete40 replay — no simulator

Final verdict: M0_STOP. Exactly 8 U0 + 4 E2 + 28 E3 = 40 legal native runs. No retries or extras.

The complete local ZIP contains the unchanged R0 original ZIP, all six `M0_NATIVE_*.zip` partitions, the final scientific code/tables/seals and Linux replay logs. GitHub stores the complete outer ZIP in ordered byte parts; `FULL_ARCHIVE_PARTS.json` and `reassemble_full_archive.py` verify and reassemble it. Parts are lossless bytes, not an alternate scientific dataset.

1. Unpack the outer complete ZIP. Unpack `R0_FROZEN_ORIGINAL.zip` alongside `m0_e3_final_20261007` to create `m0_clean_support_r0_20261007`.
2. Inside the E3 folder, verify `FINAL_EVIDENCE_FILES_SHA256.csv` against `FINAL_EVIDENCE_SEAL.json`. Each native ZIP SHA256 is recorded in `M0_NATIVE_PACKAGES_MANIFEST_20261007.json`.
3. Unpack all six native partitions into one fresh `m0_e3_final_20261007/evidence/`. Their members are disjoint and cover the whole bank, metadata, all inputs/readbacks/source hashes, native states, raw iterations, original argv/env/time/RSS/logs, and ROI/global columns. Verify `evidence/NATIVE_FILES_SHA256.csv` (14,779 files) and the original-to-archive mapping.
4. On an extracted copy with compatible NumPy >=1.22 and SciPy, run:

```
python -B evaluate_final.py
python -B verify_final_independent.py
python -B verify_secondary_global.py
```

The primary evaluator calls the unchanged frozen R0 gate; the independent checker uses scalar likelihoods/variance, stable erfc bounds, independent normalization and decision arithmetic. Both preserve U0 observations and exclude the held-out seed from both candidate sources and all five winds. BMA is a prior-art comparator outside the primary decision inputs.

The pre-run E3 seal includes the main runner, qualification, scoring and independent checker. Supplemental whole-domain native columns are the R0-prespecified secondary diagnostic; their helper changes only grid dimensions/origin/indexing from the E1 helper. These outputs do not enter any primary metric or decision. All 2,040 ROI crops are byte-identical to the original primary maps; 102,000 additional direct parity queries pass.

Fresh Linux extraction replay also passed without calling any native executable. Logs retain the historical NumPy/SciPy version-range warning; dependencies and native runtime were not changed. R0 archive integrity remains verifiable with its unchanged `freeze_design.py --verify`; historical Windows provenance strings are retained, not used as live Linux IO paths.

Do not run `prepare_e3_vm.py`, `run_e3_vm.py`, `extract_secondary_global_vm.py` or `pack_all40_vm.py` during review. They are archived provenance. No new source, seed, gas, route, threshold, family, neural training, fit or simulation is authorized by replay.

All 40 runs qualified, but neither pair has any >=0.10 material Brier difference seed. The common-direction source/family/same-seed intersection is 0/4 everywhere, so M0_STOP is the original gate's result. This is a null for the frozen two-candidate mechanism box, not a universal claim about lakeshores. Stop this candidate route; FSR data construction is independent.
