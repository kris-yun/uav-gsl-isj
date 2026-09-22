# CSL V1 — Transport-Contrastive Surrogate Likelihood

Date: 2026-09-22  
Branch: `research/contrastive-surrogate-likelihood-v1`  
Status: **GO FOR FROZEN-BANK OFFLINE SCREEN ONLY**

## 1. Main scientific thesis

The current project failure is not well described as “there is no source
signal”.

The controlled VGR concentration asset contains strong source identity, while
the authoritative TNQC 300-s hit-logit replay does not rank the true source
reliably.  This motivates a change in **inference semantics**:

> When the forward transport operator is only partially specified, source
> inference should be performed in a compatibility representation learned to
> preserve source identity across transport realizations, rather than by
> treating each simulator output as a literal likelihood and multiplying it
> recursively.

Working name:

**Transport-Contrastive Surrogate Likelihood (CSL).**

## 2. Remote-field source

Primary 2026 anchor:

- Basu et al., **Contrastive Diffusion Guidance for Spatial Inverse Problems**,
  ICLR 2026.

That work studies spatial inverse problems with partially specified,
non-smooth forward operators.  It replaces unstable direct likelihood
guidance with a contrastively learned compatibility embedding in which
matching observation-hypothesis pairs are pulled together and mismatches are
pushed apart.

Related 2026 blind-inverse line:

- Ye et al., **CL-DPS: A Contrastive Learning Approach to Blind Nonlinear
  Inverse Problem Solving via Diffusion Posterior Sampling**, ICLR 2026.

CSL does **not** import diffusion sampling.  The transferred principle is the
surrogate compatibility representation for a blind / misspecified forward
operator.

## 3. Why this is not TNQC, SBI, or active deconfounding V1

TNQC:
- analytically canonicalizes a chosen nuisance group;
- then scores measured and candidate fields directly;
- authoritative online hit-logit ranking was wrong in H01/H03 and unsupported
  at the true owner in H02.

CSL:
- does not assert that one analytic nuisance transform is sufficient;
- uses simulator transport randomization itself to define positive
  equivalence classes;
- learns/derives a representation in which the **same source across transport
  worlds** should remain close.

SBI:
- is not used as the paper thesis;
- V1 does not learn a posterior density or amortized parameter posterior.

Active deconfounding V1:
- selects a two-action pair and maximizes worst-world source separation;
- failed 0/6 because selected pairs remained no-hit ambiguous.

CSL V1 first asks a different necessary question:

> Does the **full feasible-action response manifold** contain a
> transport-invariant source identity at all?

If not, do not build a neural encoder or modify ROS.

## 4. Truth-blind positive and negative pairs

For one frozen case, let

- `s` be a native positive-measure source leaf;
- `theta` be a transport world;
- `a_1,...,a_A` be the already-frozen feasible actions;
- `p(s,theta,a)` be the frozen native Bernoulli hit response.

The response vector is

`r_{s,theta} = [p(s,theta,a_1), ..., p(s,theta,a_A)]`.

Positive pairs:
- same candidate source `s`;
- different design transport worlds.

Negative pairs:
- different candidate source IDs.

No evaluation source truth is required to create these pairs.

## 5. V1 linear contrastive proxy

Before any InfoNCE network is allowed, V1 tests the smallest possible
contrastive object.

For every Bernoulli response `p`, use its Hellinger coordinates

`phi(p) = [sqrt(p), sqrt(1-p)]`.

Over the 27 frozen design worlds:

1. compute a prototype for each candidate source;
2. compute pooled **within-source transport covariance**;
3. whiten that covariance;
4. keep source identity only insofar as it survives this transport
   contraction.

No weights are fit to source truth.

The eight grid-off worlds 27:35 are untouched held-out transport worlds.

## 6. Baselines and destructive control

Required comparison:

- **RAW** — raw Hellinger response geometry with source prototypes;
- **CSL-LINEAR** — within-source transport-covariance whitening;
- **SHUFFLED-POSITIVE** — independently shuffle source identity inside every
  training world before fitting the same whitening.

The shuffled control preserves each world's response distribution but destroys
the same-source-across-transport correspondence.

If CSL remains strong after this shuffle, the claimed contrastive mechanism is
not load-bearing.

## 7. Case-level frozen gate

Implemented in:

`research/contrastive_surrogate/screen.py`

For each of the six existing response banks, all four criteria must pass:

1. weighted held-out unique top-1 source retrieval gain over RAW >= 0.05;
2. weighted physical source-representative retrieval error reduction >= 10%;
3. minimum held-out-world weighted top-5 retrieval >= 0.90;
4. source-group shuffle decreases weighted top-1 by >= 0.20.

Source-leaf evaluation is weighted by represented physical source measure, not
raw quadtree leaf count.

Numerical covariance regularization is fixed in code before results:
relative eigenvalue floor `1e-6`, absolute floor `1e-10`.

## 8. Six-case promotion gate

Use the same six frozen development contexts:

- House01 seed0 / seed1
- House02 seed0 / seed1
- House03 seed0 / seed1

Aggregate promotion to the next offline stage requires:

- at least **5/6** cases pass the case-level gate;
- every House has at least one passing seed;
- pooled weighted top-1 gain >= 0.05;
- pooled weighted physical retrieval-error reduction >= 10%;
- no case loses more than 0.05 weighted top-1 versus RAW;
- pooled contrastive-vs-shuffled top-1 gap >= 0.20.

These thresholds are frozen before running CSL V1.

## 9. Reproduction on the VGR / evidence machine

Extract the already-frozen evidence archive.  Its packaged response tree is
under `responses/`.

Single case:

```bash
python research/contrastive_surrogate/screen.py \
  --design evidence/active_deconfounding_v1/pre_response/House01_seed0.json \
  --bank EXTRACTED_ARCHIVE/responses/House01_seed0 \
  --out /tmp/csl_v1/House01_seed0.json
```

Run all six and aggregate:

```bash
python research/contrastive_surrogate/run_six.py \
  --responses-root EXTRACTED_ARCHIVE/responses \
  --out-root /tmp/csl_v1
```

No new native forward calls are required.

## 10. Novelty boundary

Not claimed as new:

- contrastive learning;
- metric learning;
- simulator domain randomization;
- source prototypes;
- Hellinger geometry.

Targeted GSL novelty hypothesis:

**transport-randomized contrastive surrogate likelihood for mobile turbulent
gas-source localization, where candidate source identity is represented by
same-source response equivalence across forward-transport worlds rather than
literal PMFS likelihood multiplication.**

A targeted current search found contrastive methods for other localization
domains and visuo-olfactory representation, but no direct turbulent GSL
implementation of this source-by-transport compatibility construction.

This remains a novelty-screen result, not an exhaustive patent/literature
claim.

## 11. What a positive V1 result does and does not mean

Positive V1 means:
- the frozen native simulator contains a transport-invariant source manifold;
- the invariant structure is stronger than raw full-response geometry;
- the source grouping itself is load-bearing;
- it is scientifically justified to test a lightweight compatibility encoder
  on actual frozen observations.

Positive V1 does **not** mean:
- 300-s localization is improved;
- the native simulator is externally valid;
- all feasible actions can be observed online;
- ROS or closed loop is authorized.

The next stage, only after V1 GO, is actual frozen-observation compatibility
on the native 300-s trajectory.  Closed loop remains forbidden until that
stage improves the original PMFS endpoint.
