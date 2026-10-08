# M0 E0/E1 evidence replay

No simulator is launched by this replay. R0 remains unchanged; all science runs in this evidence are the eight authorized U0 rows.

1. Place the unchanged `m0_clean_support_r0_20261007` R0 folder beside this `m0_e0_e1_20261007` folder.
2. Unpack `M0_E0_E1_RAW_NATIVE_20261007.zip` into `m0_e0_e1_20261007/evidence/`. Verify its SHA256 against `M0_E0_E1_RAW_NATIVE_PACKAGE_VERIFICATION.json`.
3. Run `python -B verify_r0_portable.py` for cross-platform frozen archive/provenance hashes. The unchanged R0 `freeze_design.py --verify` also works. The old R0 static verifier has a Windows-path basename limitation and is not edited.
4. With NumPy and SciPy installed, run `python -B analyze_e1.py`, then `python -B verify_e1_independent.py`. These rebuild the E1 support/observation/resource decision and compare all native raw files, pre-run code seals and posterior results. No scientific threshold is fitted during replay. Primary analyzer was sealed before all eight baseline runs.
5. Inspect `REPORT_zh.md`, `E1_DECISION.json`, `E1_BASELINE_SUMMARY.csv`, `E1_ALL_RECORD_SUPPORT.csv`, `E1_U0_LORO.csv`, `E1_CLOCK_RNG_CERTIFICATE.json`, `INDEPENDENT_E1_VERIFICATION.json` and the raw per-run `RUN_MANIFEST.json`/`RAW_OUTPUT_SHA256.csv` files.

`prepare_assets.py`, `qualify_e0_vm.py`, `run_e1_vm.py` and build/native helpers are archived provenance. Do not invoke them during review. The runner rejects an existing campaign and cannot launch intervention rows. Its project/YAML entry uses the unchanged frozen generator and fixes the effective ambient-parameter binding without changing science settings or native code.

Windows generation used the frozen NumPy bump implementation to meet exact wind byte fingerprints. Native assets/readback in the raw ZIP allow verification without recomputing field exponentials on another OS. The independent E1 checker uses relative archive paths; historical Windows provenance strings are handled by the external portable verifier.

Original native 3sigma cutoff and line-of-sight logic are preserved for concentration parity. Physical boundary qualification is separate: Gaussian support/box-tail and release/deletion accounting. Reported CDF subtraction zeros are numerical; stable erfc bounds are archived. RNG/deletion evidence is a pinned-code invariant with every saved-frame count/sigma and between-save/terminal displacement certificate, not an instrumented per-tick trace. Wrong-wind cross-arm CRN is pending E2, not passed here.

Verdict: `M0_E1_BASELINE_QUALIFIED`. Stop. No E2/32-arm launch authorization and no M0_PASS/PRIMARY_GO claim.
