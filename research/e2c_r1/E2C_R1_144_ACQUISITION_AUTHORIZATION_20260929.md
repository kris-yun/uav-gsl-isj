# E2C-R1 144-run acquisition authorization
Date: 2026-09-29

The revised source-unseen panel frozen at
`e6b9d9cbda969c7b8ed8eb9f85dad377c1b61e36` is accepted for acquisition.

Scientific interpretation boundary:
- H01/H02: six historical discovery sources + two source-unseen within-House confirmation sources.
- H03: eight source-unseen confirmation sources.
- House03 itself is historically studied and MUST NOT be described as an unseen environment.
- The valid later claim, if confirmed, is source-unseen cross-House confirmation under a common acquisition contract.

Execution authorization:
- generate exactly the 144 runs listed in `evidence/e2c_r1/SEED_MANIFEST_144.tsv`;
- use the frozen House-specific canonical winds, source positions, seeds, E1 probe geometry, 2x2 footprint, ten certified writer-record IDs, and unchanged E2 extractor;
- do not replace a failed run with a new seed without first recording the failure and pausing for an explicit contract amendment;
- do not inspect scientific concentration values from sealed confirmation data during acquisition/packaging;
- hash raw cubes, metadata, and extracted arrays.

Sealing after acquisition:
- OPEN: H01/H02 discovery sources only.
- SEALED: H01/H02 new confirmation sources.
- SEALED: all House03 scientific arrays.

STOP after acquisition, extraction, hashing, and integrity packaging.
Do not run Ordinal, AOD, CENTERED, dependence, TCMA/AEC, PMFS-Clean, VGR, or any new mechanism score.
