# PF-DEI-SR V2 frozen support artifacts

This directory contains the truth-blind V2 planar support, the strict exact-column height audit, fixed source-strength audit, and the single joint nuisance schedule. The planar support and geometry prior were checked against all 50 context NPZ files per House: H01 210 rows, H02 201 rows, H03 206 rows; all 150 priors matched the persistent carrier weights to numerical equality.

The V2 target is the carrier planar representative `(x,y)`. Under the strict V2 rule, exact native occupancy-column mapping yields no legal height for 49 H01, 41 H02, and 51 H03 carriers. The footprint-based height list in `source_height_support_manifest.csv` is retained only as a diagnostic comparison and is explicitly not a valid V2 support manifest because it changes horizontal support. No physical bank was generated from it.
