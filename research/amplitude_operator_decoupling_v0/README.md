# Amplitude observation operator: implementation-only OPEN replay

This standalone development module reads saved PMFS forward products. It does
not run a forward simulator or integrate a new likelihood into the planner.
The native occurrence implementation remains unchanged. No scientific gate is
reclassified; the historical D0 remains
`ME_PMFS_D0_MARK_INFORMATION_FORWARD_INADEQUATE`.

## Interface

`Arm` enumerates `u_nearest`, `u_footprint`, `rawu_nearest`, and
`rawu_footprint` (development default). `load_saved_mean_maps` requires explicit
`u` or `rawu`, checks all 11 states x 8 replicas, and averages float32 products
in float64. There is no Gaussian operation in this module. `rawu` is the saved
unblurred amplitude product, not a reconstruction from `u`.

`frozen_operators` constructs nearest one-hot and rectangular area weights from
the frozen geometric probe contract. Footprints outside the map are rejected;
wall support is not removed or renormalized. `ObservationOperator` is separate
from map selection. `AmplitudeTemplates.prepare` applies only that operator,
then the archived B2 EPS of 1e-9 and ten-time broadcast.

`AmplitudeTemplates.score` retains the archived B2 gain and SSE arithmetic.
Ranking uses strict comparisons, and Top-1 requires a unique minimum. These
scores are **not** posterior probabilities. Templates are area-averaged cell
count proxies, **not calibrated ppm**; no cell-area conversion is added.

## Reproduction

Use the bundled Python and its bundled packages. On Windows, set
`PYTHONNOUSERSITE=1` to prevent an unrelated user-site pandas installation from
shadowing them; set `PYTHONUTF8=1`, `OPENBLAS_NUM_THREADS=1`, and
`OMP_NUM_THREADS=1`. These runtime settings do not change the scientific
contract. The supplied Pro scripts under `pro_reference/code` are unchanged.

1. Run `pro_reference/code/test_readout.py` and `test_amplitude_readout.py`.
2. Run `pro_reference/code/reproduce.py --review-zip <exact D0 ZIP>` with
   `--out <evidence root>/pro_reproduction`.
3. Run `run_saved_readout.py --task-zip <task ZIP> --pro-zip <Pro ZIP>
   --d0-zip <D0 ZIP> --out <evidence root>/implementation`.

The implementation output directory must not already exist. The runner verifies
ZIP and internal inventory hashes, compares all twelve Pro reproduction CSVs,
checks four-arm templates/scores/gains/ranks against Pro, and checks native p
hashes across the replay. It also repeats scoring byte-for-byte.

## Cost interpretation

`compute_cost.csv` reports geometric operator construction, loading and averaging
both saved amplitude banks, arm projection/template preparation, and median/q95
online SSE latency after templates are prepared. Warmed latency uses the same
24 already-OPEN observations 100 times, without fitting. Memory fields report
NumPy array payload bytes, **not process RSS or Python object overhead**; shared
maps/operators must be counted once per environment. Forward simulation and
archive verification costs are excluded from online timing.

Only the existing 72 OPEN targets are used. House03, sealed data, fresh plume
generation, training, and closed loop are outside this implementation task.
The footprint D1 replay plan is superseded and is not executed.
