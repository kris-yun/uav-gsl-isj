# Superseded RCEC native-increment evidence

The following older files are retained only for audit history:

- `rcec_v13_offline_15pairs.csv`
- `rcec_v13_offline_15pairs_summary.json`

They correspond to a rejected M2 definition based on a native log increment against a pre-native source state. Static review found that the pre-native state can contain the previous V11/RCEC injection, so this view is feedback-coupled and the archived V11 replay is not dynamically equivalent to a real RCEC recursion.

**Do not use these files as evidence for the active RCEC method.**

The active corrected development audit is:

- `rcec_v13_native_absolute_pairs_v3.csv`
- `rcec_v13_native_absolute_summary_v3.json`

Contract: `RCEC_V13_NATIVE_ABSOLUTE_FIXED_TRAJECTORY_AUDIT_V3`.

These corrected files are still development-visible fixed-trajectory shadow evidence, not closed-loop confirmation.
