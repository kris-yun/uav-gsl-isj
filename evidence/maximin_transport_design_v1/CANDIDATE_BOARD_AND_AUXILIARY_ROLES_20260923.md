# Candidate Board — after transition-KL derivation

Date: 2026-09-23

## M1 — Transition-KL Credal PMFS
**Role:** current main candidate  
**Status:** KEEP, waiting for repaired-Native PMFS F1/F2 data

Main idea:
- put ambiguity on PMFS filament transport transition/path law;
- propagate it to a set-valued forward hit map;
- maintain a credal source map;
- choose observations by worst-case source identifiability;
- later make source declaration robust to the same uncertainty.

This remains the only candidate currently strong enough to justify a paper-level main narrative.

## M2 — R-IDeA / de-amplifying active localization
**Role:** mechanism diagnostic only  
**Status:** REJECT AS MAIN

Parent:
R. Tang, S. J. Sloman, S. Kaski,
"Representative, Informative, and De-Amplifying: Requirements for Robust Bayesian Active Learning under Model Misspecification,"
AISTATS 2026, PMLR 300.

Why it is scientifically relevant:
- formalizes generalization error under misspecification as misspecification bias + estimation bias + an interaction term called error (de-)amplification;
- explains why actively selecting "informative" points can make a wrong model more confidently wrong;
- directly resembles our empirical failure mode where PMFS-native candidate-variance cells were stable/informative in the simulator but worsened truth-source rank.

Why it is NOT a suitable main novelty for us:
1. the paper already includes a source-localization experiment (acoustic energy attenuation);
2. its R-IDeA method is still an acquisition-function construction:
   R-IDeA(x) = R-I(x) * DeA(x);
3. it introduces tuning parameters such as tau, and the authors explicitly leave systematic hyperparameter selection open;
4. porting that score to GSL would look like another movement/reward patch rather than changing the PMFS scientific model.

Allowed use in our project:
- theoretical motivation;
- post-hoc mechanism diagnostic: test whether locations selected by M1 avoid error-amplifying regions;
- comparator if implementation is cheap.

Do not call it an auxiliary module unless later experiments show an independent, source-blind role that is not just score multiplication.

## A1 — Inverse conformal calibration of the transport ambiguity
**Role:** preferred auxiliary candidate if M1 survives  
**Status:** HOLD

Parent:
W. Zhou, S. Zhu,
"Calibrating Decision Robustness via Inverse Conformal Risk Control,"
ICML 2026.

Problem it solves:
M1's largest unresolved issue is selecting transport/path ambiguity radius without using source truth.

Desired adaptation:
- construct a calibration score from forward-prediction discrepancy available before assimilating the current observation;
- choose the smallest transport ambiguity radius satisfying a predeclared coverage/risk requirement;
- never choose radius by final source rank or endpoint error.

Why this is a good auxiliary:
- it solves a required scientific problem in M1 rather than adding another feature;
- it gives a finite-data calibration narrative;
- it prevents the main method from degenerating into hand-tuned robustness.

Hard gate:
do not implement A1 until M1 Level-A has a repeated source-rank positive signal.

## A2 — reliable source declaration
**Role:** open auxiliary slot  
**Status:** DO NOT SELECT YET

Two current remote-field parents:

### Option A2a — Conformalized Decision Risk Assessment (ICLR 2026)
Could reinterpret source declaration as a candidate decision and attach a distribution-free upper bound on decision/suboptimality risk.

Risk:
mapping its inverse-optimization geometry to candidate-source declaration may be artificial.

### Option A2b — anytime-valid sequential evidence
Recent examples include NeurIPS 2025 anytime-valid prediction-powered inference and modern confidence/e-process work.

Potential fit:
PMFS repeatedly inspects its posterior while adaptively choosing new measurements. A fixed posterior threshold can be overconfident under repeated adaptive stopping. An anytime-valid source-vs-alternatives evidence process could provide a principled declaration condition that remains valid under optional stopping.

Risk:
must handle adaptive spatial sampling and misspecified plume likelihood. Do not use a textbook e-value construction without proving the supermartingale/e-process condition under our observation process.

Decision:
leave A2 open until M1 succeeds. The best auxiliary must solve an experimentally observed failure, not be selected for fashion.

## Overall architecture if M1 survives

The preferred eventual scientific structure is:

1. **M1 — transport uncertainty:** Transition-KL Credal PMFS.
2. **A1 — uncertainty calibration:** source-blind inverse conformal calibration of ambiguity radius.
3. **A2 — decision reliability:** robust/anytime-valid declaration only if the data show declaration overconfidence is an actual remaining failure.

This architecture is intentionally asymmetric:
M1 carries the paper thesis; A1/A2 repair specific necessary weaknesses rather than competing with the main idea.
