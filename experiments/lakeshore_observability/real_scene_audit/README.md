# WiscoDISCO real-scene feature audit

This is an exploratory observation audit under the frozen STOP protocol at commit
3cb1e989e901f6391fa4163571b8beb17b96f3ad. It does not change R1/R1A/R1B.
No gas, CFD or active-sensing experiments are run.

Run `python experiments/lakeshore_observability/real_scene_audit/audit.py`.
Dependencies: numpy, pandas, scipy, xarray, h5py. Reporting also uses matplotlib
and tabulate. RAAVEN is read through xarray/scipy; lidar through h5py, so no
new netCDF4 installation is necessary.

Default raw root: `C:/work/LAKESHORE_GSL_DATA_20261002/data_external`.
The evidence ZIP contains the exact 42 raw files beneath `inputs/` (223.6MB
uncompressed). For portable replay, extract into a fresh folder and set the
PowerShell environment variable to that folder's absolute inputs directory:

```powershell
$env:WISCO_DATA_ROOT = 'C:\work\wisco_audit_replay\inputs'
python C:\work\wisco_audit_replay\experiments\lakeshore_observability\real_scene_audit\audit.py
```

Run direction_qa.py for the additional published-direction consistency check.
Then run package.py to generate the report/plots/ZIP. Its old-evidence
immutability checks require the full repository and original R1/R1A/R1B data;
those earlier evidence sets are not duplicated in this ZIP. Offline numerical
audit.py replay is self-contained with the included raw inputs. Input path
spelling in manifests changes after relocation; the SHA256 identities and
numerical CSV outputs remain the relevant comparisons.

`INPUT_MANIFEST.csv` records original absolute raw paths and ZIP member names.
`MANIFEST.csv` is an archive manifest: paths starting with inputs/ are raw ZIP
members, deliberately not committed again to Git. Other paths are repository
members. Old evidence manifests remain unchanged.

Missing 10/30m wind directions and unidentified layer heights are blank, not
interpolated. The inversion endpoint height and thermal-transition proxy are
not identified lake-breeze or internal-boundary-layer tops. Single-anchor AGL
estimates and low lidar gates remain sensitivity/diagnostic results.
