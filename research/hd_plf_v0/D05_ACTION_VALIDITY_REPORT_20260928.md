# HD-PLF D0.5 OPEN action-validity audit

Decision: **`HD_PLF_V0_ACTION_PROXY_NOT_VALIDATED_IN_OPEN_D05`**. Do not start a
VGR campaign using this v0 action value. This does not reverse the historical
AOD B2 readout result, nor does it test a calibrated Native posterior policy.

## Frozen question and assets

The action rule is unchanged from `aa33846d`: each arm scores the same feasible
local goals using six source templates, their squared-cosine separation, and
the same `0.01/m` travel penalty. The D0.5 diagnostic contract was committed
at `30248f96` before action-validity scoring. A user clarification changed the
secondary outcome to **raw B2 SSE margin** with no posterior construction at
`2dff8248`. A float32-relative check of the stored 2×2 pooling was corrected
at `ed25f264`; the first VM run stopped at this asset parity check without
emitting or inspecting an action-validity result. The final contract SHA256 is
`d8f84e03b2d54d41ca6c7c6dd1e7bcbaddaa2f02c3f32963dcdf607ce34a86d5`.
No cost, radius, EPS, blur, source, target, or goal set
was selected from the outcome.

All 72 retained OPEN target cubes (3 environments × 6 sources × 4 realizations)
matched their historical SHA256 manifest. The retained 10×30 pooled target
tensor matched byte values, and physically projecting each full cube onto the
30 frozen 2×2 probes had a maximum scaled discrepancy of `1.16e-7`
(maximum absolute `3.05e-5` ppm, consistent with float32 reduction). No plume,
PMFS forward, model training, House03 asset, or VGR run was created.

For each episode the anchor is the first strictly positive frozen probe at
snapshots 0–8, scanning time and then probe rank. It is an observed OPEN
concentration, not a truth-selected point. At the next stored snapshot, the
full target cube supplies a counterfactual 0.20 m square observation at **all**
geometry-feasible local goals. The action selector sees neither these future
values nor the truth source. All 72 episodes yielded at least two local goals;
there were 1104 episode-goal evaluations, but the independent unit for this
diagnostic is the **episode/source**, not the individual goal.

The B2 evaluator fits a separate nonnegative gain for each of the same six
candidate sources using the one observed anchor reading, then with the goal
reading added. The primary outcome is truth-rank improvement; the secondary
outcome is the change in `[best wrong SSE - truth SSE]`. No SSE-to-posterior
temperature or probability normalization is introduced. Because one positive
reading can give multiple candidates exactly zero SSE after free gain fitting,
the pre-frozen tie-aware expected rank is reported alongside the exact
historical strict B2 rank (`1 + count(SSE_other < SSE_truth)`). Their within-
episode Spearman correlations happen to coincide in this run; both sets of
raw values are retained in the goal CSV.

## Association with observed identification gain

Each number below is the median of **within-episode** Spearman correlations
across feasible goals. `n` counts episodes with defined rank correlation;
constant gain vectors remain undefined and are not silently set to zero.

| OPEN environment | LF-u rank rho (n/24) | LF-rawu rank rho (n/24) | LF-u raw-margin rho | LF-rawu raw-margin rho | Paired median rawu−u rank rho |
|---|---:|---:|---:|---:|---:|
| H01 fast | +0.571 (16) | −0.011 (15) | +0.181 | +0.006 | −0.572 (15 paired) |
| H02 `3,5-1_slow` | +0.317 (24) | +0.457 (20) | +0.363 | +0.319 | +0.204 (20 paired) |
| H02 `4,5-3_slow` | +0.036 (18) | +0.439 (13) | +0.062 | +0.244 | +0.264 (12 paired) |

For the paired defined rank episodes, rawu exceeds u in 3/15, 15/20, and
12/12 episodes, respectively. This is a House-dependent pattern, not a stable
cross-House AOD action benefit. Six-source medians are also heterogeneous:
H01 rawu has negative median rank correlation at sources 0 and 3, near zero at
source 1, positive at source 5, and undefined at sources 2 and 4. H02 W0 has
positive rawu source medians for five evaluable sources; H02 W2 has positive
medians for four, with two undefined.

Positive correlation does not guarantee that the chosen maximum-action goal
beats a typical feasible goal. The selected LF-rawu goal has **strictly higher
rank improvement than the within-episode median goal** in only 7/24 H01,
8/24 H02 W0, and 1/24 H02 W2 episodes. The selected goal is different between
the two arms in 24/24, 16/24, and 16/24 episodes, respectively. The readout
therefore confirms that the template channel changes action, while its
selected-action benefit is not established.

## Interpretation and limits

The v0 squared-cosine proxy is not a consistently reliable predictor of
observation-grounded B2 source discrimination across the two OPEN Houses.
House02 has a conditional positive association for rawu, so this result is
**not** an AOD representation failure. It also does not license VGR: this
audit uses uniform six-source weights because no cycle-aligned Native
`sourceProbability` exists for these retained targets, and the full legal
596/630-source action axis is not available here. The anchor is a real frozen
probe hit but not a recorded single-UAV stop; the next-snapshot goal readings
come from the spatial cube, not an executed VGR path. Its exact probe center
can be up to one coarse-cell half-width from the memory cell center used by
the current action implementation. Ten archived snapshots cannot reproduce
continuous VGR acquisition timing.

The v0 action function remains unchanged. Stop this D0.5 audit here. A future
B2-consistent expected-evidence utility would be a **new predeclared action
rule**, not a rescue fit to these OPEN outcomes. The historical AOD readout
and Native source probability call chain keep their original status.

## Reproducibility

- Result: `evidence/hd_plf_v0/action_validity_d05/D05_RESULT.json`, SHA256
  `baa871f020703f2d05e9dc1d71d036511c5d61ef5a00bc88ab31b643781f1e10`.
- All goals: `evidence/hd_plf_v0/action_validity_d05/GOAL_COUNTERFACTUALS.csv`,
  SHA256 `66a9a2e3f7244f88ed30d706bbab4a4abf26bf0757e83a460317241befb59c1f`.
- Both outputs were byte-identical on a complete second VM traversal.
- The original tie-aware result before adding the exact archived-rank columns
  is separately preserved as `*_INITIAL_TIE_AWARE.*`.
- 15 HD-PLF/D0.5 unit tests and 8 frozen local-memory tests pass.
