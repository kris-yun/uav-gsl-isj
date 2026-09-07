# M1/M2: verified distant-field sources, actual PMFS target, and revision boundary

2026-09-07. Evidence base: `ea58d37`; environment engineering starts at `624ea16`.
Status: **MECHANISM REVIEW, NOT A NEW SCIENTIFIC PASS OR EXECUTION FREEZE**.
The idea-spark pipeline is being used for a literature-grounded redesign; its
retrieval/partition artifacts are not a completed novelty or feasibility audit.

## Bottom line

The mother ideas are real and relevant. Their existing transfer into PICR/CPO
is insufficient. Do not add layers, increase training steps, pick another seed,
or use an entropy clamp to relabel the controlled NO-GO as success. An environment
PASS fixes evidence integrity, not the scientific failure.

Current identities remain **M1 PICR (Perturbation-Invariant Causal
Representation)** and **M2 CPO (Committor Predictive Operator)**. Neither current
CSTAR prototype has demonstrated lower real closed-loop localization error.
The old CTPI-G2 M2 predictive PASS is a different implementation and experiment.

## 1. Primary publications verified in this review

| Primary paper | What is actually supported | What it does NOT establish here |
|---|---|---|
| Guo et al., [XPert, Nature Machine Intelligence, 26 January 2026](https://www.nature.com/articles/s42256-025-01165-w) | Separate baseline cellular context and perturbation-dependent response; predict both treated expression and expression changes; compare context-specific mean baselines and cold-context splits. | A same-source embedding-distance penalty identifies a gas source, or four training source locations suffice for unseen-map localization. |
| Driessen et al., [Conditional Monge Gap, Nature Machine Intelligence, 1 June 2026](https://www.nature.com/articles/s42256-026-01242-8) | Learn response-distribution maps conditioned on treatment covariates; accommodate unpaired cell measurements. | Optimal transport uniquely recovers physical gas transport or source causality from confounded source/transport pairs. |
| Li et al., [CARL, ICLR 2026 proceedings](https://proceedings.iclr.cc/paper_files/paper/2026/hash/d63cf0622eed012a17fe88fced64dcb8-Abstract-Conference.html) | Preserve conditional-independence and Markov-boundary structure during cross-modal representation learning. | Arbitrary representation invariance is sufficient; the current PICR prototype implements CARL's preservation conditions. |
| Contreras Arredondo et al., [Learning the committor without collective variables, Nature Computational Science, 17 February 2026](https://www.nature.com/articles/s43588-026-00958-2), [author preprint](https://arxiv.org/abs/2507.17700) | Predict molecular transition probability from atomic configurations using geometric representations, rather than hand-chosen collective variables. | A short first-hit label is informative about robot routes when most cases begin above the sensor threshold, or that our observed history is a sufficient Markov state. |

These are mechanism sources, not transferred performance guarantees. Dates and
venues above were checked against primary publisher/conference records. This is
a targeted source check, **not** an exhaustive novelty search. Other references
in the earlier theory document were not all independently rechecked this turn.

## 2. Correct the baseline attribution before claiming an improvement

Actual native path:

1. `PMFS.cpp` thresholds a completed observation block and calls
   `PMFSLib::EstimateHitProbabilities`, updates estimated wind, then periodically
   calls `Simulations::updateSourceProbability`.
2. `internal/Simulations.cpp` simulates candidate sources and compares their hit
   maps to the measured hit-probability map.
3. `sourceProbFromMaps` multiplies free-cell compatibility factors.
   `probabilityFromSingleCell` interpolates from neutral 1 to the frequency
   compatibility by cell confidence; with the compiled default branch,
   `probabilitySingleFrequency(m,p) = 1 - |m-p| * sourceDiscriminationPower`.

Thus the PMFS bottleneck to test is **spatially aggregated, correlated evidence
and an approximate source-conditioned forward family**, not a generic Gaussian
SSE posterior. The gas threshold/aggregation discards temporal detail. Multiplying
factors across a spatially propagated map does not by itself provide calibrated
independent evidence. The size of that defect must be measured, not assumed.

`CPIR.cpp::applyCPIRPosterior` is a later extension. Its peak/shape/Gaussian-SSE
behavior must not be attributed to original PMFS. `CTPI.cpp` is also an extension,
not evidence of the original planner's exact action objective. A future comparison
must freeze an actual A0 call path and its flags, not just label an arm 'PMFS'.

## 3. Why the present M1 transfer is not yet load-bearing

- Same physical source does not imply equal information under different winds.
  A plume may miss a route entirely in one context. Forcing equal representations
  can erase a genuine change in source identifiability. Stable source identity
  and equal posterior confidence are different requirements.
- Same-source fast/slow provenance is valid, but release draws are not matched.
  Cross-source examples also change transport settings and sometimes gas type.
  They are not isolated `do(source)` pairs. A discriminative separation loss
  cannot be described as a demonstrated source-intervention effect.
- The bounded model scores absolute candidate coordinates using a global latent
  representation. The code allows context shortcuts; the controlled results
  show a large generalization gap, not a proof of which shortcut caused it.
- A null-value stress test is not a missing-data experiment. **Measured zero gas
  can contain negative evidence** given wind, route and a valid detection model.
  Future interfaces must distinguish `measurement_valid=false` from a true zero.
  The frozen old gate remains NO-GO; do not change its result. Its null test is
  a robustness diagnostic, not a theorem that every zero-gas posterior is uniform.

The most defensible direction is to test **conditional response evidence**:
does gas add correct source evidence after accounting for the executed route,
transport context and sensor history? The source scorer must earn its preference
through a candidate-conditioned observation law, not through pose/time alone.
The XPert analogy is the separation of context and perturbation-dependent change,
not adopting its architecture or importing its reported gains.

## 4. Why the present M2 target is inadequate for the desired claim

The controlled data have 168 immediate hits among 252 route outcomes, and only
5/84 matched contexts have different first-hit labels across routes. A train-only
current-threshold baseline reaches 100.0%, 98.81%, 95.24% held-House label accuracy.
This is not a learned CPO result, and does not show all future gas is unpredictable.
Indeed, 69/84 contexts have different future concentration sequences.

The next target should test **new route-dependent observation evidence**, with
the shared prefix and sensor memory treated identically between alternatives.
Full time-resolved observations or their conditional innovations are a candidate
object. Merely lengthening the horizon, raising the hit threshold, or selecting
the five differentiating contexts after seeing outcomes is not acceptable.

A joint observation law must model temporal dependence (for example through a
causal state). Calling independent per-step Gaussian heads a calibrated joint
trajectory law would repeat the evidence double-counting problem.

## 5. One coherent redesign direction, not two unrelated networks

Investigate one candidate-conditioned **context + response-change** mechanism:

- M2 would define a causal observation law for candidate sources under known
  feasible route interventions, initialized by a *belief* over unresolved
  transport/sensor state. No future fields or true sensor-input delay queue enter
  a deployed model. The named conservative transport/FOPDT prior must really be
  called, and bound to its code and sensor contract.
- M1 would accumulate only the observation evidence supplied by that same law,
  retaining transport uncertainty rather than forcing all contexts into equal
  embeddings. An empty set of valid measurements contributes neutral likelihood;
  a valid zero reading does not automatically do so.
- Shared physics/observation consistency could make representation changes useful
  to inference and decisions. However, writing Bayes' rule or adding a residual
  operator is **not itself a new causal contribution**. The proposal still needs
  an identifiable intervention claim, a concrete implementable operator, a
  nontrivial comparison and a collision/naive-baseline audit.

This is an investigation direction, not an approved replacement formula. No new
model was trained or substituted for PICR/CPO in this review.

The online plumbing boundary now exists in
`closed_loop/ctpi/cstar_m2_online.py`: it receives the same stamped pose/gas/wind
frames as the ROS ingress, copies only the past prefix into an injected route-law
provider and enforces prediction-before-observation. Its synthetic self-test is
not a CPO performance or closed-loop result.

The corresponding M1 score transform is now implemented as
`m1_picr/conditional_evidence.py`: `Delta_s = log p(Y|S=s,N) - log p(Y|N)`.
Because subtracting a common context constant would cancel in ordinary Bayes,
the mechanism is only meaningful when the context law has candidate-varying
shortcut bias and is itself produced without gas/source inputs. The code and
tests make that distinction explicit; no performance claim is attached.

## 6. Small next gates and stopping rule

1. Finish the focused mechanism/novelty and implementability review. Explicitly
   separate observational calibration from identifiable causal intervention.
2. Implement and verify the actual causal physics/FOPDT baseline on the existing
   controlled data before learning another large source classifier. Compare
   current-value persistence, conditional training-only baseline and physical
   prediction on the **same** source/route outcomes.
3. Freeze any revised observation law and primary metric prospectively, retain
   all previous negatives, and use only the already permitted House123 seed12.
   These exposed data are development data, not virgin confirmation.
4. Enter a bounded true closed-loop comparison only after the forward/inference
   gates justify its cost. Freeze M1-alone and incremental M2 attribution with
   common environment, planner/stopping settings and full horizon. Report both
   240 s final localization error and the existing distance-AUC metric; changing
   the primary endpoint requires a new explicit protocol version.
5. If the House123 one-seed screen fails, stop expansion; do not launch multiseed
   validation to average away an unsupported mechanism. A one-seed win would be
   a pilot signal, not a generalization proof.

## 7. Environment is now a reusable prerequisite, not an algorithm innovation

See `CSTAR_REUSABLE_ENVIRONMENT_20260907.md` for the common numeric reader,
byte-bound launch preflight, resolved sensor/clock contract, regression tests
and VM evidence. Its PASS cannot authorize a scientific campaign.
