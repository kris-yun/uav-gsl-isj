# E3 horizontal-reference-wind diagnostic

Only the fixed-grid horizontal wind input is replaced. Frozen O24 and all old
evidence remain intact. This oracle information is an offline diagnostic,
never a deployment input. There is no new gas world, ROS, training, or3D armC.

The contract freezes z=0.7m at every44x48coarse-cell center. Actual GADEN
Environment/WindSequence APIs and an independent raw binary decoder agree on
all2112query vectors. No smoothing, filling, height selection or source-specific
correction is allowed. Original2D and3D masks are retained and their mismatch
is reported. Only scene.wind_xy changes. Same220second warmup,200record steps,
cache/uniform initial states, PID kernel andD=0.2scoring are used.

Read `中文科学裁决报告.md` and `SCIENTIFIC_VERDICT.json`. True-source PID
response recovers at stops8and9, but not10to13. The locked source-pair rank
does not recover; neither wind irrelevance nor a unique2D cause is established.
These pair results are not a new1132cell posterior or closed-loop metric.

Recompute tables in a COPY of the extracted evidence, with Python and NumPy:

```powershell
$env:E3_ORACLE_OUTPUT = 'C:/path/to/E3_HORIZONTAL_WIND_ORACLE_20261025'
$env:E3_HISTORY_OUTPUT = "$env:E3_ORACLE_OUTPUT/parent_history"
$env:E3_PAIR_OUTPUT = "$env:E3_ORACLE_OUTPUT/parent_pair"
python code/analyze.py
```

`parent_history` provides the old GMRF PID series; all current GMRF particle
traces were exactly replayed and checked against the previous experiment.
`parent_pair` supplies the actual four-world window means. Their raw native
physical states remain in the previous paired-world archive.

`COST.json` records all successful build/run argv. `export_wind.cpp` uses the
retained native GADEN parser. `history_observer.cpp` and its ELF are identical
to the previous isolated220second tool; the frozen O24 ELF is never overwritten.
Reduced native/frozen dependencies are under `build_source/`. Binaries are
Linux x86_64 and require the documented native fmt/yaml/zlib ABIs; libbsc is
included. Do not rerun prepare/worker against first outputs, which deliberately
refuse overwrite. Portable result recomputation was independently checked.
