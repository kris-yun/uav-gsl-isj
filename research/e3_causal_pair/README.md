# E3 paired physical response attribution

Read `中文科学裁决报告.md` and `SCIENTIFIC_VERDICT.json` first. This is a
four-world paired offline physics experiment and a same-trajectory observation
operator intervention. It is not a new ROS episode or a main-innovation pass.

Frozen O24, the old E3, all A2 normal references, and B2 domain diagnostics
remain intact. All formal new worlds ran once with the preregistered streams.

## Repeat analysis in a copy of the evidence archive

Python requires NumPy and SciPy. Do not rerun prepare/workers to reproduce tables.

```powershell
$env:E3_PAIR_OUTPUT = 'C:/path/to/extracted/evidence'
$env:E3_PARENT_OUTPUT = "$env:E3_PAIR_OUTPUT/parent_audit"
$env:PMFS_AUDIT_OUTPUT = $env:E3_PARENT_OUTPUT
python code/analyze.py
python code/diagnostics.py
python code/age_audit.py
python code/verify.py
```

On Linux, export the same environment variables. `age_audit.py` is a readonly
posthoc attribution, not an instruction to tune rollout/warmup or delete old gas.

## Native readout reproduction

Each `worlds/*/saved_world` contains all filaments at the queried physical steps,
with original-format serialization and a physical pre/post-step timeline. The
generator advanced every step from empty to240s; it did not jump checkpoints.
`RESPONSES.csv` gives actual frame bindings. Original RNG engines, distributions,
cyclic cache and source/runtime parameters are retained beside each world.

The supplied Linux x86_64 binaries require fmt8, yaml-cpp0.7, zlib and OpenMP;
libbsc is bundled. Use `LD_LIBRARY_PATH` to include `native_runtime/` as needed.
Original build argv, source IDs, and logs are retained. A reduced source set for
rebuilding the decoder/physics tool is supplied under `build_source/`.
`bash code/rebuild_tools.sh` gives the corresponding relocation-aware build
recipe (compiler versions and installed library ABIs can change the ELF hash).
The optional recipe itself was not rerun as another experiment.

Without generating gas, the supplied reader can independently query one world:

```bash
export LD_LIBRARY_PATH="$PWD/native_runtime:${LD_LIBRARY_PATH:-}"
./native_runtime/headless_saved_query ./native_runtime/OccupancyGrid3D.csv \
  ./worlds/true_r0/saved_world < ./worlds/true_r0/NATIVE_REPLAY_INPUT.csv \
  > ./replayed_true_r0.csv
```

For the old E3 contribution audit, the 95 queried original frames and native
wind are supplied under `original_E3_decomposition/saved_world`; the exact query
frame bindings are in `schedule/ORIGINAL_NATIVE_QUERY_INPUT.csv`. The native
`physics decompose` mode can re-read them without propagation. They are copies
of historical states, not the four new worlds.

## Interpretation boundaries

- Whole13station continuous physical-template diagnostic:4/4, with source-labelled
  references used only to measure observability. Unknown-amplitude control:3/4.
- All8to13station hit strings coincide in the four physical worlds. Adjacent
  windows are correlated and not independent realizations.
- Matching PID window events on the exact same native2D trajectories does not
  rescue the true-source worlds. The ordinary response reliability gate fails.
- Two-hypothesis ranks/errors are kept apart from1132cell fixed-bank metrics.
  The latter reuse the old tree and are not fresh native posterior/ROS results.
- The new gas-age support observation does not establish that longer warmup
  alone fixes the problem. No outcome-driven longer rollout was run.
- Historical `PHYSICAL_STOP_RECEIPT.json` records an engineering parser/build
  stop; final scientific execution is in `PHYSICAL_CAMPAIGN_RECEIPT.json` and
  `event_control/RECEIPT.json`. First compiler CPU receipt is explicitly unknown.

No ANCA/Poleg training, no new ROS, no changed source, no result-dependent retry.
