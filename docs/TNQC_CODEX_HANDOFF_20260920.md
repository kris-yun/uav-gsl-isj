# TNQC Codex handoff — frozen offline candidate
Date: 2026-09-20
Repository: `kris-yun/uav-gsl-isj`
Branch: `main`

## 0. Status that must not be overstated

**External source-identity representation signal: positive.**
**VGR/GADEN 300-s offline localization gain: not yet established.**
**Closed-loop localization gain: not yet established.**

Correction: the Orebro 2/5/10-min experiments are auxiliary only and cannot serve as the project's offline GO. Codex must not start the House closed-loop matrix until `docs/TNQC_VGR_300S_CORRECTION_20260920.md` is satisfied and a new explicit GO is committed.

Codex is being handed a pre-registered closed-loop test, not permission to tune the method after seeing House truth.

The only known external infrastructure blocker is the installed VM launch overlay:
`/dev/shm/meaci_online_20260824/launch/vgr_gsl_pmfs_pfdi.launch.py`
must declare a `tnqc_mode` launch argument and forward it to the PMFS node. The repository-side C++ implementation and case runner already accept `off|shadow|fused|only`.

---

## 1. Paper-level scientific line

### Main innovation: Transport-Nuisance Quotient Canonicalization (TNQC)

Gas-source inference is performed on equivalence classes of spatial plume observations after removing nuisance coordinates that do not identify the source.

For an observed logit field (x\in\mathbb{R}^n), positive weights (w_i), and weighted mean

[
\mu_w(x)=\frac{\sum_i w_i x_i}{\sum_i w_i},
]

define the weighted centered representative

[
\tilde x_i=x_i-\mu_w(x).
]

The continuous TNQC field match for observation (x) and candidate prediction (y_s) is

[
q_{\rm aff}(x,y_s)=
\frac{\sum_i w_i\tilde x_i\tilde y_{s,i}}
{\sqrt{\sum_iw_i\tilde x_i^2}\sqrt{\sum_iw_i\tilde y_{s,i}^2}}.
]

For independent positive-affine nuisance actions

[
x' = a x+b\mathbf 1,\quad
y'_s=c y_s+d\mathbf 1,\qquad a,c>0,
]

we have exactly

[
q_{\rm aff}(x',y'_s)=q_{\rm aff}(x,y_s).
]

The PMFS prediction remains transport-conditioned; TNQC does **not** discard wind/transport physics. It removes nuisance amplitude/background coordinates only at candidate comparison time.

### Secondary innovation: confidence-weighted local spatial partial-order quotient

Let (E) be the fixed set of spatially adjacent supported grid-cell pairs. Define

[
\sigma^x_{ij}=\operatorname{sgn}(x_i-x_j),\qquad
\sigma^{y_s}_{ij}=\operatorname{sgn}(y_{s,i}-y_{s,j}),
]

with edge weight

[
\omega_{ij}=\min(w_i,w_j).
]

Ignoring ties, the local-order score is

[
q_{\rm ord}(x,y_s)=
\frac{\sum_{(i,j)\in E}\omega_{ij}
\sigma^x_{ij}\sigma^{y_s}_{ij}}
{\sum_{(i,j)\in E}\omega_{ij}}.
]

If (g) and (h) are arbitrary strictly increasing scalar calibration curves,

[
q_{\rm ord}(g(x),h(y_s))=q_{\rm ord}(x,y_s).
]

This is deliberately **local adjacency order**, not global concentration ranking.

### Frozen fusion

No fitted fusion coefficient is allowed in the first closed-loop screen:

[
e_s=
\begin{cases}
\tfrac12(q_{\rm aff}+q_{\rm ord}), & \text{at least 2 valid local edges},\\
q_{\rm aff}, & \text{otherwise}.
\end{cases}
]

By construction (e_s\in[-1,1]). The online arms are

[
L_{\rm fused}(s)=L_{\rm native}(s)\exp(e_s),
\qquad
L_{\rm only}(s)=\exp(e_s).
]

`shadow` computes the same (e_s) but leaves (L_{\rm native}) untouched.

**Important frozen design decision:** do not multiply (e_s) by (sqrt{N_{\rm eff}}) or raw cell count. PMFS map cells are spatially correlated/smoothed; such scaling would create pseudo-replication and could overwhelm the native likelihood.

---

## 2. Why this is a current scientific line, not a relabeling exercise

Verified remote-domain lineage:

1. Behrooz Tahmasebi & Stefanie Jegelka, **Generalization Bounds for Canonicalization: A Comparative Study with Group Averaging**, ICLR 2025.
   - Proceedings: https://proceedings.iclr.cc/paper_files/paper/2025/hash/b36dc39b319ba6ba2a0fd7601951efb4-Abstract-Conference.html
   - Relevance: formalizes canonicalization as projection to a reduced space of symmetry classes and identifies regimes where canonicalization vs group averaging differ.

2. Zakhar Shumaylov et al., **Lie Algebra Canonicalization: Equivariant Neural Operators under Arbitrary Lie Groups**, ICLR 2025.
   - OpenReview: https://openreview.net/pdf?id=7PLpiVdnUC
   - Relevance: canonicalization under continuous/non-compact Lie symmetries; supports treating nuisance actions analytically before ordinary inference.

3. Hannah Lawrence et al., **Improving Equivariant Networks with Probabilistic Symmetry Breaking**, ICLR 2025.
   - OpenReview: https://openreview.net/pdf?id=ZE6lrLvATd
   - Relevance: self-symmetry can make deterministic equivariant outputs under-identifying; motivates explicit abstention/identifiability handling rather than forced mode selection.

4. Yikang Li et al., **Affine Steerable Equivariant Layer for Canonicalization of Neural Networks**, ICLR 2025.
   - OpenReview: https://openreview.net/pdf?id=5i6ZZUjCA9
   - Relevance: affine-group canonicalization is a first-class modern equivariance problem.

5. Ya-Wei Eileen Lin & Ron Levie, **Adaptive Canonicalization with Application to Invariant Anisotropic Geometric Networks**, ICLR 2026.
   - Proceedings: https://proceedings.iclr.cc/paper_files/paper/2026/hash/2774a3b52d436b5930da660dd2b32b3a-Abstract-Conference.html
   - Relevance: canonicalization can be input/model dependent and still symmetry respecting; this is the future route if airflow-conditioned canonicalization is needed after the frozen first screen.

6. Alonso Urbano et al., **RECON: Robust Symmetry Discovery via Explicit Canonical Orientation Normalization**, ICLR 2026.
   - OpenReview: https://openreview.net/pdf?id=bpWzTPDybh
   - Relevance: data-aligned canonical orientation under unknown instance-specific symmetries and distribution shift.

7. Yixian Xu et al., **Quotient-Space Diffusion Models**, ICLR 2026.
   - Proceedings: https://proceedings.iclr.cc/paper_files/paper/2026/hash/ddbc4b54d1167f3c64ec639e388bf555-Abstract-Conference.html
   - Relevance: if group-related observations are equivalent, learning/inference can be formulated directly on the quotient space rather than spending capacity on group-action coordinates.

### GSL novelty collision that must be respected

Wanting Jin, Agatha Duranceau, İzzet Kağan Erünsal & Alcherio Martinoli,
**Calibration-Free Gas Source Localization with Mobile Robots: Source Term Estimation Based on Concentration Measurement Ranking**, ICRA 2026 / arXiv:2605.13208.
- arXiv: https://arxiv.org/abs/2605.13208
- EPFL DISAL record: https://www.epfl.ch/labs/disal/research/gassensingstructure/

That work uses global relative concentration ranking to obtain calibration-free probabilistic GSL. Therefore **do not claim rank invariance, monotone invariance, or calibration-free ranking itself as the novelty**.

The novelty boundary of this branch is the combined construction:
- explicit physical nuisance quotient formulation;
- continuous affine-quotient field match;
- PMFS transport-conditioned candidate fields;
- local spatial-adjacency partial-order robustness channel;
- confidence/support-aware abstention;
- direct online posterior use with an exact shadow determinism arm.

---

## 3. Auxiliary external evidence (not the VGR localization gate)

Dataset: public Orebro3DSEN, 27 calibrated MOX sensors in a 3x3x3 array, 2 Hz.

Repeated-source group:
`Exp01/Exp02/Exp06/Exp08/Exp09` share the same source coordinate while release strength and airflow conditions vary. Other experiments supply alternative source positions.

No source truth enters feature construction; labels are used only after representation construction for evaluation.

Frozen interval: 40–90 min.

Conservative results:

| window | affine quotient AUC / LOCO acc | local-order AUC / LOCO acc | equal fusion AUC / LOCO acc |
|---|---|---|---|
| 2 min | 0.806 / 0.600 | 0.696 / 0.696 | 0.791 / 0.616 |
| 5 min | 0.789 / 0.620 | 0.681 / 0.680 | 0.791 / 0.700 |
| 10 min | 0.789 / 0.600 | 0.723 / 0.680 | 0.823 / 0.680 |

At 5 min raw sensor means are about AUC 0.486 / LOCO acc 0.20. A fresh independent recheck against the current public blobs and the current frozen probe logic was used to reconcile the affine-only numbers above before any House closed-loop TNQC result was available.

Condition-specific monotone compression
(g_a(c)=\operatorname{asinh}(ac)/a)
changes the affine channel but leaves the local-order representation exactly unchanged. This is the empirical reason the local spatial partial-order channel is retained as the secondary innovation.

Reproduction:
```bash
python3 reference/tnqc_orebro_offline.py --window-minutes 2
python3 reference/tnqc_orebro_offline.py --window-minutes 5
python3 reference/tnqc_orebro_offline.py --window-minutes 10
```

Primary record: `docs/TNQC_OFFLINE_GATE_20260920.md`.

---

## 4. Repository implementation map

Core online equation:
- `ros2_package/src/gsl_server/algorithms/PMFS/internal/TNQCScore.hpp`

PMFS integration:
- `ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.hpp`
- `ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp`
- `ros2_package/src/gsl_server/algorithms/PMFS/PMFS.hpp`
- `ros2_package/src/gsl_server/algorithms/PMFS/PMFS.cpp`

Standalone invariance test:
- `ros2_package/test/test_tnqc_score.cpp`
- wired into `ros2_package/CMakeLists.txt`

Offline measured-data probe:
- `reference/tnqc_orebro_offline.py`

Closed-loop case runner:
- `reference/run_meaci_case_20260824.sh`
- accepts `TNQC_MODE=off|shadow|fused|only` without changing the historical OFF launch argument list.

Closed-loop matrix:
- `reference/run_tnqc_closed_loop_matrix_20260920.sh`

Theory/search records:
- `docs/CANDIDATE_SYMMETRY_QUOTIENT_20260920.md`
- `docs/RESEARCH_CYCLE_20260920.md`
- `docs/TNQC_OFFLINE_GATE_20260920.md`

---

## 5. Codex execution order — do not tune before truth evaluation

### Stage A — checkout/build/sanity

1. Pull current `main`.
2. Build the ROS package with the existing VM toolchain.
3. Run the standalone `tnqc_score` test.
4. Re-run the Orebro 2/5/10-min probe and confirm the JSON outputs match the frozen gate within numerical precision.

Do not change equations because of any House result.

### Stage B — external launch plumbing only

Inspect:
```bash
ros2 launch /dev/shm/meaci_online_20260824/launch/vgr_gsl_pmfs_pfdi.launch.py --show-args | grep tnqc_mode
```

If absent, modify only the installed launch overlay so that:
- it declares string launch argument `tnqc_mode`, default `off`;
- it forwards that argument to the PMFS node parameter `tnqc_mode`.

Do **not** change PMFS scoring equations, weights, thresholds, source truth, wind settings, planner settings, timeout, or update cadence in this step.

### Stage C — HOLD

Do not execute the House closed-loop stages below yet. First complete the VGR/GADEN fixed-trajectory 300-s offline localization replay specified in `docs/TNQC_VGR_300S_CORRECTION_20260920.md`.

### Stage D — determinism gate after explicit VGR offline GO

Run only:
```bash
TNQC_MODES="off shadow" \
bash reference/run_tnqc_closed_loop_matrix_20260920.sh
```

For all House01/02/03 × seed0/1 pairs:
- OFF and SHADOW must match in final native PMFS result;
- preferably compare trajectory/result artifacts too, not only the printed error.

Any mismatch invalidates the batch. Fix plumbing/determinism only; do not alter TNQC mathematics.

### Stage E — primary closed-loop screen

After Stage C passes:
```bash
TNQC_MODES="off shadow fused only" \
bash reference/run_tnqc_closed_loop_matrix_20260920.sh
```

Frozen run contract:
- House01/02/03;
- seeds 0/1;
- 300 simulation seconds;
- `stepsSourceUpdate=3`;
- same sensor, wind, planner and PMFS settings across arms;
- `fused` is the primary TNQC arm;
- `only` is a mechanism ablation.

### Stage F — frozen advancement gate

Against native PMFS OFF:
- pooled PMFS top-5%-expected-location error reduction >= 10%;
- at least 4/6 pairs improve;
- no pair degrades > 25%;
- no false confident collapse.

This is a **development** gate only. Passing it authorizes the next experimental cycle; it is not sufficient for a paper claim.

### Stage G — comparison with the previously frozen method

Only if Stage E passes, run the same six House/seed conditions for the frozen ME-ACI V10 arm (`ARM=on, PFDI_MODE=me_aci, TNQC_MODE=off`) and then test the combined arm (`TNQC_MODE=fused`) without retuning either component. Report:
- native PMFS;
- frozen ME-ACI V10;
- TNQC fused;
- ME-ACI V10 + TNQC fused.

This separates “beats baseline PMFS” from “adds value beyond the already successful project method.”

---

## 6. No-touch list before the first House matrix is complete

Do not change:
- 1:1 fusion weight;
- evidence bound ([-1,1]);
- support rule (<4 supported cells => invalid);
- local-edge definition;
- confidence weights;
- `exp(e_s)` likelihood modifier;
- PMFS `stepsSourceUpdate=3`;
- 300 s budget;
- planner/sensor/wind settings;
- House source truth or start points;
- Orebro source groups or evaluation interval.

Any alteration after looking at House truth creates a new method version and requires a new pre-registration file.

---

## 7. What Codex must return

For every run:
- exact git commit SHA;
- algorithm binary SHA-256;
- launch-overlay diff;
- House / seed / arm / TNQC mode;
- final PMFS top-5% expected-location error;
- MAP / full-mean / variance diagnostics where available;
- wall-clock and simulation-time budget;
- OFF-vs-SHADOW determinism result.

For the matrix:
- 6 paired OFF-vs-FUSED errors and percentage changes;
- pooled error;
- improve count;
- worst degradation;
- false-collapse check;
- Stage-E PASS/FAIL;
- raw artifacts path.

No method changes are allowed during this report-generation step.

---

## 8. Frozen commit trail before this handoff

Key commits already on `main`:
- `0e771ece` — TNQC quotient-field scoring core
- `9fddc3c0` — expose TNQC scoring state
- `fe06d13a` — opt-in TNQC PMFS mode
- `051589d6` — configure TNQC arms
- `d1849979` — integrate quotient evidence into PMFS scoring
- `77175cfb` — local-edge utility fix
- `88bd8916` / `015ba315` — standalone invariance test + CMake wiring
- `76760605` — runner exposes TNQC arm
- `6a005e2b` — frozen Orebro falsification probe
- `942e485e` — frozen closed-loop ablation driver
- `25b829f1` — offline gate record
- `4e6188bc` — bound TNQC evidence against spatial pseudo-replication
- `123436d1` — advance to frozen closed-loop candidate

The scientifically correct status at handoff is:

**TNQC OFFLINE POSITIVE / CLOSED-LOOP PENDING.**


## 9. Corrected handoff status

Do not interpret the Orebro classification-style probe as a localization result. The project endpoint is the final 300-s PMFS top-5% expected-location error on VGR/GADEN House01/02/03.

**Handoff status: VGR 300-S OFFLINE GATE PENDING — CLOSED LOOP NOT AUTHORIZED YET.**
