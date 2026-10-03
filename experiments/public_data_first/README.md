# Public-data-first real observation audit

Frozen roadmap: `experiments/lakeshore_observability/PUBLIC_DATA_FIRST_ROADMAP_20261003.md`, commit `17b31989e726b64ac95030a5b3f7dd635578af65`.

No new CFD, GADEN, neural training, closed-loop or multi-UAV work. Different datasets retain different valid endpoints. Read `evidence/public_data_first_20261003/PUBLIC_DATASET_QUALIFICATION_REPORT_zh.md` first.

Each dataset lives in a separate `C:\work` directory. Script subdirectories cover Lagoon publisher-contract checks, Mackenzie download/author-kernel reproduction and explicitly conditional fixed-route inverse diagnostics, and Svalbard publisher preprocessing/conditional-wind Bayesian STE. Ground wind is not present in the Mackenzie archive, Lagoon's corrected wind mapping is not verified, and Svalbard's original field PF has a missing import and fixes the known source. These limitations are retained rather than silently substituted.

Run from the repository using Python 3.12 with numpy/pandas/scipy/matplotlib, plus isolated pyproj dependencies. Original inputs and pinned authors' code are included in the evidence ZIP; installed dependencies are not. Scripts record fixed Windows paths to ensure data isolation. See each track report for the raw hashes, exact configuration, source-truth separation, and portability changes. `integrate.py` creates the qualification matrix, integrated report, all-input manifest and verified evidence ZIP.

## Replay Mackenzie after original package download

```
python experiments/public_data_first/mackenzie/download.py
python experiments/public_data_first/mackenzie/audit.py
python experiments/public_data_first/mackenzie/audit.py --dispersion-sensitivity
python experiments/public_data_first/mackenzie/report.py
```

The sensitivity extends dispersion support to diagnose non-identifiability; it does not replace the primary result or select favorable arms. `report.py` sets the final Mackenzie HOLD rather than the initial availability-only status in `audit.py`.

## Replay Svalbard

Use official active commit `2aec1667f10648c4be2ccc15ab2b385ec80305b7` under `C:\work\SVALBARD_BOREHOLE_REAL_DATA_20261003\raw\active`, then execute the preprocessing, audit/invert, forward parity and finalize scripts. Its frozen primary/sensitivity configs are included in the evidence subdirectory. Bayesian posterior is conditional on the stated model, not independently calibrated measurement uncertainty.

No common mechanism met the requested >=2 independent real dataset gate. Wind representation / source-receptor propagation remains a candidate research question, not an established first-paper innovation.
