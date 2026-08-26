# V13 CTT independent review — mandatory gates before closed-loop

Date: 2026-08-26

This memo reviews the V13 CTT direction against the revealed V11/V12 failures. It is an independent audit note only. It does not modify the frozen V11/V12 runtime or the VM development tree.

## 1. What the existing evidence really says

### V11 multi-seed

The frozen 15-pair V11 experiment is a scientific NO-GO under the predeclared >=10% pooled-improvement criterion, but it is not random failure:

- 11/15 pairs improved;
- pooled improvement = 9.0688%;
- stratified bootstrap 95% CI = [0.81%, 15.58%];
- one catastrophic regression occurred;
- House02 median improvement was slightly negative.

Therefore the earlier three-seed 3/3 result was optimistic, but the inference idea retained signal. A replacement method should explain both the majority-positive cases and the unstable/catastrophic tail.

### V12-M

The later three-new-seed V12-M generalization result was stronger NO-GO: pooled -1.78%, with candidate truth ranks already poor at the first likelihood update and evidence gaps growing in the wrong direction. The important diagnosis is likelihood/response-model direction error, not insufficient runtime.

## 2. V13 CTT direction: what is scientifically right

The current staged protocol is substantially better than immediately running 300-s closed loops:

1. M1 is treated as a physical response field, not as an extra likelihood factor.
2. M2 and M3 are being forced into one joint event-sequence probability model rather than multiplied as independent scores.
3. Time-order/path-shuffle controls are defined before final closed-loop evaluation.
4. Truth coordinates are excluded from online inputs and used only in external source-ranking evaluation.
5. Static response-bank identity was explicitly tested and found context-dependent, motivating current-wind conditioning.

The current M1 evidence is useful mechanism evidence: held-out wind/member proper scores improve and causal temporal permutations destroy the improvement. However it is not yet sufficient to declare source-localization generalization.

## 3. RED LINE A — do not make `PMFS posterior × CTT likelihood` a double-counting rule

This is the most important unresolved interface issue.

Native PMFS posterior already contains information from gas observations. If CTT uses the same observations and the final update is simply

```
q_t(s) ∝ p_PMFS,t(s) * L_CTT,t(s),
```

then the same measurement block may be counted twice. This is not automatically a valid Bayesian fusion rule.

Before implementation, choose and document exactly one of the following contracts.

### Preferred contract: prequential held-out increment

At source update t, freeze the source state before the new CTT evidence block B_t. Score only data not already used in the frozen prior:

```
q_t(s) ∝ q_{t-1}(s) * exp(J_CTT(B_t; s)),
```

with a precise event ownership ledger proving that each observation enters a CTT evidence increment once.

If PMFS also consumes B_t before injection, then the CTT correction must not be described as independent Bayesian evidence.

### Alternative contract: likelihood-ratio / residual correction

If CTT and native PMFS both model the same observations, use a declared relative correction such as

```
q_t(s) ∝ p_PMFS,t(s) * exp[J_CTT,t(s) - J_reference,t(s)],
```

where `J_reference` is the explicitly defined native/reference predictive score for those same observations. This is a generalized correction, not an exact Bayes product.

No fusion temperature or adaptive scalar may be tuned on revealed source error.

## 4. RED LINE B — observation mask: unobserved time bins are not misses

The proposed M2/M3 discrete-time onset model must distinguish:

- observed hit;
- observed miss;
- not observed / robot was not measuring.

Introduce an observation mask `m_t`. Survival/count evidence may include a time bin only when the sensor was genuinely exposed/observed under the online measurement contract. Do not treat every one of the 200 physical trace bins as a negative observation.

This is especially important for a moving robot and StopAndMeasure sampling. Otherwise M3 will create strong false negative evidence from periods that were never sensed.

Minimum unit test:

- inserting an unobserved gap (`m_t=0`) must not change candidate log evidence;
- converting that gap into an observed miss (`m_t=1,y_t=0`) may change evidence.

## 5. RED LINE C — M2/M3 factorization must be exact under one generative model

The decomposition

```
log p(y_1:T | s,q)
  = log p(y_1:T | N,s,q) + log p(N | s,q)
```

is valid only when both terms are derived from the same declared joint model.

Required audit:

1. define hidden state(s), transition probabilities and emission/onset probabilities;
2. derive the joint forward likelihood;
3. derive the conditional-on-count M2 term and the count/survival M3 term from that same joint probability;
4. numerically verify on tiny sequences by exhaustive enumeration that
   `J_full == J_M2 + J_M3` to <=1e-12;
5. verify A2 does not already retain a count-dependent normalizer that is then added again in A3.

Until this passes, do not call M2/M3 an exact likelihood decomposition.

## 6. RED LINE D — first-arrival physics must match the actual continuous-release/sensor contract

A first-arrival trace is scientifically meaningful only if its time origin maps to the actual GADEN source-release/playback and robot measurement chronology.

Before using `first arrival` or `travel-time tomography` in the paper, document:

- what time zero means;
- whether the source is pulse, continuous, or replayed filament release;
- how a moving query location is mapped to a source-to-query arrival distribution;
- how sensor response time / thresholding transforms filament occupancy into observed burst onset;
- whether repeated bursts after first arrival are modeled or discarded.

If the observation is not literally generated by a first-arrival process, name the M1 output a `transport-response delay/hazard field` instead of overclaiming first-arrival tomography.

## 7. RED LINE E — M1 baseline must be stronger than a stale static bank

Current M1 compares a wind-conditioned model against a same-capacity static/mean-wind model. That establishes that wind context contains information, but it does not yet establish that a neural surrogate is the necessary or best mechanism.

Add at least one strong baseline:

### Dynamic keyed-simulator baseline

For the current wind context, generate the time-resolved response directly with the same keyed filament simulator when computationally feasible.

If a fresh full candidate/member bank takes only seconds, this is the scientific gold-standard response model. The neural field should then be framed as an acceleration/surrogate and must approximate this dynamic solver.

### Simple wind-conditioned baseline

Also compare with a non-neural or low-capacity wind-conditioned interpolation/parametric travel-time model. Otherwise a gain over mean wind can be explained merely by giving the network the missing covariate.

Do not promote the network itself as the novelty unless it beats these controls in accuracy/runtime tradeoff.

## 8. RED LINE F — avoid pseudo-replication in M1 confidence intervals

The reported 824 evaluation atoms share only two held-out wind contexts and two held-out transport members. Candidate-source atoms within a context are strongly dependent.

Therefore a naive atom-level bootstrap CI is anti-conservative.

Required statistics:

- aggregate first at independent context/seed level;
- use cluster bootstrap/permutation by complete wind context or complete run/seed;
- report per-context signs and effect sizes;
- when possible add more independent held-out wind contexts from different seeds/houses before claiming generalization.

The current atom-level CI can remain a diagnostic, not the main generalization confidence interval.

## 9. RED LINE G — report both directions of ranking flips

Current M1 audit reports 26 `wrong -> right` local ranking corrections. Also report:

- `right -> wrong` flips;
- net flip gain;
- top-1 matched-neighbor accuracy;
- true-source mean/median rank;
- pairwise AUC or fraction of matched false candidates beaten;
- per-context results.

A module may improve average margin while creating a harmful tail. The V11 history shows that tail risk matters.

## 10. Development cases and held-out qualification must stay separated

All revealed V11/V12 seeds, including catastrophic/negative examples, are now development-visible and may be used for mechanism replay only.

Recommended development stress cases from V11 15-pair archive:

- House01 seed653959: catastrophic V11 regression, -38.1%;
- House02 seeds251322, 608060, 868245: small negative V11 cases;
- House02 seed276860 and existing 825201: positive contrast cases;
- House03 cases: small but consistently positive contrast cases.

Use them to test mechanism invariants, not to choose final thresholds by source error.

After M1/M2/M3 and the fusion contract are frozen, final qualification must use genuinely new seeds whose source-error outcomes were not inspected during V13 design.

## 11. Module-specific GO gates before any 300-s closed loop

### M1 — transport-response field

GO requires all of:

- deterministic trace reconstruction on Free support;
- current-wind conditional proper score better than strong static and simple conditioned baselines on independent held-out contexts;
- source-ranking metric improvement, with net ranking flips positive;
- temporal/directional permutation controls remove the gain;
- no truth coordinates in model inputs/training targets.

### M2 — ordered association

GO requires all of:

- exact probability normalization / tiny-sequence enumeration audit;
- improvement over M1-only on held-out event sequences;
- time shuffle or path-order reversal degrades M2;
- no use of final localization error to choose HMM state count or transition constants.

### M3 — count/survival negative evidence

GO requires all of:

- explicit observation mask;
- exact complementarity with M2 under the same joint model;
- all-miss observed blocks can demote candidates predicting events;
- missing/unobserved blocks have zero evidence contribution;
- window-shift negative control removes or reverses the claimed gain.

### Full A3

Before closed loop, A3 must beat A2 on source-ranking/evidence metrics across independent development contexts without creating a new catastrophic tail.

## 12. Closed-loop sequence

Only after all gates pass:

1. freeze source SHA, model checkpoint SHA, trace-bank/data hashes, formula marker, all hyperparameters, observation mask and fusion contract;
2. first run one previously revealed failure seed as mechanism regression only (not confirmatory evidence);
3. if structural behavior is correct, run a small new-seed House03 OFF/ON pair;
4. only then launch cross-House new-seed qualification;
5. do not adjust model after reading qualification truth.

## 13. Literature positioning

Relevant current theory/examples include:

- 2025/2026 seismic first-arrival/travel-time physics-informed tomography: supports learning/solving a propagation-delay field from physical constraints, but does not validate plume source localization automatically;
- ICML 2025 physics-informed sequential/state-space learning: supports explicit temporal dynamics in learned physical surrogates;
- ICML 2025 Residual TPP and 2026 Annual Review on deep spatiotemporal point processes: support event-intensity plus survival/no-event likelihood structure;
- 2025/2026 astronomy reverberation mapping: supports transfer/delay response functions as interpretable mappings from a driving cause to delayed observations.

Do not claim that CTT inherits tomography identifiability, point-process consistency, or causal-effect theorems unless their assumptions are explicitly established.

## Independent verdict at current progress

**Direction: GO for mechanism development, NOT YET GO for closed-loop qualification.**

The strongest part of Codex's current work is that it has stopped tuning final error and is now validating the physical response premise first. M1 has positive mechanism evidence. The next risk is not whether the network trains; it is whether M2/M3 define a valid masked observation likelihood and whether final PMFS fusion avoids both posterior replacement and double-counting.
