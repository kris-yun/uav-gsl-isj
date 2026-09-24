# Source-Lineage Lagrangian Plume Operator v2 — Scientific Charter

Date: 2026-09-24
Branch: `research/source-lineage-lagrangian-v2`
Status: **CANDIDATE — FILAMENT L1 REQUIRED BEFORE ANY CLOSED LOOP**

## 1. Failure mechanism being solved

The frozen M4 sequence established that:
- wind information is present and characteristic transport materially drives the response;
- bulk displacement / response amplitude can be approximately correct;
- nevertheless source-conditioned absolute transport geometry is wrong;
- improving field MSE or generic memory does not reliably restore truth-source rank;
- the same wind intervention produces strongly source-dependent plume changes.

Working diagnosis:

> the projected 2-D concentration field destroys source-to-path lineage. A reusable transport law cannot be closed on a single scalar concentration slice.

The state must therefore carry transport-path information explicitly.

## 2. Main scientific idea

Represent each source hypothesis as a compact Lagrangian Gaussian measure

[
Z_s(t)={(mu_i(t),Sigma_i(t),w_i(t),a_i(t))}_{i=1}^{K},
]

where particles/atoms preserve:
- 3-D position (mu_i);
- filament scale / anisotropy (Sigma_i);
- weight (w_i);
- age / lineage state (a_i).

Source identity is NOT an input to the transport network.

The source enters only by injection:

[
Z_s(t^+) = Z_s(t^-)oplus B(s).
]

A single reusable transport operator acts on all candidates:

[
Z_s(t+Delta t)=
mathcal T_	hetaig(Z_s(t),hat W_t,Oig).
]

This preserves the M4 compositional principle but changes the state space from
an Eulerian scalar field to a lineage-bearing Lagrangian measure.

## 3. 2026 parent theory

Primary external anchor:
**Gaussian Particle Operator (ICML 2026), _From Basis to Basis: Gaussian Particle Representation for Interpretable PDE Operators_.**

Relevant transferable ideas:
- Gaussian particles as the primary state representation;
- explicit centers/scales/weights;
- mesh-agnostic compact representation;
- localized/high-frequency structures;
- irregular geometry;
- native 2-D to 3-D extension;
- near-linear cost for fixed modal budget.

This project must NOT claim Gaussian particles or particle operators themselves as novel.

Target novelty, only if validated:

> source-lineage Gaussian/Lagrangian transport used as the candidate forward state for probabilistic gas-source localization, with source injection separated from a reusable wind/geometry transport operator and the resulting path consistency used in PMFS source ranking.

## 4. Auxiliary modules if the main mechanism survives

### A. 3-D sensor-plane observation operator

Map the 3-D particle measure to the UAV gas sensor likelihood at its pose:

[
p(y_tmid s)=mathcal O_{phi}(Z_s(t),x_t^{UAV},h_t).
]

This module handles:
- vertical transport / particles leaving the sensing plane;
- filament scale and sensor footprint;
- frozen sensor response dynamics.

It may use estimated wind but never future/oracle wind in deployment mode.

### B. Path-consistency likelihood

Do not rank source candidates only by field residual.

For each candidate, combine gas-observation fit with transport-path consistency:

[
log p(smid y_{1:t}) propto
log p(y_{1:t}mid Z_s)
-lambda E_{m path}(Z_s,mathcal H_t)
+log p_{t-1}(s).
]

The path term penalizes candidates requiring implausibly large/non-smooth
trajectory corrections to explain observed gas history.

This is motivated by the existing House02 result that truth rank can improve
when absolute plume-path correction cost is scored explicitly, whereas pure
field MSE remains confounded by nearby false sources.

## 5. Filament L1 — decisive necessary-condition test

House02 remains development-only.

Raw GADEN filament snapshots are required. Do not substitute concentration maps.

Training combinations:
- S1-W1 A/B
- S2-W1 A/B
- S1-W2 A/B

Held out:
- S2-W2 A/B

### L1-A: snapshot integrity

Export each `iteration_*` snapshot as [x,y,z,sigma].
Reconstruct age/lineage from the monotonic filament sigma schedule and creation order.

Required:
- parser integrity on all selected snapshots;
- finite values;
- monotonic age reconstruction;
- >=95% adjacent-snapshot survivor linkage where a successor is physically present.

Failure: **STOP SOURCE-LINEAGE L1**.

### L1-B: source-agnostic transition transfer

Fit ONE transition law on the three training combinations only.

Inputs may include:
- current 3-D filament state;
- filament age/sigma;
- current local 3-D wind;
- local occupancy/boundary context.

Forbidden:
- source ID;
- source coordinates as a model feature;
- S2-W2 target fields;
- future wind;
- true concentration target during transition fitting.

Evaluate on S2-W2 A/B.

Two gates are separated to prevent overclaiming.

**State gate** (3-D lineage state vs matched 2-D particle baseline), BOTH A/B:
1. mean next-plume-centroid trajectory error improves by >=25%;
2. held-out transport-direction cosine >0.5.

**Operator gate** (learned source-agnostic transition vs deterministic 3-D physics), BOTH A/B:
1. mean next-centroid error improves by >=10%;
2. filament XY displacement RMSE improves by >=10%;
3. held-out transport-direction cosine >0.5;
4. destroying lineage successor correspondence makes centroid error >=10% worse.

Decisions:
- state FAIL -> **STOP PARTICLE/LAGRANGIAN MAINLINE**;
- state PASS + operator FAIL -> **STATE REPRESENTATION SIGNAL ONLY; LEARNED OPERATOR NO-GO**;
- state PASS + operator PASS -> **L1 OPERATOR PASS**, which alone authorizes L2.

This distinction prevents claiming a neural/learned operator innovation if ordinary 3-D particle physics already explains the gain.

## 6. L2 — inverse source test before ROS

After L1 passes, freeze transition, atom count, observation projection and likelihood.

Run a >=20-candidate source bank on the already-open House02 development data.

Primary endpoint:
**truth-source rank**.

Required:
- truth rank 1 in both plume realizations under the frozen probe/trajectory budget;
- improvement over Native PMFS/M4 candidate ranking;
- source-label permutation destroys the gain;
- no oracle source position or target concentration used at inference.

Only then generate/open fresh House01/House03 confirmation.

## 7. Real-world constraint

Deployment state is causal:

[
Z_s(t+Delta t)=mathcal T_	heta(Z_s(t),hat W_t,O)
]

using current/past estimated wind only.

Hundreds of candidate sources must share the same transport operator and be batched.
No candidate-specific neural network is allowed.

The final output remains the PMFS-style source probability map.

## 8. Stop rule

Do not:
- revive M4-v3 as a complete model;
- add more memory/residual CNNs to rescue concentration-space geometry;
- use field MSE as the decisive endpoint;
- enter ROS/closed loop before L1 and L2 both pass.

Current next action:
**export the existing House02 raw GADEN filament snapshots and run L1.**


## 9. Frozen raw-bank availability and exact generator contract

No new GADEN generation is required for L1.

The eight raw filament realizations already exist on the VM under:

`/home/zyc/c0_5_real_gaden_bank_20260923/{CELL}/realization/iteration_*`

Cells:
- S1_W1_A/B
- S1_W2_A/B
- S2_W1_A/B
- S2_W2_A/B

Each cell has exactly 566 saved snapshots.

Frozen generator:
- binary SHA-256: `4127b9ba4f42186ba2d6d33c84fba8d4b92749da59b83750fa4847dbd9957ce1`;
- simulation dt: 0.1 s;
- save dt: 0.5 s;
- emission rate: 7 filaments/s;
- initial sigma: 10;
- growth gamma: 15;
- filament noise std parameter: 0.01;
- W1/W2 canonical House02 winds;
- source z: 0.20 m.

Important wrapper audit:
the historical ROS parameters `variable_rate=true` and `filament_stop_steps=0`
are not consumed when this frozen wrapper builds `RunningSimulation::Parameters`.
The effective emission law is therefore the core float32
`releaseAccumulator += 7*0.1` rule.

Snapshot indices are save counters, not physical 0.5-s multiples.
The exact first save simulation steps are:
`0, 6, 11, 16, 22, 28, 34, ...`
and save index 565 is simulation step 2998 at about 299.809082 s.
The exporter emulates this float32 strict-'>' timing contract.

This contract is frozen before L1.
