# LSC Cross-Wind D0 pre-data execution patch

This patch was made before any W1 or W2 realization was generated or scored.

- The frozen analyzer accepted a D1R W0 tensor with 16 replicates, then passed it to a function requiring eight. It now selects D1R replicates 1–8 for the protocol's W0 first4/second4 anchor. The W0 stability, A, and B Spearman values reproduce as 0.696969697, -0.368705921, and -0.557272224.
- The VM's SciPy returns Spearman correlation in tuple position 0 and has no `.statistic` attribute. The analyzer now reads tuple position 0. The statistic and all thresholds are unchanged.
- The handoff did not include a simulation or package runner. Added scripts that use the frozen D1R GADEN and extractor settings, the eight preselected cells, the two canonical wind paths, and seeds 2026110001–2026110128. They retain raw concentration cubes and provenance, and package the compact tensors and manifests.

No W1/W2 plume outcome, source rank, or mechanism decision informed these changes.
