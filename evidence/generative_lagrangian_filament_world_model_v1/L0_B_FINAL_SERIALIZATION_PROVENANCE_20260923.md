# L0-B Final Serialization Provenance — No Native Filament ID

Date: 2026-09-23  
Branch: \`research/generative-lagrangian-filament-world-model-v1\`

## Decision

\`ASSUME NO NATIVE FILAMENT ID\`

Use the already derived sigma-age / preserved-order pseudo-ID scheme.

Do not rely on the \`filament_index\` field seen in legacy GADEN loaders.

## 1. Exact upstream dependency

MAPIRlab/GADEN:
- branch: \`humble\`;
- commit inspected: \`ccb02e959a45a188e4b6c78792e197633fc64f1c\`.

Its git submodule:

\`gaden_common/third_party/gaden_core\`

is pinned to:

\`1a20e35cd5f174ae9675a2ae3c796137a05c4ee5\`.

## 2. Exact serialization contract at that gaden_core commit

\`Filament.hpp\` contains only:

\`\`\`cpp
Vector3 position;
float sigma;
\`\`\`

\`RunningSimulation::SaveResults()\` writes modern filament-mode files using:

\`\`\`cpp
writer.WriteVector(activeFilaments);
\`\`\`

Therefore modern result files contain the active vector of \`Filament{position,sigma}\` and no persistent filament index.

## 3. Why legacy loaders are misleading

\`PlaybackSimulation.cpp\` contains backward-compatibility paths for:
- version 1;
- pre-2.6;
- version 2.6.

Those legacy parsers read an integer \`filament_index\` before x/y/z/stddev.

However the modern \`LoadLogfile()\` path reads the vector directly and has no ID field.

Therefore the presence of \`filament_index\` in old-format parsing does **not** imply the 2026 project realizations contain IDs.

## 4. Project-generation consistency

The project independent-realization generator uses the ROS \`gaden_filament_simulator\` wrapper, which constructs \`gaden::RunningSimulation\` and delegates saving to gaden_core.

The frozen 2026-09-22 generation contract records:
- 7 filaments/s;
- dt=0.1 s;
- sigma0=10 cm;
- gamma=15 cm²/s;
- write concentrations=false;
- result timestep=0.5 s.

The project RNG patch changes seeded random-number generation for independent plume realizations; no evidence indicates a serialization-schema modification.

## 5. Conservative training contract

For M5:

- never assume vector index is globally persistent;
- infer age from deterministic sigma;
- infer birth step from frame step minus age;
- use birth step as pseudo-ID under the current ≤1 birth/step generator;
- validate ordering, sigma progression, disappearance/no-reappearance, and physical displacement before accepting a track.

If any validation fails, discard that track rather than silently rematching it.

## 6. Scientific consequence

This is still sufficient for Lagrangian supervision because the pseudo-ID is based on known simulator invariants, not nearest-neighbor spatial matching.

Status:

\`L0 COMPLETE — ADVANCE TO L1 RESIDUAL STRUCTURE\`.
