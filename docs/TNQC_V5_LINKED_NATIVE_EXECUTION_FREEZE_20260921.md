# TNQC V5 linked-native execution freeze
Date: 2026-09-21

This is the authoritative pre-truth execution contract for the first
House01/02/03 x seed0/1 full-300-s TNQC feasibility batch.

It supersedes earlier endpoint-execution wording while leaving the **TNQC V5
method equation unchanged**.

Status:

**V5 METHOD FROZEN / LINKED-NATIVE ENDPOINT FROZEN / CLEAN CURRENT-SOURCE
BUILD REQUIRED / HOUSE 300-S GATE PENDING / CLOSED LOOP HOLD.**

---

## 1. Three frozen layers

### Method layer — TNQC V5

Authoritative method document:

`docs/TNQC_V5_SUPPORT_COVERAGE_GATE_20260921.md`

The method remains:

- measured PMFS hit-logit field versus native transport-predicted hit-logit
  field;
- confidence-weighted centered-cosine quotient score (q_aff);
- adjacent-cell local-order corroboration (q_ord);
- terminal active free leaves only;
- leaf hypothesis measure (m_i) equal to represented free-cell count;
- reference affine pair mass (W_main);
- informative local-order pair mass (W_info);
- signed informative mass (S);
- coverage-aware shared gate

[
g = max(0,S/W_{main})
  = max(0,C_{cond}),ho ,
quad
ho=W_{info}/W_{main};
]

- bounded evidence (e_i=gq_{aff,i});
- fused generalized-loss tilt (L_i^{fused}=L_i^{PMFS}exp(e_i)).

No method term above is changed by this execution freeze.

### Endpoint layer — linked native ExpectedValue

The primary 300-s endpoint remains the historical PMFS metric:

[
left|
operatorname{ExpectedValue}(P_{300},0.05)-s^*
ight|_2.
]

The authoritative counterfactual evaluator is now:

`ros2_package/tools/tnqc_expected_value_native.cpp`

It is built in the **same colcon build** as `gsl_actionserver_node`, links
`GSL_common`, reconstructs a `Grid2D<double>` from the exported PMFS grid
metadata, and directly calls:

`GSL::Utils::ExpectedValue(grid, 0.05)`.

Therefore the native PMFS run and the counterfactual TNQC posterior share the
same source implementation, compiler/toolchain and standard-library
`std::sort` behavior.

The older standalone file

`reference/tnqc_expected_value_eval.cpp`

is retained only for dependency-free static/synthetic tests and for the
equal-probability tie falsification that motivated this correction. It is not
accepted by the authoritative six-case aggregate.

### Execution layer — clean current-source build

Before any House result is produced:

`reference/build_tnqc_v5_current.sh`

must:

1. verify the machine-readable TNQC manifest;
2. verify the complete committed `ros2_package` Git tree SHA;
3. reject tracked or untracked working-tree changes under `ros2_package`;
4. run the standalone `test_tnqc_score.cpp` core test;
5. delete the previous TNQC build workspace;
6. copy the frozen `ros2_package` tree into a clean colcon workspace;
7. build `gsl_server` in Release mode;
8. require both
   `gsl_actionserver_node` and `tnqc_expected_value_native`;
9. record SHA-256 provenance for both binaries.

The external VGR launch Python file is **plumbing only**. Its SHA-256 is
captured before the batch, copied into the run root, and every case runtime
manifest must report the same launch SHA.

---

## 2. Why direct linkage is necessary

PMFS `ExpectedValue` sorts cells by probability with a probability-only
`std::sort` comparator. Quadtree posterior leaves create exact probability
ties, and the 5% cutoff can split one tied block.

A source-blind 40-cell equal-probability counterexample showed that the old
Python cell-index tie-break and C++ `std::sort` can produce materially
different source estimates. That evidence is frozen in:

`evidence/TNQC_CPP_ENDPOINT_PARITY_AUDIT_20260921.json`.

A standalone C++ clone substantially reduced the risk, but a cloned
`std::sort` call still leaves a residual implementation/toolchain assumption.
Directly linking and calling `GSL::Utils::ExpectedValue` removes that
assumption.

---

## 3. Replay contract

Authoritative replay contract:

`TNQC_VGR_FIXED_TRAJECTORY_300S_REPLAY_V7_LINKED_NATIVE_ENDPOINT`

For each case, the replay must first reconstruct the exported native PMFS
posterior and pass:

- max absolute cell probability discrepancy <= (5	imes10^{-6});
- L1 posterior discrepancy <= (5	imes10^{-4}).

It then writes controlled posterior CSVs for:

- native exported posterior;
- TNQC V5 fused counterfactual;
- TNQC-only diagnostic.

All three are evaluated by the **same**
`tnqc_expected_value_native` binary.

The evaluator reports engine:

`gsl_utils_expected_value_linked_native_v1`.

Any other engine is invalid for the authoritative gate.

The linked evaluator's native result must also reproduce the actual
`gsl_actionserver_node` terminal

`RESULT IS: ... Error=...`

within 0.011 m, where the tolerance only covers the native log's two-decimal
printing.

Python top-5% remains a diagnostic used to expose tie sensitivity; it cannot
control GO/HOLD.

---

## 4. Aggregate contract

Authoritative aggregate contract:

`TNQC_VGR_FIXED_TRAJECTORY_300S_GATE_V6_LINKED_NATIVE_ENDPOINT`

A case enters the development statistic only if all integrity checks pass,
including:

- native posterior reconstruction;
- linked-native engine identity;
- native endpoint parity;
- V7 replay contract;
- V5 final-leaf/free-cell-measure/support-coverage gate scope;
- clean-build/runtime binary provenance.

Frozen development GO rule remains unchanged:

- all six cases integrity-valid;
- pooled top-5% error reduction >= 10%;
- >= 4/6 paired cases improve;
- worst paired degradation <= 25%;
- no false-confident collapse.

No method, endpoint rule, source truth, House assignment or threshold may be
changed after inspecting these six outcomes.

---

## 5. Current-source binary provenance

`reference/run_meaci_case_20260824.sh` now accepts the algorithm installation
root and VGR launch file independently.

The authoritative offline runner:

`reference/run_tnqc_vgr_offline_gate_20260920.sh`

must use:

- `PFDI_INSTALL_ROOT` = clean TNQC build workspace;
- `LAUNCH_FILE` = frozen external VGR launch overlay.

Each case records:

- algorithm binary path and SHA-256;
- external launch path and SHA-256.

The offline runner independently compares those values with the batch-level
pre-run hashes. A mismatch aborts the batch.

Thus an old August algorithm binary cannot silently satisfy a September
source manifest.

---

## 6. Closed-loop boundary

The closed-loop matrix is still prohibited until the authoritative offline
aggregate contains both:

- `valid=true`;
- `go_for_closed_loop=true`.

`reference/run_tnqc_closed_loop_matrix_20260920.sh` must additionally require
the V6 aggregate contract and clean-build the same frozen V5 source tree.

Within each source update, TNQC never controls native quadtree refinement.
Closed-loop `fused` may change posterior-derived planner state/variance and
therefore later motion; that planner-feedback effect is intentionally tested
only after fixed-trajectory inference gives GO.

---

## 7. One authoritative command

On the qualified VGR VM, after pulling the frozen repository:

```bash
bash reference/run_tnqc_vgr_offline_gate_20260920.sh
```

That command must perform manifest verification, clean build, binary/launch
provenance checks, six 300-s native runs, V7 fixed-trajectory replay, and V6
aggregation.

A nonzero HOLD/INVALID exit is a scientific result, not permission to tune the
same version.
