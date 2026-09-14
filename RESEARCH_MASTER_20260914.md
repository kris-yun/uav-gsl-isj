# UAV-GSL-ISJ — Research Master

Date: 2026-09-14

Branch: `project/research-master-20260914`
Base evidence head: `3cf57c079411d03205c820d9cc1f2dc5281083e4`

This branch is the **research-control branch**. It does not authorize algorithm or simulator changes. Its purpose is to keep one authoritative view of the scientific question, evidence, rejected routes, candidate theory, and the next falsification gate.

## Read in this order

1. `docs/PROJECT_SCIENTIFIC_QUESTION_AND_CORE_IDEA_20260914.md`
2. `docs/PROJECT_EVIDENCE_LEDGER_20260914.md`
3. `docs/BIG_SCIENCE_THEORY_MAP_20260914.md`
4. `docs/NEXT_STAGE_EXECUTION_CONTRACT_20260914.md`
5. `docs/PROJECT_RESEARCH_STATE_20260914.json`

## Current one-sentence research problem

> In turbulent gas transport with slow sensor dynamics, how can a mobile sensing system **design its measurement geometry and trajectory so that different source hypotheses remain physically distinguishable across transport regimes before Bayesian inference is allowed to update the source belief?**

The project is therefore no longer primarily about inventing another posterior correction. The dominant unresolved problem is **source identifiability under the measurement operator**.

## Current core scientific idea — CANDIDATE, not yet validated

Working name:

**Transport-Robust Persistent-Excitation Sensing**  
**输运鲁棒的持续激励感知**

Core principle:

> Do not ask the inference algorithm to recover source identity from a measurement trajectory that never excited all source directions. Design the sensing trajectory/formation first so that the weakest source-discriminating physical mode remains observable under multiple transport regimes; only then assimilate measurements into PMFS.

For a route/design `R`, transport regime `w`, and `S` controlled source hypotheses, collect source responses into `Y_w(R)`. Center across source hypotheses:

\[
C_w(R)=P_S Y_w(R),\qquad P_S=I-\frac1S\mathbf1\mathbf1^T.
\]

For four source hypotheses there are at most three independent source-contrast modes. A basic conditioning diagnostic is

\[
\gamma_w(R)=\frac{\sigma_3(C_w(R))}{\sigma_1(C_w(R))}.
\]

The current design objective is not expected posterior entropy. It is a worst-transport observability objective such as

\[
R^*=\arg\max_R\min_{w\in\mathcal W_{design}}\gamma_w(R),
\]

subject to a non-negligible weakest-mode energy, exposure/coverage, collision-free geometry, and deployment constraints.

This is closest to **persistent excitation / system identification / optimal experimental design**, not to a new Bayesian likelihood.

## Why the project arrived here

The strongest repeated failure pattern is now:

```text
more elaborate inference on the same weak observation stream
    -> sometimes changes ranking
    -> does not stably recover source identity across environments
```

while the newest dual-receiver experiment showed:

```text
same-frame dual trace integrity: PASS
signed two-point structure: formally rank 3
weakest source direction: ~10^-3 of dominant direction
held-wind source identity: 2/4
ordinary dual receiver: 1/4
```

The frozen route exposed `S_truth` hundreds of times, but some alternative source interventions only a handful of times or nearly never. That is an **experiment-design / observability failure before it is an inference failure**.

## Current status labels

### CONFIRMED

- `main_v8` remains the authoritative forward contract; `dataset_v1` is excluded.
- RMFE full32x2 did not improve H02 and exposed amplitude-scale/ranking failure.
- SCTT downstream did not outperform classic PMFS and shuffle contradicted the claimed temporal mechanism.
- M1R has development-screen gains, but its historical implementation/documentation do not justify a clean cross-domain causal claim.
- Old M2 transport-member averaging is NO-GO.
- Counterfactual exact microbank tests showed source effects can survive controlled transport changes when exact candidate-specific physical responses are available; this did not produce a deployable full-map provider.
- LMBT / CTAER / CFIR / Rank-2 / DPISC / CCDE / SCSP and related single-stream transformations did not establish stable full-support source identity.
- Same-frame dual-UAV data are technically feasible in House02 after geometry parity correction.
- Fixed 2 m signed two-point difference is NO-GO as the main algorithmic innovation: per-wind conditioning is about `6.8e-4`–`1.4e-3`, held-wind source rank is 2/4, and a 5 s time mismatch improves to 3/4.
- House02 has enough physical space for a 2 m dual-UAV formation; the earlier route-only infeasibility was not a whole-map limitation.

### CURRENTLY TESTING

- Whether the 5 s mismatch improvement is a motion-revisit artifact rather than a plume-advection cue.
- Whether source-blind measurement-route design can turn the source-response operator from practically rank-collapsed into well-conditioned without changing the inference rule.

### PRIMARY CANDIDATE THEORY

**Persistent excitation + robust optimal experimental design / observability-first sensing.**

### SECONDARY CANDIDATE MODULE — only if the primary premise passes

**Collective multi-trajectory informativity** for two UAVs.

If no single safe trajectory can excite all source directions, two UAVs should not be treated as two ordinary PMFS agents or a simple difference pair. They may instead be assigned **complementary trajectories whose stacked measurements are collectively persistently exciting**. This maps directly to modern multi-signal informativity theory and is the strongest current candidate for a genuine second module.

### CANDIDATE BIOPHYSICAL ROUTE PRIOR — not yet a module

2026 Nature work on Drosophila plume-edge navigation suggests that plume boundaries can act as high-information spatial landmarks. This may later motivate a route generator that seeks plume-boundary transitions, but it is not authorized as a main contribution until the observability-first premise passes and collision with existing plume-tracking work is screened.

### REJECTED OR DEMOTED AS MAIN INNOVATION

- fixed-A RMFE ranking;
- SCTT as a causal temporal module;
- global transport-invariant representation;
- old M2 member averaging;
- TSBIE transport-member reweighting;
- local-wind continuum causal provider;
- simple causal posterior repair on the same single-UAV gas stream;
- signed simultaneous two-point difference / second-order difference as the main dual-UAV algorithm;
- ordinary multi-robot fusion, Product-of-Experts, or 'two robots give more data' as novelty;
- ME-ACI V11 as established cross-domain evidence (later multiseed qualification is NO-GO).

## Paper-level claim boundary today

The project **does not yet have a validated cross-dataset main innovation**.

The strongest defensible paper-level scientific narrative today is:

1. PMFS and several increasingly sophisticated source-evidence transforms fail when the sensing trajectory does not physically excite source-discriminating modes.
2. These failures expose an identifiability bottleneck upstream of Bayesian assimilation.
3. The new research direction is to make source identity observable by design, using transport-robust persistent excitation / optimal experimental design principles.
4. Only if that premise succeeds on frozen development winds and an untouched held transport regime should it be promoted to the paper's main innovation.

## Immediate next decision

Run the contract in `docs/NEXT_STAGE_EXECUTION_CONTRACT_20260914.md`.

The decisive question is:

> Can measurement design alone, with the same sensor physics and the same simple source evaluator, raise the weakest source mode from the current ~10^-3 regime to the pre-registered observability regime and recover 4/4 held-wind source identity?

If YES: freeze the mechanism, run novelty collision, then prepare untouched cross-environment confirmation.

If NO: stop modifying inference under the current sensing modality and redesign the physical sensing modality / environment before proposing another algorithm.
