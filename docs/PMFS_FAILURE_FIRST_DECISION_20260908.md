# PMFS failure-first decision

Status: code-grounded diagnosis and proposed development protocol. No new performance PASS.

## Actual baseline and evidence

Native PMFS calls EstimateHitProbabilities from PMFS.cpp, spatially propagates a completed hit observation in PMFSLib.cpp, and scores source hypotheses in internal/Simulations.cpp::sourceProbFromMaps. The compiled frequency branch uses confidence-weighted factors 1 - discrimination_power * abs(measured - simulated), multiplied across free cells. These factors are compatibility scores; their product alone does not establish a calibrated observation likelihood.

An observation can affect multiple map cells. Treating their contributions as independent evidence risks overconfidence. Whether it explains a particular House failure must be measured using event provenance and matched replay; this is not established by source inspection alone. Temporal aggregation also removes observation order. Recovering useful information from that order requires a validated time-dependent observation model.

R4 F00/F01 are CPIR extensions, not the native PMFS likelihood. The archived R4 attribution identifies peak/time mismatch and simultaneous estimator/controller changes. Its numerical-field M2 PASS belongs to a different implementation from F01. Preserve these distinctions.

## Corrections to preceding advice

- Removing wind does not establish causal source identification; wind can be required to explain the measured gas. The strict-stream negative does not isolate wind removal as its sole cause.
- A fixed source under different winds need not yield identical finite-data posteriors. Different winds alter exposure and source information. Evaluate correctness and calibration across interventions, not compulsory equality of uncertainty.
- A measured zero is evidence under a detection model. Missing observations contribute neutral likelihood; the two cases must remain distinct.
- Subtracting a candidate-independent context log likelihood cancels in normalized Bayes. A candidate-dependent denominator needs a separately justified estimand. Neither subtraction nor an additive learned correction is inherently causal.
- Adaptive sampling does not automatically require inverse-propensity weighting. A sequential likelihood conditioned on past history and the actual action is valid under an ignorable known policy; selection corrections require a demonstrated violation.
- General Bayesian filtering is an appropriate strong baseline. A new name or causal graph cannot make it a novel estimator.

## Recommended mechanism and first decision

Investigate source evidence from distinct, time-indexed sensor observations under an explicit candidate-conditioned transport and sensor-state model. M1 owns source evidence accumulation and nuisance marginalization. M2 owns the predictive transport/sensor law and its uncertainty. Source truth is evaluator-only. Condition on measured past wind and actual pose; do not invent access to full future wind.

First establish whether the true source can predict withheld observations within the allowed source-strength and transport uncertainty family. Fit nuisance variables only on a past prefix and score the subsequent observations before assimilating them. An evaluator-only diagnostic can use true source position, but its fitted nuisance parameters must not enter deployable arms. If the true-source model fails predictive support, evidence reweighting cannot repair missing physical explanations: address M2 first. If support exists but native posterior odds become wrong or overconcentrated, test event-level scoring first.

The minimal comparison uses exactly the same recorded observations and frozen candidate support: native map compatibility, event-level evidence under the same forward model, and event-level evidence under the corrected dynamic forward model. Before introducing a learned correction, compare source rank, true-source probability/proper score, localization error, and coverage at matched prefixes. Confidence-only improvements do not qualify as better localization. Offline prefixes and cells are not independent experimental replications.

Causal attribution requires changing one mechanism at a time. Test whether repeated map propagation changes posterior odds without new sensor data; test chronological state alignment against a deliberately mismatched transport/sensor history; retain null/missing and valid-zero controls. A synthetic construction demonstrates algebra, not House efficacy. Source-versus-transport intervention pairs require a stated coupling of release randomness; a common RNG seed alone may not guarantee that coupling.

Only after a candidate passes this development diagnostic, freeze the runtime mapping and run native / M1 / M1+M2 with a common controller on House123 seed12, 240 seconds. Record final source error and distance AUC. This exposed seed is development screening, not independent confirmation or cross-dataset proof. A failed one-seed screen does not authorize multiseed expansion.

## Novelty obligation

The potential causal contribution is an identifiable way of distinguishing source evidence from transport/sensor mismatch under the available observations, with an experimentally demonstrated reduction in wrong-source evidence. That claim needs explicit identifying assumptions and separation from ordinary sequential Bayes with the same inputs. If no such separation or new validated model structure exists, classify the work as a useful PMFS correction/application rather than a new causal inference method.

The idea-spark candidate and its literature retrieval remain incomplete reviews; neither authorizes algorithm substitution or a novelty claim. This decision follows the user's request to return to PMFS failure mechanisms.
