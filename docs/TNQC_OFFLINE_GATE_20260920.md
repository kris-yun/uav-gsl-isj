# TNQC offline evidence gate — VGR first
Date: 2026-09-20

## Claim boundary

The project data are authoritative. The current status is:

- **VGR/GADEN House mechanism signal: positive.**
- **Full 300-s VGR localization gate: pending.**
- **Planner-coupled closed loop: HOLD until the 300-s gate returns GO.**

The public Orebro experiment is retained only as an external falsification appendix. It is not used to authorize closed loop.

Main candidate: **Transport-Nuisance Quotient Canonicalization (TNQC)**.

---

## 1. VGR/GADEN mechanism screen on the project archive

Data are read from the frozen historical project branch:

```
ref:  project/research-master-20260914
sha:  26e89a99532e4268c5022dca2e938bf1473377b1
root: evidence/cstar_current_runtime_assets240_20260907/realizations
```

Design:

- House01 / House02 / House03;
- two source locations per House, SA/SB;
- fast / slow transport condition;
- 12 histories total;
- 1200 samples per history;
- 0.2 s sampling, ending at 240 s;
- all SA/SB × fast/slow histories within one House use the same geometry-only pose sequence.

This is a fixed-route **mechanism** test. It is not the final PMFS localization endpoint.

### Spatial alignment to the actual PMFS grid

The old VGR route-order proxy has been superseded. The current probe bins `pose_xy + gas_ppm` onto the same reduced PMFS grid used by the native benchmark.

Historical native PMFS logs give:

| House | raw map resolution | PMFS scale | reduced cell | map origin |
|---|---:|---:|---:|---|
| H01 | 0.1 m | 3 | 0.3 m | (-7.55, -7.88) |
| H02 | 0.1 m | 3 | 0.3 m | (-5.39, -7.45) |
| H03 | 0.1 m | 3 | 0.3 m | (-0.85, -1.86) |

At 240 s the common route covers about 228 / 227 / 232 PMFS bins in H01/H02/H03, with 252 / 252 / 251 structural 4-neighbour spatial edges.

Thus the auxiliary order channel is now evaluated on **spatially adjacent PMFS cells**, not adjacent timestamps.

Reproduction:

```bash
python3 reference/tnqc_vgr_offline_240s.py \
  --json-out /tmp/tnqc_vgr_240s_spatial.json
```

Frozen record:

`evidence/TNQC_VGR_240S_SPATIAL_MECHANISM_20260920.json`

---

## 2. Main quotient

For an observed logit field (x), candidate-predicted field (y_s), and confidence weights (w_i),

[
mu_w(x)=rac{sum_iw_ix_i}{sum_iw_i},
]

[
q_{m aff}(x,y_s)=
rac{sum_iw_i(x_i-mu_w(x))(y_{s,i}-mu_w(y_s))}
{sqrt{sum_iw_i(x_i-mu_w(x))^2}
 sqrt{sum_iw_i(y_{s,i}-mu_w(y_s))^2}}.
]

For independent positive-affine nuisance actions

[
x'=a x+b{f 1},qquad y'_s=c y_s+d{f 1},qquad a,c>0,
]

[
q_{m aff}(x',y'_s)=q_{m aff}(x,y_s)
]

exactly.

The candidate prediction remains PMFS transport-conditioned. The quotient removes non-identifying global amplitude/background coordinates; it does not claim that wind is a global affine nuisance.

---

## 3. VGR result

Cross-transport source identification compares each fast history with the two slow source templates, and vice versa. Source truth is used only for the final accuracy/error calculation.

| accumulated VGR history | raw | affine quotient | local spatial order | old equal fusion | hierarchy-guarded |
|---|---:|---:|---:|---:|---:|
| 60 s | 8/12 | 8/12 | 8/12 | 8/12 | 8/12 |
| 120 s | 8/12 | 8/12 | 8/12 | 8/12 | 8/12 |
| 180 s | 12/12 | 10/12 | 9/12 | 9/12 | 10/12 |
| **240 s** | **12/12** | **12/12** | **11/12** | **11/12** | **12/12** |

The nominal 240-s result does **not** show an advantage over raw amplitude; raw is also 12/12. The positive scientific signal is nuisance robustness below.

### Source-blind positive-scale stress

Each episode is independently multiplied by a positive factor drawn log-uniformly from [0.1, 10], using only episode ID + deterministic stress seed. Across 100 stress seeds:

| representation | mean accuracy | min | perfect runs |
|---|---:|---:|---:|
| raw | 0.8333 | 0.8333 | 0/100 |
| **affine quotient** | **1.0000** | **1.0000** | **100/100** |
| local spatial order | 0.9167 | 0.9167 | 0/100 |
| old equal fusion | 0.9167 | 0.9167 | 0/100 |
| **hierarchy-guarded** | **1.0000** | **1.0000** | **100/100** |

This stress corresponds directly to the exact positive-scale nuisance removed by the main quotient.

### Source-blind monotone compression stress

Each episode receives an independent strictly increasing compressive response
(g(c)=log(1+alpha c)/alpha), with (alpha) assigned without source truth. Across 200 seeds:

| representation | mean accuracy | min | max | perfect runs |
|---|---:|---:|---:|---:|
| raw | 0.7833 | 0.6667 | 0.9167 | 0/200 |
| **affine quotient** | **1.0000** | **1.0000** | **1.0000** | **200/200** |
| local spatial order | 0.9167 | 0.9167 | 0.9167 | 0/200 |
| old equal fusion | 0.9167 | 0.9167 | 0.9167 | 0/200 |
| **hierarchy-guarded** | **1.0000** | **1.0000** | **1.0000** | **200/200** |

The affine quotient is not mathematically invariant to arbitrary nonlinear monotone transforms; its 200/200 result here is an empirical VGR robustness observation, not an invariance claim.

---

## 4. Secondary innovation was falsified and repaired before the 300-s House gate

The original unconditional 1:1 fusion is **rejected**.

The falsifying case is H02 / fast / source SA at 240 s:

[
q_{m aff}(SA)=-0.02142,quad q_{m aff}(SB)=-0.03821,
]

so the exact affine quotient correctly selects SA. But

[
q_{m ord}(SA)=0.75758,quad q_{m ord}(SB)=0.87879,
]

and unconditional averaging flips the result to SB.

This is scientifically useful: a broader symmetry quotient discards more information and must not be allowed to override a more physically exact quotient.

### Symmetry-Hierarchy Consistency Guard

The repaired auxiliary has no learned coefficient and no fitted threshold:

[
e_s=
egin{cases}
rac12(q_{m aff}(s)+q_{m ord}(s)),
& |E_s|ge2 	ext{ and }q_{m aff}(s)q_{m ord}(s)ge0,\
q_{m aff}(s),&	ext{otherwise}.
end{cases}
]

Interpretation:

- (q_{m aff}) is the privileged exact physical quotient;
- (q_{m ord}) is a broader monotone-invariant corroboration channel;
- the broader channel may reinforce the exact quotient only when directionally consistent;
- disagreement triggers analytic fallback, not learned arbitration.

On the frozen VGR screen this restores 12/12 at 240 s and remains 12/12 in all 100 scale-stress and 200 monotone-stress runs.

This guarded equation is now implemented identically in:

- `ros2_package/src/gsl_server/algorithms/PMFS/internal/TNQCScore.hpp`;
- `reference/tnqc_vgr_fixed_trajectory_replay.py`;
- `ros2_package/test/test_tnqc_score.cpp`.

---

## 5. External Orebro result is auxiliary only

The earlier Orebro3DSEN repeated-source experiment remains useful as an independent sensor-array falsification. It showed that quotient/canonical spatial information can persist under release/fan changes while raw amplitude is weak. It does **not** measure the project's 300-s localization endpoint and is not part of the GO rule.

Reproduction remains:

```bash
python3 reference/tnqc_orebro_offline.py --window-minutes 5
```

Do not substitute its AUC/LOCO metrics for House localization error.

---

## 6. Authoritative next gate: fixed-trajectory VGR 300 s localization

The project-level offline gate is:

```bash
python3 reference/test_tnqc_vgr_fixed_trajectory_replay.py
bash reference/run_tnqc_vgr_offline_gate_20260920.sh
```

For House01/02/03 × seed0/1 the driver:

1. runs native PMFS to the full 300-s budget;
2. exports the exact native trajectory and PMFS candidate/context bank;
3. reconstructs the native posterior and requires a cell-wise audit to pass;
4. reweights the same frozen candidate bank with the guarded TNQC equation;
5. evaluates the final PMFS top-5% expected-location error;
6. aggregates the six paired cases.

Closed-loop GO requires:

- pooled final error reduction >= 10%;
- >=4/6 paired cases improve;
- no pair degrades by >25%;
- no false confident collapse;
- all native posterior reconstruction audits pass.

Until the resulting `tnqc_vgr_300s_offline_gate.json` contains
`"go_for_closed_loop": true`, planner-coupled TNQC remains on HOLD.

---

## 7. Current status

The VGR project data now support the **mechanism**:

- exact affine quotient: survives the frozen spatial cross-transport screen and exact scale nuisance;
- unconditional broad-symmetry fusion: falsified;
- symmetry-hierarchy guard: survives the corrected VGR screen without a fitted parameter.

They do **not yet** establish final 300-s localization improvement.

**Status: VGR MECHANISM POSITIVE / VGR 300-S LOCALIZATION GATE PENDING / CLOSED LOOP HOLD.**
