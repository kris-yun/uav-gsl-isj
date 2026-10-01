# P3T-D0 — Controlled Gaussian-support test for source evidence

Date: 2026-10-01
State: **FINAL PRE-REGISTRATION / NO SCIENTIFIC EXECUTION YET**

Parent result: \`PMFS3D_R1P5_HOLD_PARTIAL_SELECTIVITY\`.

## 1. Scientific question

R1/R1P5 established two facts that must be separated:

1. retained 3-D transport changes many false-source scores;
2. it produces exactly zero true-source score gain in all four frozen cases.

The R1 Oracle-3D observation operator is extremely sparse: a point filament contributes only when its center occupies the relevant PMFS xy cell and the sensor z-layer. Historical GADEN/Gaden-RT instead models a filament as a continuous 3-D Gaussian concentration distribution.

D0 asks two ordered questions:

### Q1 — support-restoration question

Does replacing point support by the physically grounded Gaussian support create positive evidence at the true source?

### Q2 — 3-D-specific question

If positive evidence is restored, is the gain materially larger/better when the same Gaussian observation operator is driven by 3-D transport trajectories rather than the collapsed 2-D trajectories?

Q2 is required because a Gaussian kernel can improve overlap merely by smoothing. A D0 result cannot be used to support the 3-D world-model thesis unless the 3-D arm is distinguished from the matched 2-D Gaussian control.

This is still a representation kill test. It is not world-model training.

## 2. Frozen cases and inputs

Exactly the four historical R1 terminal cases:

- House01_seed0_off_off
- House01_seed1_off_off
- House02_seed0_off_off
- House02_seed1_off_off

Preserve:
- active candidate leaves and source ownership;
- measured hit-probability/confidence maps;
- Oracle-2D and Oracle-3D transport centers;
- state0 CFD contract;
- occupancy/geometry;
- source height convention;
- deterministic source draws and transport keys;
- PMFS likelihood and posterior normalization.

No H03.
No confirmation.
No new GADEN plume.
No new trajectory seed.
No training.
No closed loop.

## 3. Four arms

### P2 — frozen Oracle-2D Point

Read the completed R1 Oracle-2D score/maps. No new computation except integrity checks.

### P3 — frozen Oracle-3D Point

Read the completed R1 Oracle-3D score/maps. No new computation except integrity checks.

### G2 — Oracle-2D Gaussian support control

Use the exact frozen Oracle-2D filament center trajectories.

The 2-D transport state has no resolved z coordinate. For the Gaussian observation calculation, embed its center trajectory on the frozen PMFS sensor plane. This is an intentionally optimistic 2-D support control: it asks whether continuous support alone, without retained vertical/path state, can explain the gain.

Use the same Gaussian mass, diffusion schedule, sensor-query positions, gas-detection threshold and PMFS likelihood as G3.

No parameter may be separately selected for G2.

### G3 — Oracle-3D Gaussian support

Use the exact frozen Oracle-3D xyz filament-center trajectories.

Use exactly the same Gaussian physical parameters and observation operator as G2.

The G2-vs-G3 difference is therefore the retained transport state/path, not a different smoothing width or scorer.

## 4. Gaussian concentration semantics

A GADEN filament is a continuous gas-concentration distribution, not a random point-membership probability.

For every frozen query location x_i and timestep t:

\[
C_{i,t}=\sum_k C_k(x_i;\mu_{k,t},\Sigma_{k,t},m_f)
\]

using the historical GADEN/Gaden-RT concentration equation.

The physical parameters must be recovered from historical configuration/provenance:

- filament mass or equivalent released mass convention;
- diffusion/growth schedule defining Sigma;
- gas-detection threshold used to create the PMFS hit/miss observations.

Convert concentration to a hit with the frozen threshold:

\[
h_{i,t}=\mathbf{1}[C_{i,t}\ge C_{\rm det}]
\]

and simulated hit probability:

\[
\hat H_i=\frac{1}{T}\sum_t h_{i,t}.
\]

Only on-demand concentration at the frozen PMFS query locations is required. Do not build a dense 3-D concentration volume.

If a unique compatible physical parameter set cannot be recovered before truth evaluation:
\`P3T_D0_INVALID_STOP\`.

Do not tune sigma, mass or threshold against rank, truth or margin.

## 5. Pre-scoring integrity/software gates

All must pass before truth is opened:

1. P2/P3 reproduce frozen R1 scores, ranks and maps.
2. G2 and G3 use identical Gaussian mass/diffusion/threshold parameters.
3. G2 and G3 use the correct corresponding frozen center trajectories.
4. Gaussian concentration is independently checked against the historical GADEN/Gaden-RT equation on deterministic synthetic probes.
5. Tiny-covariance synthetic behavior is qualitatively consistent with point support; do not claim byte equivalence to R1 collision semantics.
6. measured PMFS maps and likelihood code are unchanged.
7. no truth coordinate enters parameter selection.
8. deterministic repeat passes.
9. all input/code/config hashes are frozen before scientific scoring.

Any failure -> \`P3T_D0_INVALID_STOP\`.

## 6. Gate A — does physical Gaussian support restore true-source evidence?

Compare G3 against P3.

\`GAUSSIAN_SUPPORT_RESTORED\` requires:

- G3 truth log score > P3 truth log score in at least 3/4 cases;
- G3 has nonzero concentration support at at least one confident observation cell for the truth in at least 3/4 cases;
- truth-tie count decreases versus P3 in at least 3/4 cases;
- truth rank improves in at least 3/4 cases;
- median active-leaf rank improvement >= 10;
- truth-vs-best-wrong margin improves in at least 3/4 cases;
- no more than one case has worse truth rank.

If truth log score improves in fewer than 3/4:
\`P3T_D0_NO_POSITIVE_TRUTH_SUPPORT_STOP\`.

If support/log-score improves but the rank/tie/margin gate fails:
\`P3T_D0_HOLD_SUPPORT_NOT_DISCRIMINATIVE\`.

## 7. Gate B — is the useful gain genuinely 3-D rather than Gaussian smoothing?

Run only as part of the same frozen analysis after Gate A metrics are available. Compare G3 against G2.

\`THREED_INCREMENT_PRESENT\` requires all:

- G3 truth-vs-best-wrong margin > G2 in at least 3/4 cases;
- median (G3 margin - G2 margin) > 0;
- median G3 truth rank <= median G2 truth rank;
- no more than one case has worse G3 truth rank than G2;
- at least one positive G3-vs-G2 margin case occurs in House01 and at least one in House02.

Interpretation:

- Gate A pass + Gate B pass:
  \`P3T_D0_3D_GAUSSIAN_SOURCE_EVIDENCE_PASS\`
- Gate A pass + Gate B fail:
  \`P3T_D0_GAUSSIAN_ONLY_HOLD\`
  meaning continuous support matters, but D0 does not yet justify a 3-D world-state contribution.
- Gate A fail:
  use the Gate-A STOP/HOLD result above.
- integrity/provenance fail:
  \`P3T_D0_INVALID_STOP\`.

No result is yet a paper-level main-innovation PASS.

## 8. Required diagnostics

For every case and all four arms report:

- truth log score;
- truth midrank and pessimistic rank;
- truth-vs-best-wrong margin;
- equal-score wrong-leaf count;
- confident observation cells with nonzero truth concentration/support;
- truth-template total hit support;
- source-map entropy;
- top-5 candidate IDs.

For G2/G3 also report:

- continuous truth concentration at confident cells before thresholding;
- active Gaussian/filament count;
- on-demand query count;
- runtime and peak memory;
- equivalent dense-volume size for reference only.

Report pairwise deltas:

- G3-P3;
- G2-P2;
- G3-G2.

## 9. R1P5 interaction

R1P5 showed broad false-source suppression but failed cross-seed stability because H01 suppression was unstable.

Therefore:
- do not implement counterexample/hypothesis elimination in D0;
- do not reuse R1P5 pairwise suppression as a score;
- do not let false-source suppression rescue Gate A;
- positive truth evidence is mandatory.

## 10. STOP boundary

After the D0 decision and independent audit: **STOP**.

Only \`P3T_D0_3D_GAUSSIAN_SOURCE_EVIDENCE_PASS\` authorizes D1 design for a persistent/task-sufficient 3-D transport state.

\`P3T_D0_GAUSSIAN_ONLY_HOLD\` authorizes only a representation review: determine whether the main opportunity is a better continuous observation model rather than persistent 3-D state.

No outcome authorizes:
- neural world-model training in the same run;
- H03/confirmation;
- new GADEN plume generation;
- ROS/300 s closed loop;
- real flight.
