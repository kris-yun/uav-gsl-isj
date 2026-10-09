# Red:Vapor local discovery and minimal qualification — NO download-first
Date: 2026-10-08

User recalls a previous Red:Vapor download. Treat that as unconfirmed, not absent. Read-only local inventory; never rerun M0, run gas simulations, delete, move, overwrite, unzip huge archives, or download a full release.

## Versioned identifiers
Paper: Hinsen et al., 2026 Scientific Data, DOI 10.1038/s41597-026-06927-8.
Data record: https://zenodo.org/records/18299926 ; parent DOI https://doi.org/10.5281/zenodo.16414472 ; code https://github.com/DLR-KN/red-vapor.
Expected filenames: overview_table.csv, csv_header_specification.pdf, data_records_csv.zip, experiments.pkl, voxel_maps.pkl, supplementary_material.zip. Extracted path examples: DNW_Data, Fly-Through_Experiments, Purging_Runs, Sampling_Experiments.

## 1. bounded discovery before any network
Search likely roots: D:\ZYC\A-gas\_staging, D:\ZYC\A-gas\_deliveries, D:\ZYC\UAV, D:\ZYC, C:\work, C:\Users\50176\Downloads, /home/zyc, /mnt/d/ZYC (only if mounted). Look up earlier manifests first.
Search filename and directory layout using red-vapor / RedVapor / Vapor Advection Plumes / DNW_Data / Fly-Through_Experiments / overview_table.csv / data_records_csv.zip / voxel_maps.pkl / experiments.pkl. Avoid full-drive recursive contents grep; bound filename search and record skipped/unreadable roots.
For each plausible candidate collect exact private local path, size, modification time, archive member listing/count without extraction, original manifest/provenance and whether actual content is present versus symlink/placeholder.
Compare official Zenodo version/files/sizes/MD5, calculate cryptographic checksum only on credible candidates, and report deferred large-file hash checks honestly. Preserve old raw bytes and established historical manifests.
Never run pickle.load or joblib.load on untrusted .pkl: deserialization can execute code. Inspect official CSV and ZIP metadata first.

## 2. scientific usefulness audit (small file / metadata only)
Identify actual independent source locations, facility geometry, plume concentration measurements, raster scans vs moving fly-through, clocks, sensor IDs, wind metadata/units, PID/MOX response timing, and possibility of matched mobile sensor trajectories.
Reported Red:Vapor facility has ONE fixed physical source outlet with turntable configurations. Verify from actual metadata and do NOT treat changed layout as multiple independent true source labels.
Differentiate time-assembled raster voxel maps from simultaneous 3D truth and identify whether actual 3D wind time-series is available. Check source-location posterior ground truth before attempting gas source localization scoring.
If paired PID/MOX traces with timestamps and common routes are valid, propose sensor dynamics comparison only for later approval. No Top1/MAP/multi-source generalization claims with a single true source.

## 3. bounded completion output
Return REDVAPOR_LOCAL_COMPLETE, REDVAPOR_LOCAL_PARTIAL, REDVAPOR_NOT_FOUND or REDVAPOR_INVALID_CANDIDATE.
One-page table: files exact versions, private paths, verified hashes, missing bytes, usable comparisons, key scientific limitations, and only-the-missing-file download proposal (smallest bytes) if needed.
Save sanitized report in a new unprotected folder and push only audit text/manifest to a new GitHub branch, no dataset bytes, secrets or personal absolute paths. Stop immediately after audit. No downloads without new user approval.

Use this audit to support 2025–26 GSL failure-first screening: RedVapor may support measured sensor-response / plume physics validation, not yet first-paper multi-source positioning.