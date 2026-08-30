# CTT FINAL AGENT HANDOFF — FULL STATE

Date: 2026-08-30
Repository: `kris-yun/uav-gsl-isj`
Handoff branch: `handoff/ctt-final-agent-resume-20260830`
Parent working commit: `aacf30f427d8a23a4b5ba936b78d0d0a21bdaf29`

---

## 1. Paper-level method is NOT changing

The umbrella remains **Causal Transport Tomography (CTT)** / causal spatiotemporal neural transport inference.

Scientific chain:

```text
source S
  -> transport latent/state Z_t
  -> physical concentration C_t
  -> run-persistent sensor state R_t
  -> measured concentration M_t
  -> ordered first-passage/event observation F/Y
  -> source likelihood/posterior
```

The three load-bearing components are:

1. **Causal / mechanistic generative structure** — source intervention is evaluated through the physical transport + sensor chain, not by direct source-coordinate classification.
2. **Temporal first-passage information** — native 0.2-s arrival timing and survival/no-arrival evidence.
3. **Neural physical solver surrogate** — amortized approximation of candidate-conditioned transport/first-passage dynamics; never a direct `p(source|data)` black box.

Do not create a new paper-level method name or another V8/V9 rescue family.

---

## 2. Frozen authoritative simulator/data boundaries

- ROS2 Humble + GADEN.
- authoritative forward contract: `main_v8`.
- `dataset_v1` is excluded/frozen and may not be substituted.
- native physical chain must remain `physical ppm -> persistent sensor -> measured ppm`.
- occupancy/hit maps are not admissible substitutes for physical ppm.
- sensor state is **run-persistent**; do not reset per context/block.
- native sample cadence used for the first-passage tape: `0.2 s`.
- one complete PMFS physical stop contributes exactly the first 80 causal samples = 8 blocks x 10 samples; incomplete tail is not a ninth block.
- first-passage threshold semantics are **strict** `measured_ppm > 0.1`, not `>= 0.1`.

---

## 3. Frozen prior failures (do not revisit as tuning targets)

### 3.1 RMFE

- activation chain worked, but H02 full32x2 gave 0/2 improvement.
- classified A-type macro-ranking failure; fixed-A amplitude scale mismatch was primary.
- RMFE main innovation: NO-GO.

### 3.2 SCTT downstream

- C3 SCTT did not beat Classic and shuffle beat ordered SCTT.
- `SCTT_H02_DOWNSTREAM_MAIN_INNOVATION = NO-GO`.

### 3.3 residual-TCN / temporal V1–V7

Frozen review PR #8:

```text
PR: https://github.com/kris-yun/uav-gsl-isj/pull/8
head: 484fb9f330a21c8f2969fdcced8ce7c578217df2
base: d26194259b5089cb0905059d8017dd8171b0f97d
```

Interpretation: generic residual TCN temporal representations had real temporal sensitivity in subsets but were not nuisance-stable. Post-hoc interval/order/isotonic/NNLS protection did not rescue them. Do not tune blends, margins, temperatures, Top-K, posterior projections, or gates.

---

## 4. First-passage line before the new wind bank

Frozen review PR #9:

```text
PR: https://github.com/kris-yun/uav-gsl-isj/pull/9
review head: 7fcab1606a059f07fcf7959675ae7a0d275d9243
base: eacdfc28324085fd860db4a20a60a9e9e22a54e0
```

PR #9 contains:

- coarse 8-block temporal falsification;
- native 0.2-s first-passage premise code;
- failed neural M1 training/diagnostics;
- final factorized survival + phase neural implementation;
- method freeze and H01 offline verdict;
- next wind-conditioned physical bank contract;
- Codex1 review contract.

Frozen status at that point:

```text
CTT_H01_NATIVE_FIRST_PASSAGE_PREMISE_PASS
CTT_H01_FACTORIZED_NEURAL_FIRST_PASSAGE_FINAL_NO_GO
CLOSED_LOOP_NOT_AUTHORIZED
```

---

## 5. Correct wind-conditioned H01 physical bank — COMPLETED

A later Codex run executed the preregistered wind-conditioned bank build.

### 5.1 Bank integrity result

```text
16,800 / 16,800 coherent worlds generated
= 210 source carriers x 10 generating wind contexts x 8 transport keys
```

Each `(source, wind, transport-key)` world was generated coherently and sampled on five routes; routes did not regenerate/perturb plume RNG.

G0 integrity checks all passed:

- source/query coverage;
- exact wind provenance;
- held-key variation;
- deterministic replay;
- native physical/sensor parity;
- PMFS 8x10 block semantics.

Persistent sensor parity was bitwise exact.

Physical manifest SHA-256 from the returned package:

```text
6530cd93d315d0db93a9bbfb241718fefc693e52f3f7dac2a51777fb50e66a7f
```

The ~595 MB bank is preserved on the VM; the compact evidence package does not duplicate all payload bytes.

### 5.2 Formal freeze identifiers for the bank run

From the returned preliminary package:

```text
scientific freeze commit:
ef33630cc1b2e26dac4f63e9b5c23178198aeaa7

registration commit:
a3204de10b04344e6cac469d44daa09c0ffcfc92

latest tooling-only monitor repair:
b2ce1e4

freeze JSON SHA-256:
f867bd1815dea7a6b95ea2aac7ac7f88dcc4ef1e2024c9493c140272927f6979
```

### 5.3 Old 33-feature neural M1 — FORMAL NO-GO

Terminal status:

```text
CTT_H01_WIND_CONDITIONED_NEURAL_M1_PHYSICAL_NO_GO
```

Held-out setup:

- wind contexts 1 and 2;
- held transport keys 6 and 7;
- route 4005.

Conditional wind model was significantly worse than frozen static-wind comparator:

```text
static - conditional NLL   = -0.024364018746357307
95% CI                     = [-0.03782184910260429, -0.010123398599043742]

static - conditional Brier = -0.017060325642619653
95% CI                     = [-0.020823891027456614, -0.013127244291947277]

shuffle - conditional NLL  = 0.00524029638093322
shuffle 95% CI             = [-0.008678368378783802, 0.018949281576736005]
```

Both held-out wind contexts independently failed the conditional-better criterion.

Checkpoint hashes:

```text
conditional checkpoint SHA-256:
995e859d67629cb03cae165539980cffb3740fbfb42b1e500c7bb1a4a5d436f9

static checkpoint SHA-256:
f67746aeb85f458beee5efc1cd2c8208cf0bda9341fe62ae9ead59c11e762816
```

The old 33-feature MLP is rejected. Do not use it in runtime/closed loop.

### 5.4 Local evidence package for this NO-GO

User-provided local package name:

```text
CTT_H01_WIND_M1_PRELIMINARY_NO_GO_20260830_R1.zip
```

SHA-256:

```text
C1AC52683DDBC0B18E91D8656B73E7BFE353ED159ABC4CAD7BA83981FF7FC32A
```

Original Windows staging path reported by Codex/user:

```text
D:\ZYC\A-gas\_staging\CTT_H01_WIND_M1_PRELIMINARY_NO_GO_20260830_R1.zip
```

This binary ZIP is NOT asserted to be checked into GitHub. Treat the hash above as the identity contract and locate the exact local file if full evidence is needed.

---

## 6. Cross-wind NATIVE first-passage diagnosis — PASS

Because neural M1 failed, a preregistered no-network mechanism diagnosis was run on the already valid bank. No new network was trained; no new GADEN worlds or closed-loop runs were launched.

Frozen verdict:

```text
CROSS_WIND_NATIVE_FIRST_PASSAGE_PASS
```

Preregistration commit:

```text
aacf30f427d8a23a4b5ba936b78d0d0a21bdaf29
```

Preregistration JSON SHA-256:

```text
34555e2e66e78f189f9af17ff9846e0a1efcfad1625887cea126ff3d2be1ffb6
```

Diagnostic script SHA-256:

```text
06e43502ea0d4bcf9e1f2d275b290a7f3276b51c80d16e21b4c039957bc1e562
```

840-case CSV SHA-256:

```text
d01498032fb3c2b342a114747822a203a137c0422fdefa1ab1dfcce009f22e62
```

SUMMARY.json SHA-256:

```text
c1e76f41ee8ee785210ccbf3d794daa1f15169dc23181bd776b616628d1033cb
```

### 6.1 Overall results

840 cases = `2 held wind contexts x 2 observation keys x 210 source interventions`.

```text
FULL first-passage mean normalized rank = 0.123861
random reference                         = 0.5
Top-5                                    = 13.33%
random Top-5                             = 2.38%
Top-10                                   = 26.07%
random Top-10                            = 4.76%
```

FULL vs SURVIVAL:

```text
FULL mean normalized rank      = 0.123861
SURVIVAL mean normalized rank  = 0.135051
relative rank reduction        = 8.29%
wins/losses/ties               = 408 / 228 / 204
one-sided exact sign p         = 4.49648e-13
```

FULL vs hit-count-preserving TIME_PERMUTE:

```text
TIME_PERMUTE mean normalized rank = 0.136062
relative rank reduction           = 8.97%
wins/losses/ties                  = 157 / 83 / 600
one-sided exact sign p            = 1.02698e-6
```

Both held-out wind contexts were non-reversing.

Per context FULL:

```text
context 1: mean norm rank 0.142937, median rank 19, Top-5 13.57%, Top-10 21.90%
context 2: mean norm rank 0.104785, median rank 15, Top-5 13.10%, Top-10 30.24%
```

Scientific interpretation:

1. Native first-passage retains source ordering across held-out winds.
2. Arrival timing adds source information beyond reachability/survival.
3. The earlier neural NO-GO is more consistent with a representation/amortization failure than with collapse of the underlying first-passage mechanism.

### 6.2 Interpretation boundary

This does **not** prove:

- the deployable neural solver works;
- cross-House generalization;
- a >=10% localization-error improvement over PMFS;
- closed-loop benefit.

The 8.29% / 8.97% values are relative improvements in normalized source-rank diagnostics, not localization error.

### 6.3 TEST consumption boundary

Wind contexts **1 and 2 are permanently diagnostic-only from this point forward**.

Any future revised neural M1 must use completely new unseen wind contexts for confirmatory testing. Contexts 1/2 may not be reused to claim confirmatory PASS.

### 6.4 Local evidence package for this PASS

```text
CTT_H01_CROSS_WIND_NATIVE_FIRST_PASSAGE_PASS_20260830_R1.zip
```

SHA-256:

```text
76F3A1D5FE0DB0BE1944502E9EF6DED38B53C97D273174FD945D10A41D65AF4F
```

Original Windows staging path reported:

```text
D:\ZYC\A-gas\_staging\CTT_H01_CROSS_WIND_NATIVE_FIRST_PASSAGE_PASS_20260830_R1.zip
```

Again: do not claim the binary ZIP is in GitHub unless you verify it; use the hash to locate and validate the exact local package.

---

## 7. Current working branch at the handoff point

Previous Codex working branch:

```text
codex/ctt-h01-wind-bank-freeze-20260830
```

GitHub head at handoff:

```text
aacf30f427d8a23a4b5ba936b78d0d0a21bdaf29
```

That commit is the cross-wind diagnosis preregistration commit. The returned post-run diagnostic binary evidence is local and identified by hashes above; a later GitHub evidence commit had not been verified at handoff.

This handoff branch was created from exactly that commit and adds only handoff documentation.

---

## 8. User's shared-data location — CURRENT PRACTICAL BLOCKER

The user explicitly states the already-unpacked/shared workspace is:

```text
D:\ZYC\A-gas\workspace
```

Previous agent behavior immediately before quota exhaustion:

1. It checked currently visible H01 wind files and saw only `wind_iteration_0..10` in one location.
2. It believed old contexts 0..9 consumed iterations 1..10, leaving only one visible unused field.
3. It searched for additional source data and began preparing/downloading VGR House01 from Zenodo.
4. User corrected it: the dataset is already in the local VMware shared folder.
5. Agent stopped the redundant download and started to inspect VMware shared-folder mapping / `/mnt/hgfs`.
6. Context window/quota ended before that inventory was completed.

Therefore the next agent's FIRST action is to inspect the shared dataset, not to train a model.

Do not assume the Linux mount path. Resolve the VMware shared-folder mapping and establish which mounted path corresponds to `D:\ZYC\A-gas\workspace`.

Do not redownload VGR unless the shared folder is proven incomplete.

---

## 9. Fresh-wind requirement and logical IDs

The prior execution plan reserved logical IDs:

```text
10,11,12,13 -> final neural confirmatory test
14,15       -> later H01 300-s closed-loop development
```

These are **logical experiment IDs only**. They do not require filenames literally named `wind_iteration_11..16`.

A field may be assigned one of these IDs only if it is a genuinely unused independent House01 airflow/wind realization with explicit provenance/hash and has not been used for architecture selection, feature engineering, training, validation, or prior diagnosis.

Forbidden ways to create a "fresh" context:

- copy/rename an old wind;
- add artificial numerical noise;
- rotate/reflect an old field;
- rescale an old field after seeing results;
- combine old fields into a synthetic test without preregistered physical justification.

If fewer than six genuine unused H01 contexts exist, freeze:

```text
FRESH_WIND_INPUT_BLOCKED
```

and document exactly what is available. Do not silently substitute H02/H03 or fabricated winds.

---

## 10. Deployment/runtime warning about wind input

The old failure proved that using a wind feature that is not a causal parent of the forward field is invalid.

Future neural M1 must distinguish:

```text
W_gen    = wind field/context that actually generated the forward physics
W_online = wind representation truly available to the deployed runtime
```

Do not assume `W_online == W_gen`.

For every neural wind feature, freeze:

- feature name;
- physical meaning;
- coordinate frame;
- time semantics;
- source during training;
- source during runtime;
- whether simulator-only;
- whether future information is required.

If exact full simulator wind is used for the simulation-only paper experiment, label it `SIMULATION_KNOWN_WIND`; do not claim real-flight deployability without an online adapter.

The previous VM audit also noted no ONNX Runtime/LibTorch deployment library was installed. Do not solve this deployment dependency before the offline neural gates pass; runtime integration is downstream.

---

## 11. Final neural formulation allowed for one last implementation

No more residual TCN or 33-summary MLP rescue.

The allowed final neural role is a **physics-conditioned first-passage hazard solver** with spatial wind/map representation.

For sample bin `j=1..80`:

```text
h_j(s, X) = P(F=j | F>=j, source candidate s, causal physical context X)
```

Distribution is uniquely induced by hazards:

```text
P(F=j)     = h_j * product_{r<j}(1-h_r)
P(F=never) = product_{r=1..80}(1-h_r)
```

Proper event-time likelihood:

```text
if F=j:
  loss = -log(h_j) - sum_{r<j} log(1-h_r)

if F=never:
  loss = -sum_{r=1..80} log(1-h_r)
```

No trainable survival/phase weights, temperatures, alphas, posterior/rank/localization loss, learned reliability gate, Top-K rescue, or post-test architecture change.

Preferred representation class:

```text
source-independent spatial wind/map encoder
+ source/query geometric conditioning
+ hazard decoder
```

The exact architecture must be frozen **before fresh confirmatory wind performance is generated/opened**.

---

## 12. Exact closed-loop likelihood semantics (downstream only)

Only after fresh neural physical + source-evidence gates pass:

For completed stop `b`:

```text
L_b(s) = P_theta(F_b^obs | s, X_b)
```

Bayesian update:

```text
log posterior_b(s)
  = log posterior_{b-1}(s)
  + log L_b(s)
  - logsumexp_s'[ log posterior_{b-1}(s') + log L_b(s') ]
```

Single-consumption rule:

- native sensor preprocessing: KEEP
- persistent sensor state: KEEP
- measured gas/environmental map: KEEP
- wind mapping: KEEP
- occupancy/map: KEEP
- planner shell: KEEP
- native PMFS source HIT/NOTHING assimilation for the same 80 gas samples: DISABLE when CTT ON
- CTT first-passage source likelihood: ENABLE exactly once

Never multiply native source likelihood and CTT likelihood for the same observation.

Maintain an assimilation ledger:

```text
run_uuid, physical_stop_id, sample_id_start, sample_id_end,
observation_hash, assimilation_method
```

Each observation hash may be consumed exactly once by source inference.

---

## 13. Current authorization

As of handoff:

```text
CLOSED_LOOP_NOT_AUTHORIZED
```

A future agent may authorize H01 closed-loop development only after:

1. genuinely fresh neural M1 physical gate PASS;
2. genuinely fresh neural source-evidence gate PASS;
3. Python/deployment probability parity PASS;
4. first-passage extraction parity PASS;
5. posterior update parity PASS;
6. observation single-consumption PASS;
7. no-future leakage PASS;
8. CTT OFF/native parity PASS;
9. runtime budget PASS.

Then and only then may it launch the preregistered 300-s paired H01 OFF/ON development runs.

See `docs/CTT_AGENT_NEXT_EXECUTION_CONTRACT_20260830.md` for the exact continuation sequence.
