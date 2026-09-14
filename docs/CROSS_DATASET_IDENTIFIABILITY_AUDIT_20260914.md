# Cross-dataset source-identifiability audit

Date: 2026-09-14

Branch: `codex/dual-uav-two-point-premise-20260913`

Audited HEAD: `5e15ccaaa8da5cfaf308a3f8771cfacbda8aea1d`

## Decision

```text
H03_IDENTIFIABILITY_CONTROL_SAFETY_PASS_BUT_LOCALIZATION_REPAIR_NO_GO
NO_GO_NO_UNSEEN_SEED
CROSS_DATASET_LOCALIZATION_CLAIM = NOT_AUTHORIZED
ONE_NEXT_MECHANISM = OBSERVATION_QUOTIENT_IDENTIFIABILITY_CERTIFICATE
OCTREE_OR_SPATIAL_MEMORY = REPRESENTATION_OR_PLANNER_ABLATION_ONLY
```

The latest remote branch was fetched and the checkout was already up to date.
This audit did not run GADEN, read the unopened held wind, consume or regenerate
a protected response bank, or open an unseen seed.

## H03 development repair gate

The historical seed-12 comparison remains the binding failed House--seed:

| arm/policy | final error (m) | distance AUC (m s) |
|---|---:|---:|
| A0 | 7.646821 | 1439.630310 |
| M1R | 8.710182 | 1425.329580 |
| identifiability control: abstain to A0 | 7.646821 | 1439.630310 |

The control prevents the M1R endpoint regression by refusing unsupported
fine-source evidence.  Relative to M1R, final error improves by 1.063361 m but
AUC worsens by 14.300730 m s.  Relative to A0 it is an exact tie, not a strict
improvement.  It therefore passes a safety property but fails the required
localization-repair gate.  Per the frozen stop rule, no unseen seed was opened.

The source-evidence failure is not a posterior-only diagnosis.  At the final
instrumented update, the true-containing region ranked 29/85 and its separately
audited native posterior mass was `3.2793023375770594e-168`.  In the fixed-point
quadrature audit, at least 63 of 65 positive events had zero raw predicted
probability for every true-region point, while the strongest fixed false region
had at most three such zeros.  The final true-minus-fixed-false log-mixture
margin was `-348.218906` nats.  Reweighting or entropy reduction cannot create
the missing support.

The instrumented evidence is not an exact replay of the historical result.
Observation and pose sequences first differ at row 98, and the algorithm hashes
differ.  Its rank, mass and event-level conclusions remain
`NEW_INSTRUMENTED_DEVELOPMENT_REPLICATION`, not a historical causal attribution.

## Why the apparent alternatives do not supply new information

| candidate | necessary current-data fact | gate |
|---|---|---|
| transport-replicated/e-value evidence | H03 attribution has 85 candidates but one transport member | FAIL |
| local PDE source residual | 1,392 samples, 72 visited XY values, but zero timestamps with three simultaneous spatial points; no boundary flux or certified zero initial field | FAIL |
| persistent candidate transport provider | saved wind history is receiver-local only and has no causal full-GMRF field sequence; attribution still has one member | FAIL |
| exact cross-wind counterfactual ranking | ranks the true source first in 12/12 two-source cases, but calibrated commits are 0/12 and it is not an online full-map provider | RANKING ONLY |
| octree/spatial memory | PMFS uses a quadtree candidate support; SCIM explicitly records planner state without modifying `pi_map` and consumes the current posterior | ABLATION ONLY |

The prior physical gates agree with this audit: all 12 source-blind 150 s routes
failed; extending the response horizon to 222.8 s still gave 0/12; the 5 m
aperture had no feasible geometry among 24 starts; and observability-aware
learning failed its held condition.  The unopened held wind remains unread.

## Literature and collision audit

Only primary paper or publisher records were used for the following decisions.

| work | useful theoretical property | applicability/collision decision |
|---|---|---|
| Ojeda et al., *Robotic Gas Source Localization with Probabilistic Mapping and Online Dispersion Simulation*, IEEE T-RO 2024, DOI `10.1109/TRO.2024.3426368` | compare an observed gas map with online dispersion from every source candidate | Direct collision: a generic candidate-forward source score is already PMFS, not a new main innovation. |
| Ristic et al., *Bayesian likelihood-free localisation of a biochemical source using multiple dispersion models*, Signal Processing 2015, DOI `10.1016/j.sigpro.2014.08.023` | infer source with an entire observation vector while averaging structural dispersion uncertainty; evaluated on two experimental datasets | Direct collision: ordinary nuisance marginalization or likelihood-free Bayes is not the missing novelty. |
| Nanavati et al., *Mr.MSTE*, arXiv:2512.17001, 2025 preprint | multi-robot hybrid Bayesian multi-source density plus wind-aware coverage | High collision for broad multi-robot/wind-aware Bayesian claims; still assumes an informative measurement model. |
| Liu et al., *Sparse Sensor Allocation for Inverse Problems of Detecting Sparse Leaking Emission Sources*, IISE Transactions, online 2025 / vol. 58 (2026), DOI `10.1080/24725854.2025.2578523` | bilevel sensor placement under wind/forward-model uncertainty | High collision for generic observability-aware route/sensor design; our 12-route gate already falsified the available geometry-budget premise. |
| Gu et al., *Inverse source problem for the parabolic equation with sparse moving observations*, arXiv:2604.11157, 2026 preprint | uniqueness from one moving observation point | Not transferable: it observes boundary normal flux on a unit disc, assumes zero initial field and persistent source, and requires two boundary dwell intervals with an irrational angular relation. |
| Qiu and Yu, *Optimal-Transport Stability of Inverse Point-Source Problems for Elliptic and Parabolic Equations*, arXiv:2512.21821 / Inverse Problems 2026 | global OT stability by representing a dual potential with controllable adjoint solutions | Not transferable to the current trajectory: the bound uses boundary observations and explicit regularity/separation assumptions absent here. |
| Wu et al., *Overcoming Vanishing Gradients in Inverse Source Localization via Physically-Relaxed PINNs*, SSRN 6333518, 2026 preprint | explains source--sensor support non-overlap and relaxes the PDE during optimization | Useful diagnosis but not identification: artificial smoothing/dilation/nudging restores gradients, not measured source information. It is also a preprint, not top-journal evidence. |

The 2026 sparse-moving-observation paper is the closest new theoretical result,
but its theorem makes the missing measurement contract explicit rather than
repairing this dataset.  None of the checked work licenses ordinary Bayes,
another network, parameter search, posterior repair, or octree memory as a new
causal source-identification mechanism.

## One next mechanism and exact claim boundary

The only defensible next mechanism is an **observation-quotient
identifiability certificate**:

1. form local source-candidate edges from geometry;
2. declare an edge resolved only when source contrast replicates across
   transport members on the actually observed support;
3. merge unresolved edges into resolution cells;
4. project pre-Bayes evidence to the cell level, preserving prior odds within
   each unresolved cell;
5. abstain when the source cannot be resolved at the requested spatial scale.

This mechanism has the missing theoretical property: it cannot create
candidate-relative information inside an observational equivalence class.
Quadtree/octree is only an adaptive carrier for these cells.  The main paper
claim would have to be **cross-dataset certification of when localization is
identified**, not cross-dataset improvement of point localization.  The latter
claim remains NO-GO under the current measurements.

This certificate itself is still only a candidate main innovation.  It needs
validation on an external dataset with multiple transport replicates and known
source geometry before a cross-dataset claim is allowed.  Current project
assets cannot supply that untouched confirmation.

## Reproduction

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'
D:\Anaconda\python.exe -X utf8 experiments\cross_dataset_identifiability_audit_v1\audit.py `
  --out experiments\cross_dataset_identifiability_audit_v1\FINAL_AUDIT.json
```

The generated JSON binds all reused evidence and code inputs by SHA-256 and
records the development/repair/confirmation boundary explicitly.
