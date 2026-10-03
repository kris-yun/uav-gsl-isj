# Lagoon Pingo Track A contract unlock audit

Date: 2026-10-03. Decision: `REAL_LAGOON_HOLD_METADATA_CONTRACT`.

These scripts operate only on the isolated `C:\work\LAGOON_PINGO_REAL_DATA_20261003\unlock_20261003` tree and emit compact repository evidence under `evidence/public_data_first_20261003/lagoon`. The existing `raw` tree is read only. They do not pair ordinal flight axes or run physical/source inference.

Run with the existing Python environment:

1. `python experiments/public_data_first/lagoon/unlock_audit.py` to save official HTTP/code/metadata availability receipts.
2. `python experiments/public_data_first/lagoon/sensor_contract_inputs.py` to download/verify the three official processed sensor products and inspect their HDF5/NetCDF attributes. Dependencies: requests, h5py.
3. `python experiments/public_data_first/lagoon/report_contract.py` to assemble the frozen qualification row/report and manifest.

The report is the dated outcome of this retrieval, not an assertion that the publisher code will remain unavailable. Some GitHub API requests were rate limited and are explicitly separated from confirmed public webpage/raw URL 404 responses. The author profile HTML retrieval receipt is supplemental, saved locally in the same audit directory. Only an authoritative flight mapping, wind correction and synchronization contract may unlock downstream work.

No new CFD/GADEN, images, training or closed-loop simulation is part of this track. The standalone sensor products comprise 201,131,206 bytes and remain outside git.
