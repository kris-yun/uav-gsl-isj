# Gate 1A pre-result extractor repair

After the PMFS center-cell validation fix, the unchanged runner generated the 630-source bank and simulated its first candidate (`pmfs_1_1`, seed `2026092401`). The verified GADEN binary completed and wrote 566 snapshots, but the frozen spatial extractor stopped with `ENV_READ_FAILED`: it could not find `realization/OccupancyGrid3D.csv`.

The runner had linked the exact frozen House02 occupancy file into the realization directory **before** launching GADEN. The binary clears that output directory when it writes a realization, removing the link. The repair restores the **same** symlink after GADEN completes and before invoking the extractor. The extractor, binary, occupancy contents, W2 wind, sources, seeds, probes, score, and gates are unchanged.

No compact prediction vector or A/B truth rank was produced before this repair. The exact frozen batch command must be rerun; its resume logic will regenerate the first incomplete candidate under the same contract.
