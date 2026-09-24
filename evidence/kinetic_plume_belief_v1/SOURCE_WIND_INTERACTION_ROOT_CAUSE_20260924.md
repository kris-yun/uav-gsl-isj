# House02 root-cause audit — strong source × wind interaction

Date: 2026-09-24
Status: DEVELOPMENT-ONLY ROOT-CAUSE EVIDENCE

## Why this audit was run

M4-v3 learned a real bulk wind response but failed held-out W1→W2 response geometry.
Memory, wall-slide and simple vertical corrections did not repair that failure.

The question is whether the missing term is a reproducible source×wind interaction
rather than generic noise or a source-independent field-space distortion.

## Exact factorial interaction

For each plume realization, define:

[
I_{SW}=C(S2,W2)-C(S2,W1)-C(S1,W2)+C(S1,W1).
]

All quantities are the frozen House02 log1p concentration fields on the same
downsampled free-space grid used by M4-v3 D0.

### Realization A

- source main-effect norm: 98.1058
- wind main-effect norm at S1: 21.0357
- interaction norm: 54.7926
- interaction / source main effect: 0.5585
- interaction / S1 wind main effect: **2.6047**
- interaction cosine with source main effect: -0.2911
- interaction cosine with S1 wind main effect: -0.3558

### Realization B

- source main-effect norm: 94.9998
- wind main-effect norm at S1: 26.1549
- interaction norm: 54.2128
- interaction / source main effect: 0.5707
- interaction / S1 wind main effect: **2.0728**
- interaction cosine with source main effect: -0.3058
- interaction cosine with S1 wind main effect: -0.4782

### Reproducibility

The A/B cosine between the two independently realized source×wind interaction
fields is **0.9396**.

This is therefore not a stochastic fluke.

## Wind-response geometry is source-context dependent

True W1→W2 response:
- S1 A vs S2 A cosine: **0.0300**
- S1 B vs S2 B cosine: **0.00488**

Within the same source, however, independent plume realizations are consistent:
- S1 A vs B wind-delta cosine: **0.9079**
- S2 A vs B wind-delta cosine: **0.9523**

Thus the same wind intervention produces a stable but radically different spatial
response depending on source context.

## Frozen local-response transfer test

A source-blind 3×3 linear response kernel was fitted only to the legal S1
W1→W2 intervention and then applied without refitting to S2.

Instead of improving M4-v3, it reversed the held-out response direction:

- base 1729 A: 0.3506 -> kernel -0.3373
- base 1729 B: 0.3832 -> kernel -0.4512
- base 2718 A: 0.3407 -> kernel -0.3292
- base 2718 B: 0.3698 -> kernel -0.4414

Therefore the missing response is not a reusable local field-space distortion.

## Interpretation

The microscopic gas transport dynamics may remain source-agnostic after a
filament is born, but a **projected 2-D concentration field is not a sufficient
source-independent Markov state**.

Source birth location selects:
- which obstacle/corridor topology is visited;
- which shear/strain regions are traversed;
- which vertical exchange paths are sampled;
- the age and dispersion distribution arriving at each observed cell.

After those hidden variables are projected away, the effective reduced
wind-response law becomes strongly source-context dependent.

This explains why field-space compositional factorization repeatedly fails even
though explicit wind transport is real.

## Consequence

Do not keep repairing the 2-D M4 field operator.

The scientifically consistent place for source-independent transport is
**before field projection**, in a latent/Lagrangian transport state:

[
p_{t+1}=T(p_t,W,O),
qquad
p_{birth}sim Q_s,
qquad
C_t=Pi({p_t}).
]

Source affects birth/intervention; one shared transport law acts on particles or
latent transport states; only afterwards are they projected to concentration or
PMFS hit probability.

This provides a data-driven justification for re-opening the M5-style
source-agnostic Lagrangian world-model direction, but with a much narrower
claim: the main necessity is **pre-projection transport state**, not a generic
large particle transformer.

## Additional fast local closure probe

A scalar conservative flux regression trained on S1W1/S2W1/S1W2 achieved
reasonable held-out time-derivative cosine (~0.60), but only:
- 0.415 / 0.440 cosine on the S2 W2-W1 intervention delta.

Adding a simple telegraph/second-time-derivative term reduced those values to:
- 0.407 / 0.430.

Therefore a first-order scalar-flux memory extension is also insufficient.

## Current research decision

- M4-v3 field-space compositional mainline: remains STOP.
- Memory auxiliary: STOP.
- simple wall/vertical rules: STOP as sufficient explanation.
- first-moment/telegraph closure: insufficient.
- D2Q9 quick preview: negative so far; not the preferred mainline.
- **Promote pre-projection source-agnostic Lagrangian/latent transport as the next mechanism family.**

Next hard gate:
use recoverable high-fidelity filament transitions to determine whether a
small predictor-corrector transport law captures the source-relevant interaction
without requiring a large generative architecture.
