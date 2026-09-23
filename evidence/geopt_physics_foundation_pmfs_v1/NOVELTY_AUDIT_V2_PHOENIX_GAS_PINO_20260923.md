# M6 Novelty Audit v2 — Foundation Transfer vs Gas-Specific Surrogates

Date: 2026-09-23  
Branch: `research/geopt-physics-foundation-pmfs-v1`

## Decision

M6 remains **OPEN**, but its novelty claim is now substantially narrower.

Do **not** claim:
- first learned plume simulator;
- first physics-guided gas surrogate;
- first neural operator for GSL;
- first gas model that conditions on wind/source/obstacles;
- first gas model that generalizes to unseen wind/source conditions.

## 1. Strong 2026 near-neighbor — PHOENIX-UNet

Jianyao et al., *Physics-enhanced deep learning for obstacle-resolved atmospheric dispersion in leakage accidents*, Building and Environment 301 (2026), 114797.

PHOENIX-UNet already:
- predicts obstacle-resolved gas concentration fields;
- incorporates Gaussian-plume physics priors;
- incorporates building/obstacle geometry;
- conditions on meteorological variables;
- conditions on source information;
- reports generalization to unseen wind directions, wind speeds, and source locations;
- provides public code and a public ~4000-case dataset.

Its public implementation uses:
- 3-channel image input:
  - building mask;
  - Gaussian-plume prior;
  - source map;
- source + meteorology metadata;
- physics-enhanced fusion blocks inside a U-Net;
- approximately 4.30M trainable parameters in the published configuration.

This is a **strong near collision** for generic physics-enhanced plume surrogates.

## 2. 2026 gas-PINO collision

A 2026 IROS-accepted gas-source-localization work already occupies the broad claim:
- physics-informed neural operator for gas source localization.

Therefore M6 must not be framed as “PINO but with another backbone.”

## 3. What is still distinct

The M6 hypothesis is specifically:

> a **cross-domain physics foundation model**, pretrained before seeing gas-plume labels on large-scale geometry–dynamics self-supervision, can be transferred into PMFS and achieve useful source-conditioned plume prediction with much less gas-specific high-fidelity data than gas-specific training from scratch.

The novelty object is **pretrained geometry–dynamics representation transfer**, not the downstream surrogate architecture alone.

## 4. Hard empirical implication

M6 is only interesting if:

[
	ext{pretrained GeoPT}
>
	ext{same architecture from scratch}
]

in the **low gas-data regime**.

A full-data tie is not sufficient.

A speedup with no source-rank benefit is not sufficient.

## 5. Required controls

At minimum compare:

### A — GeoPT pretrained backbone
- official pretrained weights;
- gas-specific source adapter/head.

### B — identical Transolver architecture from scratch
- exact same gas input contract;
- exact same adapter/head;
- random initialization.

### C — small gas-specific physics surrogate
Prefer either:
- PHOENIX-like matched-capacity baseline; or
- a simpler physics-enhanced network with public PHOENIX settings.

Parameter counts must be reported.

## 6. Low-data scaling gate

Freeze data subsets before training:

- 5%;
- 10%;
- 25%;
- 50%;
- 100%.

For each subset, compare:
- held-out field error;
- held-out hit/miss likelihood;
- convergence speed;
- downstream truth-source candidate rank.

Main M6 signature:

> the pretrained model reaches a given source-identification quality with substantially fewer gas-specific simulations.

## 7. Public external sandbox

PHOENIX's public dataset is a useful **external transfer sanity test** because it contains:
- obstacle geometry;
- many source locations;
- multiple wind directions/speeds;
- concentration fields.

However the public archive is approximately 14.7 GB.

Do not download the whole archive solely for a speculative first test unless bandwidth/storage are acceptable.

Use it only if:
- Codex/VM has convenient access; or
- a smaller subset can be extracted/downloaded.

The main project evidence must still come from GADEN/VGR House data.

## 8. Source adapter novelty boundary

The source injection adapter is a gas-specific second derivation, not the main mother idea.

Its role is to:
- keep the pretrained GeoPT input embedding unchanged;
- preserve environment geometry+wind features;
- inject PMFS candidate source downstream.

It must not be marketed as a standalone main innovation.

## 9. Current verdict

M6 survives because no direct prior art has yet been found for:

> **cross-physics foundation-model transfer into PMFS-style gas-source localization with low-data source-conditioned adaptation.**

But its novelty margin against modern gas-specific surrogates is narrower than initially assumed.

Status:

`KEEP — ONLY IF PRETRAINING DATA-EFFICIENCY + SOURCE-RANK BENEFIT IS DEMONSTRATED`.
