# Evidence pseudoreplication execution provenance

Supplied ZIP SHA256:
`0331d1aa82aa25cac500af9f14c2d4c452ae90c5b67895c79930dc1f2b63e941`.
All six supplied package members passed their internal SHA256 manifest.
The supplied scorer and evaluator were copied unchanged.

Branch: `research/pmfs-evidence-pseudoreplication-v0-20260926`.
Base: `583204fc06925dcb8725c4046cca29c48bf2abbf`.
Historical source: `/home/zyc/native_pmfs_recovery_v1/runs/R1_R2_SOURCE_CORRECTED_House01_S0_20260923`.
The historical `R1_arm_C/candidate_scores.csv` was copied byte-for-byte as
`C_candidate_scores.csv`. All three prescribed input hashes and all 87 map
hashes matched both the supplied contract and historical frozen manifest.

Scoring ran with Python 3 on the VM, using only copied source-blind inputs.
No truth path was supplied to the scoring process. No PMFS executable,
forward simulation, GADEN, new plume, training, parameter sweep or closed loop
was run. Historical evidence and the stopped persistent-source branch were
not modified.

Native parity max absolute error: `9.159339953157541e-16`, below `1e-10`.
Two clean output directories produced byte-identical `candidate_scores.csv`,
`event_support_audit.json`, `native_parity.json` and `SCORES_SHA256.txt`.
The source-blind freeze is committed and pushed before invoking the truth
evaluator. The committed inputs include all 87 frozen C-arm maps to permit
independent recomputation.

Final source-blind freeze commit:
`957781a646b748bcaec99c37d1759aa3218fdb48`.
This commit was pushed before invoking the historical truth evaluator.
All 100 frozen evidence files were verified byte-identical between working
files and their Git blobs. The Git `-text` storage attribute was added to
retain the scorer's original CSV line endings, with no scientific code change.

Truth JSON SHA256:
`07ee4081fab67441f4bba9cde64f1828b369b6dca20b9c660dec9a5d542e4311`.
The unchanged evaluator returned `EVIDENCE_PSEUDOREPLICATION_NULL_OR_ADVERSE`.
M/S/Elog/Ebrier truth ranks are 47/46/47/46. The full raw metrics and top-10
lists are retained in truth_evaluation.json. Execution stops after evidence
packaging; no subsequent temporal/state-closure experiment is run.
