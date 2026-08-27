# CG-PC-CTT research entrypoint — V3 observation-conditioned resolution

Current branch: `research/cg-pc-ctt-v3-observation-quotient-theory`  
Status: **RESEARCH / H02 replacement challenge pending / no paper-level GO yet**.

This directory contains several historical protocol layers. Do not treat every file as a current entrypoint.

## 1. Frozen scientific status

### CONFIRMED

- CTT M1 wind-conditioned first-passage transport model is the frozen positive transport premise.
- Gate V2 repaired the finite-member self-noise bug in V1 and passed the real House03 bank `phi[10,206,8,626]` in all 10 contexts.
- Gate V2 is currently interpreted as a **model-side replicated-completeness premise**, not yet as a runtime reliability selector.
- Sparse observation support causes real local source-information loss in both the H03 CTT first-passage representation and the recovered House02 201-candidate PMFS hit-probability response representation.
- The recovered V12 House02 response bank has been replayed with the canonical V3 full-covariance nuisance metric; the sparse 2-D rank-loss phenomenon persists.
- Existing PMFS `applyEnsembleEcEdcl()` already materializes candidate × replica responses at actual measurement-event positions before its historical Hellinger normalization. This is the preferred runtime source for `H_t phi`.

### INVALID / LEGACY

- Gate V1: `INVALID_PROTOCOL` because finite `M=8` member-mean noise could create false source rank.
- Historical H02 hard-28 primary provenance: `LEGACY_HARD28_PROVENANCE_LOST`.
  Its summary numbers are development history only. Do not reconstruct cases to reproduce those numbers.
- `h02_hard28_fast_eval.py` and `bridge_fasttrack_verdict.py` are retained only for legacy artifact compatibility. They are **not** the current V3 H02 entrypoint.
- `local_pair_audit.py` is the earlier diagonal-whitening diagnostic. Use `local_pair_audit_v3.py` for current V3 full-covariance diagnostics.

### CURRENTLY TESTING

V3 asks a different question from global Gate V2:

> Given only the observations actually collected so far, what physical source resolution is currently supported, and are those observations compatible with the predictive family at all?

The central runtime object is

`z[s,m,e] = H_e phi[s,m]`,

where `H_e` restricts each candidate/member predictive response to causally available measurement support.

## 2. Shared V3 mathematics

All new V3 source-resolution scripts should import:

`v3_math.py`

It owns the canonical implementations of:

1. exact physical-coordinate quotient of candidate IDs;
2. full pair-difference transport-member covariance `Sigma_tr`;
3. Moore-Penrose nuisance precision `Sigma_tr^+`;
4. Delaunay physical-source neighbourhoods;
5. cross-member 2-D local tangent information

   `F_s = sum_{m!=n} B_{s,m} Sigma_tr^+ B_{s,n}^T / [M(M-1)]`;

6. replicated hard-negative pair separation;
7. ACI/data-assimilation-inspired local uncertainty-reduction diagnostics.

The full-covariance pseudoinverse replaces the earlier V3 diagnostic use of diagonal V2 whitening because exact duplicated feature embeddings do not create extra Mahalanobis information.

Observation/model compatibility is deliberately separate:

`v3_adequacy.py`

It reports scale-free candidate-family support diagnostics, including residual distance relative to member spread and the fraction of observation residual lying in the empirical member-variation span. No adequacy threshold is currently frozen.

Run before any V3 experiment:

```bash
cd experiments/cg_pc_ctt
bash run_v3_selftests.sh
```

Expected:

`CG_PC_CTT_V3_STATIC_AND_MATH_SELFTEST PASS`

## 3. H02 replacement challenge — current path

The lost historical hard-28 is not a blocker anymore.

Current challenge:

`H02_RECONSTRUCTED_CHALLENGE_V1`

Read first:

`docs/H02_LEGACY_HARD28_PROVENANCE_LOSS_AND_REPLACEMENT_20260827.md`

Before generating any new truth/margin/bridge outcome, freeze all structurally eligible House02 contexts:

```bash
python3 freeze_h02_reconstructed_context_manifest.py \
  /path/to/H02/search/root1 /path/to/H02/search/root2 \
  --carrier-manifest /path/to/v12_carrier_manifest.csv \
  --out-csv /tmp/H02_RECONSTRUCTED_CONTEXTS.csv \
  --out-json /tmp/H02_RECONSTRUCTED_CONTEXTS.json
```

Then rebuild all frozen contexts on the frozen 201-coordinate geometry grid under the declared CTT V13 truth-free member contract.

Final H02 replacement verdict uses:

```bash
python3 h02_reconstructed_challenge_verdict.py \
  H02_RECONSTRUCTED_CASE_RESULTS.csv \
  --audit-json H02_RECONSTRUCTED_AUDIT.json \
  --out H02_RECONSTRUCTED_VERDICT.json
```

The replacement challenge does **not** require exactly 28 cases. Frozen minima are at least 18 eligible atoms and at least 3 independent run/seed clusters.

## 4. Observation-conditioned V3 components

### Physical/observation resolution

- `observation_quotient_gate.py` — observational equivalence classes / local pair resolution prototype using shared full-covariance mathematics.
- `local_tangent_information.py` — 2-D physical source tangent-information diagnostic using shared full-covariance mathematics.
- `local_pair_audit_v3.py` — current full-covariance hard-negative pair audit.
- `qualify_observation_support_contract.py` — verifies feature-space geometry needed to materialize `H_e`.
- `v12_response_bank_tangent_audit.py` — cross-representation replay on the frozen V12 PMFS hit-probability bank; never CTT hard-28 evidence.

### Observation adequacy

- `v3_adequacy.py` — candidate-family predictive support diagnostics.
- `observation_adequacy.py` — CLI for `prediction[S,M,E] + observed[E]` or batched equivalents.
- `selftest_v3_adequacy.py` — synthetic shared-systematic-bias regression.

Replicated source structure and observation adequacy are separate premises: a family may be highly reproducible and still be jointly wrong.

### Sparse sensor outcome

- `block_dynamic_marker.py` — fixed within-stop dynamic outcome marker from repeated StopAndMeasure concentration samples.

### Bridge/data contract

- `qualify_bridge_causal_contract.py` — rejects primary causal `R` features that contain source-downstream gas/hit/concentration/sensor-state information.

Primary causal roles:

- `R`: source-independent wind / pose / action / map context;
- `Z(S)`: candidate-dependent transport/predictive physics proxy;
- `Y`: observed gas/sensor block outcome.

No script may claim a general proximal-identification theorem from this finite-dimensional operational bridge alone.

## 5. Sequential evidence boundary

Ordinary member sign-flip `p` values are frozen **offline diagnostics**. Recomputing an unadjusted `p<=0.01` at every online source update and releasing on the first crossing is not authorized because repeated peeking creates optional-stopping risk.

Current low-risk runtime direction is deterministic physical resolution + observation adequacy + fold-consistent ordering, while inferential p-values remain in frozen offline qualification unless an anytime-valid evidence process is explicitly derived and self-tested.

## 6. Closed-loop handoff

The already prepared confirmatory matrix remains unchanged:

`3 Houses x 10 seeds x OFF/ON = 60 runs`.

V3/H02 offline qualification is only a falsification gate before spending that experiment budget.

Do not change House/seed-specific parameters after H02 manifest freeze. If `H02_RECONSTRUCTED_CHALLENGE_V1` passes the frozen criteria, hand off to the existing multi-seed runner in:

`closed_loop/cg_pc_ctt/`.

Primary final endpoint remains PMFS `ExpectedValue(sourceProbability,0.05)` localization error with the previously frozen 30-pair aggregate criteria.

## 7. Theory map

Primary V3 derivation:

`docs/CG_PC_CTT_V3_OBSERVATION_QUOTIENT_DERIVATION_20260827.md`

Supporting diagnostics and design notes:

- `docs/CG_PC_CTT_V3_ASSIMILATIVE_RESOLUTION_AND_SEQUENTIAL_VALIDITY_20260827.md`
- `docs/CG_PC_CTT_V3_FULL_COVARIANCE_REPLAY_20260827.md`
- `docs/CG_PC_CTT_V3_SPARSE_TANGENT_DIAGNOSTIC_20260827.md`
- `docs/CG_PC_CTT_V3_CROSS_REPRESENTATION_AND_RUNTIME_REUSE_20260827.md`
- `docs/CG_PC_CTT_V3_GEOMETRY_INFORMATION_ADDENDUM_20260827.md`
- `docs/CG_PC_CTT_V3_FAILURE_PREMORTEM_20260827.md`
- `docs/H02_LEGACY_HARD28_PROVENANCE_LOSS_AND_REPLACEMENT_20260827.md`

Binding rule: **no outcome-fitted threshold, no House-specific tuning, no source truth in runtime objects, no unvisited forward-field support counted as current localization evidence, and no repeated unadjusted online p-value release.**
