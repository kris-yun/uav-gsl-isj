# M6 Novelty Audit v1 — Physics Foundation Transfer for PMFS/GSL

Date: 2026-09-23  
Branch: `research/geopt-physics-foundation-pmfs-v1`

## Decision

`NO DIRECT COLLISION FOUND YET — KEEP, WITH NARROW CLAIM BOUNDARY`

The broad phrases "deep learning for GSL", "neural operator for GSL", "pretraining for GSL", and "foundation model for gas" are **not** defensible novelty claims.

M6 survives only under a much narrower scientific claim:

> transfer a **cross-physics, dynamics-lifted geometry foundation representation** into the PMFS candidate-source forward model, preserving its pretrained geometry–dynamics backbone and learning a small gas/source-specific injection adapter under scarce high-fidelity plume supervision.

## 1. Direct GSL near-neighbors

### 2024 — Physics-guided NN for GSL

Prieto Ruiz et al., *Gas Source Localization Using Physics-Guided Neural Networks*, ISOEN 2024.

They:
- use a learned gas-dispersion surrogate;
- include source location as a network input;
- solve the inverse localization problem efficiently.

Therefore M6 cannot claim:
- first learned forward surrogate for GSL;
- first physics-guided neural gas dispersion for source inversion;
- first source-conditioned neural forward model.

### 2026 — Physics-informed neural operator for GSL

Quanqi Zheng & Lei Chen, *A physics-informed neural operator for gas source localization in turbulent environments*, IROS 2026 accepted.

Public details are still limited, but the title alone occupies:
- neural operator + GSL;
- physics-informed operator + turbulent gas localization.

Therefore M6 cannot claim:
- first neural operator for GSL;
- first PINO/PINO-like GSL.

A full-text comparison is mandatory when the paper/code becomes public.

### 2026 — Deep probabilistic indoor GSL

Kim et al., *Deep Probabilistic Indoor Gas Source Localization via Physical Dependency-Guided Sequential Inference*, arXiv:2608.16221.

DGSE-S:
- predicts source posterior directly over map cells;
- estimates probabilistic wind and concentration fields;
- explicitly uses physical dependency structure;
- operates online in active mobile-robot GSL.

Therefore M6 cannot claim:
- first deep probabilistic indoor GSL;
- first deep model incorporating wind/concentration physical dependencies;
- first learned source posterior in complex multi-room environments.

## 2. Pretrain/fine-tune is not itself novel in robotic GSL

Liu et al., *A Fast-trained and Generalized Spiking Neural Network for Robotic Gas Source Localization*, ICARM 2024.

The method uses a pretrain–fine-tune paradigm for robotic GSL.

Therefore do not claim:
- first pretraining for robotic GSL;
- first fine-tuned pretrained model for GSL.

The M6 distinction must be **physics foundation pretraining across broad geometry–dynamics systems**, not generic task pretraining.

## 3. Foundation models have already been used for gas/methane tasks

Examples:
- 2025 IEEE Access work uses Segment Anything Model for hyperspectral methane plume segmentation;
- related SAM/VLM methane plume mapping also exists.

Therefore do not claim:
- first foundation model for gas/methane applications.

These works are remote-sensing detection/segmentation, not PMFS-style source inversion or physical forward simulation.

## 4. Recent gas-dispersion surrogate near-neighbors

Recent 2026 works include:
- obstacle-resolved physics-enhanced deep learning for gas dispersion under unseen wind/source/leak conditions;
- conditional Fourier neural operator with analytical prior for spatio-temporal gas-dispersion forecasting.

These strengthen the prior-art boundary:
- accurate learned gas dispersion under varying wind/source is not itself novel;
- generalization to unseen wind/source is not by itself enough.

## 5. Current defensible M6 hypothesis

The scientific object is specifically:

### Parent representation

A pretrained geometry–dynamics physics foundation model learned across large heterogeneous physical systems.

### Gas adaptation

Preserve the pretrained 11-D geometry+dynamics interface:

[
[x,y,z,mathrm{SDF},d_x,d_y,d_z,
hat w_x,hat w_y,hat w_z,|w|].
]

### PMFS-specific source mechanism

Inject the candidate source through a small hidden-space source adapter, without rebuilding the foundation backbone.

### Main empirical claim

Under scarce GADEN labels, the pretrained representation should:
- require fewer source simulations;
- generalize to unseen source locations;
- improve PMFS candidate-source rank relative to:
  - Native PMFS;
  - same Transolver from scratch;
  - small task-specific neural surrogate.

This low-data transfer advantage is the key M6 claim.

## 6. Claim discipline

Until a final systematic audit is complete, do NOT write "first."

Potential future wording:

> We adapt a dynamics-lifted physics foundation representation to PMFS-style source localization, preserving the pretrained geometry–dynamics backbone while introducing a localized source-injection adapter for candidate-conditioned gas transport.

## 7. Current risk assessment

Direct GSL collision: **low-to-moderate**.  
Generic learned-surrogate collision: **high**.  
Generic pretraining collision: **present**.  
Physics-foundation-transfer distinction: **currently open-looking**.  
2026 IROS PINO uncertainty: **must remain an explicit risk**.

Status:

`KEEP — NOVELTY DEPENDS ON FOUNDATION TRANSFER, NOT OPERATOR ARCHITECTURE`.
