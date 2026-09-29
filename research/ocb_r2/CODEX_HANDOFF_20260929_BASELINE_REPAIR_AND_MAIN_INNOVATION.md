# 2026-09-29 Research Handoff — OCB-R2 Baseline Repair and Main-Innovation Search

## Executive summary

Today's most important result is **not a new algorithm**. It is the repair of the experimental baseline.

A large part of the earlier House01/House02/House03 evidence was produced under conditions that were not cleanly comparable across source hypotheses or across historical/current simulator generations. In particular:

- source position could change together with wind family and gas type;
- the historical simulator produced 2000 records while the current simulator produced 1803;
- historical/current time semantics and wind-update ordering differed;
- the historical RNG state/seed was not recoverable;
- some old candidate banks belonged to older PMFS/GADEN contracts.

Therefore earlier positive/negative results remain useful as **legacy discovery evidence**, but they must not be interpreted as clean prospective cross-dataset confirmation.

Today OCB-R2 established a reproducible, explicitly seeded prospective benchmark that separates:
1. simulator reproducibility;
2. stochastic realization;
3. source identity;
4. wind/gas/environment conditioning;
5. discovery versus confirmation.

This changes how the main innovation should be searched and validated from now on.

---

## 1. Benchmark repair completed today

### 1.1 Historical/current timebase mismatch identified

Historical generator evidence:

- approximately 2000 records over 1000 s;
- first record 0 s;
- last record about 999.5 s;
- binary64-style simulation clock;
- floor(time/0.5)-type save semantics.

Current generator:

- 1803 records;
- first record 0 s;
- last record about 999.502991 s;
- accumulated binary32 clock;
- strict `>` save condition;
- different wind-update ordering.

The previously frozen 10 historical target record IDs had:

- exact physical-time matches: 0/10;
- maximum nearest-time error: about 0.299805 s;
- matching wind index: 1/10.

Conclusion:

`CURRENT_1803_BINARY_NOT_ELIGIBLE_FOR_OCB_R1_REFERENCE`

This showed that old/new data could not be treated as if they came from the same generator merely by matching record number or nominal save interval.

### 1.2 Historical simulator parity could not be recovered

No historical-equivalent executable was proven.

A rebuild path stopped before producing a binary because the historical ROS1/catkin environment was not available.

More importantly, historical RNG provenance was unrecoverable:

- C RNG used wall-clock initialization;
- thread-local Boost RNG also used time-dependent initialization;
- old outputs did not preserve the RNG seed/state.

Conclusion:

`OCB_R1_HISTORICAL_PARITY_UNRECOVERABLE`

This does **not** invalidate historical data. It means old data are legacy evidence, not a deterministic same-seed prospective benchmark.

### 1.3 OCB-R2 deterministic prospective generator established

A new isolated prospective generator was frozen with:

- explicit master seed;
- deterministic RNG stream initialization;
- no wall-clock RNG seed in the frozen path;
- read-only run/timeline provenance instrumentation;
- plume physics unchanged.

Frozen binary SHA256:

`ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688`

Qualification:

`A(S1) -> B(S2) -> C(S1)`

Results:

- 1803/1803/1803 records;
- timeline exact across all three;
- wind-index sequence exact;
- A versus C: 1803/1803 scientific outputs byte-identical;
- A versus B: 1802/1803 different, with only the expected first empty record equal;
- 5409/5409 output hashes independently verified.

Decision:

`OCB_R2_GENERATOR_REFOUNDATION_PASS`

Any future binary hash change invalidates benchmark qualification until the same A-B-C test is repeated.

### 1.4 S1 structural smoke passed

H01/H02 eight original source×wind configurations were run with one frozen seed each.

Decision:

`OCB_R2_S1_H12_STRUCTURAL_PASS`

- H01: 4/4 PASS;
- H02: 4/4 PASS;
- 8/8 record, asset, provenance and scientific-sanity contracts passed;
- H03 remained sealed.

### 1.5 S2 prospective discovery dataset passed

32 H01/H02 discovery runs were generated:

- H01: 16/16 PASS;
- H02: 16/16 PASS;
- every run has 1803 records;
- time axis 0 to 999.502991 s;
- archived with post-copy SHA256 verification;
- eight runs that reused S1 seeds reproduced S1 scientific outputs exactly.

Decision:

`OCB_R2_S2_DISCOVERY_DATASET_PASS`

No PMFS, source ranking or method analysis was used to qualify this dataset.

### 1.6 D0A exposed source-comparison confounding

The original S2 design had eight fixed House-wind-gas strata, but each stratum contained:

`1 source x 4 stochastic realizations`

Within both H01 and H02, changing the configured source also changed wind family and gas type.

Therefore a direct source-rank test would confound source identity with environmental configuration.

Decision:

`OCB_R2_D0_HOLD_COMPARABILITY`

No M0, P, Q-time or dependence score was computed.

This HOLD is a task-design problem, not evidence that temporal dependence is absent.

### 1.7 S2X matched-source crossover repair passed

S2X added the missing source under each already-qualified non-source condition.

32 crossed-source runs were generated.

Decision:

`OCB_R2_S2X_MATCHED_SOURCE_DATASET_PASS`

Combined S2+S2X now gives:

`8 fixed House-wind-gas contexts x 2 source locations x 4 independent realizations/source`

All 32 S2X runs:

- used the same frozen generator;
- had 1803 records;
- matched parent wind-index sequences;
- were archived with file-by-file SHA256 verification;
- did not open confirmation or H03.

This is the first clean prospective panel in this project where source identity can be studied while House, wind, gas, occupancy, generator and time semantics are fixed.

---

## 2. Why earlier House123 conclusions need reinterpretation

The key lesson from today is:

> Earlier "cross-house" or "new-data" failures often changed more than the method-testing variable.

Potentially changing together were:

- source position;
- wind family;
- gas type;
- simulator version / timebase;
- wind update ordering;
- stochastic plume realization;
- candidate-bank provenance.

Therefore statements such as:

- "the old data had a signal but the new data did not";
- "the method fails to generalize across House01/02/03";
- "House03 contradicts House01/02";

must now be treated cautiously unless they were already based on a clean matched contract.

Do **not** erase the old work. Its proper role is:

- mechanism discovery;
- failure-mode discovery;
- hypothesis generation;
- identifying promising modules;
- identifying what not to repeat.

But final mainline promotion now requires prospective OCB-R2 evidence.

---

## 3. Current mainline: return first to AOD because it already has positive evidence

Do not treat every old route equally.

AOD has already shown repeated positive evidence before OCB-R2.

### 3.1 Old AOD positive evidence

Original AOD idea:

`u-ABS` versus `rawu-ABS`

Only the amplitude readout operator changes.

- `rawu`: pre-blur amplitude / filament-count readout;
- `u`: Native 1.5-cell Gaussian-blurred amplitude;
- same B2 positive-gain profile SSE;
- no centered transform;
- no conditional filter;
- no learned calibration.

On the old OPEN H01/H02 development material, the unblurred readout improved source identification in some environments.

On the fresh House03 full-support F1:

- support: 624 legal candidates;
- 12 truth sources;
- 8 independent plume realizations/source;
- 96 fresh target plumes;
- nominal unique Top1:
  - u: 0.0520833
  - rawu: 0.1041667
- Delta unique Top1: +0.0520833;
- bootstrap 95% CI: [0.0364583, 0.0729167];
- nominal rescued/harmed target-path observations: 11 / 1.

Decision:

`AOD_F1_FULL624_CONFIRMED_STRESS_NONINFERIOR`

But AOD was heterogeneous:

- mean truth rank did not improve globally;
- MAP error did not improve globally;
- only some sources benefited;
- later centered/conditional-filter variants did not solve the problem.

Therefore the correct question is not "AOD already works".

The correct question is:

> Does the original unblurred-amplitude mechanism replicate under the repaired OCB-R2 stochastic benchmark, and if so, where and why?

### 3.2 AOD-R2 transfer audit completed

Branch:

`codex/aod-r2-transfer-audit-20260929`

Commit:

`53b92c87f99d64045b108b4fd0b881110c7d5e2c`

Results:

- 3/8 H01/H02 contexts already have complete legal rawu candidate banks that might be reusable after strict asset checks;
- 5/8 contexts have no full legal bank;
- brute-force full completion would require about 268,224 PMFS candidate forwards;
- no new GADEN plume is needed;
- 1,584 old forward maps verified the frozen rawu->u blur operator;
- however, old/new bank campaign provenance must not be silently mixed;
- the four configured H01/H02 truths are off the exact PMFS candidate centers;
- some true-source z coordinates also differ from the PMFS template plane z=0.20 m;
- therefore old exact-cell truth Top1/rank cannot be copied directly.

The transfer audit correctly stopped before reading target concentration.

### 3.3 Current AOD-R2 step in progress

Codex is currently executing:

`AOD_R2_F0_MATCHED_SOURCE_NEIGHBORHOOD_GATE`

Purpose:

- use the 64 clean discovery plumes from S2+S2X;
- no new GADEN;
- no confirmation;
- no H03;
- no centered AOD;
- no conditional filter;
- no neural network;
- no dependence score.

Instead of immediately paying for a full 596/630-candidate bank, F0 tests whether the original AOD mechanism still gives a local matched-source discrimination signal.

The proposed local endpoint uses:

- source-blind E1 H01/H02 probes;
- physical-time observations frozen before concentration readout;
- legal PMFS source neighborhoods around the continuous true XY source positions;
- original `u-ABS` versus `rawu-ABS`;
- the same frozen B2 gain-profile SSE;
- rescue/harm and true-neighborhood versus alternative-neighborhood margin.

If F0 is positive, only then consider full-support AOD-R2.

If F0 is heterogeneous, investigate the mechanism before spending the full forward budget.

If F0 has no signal, stop AOD and do not rescue it with post-hoc variants.

---

## 4. Main-innovation search doctrine

The project still requires:

> **one main innovation + two auxiliary innovations**

The main innovation must be a scientific idea that can carry the paper, not an engineering patch.

### 4.1 What qualifies as a main innovation

A candidate should satisfy all of the following:

1. **Clear mother theory from a distant field**
   - examples: causal inference, world models, statistical physics, information geometry, biological sensing, copula/dependence theory, emergence;
   - preferably 2025/2026 top venue;
   - theory must be explainable independently of PMFS.

2. **A real failure mechanism in current gas-source localization**
   - not "we add another module";
   - must state what PMFS or the current observation/inference process systematically gets wrong.

3. **A second innovation, not direct copying**
   - transfer the mother principle into a source-localization-specific mathematical object;
   - derive a new source score, factorization, representation, or update rule;
   - preserve the PMFS-style source probability map as final output if useful, while internal inference may be replaced.

4. **Offline positive evidence before closed loop**
   - first identify the mechanism on frozen discovery data;
   - then formulate the method;
   - then freeze;
   - only then open independent confirmation.

5. **Cross-realization and cross-environment stability**
   - effect must not come from one lucky plume seed;
   - must not be driven by one House only;
   - must survive matched non-source conditions.

6. **Source discrimination, not merely predictive fit**
   - better reconstruction/predictive density is not enough;
   - improved confidence is not enough;
   - the method must provide information that helps source localization.

7. **Deployability path**
   - after offline confirmation, the object must have a credible online/closed-loop implementation within the UAV search budget.

### 4.2 What does NOT qualify

Do not promote as main innovation:

- ad-hoc weighting;
- arbitrary posterior temperature;
- manually tuned thresholds;
- global normalization with no physical mechanism;
- "another loss function";
- merely changing observation dwell time;
- a complex neural model before a mechanism is shown;
- a method that only improves predictive density;
- a method that only improves confidence/separability while source rank worsens;
- a method that needs truth labels online;
- a result that works only on one old dataset realization.

---

## 5. Search strategy from now on

Do not run many candidate methods in parallel.

Use a serial mechanism-first loop:

### Stage A — recover/promote the strongest legacy positive signal

Priority 1 is AOD because it already showed repeated positive evidence.

Question:

> Is the amplitude blur itself destroying source-discriminative information under controlled stochastic realization?

Do not add new modules until this is answered on OCB-R2.

### Stage B — if AOD replicates, diagnose the remaining defect

Known old defect:

- Top1 can improve;
- global rank/MAP may not improve;
- effect is source-dependent.

Therefore if AOD-R2 F0 is positive, the next scientific task is to identify **when local unblurred amplitude is trustworthy** and when native smoothed/global evidence should dominate.

Possible second-innovation direction should emerge from data, not be invented first.

Candidate high-level form:

- preserve stable coarse/global PMFS evidence;
- use unblurred amplitude only to resolve local source ambiguity;
- avoid globally replacing a stable channel with a high-variance channel.

A proper far-domain mother theory must be found before calling this a publishable module.

### Stage C — if AOD fails prospectively, stop it

Do not rescue AOD with:

- centered transforms;
- learned conditional filters;
- different blur widths;
- target-dependent thresholds;
- new seed selection.

Those routes have already shown failure/instability.

Then move to the next strongest mechanistic candidate.

### Stage D — backup route: marginal-preserving temporal dependence

The dependence route is **not currently the primary line**, but S2X has now repaired the source-comparability problem that blocked D0A.

The mother principle:

> preserve complete marginal source evidence, destroy only cross-time realization dependence, then measure the lost source information.

This is linked to modern copula/dependence work.

Important rule:

- never replace the full spatial marginal field with the old 10-D count trajectory;
- temporal dependence can only be an incremental residual on top of strong marginal evidence.

If AOD stops, rerun D0A on S2+S2X and then execute the frozen marginal-preserving dependence gate.

### Stage E — only search for a new far-domain mother theory if both AOD and dependence fail

Do not continuously invent new modules while unresolved positive evidence exists.

If both fail prospectively:

1. freeze their failures;
2. state the observed failure mechanism;
3. search 2025/2026 top papers in distant fields;
4. shortlist only theories that directly match that mechanism;
5. implement the cheapest offline falsification test;
6. STOP immediately on no signal;
7. repeat.

The goal is not novelty by vocabulary. The goal is a mother theory that predicts a measurable, source-relevant effect in the repaired benchmark.

---

## 6. Data split and leakage rules

The repaired benchmark must remain staged.

### Discovery

Current open discovery material:

- S2: 32 H01/H02 original-config runs;
- S2X: 32 H01/H02 matched-source crossover runs.

Total current clean discovery plume bank:

`64 runs`

Use only these for:

- mechanism analysis;
- method derivation;
- hyperparameter choice;
- ablation design.

### Independent stochastic confirmation

The original H01/H02 confirmation seeds remain sealed.

Do not generate/open them until:

- the scientific method is frozen;
- all formulas and hyperparameters are fixed;
- success/failure gates are committed.

### External-house confirmation

House03 remains sealed in the OCB-R2 prospective benchmark.

Do not use H03 to tune the new method.

Historical House03 AOD work is legacy evidence and must be clearly distinguished from the still-sealed prospective OCB-R2 H03 confirmation.

### Closed loop

No closed-loop Codex campaign until:

1. discovery mechanism positive;
2. method frozen;
3. independent H01/H02 confirmation passes;
4. H03 sealed confirmation is acceptable.

---

## 7. Interpretation of old NO-GO/HOLD routes

Do not automatically rerun every failed historical route.

Use this rule:

### Keep the old verdict as a route warning if:

- the failure was internal to the method;
- the method failed even under its own matched development comparison;
- the mechanism itself was absent;
- the route was already known prior art in olfaction/GSL.

Examples of routes that should not be casually revived:

- TNQC quotient projection;
- generic active observability already used in the field;
- DRPE-style route with existing olfactory overlap;
- HCMC route after independent offline failure;
- M4-v3 after its own operator/linearity gates failed;
- AOD conditional-filter variants that improved predictive density but not source inference.

### Revisit only if:

- today's benchmark repair specifically removes the confound that dominated the earlier conclusion;
- there was a real legacy positive signal;
- the new test can be made cheap and preregistered.

AOD satisfies this criterion.

The marginal-preserving dependence signal may also satisfy it after AOD is resolved.

---

## 8. Immediate execution order for Codex

### Current task

Finish:

`AOD_R2_F0_MATCHED_SOURCE_NEIGHBORHOOD_GATE`

Do not change its frozen contract after target values are exposed.

### If F0 = LOCAL_SIGNAL_POSITIVE

1. stop and package;
2. audit whether the positive effect is:
   - cross-House;
   - cross-source;
   - cross-seed;
   - not driven by one context;
3. design a full-support AOD-R2 validation protocol;
4. only then consider generating the missing complete PMFS candidate banks;
5. do not yet open confirmation/H03.

### If F0 = HETEROGENEOUS_HOLD

1. stop;
2. identify the fixed pre-target covariates associated with gain/loss;
3. determine whether a principled far-domain theory explains the heterogeneity;
4. permit one preregistered secondary mechanism test only if theory predicts it;
5. otherwise stop AOD.

### If F0 = NO_SIGNAL

1. freeze AOD-R2 NO-GO on the repaired prospective benchmark;
2. do not tune AOD;
3. rerun D0A on S2+S2X metadata;
4. if D0A passes, execute the marginal-preserving dependence gate;
5. if dependence is not incremental, stop that route too and begin a new far-domain literature search.

---

## 9. What Codex should report every cycle

For every candidate mechanism, report:

- exact branch and commit;
- exact frozen inputs;
- exact benchmark split used;
- whether any confirmation/H03 data were touched;
- mother-theory source and novelty boundary;
- scientific failure mechanism addressed;
- preregistered metric/gate;
- per-House result;
- per-context result;
- per-source result;
- per-realization result;
- whether gain is localized to one stratum;
- destructive/null controls where applicable;
- decision: PASS / HOLD / NO-GO / STOP;
- next authorized action only.

Do not advance automatically after a PASS. Stop for review.

---

## 10. One-sentence handoff

> The project should now stop treating old House123 comparisons as clean cross-dataset confirmation, use the repaired OCB-R2 matched prospective benchmark as the only promotion gate, finish the original AOD `u-ABS -> rawu-ABS` prospective mechanism replication first because it already has repeated legacy positive evidence, and only if AOD fails move to the now-repaired marginal-preserving dependence route; every future main-innovation candidate must come from a clear distant-field mother theory, show a source-relevant mechanism offline, survive cross-seed/cross-context controls, then freeze before confirmation/H03/closed-loop.
