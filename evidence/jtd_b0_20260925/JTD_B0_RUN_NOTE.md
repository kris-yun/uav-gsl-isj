# JTD-B0 frozen R=4 bridge result

Decision: `JTD_B0_FAIL_R4_ESTIMATOR_NOT_RELIABLE`.

The B0 scorer was frozen and committed as `98654c29c81487e627f76eaf57de39a86814d2b4` before any B0 result was opened. It uses the upstream G0 canonical R0 bank from `170d0ccddc559c97744af5409ec1e3642bcfa743`, 18 sources x 16 independent realizations. No new plume and no E2 environment data were used.

All four quartets and 16 leave-one-realization-out folds completed. Every fold used 3 training realizations/source, one held-out target/source, 5 contiguous two-time blocks, two training-only PCA components/block, shared pooled within-source OAS covariance, and 200 deterministic three-cycle SHUFFLED nulls. The full scorer and exact null SHA key rule are included in the review package.

The six frozen gates were applied without changing thresholds. G1, G2 and G5 failed; G3, G4 and G6 passed. Q2 had a negative mean effect. A B0 FAIL means this R=4 estimator did not reliably reproduce the G0 temporal-dependence signal. It is not a verdict on the JTD mechanism across environments. JTD-E1 was not run.

The G0 A0 audit was verified by SHA. The same G0 audit script (SHA256 `ec40adbfd90b28e31c0f223dce3671caf2dbe98c89fa4e57b873b3192bba023d`) was run again on the VM against all 288 original concentration cubes. All 288 raw/pooled hashes and exact 10x30 re-extractions passed. The fresh `.npz` container has a different file SHA due to serialization bytes, while its X tensor, source IDs, coordinates, realization IDs, time/probe axes and iteration indices are exactly equal to G0's canonical cache. The independent verifier checks this and recomputes all six gates from `JTD_B0_TARGETS.csv`.

Input origin: `/home/zyc/r0_stochastic_benchmark_20260924` on the VM. Audit code origin: G0 final commit above. Local scoring used Python 3, NumPy, SciPy and scikit-learn versions recorded in `JTD_B0_NULL_PROVENANCE.json`, with OMP/OpenBLAS/MKL threads fixed at 1.

No estimator, block, PCA dimension, source, seed, null count or gate was changed after seeing the B0 score. The verifier's source-order correction affects independent bootstrap replay only; the frozen scorer and its outputs were unchanged.
