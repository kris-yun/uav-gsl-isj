# CESS Novelty Boundary v1

Date: 2026-09-25

Status:
**PRIOR-ART BOUNDARY FOR MAINLINE CLAIMS**

## 1. Claims that are NOT novel

The project must not claim novelty for any of the following in isolation:

- coarse-graining micro states into macro states;
- multiresolution / multigranularity representation;
- causal-emergence-inspired representation learning;
- maximizing effective information;
- finite-sample state aggregation;
- clustering statistically similar states;
- hierarchical pooling / shrinkage;
- restoring/refining a macro prediction to fine labels;
- using binary odor encounters;
- using source probability maps.

Relevant nearby work includes:

### AAAI 2025 — emergence-inspired multi-granularity causal learning

Luo et al.,
*Emergence-Inspired Multi-Granularity Causal Learning*,
AAAI 2025,
DOI 10.1609/aaai.v39i18.34113.

This already uses emergence inspiration, progressive micro-to-macro mapping and
micro/macro consistency in causal-structure learning.

Therefore "emergence-inspired multi-granularity learning" is not a sufficient
novelty claim.

### UAI 2023 — finite-sample state aggregation

Geng et al.,
*A Data-Driven State Aggregation Approach for Dynamic Discrete Choice Models*,
UAI 2023.

This already develops data-driven state aggregation with finite-sample error
bounds and explicitly studies complexity / estimation-error / sample-complexity
trade-offs.

Therefore "aggregation reduces finite-sample estimation error" is not by itself
new.

### Causal-emergence literature

Recent 2025/2026 work includes SVD/effective-information formulations and a
2026 reframing of the causal-emergence landscape.

Therefore the project must not imply that it invented causal emergence,
effective information, or macro-scale causal descriptions.

---

## 2. Candidate defensible novelty bundle

If future frozen gates succeed, the defensible contribution is the combination
of the following elements in stochastic gas-source localization:

1. **Repeated-realization source identifiability as the scientific object**

   Source scale is determined from independent turbulent plume realizations,
   not from a fixed geometric resolution or endpoint-error tolerance.

2. **Source-state coarse-graining under a fixed micro source task**

   The final inference task remains the same set of fine candidate source
   cells.

3. **Uncertainty-preserving macro-to-micro posterior**

   Every macro posterior is lifted back to the original PMFS source support
   without inventing within-macro evidence.

4. **Exact information-fidelity decomposition**

   For a source partition \(M=g(S)\), the oracle hard-coarse-graining log-loss
   penalty is exactly

   \[
   I(S;Y\mid M).
   \]

   Finite-sample improvement is therefore interpreted as estimation-risk
   reduction exceeding this unavoidable fidelity loss, not as information
   creation.

5. **Untouched-target same-support proper-score confirmation**

   Candidate and identity models are compared on exactly the same microcell
   support, prior, observations and final targets.

6. **Explicit ordinary-pooling challenge**

   Geometry pooling, profile clustering, hierarchical shrinkage and random
   groupings are treated as serious baselines rather than weak controls.

7. **PMFS-compatible probability-map output**

   The method preserves the source-location probability-map object required by
   the application rather than replacing localization with macro-label
   classification.

No single item above is necessarily novel alone.
The paper-level novelty depends on their integrated use to solve the
realization-dependent source-identifiability problem exposed by the project.

---

## 3. Claim ladder

### Safe now

"causal-emergence-inspired multiscale statistical source identifiability"

### Safe only after D1C fresh-target confirmation

"finite-sample emergent source scale improves microcell source inference under
stochastic plume realizations"

### Safe only after cross-wind / cross-House validation and stronger theory

"causal-emergent source macrostates"

### Not currently safe

"causal emergence is proven in gas-source localization"

"macro source states contain more true information than micro source states"

"the method discovers the globally optimal source scale"

---

## 4. What can still kill the mainline

The stronger mainline should be downgraded or stopped if:

- ordinary pooling/shrinkage matches the candidate under the same budget;
- the partition is unstable across reference splits;
- the selected scale changes arbitrarily with observation protocol;
- fresh-target microcell proper score does not improve;
- improvement comes only from changing the source prior or task;
- gains disappear under cross-wind / cross-House validation;
- the final probability map hides unresolved within-macro uncertainty.

The project should prefer a narrower correct statistical-identifiability claim
over an overstated causal-emergence claim.
