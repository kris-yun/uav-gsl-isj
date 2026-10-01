# O0 execution repair, before any scientific scoring

The first projected S1/A simulation completed successfully with 566 files. The
frozen extractor then exited 3 with ENV_READ_FAILED because the runner did not
place OccupancyGrid3D.csv in the environment directory supplied to the extractor.
The historical export_c05_spatial_slices_remote.sh explicitly supplies this link.

The repair adds only that link to the exact original occupancy file. The first
successful simulation is retained and extracted without another GADEN execution.
No source, seed, physics, wind projection, snapshot record ID, extraction grid,
scorer or decision threshold changes. The failed extraction log is retained.

Infrastructure adaptations: use the existing shared drive as WORK_ROOT, load the
same historical ROS/library environment, invoke system python3 via a python shim,
and ignore hgfs executable-bit presentation for Git checks. A storage-only Python
guard renames new raw directories to raw_retained instead of deleting them and
records every retained file's SHA256. The ROS environment and original assets are
not changed. No historical raw files are deleted.
