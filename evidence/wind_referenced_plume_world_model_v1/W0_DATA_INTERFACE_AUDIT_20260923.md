# W0 Data/Interface Audit — Physics-Anchored Stochastic Plume World Model

Date: 2026-09-23  
Branch: \`research/wind-referenced-plume-world-model-v1\`

## 1. Existing uploaded archives

Audited:

- \`TNQC_V5_R2_HOUSE123_SEED01_OFFLINE_HOLD_20260921_FINAL.tar.gz\`
- \`ACCEPTED_RAW_CONTEXT.tar.gz\`

They contain:
- robot sensor traces;
- wind traces;
- measured hit-probability maps;
- source posterior/candidate manifests;
- runtime provenance.

However the exported \`candidate_maps/\` directories are empty and no full spatial concentration/plume snapshot fields are included in the archives.

Therefore current uploaded evidence is **not sufficient** to train or validate a full stochastic plume field world model.

## 2. High-fidelity GADEN realization data exists on the user's VM

The 2026-09-22 independent-run runtime manifests point to local GADEN realization directories, e.g. House02:

\`/home/zyc/hcmc_v1_independent_data_20260922/H02_R2026092211/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20\`

The GADEN player log confirms:
- this directory is directly loaded as \`simulation_data_0\`;
- wind files are found under its \`wind/\` subdirectory;
- House02 environment dimensions are 83 × 119 × 26;
- cell size is 0.1 m;
- player rate is 1 Hz.

Thus the original VM likely still contains the high-fidelity field/filament data required for a world-model feasibility audit.

## 3. Major data-coverage problem

The six independent 2026-09-22 realizations have only one source location per House.

Observed realization roots:

| House | Realization seeds | Source position |
|---|---|---|
| House01 | 2, 3 | (-0.40, -2.90, -0.30) |
| House02 | 2, 3 | (0.00, -1.00, 0.20) |
| House03 | 2, 3 | (-0.45, 1.90, -0.10) |

Therefore the current high-fidelity data provides:

\[
3\ \text{source positions}\times2\ \text{independent plume realizations}.
\]

That is not enough to train and validate a source-conditioned generative operator over the full PMFS candidate-source space.

## 4. W0 decision

Current status:

\`W0 = YELLOW / HOLD FOR LOCAL GADEN COST AUDIT\`

The candidate is **not killed** because the complete GADEN simulator/scenario files are available on the user's VM and additional source-conditioned simulations may be generated.

But do not train OFM/PINO/FNO using only the current three source locations.

## 5. Required local VM audit before model implementation

For one existing realization root:

1. inventory all files and formats;
2. identify which files encode:
   - filament positions;
   - concentration grid;
   - gas occupancy/hit field;
   - wind grid;
   - timestamps;
3. export only a tiny representative sample and metadata;
4. determine whether a 2-D slice at the robot sensor height can be reconstructed exactly.

Then benchmark regeneration for **one new source position**:

- wall-clock time;
- CPU/RAM;
- disk usage;
- number of usable temporal snapshots;
- whether wind simulation can be reused;
- whether gas simulation alone can be rerun for a changed source.

Do not launch a large source grid yet.

## 6. Source-position design if generation is cheap

Do not simulate all PMFS candidates initially.

Stage W0.5:
- choose 4–8 source positions per House using a source-blind space-filling design;
- include obstacle/room diversity;
- generate 2 plume realizations each;
- reserve at least one source position per House as unseen-source validation.

Only expand if a tiny residual/world-model probe shows positive signal.

## 7. Hard stop rule

If one new high-fidelity GADEN source realization is too expensive to make a small multi-source dataset practical, demote M3 as the main innovation.

Do not compensate by training only on PMFS-generated fields: that would merely learn the same forward family whose mismatch is the scientific concern.
