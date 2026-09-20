# Candidate Auxiliary M3 — Anytime-Valid Evidence Accounting for PMFS

Date: 2026-09-20
Branch: research/remote-paradigm-loop-20260919
Status: CANDIDATE / OFFLINE FALSIFICATION ONLY

## 1. Why the previous conformal M3 is demoted

A direct 2025/2026 collision screen found source-detection/source-localization work already using conformal prediction or closely related calibrated source sets. Conformal calibration remains useful as an evaluation tool, but it is no longer strong enough to count as one of the paper's three innovations.

## 2. New remote-domain source

### Sequential anytime-valid inference / e-values / e-processes

Primary recent anchors:

- ICML 2025 — Csillag, Struchiner, Goedert, *Prediction-Powered E-Values*.
- NeurIPS 2025 — Kilian, Cortinovis, Caron, *Anytime-valid, Bayes-assisted, Prediction-Powered Inference*.
- JRSS Series B 2026 — *Combining evidence across filtrations*.

Supporting lineage:
- PNAS 2024 — e-values as a decision-theoretic evidence object.
- Philosophical Transactions A 2023 — Grünwald, *The E-Posterior*.

The transfer target is not generic confidence calibration. It is **sequential evidence accounting**.

## 3. Project-specific failure mechanism

The native PMFS code reveals a concrete repeated-evidence hazard.

### Measurement propagation

PMFSLib::EstimateHitProbabilities(...) takes one hit/miss observation and propagates the local estimate through the map. Every free cell then receives a Bayesian-binary-filter log-odds update:

    cell.logOdds += cell.auxWeight - logOddsPrior;

Thus one physical sensing event can alter many spatial cells.

### Source scoring

Simulations::sourceProbFromMaps(...) then iterates over all free cells and multiplies one compatibility factor per cell:

    long double total = 1;
    for (int i = 0; i < measuredHitProb.data.size(); i++)
    {
        if (measuredHitProb.occupancy[i] != Occupancy::Free)
            continue;
        double sourceGivenThisCell =
            probabilityFromSingleCell(measuredHitProb.data[i], hitMap[i]);
        total *= sourceGivenThisCell;
    }

The per-cell compiled frequency score is:

    1 - abs(measured - simulated) * sourceDiscriminationPower

These are compatibility factors, not a proven factorization into conditionally independent observation likelihoods.

Therefore the same physical observation can be spatially replicated and then multiplied across many cells. The repository's 2026-09-08 failure audit already flags this as an overconfidence risk.

The later CER/M1 repair explicitly changed the semantics: each completed StopAndMeasure block enters once and spatial propagation is not recounted as independent evidence. That repair passed the exposed House123 development screen in 2/3 endpoint error and 3/3 AUC, showing that evidence-accounting semantics can materially change downstream behavior.

## 4. Scientific transfer

The auxiliary idea is:

> treat every genuinely new sensing block as one sequential evidence increment, and maintain an anytime-valid evidence process whose validity is tied to the information filtration actually available at that time.

This directly addresses:
- repeated spatial reuse of one measurement;
- repeated temporal monitoring;
- optional stopping / variable mission length;
- combining a predictive-latent evidence stream with an extreme-event/intermittency stream.

The core object is an event-level e-process, not a post-hoc confidence interval.

## 5. Proposed role in the 1+2 method

M1: Predictive self-supervised physical representation.

M2: Extreme-event-aware intermittency preservation.

M3: Anytime-valid event evidence accounting.

M1 and M2 produce candidate-conditioned evidence from a completed observation block. M3 controls how those increments are accumulated across time and across the two evidence streams.

Final output remains a PMFS-compatible source-location probability map. M3 is an evidence-accounting layer; it does not replace the map.

## 6. Minimal mathematical form

For source candidate s and completed event block i, construct a nonnegative evidence factor e_i(s) from the frozen representation score using only information available before/at block i.

Candidate wealth:

E_t(s) = product_{i <= t} e_i(s)

with the construction constrained so that, under the null/model class for candidate s, E_t(s) is an e-process or a conservative approximation to one.

The deployable map can use an evidence-tempered update such as

log w_t(s) = log w_{t-1}(s) + g(log e_i(s))

followed by normalization over source cells.

Important:
- the normalized map is still a localization belief representation;
- e-values themselves are not probabilities and must not be mislabeled as posterior probabilities;
- validity must come from the event-level construction, not from merely exponentiating a neural score.

## 7. Mandatory destructive controls

This auxiliary is killed unless all controls pass.

1. Duplicate-block control: replaying the identical completed sensing block without a new observation must not create new evidence.
2. Spatial-replication control: copying one observation into additional propagated map cells must not increase candidate evidence.
3. Time-permutation control: if M1/M2 claim chronological evidence, deliberate block permutation must degrade or alter the evidence process in the predicted way.
4. Null/no-support control: in zero-support source×wind segments, cumulative evidence must remain neutral/weak rather than sharpening the map.
5. Stopping-time control: decisions at arbitrary intermediate source-update times must retain the preregistered guarantee associated with the chosen e-process construction.
6. Matched-baseline control: compare against ordinary sequential Bayes / likelihood-ratio accumulation using exactly the same M1/M2 scores.

## 8. Novelty collision status

Current targeted search found:
- many sequential source-detection methods using SPRT or ordinary likelihood ratios;
- no direct gas/odor source-localization work using e-values/e-processes or anytime-valid event evidence accounting;
- no direct PMFS work treating repeated spatial propagation through a filtration-aware evidence process.

Status: POSITIVE NOVELTY SIGNAL, NOT YET A NOVELTY CLAIM.

## 9. Why this is stronger than conformal as M3

Conformal mainly calibrates the uncertainty of an output set.

The current PMFS project has a more upstream problem: how sequential evidence is counted before the probability map becomes sharp.

E-processes target that exact mechanism:
- one block -> one admissible increment;
- evidence can be monitored continuously;
- repeated/optional monitoring is part of the theory;
- multiple evidence streams can be combined only under explicit filtration assumptions.

This makes M3 mechanistically connected to the project's historical overconfidence/recounting issue rather than merely adding a reliability wrapper after inference.

## 10. Current decision

M3_CONFORMAL = DEMOTED_TO_EVALUATION_TOOL
M3_EPROCESS = ACTIVE_AUXILIARY_CANDIDATE
CLOSED_LOOP = NOT_AUTHORIZED

Next gate:
- reconstruct the source-update evidence sequence from archived PMFS/M1 runs;
- quantify whether native map multiplication produces evidence growth unsupported by genuinely new completed sensing blocks;
- build the smallest event-level e-process proxy and run duplicate/spatial-replication/null-support destructive controls before integrating it with M1/M2.

## 11. Existing closed-loop evidence for the counting problem

The repository already contains a particularly strong falsification/repair sequence.

### CORE-M1S seed11

docs/PMFS_CORE_M1S_HOUSE123_SEED11_RESULT_20260908.md reports:
- preregistered majority gate PASS (H01/H02 improved, H03 failed);
- in H03, posterior entropy collapsed to 0.694881 over two candidates while localization slightly worsened;
- runtime attribution found that one chosen sensing position was held for eight internal 2 s measurement blocks;
- M1S treated all eight as independent position interventions;
- a typical source window therefore used **24 likelihood factors for only three newly executed sensing positions**.

The project diagnosis was explicit: **temporal composite-likelihood overconfidence**.

This is exactly the type of evidence-accounting pathology that an event-filtration formulation must prevent.

### Existing partial repair

The frozen follow-up M1P retained the event-time contrast but recorded only the terminal measurement block of each completed physical sensing stop.

Separately, CORE-M1E used disjoint sequential event windows and achieved:
- H01 final +0.480 m, AUC +82.279 m s;
- H02 final -1.503 m, AUC +0.440 m s;
- H03 final +2.279 m, AUC +105.469 m s;
- mean final +0.419 m and mean AUC +62.730 m s.

This does not validate an e-process. It does show that **changing the evidential unit from repeated internal blocks toward disjoint genuinely new events materially changes closed-loop behavior**.

### Consequence

The M3 premise is no longer merely source-code suspicion.

There are now three independent project facts:
1. native PMFS spatially propagates one observation and later multiplies per-cell compatibility factors;
2. M1S explicitly overcounted 24 likelihood factors for three physical sensing positions and produced an overconfident H03 failure;
3. disjoint sequential event windows are already technically feasible and have produced real cross-House development gains.

Therefore the remaining research question is not whether evidence duplication can occur; it can.
The open question is whether a **formally anytime-valid event-level evidence process** gives an incremental advantage over the already implemented disjoint sequential likelihood baseline.

## 12. Updated gate

M3 advances only if, on the same frozen event scores:

- duplicate internal blocks cannot increase evidence;
- three physical stops produce at most three admissible evidence increments;
- arbitrary source-update stopping times remain valid;
- candidate elimination or map contraction is less overconfident than ordinary composite-likelihood accumulation;
- and the method improves calibration/rank without simply flattening every map.

If ordinary disjoint sequential likelihood already matches the e-process on all these controls, M3 is rejected as unnecessary theory.
