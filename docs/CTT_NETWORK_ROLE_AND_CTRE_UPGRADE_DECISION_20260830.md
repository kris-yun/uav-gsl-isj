# CTT network role and CTRE upgrade decision

> **SUPERSEDED ON 2026-08-30.** This development note authorized an H01 pilot
> before the later metric/prior/tie, calibrated-emission, exact-replacement and
> planner-consumer audits were formalized. Its evidence remains preserved, but
> its runtime authorization is withdrawn. The controlling contract is now
> docs/CTT_FINAL_THREE_MODULE_METHOD_REDERIVATION_20260830.md.

Date: 2026-08-30  
Status: **HISTORICAL DEVELOPMENT NOTE / PILOT AUTHORIZATION SUPERSEDED**

## 1. Decision in plain language

The current neural module is not useful as a source-likelihood model. It saw a sparse local wind patch and attempted to predict first-passage hazard, but it did not improve held-out hazard NLL over a zero-wind static model and wind shuffling did not make it meaningfully worse. This is a terminal NO-GO for that model and input representation, not proof that neural networks in general are impossible.

The native physical bank does contain strong source information. On 1,680 fresh-context cases, an oracle same-context physical ensemble achieved mean normalized true-source rank 0.13825 (random expectation approximately 0.5), median rank 20/210, Top-10 26.67%, and Top-5 15.42%. The information is therefore present in the source-by-transport physical response family.

However, precise first-passage timing is not the robust source mechanism. FULL first-passage was slightly worse than SURVIVAL_ONLY on mean normalized rank (0.13841 versus 0.13825; one-sided sign p=0.15385), and the time-permutation comparison missed the preregistered p<=0.01 threshold and reversed in context 11. The stable signal is reachability/detection, not arrival phase.

Two later frozen tests materially strengthen this decision. First, keeping one
transport member coherent across all stops improved mean normalized true-source
rank from 0.14841 to 0.13288 on 1,680 fresh physical cases (574 wins, 430
losses, 676 ties, exact one-sided p=3.09e-6), with no reversal in contexts
10--13. Second, the preregistered H01 historical source-update shadow produced
10/10 lower formal localization errors: mean error 5.0013 m became 2.8206 m,
pooled improvement was 43.60%, and there were no preregistered catastrophic
regressions.  No network, GADEN rerun, threshold fitting, temperature, blend or
PMFS posterior input was used in that shadow replay.

## 2. Why the current network failed

The network input did not contain the state needed to determine obstacle-driven transport topology:

- it received local wind along visited positions, binned into a 32x32 patch;
- unobserved cells were mean-filled;
- the new test contexts changed airflow configuration, direction, and speed;
- the output target was candidate first-passage hazard rather than the missing global flow/transport field.

This is an information bottleneck, not simply insufficient depth. The W-online sufficiency audit confirmed it: development-nearest local wind produced mean normalized rank 0.47935 and static mixing 0.49894, while same-context physics produced 0.13825. Fresh leave-one-context-out matching improved to 0.37941 overall but catastrophically reversed in context 12. A larger CNN or Transformer cannot infer an unobserved global corridor/recirculation topology from a representation that does not determine it.

## 3. Why this is not V3/ORR again

The failed V3 runtime used `simulateSourceInPosition()` to produce a 2-D PMFS hit-frequency map, sampled that map repeatedly at completed events, and then built a replacement posterior. Its frozen outcome was 18/30 improved, approximately 4.02% pooled improvement, with H01 degradation.

V3 had four structural problems that the new method must not repeat:

1. repeated blocks at one physical stop acted as pseudo-replicated spatial dimensions;
2. the operator was a PMFS occupancy/hit-frequency proxy, not native GADEN concentration passed through the persistent sensor;
3. transport evidence was compressed and could lose whole-trajectory member coherence;
4. the method replaced/reset useful PMFS posterior state, so it sometimes destroyed already-good states.

The proposed method requires the exact native physical chain and a likelihood-ratio correction; it is not a renamed V3 gate.

## 4. Frozen upgrade: Causal Transport Reachability Evidence (CTRE)

### 4.1 Generative factorization

For source carrier `S`, legal 3-D placement `U`, coherent transport realization `Z`, physical concentration `C`, persistent sensor state `R`, and observed block detection `Y`:

`do(S=s) -> U -> Z -> C_1:T -> R_1:T -> Y_1:B`.

`S` is the localization target. `U`, `Z`, source strength and sensor parameters are nuisance variables and must be fixed source-independently or marginalized. One `Z` remains coherent across all stops in a run.

### 4.2 Detection probability

For candidate `s`, transport member `z`, and physical stop `b`, the native simulator plus persistent sensor yields binary detection replicas `E[s,z,r,b]`. With Jeffreys smoothing:

`p[s,z,b] = (1/2 + sum_r E[s,z,r,b]) / (R + 1)`.

This is an observation probability, not an occupancy-to-ppm conversion.

### 4.3 Coherent sequential likelihood

For observations `y_b` at distinct physical stops:

`ell[s,z] = sum_b { y_b log p[s,z,b] + (1-y_b) log(1-p[s,z,b]) }`.

Transport is marginalized after accumulating the complete sequence:

`L_phys(s) = logsumexp_z( log pi_z + ell[s,z] )`.

It is forbidden to choose a different best transport member independently at each stop. Repeated blocks within one stop refine the sensor observation but do not create extra spatial sample units.

### 4.4 PMFS likelihood-ratio correction

Let `L_pmfs,t(s)` be the exact native PMFS likelihood contribution of the same new observation window and `L_phys,t(s)` the CTRE likelihood. The correction is:

`q_t^CTRE(s) proportional_to q_t^PMFS(s) * exp( L_phys,t(s) - L_pmfs,t(s) )`.

When `q_t^PMFS proportional_to q_(t-1) * exp(L_pmfs,t)`, this gives:

`q_t^CTRE proportional_to q_(t-1) * exp(L_phys,t)`.

Thus the high-fidelity observation operator replaces the approximate current-window operator exactly. There is no temperature, blend coefficient, posterior reset, error gate, or double use of the window.

### 4.5 Temporal claim

The temporal contribution is **coherent sequential reachability under a persistent sensor**, not exact within-stop arrival phase. First-passage time remains a preregistered ablation. It can return only after a new, unseen airflow-context experiment shows incremental ordering beyond ever/never detection.

## 5. Three publishable modules

### M1 — Interventional physical response bank (main causal mechanism)

- intervenes on each persistent source carrier with `do(S=s)`;
- samples legal 3-D placement and transport nuisance without source-dependent RNG;
- uses native GADEN concentration and the parity-proven persistent sensor;
- produces candidate-relative evidence before Bayesian accumulation.

### M2 — Reachability-detection observation operator (far-domain transfer)

- separates latent plume reachability from imperfect sensor detection, analogous to occupancy-detection models in ecology;
- uses proper Bernoulli predictive likelihood with finite-ensemble smoothing;
- preserves coherent transport identity and physical-stop statistical units.

### M3 — Exact sequential likelihood replacement (safety mechanism)

- corrects the native PMFS window by the physical-to-PMFS likelihood ratio;
- preserves the previous posterior and planner history;
- eliminates the V3 posterior-reset and double-counting failure.

These three modules act at different locations and do not compete: M1 creates the physical intervention family, M2 defines observations, and M3 integrates the evidence into PMFS.

## 6. Neural module decision

The direct neural hazard module is removed from the performance method.

A network may be reintroduced only in one of two auxiliary roles:

1. **Physics-field reconstruction:** map sparse source-independent wind measurements plus occupancy geometry to a global wind/transport field under PDE or projection constraints.
2. **Exact-operator compression:** approximate the frozen CTRE bank for speed after candidate-ordering parity is already demonstrated.

It must pass all of the following without source labels from the target environment:

- held-out airflow full-field velocity error versus static and nearest-context baselines;
- physical residual/divergence and obstacle-boundary consistency;
- CTRE candidate-ordering parity on held-out source interventions;
- no House-specific retraining, threshold, temperature, or posterior weight.

If it fails, the exact bank remains the scientific method and the network is omitted. The paper does not need a neural module to be scientifically complete.

## 7. Fast validation ladder

### Gate A — operator parity (no performance reading)

On frozen traces, verify native concentration, sensor state, block decisions, carrier mapping, source-independent RNG and exact PMFS window likelihood. Any mismatch stops implementation.

### Gate B — historical shadow development

Use the already-open H01/H02/H03 seeds 0..9 and their fixed trajectories. Compare PMFS and CTRE at every source update without changing the trajectory. Preregister:

- true-source rank change and expected-location error;
- false-confident-collapse count;
- FULL, minus-M1, minus-M2, minus-M3;
- source-label permutation and transport-member permutation controls.

Development GO requires pooled endpoint improvement >=10%, at least 20/30 improved, no House pooled degradation >5%, and zero new false-confident collapses. This stage may reject CTRE but cannot confirm it.

The first, House-specific portion of Gate B is now complete. H01 seeds 0..9
passed 10/10 with 43.60% pooled improvement. This does not satisfy the stated
30-run cross-House Gate B and is not a generalization claim. It authorizes only
the H01 revealed closed-loop pilot needed to test feedback through the planner.

### Gate C — one revealed closed-loop smoke

Only after Gate B GO: one already-revealed seed, 300 s, confirms runtime consumption, trajectory divergence, finite posterior and stop timing. Error is diagnostic only.

### Gate D — frozen development closed loop

Run H01/H02/H03 x seeds 0..9, OFF versus CTRE, 30 matched pairs. No mid-run inspection or modification.

### Gate E — confirmatory generalization

Freeze source, binary, launch, physical bank construction and all metrics; run previously unused seeds 10..19 or unseen airflow contexts. The final >=10% claim comes only from this stage.

## 8. Current authorization

- Direct hazard network: **terminal NO-GO**.
- Native source information: **present, primarily reachability/detection**.
- Coherent transport identity: **fresh-context diagnostic PASS**.
- H01 fixed-trajectory shadow: **10/10 improvement; 43.60% pooled development GO**.
- Exact arbitrary-position lookup: **engineering smoke PASS**; one native
  source/member queried all 626 H01 free cells for 1,500 samples per cell in
  2.76 s using the frozen RNG-enabled binary.
- H01 runtime takeover: **authorized only for one already-revealed 300 s pilot
  after lookup hash/parity and exact single-window replacement parity pass**.
- H02/H03 runtime and any cross-House or confirmatory >=10% claim: **not yet
  authorized**.

## 9. Interpretation of historical true-carrier rank

The formal metric improved for all ten H01 trajectories, but exact true-carrier
rank improved over native PMFS on only four final updates. In particular, some
fixed trajectories yield a spatially better top-5% expectation while assigning
low probability to the exact persistent carrier. Therefore the 43.60% result
must not be described as universal source identification. The closed-loop pilot
must preserve and report both the formal error and the exact-carrier rank/mass,
posterior variance, false-confident-collapse status and trajectory divergence.
This discrepancy is a falsification target, not a reason to tune CTRE after the
result.
