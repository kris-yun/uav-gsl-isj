# E0 inventory byte normalization

E1 read the checked-out E0 inventory at
`evidence/environment_level_benchmark_v0/e0/E0_ENVIRONMENT_ASSET_INVENTORY.tsv`.
Its SHA256 is `5e7fd902a047fab8a1dbd303f1f41431c4acd5df6f8cccb7c34bb13392f67672`.

The original E0 VM output has SHA256
`5139d6718c9fca05fb9964508a0fa6c33956ede5fae0277351a3f02f27d24319`.
`diff --strip-trailing-cr` reports the files identical: Git normalized CRLF to LF
at checkout. The 4,430 inventory rows and all fields are unchanged.
