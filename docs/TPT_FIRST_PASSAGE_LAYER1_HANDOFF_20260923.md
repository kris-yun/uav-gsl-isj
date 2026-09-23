# PMFS backbone-preserving TPT / first-passage Layer-1 handoff

Date: 2026-09-23  
Branch: `research/multirun-candidate-replay-tpt-20260923`  
Status: **IMPLEMENTED, EXECUTION PENDING ON QUALIFIED ROS/GADEN VM**

## Scientific role

This is not a new posterior and not a closed-loop method.

It is the next mother-idea **necessary-phenomenon gate** after two 2026-09-23 failures:

- direct PMFS-local time-irreversibility transfer: NO-GO;
- biological kinetic-proofreading as source evidence: NO-GO.

Those negative audits are recorded on branch
`research/cross-domain-mother-idea-audits-20260923`.

The present line keeps the classical PMFS chassis:

- occupancy/grid representation;
- source probability map;
- quadtree source hypotheses;
- Native filament forward transport;
- planner / navigation interface.

It changes the scientific meaning of candidate evidence before any posterior is built.

## Exact information-loss target in Native PMFS

Current Native PMFS first simulates a source candidate into a 200-step hit map and then evaluates
`sourceProbFromMaps()`.

In `Simulations.cpp`, the Native score is a product over free cells. Each cell compares:

- the measured hit probability;
- the candidate's final simulated occupancy frequency.

The 200 internal transport steps have already been collapsed to one scalar occupancy frequency per cell before this likelihood is constructed.

Therefore Native distinguishes hypotheses using **where the simulated plume spent time**, but not **how candidate-conditioned transport first reached an observed region**.

The proposed mother-theory transfer targets exactly that discarded information.

## Cross-domain mother theory

Transition Path Theory (TPT), committor analysis, first-passage theory and reactive flux characterize source-to-target stochastic transport by path ensembles rather than only stationary occupancy.

Recent anchors relevant to the transfer include:

- Hillen, D'Orsogna, Mantooth & Lindsay, *Mean First Passage Times for Transport Equations*, SIAM Journal on Applied Mathematics 85(1), 2025, DOI 10.1137/24M1647667.
- Chen et al., *Following the Committor Flow: A Data-Driven Discovery of Transition Pathways*, Journal of Chemical Theory and Computation 22(3), 2026, DOI 10.1021/acs.jctc.6c00007.
- Earle & Van Koten, *Relative Entropy Methods for the Approximation of Reactive Trajectories and Committor Functions*, SIAM/ASA Journal on Uncertainty Quantification 14(2), 2026, DOI 10.1137/25M1757708.
- Aggarwal, Koes, Boffi & Vanden-Eijnden, *Reactive Flux Matching: Mechanism Discovery and Adaptive Sampling of Rare Events*, arXiv:2606.06295, 2026.
- TPT has already transferred outside molecular kinetics to large-scale Lagrangian transport, e.g. ocean source-to-target pathways (GRL 2022 DOI 10.1029/2021GL096646; JTECH 2022 DOI 10.1175/JTECH-D-22-0022.1).

A 2026-09-23 targeted prior-art search found no indexed exact collision for:

- gas source localization + committor / TPT / reactive flux;
- odor source localization + first passage / committor / transition path;
- plume/gas source + first-passage time / reactive trajectory.

This is **not proof of absence**. The closest source-inference family found uses adjoint source-receptor probabilities plus Bayesian inversion, which is conceptually adjacent but does not use candidate-conditioned reactive-path/first-passage evidence.

## Why the existing H01 replay is not enough

The six accepted independent runs contain 88 causal StopAndMeasure blocks before source update 1.

Using the frozen Native gas threshold 0.1 ppm and exact state-machine positions:

| run | hit blocks / 88 | unique hit cells |
|---|---:|---:|
| H01_R2026092201 | 0 | 0 |
| H01_R2026092202 | 2 | 1 |
| H02_R2026092211 | 52 | 3 |
| H02_R2026092212 | 70 | 6 |
| H03_R2026092221 | 24 | 3 |
| H03_R2026092222 | 24 | 3 |

The released deterministic trace is only H01_R2026092201, which has no positive observed target region.

Therefore a positive source-to-observed-hit first-passage test must use H02/H03. H01 remains a low-information/abstention control and cannot be used to claim TPT support.

## Multi-run deterministic replay changes

The standalone replay was generalized without changing the PMFS kernel.

### Removed H01-only gate

The old tool rejected navigation seed 3 even though all six accepted manifests have:

- the same Native OFF arm;
- the same launch SHA-256 `0cd1ae4ad852bf548fd1ebc131e7f46f0d6d20603a2e4e71ae37c6831e40f2c9`;
- the same Native algorithm SHA-256 `b06c2036da91ef22285d1cb5d4d08172e828956fc5844d8a2044a4221a8c2cce`.

The frozen launcher passes `random_seed`, while Algorithm/PMFS reads `seed`; therefore the candidate transport/source RNG uses the default seed 0 for both navigation seeds 2 and 3.

The generalized replay now accepts only NAV2/NAV3 under the exact frozen contract and exact launch/algorithm hashes.

### Removed H01 grid-size assumption

`verify_native_candidate_trace.py` previously hard-coded 29x38.

It now obtains width x height from each run's `source_update_timing.csv` when `--run-dir` is supplied. The legacy H01 invocation remains compatible.

## Frozen Layer-1 primary observable

Let B be the **unique causal observed hit cells** before source update 1.

For candidate source s and hit cell b, let tau_s(b) be the first candidate-internal step at which a filament occupies b, with 200 internal steps total.

The primary score is the discrete first-arrival coverage AUC:

`A_FP(s) = mean_b [(201 - tau_s(b))/200]`

with zero contribution if b is never reached.

Interpretation:

- 1 means target cells are reached immediately;
- 0 means they are never reached;
- candidate-internal time is **transport age**, never future robot/GADEN time.

No source truth enters score construction.

## Required controls

### Static occupancy control

For exactly the same hit cells B:

`A_static(s) = mean_b [occupied_step_count_s(b)/200]`

This uses the same information retained by a final hit map.

If first-passage cannot beat this control, the purported TPT gain is not caused by path timing.

### Geometry control

`A_geom(s) = - mean_b distance(source_point_s, hit_cell_b)`

If first-passage cannot beat this, the result may simply be source-to-hit proximity.

### Destructive time-order null

For every candidate and hit cell independently:

- keep the exact 200-step occupancy count fixed;
- randomly reassign those occupied timestamps;
- recompute first arrival and first-passage AUC.

This preserves final occupancy exactly and destroys only internal temporal order.

200 source-blind shuffles use fixed seed 20260923.

## Frozen single-run gate

A run passes only if all are true:

1. first-passage truth-nearest terminal-leaf rank percentile is better than static occupancy;
2. first-passage score-vs-truth-distance Spearman is better than static occupancy;
3. both corresponding metrics beat geometry;
4. at most 5% of time-order nulls achieve an equal/better truth rank percentile;
5. at most 5% of time-order nulls achieve an equal/better score-distance Spearman.

Truth is used only after all scores are frozen.

A positive reactive-target run additionally requires at least three unique causal hit cells.

## Frozen four-run promotion gate

Only these four runs are eligible for the positive Layer-1 TPT decision:

- H02_R2026092211
- H02_R2026092212
- H03_R2026092221
- H03_R2026092222

Promotion to Layer 2 requires:

- all four present and replay-parity verified;
- at least 3/4 pass the strict single-run mechanism gate;
- the passes include at least one H02 and at least one H03 realization;
- median first-passage truth rank percentile <= 0.25;
- median first-passage truth rank percentile beats both static occupancy and geometry.

Otherwise the line remains `TPT_LAYER1_HOLD`.

Even a Layer-1 GO does **not** authorize a localization posterior or closed loop.

## One-command qualified-VM execution

From the repository root on the qualified ROS 2 Humble/GADEN VM:

```bash
git checkout research/multirun-candidate-replay-tpt-20260923
bash reference/build_and_run_tpt_first_passage_layer1_20260923.sh
```

The script:

1. py-compiles all Python analysis/verifier files;
2. shell-syntax checks the batch runner;
3. clean-copies `ros2_package` into `/dev/shm`;
4. sources the same qualified VM overlays used by prior Native builds;
5. performs a Release `gsl_server` build;
6. runs parity for 1, 10 and all candidates on every accepted run;
7. runs a traced all-candidate replay only after static parity;
8. verifies full trace integrity using per-run grid dimensions;
9. runs the frozen first-passage screen;
10. writes the four-run aggregate decision.

Default output:

`_staging/TPT_FIRST_PASSAGE_LAYER1_20260923`

The aggregate runner exits:

- 0 only for `GO_TO_LAYER2_CROSS_REALIZATION_TPT`;
- 10 for `TPT_LAYER1_HOLD`.

## Files added / changed on this branch

- `ros2_package/tools/native_candidate_replay.cpp`
- `reference/verify_native_candidate_trace.py`
- `reference/tpt_first_passage_screen.py`
- `reference/aggregate_tpt_first_passage_layer1.py`
- `reference/run_tpt_first_passage_layer1_20260923.sh`
- `reference/build_and_run_tpt_first_passage_layer1_20260923.sh`

## Stop rules

Do not change after seeing H02/H03 results:

- 0.1 ppm hit threshold;
- minimum three unique hit cells;
- first-arrival AUC definition;
- 200 internal steps;
- unique-cell target definition;
- static and geometry controls;
- null construction;
- null repeats/seed;
- single-run p-like 5% null thresholds;
- 3/4 aggregate pass requirement;
- 0.25 median truth-rank-percentile threshold.

If the gate fails, record the failure and return to mother-idea search.

Do not rescue by changing target radius, weighting repeated hits, selecting favorable transport ages, House-specific rules or source-distance regularization.
