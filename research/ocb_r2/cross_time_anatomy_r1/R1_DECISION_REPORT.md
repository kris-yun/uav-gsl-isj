# OCB-R2 R1 cross-time memory anatomy decision

**Decision: `OCB_R2_R1_BROAD_MEMORY_REQUIRED`.** This is a discovery-only mechanism label, not a localization method result or a claim that a full trajectory model is necessary.

## Contract and provenance

- Source protocol: `OCB_R2_CROSS_TIME_MEMORY_ANATOMY_R1.md`, source commit `a715dd2f198a0f55e2cef78c3b017ef97319a733`.
- Parent mechanism: R0 `OCB_R2_MECH_CROSS_TIME_STABLE`, evidence commit `c7b52bb969f8d48ffdbf87016574c00f1dd0cdae`.
- R0 input parity: 9 contract/metadata files and all 64 binary discovery tensors matched the R0 SHA256 freeze. No target was extracted again.
- Each target was compared only with the alternative source under the same House, wind, gas, occupancy and observation contract. Truth references used the other three realizations; the alternative used a 3-of-4 reference bank. All four alternative omissions were evaluated.
- Scores: the R0 fair-U Energy Score on 60-D lagged pairs or complete 300-D trajectories. There were 1000 surrogate draws per candidate/reference view with the preregistered seed families.
- Recomputed B1 and B10 source margins matched the frozen R0 target effects exactly (maximum absolute difference 0). Lag snapshot and block preservation assertions passed. Two complete scoring passes were byte-identical in every scientific output.

## Lag spectrum

The table reports median source×context group increments `I_LAG`; each House has eight groups. Pairwise time positions were averaged inside a target and were never treated as independent targets.

| Lag | House01 | House02 | Positive groups /16 | Positive contexts /8 |
|---:|---:|---:|---:|---:|
| 1 | 0.016868 | 0.018164 | 16 | 8 |
| 2 | 0.009330 | 0.007887 | 15 | 8 |
| 3 | 0.009302 | 0.005722 | 16 | 8 |
| 4 | 0.006097 | 0.005979 | 11 | 6 |
| 5 | 0.002725 | 0.005128 | 12 | 6 |
| 6 | -0.000427 | 0.003647 | 8 | 4 |
| 7 | -0.004135 | 0.007216 | 8 | 3 |
| 8 | -0.000541 | 0.003205 | 6 | 3 |
| 9 | 0.000000 | 0.000000 | 4 | 4 |

Lag 3 independently satisfies the broad-memory branch: both House medians are positive and all 16 group means are positive. For alternative reference omissions 1–4, lag-3 positive group counts are **13, 15, 12, 15** and both House medians remain positive in every case. Thus the broad-memory label does not depend on one omitted reference or one context. Lag 1 is also positive in all 16 primary groups; this does not satisfy the short-memory label because its block-recovery condition fails.

## Block preservation

House medians of source×context group recovery fractions, relative to the R0 B1-to-B10 increment:

| House | B2 | B5 |
|---|---:|---:|
| House01 | 0.250180 | 0.557211 |
| House02 | 0.161643 | 0.741679 |

B2 is below the frozen 2/3 short-memory threshold in both Houses. B5 crosses 2/3 in House02 but not House01; therefore the separate B5-based broad-memory branch is **not** established. The label rests on the robust lag-3 branch. In one alternative-reference omission, a group R0 denominator is nonpositive, so a House-level block-recovery median is undefined; it was not clipped or converted into a favorable number. This does not affect the lag-3 branch.

## Boundary

The evidence supports source-relevant dependence beyond adjacent two-slot structure under this fixed 10-slot, two-source-per-context discovery contract. It does **not** establish a unique memory horizon, a calibrated source posterior, full-map localization performance, whole-path necessity, or held-out confirmation. Confirmation data and House03 remained sealed. No GADEN, PMFS forward, network training, closed loop, or literature search was run.

Detailed target, group, context, reference-omission, preservation and repeat records are under `evidence/ocb_r2/cross_time_anatomy_r1/`.
