# Execution provenance

Branch: research/wind-contract-identity-audit-v0-20260926.
Base: 583204fc06925dcb8725c4046cca29c48bf2abbf.
Original ZIP: WIND_CONTRACT_IDENTITY_AUDIT_V0_20260926.zip.
SHA256: 4d5a578caee49c7f19a848c6fd3217fa1b98cced287611ffe15128eb69b5bc0f.
All six original members retain their original byte hashes.

Read-only collection/probing and the unchanged supplied analyzer ran on the VM
with Python, NumPy and pandas. ROS and simulation executables were not run.
Evidence includes source snapshots, asset inventories, probes, frozen matching,
historical wind traces and explicitly labelled aggregation diagnostics.

The first collector stopped on an overly strict equality assertion comparing
decimal text in the supplied event CSV with historical CSV. The difference was
approximately 4e-17 m/s. That incomplete collection is preserved on the VM under
evidence_collection_attempt1. The input-validation comparison was corrected to
absolute 1e-12; neither supplied input nor analyzer was changed. This comparison
is a provenance check, not an event/state match threshold. Probe and matching
calculations were then performed once with the supplied contract unchanged.

Git -text attributes preserve original supplied files and raw evidence bytes.
No science parameter, z-selection rule, event matcher or conclusion threshold
was changed. Final decision is HOLD_Z_OR_TIME_SEMANTICS_UNRESOLVED, limited to
unresolved event-block receipt/time assignment. No next experiment is started.
