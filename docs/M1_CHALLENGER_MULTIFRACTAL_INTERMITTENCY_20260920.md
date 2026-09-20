# M1 Challenger 5 — Multifractal / Multiscaling Intermittency for Source Identity

Date: 2026-09-20
Branch: research/remote-paradigm-loop-20260919
Status: SCREENED / NO-GO AS M1

## Remote-domain provenance

Recent physical-science anchors:
- Physical Review Letters 134, 088302 (2025), *Onset of Intermittency and Multiscaling in Active Turbulence*.
- Physical Review Fluids 10, 084605 (2025), *Hidden symmetry in passive scalar advected by two-dimensional Navier–Stokes turbulence*.
- Physical Review Fluids accepted 2026, *Joint multifractal description of small-scale turbulence: Unifying longitudinal and transverse velocity intermittency*.

The transferable scientific object is genuine turbulence physics:
- scale-dependent structure functions;
- anomalous scaling exponents / multiscaling;
- intermittency spectra.

This is not “multiscale pooling”.

## Candidate GSL thesis

A mobile gas trace is a one-dimensional cut through an intermittent passive-scalar field.
If source location changes the organization of plume intermittency along that cut, source identity might be encoded in the scale dependence of concentration increments rather than in absolute concentration.

## Existing-data proxy

Data:
- H01/H02/H03 × {SA,SB} × {fast,slow}.
- log concentration histories.
- source-blind temporal structure functions at lags 0.4, 0.8, 1.6, 3.2, 6.4, 12.8 s;
- moment orders q=1..4;
- scaling exponents and ESS-style exponent ratios.

Fast-wind source fingerprints were used as references; slow wind was held.

### Positive cases

H01:
- at 180 s, exponent-only representation recovers 2/2 held-wind identity with wind/source ratio ~0.43.
- a deterministic order-destroying permutation drops it to 1/2 and ratio >1.
- at 210 s, ordered exponent representation remains 2/2 and substantially better than the permuted control.

H03:
- 150 s exponent ratio ~0.035, 2/2; permutation drops to 1/2 and ratio ~0.62.
- 180 s exponent ratio ~0.018, 2/2; permutation drops to 1/2 and ratio ~0.62.

Thus there are real cases where multiscale temporal ordering contains source-discriminative information.

### Negative cases

H02:
- 120–150 s remains 0/2, consistent with absent source support.
- 180–210 s exponent/shape representations reach only 1/2; destroying order can even improve some variants.
- only at 240 s does the representation recover 2/2.

H03:
- at 240 s exponent-only/normalized scaling-shape representations degrade to 1/2.
- full structure-function amplitudes retain 2/2, indicating that scale-law shape alone is not the stable source object.

H01:
- full structure-function representation at 150–210 s can remain 1/2 even when exponent-only variants are better.

## Theory-level warning

Multifractal / anomalous scaling theory is largely designed to expose universal or flow-regime properties of turbulence.
That creates a fundamental tension for source localization:
- the more universal the scaling law is across source positions, the less source identity it should carry;
- source-specific information in the current proxy can come from finite-horizon geometry/route effects rather than a genuine source-conditioned multifractal law.

The current data do not justify a theorem or stable empirical claim that source location induces a unique multifractal spectrum.

## Collision screen

Direct search found extensive odor-plume work on intermittency, whiff/blank timing and temporal plume statistics, but no direct 2025/2026 GSL paper using multifractal source-probability inference.

Absence of a direct collision is not enough: the cross-House mechanism gate fails.

## Decision

MULTIFRACTAL / MULTISCALING M1 = **NO-GO**.

Allowed future use:
- diagnostic for intermittency regimes;
- possible ablation for M2 η-learning;
- not a main innovation and not one of the final module slots.

Reason:
> genuine turbulence physics is present, but the unique multifractal object is not stably source-specific across Houses and horizons.
