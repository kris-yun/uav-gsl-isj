# M1R post-NO-GO decision: keep the causal contract, retire causal reweighting as the main innovation

Date: 2026-09-13
Status: **CURRENT_CAUSAL_SCORER_NO_GO; INFORMATION_ACQUISITION_PIVOT_ONLY**

## Decision

The current M1/M1R claim must not remain the paper's main innovation.  Candidate
source intervention, shared nuisance keys, event-time alignment, transport
marginalization and source-region quadrature are implemented and auditable, but
they have not produced source evidence that is valid across H01/H02/H03.  The
causal graph remains useful as a scientific contract:

```text
source S + transport/sensor nuisance U -> concentration C -> sensor response M
executed route X controls which response is observed
```

It specifies legal inputs, prevents future information and source truth from
entering the estimator, and separates interventions from observations.  It does
not make a misspecified response family identifiable and is not, by itself, a
new performance mechanism.

The next research direction is therefore not another transform, pooling rule,
posterior temperature, abstention radius or nuisance prior on the same response.
The only admissible causal continuation is a **new, physically executed
measurement operator** whose source contrast survives the allowed nuisance
subspace.  If the benchmark must keep exactly the present sensing actions and
single gas channel, the causal main-innovation line should stop.

## Decisive local evidence

### 1. H03 fixed-source quadrature failed because the truth is outside response support

`INFORMATION_GATE.json` reconstructs every source update from the actual event
attribution log.  The unique current partition leaf containing the H03 truth is
compared with the highest-likelihood false leaf.  The online estimator did not
use the truth; truth is read only by this evaluator.

| update | positive events | zero predicted probabilities among the four truth-region points | zero predictions for strongest false points | truth-minus-false log-mixture margin |
|---:|---:|---|---|---:|
| 1 | 11 | 9, 9, 8, 8 | 2, 0, 2, 2 | -49.889 |
| 2 | 35 | 32, 33, 32, 32 | 3, 3, 3, 3 | -190.148 |
| 3 | 59 | 57, 56, 56, 56 | 3, 3, 3, 3 | -333.861 |
| 4 | 65 | 63, 63, 63, 63 | 3, 3, 3, 3 | -348.219 |

The independent scorer audit already established arithmetic parity to about
`1.96e-15`.  This is not an implementation error in quadrature.  The forward
response family says the true source almost never produces events that were
actually observed, while a remote false source does.  No lawful Bayesian
accumulation can reverse that evidence without replacing or expanding the
physical response support.

The paired 240 s H03 screen agrees with this attribution: source quadrature
worsened endpoint error by `0.967113 m`, worsened common-interval distance AUC
by `18.593548 m s`, and increased source-update wall time by `7.723x`.

### 2. Full physical ppm plus persistent FOPDT also failed the source premise

The completed same-provider H01 test used chronological filaments, physical
ppm, persistent FOPDT sensor dynamics, map collision and past estimated wind.
On actual source SA, ordinary full-prefix `log1p(ppm)` MSE selected false source
SB (`0.000806054 < 0.007337530`).  On actual SB it selected SB.  This is `1/2`,
so the missing information cannot be attributed only to the old occupancy
compression.

### 3. The simplest 2026 biology transfer also fails

As a parameter-free information check, this package applies the first
difference of `log1p(ppm)`, motivated by the task-relevant logarithmic
concentration change discussed by Mattingly et al.  It is intentionally not
presented as their fitted adaptive kernel or as a likelihood.

| actual source | loss for SA prediction | loss for SB prediction | correct |
|---|---:|---:|:---:|
| SA | 8.82546e-5 | 1.94048e-5 | no |
| SB | 7.00520e-5 | 1.83428e-7 | yes |

The result remains `1/2`.  Therefore a derivative/adaptive-filter story cannot
be selected as the repair from the existing evidence.

### 4. Several apparent pivots are already exhausted

- Intervention-time event scoring was implemented in CORE-M1F and achieved
  only one House with joint endpoint-and-AUC improvement in the frozen
  House123 seed6 gate.
- Adjacent temporal increments were exactly neutral on all ten H01 terminal
  replays; trajectory coherence was also unsupported there.
- Full route-encounter laws, distributional geometry, partial-identification
  output and non-myopic information planning have already been developed in
  the CTPI line.  Predictive or oracle premises could pass while proper
  closed-loop utility failed.  Renaming them does not create a new mechanism.
- Active probing already exposed the danger that a wrong forward response can
  actively drive the robot toward the wrong regime.  A new action is admissible
  only after its source-versus-nuisance separation is shown, before planning.

## What the selected 2026 papers actually permit

The six verified papers are theory sources and boundary conditions, not direct
gas-localization guarantees.

1. Mattingly et al. distinguish information physically present in the input
   from information lost by the sensing network.  Our derivative check shows
   that merely changing the temporal encoding does not recover the failed SA
   ordering.
2. Bloxham et al. gain source-direction information from two real chemicals
   with different diffusion kernels.  Two filters of one gas trace are not two
   physical channels.
3. Herter et al. separate response and fluctuation through physically distinct
   quadrature measurements.  Post-hoc algebra on one response cannot substitute
   for those measurements.
4. Wu et al. identify an inverse scattering operator using controlled inputs.
   A UAV cannot modulate an unknown gas source, so only its own sampling action
   is a legal intervention.
5. Shi et al. use observations linked by common source-event and medium latent
   structure.  A continuously emitting plume observed sequentially by one UAV
   does not automatically provide associated simultaneous arrivals.
6. Luo et al. show that source redistribution can change a supposedly
   medium-sensitive phase even when the medium is fixed.  This is a direct
   warning against assuming source-invariant nuisance features.

The common transferable principle is narrow: **new identifiability requires a
physically independent constraint, controlled input or associated measurement;
feature expansion cannot manufacture it from aliased observations.**

## Only admissible continuation: paired-position measurement design

This is a research candidate, not a validated module or novelty claim.  Let a
pre-registered short action cycle collect measurements `y(q)` under a real
sampling operator `q`, with

```text
y(q) = a f_s(q, eta) + B(q) beta + epsilon,
```

where `s` is the candidate source, `eta` is a frozen independently justified
transport/sensor class, `a` is a cycle-shared positive scale, and columns of
`B` are only background effects with independent physical justification.  A
contrast `c` is useful only if

```text
c^T B = 0
c^T (f_s - f_r) != 0
```

for the relevant source competitors across the allowed `eta`.  Equivalently,
for a particular pair, the elementary existence condition is

```text
rank([B, f_s-f_r]) > rank(B).
```

This algebra is not the novelty.  A defensible gas-specific contribution would
have to derive a realizable paired trajectory with FOPDT state continuity,
travel/wait cost and turbulent nuisance; prove or empirically establish its
source-set separation; and show the same-information ordinary Bayes control
does not already explain the gain.

### Minimum gate before any new closed loop

Use only the failed H03 setting and do not change seed, House, posterior,
planner weight or threshold.

1. Freeze one paired-position action cycle, its timing, travel/wait budget,
   sensor-state recurrence and nuisance set before reading the evaluator truth.
2. Generate candidate response sets for that new cycle.  The truth-containing
   region and the strongest existing false region must both be included; no
   nearest-source subset is allowed.
3. Project only independently justified shared background columns.  Report the
   minimum truth-versus-false separation across nuisance and the response-support
   coverage of real H03 positive events.
4. Run a shuffled-position/order negative control and a same-information
   ordinary Bayesian comparator.
5. Stop without ROS if the truth response set overlaps the strongest false set,
   if real positive events remain outside truth support, or if the negative
   control preserves the claimed separation.
6. Only a passed premise gate permits one paired 240 s H03 A0/action-design
   screen.  It must improve both endpoint error and common-interval AUC; an
   abstention-only result is not improvement.

No such new action trace exists in the current evidence.  Consequently the
scientifically correct next state is a design/premise gate, not another edit to
the M1R likelihood and not a claim that the causal main innovation is already
standing.

## Final classification

```text
current causal reweighting as main innovation: RETIRE / NO_GO
causal graph and intervention contract: KEEP
same-data temporal or distributional re-encoding: DO_NOT_REPEAT
2026 remote-domain direct module transfer: NOT_SUPPORTED
paired-position physical measurement design: ONLY ADMISSIBLE RESEARCH CANDIDATE
cross-dataset effectiveness: NOT ESTABLISHED
```

## Traceability

- Machine-readable diagnosis: `INFORMATION_GATE.json`
- Reproducer: `tools/diagnose_m1r_post_nogo_information.py`
- H03 paired result: `evidence/m1r_h03_source_quadrature_pair_20260913/`
- 2026 literature index and raw searches: `evidence/m1r_crossdomain_20260912/`
- H01 full-provider evidence: `evidence/cstar_m1_h01_same_provider_20260911.json`
- Prior event-time result: `docs/PMFS_CORE_M1F_SEED6_SEED7_RESULT_20260909.md`
- Prior temporal ablation: `docs/PF_DEI_H01_10SEED_POST_REPLAY_DECISION_20260829.md`
