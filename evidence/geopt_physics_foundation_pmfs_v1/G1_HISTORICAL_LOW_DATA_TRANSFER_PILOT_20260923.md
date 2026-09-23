# G1 Historical Low-Data Transfer Pilot — GeoPT for PMFS

Date: 2026-09-23  
Branch: \`research/geopt-physics-foundation-pmfs-v1\`  
Status: **READY AFTER G0.5-B ACTUAL CHECKPOINT LOAD**

## 1. Purpose

Test the only novelty claim that still matters for M6:

> Does cross-physics GeoPT pretraining provide a useful low-data representation for gas-dispersion/source-conditioned forward prediction?

This pilot uses existing controlled historical VGR/GADEN fixed-route data so that no new plume generation is required.

It is a mechanism screen, not the final PMFS benchmark.

## 2. Data

Historical controlled branch:

\`project/research-master-20260914\`

Asset:

\`evidence/cstar_current_runtime_assets240_20260907/realizations\`

Design:

- H01/H02/H03;
- SA/SB;
- fast/slow transport;
- identical route/timing within each House;
- source-invariant wind within a transport condition.

Use gas values averaged onto the PMFS 0.3-m grid at 240 s.

Optional harder stress:
- repeat at 120 s after the 240-s implementation is frozen.

Do not tune model choices using source identity.

## 3. GeoPT environment token

For every free/path grid cell:

### Separate coordinate input

\[
x=[x,y,z].
\]

### 11-D physical feature input

\[
fx=
[x,y,z,d_{\rm wall},n_x,n_y,n_z,
\hat w_x,\hat w_y,\hat w_z,\|w\|].
\]

Geometry:
- use the actual House occupancy grid;
- compute nearest-wall distance + direction exactly as in the G0.5 feature builder.

Wind:
- for the historical fixed-route pilot, use the recorded wind vector at each PMFS bin;
- aggregate repeated observations by the same fixed averaging rule as gas.

This pilot does not use the historical R2 GMRF context-bank wind.

## 4. Candidate-source adapter

Do **not** change GeoPT's pretrained raw input dimension.

For candidate source \(s\), construct:

\[
r_s(x)=
[
x-s,\;
\|x-s\|,
\;Q_s(x)
].
\]

For the 2-D pilot:

\[
Q_s(x)
=
\exp
\left(
-\frac{\|x-s\|^2}{2\sigma_Q^2}
\right)
\]

with the predeclared:

\[
\sigma_Q=0.3\,\text{m}
\]

equal to one reduced PMFS grid cell.

Adapter:

\[
4\rightarrow64\rightarrow256.
\]

Inject after GeoPT's pretrained input projection and before the first Transolver block.

Do not search adapter width/position using held-out truth.

## 5. Output

Replace only the task head.

Predict:

\[
\log(1+c(x))
\]

for every queried PMFS path cell.

Output head:
- 256 → 1.

No source posterior is used for training.

## 6. Four controls

### G1-P — pretrained frozen
- load official \`GeoPT_8layers.pt\`;
- freeze all GeoPT backbone parameters;
- train only source adapter + scalar gas head.

### G1-RF — random frozen
- same exact architecture;
- random backbone initialization;
- freeze backbone;
- train the same adapter + head.

Tests whether pretrained features contain transferable information.

### G1-S — from scratch
- same exact GeoPT/Transolver architecture;
- train full model from random initialization on the same gas data.

Tests whether pretraining improves low-data efficiency over task-specific learning.

### G1-L — lightweight non-foundation control
Use the already-defined matched-capacity 28-feature ridge model.

This prevents a large network from receiving credit merely for capacity.

## 7. Held-out source×wind cross-validation

For each House, four folds:

- train three of:
  - SA-fast;
  - SA-slow;
  - SB-fast;
  - SB-slow;
- hold out the fourth combination.

Total:

\[
3\text{ Houses}\times4\text{ folds}=12
\]

held-out tests.

No held-out gas values may enter:
- normalization statistics;
- early stopping;
- hyperparameter selection.

## 8. Low-data curve

Within the three training combinations, use source-blind spatial hashing to retain:

- 10%;
- 25%;
- 50%;
- 100%

of training PMFS bins.

Use the exact same selected bins for all model arms.

This is the central foundation-model test.

## 9. Training contract

Predeclare:
- optimizer;
- LR;
- epochs;
- early-stopping rule based only on an internal source-blind validation subset from training combinations;
- random seeds.

Run at least 3 training seeds per arm if training is stochastic.

Do not optimize these per House.

## 10. Source-blind metrics

Held-out combination:

- log-concentration RMSE;
- MAE;
- nonzero plume-bin RMSE;
- hit/miss log score under one fixed threshold;
- calibration diagnostic.

Foundation transfer should be most visible in the 10–25% data regime.

## 11. Source-identification diagnostic

After every model is frozen:

For the held-out wind condition, predict fields for both candidate sources:

\[
\hat C_{SA,W},
\qquad
\hat C_{SB,W}.
\]

Compare the held-out observed field against both predictions.

Report:
- correct source rank among 2;
- RMSE margin:
  \[
  \Delta=
  RMSE(\text{wrong source})
  -
  RMSE(\text{true source}).
  \]

The historical 240-s task is easy enough that simple controls can reach 12/12 source identity; therefore **margin and field error matter in this pilot**.

This does not replace the final multi-candidate PMFS truth-rank gate.

## 12. G1 hard success condition

M6 gets a real positive transfer signal only if:

1. pretrained frozen beats random frozen clearly;
2. pretrained model beats or reaches from-scratch performance with materially less gas data;
3. advantage is present in multiple Houses/folds;
4. wind/source destructive controls reduce the advantage.

An isolated 12/12 source-correct result is insufficient because the simple ridge control already achieves 12/12.

## 13. Destructive controls

### N1 — wind shuffle
Shuffle fast/slow wind feature maps within a House while preserving gas labels.

Pretrained transfer advantage should fall.

### N2 — source adapter label shuffle
Swap SA/SB source adapter inputs.

Source margin should collapse/reverse.

### N3 — random checkpoint
Already represented by G1-RF.

### N4 — geometry destruction
Permute wall-distance/direction features among free cells while keeping xyz/wind unchanged.

If GeoPT's advantage survives, the claimed geometry-dynamics transfer is suspect.

## 14. Escalation

If G1 is positive:

### G2
Run the same comparison on newly generated multi-source GADEN field slices.

### G3
Integrate candidate forward predictions into recovered Native PMFS replay.

Hard metric:
- truth-containing source-candidate rank across the full candidate bank.

If G1 is neutral/negative:
- demote M6 before expensive GADEN generation.

## 15. Current status

\`READY — WAITING ONLY FOR G0.5-B ACTUAL CHECKPOINT LOAD\`.
