# DRPE V1 — Dendritic Resonant Plume Encoding

Status: **offline mechanism/endpoint screen POSITIVE; closed-loop pilot pending**.

Base execution commit:

`b24da77fd24bd5ea2cbb33caf856f80b9d7670e4`

This branch is deliberately separate from frozen TNQC V5. TNQC remains HOLD.

## Main innovation

**Dendritic Resonant Plume Encoding (DRPE)** transfers the multi-dendritic
resonance principle of the NeurIPS 2025 Dendritic Resonate-and-Fire neuron to
robotic gas-source inference.

Instead of treating gas evidence as a static accumulated hit map or as a
single leaky/exponential memory, sparse whiff-onset events drive three
damped resonant branches with fixed periods:

`P = {1, 5, 20} s`.

For branch k:

`z_k[t] = r_k exp(j omega_k) z_k[t-1] + u[t]`

with

`r_k = exp(-dt/(2 P_k))`, `omega_k = 2 pi dt/P_k`,

and normalized branch envelope:

`m_k[t] = |z_k[t]| / n_k[t]`,
`n_k[t] = r_k n_k[t-1] + 1`.

The scientific thesis is **resonant temporal coding of turbulent plume
encounters**, not "use an SNN".

## Secondary innovation 1 — Whiff-Onset Sparse Transduction (WOST)

Input event:

`u[t] = 1[c_t > 0.1 ppm and c_{t-1} <= 0.1 ppm]`.

Only the appearance of a new whiff excites the resonant branches. Dense hit
occupancy, continuous concentration and blank channels are not fed as extra
neural channels.

This is motivated by biological olfactory work showing that encounter timing,
intermittency, whiff and blank statistics contain navigational information.

## Secondary innovation 2 — Wind-Relative Resonant Readout (WRRR)

Resonant states are not used as a generic sequence embedding. For each source
candidate, branch activity is projected through candidate-relative transport
geometry along the executed trajectory:

- candidate-to-robot distance;
- local wind alignment;
- downwind feasibility;
- crosswind offset;
- wind-speed-weighted alignment.

A lightweight linear readout converts these fixed features into a candidate
source score. This is the GSL-specific bridge from the imported neural idea
to source inference.

## Frozen development constants

- gas-present threshold: 0.1 ppm (existing PMFS threshold);
- sensor sampling interval: 0.2 s;
- resonant periods: 1, 5, 20 s;
- resonator decay time: 2 periods;
- ridge alpha: 1.0;
- posterior tilt beta: 2.0;
- candidate-score clipping: [-3, 3] after within-bank z-normalization.

No fractional memory, branch pruning, refractory period, adaptive threshold,
TNQC score or predictive-coding score is part of DRPE V1.

## Training/evaluation discipline

The six existing House01/02/03 x seed0/1 traces are development data.

The offline screen is leave-one-House-out:

- House01 scorer trained only on House02+House03;
- House02 scorer trained only on House01+House03;
- House03 scorer trained only on House01+House02.

Source truth is used only as the supervised target on training Houses and for
endpoint evaluation on the held-out House.

Any closed-loop pilot must use **new seeds/realizations**. Seeds0/1 must not be
reused as the confirmatory closed-loop verdict.

## Targeted novelty boundary

Existing GSL literature already contains SNN-based odor-source distance
estimation, temporal odor encoding, peak/intermittency features and generic
deep/RL approaches. Therefore DRPE does not claim "first SNN for GSL".

The targeted distinction is the use of **multi-dendritic resonant neural
dynamics as a candidate-conditioned source-inference representation**, plus
the WOST and WRRR mappings above.

A targeted literature search did not find an existing robotic GSL method using
Dendritic Resonate-and-Fire dynamics, but this is not a proof of exhaustive
novelty and must be rechecked before publication.

## References

- Zhang et al., "Dendritic Resonate-and-Fire Neuron for Effective and
  Efficient Long Sequence Modeling", NeurIPS 2025.
- Reddy et al., "Learning to predict target location with turbulent odor
  plumes", eLife, 2022.
- Gumaste et al., "Behavioral discrimination and olfactory bulb encoding of
  odor plume intermittency", eLife, 2024.
- "Rapid distance estimation of odor sources ... based on spiking neural
  network", Sensors and Actuators B, 2025.
- "Neuromorphic Circuit for Temporal Odor Encoding in Turbulent
  Environments", IEEE Sensors Journal, 2025.

See `evidence/drpe_v1/OFFLINE_SCREEN_20260921.md` before any ROS run.
