# Frozen offline protocol, 2026-10-17

Scope: original closed loops are immutable. No world, ROS, planner, threshold,
seed or stopping rule is changed. 2024 B4 eight-run evidence and the corrected
2026 implementation twenty-configuration evidence are separate strata.

Trigger: a sampled stop has both >threshold and <=threshold consumed windows.
Use every stop, including all-zero and all-hit controls. A stop is not an
independent world. A five-window sequence cannot identify a correlation time;
report transitions, lag-one statistics descriptively and abstain from tau.

Primary fixed-history experiment uses captured full forward maps, final leaf
owners and original source domain. All O arms retain native confidence:

* O0: original accumulated binary-filter contact log-odds.
* O1: ordinary wind-kernel-weighted empirical detection frequency. Unobserved
  cells retain prior .3. Kernel is native Gaussian on native propagated distance
  and direction, independently recomputed using the original C++ functions.
* O2: Beta(.3,.7) (strength 1) with the same fractional kernel-weighted hits and
  misses; posterior mean. Weights are spatial smoothing, not independent data.
* O3: same Beta prior, but each completed/partial stop contributes one block:
  weight=sum(window weights)/number of observed windows in that stop; hit
  fraction=sum(weight*hit)/sum(weight). This is an ordinary effective-block
  correlation control, without estimating an unidentifiable five-point tau.

Secondary confidence ablation alone replaces repeated-window coverage with
mean within-stop coverage before applying the unchanged native confidence
formula. Cross it with all O arms; report it separately from O main effects.
Sensitivity: raw pre-blur candidate center-occupancy maps, if archived, compared
with original blurred maps. This is NOT an aligned PID event model. A particle
center snapshot alone cannot reconstruct subwindow 3D PID threshold events.

Source score is the original product (computed in log space), original D,
native free-cell mask and leaf area. Score every final leaf on the same maps,
assign each leaf score to all its free cells, then normalize over free cells.
Verify candidate and posterior parity before admitting a case.

Competitor for epoch t is the first row-major maximum of O0 posterior at t-1;
it is locked before current observations. Epoch one: ABSTAIN, no previous
source snapshot. Do not select a competitor using current/final outcomes or
truth. Compare the current leaf containing that locked cell to the truth leaf.
If both share an owner, label unresolvable at captured resolution, not rescue.

Metrics: true-minus-locked-competitor log score, truth rank (strict plus ties),
truth-cell mass, truth 90% membership, working NLL/Brier, MAP, native C++ Top-5%
cell-count decoder, posterior mean and spatial variance. Same-history errors
are diagnostic counterfactual readouts, never new closed-loop task gains.

Source exclusion, invalid 3D sensor support, missing event/geometry binding,
wind/clock/navigation failure and implementation version changes are separate
exclusions or qualifications; no scientific gain attributed to repairing them.

Preserve R05, R06, R08 and PC16 counterexamples. No posthoc 1m success rule.
No source-conditioned tuning. Only search a new cross-domain module after
ordinary controls leave a reproducible, qualified source-ranking defect.
