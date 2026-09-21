# Active source–transport deconfounding V1: development screen

Frozen before generating new responses, 2026-09-21. Historical truth and V5
outcomes have already been seen; this is not a pre-truth registration or a
confirmation experiment. Base: b24da77fd24bd5ea2cbb33caf856f80b9d7670e4.

V5 remains HOLD. No V5 edits, online planner edits, ROS runs, new trajectory
seeds, protected banks, or previously withheld winds are authorized here.

## Fixed design

- Six existing House01–03 / seed0–1 contexts, last update at or before 300 s.
- Source hypotheses: every terminal native leaf, represented by its recorded
  native source point. This point-source surrogate is not an exact replay of
  the region-source generator. Source prior is free-cell leaf measure, common
  to all information strategies; never the collapsed native posterior.
- Training transport: Cartesian product of wind rotation {-15,0,15} degrees,
  speed multiplier {0.8,1,1.2}, diffusion-velocity noise multiplier {0.8,1,1.2}.
  Rotate/scale the whole estimated wind field. Noise base is 0.5 m/s.
- Held-out grid-off transport: Cartesian product {-7.5,7.5} degrees,
  {0.9,1.1} speed, {0.9,1.1} noise. No range tuning after outcomes.
- Original forward kernel, 200 recording steps, dt=0.2 s, warmup min=1/max=3.
  Train replica=0 and held-out replica=1 use event-keyed common randomness,
  keyed by case seed and update. One field/world per source+nuisance; never
  choose a different nuisance for individual cells or observations.
- Actions: up to 12 map-only farthest-point locations in the robot's connected
  free-cell component, using four-neighbour shortest paths. First is the
  nearest free cell to the robot. All pairs obey speed 0.35 m/s, two 3-s dwells,
  and the remaining 300-s budget. Grid feasibility is a point-robot surrogate,
  not a Nav2 collision certificate. Save paths and lengths.
- Each dwell contributes one Bernoulli observation, with hit probability from
  the native forward map. Two observations are conditionally independent
  given ONE shared world index. This is an explicit measurement surrogate;
  temporal correlations and real GADEN mismatch are not validated.
- Native acquisition heuristic: original variance × (1-confidence) × visible
  neighbourhood weight, divided by (distance+0.1)^0.15. Use first-level
  native candidates/weights where exported; report any missing support rather
  than substitute a source-MI baseline. This is an offline heuristic, not a
  reproduction of full open/closed sets or exploration RNG state.
- Source-MI and joint-MI: two equal-budget greedy actions, second chosen by
  expected conditional information, not by the true outcome. Also report the
  first-action information. No adaptive policy claim.
- Two-step deconfounding: jointly choose a feasible pair maximizing the
  source-prior-weighted mean of pairwise worst-world squared Hellinger
  separation. For each distinct source pair, minimize over two nuisance
  hypotheses, each fixed across both observations. Tie: larger global minimum,
  then shorter path, then cell ids. No posterior/truth-selected rivals.
- Local sensitivity diagnostic: standardized finite-difference nuisance
  columns and source contrasts on existing confidence-weighted support;
  Moore–Penrose/SVD projection. Report ranks and residual fractions. Fisher
  terminology requires whitening; these confidence weights are not a measured
  sensor-noise covariance. With two scalar observations and 3 nuisance axes,
  full nuisance row rank can annihilate local source information.

## Evaluation / stopping

Actions are saved and hashed before reading a separate truth file. Evaluate
true-leaf representative vs every wrong source under each of 8 held-out
worlds, minimizing over training nuisance of the wrong source. Report true
representative distance, minimum separation, pair-vs-single and pair-vs-greedy
gains, expected finite-observation source entropy, and times. Truth outside
the candidate partition is a failure, not permission to insert it.

Necessary numerical promotion gate (not a localization claim): two-step vs
source-MI minimum separation improves by >=10% AND >=1e-4 in at least 6/8
held-out worlds in >=4/6 cases, with at least one passing case in each House;
no case mean separation degradation >5% or >1e-4 absolute. Action selection
must be truth blind and paired observation/travel budgets equal. A surrogate
pass still requires an independently qualified response model and review
before ROS. Failure stops this screen; no nuisance tuning or extra gates.

Classical nuisance projection / optimal design is not itself a new 2026 mother
theory. This screen tests usefulness only, not novelty or cross-dataset validity.
Prior observability NO-GO remains valid for its frozen route/response contract.
