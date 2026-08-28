# CG-PC-CTT V6 — dynamic transport-conditioned source inference research freeze

Date: 2026-08-28

Branch: `research/cg-pc-ctt-v6-dynamic-transport-sbi`

Parent V5 audit HEAD: `3ae1e708c285f9c4ef16849758cdf1ab30aa3a85`

## Status

`V5_ACTIVE_PROBE = HOLD`

`V6 = NEW_METHOD_VERSION / PRE-CPP FALSIFICATION`

V5 removed the exact trajectory lock, but passive cumulative replay on 30 development runs produced 0/30 runs with any ACCEPT after a median of 16 unique cells. Final failures were dominated by `CONTEXT_LOO_COMPONENT_DISAGREE`.

This does NOT yet prove that the frozen transport family is irreparably misspecified. V5 also changes the observation-resolved source partition as more physical stops are added. As resolution increases, a hard exact component identity can become progressively finer and can fail even when continuous source probability transfers across contexts.

V6 therefore separates two hypotheses before any further C++ work:

- H-A: hard component identity is the primary blocker;
- H-B: continuous source evidence itself reverses across contexts because the transport representation is structurally inadequate.

No Active Probe smoke and no 60-arm performance matrix are authorized until this separation is complete.

## 2026 big-science method anchors

These are methodological inspirations, not novelty claims.

1. Somer, Mannor & Alon, **Temporal tissue dynamics from a spatial snapshot**, Nature 650, 490–499 (2026), DOI `10.1038/s41586-025-09876-1`.
   - Capability extracted: recover dynamics from event/neighbourhood structure rather than treating one snapshot as a static state.
   - GSL implication: the eight completed gas blocks at one physical stop may contain dynamical information that is destroyed by reducing them to one mean hit fraction.

2. Lenain et al., **An unprecedented view of ocean currents from geostationary satellites**, Nature Geoscience 19, 526–533 (2026), DOI `10.1038/s41561-026-01943-0`.
   - Capability extracted: transform sequential scalar tracer observations into features that reveal hidden transport; three consecutive `log|grad T|` frames are used to infer the underlying velocity field.
   - GSL implication: source inference should condition on recovered transport dynamics rather than demanding raw source-likelihood invariance under an unmodelled changing flow state.

3. Peng, Zhou & Li, **stVCR: spatiotemporal dynamics of single cells**, Nature Methods 23, 542–553 (2026), DOI `10.1038/s41592-026-03010-3`.
   - Capability extracted: reconstruct continuous migration/growth dynamics from destructive snapshots using dynamic unbalanced optimal transport and alignment.
   - GSL implication: context-to-context observations can belong to one latent transport process without being identical in the raw observation/source-score coordinates.

4. Karchev, Trotta & Jimenez, **CIGaRS I: combined simulation-based inference from type Ia supernovae and host photometry**, Nature Astronomy 10, 1057–1072 (2026), DOI `10.1038/s41550-026-02842-5`.
   - Capability extracted: use a unified physics-based forward simulator and simulation-based inference to disentangle intrinsic and extrinsic latent factors instead of applying separate empirical corrections.
   - GSL implication: source is a global latent factor; transport is a context-specific extrinsic latent factor. They should be inferred jointly/conditionally, not conflated into a requirement that marginalized source rankings remain identical across contexts.

5. Peng et al., **WFR-FM: Simulation-Free Dynamic Unbalanced Optimal Transport**, ICLR 2026.
   - Capability extracted: represent dynamics with both displacement and mass growth/decay rather than displacement alone.
   - GSL implication: plume transport contains both advection/turning and dilution/intermittency; a future transport latent should permit both kinds of dynamics.

## Core physical correction

The invariant object is the physical source `s`.

The transport state `z_c` is allowed to change with context `c`:

`p(y_1,...,y_C | s) = product_c integral p(y_c | s,z_c) p(z_c | context_c) dz_c`.

V4/V5 instead approximately required a common best hard source component after transport marginalization. That is stronger than source invariance and can be false even when the same source generated all observations.

V6 must therefore validate a GLOBAL source posterior by held-out predictive transfer across contexts, without first requiring exact hard-component identity.

## V6-A — continuous source-transfer falsification

Use only the already materialized truth-blind NPZ files:

`/home/zyc/V4_TRUTHBLIND_COVERAGE_20260828_R1/contexts`

For each context `c`, scoring members produce coherent per-source log evidence

`E_c(s) = logmeanexp_m sum_j ell_cjm(s)`.

For each held-out context `c`, construct the training posterior

`q_-c(s) proportional q0(s) exp(sum_{d != c} E_d(s))`.

Held-out model predictive score:

`A_c = log sum_s q_-c(s) exp(E_c(s))`.

Geometry-prior source-mixture score:

`B_c = log sum_s q0(s) exp(E_c(s))`.

Source-transfer gain:

`G_transfer,c = A_c - B_c`.

Absolute source-independent score remains a Jeffreys-Beta prequential model fitted only on TRAINING stop outcomes; held-out context observations are never used to fit it.

The diagnostic asks two different questions:

1. Does source evidence learned from other contexts improve prediction of the held-out context over the geometry-prior source mixture?
2. Does the transport/source family beat a source-independent observation model at all?

No hard component is used in V6-A.

### V6-A interpretation

If at least 20/30 development runs have:

- no negative held-out source-transfer contradiction;
- at least two strictly positive held-out source-transfer gains;
- all held-out absolute gains positive;

then hard component identity is a primary blocker candidate. Do not immediately implement C++; first freeze a component-free runtime posterior and run a separate development-truth source-validity replay.

If fewer than 20/30 runs satisfy continuous predictive transfer, the V5 failure is not explained by component fragmentation alone. Proceed to V6-B.

The number 20/30 is not fitted to V6-A outcomes. It is inherited from the already frozen downstream requirement that at least 20/30 development pairs improve; a method that cannot even transfer source evidence in 20 runs has inadequate pre-C++ actionability for that endpoint.

## V6-B — within-stop dynamic transport evidence

V6-B is only entered if V6-A shows that continuous frequency-only evidence still fails.

The current V4/V5 materialization destroys event order by collapsing eight block outcomes at one physical stop into

`r_j = mean(block_hit_j)`.

That makes sequences such as `00001111`, `11110000` and highly alternating tapes partially or completely indistinguishable whenever their means agree.

The frozen CTT V13 binary record already contains a full `occupancyWords[T,words_per_step]` time series with `T=200`, plus first-hit bins. The historical action log contains the eight ordered completed-block HIT/NOTHING outcomes and block-average gas values.

V6-B must retain these dynamics rather than inventing another scalar feature.

Minimum reference observation model:

- observed stop: ordered eight-block hit tape;
- predicted source/member/stop: full CTT occupancy tape;
- derive a phase-insensitive, Jeffreys-smoothed transition model from the predicted tape;
- score the ordered observed tape with the transition likelihood;
- keep source `s` global but marginalize transport member independently per context;
- validate the resulting GLOBAL source posterior with the same context-held-out source-transfer and absolute-null tests as V6-A.

The exact mapping between one CTT recorded step and one PMFS measurement-block interval must be derived from frozen simulator timing/provenance. It must not be performance-tuned. If the mapping is not identifiable from provenance, report that and use a timing-invariant transition statistic; do not guess a dilation.

### Why this is not a Gate rescue

V6-B changes the observation representation. It recovers information currently discarded by `8 blocks -> one fraction`.

It does not lower Jeffreys/null requirements, member count, truth exclusion, or downstream performance criteria.

## V6-C — fixed transport family rejection and factorized simulation inference

If V6-B still fails source-validity across H02/H03, STOP modifying the same eight-member CTT family.

Then the scientific conclusion is that the approximation family lacks the transport degrees of freedom needed by the Houses.

The next method is a physics-factorized simulation-inference model inspired by CIGaRS:

- global latent: source position `s`;
- context latent: transport state `z_c`;
- sensor latent/noise state `n_c` when identifiable;
- observations: ordered gas blocks + pose + measured/estimated wind + geometry;
- forward data: randomized GADEN simulations spanning source and transport variation;
- inference: conditional neural ratio/posterior estimation of the global source after marginalizing context-specific transport.

A preferred transport latent should represent both displacement/advection and mass/dilution, following the physical separation emphasized by WFR-FM. It must be trained/frozen on simulator-known factors, not inferred from localization error.

This is a major method change, not V6-B threshold tuning.

## Development-truth source-validity gate

Truth is forbidden in V6-A/V6-B decision construction. After a candidate observation model and all formulas are frozen, development truth may be opened once for source-validity evaluation on seeds 0..9.

Required offline replay report must compare the frozen candidate posterior against Classic PMFS on the SAME archived OFF observations and report:

- expected-location error per run;
- pooled error change;
- improved-run count;
- House-level pooled changes;
- true-source/nearest-carrier rank or posterior mass diagnostics.

No parameter may be changed after this truth report. A failure requires a new method version, not retuning V6 on seeds 0..9.

Seeds 10..19 remain untouched for later fresh confirmation after a closed-loop development GO.

## Current authorization

`V5_ACTIVE_PROBE_CPP = HOLD`

`V6_A_TRUTHBLIND_CONTINUOUS_DIAGNOSTIC = AUTHORIZED`

`V6_B_DYNAMIC_TRACE_MATERIALIZATION = CONDITIONAL_ON_V6_A_FAIL`

`V6_C_GADEN_FACTORIZED_SBI = CONDITIONAL_ON_V6_B_SOURCE_VALIDITY_FAIL`

`60_ARM_MATRIX = NOT_AUTHORIZED`
