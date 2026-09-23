# Distributional-forward mother idea: pre-audit and frozen H01 gate

Date: 2026-09-23
Status: ACTIVE MOTHER-IDEA SCREEN — NOT YET A MAIN INNOVATION

## Why this is a major PMFS-core replacement

PMFS is retained only as the outer probability-map / candidate-source / closed-loop scaffold. The old inner semantics — one deterministic time-averaged hit-probability field per source candidate, followed by cellwise agreement multiplication — is not protected.

The 2026 mother idea is distributional scientific computing for chaotic/stochastic PDEs: the scientifically relevant forward object is a conditional law over possible fields/trajectories, not a single conditional mean field. This is directly motivated by:

- Raonic et al., *Generative AI for efficient statistical computation of fluids*, Nature Communications 17, 9846 (2026), DOI 10.1038/s41467-026-76390-x.
- Park et al., *Generative Neural Operators through Diffusion Last Layer*, ICML 2026.
- Hu et al., *Wavelet Diffusion Neural Operator*, ICLR 2025.

For GSL, the proposed transfer is not “put a diffusion model on PMFS”. The hypothesis is stronger: source evidence should be computed from the candidate-conditioned distribution of stochastic plume observations along the measurement path. A learned diffusion/operator model would only be justified later if the distributional mechanism itself passes source-identity tests.

## Failure mechanism this targets

The accumulated evidence says that changing PMFS likelihood/scoring after the simulator has already compressed the plume to a single hitMap does not reliably restore truth-source identity. The candidate forward family can be sharp yet wrong, and endpoint improvements can be geometry shortcuts.

The concrete suspected information loss is therefore:

> source -> stochastic plume trajectory/distribution -> time-averaged per-cell hit probability -> independent cell product

The proposed core replacement attacks the first compression arrow. It asks whether source identity exists in the stochastic joint/sequence law even when the averaged hitMap is insufficient.

## Prerequisite check on authoritative R2 banks

Before testing high-order information, we checked a weaker prerequisite: whether the source-conditioned *mean* hit fields are at least reproducible enough across independent seeds to preserve the same source neighborhood. This check is NOT distributional evidence and must not be cited as proof of the mother idea.

Using source-blind pairwise field distances between seed0 and seed1 candidate banks at the final <=300 s update, the truth-nearest candidate in one seed retrieves the truth-nearest candidate in the other seed by per-cell Bernoulli Hellinger distance at ranks:

- House01: 4/148 and 2/152
- House02: 1/144 and 2/148
- House03: 1/199 and 1/197

This passes only a prerequisite: source-conditioned forward fields are not pure random noise across seeds. It does NOT show that high-order distributional information matches real observations.

Machine-readable table: `GENCFD_DISTRIBUTIONAL_FORWARD_PREAUDIT_R2.csv`.

## Frozen first knife: H01 path-distribution joint-structure gate

No neural network is trained. We use the frozen standalone candidate replay for H01_R2026092201 (`occupied_cells.csv.zst`, 200 internal plume steps) and the accepted real sensor trace from the same run.

Observation window is frozen as the last 200 sensor samples ending at source update 1 (nominally 40 s at 0.2 s/sample). The online gas threshold is frozen to the PMFS default `th_gas_present = 0.1 ppm`; the script records the actual observed hit count.

For each terminal source candidate:

1. Reconstruct a 200-step binary occupancy process only on grid cells visited by the real robot during the frozen window.
2. Treat global cyclic plume phase as unknown. For each of the 200 phase offsets, sample the candidate's predicted hit sequence along the real robot path.
3. Compress each phase realization into 10 consecutive 20-sample hit-count blocks. This gives an empirical candidate-conditioned distribution over block hit counts.
4. **Primary frozen score:** sum the empirical CRPS of the 10 block-count distributions against the actually observed block counts. Lower is better. CRPS is a proper scoring rule and requires no fitted coefficient.
5. **Secondary diagnostic only:** compute the exact multivariate Energy Score for the unshuffled candidate ensemble. It is reported for interpretation but does not enter the advancement gate.

The primary score is blockwise CRPS rather than a 10-D Energy Score because the destructive-null test requires 500 source-wide repetitions; CRPS admits an exact finite-support computation from count histograms without an O(T^2) pairwise-distance loop. This implementation choice is frozen before any joint-structure result is viewed.

### Destructive null

For each candidate and each visited grid cell, independently apply a random circular shift to that cell's 200-step occupancy trace before constructing the phase ensemble. This preserves every candidate x cell final occupancy count and every cell's own circular autocorrelation pattern while destroying cross-cell plume-phase synchronization / joint spatial-temporal organization.

Run 500 null repetitions with frozen RNG seed 20260923.

### Predeclared advancement gate

The mother mechanism advances beyond H01 only if BOTH are true:

1. actual joint-distribution CRPS ranks the truth-nearest terminal source candidate better than the already observed H01 static low-occupancy baseline rank 20.5/121;
2. <=5% of joint-destruction null repetitions give the truth candidate a CRPS rank as good as or better than the actual joint score.

Truth coordinates are used only after scores are frozen, for evaluation.

A failure is a mechanism NO-GO for “high-order joint plume structure rescues H01 beyond the mean hitMap” and must not be rescued by tuning block size, threshold, phase weighting, or score coefficients on H01.
