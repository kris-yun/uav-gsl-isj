# TNQC V3 final-leaf freeze: quotient theory, claim boundary, and 300-s gate
Date: 2026-09-21

Code freeze for the method/evaluator corrections below:
`3024ff349c37105aee1816f6648db3e81c178202`

This document supersedes any earlier wording that (a) treats the archived
240-s `gas_ppm` screen as direct validation of the online TNQC variable,
(b) lets subdivided quadtree ancestors influence the candidate-bank gate, or
(c) states that TNQC is exactly invariant to arbitrary physical sensor or
release-rate changes without an explicit observation-model assumption.

The authoritative status remains:

**MECHANISM POSITIVE / ONLINE LOGIT-HIT 300-S LOCALIZATION GATE PENDING /
CLOSED LOOP HOLD.**

---

## 1. Exact object on which online TNQC acts

Online TNQC does not operate directly on raw gas concentration.

For one PMFS source update let the supported measured field be

[
x_i = operatorname{logit}(p_i),
]

where (p_i) is the accumulated PMFS measured hit probability at free grid
cell (i). Let the candidate PMFS transport simulation for source hypothesis
(s) produce hit probability (hat p_i(s)), and define

[
y_{s,i} = operatorname{logit}(hat p_i(s)).
]

The positive weight (w_i) is the native PMFS confidence for that measured
cell. Cells with non-positive confidence or non-finite values are excluded.
The current implementation requires at least four supported cells.

This distinction is essential. The archived 240-s mechanism probe constructs
a field from spatially binned `gas_ppm`; it demonstrates that VGR contains
a robust source-dependent spatial pattern, but it is not the same random
variable as (x_i) above.

---

## 2. Main innovation as a quotient canonicalization

Consider the positive-affine nuisance group

[
G = {(a,b): a>0,; binmathbb R}
]

acting on a non-constant supported field by

[
(a,b)cdot x = ax+bmathbf 1.
]

Define the weighted mean and centered norm

[
mu_w(x)=rac{sum_iw_ix_i}{sum_iw_i},
qquad
|x|_w^2=sum_iw_ix_i^2,
]

and the canonical representative

[
pi_w(x)=
rac{x-mu_w(x)mathbf 1}
{|x-mu_w(x)mathbf 1|_w}.
]

For every (a>0) and (binmathbb R),

[
pi_w(ax+bmathbf 1)=pi_w(x).
]

For two non-degenerate fields, equality of canonical representatives is also
complete for this group action:

[
pi_w(x)=pi_w(y)
quadLongleftrightarrowquad
y=ax+bmathbf 1
	ext{ for some }a>0,binmathbb R.
]

Thus (pi_w) is not merely a normalization heuristic: on the supported
non-degenerate domain it selects a representation of the positive-affine
orbit/equivalence class.

The TNQC continuous score is the weighted inner product in the canonical
space,

[
q_{m aff}(x,y_s)
=
langle pi_w(x),pi_w(y_s)angle_w
=
rac{sum_iw_i(x_i-mu_w(x))(y_{s,i}-mu_w(y_s))}
{sqrt{sum_iw_i(x_i-mu_w(x))^2}
 sqrt{sum_iw_i(y_{s,i}-mu_w(y_s))^2}}.
]

An equivalent chordal quotient distance is

[
d_Q^2([x],[y_s])=2,[1-q_{m aff}(x,y_s)].
]

The paper-level idea is therefore:

> perform source comparison after projecting the measured and
> transport-predicted spatial hit fields onto the quotient by nuisance
> amplitude/background coordinates.

This is the main scientific line. The novelty claim is not “Pearson
correlation is new”; the contribution is the explicit nuisance-orbit
formulation, its integration with PMFS transport-conditioned source
hypotheses, and source inference in the resulting quotient representation.

---

## 3. Exact invariance claim — and what must not be claimed

The exact theorem above is about the online variables (x_i) and (y_{s,i}):
positive-affine transformations **in hit-logit space** are removed exactly.

PMFS constructs the measured hit map by thresholding concentration
(`concentration > thresholdGas`) and then applying its spatial/Bayesian hit
filter. Therefore an arbitrary raw-concentration transformation

[
c' = ac+b
]

does not, without additional assumptions, imply

[
operatorname{logit}p'(H_i)
=
alpha,operatorname{logit}p(H_i)+eta.
]

Accordingly, V3 must not make the unqualified statement that it exactly
removes arbitrary physical release-rate changes, arbitrary background gas, or
arbitrary sensor calibration curves.

Allowed wording:

- exact positive-affine nuisance invariance of the supported PMFS hit-logit
  representation;
- empirical robustness of the archived concentration-space representation to
  the source-blind scale/background interventions actually tested;
- a hypothesis that some physical/calibration nuisance is compressed into
  approximately affine coordinates by the PMFS representation, to be tested
  rather than assumed.

---

## 4. Auxiliary A: local spatial-order corroboration

For fixed spatially adjacent supported grid-cell pairs (E),

[
q_{m ord}(x,y_s)=
rac{sum_{(i,j)in E}min(w_i,w_j)
,operatorname{sgn}(x_i-x_j)
,operatorname{sgn}(y_{s,i}-y_{s,j})}
{sum_{(i,j)in E}min(w_i,w_j)},
]

ignoring ties.

This channel is invariant to strictly increasing pointwise transforms, but
global/rank-based calibration invariance is not claimed as the TNQC novelty.
A 2026 GSL method already uses concentration measurement ranking for
calibration-free source localization. TNQC therefore uses local order only as
a corroboration/abstention signal for the continuous quotient channel.

---

## 5. Final-leaf candidate-bank gate

### 5.1 Correct hypothesis set

Let (mathcal B_u^{m leaf}) be the PMFS candidates that, after native
quadtree refinement finishes at source update (u),

1. are free-space candidates, and
2. remain active leaves of the final partition.

A candidate evaluated at a coarse level and later subdivided is search
history, not a terminal source hypothesis. It must not affect the shared gate.

This is a correction to V2. The old implementation computed concordance over
all evaluated candidates, allowing subdivided ancestors to change the gate
strength applied to terminal leaves.

V3 computes the gate only on (mathcal B_u^{m leaf}). The Python 300-s
replay derives the identical set as the unique candidate IDs owning cells in
the reconstructed final partition.

### 5.2 Ranking-safe corroboration

For valid final leaves write

[
a_i=q_{m aff}(s_i),qquad o_i=q_{m ord}(s_i).
]

Over non-tied valid leaf pairs,

[
C_u=
rac{1}{|mathcal P_u|}
sum_{(i,j)inmathcal P_u}
operatorname{sgn}(a_i-a_j)
operatorname{sgn}(o_i-o_j).
]

Then

[
g_u=max(0,C_u),
qquad
e_i=g_u a_i.
]

Because the same (g_uge0) multiplies every terminal hypothesis,

[
e_i-e_j=g_u(a_i-a_j).
]

Hence the auxiliary order channel can attenuate or abstain but cannot reverse
the main quotient ordering.

The evaluated-ancestor version of (C_u) is still recorded by the replay as a
source-blind diagnostic. It cannot control evidence or the GO decision.

---

## 6. Exponential tilt: correct statistical interpretation

The frozen fused score is

[
L_{m fused}(s_i)
=
L_{m PMFS}(s_i)exp(e_i).
]

This has the mathematical form of an exponential/Gibbs tilt. If one defines a
quotient loss

[
ell_Q(s_i;x)=-g_u q_{m aff}(x,y_{s_i}),
]

then the multiplier is (exp[-ell_Q]).

This is compatible with the broader generalized-Bayes idea of updating with
an exponentiated loss when a conventional likelihood is not the chosen
information link. The canonical reference is:

P. G. Bissiri, C. C. Holmes, S. G. Walker,
“A General Framework for Updating Belief Distributions,” JRSS-B, 2016.
https://doi.org/10.1111/rssb.12158

However, V3 does **not** claim that (L_{m PMFS}) and (exp(e_i)) are two
conditionally independent physical likelihoods. Both are constructed from
the same accumulated PMFS observation map. In the paper, call the operation a
bounded quotient-space exponential tilt / generalized-loss correction, not an
independent-likelihood product.

The evidence remains bounded:

[
e_iin[-1,1].
]

Do not multiply it by raw support count or (sqrt{N_{m eff}}), because the
PMFS cells are spatially propagated/smoothed and are not iid replications.

---

## 7. What the 240-s evidence actually establishes

The archived project-data screens remain useful, but their role is now
explicitly bounded.

From
`evidence/TNQC_VGR_240S_SPATIAL_MECHANISM_20260921.json` and
`evidence/TNQC_VGR_DISTRIBUTED_SUPPORT_AUDIT_20260921.json`:

- the fixed routes are identical across controlled source/transport episodes;
- the spatially binned concentration representation preserves two-source
  identity at the 240-s endpoint;
- the signal is not confined to a near-source patch;
- disjoint spatial subsets usually recover the same ordering;
- source-blind scale/background interventions strongly separate affine
  canonicalization from raw amplitude on that controlled asset;
- identifiability is late rather than early.

These results support the physical motivation for a quotient representation.
They do not establish the online hit-logit TNQC localization gain.

The first experiment that directly tests the online representation against
the project endpoint is the frozen 300-s House fixed-trajectory replay.

---

## 8. Authoritative 300-s V3 gate

Run on the VGR VM:

```bash
python3 reference/test_tnqc_vgr_fixed_trajectory_replay.py
bash reference/run_tnqc_vgr_offline_gate_20260920.sh
```

Cases:

- House01 seed0/1
- House02 seed0/1
- House03 seed0/1

Budget: 300 simulation seconds.

Primary endpoint:

[
left|
operatorname{ExpectedValue}(P_{300},0.05)-s^*
ight|_2.
]

### Mandatory integrity audits for every case

The case is invalid unless all of the following pass before its TNQC gain is
used:

1. **native posterior reconstruction**
   - max absolute cell discrepancy <= (5	imes10^{-6});
   - L1 discrepancy <= (5	imes10^{-4}).

2. **native C++ endpoint anchor**
   - Python's top-5% native error reconstructed from the exported terminal
     posterior must agree with the C++ `RESULT IS: Error=` endpoint;
   - because the C++ log prints two decimals, the pre-registered absolute
     tolerance is 0.011 m.

3. **final-leaf gate scope**
   - `candidate_gate_scope` must equal
     `final_partition_leaf_candidates_only`.

The replay also records:

- total evaluated candidate count;
- final active leaf candidate count;
- final-leaf gate strength/concordance;
- the all-evaluated-candidate gate as an audit only;
- budget-to-last-source-update gap.

### Frozen development GO rule

Only if all six integrity audits pass:

- pooled final top-5% error reduction >= 10%;
- at least 4/6 paired cases improve;
- no pair degrades by more than 25%;
- no false-confident collapse.

No TNQC equation, gate, weight, threshold, support rule, or candidate scope may
be changed after viewing the six House truth outcomes. A change creates a new
method version and requires a new pre-registration before re-testing.

If the result is HOLD, report it and stop.
If the result is GO, proceed to OFF-vs-SHADOW determinism before any fused
planner-coupled closed loop.

---

## 9. Current literature lineage and novelty boundary

### Canonicalization / quotient-space line

Behrooz Tahmasebi and Stefanie Jegelka,
“Generalization Bounds for Canonicalization: A Comparative Study with Group
Averaging,” ICLR 2025.
https://proceedings.iclr.cc/paper_files/paper/2025/hash/b36dc39b319ba6ba2a0fd7601951efb4-Abstract-Conference.html

Relevant idea: project inputs to a reduced/canonical space before ordinary
inference, rather than learning every nuisance-group coordinate separately.

Zakhar Shumaylov et al.,
“Lie Algebra Canonicalization: Equivariant Neural Operators under Arbitrary
Lie Groups,” ICLR 2025.
https://openreview.net/pdf?id=7PLpiVdnUC

Relevant idea: continuous/non-compact symmetry structure can be handled by
canonicalizing inputs before an otherwise ordinary model.

Ya-Wei Eileen Lin and Ron Levie,
“Adaptive Canonicalization with Application to Invariant Anisotropic
Geometric Networks,” ICLR 2026.
https://proceedings.iclr.cc/paper_files/paper/2026/hash/2774a3b52d436b5930da660dd2b32b3a-Abstract-Conference.html

Relevant future direction: if fixed affine canonicalization proves too rigid,
a transport/input-conditioned canonicalizer is scientifically motivated, but
it is not part of frozen V3.

### GSL novelty collision

Wanting Jin, Agatha Duranceau, İzzet Kağan Erünsal, Alcherio Martinoli,
“Calibration-Free Gas Source Localization with Mobile Robots: Source Term
Estimation Based on Concentration Measurement Ranking,” 2026.
https://arxiv.org/abs/2605.13208

Therefore do not claim concentration ranking, rank invariance, monotone
invariance, or generic calibration-free GSL as TNQC's main novelty.

### Frozen novelty statement

The defensible TNQC novelty is the combined construction:

1. explicit positive-affine nuisance quotient of PMFS spatial hit-logit
   fields;
2. continuous quotient-field comparison against transport-conditioned PMFS
   candidate simulations;
3. local spatial-order corroboration used only through a shared
   ranking-preserving abstention gate;
4. gate computation on the terminal PMFS hypothesis partition rather than
   quadtree search history;
5. bounded quotient-space exponential tilt with exact OFF/SHADOW and
   fixed-trajectory falsification contracts.

---

## 10. Auxiliary-B direction remains unactivated

The distributed-support audit suggests a second auxiliary mechanism:
source-blind disjoint spatial folds can be used to require independent
subregions to agree on candidate ordering.

That is scientifically promising, but the evidence currently exists in the
240-s concentration representation, not yet in the online PMFS hit-logit
candidate bank. It is therefore **not activated in V3**.

Do not add this gate after seeing the authoritative V3 300-s outcomes.
If it is developed later, it must first be tested source-blind on the online
representation and frozen as a new version before a new House endpoint batch.

---

## 11. Frozen decision

The previous broad statement “TNQC is already localization-positive” is not
supported.

The current defensible statement is:

**The quotient/canonicalization mechanism has strong project-data motivation
and corrected implementation integrity. The online PMFS hit-logit
representation now has a pre-registered, self-auditing 300-s localization
test. That test has not yet been executed in this environment.**

Closed loop remains HOLD until the V3 fixed-trajectory gate returns an
explicit GO.
