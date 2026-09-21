# 01 — Core Research Idea

This directory is the conceptual entry point of the project.

The project is not organized around “adding another module” to PMFS. The
research strategy is to identify a **large transferable scientific idea**
from recent adjacent fields, map that idea onto the physical/statistical
structure of gas-source localization, falsify it cheaply on existing VGR
data, and only then promote it into an online method.

## 1. The central doctrine

A publishable main innovation should satisfy all of the following:

1. **It has a scientific thesis larger than one engineering trick.**
   Examples of the right level are causality, symmetry/canonicalization,
   quotient-space inference, world-model reasoning, uncertainty
   factorization, or another similarly general organizing principle.

2. **The thesis maps to a real nuisance or structure in gas transport.**
   We do not import a fashionable method by name. We ask what transformation,
   latent factor, causal direction, invariance, transport uncertainty, or
   identifiability structure exists in the gas-source problem.

3. **The main module changes the representation or inference principle.**
   The main innovation must explain the paper. Auxiliary modules are allowed,
   but they must support the main idea rather than hide a weak main idea.

4. **The first evidence is data-driven and source-blind.**
   Candidate modules are screened on existing project data before expensive
   closed-loop experiments. Source truth is reserved for evaluation, not for
   tuning the inference rule.

5. **A candidate is rejected early if the mechanism is not visible.**
   Negative offline evidence is useful. We prefer killing a weak idea before
   spending time on ROS/GADEN closed-loop runs.

6. **The method is frozen before the authoritative endpoint is inspected.**
   Once equations, thresholds, candidate scope and endpoint rules are frozen,
   the 300-s House result is a test, not a tuning signal.

## 2. Discovery loop

The working loop is:

**recent cross-domain idea**
→ **structural match to GSL**
→ **minimal mathematical formulation**
→ **source-blind offline probe**
→ **falsification / robustness stress**
→ **keep or reject**
→ **secondary innovation only after the main signal exists**
→ **freeze**
→ **300-s localization gate**
→ **closed loop only after offline GO**

This is deliberately different from starting with a neural-network block,
adding losses, and then searching for a story afterward.

## 3. How candidate ideas are generated

The search should preferentially examine recent top-tier work (especially
2025–2026) outside conventional gas-source localization and ask whether its
scientific mechanism has not yet been exploited in GSL.

Useful neighboring domains include, but are not limited to:

- symmetry, invariance and canonicalization;
- inverse problems and generalized Bayes;
- causal representation and intervention;
- operator learning and transport models;
- uncertainty decomposition and robust inference;
- geometric learning;
- sequential decision making;
- scientific machine learning;
- system identification;
- information geometry;
- distribution shift and nuisance-factor elimination.

The transfer criterion is **structural compatibility**, not superficial
similarity of terminology.

## 4. Mapping a “big idea” into GSL

Before writing code, write down four objects:

### A. Scientific object

What is the thing being inferred?

For this project the final object is source location under turbulent,
partially observed transport.

### B. Nuisance object

What changes while source identity/location should remain meaningful?

Examples include amplitude/background coordinates, sensor calibration,
transport realization, local sampling density, candidate-partition geometry,
or other nuisance factors.

### C. Invariant / quotient / causal object

What information should survive the nuisance?

This may be a quotient representation, a conditional statistic, a
transport-consistent ordering, a causal direction, a normalized spatial
shape, or another physically motivated invariant.

### D. Observable test

What result in the already available data would falsify the idea before a
closed-loop run?

If this cannot be stated clearly, the idea is not mature enough to become the
main module.

## 5. Evidence hierarchy

We separate evidence into levels.

### Level 0 — algebraic correctness

The proposed score or transformation must satisfy its claimed mathematical
property exactly in synthetic/unit tests.

### Level 1 — representation/mechanism evidence

Use project data to test whether the proposed invariant retains source
information and suppresses the intended nuisance.

This level does **not** establish localization improvement.

### Level 2 — online-variable fixed-trajectory evidence

The exact representation used by the online implementation is replayed on a
frozen native PMFS trajectory/candidate bank.

This is the first level that can support a claim about the proposed inference
channel itself.

### Level 3 — terminal localization endpoint

Evaluate the original project endpoint at the full 300-s budget:
PMFS top-5% probability-weighted expected-location error.

### Level 4 — closed-loop effect

Only after Level 3 GO, allow the new posterior/evidence to affect later robot
motion and test OFF / SHADOW / FUSED behavior.

## 6. Main innovation + auxiliary innovation rule

The intended paper architecture is:

- **one main innovation** that carries the scientific thesis;
- **two auxiliary innovations at most**, each solving a clearly identified
  failure mode of the main mechanism.

An auxiliary module is acceptable only if it is structurally subordinate.

Good auxiliary behavior:

- corroborate;
- attenuate;
- abstain;
- enforce consistency;
- preserve the main ranking/order;
- improve reliability without changing the paper's scientific thesis.

Bad auxiliary behavior:

- independently override the main score;
- introduce many fitted coefficients;
- rescue a main module that has no positive signal;
- create an engineering patch stack with no single explanatory principle.

## 7. Current instantiation: TNQC

The current research-cycle candidate is **Transport-Nuisance Quotient
Canonicalization (TNQC)**.

Its main thesis is:

> Compare measured and transport-predicted PMFS spatial fields after
> canonicalizing nuisance coordinates, so source inference is performed in a
> representation closer to the quotient by nuisance transformations rather
> than in raw amplitude coordinates.

The online V5 implementation currently uses:

- confidence-weighted centered cosine in PMFS hit-logit space as the main
  positive-affine quotient score;
- local spatial order only as an auxiliary corroboration channel;
- terminal active PMFS leaves as the hypothesis bank;
- free-cell hypothesis measure to avoid quadtree-density artifacts;
- support-coverage attenuation so sparse auxiliary support cannot masquerade
  as full confidence;
- a bounded shared gate that cannot reverse the main affine candidate order;
- an exponential/Gibbs-style evidence tilt rather than a claim of an
  independent second physical likelihood.

The key theoretical boundary is equally important:

**exact invariance is claimed for the defined supported hit-logit
representation, not automatically for arbitrary physical sensor gain,
background gas, or release-rate transformations in raw concentration space.**

## 8. Why the 240-s and 300-s tests are different

The archived 240-s VGR screen works on spatially binned `gas_ppm`. It is
useful mechanism evidence: it shows that a nuisance-reduced spatial
representation can retain source-dependent structure.

The online TNQC implementation acts on PMFS measured/simulated
hit-probability logits.

Therefore:

- 240-s concentration evidence = motivation/mechanism evidence;
- 300-s hit-logit fixed-trajectory replay = authoritative method feasibility
  test.

These must never be conflated.

## 9. Freeze discipline

The current TNQC V5 method was frozen before the authoritative six-case
300-s House truth was run.

Rules after freeze:

- do not change equations after seeing the six-case result;
- do not change thresholds after seeing the result;
- do not alter candidate-bank scope after seeing the result;
- do not replace the historical endpoint with a more favorable metric;
- HOLD is a scientific result, not permission to tune V5;
- an infrastructure failure is not HOLD and not GO.

The full six-case 300-s TNQC batch has **not yet produced a scientific verdict**. A repaired House01/seed0 execution has now passed the terminal endpoint, context-bank reconstruction and linked-native endpoint audits; its TNQC fused endpoint was essentially neutral/slightly worse than native. This single case is pipeline validation and one observed case, not the six-case GO/HOLD verdict.

## 10. What counts as success

A useful innovation is not merely one that gives a lower number once.

The project prefers a method that is:

- theoretically explicit;
- physically interpretable;
- lightweight enough for online PMFS;
- robust to nuisance interventions;
- reproducible;
- auditable;
- clearly distinct from nearby GSL literature;
- positive on the original localization endpoint;
- simple enough that an expert can understand why it works.

That is the core research philosophy of this repository.


## Teacher-review material

The 2026-09-21 endpoint-contract and next-generation closed-loop review is preserved under:

`teacher_reviews/20260921_endpoint_and_closed_loop/`

It is research-review material, not part of the frozen TNQC V5 equations.
