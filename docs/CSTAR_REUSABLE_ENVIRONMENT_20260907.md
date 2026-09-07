# Reusable CSTAR environment preflight and verified launch path

2026-09-07. Current scope: existing House123, seed12; no algorithm training,
no new scenario/source/seed, no model or GMRF launch. This is infrastructure,
not M1/M2 scientific validation and not an unrestricted 'environment forever PASS'.

## Verified result

Execution code: `a16ffa346a0d643c73c21591d4694f4e4413a106`.
Evidence: `evidence/cstar_reusable_environment_20260907_r3/`.

- 22 synthetic regression tests pass on Windows and real VM Python.
- All 12 existing realization inputs pass numeric sequence checks: 132 wind
  files decoded/fingerprinted; 36 sampled gas headers checked, no filament body
  decoded. All 2,000 iteration filenames per realization are contiguous.
- The same generic reader independently rechecks **8,640 existing physical raw
  wind observations**, with maximum absolute vector error **0.0**. This is not
  another extraction or another training experiment.
- All three map identities, dimensions/origins/navigation-height slices and
  frozen candidate/endpoint CSVs pass hash and free-space checks.
- New fail-closed launch path passes all three real ROS stationary input probes,
  eight positive 0.2 s frames each. Resolved live sensor parameters match exactly.
- A separate verifier checks actual received ROS wind against numeric raw files:
  H01 `1.6244553827093888e-09`, H02 `1.8192811792640262e-09`, H03
  `7.180059963252106e-09` m/s maximum component error. Bootstrap frames are excluded
  from scientific observations; positive dual-clock stamps are checked explicitly.

Preflight SHA256:
`44d72183db0d19da8299c32cfe47ed9a9400930e8e981a42b0c6d412b09e6cdd`.

## Common code and responsibilities

`experiments/ctpi_cstar/environment_runtime.py` is independent of House names,
seed numbers and date-stamped VM directories. It supplies:

1. Strict numeric sequence discovery: reject missing indices, `01` aliases,
   suffix junk, negative indices, empty sequences and directories disguised as files.
2. Legacy gas-header decoding bounded to 136 decoded bytes, with dimensions,
   cell size and both coordinate encodings checked against original occupancy.
   Unsupported layouts fail explicitly; no best-effort silently wrong fallback.
3. Legacy component-major double and modern interleaved float32 wind decoding,
   normalized physical-vector fingerprints and float32 GADEN sampling/index order.
4. A raw-query reply checker using independent header/file authority, not merely
   trusting the helper's reported wind index. Same index plus wrong vector fails.
5. Explicit resolved sensor and dual-clock checks and byte-level file bindings.
6. Launch-time certificate matching for the requested geometry, helper and raw
   realization. A stale bound file or code byte makes the old certificate fail.

`tools/cstar_check_environment_runtime.py` produces the reusable preflight from
explicit input paths. It uses the existing binary-PGM-safe map validator. With
`--controlled-data`, it also verifies stored raw physical wind frames without
re-querying gas. This tool is evaluator-only; raw simulator metadata must never
be passed into production model features.

`tools/cstar_run_environment_house.py` now **requires** both
`--raw-query-executable` and `--environment-preflight`. It no longer defaults to
the historically wrong H01 loader. Before spawning processes, it verifies the
live-qualified helper's source/binary and certificate input bindings. After a
successful probe, it compares actual resolved sensor parameters to the certificate.
The fixed three-House hover profile remains a validation wrapper, not a generic
arbitrary-route navigator.

`tools/cstar_build_numeric_wind_query.sh` now resolves its own checkout instead
of `cd /home/zyc/CSTAR_CONTROLLED_ASSETS_20260907`. It accepts an explicit
dependency setup script as its first argument and still refuses to overwrite
an existing binary. A different build must earn a new qualification; changing
a path or generating a new JSON does not confer scientific authority.

## Reuse procedure

1. Generate a fresh preflight with explicit split, geometry, resolved sensor,
   clock, helper and helper-attestation inputs. There is no mtime-only cache.
2. Reuse that file for launch while its bound bytes remain unchanged. The launcher
   rehashes them. A changed map, wind file, sensor contract, helper or bound code
   requires a new preflight; a changed physical decoder requires physical parity.
3. Keep existing expensive banks/data untouched. Do not rerun maps or gas simply
   because a model checkpoint changed; validate the affected bindings instead.
4. Production model/controller launchers have not yet been implemented. They must
   adopt this boundary when built. Historical frozen extractors/runners remain
   historical evidence code, not sanctioned defaults for new experiments.

The tested VM orchestration is in `tools/cstar_verify_environment_runtime_vm.sh`
and `tools/cstar_probe_reusable_environment_vm.sh`. Independent physical ROS
verification is in `tools/cstar_verify_reusable_live.py` (a versioned evidence
verifier bound to this execution commit, not a general scientific gate).

## Explicit physical assumptions and remaining scope limits

- The existing replay advances a stored **0.5 s** field frame for each **0.2 s**
  sensor step, i.e. **2.5x field replay**. The new clock contract makes that
  mismatch visible; it does not silently change old experiments to physical-time
  replay. Wall pacing is a separate parameter. Any timing redesign needs a new
  prospective environment contract.
- The `dynamic` alias alone is not the sensor definition. Actual historical
  resolved parameters are asymmetric mode, rise/recovery 1.2 s, dead time 0.4 s,
  zero noise, unit gain. Use the complete manifest. A measured-gas EMA is not the
  true FOPDT delay queue, which depends on inaccessible raw gas inputs.
- Certificates are trusted reproducibility artifacts, not signed security
  attestations. Runtime shared-library/ROS dependency closure is not fully bound.
- Within a raw read session, wind/header caches assume immutable inputs. Start
  a new reader and preflight after editing data; this is not a live file watcher.
- Free-space candidate/endpoint checks do not establish arbitrary route tracking
  or clearance. The three live probes are stationary; full navigation remains
  a separate bounded gate.
- Header samples and wind verification do not establish integrity of all gas
  payload bodies. Existing provenance/evidence contracts remain required.

### Additional trajectory/map binding audit

The reusable preflight's map/candidate checks do not prove that every archived
history and frozen route pose is in that map frame. The new
`tools/cstar_audit_route_map_binding.py` performs that stricter check. Its first
run on the current controlled bundle is preserved as
`evidence/cstar_route_map_binding_20260907/AUDIT.json` and is **NO-GO** (H01,
H02 and H03 all contain solid or out-of-grid poses). This blocks any physical
prior or House closed-loop gate until the asset identity is repaired; no point
is silently snapped or translated.

## VM storage incident (preserved, not hidden)

The system volume reported 100% usage and zero ordinary-user free space when
`git fetch` tried to create a new verification worktree. No working tree was
reset and no old evidence, bank or experiment was removed. The just-uploaded
115 MB duplicate `CSTAR_ENV_RUNTIME_20260907.bundle` was deleted from `/home/zyc`;
its local original remains in `D:/ZYC/A-gas/_staging/`.

Validation instead used a byte-bound git-archive tree under
`/dev/shm/CSTAR_ENV_RUNTIME_20260907`. Source commit and code fingerprints are
recorded, and results were copied back into the Windows repository. Tmpfs is
ephemeral: the certificate there will not survive a reboot; regenerate it from
persistent originals. System-disk capacity has **not** been generally repaired.
No background algorithm or ROS process was left running by these probes.
