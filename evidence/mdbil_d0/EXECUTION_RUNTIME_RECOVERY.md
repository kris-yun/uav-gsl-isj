# Execution runtime recovery before scientific fold outputs

Two Windows attempts exited with OpenMP Error #15 before any FOLD_METRICS/SEED_METRICS or scientific decision output. Preserve their config, input hash and process logs under WINDOWS_OPENMP_ATTEMPTS. Do not interpret them as scientific STOP results.

No KMP_DUPLICATE_LIB_OK override was used. Continue the identical repaired frozen script on the existing Linux VM CPU runtime: Python 3.10.12, PyTorch 2.12.1+cpu, NumPy 1.26.4. These satisfy the supplied requirements. No package was installed or upgraded. Only the 64 SHA-bound tensor files and their metadata, manifest and frozen scripts were transferred; no protected dataset was opened.

The VM synthetic self-test and all 64 tensor/metadata hashes pass. The actual runner hash is recorded in VM_RUNTIME_PREFLIGHT.json and matches the local repaired committed file. Both scientific passes use the same VM runtime, epoch count, three seeds, single CPU thread and deterministic algorithms. They run as independent processes with independent output directories; numerical repeat is verified before any scientific promotion.

New GADEN, source interventions, PMFS, closed loop, confirmation and House03 counts remain zero. The prior scientific verdicts remain unchanged.
