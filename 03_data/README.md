# 03 — Data and Evidence Map

This directory is the data/evidence entry point. Raw VGR/GADEN House scenario
data are **not stored in this repository**. The repository stores compact
evidence, manifests, summaries, checksums and selected frozen artifacts.

## A. External project datasets

The authoritative VGR/GADEN House data are expected on the qualified
experimental VM at paths such as:

- `/mnt/hgfs/workspace/GADEN_files/scenarios/House01`
- `/mnt/hgfs/workspace/GADEN_files/scenarios/House02`
- `/mnt/hgfs/workspace/GADEN_files/scenarios/House03`

Those external datasets are not redistributed here.

Users must obtain/prepare compatible scenario data and ROS/GADEN
dependencies separately.

## B. Committed evidence

Primary evidence tree:

`evidence/`

Important categories:

### Historical ME-ACI evidence

- `evidence/RESULT_MATRIX.csv`
- `evidence/cases/`
- `evidence/MEACI_V10_MAIN_INNOVATION_HOUSE123_SEED01_6OF6_20260824.zip`
- `evidence/SHA256SUMS.tsv`

These belong to the frozen historical ME-ACI result and should not be
presented as the TNQC 300-s result.

### TNQC mechanism evidence

- `evidence/TNQC_VGR_240S_SPATIAL_MECHANISM_20260921.json`
- `evidence/TNQC_VGR_DISTRIBUTED_SUPPORT_AUDIT_20260921.json`

These are **concentration-space mechanism evidence**. They support the idea
that nuisance-reduced spatial structure can preserve source information, but
they are not the authoritative online hit-logit localization result.

### TNQC implementation/evaluation evidence

- `evidence/TNQC_CPP_ENDPOINT_PARITY_AUDIT_20260921.json`
- `evidence/TNQC_V5_IMPLEMENTATION_MANIFEST_20260921.json`
- `evidence/TNQC_IMPLEMENTATION_SANITY_20260921.json`

These describe evaluator semantics, source-byte freezes and implementation
integrity.

## C. Authoritative TNQC result location

The first authoritative TNQC online-representation feasibility result is
supposed to come from:

House01 / House02 / House03 × seed0 / seed1, full 300 simulation seconds,
using the original PMFS top-5% ExpectedValue localization endpoint.

At the time of this organization pass, no valid six-case TNQC aggregate has
been produced. A recent execution attempt stopped before preflight because
the local WSL/VM launch environment was unavailable.

Therefore the repository must currently say:

**TNQC 300-s localization result: pending.**

Not GO. Not HOLD.

## D. Evidence hierarchy

Use the following labels consistently:

- **mechanism evidence** — representation retains useful source structure;
- **integrity evidence** — implementation/evaluator matches the frozen
  scientific contract;
- **fixed-trajectory localization evidence** — method changes inference on a
  frozen native trajectory;
- **closed-loop localization evidence** — method is allowed to affect later
  robot motion;
- **external falsification evidence** — useful robustness evidence from
  another dataset, but not the project benchmark.

Do not collapse these categories into a single “validated” label.

## E. Primary endpoint

The project primary endpoint is:

`ExpectedValue(sourceProbability, 0.05)`

followed by Euclidean distance to the true source.

TNQC uses a linked-native evaluator built from the same ROS source tree and
directly calls the original `GSL::Utils::ExpectedValue(grid, 0.05)` to avoid
Python tie-breaking differences at the 5% cutoff.

## F. Reproducibility and provenance

Important provenance mechanisms include:

- Git blob SHA manifests;
- full `ros2_package` subtree SHA;
- clean-build requirement;
- runtime binary SHA256;
- external launch-file SHA256 captured per batch;
- per-case runtime manifests;
- native posterior reconstruction audit;
- native endpoint parity audit;
- deterministic case naming;
- source-update timing logs.

## G. Data-publication boundary

This repository intentionally separates:

1. **code and method definitions**;
2. **small reproducibility evidence and summaries**;
3. **large/external VGR/GADEN scenario data**.

Public availability of this Git repository does not imply that every external
dataset or third-party dependency is redistributed under the same terms.

Check the original dataset/software licenses before redistributing external
assets.
