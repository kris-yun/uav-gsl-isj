# UAV Gas Source Localization — Research Repository

This repository contains two clearly separated research layers for
PMFS-based single-UAV gas-source localization:

1. the frozen historical **ME-ACI V10** development result;
2. the newer **TNQC (Transport-Nuisance Quotient Canonicalization)** research
   cycle, whose authoritative full-300-s feasibility result is still pending.

The repository has been reorganized around three top-level entry points
without moving frozen executable/evidence files:

| Start here | Purpose |
|---|---|
| [01_idea/](01_idea/) | Research philosophy, module-discovery loop, theory hierarchy, current TNQC thesis |
| [02_code/](02_code/) | Online ROS/PMFS code, replay/evaluator code, tests and execution map |
| [03_data/](03_data/) | Evidence/data provenance, external House-data boundary, endpoint definitions |

For public-release provenance and upstream/licensing notes, see
[PUBLIC_RELEASE_NOTES.md](PUBLIC_RELEASE_NOTES.md).

---

## Core research philosophy

The project does **not** start from “add another module and see if the score
improves.”

The working doctrine is:

**recent cross-domain scientific idea**
→ **structural/physical mapping to GSL**
→ **minimal mathematical formulation**
→ **source-blind offline falsification on existing VGR data**
→ **keep/reject based on signal**
→ **add only subordinate auxiliary mechanisms**
→ **freeze before authoritative truth**
→ **full 300-s localization gate**
→ **closed loop only after offline GO**

The main innovation must carry a paper-level scientific thesis—such as
causality, symmetry/canonicalization, quotient-space inference, or another
similarly general principle—rather than being an engineering patch stack.

The complete formulation is in [01_idea/README.md](01_idea/README.md).

---

## Historical frozen result — ME-ACI V10

ME-ACI V10 is the previous frozen main-innovation implementation. It treats
gas-source localization as conditional inverse transport with sequential
replication gating.

Its development evidence used three VGR/GADEN House datasets and two seeds
per House. The metric is PMFS top-5% probability-weighted source-location
error.

| House | Seed | Native PMFS (m) | ME-ACI V10 (m) | Reduction |
|---|---:|---:|---:|---:|
| H01 | 0 | 5.152589 | 2.501097 | 51.459% |
| H01 | 1 | 6.928495 | 5.006343 | 27.743% |
| H02 | 0 | 2.926781 | 2.271832 | 22.378% |
| H02 | 1 | 1.813416 | 1.307146 | 27.918% |
| H03 | 0 | 6.652648 | 2.863832 | 56.952% |
| H03 | 1 | 5.219942 | 2.982003 | 42.873% |

- Pass rate: **6/6** at the frozen >=10% individual-improvement threshold.
- Pooled error: **4.782312 m -> 2.822042 m** (**40.990% reduction**).
- Worst individual reduction: **22.378%**.
- First accepted update: **72.851–217.811 simulation seconds**.

Important limitation: these are **first-identifiable-intervention**
comparisons, not final-300-s endpoint values. They are historical
mechanism/development evidence and must not be reused as the terminal 300-s
baseline for a new method.

Frozen identifiers:

- Run contract: `MEACI_SEQUENTIAL_SPATIAL_REPLICATION_V4`
- Formula marker: `inverse_transport_sequential_replication_v3`
- Source-update cadence: `stepsSourceUpdate=3`
- Runtime budget: `300 simulation seconds`
- Qualified online binary SHA-256:
  `14133117b9d24502acc8e45ad7c72fbd668fbe867fd73aeee17b70e52cfbe938`

Historical evidence lives under `evidence/` and `artifacts/`.

---

## Current research-cycle candidate — TNQC V5

The current candidate is **TNQC: Transport-Nuisance Quotient
Canonicalization**.

Its main idea is to compare measured and transport-predicted PMFS spatial
fields after canonicalizing nuisance coordinates, so source inference is
performed in a nuisance-reduced representation rather than raw amplitude
coordinates.

Current V5 ingredients:

- confidence-weighted centered cosine in PMFS hit-logit space;
- local spatial-order corroboration as an auxiliary channel;
- terminal active PMFS leaves only;
- free-cell hypothesis-measure weighting;
- local-order support-coverage attenuation;
- a ranking-safe shared nonnegative gate;
- bounded exponential/Gibbs-style evidence tilt;
- linked-native PMFS `ExpectedValue(...,0.05)` endpoint evaluation.

The exact invariance claim is intentionally narrow: it applies to
positive-affine transformations of the supported hit-logit representation
with fixed support/weights. It is not an unqualified claim of exact
invariance to arbitrary raw physical sensor/release transformations.

### Current TNQC scientific status

- concentration-space VGR mechanism evidence: **positive**;
- implementation/evaluator integrity: **frozen and audited**;
- full-300-s hit-logit fixed-trajectory House gate: **pending**;
- closed loop: **HOLD until offline GO**.

A recent execution attempt did **not** produce a scientific result: it stopped
before experiment start because of WSL/VM launch infrastructure loss.
Therefore TNQC is currently neither GO nor HOLD on the 300-s gate.

Authoritative entry point:

[CODEX_START_HERE.md](CODEX_START_HERE.md)

---

## Repository map

### 01 — Idea

[01_idea/README.md](01_idea/README.md)

Contains:

- the module-discovery philosophy;
- “big idea first” selection criteria;
- evidence hierarchy;
- main-vs-auxiliary innovation rules;
- rejection criteria;
- current TNQC conceptual formulation;
- freeze discipline.

### 02 — Code

[02_code/README.md](02_code/README.md)

Primary executable trees remain:

- `ros2_package/` — online ROS/PMFS implementation;
- `reference/` — replay, evaluator, build, runner and tests;
- `artifacts/` — selected frozen qualified binaries.

Files were intentionally **not physically moved**, because exact paths and
bytes are part of the scientific manifests and reproduction contracts.

### 03 — Data / evidence

[03_data/README.md](03_data/README.md)

Primary evidence tree:

- `evidence/`

Raw VGR/GADEN House scenario datasets are external and are not redistributed
in this repository.

---

## Reproducibility

For the historical frozen result, see:

[docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md)

For current TNQC execution, start at:

[CODEX_START_HERE.md](CODEX_START_HERE.md)

Repository-level historical integrity checker:

```bash
python3 verify_repository.py
```

TNQC uses additional manifest/tree/binary integrity guards documented in the
current execution contract.

---

## Upstream / licensing note

The captured `ros2_package/package.xml` declares the upstream
`gsl_server` package as **GPLv3** and names its upstream maintainer. The ROS
tree includes upstream/third-party-derived components.

Public availability of this repository is not a claim that every line in the
captured ROS package was authored by this project, and it does not relicense
external VGR/GADEN datasets.

See [PUBLIC_RELEASE_NOTES.md](PUBLIC_RELEASE_NOTES.md).
