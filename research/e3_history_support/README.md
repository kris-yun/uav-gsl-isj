# Controlled history-support intervention

This incremental experiment changes native warmup termination only, in an
isolated observer. Frozen O24, gas worlds, masks, local GMRF, noise and record
window stay fixed. It does not run ROS or train a model.

The sole intervention length is220seconds, preregistered from the old physical
contribution age99percentile208.3seconds, rounded upward to20second multiples.
Both existing random initializations are reused. Exact common random prefixes
are verified up to the native first-exit event; the later unequal consumption
does not imply identical individual particle trajectories.

Read `中文科学裁决报告.md` and `SCIENTIFIC_VERDICT.json`. The extension does not
rescue the locked E3 source pair. Local wind error and2D structure were not
separately intervened on. A2 provides a limited normal-case pair guard, not a
new full-map posterior or a ROS nondegradation result.

To recompute tables in a copy of the extracted evidence, with Python and NumPy:

```powershell
$env:E3_HISTORY_OUTPUT = 'C:/path/to/E3_HISTORY_SUPPORT_20261025'
$env:E3_PAIR_OUTPUT = "$env:E3_HISTORY_OUTPUT/parent_control"
python code/analyze.py
python code/diagnostic_upper.py
```

`parent_control` supplies the old short-history traces and physical window
means. The previous complete paired-world ZIP retains the actual old raw
GADEN states; its hash is in the report. No new world is silently substituted.

`COST.json` retains exact successful compiler/run argv and warnings. The source
is `history_observer.cpp`; portable frozen headers and dependencies are in
`build_source/`. Rebuild with the recorded arguments after relocating those
paths; do not automatically rerun prepare/worker, which deliberately refuse
overwriting first experiment outputs. The existing Linux x86_64 PID reader and
its source are supplied. Byte-identical analysis outputs were checked in a
fresh directory. No further history durations were tried.
