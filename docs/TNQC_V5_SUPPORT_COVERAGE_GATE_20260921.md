# TNQC V5 support-coverage-aware partition-measure gate
Date: 2026-09-21

This is the authoritative TNQC **method/gate** definition before the first
VGR/GADEN House01/02/03 x seed0/1 full-300-s truth outcome is inspected.

For the authoritative 300-s endpoint/build implementation, read
`docs/TNQC_V5_LINKED_NATIVE_EXECUTION_FREEZE_20260921.md`. That later
pre-truth execution correction changes only evaluation/build semantics; the
V5 method below is unchanged.

V5 keeps the V3 quotient/claim boundary and the V4 terminal-leaf
partition measure. It corrects one remaining normalization problem in the
local-order corroboration gate.

No House 300-s localization outcome was used to design this correction.

## 1. Why V4 could still become overconfident

V4 correctly:

- removes subdivided quadtree ancestors;
- uses only terminal active free leaves;
- weights each terminal leaf by the number of free source cells it represents.

However, V4 normalized concordance only over candidate pairs for which the
local-order channel was informative. A pair was dropped from the denominator
when either candidate had too little local-edge support or when local order
was tied.

That creates a failure mode: if the affine quotient orders 1000 weighted
candidate pairs but local order is informative on only 5 of them, and those
5 agree, conditional concordance is 1.0. Treating that as gate strength 1.0
would convert 0.5% auxiliary coverage into 100% corroboration.

For an abstention channel, absence of local-order information must attenuate
the gate rather than disappear from its normalization.

## 2. V5 definition

For terminal active free leaves, let:

- `a_i = q_aff(s_i)`;
- `o_i = q_ord(s_i)`;
- `m_i = free-cell multiplicity represented by terminal leaf i`.

Define the **reference pair measure** over every pair whose main affine
quotient has a non-tied ordering:

`W_main = sum_(i<j, a_i != a_j) m_i*m_j`.

Define the **informative local-order subset** as pairs for which:

- both candidates have the frozen minimum local-edge support; and
- `o_i != o_j`.

Its pair measure is:

`W_info = sum_(informative pairs) m_i*m_j`.

The signed informative mass is:

`S = sum_(informative pairs)
       m_i*m_j*sign(a_i-a_j)*sign(o_i-o_j)`.

For diagnostics, define:

`C_cond = S / W_info` when `W_info > 0`, otherwise 0.

`rho = W_info / W_main`.

The actual shared V5 gate is:

`g = max(0, S / W_main)`.

Equivalently, when `W_info > 0`:

`g = max(0, C_cond) * rho`.

The TNQC evidence remains:

`e_i = g * a_i`.

A local-order tie or insufficient local-order support therefore contributes
zero signed corroboration **but remains in the reference affine-order
measure**.

## 3. Ranking-safety remains exact

Because one common scalar `g >= 0` multiplies every affine quotient score:

`e_i - e_j = g*(a_i-a_j)`.

Thus the auxiliary channel can:

- release the affine quotient at full strength;
- attenuate it;
- abstain completely.

It still cannot reverse any affine candidate ordering.

## 4. No new hyperparameter

V5 introduces no fitted coefficient or support-coverage threshold.

Coverage `rho` is determined entirely by:

- the frozen PMFS observation support;
- the frozen adjacent-cell edge definition;
- the native terminal quadtree partition;
- geometry-only free-cell multiplicity.

It does not use source truth, posterior rank, native likelihood magnitude,
TNQC score magnitude, House outcome, or a post-hoc threshold.

## 5. Cell-expansion equivalence is preserved

V4 established that pair weight `m_i*m_j` is exactly equivalent to
expanding terminal leaf `i` into `m_i` identical cell-level source
hypotheses.

V5 preserves this equivalence for both measures:

- `W_main` equals the number/measure of non-tied affine-order pairs in the
  cell-expanded bank;
- `W_info` equals the corresponding informative local-order pair measure;
- `S` equals the cell-expanded signed informative mass.

Within-leaf duplicates tie in both channels and do not create artificial
cross-leaf ordering evidence.

Both C++ and Python tests lock this equivalence.

## 6. Explicit sparse-support counterexample

The standalone tests include three affine-ordered candidates. Only one of
the three candidate pairs has usable local-order information.

The expected V5 diagnostics are:

- reference pairs = 3;
- informative pairs = 1;
- informative coverage = 1/3;
- conditional concordance = 1;
- actual gate strength = 1/3.

This prevents sparse corroboration from renormalizing itself to full
strength.

## 7. Authoritative online/offline contract

Online C++:

- native PMFS alone performs quadtree refinement;
- only terminal active free leaves enter the gate;
- terminal leaf measure is represented free-cell count;
- all non-tied affine pairs enter reference pair mass;
- only supported, non-tied local-order pairs enter informative mass;
- `g=max(0,S/W_main)`;
- `e_i=g*q_aff_i`;
- fused score is `L_PMFS(s_i)*exp(e_i)`.

The 300-s fixed-trajectory Python replay mirrors the same contract.

Authoritative replay contract after the linked-native execution correction:

`TNQC_VGR_FIXED_TRAJECTORY_300S_REPLAY_V7_LINKED_NATIVE_ENDPOINT`

Authoritative aggregate contract:

`TNQC_VGR_FIXED_TRAJECTORY_300S_GATE_V6_LINKED_NATIVE_ENDPOINT`

Required gate scope:

`final_partition_leaf_candidates_free_cell_measure_support_coverage_weighted`

## 8. Integrity gates before any localization claim

Every House/seed replay is invalid unless:

1. native posterior reconstruction passes:
   - max absolute cell discrepancy <= 5e-6;
   - L1 discrepancy <= 5e-4;
2. the endpoint executable built with `gsl_actionserver_node` links
   `GSL_common`, directly calls
   `GSL::Utils::ExpectedValue(sourceProbability,0.05)`, and matches the
   native PMFS terminal result within 0.011 m;
3. the same linked-native endpoint binary evaluates the TNQC counterfactual;
4. the V5 gate-scope contract above is present.

Python and the standalone C++ clone remain diagnostics/tests only.

An integrity-invalid case writes diagnostics and the runner continues through
all six frozen cases. Execution/file failures still abort.

## 9. Frozen 300-s development decision

Only after all six cases are integrity-valid:

- pooled top-5% localization error reduction >= 10%;
- at least 4/6 paired cases improve;
- no pair degrades by more than 25%;
- no false-confident collapse.

No equation, gate normalization, support rule, partition measure, evidence
coefficient, House set, endpoint, or advancement threshold may be changed
after the six House truth outcomes are viewed. Any such change creates a new
method version and requires a new pre-registration before re-testing.

## 10. What remains auxiliary

The archived 240-s VGR screens operate on spatially binned `gas_ppm`, not
the online PMFS hit-logit field. They remain concentration-space physical
mechanism evidence only.

The distributed-support fold idea remains a future auxiliary direction and is
**not enabled in V5**. Enabling it after seeing the V5 300-s result would be
post-hoc.

## 11. Closed-loop boundary

The fixed-trajectory 300-s replay tests source inference on the native PMFS
trajectory. A later fused closed loop may additionally alter subsequent
motion through posterior/planner state.

Native within-update quadtree refinement remains driven by native PMFS.

Planner-coupled closed-loop testing remains forbidden until the V5 offline
aggregate returns `go_for_closed_loop=true`.

## 12. Status

**TNQC V5 METHOD FROZEN BEFORE 300-S TRUTH /
SUPPORT-COVERAGE + PARTITION-MEASURE + FINAL-LEAF GATE IMPLEMENTED /
LINKED-NATIVE C++ ENDPOINT + CLEAN CURRENT-SOURCE BUILD FROZEN /
VGR 300-S ONLINE HIT-LOGIT REPLAY PENDING /
CLOSED LOOP HOLD.**
