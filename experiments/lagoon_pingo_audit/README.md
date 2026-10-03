# Lagoon Pingo isolated download and Stage A audit

Data root: `C:\work\LAGOON_PINGO_REAL_DATA_20261003`. Never reuse the WiscoDISCO/S2X/GADEN raw directories. The only two original primary data files are in `raw`; all original MD5 and local SHA256 values are in `metadata`.

1. `download.py`: two frozen core files only; HTTP retry/resume, official checksum verification.
2. `audit.py`: schema, sampling, time differences, missingness, per-flight inventory, projected tracks, independent fieldnotes coordinate inventory. Does not assume a `flight` to `flight_frec` mapping, clock correction, wind frame, timezone, AGL, or shoreline.
3. `package.py`: verify core hashes, ZIP original files plus audit outputs, copy only lightweight evidence to the branch. Raw data and the ZIP remain in the isolated directory.

Current decision: REAL_LAGOON_HOLD at the user protocol's Stage A synchronization/wind contract gate. Wind quality has not been proved unusable; it has not been independently verified. No downstream physics/history predictor is fit. Surface labels, signed shore distance and crossing counts remain explicitly unknown.

Python h5netcdf and pyproj were installed only to this data root's `tools/python_deps`. Existing global Python, House/VGR, ROS and GADEN environments were not upgraded. Other imports use the existing local analysis environment.

The official author processing repository returned GitHub404/git repository-not-found. An old geometry README states May2020 surface icing; it cannot establish summer2024 water coverage. These are recorded evidence limitations, not grounds to invent synchronization or shoreline labels.

The ZIP contains all data needed to reproduce this read-only audit; install its listed Python dependencies or use the recorded local analysis environment. It does not contain a working simulator or Python interpreter.
