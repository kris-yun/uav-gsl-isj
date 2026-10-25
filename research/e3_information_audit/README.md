# Frozen O24 E3 information-source audit

This is an offline evidence audit, not a new PMFS implementation or localization
performance result. Frozen O24, the native source domain, and all old runs stay
unchanged. No new worlds, forward propagation, training, or ROS were launched.

Read `中文科学裁决报告.md`, `SCIENTIFIC_VERDICT.json`, and the separate physical
information / representation / ordinary planning verdicts first.

The archive contains E3 and all three A2 normal controls, all candidate caches,
560 consumed windows, 36 source updates, fixed short-query designs, 640 actual
native E3/E4 readouts, and the 101 physical frames needed to repeat them.
E4 is NOT a real realization of the locked wrong MAP: its source position and
height differ. The exact locked pair remains data-limited.

## Recompute tables without ROS or the VM

Requires Python, NumPy and SciPy. Work on a copy of the extracted evidence.

```powershell
$env:PMFS_AUDIT_OUTPUT = 'C:/path/to/extracted/evidence'
$env:PMFS_REPLAY_ROOT = "$env:PMFS_AUDIT_OUTPUT/replay_layout"
python code/audit.py analyze
python code/audit.py analyze_queries
python code/verify.py
```

The original A2/B2 experiment-table read is optional on portable recomputation;
its frozen table is already saved. `prepare`, `plan_queries`, `finalize`, and
`read_existing_guest` document original local execution and should not be used
to overwrite the delivered preregistration or reread already-completed data.

## Repeat the native concentration readout (Linux x86_64)

The supplied readonly ELF uses fmt8, yaml-cpp0.7, zlib, OpenMP, and the bundled
libbsc. It does not run `RunningSimulation`. From the extracted evidence root:

```bash
LD_LIBRARY_PATH="$PWD/native_query${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
  native_query/headless_saved_query native_query/OccupancyGrid3D.csv \
  native_query/E3/saved_world < native_query/E3/QUERY_INPUT.csv > E3_reproduced.csv
```

Repeat for E4 and compare by `query_id`, frame, position, and `raw_gas_ppm` with
the saved output. All queries must remain within the supplied physical frames.
Native reader source and original build recipe are included for audit/building.

Do not count four 10 Hz requests within the same stored snapshot as four new
physical samples. Raw concentration differences from E3/E4 are descriptive
single-realization evidence, not unknown-source classification/accuracy gains.

`MINIMUM_MISSING_DATA_CONTRACT_PROPOSAL.json` is a proposal only. It does not
authorize or document execution of new gas worlds or ROS.
