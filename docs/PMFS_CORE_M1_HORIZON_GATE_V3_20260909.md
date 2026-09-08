# CORE-M1 full-horizon joint-success gate V3

Status: **CORRECTED AFTER SEED6; FUTURE CONFIRMATION REQUIRED**.

V2 correctly repaired full-horizon posterior holding, but its multi-world code
did not implement the written cross-House rule.  It required a majority of
positive final-error differences and a majority of positive AUC differences
separately.  Different Houses could satisfy the two majorities, so a result
with only one House improving both metrics could incorrectly pass.

V3 requires a majority of paired worlds to improve **both** final error and
0--240 s distance AUC, while retaining positive aggregate improvements for
both metrics.  For House123 this means at least two Houses must each improve
both metrics.

The discrepancy was found after House123 seed6 was visible.  The earlier V2
JSON remains immutable evidence of the implementation error and must not be
quoted as a scientific PASS.  Seed6 is revalidated under V3 and labelled
diagnostic; any future confirmatory run uses V3 prospectively.
