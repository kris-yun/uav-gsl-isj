# RPO-G0 numerical audit note

The frozen CENTRAL decision was written and committed before this diagnostic and before the OFFSTRIP stress calculation. No features, ridge settings, paths, labels, or thresholds were changed.

- One P_G1A probe (zero-based index 27) is disconnected from every source on the frozen z=0.20 m, no-corner-cut 8-neighbor occupancy graph. The pre-run disconnected flag and finite sentinel were applied to all 168 CENTRAL and 6 OFFSTRIP source-to-probe paths involving that probe.
- CENTRAL pair 78 (`pmfs_13_18` versus `pmfs_14_18`) has a `GEOM` feature `geodesic_median_abs` of 0.029289321881344588. In the other three training bands for that outer fold, this feature ranges from -4.996e-16 to 0 with standard deviation 6.633e-17. Training-only `StandardScaler` therefore makes the held-out value approximately 4.416e14 standardized units. Ridge selects alpha 1000, yet GEOM/PHYS extrapolate to roughly 3.60e13/3.26e13 for CNR.
- These predictions make squared-error means extremely large. They are an observed numerical extrapolation risk under the preregistered standardization; they are not evidence of a physically enormous identifiability change.
- The primary G0-1 Spearman results are negative for both targets, and G0-4 sign balanced accuracy also fails. The frozen STOP decision does not depend on interpreting the huge MSE as a physical effect. An independent dual-form ridge implementation reproduced the predictions and decision.

No post-result numerical repair or rescue run was performed.
