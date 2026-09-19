# Reserve M1 Screen — Marked Temporal Point-Process Inference

Date: 2026-09-19
Branch: research/remote-paradigm-loop-20260919
Status: RESERVE / OFFLINE SCREENING ONLY

## 1. Remote-field paradigm

Primary 2026/2025 top-venue sources:

- **ICLR 2026 — Berghaus et al., _In-Context Learning of Temporal Point Processes with Foundation Inference Models_.**
  - treats multi-type event histories with marked temporal point processes;
  - pretrains a Foundation Inference Model to infer conditional intensity functions in-context from event-sequence sets;
  - transfers to target event systems without separate target-specific training.

- **NeurIPS 2025 — Chang et al., _Deep Continuous-Time State-Space Models for Marked Event Sequences_.**
  - models irregular event histories in continuous time with stochastic jump dynamics;
  - strong inductive bias for marked event sequences and efficient linear-complexity inference.

Supporting 2026 biological evidence:
- recent olfactory-neuroscience work treats intermittent odor pulses as discrete evidence rather than smooth concentration.

## 2. GSL translation

Main scientific hypothesis:

> In intermittent turbulent plumes, source identity may be encoded more robustly in the conditional rate, timing, duration and marks of whiff events than in a continuously sampled concentration trace.

Observation history becomes a marked point process:
- event time = whiff onset / plume encounter;
- duration = event persistence;
- mark = peak concentration / integrated exposure / local wind context;
- source candidate controls the event-intensity law.

The source probability map would be obtained from event-history likelihood or an amortized point-process inference head.

## 3. Existing-data point-process proxy

The 12 controlled H01/H02/H03 × {SA,SB} × {fast,slow} histories were converted into whiff events at two fixed diagnostic thresholds:
- 0.01 ppm;
- the pre-existing 0.1 ppm hit floor.

Per trace, the proxy retained:
- event count;
- inter-event interval mean/std;
- event duration mean/std/max;
- peak-amplitude mean/std/max;
- integrated-event exposure mean/std/max;
- first/last event time;
- total event occupancy.

This was compared with matched marginal concentration summaries.

### Positive results

At 0.01 ppm:
- H01 180 s: marginal held-wind identity 1/2 -> point-process 2/2; wind/source ratio 0.514 -> 0.412.
- H02 180 s: both 2/2, but ratio 0.103 -> 0.031.
- H03 240 s: marginal 1/2 -> point-process 2/2; ratio 0.810 -> 0.525.

At 0.1 ppm:
- H02 180 s: point-process ratio ~0.035 vs marginal ~0.104.
- H03 240 s: point-process 2/2 vs marginal 1/2.

Thus event morphology can recover source distinctions lost by static marginals in difficult regimes.

### Critical negative results

- H01 before ~229 s has no 0.1 ppm events; the point-process representation at the nominal hit floor is empty and gives 0/2.
- therefore a single fixed “hit process” can erase subthreshold source evidence.
- direct temporal-order destruction does not uniformly eliminate point-process source identity.

Temporal-permutation screen:
- H02 180 s: shuffling strongly worsens event ratio (0.031 -> 0.308 at 0.01 ppm), supporting true temporal/event structure there.
- H03 180 s: 0.226 -> 0.521, also supporting temporal structure.
- H03 240 s: ratio changes little (~0.525 -> ~0.540); source identity remains 2/2.
- H01 can retain or even improve source separation after shuffling in some cases.

Therefore the “conditional event intensity is the source identity” mechanism is not uniformly load-bearing across Houses.

## 4. Novelty collision boundary

Older GSL/animal-plume literature already uses:
- whiff/blank durations;
- intermittency;
- encounter counts;
- first-passage/hit timing.

So the main novelty cannot be “convert gas measurements into events”.

The only defensible modern transfer would be:
> infer a marked point-process conditional intensity law in-context / zero-shot and use that law as the source-evidence object.

This remains collision-free in the current 2025/2026 direct GSL search, but it has not yet passed the internal mechanism gate.

## 5. Possible 1+2 if reopened

M1:
- in-context marked point-process inference.

M2:
- extreme-event-aware mark preservation (Nature Communications 2026 eta-learning).

M3:
- structured shift-aware source region (ICLR/ICML 2025 conformal under shift).

Risk:
M1 and M2 may become conceptually redundant because both emphasize rare intermittent events.

## 6. Verdict

Scores:
- paradigm strength: 8/10
- 2025/26 top-venue provenance: 10/10
- physical match: 10/10
- novelty room: 8/10
- lightweight feasibility: 9/10
- public-data portability: 9/10
- existing-data mechanism specificity: 6/10

**Adjusted status: RESERVE, NOT CURRENT M1.**

Reopen only if a learned/intensity-based model beats both:
1. marginal/intermittency statistics, and
2. the current predictive+eta representation,
on held transport with a time-order destructive control.
