# E2 evidence replay (no simulator)

Unpack the unchanged `R0_FROZEN_ORIGINAL.zip` beside `m0_e2_sentinel_20261007`, then unpack `M0_E2_RAW_NATIVE_20261007.zip` inside the latter's `evidence/` folder. The E2 raw ZIP includes the completed U0 S0/r01 reference and all four sentinel arms; it does not require rerunning or unpacking the entire original E1 campaign.

Use Python with NumPy >=1.22 and SciPy. Verify `E2_EVIDENCE_FILES_SHA256.csv` and `E2_EVIDENCE_SEAL.json` before replay, and run calculations on a copy:

Windows checks and fresh Linux ZIP-extraction replay both passed. Linux replay inputs, source and receipts/logs are archived; no simulation was called. Use a compatible NumPy/SciPy combination for your review environment. The historical Linux environment version-range warning is retained in the logs.

```
python -B verify_evidence_package.py
python -B analyze_e2_clock_serialization_erratum.py
python -B verify_e2_independent.py
```

The original pre-run `analyze_e2.py` and `verify_e2_independent.py` remain unchanged. The first analyzer has a documented clock-serialization implementation mistake that produces an archived false HOLD; the external corrected analyzer changes only one expression, with no added tolerance or scientific gate changes. Read `E2_AUDIT_CLOCK_SERIALIZATION_ERRATUM.json` and `initial_audit/`. The pre-run independent verifier was not edited and verifies exact cross-arm native records directly.

The 39-file R0 seal is checked by both numerical checkers; original `freeze_design.py --verify` remains the archive integrity check. Historical Windows provenance strings are retained. Native arrays/readback, not recomputed bump exponentials, are authoritative byte inputs.

Do not invoke `initialize_local.py`, `prepare_e2_vm.py`, `run_e2_vm.py` or `pack_e2_vm.py` during review. They are provenance only. The runner is restricted to four authorized IDs and refuses repeat campaigns; all 28 other wrong-wind rows remain unauthorized.

Original full E1 evidence is preserved at commit `653dae35a72b1e29c52c37745806571bff016ef6`, path `research/M0_E0_E1_BASELINE_QUALIFIED_FULL_EVIDENCE_20261007.zip`, SHA256 `09c07dbf7acbb7587267a31681d803aa1287b878a4dd98086357dd7c357636d1`. This E2 archive includes its unchanged selected reference, parent seals and review, without duplicating the entire E1 ZIP.

Verdict: `M0_E2_CRN_SENTINEL_QUALIFIED`; four new wrong-wind runs, zero new U0, zero remaining-28 runs. M0 causal/posterior verdict remains NOT_TESTED. Stop and wait for separate review and authorization.
