# CPIR three-module theory and formula freeze

Date: 2026-08-31

Status: **THEORY FROZEN / RUNTIME SOURCE ALIGNED / VM BUILD PASS / BANK NOT OPENED / CLOSED LOOP NOT YET AUTHORIZED**

This document supersedes the old three-module CTT formulation for paper-level method definition. In particular, it permanently excludes the rejected `coherent-K`, exact first-passage phase, dynamic Markov transport-member state, and neural local-wind hazard routes.

The unified method is provisionally named **Causal Physical Intervention Reachability (CPIR)**. The paper-level method is decomposed into three scientific modules that occupy different positions in one causal chain:

1. **M1 — Causal Stochastic Physical Intervention (CSPI)**: generate candidate-conditioned native physical concentration responses under `do(S=s)` and marginalize the eight joint source-placement/height/transport atoms as an exchangeable nuisance ensemble.
2. **M2 — Persistent Sensor-State Transduction (PSST)**: propagate the candidate physical tape through the same persistent sensor dynamics as the real sensing chain, carrying sensor memory through motion and between stops.
3. **M3 — Stop-Resolved Reachability/Detection Composite Likelihood (SRDCL)**: preserve the identity of every completed physical stop and use its hit/non-hit event as source evidence instead of collapsing all stops to one hit count.

A separate **carrier-to-cell information projection** is required for a mathematically correct PMFS interface, but it is an interface theorem and is **not counted as a fourth scientific module**.

---

## 1. Why the previous theory must be replaced

### 1.1 Frozen negative evidence

The following objects are permanently excluded from the scientific method:

- exact first-passage phase as the main temporal signal;
- persistent coherent transport-member identity across the whole run;
- dynamic Markov evolution of the eight Monte-Carlo transport member IDs;
- a learned local-wind-to-hazard neural likelihood;
- deeper CNN/Transformer rescue of the same sparse local-wind input;
- posterior temperature, blending, Top-K rescue, reliability gates, or result-dependent thresholds;
- truth-conditioned selection of a transport member or hidden observation-world ID.

The final dynamic-transport M2 premise produced a physical persistence estimate `rho = 0.0502312254` and lost to fixed transport in `28/30` route clusters. Therefore the eight member labels are **not** a validated temporal state variable. In this theory they are only finite samples from an exchangeable nuisance distribution.

### 1.2 What the failures retained

The failure sequence leaves three positive scientific facts:

1. candidate-conditioned native physical responses contain strong source information;
2. a real gas sensor carries physical memory, whereas the transport-member label does not have validated temporal semantics;
3. the identity of the physical stop at which a detection/non-detection occurs contains information that is lost by a count-only reduction.

These three facts define M1, M2 and M3 respectively.

---

## 2. Current code/theory alignment audit

The reviewed worktree is `codex/ctt-wonline-sufficiency-audit-20260830` at base commit `a82440d2f2ed7b71fe9c7d4bd1b547d3584876c9`, with the aligned A1/A2/A3 runtime changes still uncommitted.

The current runtime file `ros2_package/src/gsl_server/algorithms/PMFS/CPIR.cpp` already implements:

- native candidate physical lookup under source hypotheses;
- eight predictive joint nuisance atoms (within-carrier source placement,
  source height, and transport seed vary together);
- `dt = 0.2 s`;
- a two-sample physical delay (`0.4 s`);
- a first-order persistent sensor state with `tau = 1.2 s`;
- threshold `theta = 0.1 ppm`;
- the first `80` samples of each completed physical stop;
- a cumulative completed-stop ledger;
- per-stop predicted hit bits for every source/member.

The historical `cpir_m1` path is **count-collapsed**. The reviewed worktree now
exposes nested runtime modes: `cpir_a1` uses memoryless raw events plus the
count score, `cpir_a2` uses the persistent sensor state plus the count score,
and `cpir_a3` uses the persistent state plus the stop-resolved score.

Therefore the historical runtime label `CPIR M1-only` is a **software label, not a clean scientific ablation label** if PSST is claimed as scientific M2. The runtime already contains the persistent sensor-state operator. Consequently:

> the reported 30-run fixed-trajectory result `5.1823 m -> 2.6808 m`, `48.27%`, `23/7`, must be called **CPIR-base fixed-trajectory shadow** until a proper nested `M1 raw -> M1+M2 -> M1+M2+M3` ablation is run.

This relabelling does not invalidate the result; it prevents double-crediting M2 as a new module after it has already been embedded in the software path.

The reviewed source now implements the paper-level M3 formula in `cpir_a3` and
the carrier-to-cell information projection using the frozen uniform
geometry-only pre-gas reference. It also checks that the cell manifest is
exactly the runtime free-cell set. An isolated VM Release build passed; actual
runtime formula parity is still untested because this review deliberately did
not open the generated bank.

---

## 3. Variables and unified causal graph

Let:

- `S` be the unknown source carrier/source hypothesis;
- `s` be one candidate source value;
- `K` be a stochastic native transport realization; `K` is exchangeable nuisance, not a temporal state;
- `X_n` be robot position at native sample `n`;
- `C_n^{s,k}` be native physical concentration predicted by GADEN for candidate `s`, member `k`, at the actual robot pose/time;
- `R_n^{s,k}` be the candidate sensor internal state;
- `M_n^obs` be the authoritative measured gas signal from the observation world;
- `I_b` be the set of native sample indices belonging to completed physical stop `b`;
- `Y_b in {0,1}` be the observed stop-level hit/non-hit event;
- `Z_{sbk} in {0,1}` be the candidate predicted stop hit for source `s`, member `k`, after the sensor model;
- `q_{sb}` be the predictive probability of a hit at stop `b` under source `s` after transport-member marginalization;
- `pi_0^C(s)` be the pre-gas carrier prior;
- `Q_t^C(s)` be the source-carrier posterior after all completed stops up to update `t`.

The unified chain is

```text
source hypothesis do(S=s)
        |
        v
M1: native stochastic transport response C^{s,k}(x,t)
        |
        v
M2: persistent sensor state R^{s,k}(t)
        |
        v
candidate stop detection Z_{sbk}
        |
        v
transport marginalization q_{sb}
        |
        v
M3: stop-resolved observed history Y_1,...,Y_B
        |
        v
carrier posterior Q^C(s)
        |
        v
information-projection carrier -> PMFS cells
        |
        v
existing PMFS planner
```

The real measured signal is never passed through the candidate sensor model a second time. Only candidate physical tapes are transformed by M2.

---

## 4. M1 — Causal Stochastic Physical Intervention

### 4.1 Scientific object

M1 answers:

> If candidate source `s` were the source, what physical concentration tape would the robot experience along its actual trajectory under legal transport uncertainty?

For each candidate and nuisance realization,

\[
C_{1:N}^{s,k}
=
F_{\mathrm{GADEN}}
\left(
 do(S=s),K=k,X_{1:N},E
\right),
\]

where `E` denotes the frozen map, boundary and simulator contract.

The candidate predictive physical distribution is approximated by the frozen ensemble

\[
p(C_{1:N}\mid do(S=s),X_{1:N},E)
\approx
\frac{1}{M}\sum_{k=1}^{M}
\delta\!\left(C_{1:N}-C_{1:N}^{s,k}\right),
\]

with `M=8` in the current contract.

### 4.2 Causal requirement

The source coordinate is treated as an intervention variable, not as a feature inferred by a black-box regression:

\[
do(S=s)\rightarrow C\rightarrow R\rightarrow Y.
\]

No source truth, source rank, PMFS posterior, localization error, planner future, or observation-world transport ID may enter the candidate simulator.

### 4.3 Nuisance policy

`K` is marginalized, never selected using truth:

\[
p(\cdot\mid do(S=s))
=
\sum_k p(K=k)\,p(\cdot\mid do(S=s),K=k).
\]

After the dynamic-transport NO-GO, the method makes **no claim** that member `k` persists as a physical hidden state across time. Member IDs are numerical nuisance samples only.

### 4.4 M1-only ablation definition

To isolate the scientific increment of M1 from M2, the formal M1-only arm uses the same native physical bank but a memoryless concentration-to-event operator:

\[
Z^{\mathrm{raw}}_{sbk}
=
\mathbf 1
\left[
\max_{n\in I_b} C_n^{s,k}>\theta
\right].
\]

All later likelihood formulas are kept unchanged. This is the only valid paper-level `M1-only` comparator if M2 is claimed separately.

### 4.5 Failure mechanism addressed

M1 specifically addresses the failure observed in RMFE, SCTT and neural wind-conditioned routes: source hypotheses cannot be ranked reliably when the source-to-observation consequence is represented by a scale-mismatched or unidentifiable surrogate. M1 replaces that shortcut with a native intervention-defined physical forward family.

---

## 5. M2 — Persistent Sensor-State Transduction

### 5.1 Why M2 is temporal but not a transport-state model

The rejected routes tried to attach temporal state to transport-member identity `K_t`. The evidence does not support that object.

The sensor state `R_t`, in contrast, is a real physical state with a deterministic transition law, is carried by the robot, and depends on recent concentration history. Two trajectories can have the same current concentration but different measured responses because their prehistory differs.

Therefore the scientifically valid temporal state is

\[
R_n,
\]

not

\[
K_n.
\]

### 5.2 Exact frozen sensor equations

The current CPIR implementation has

\[
\Delta t = 0.2\,\mathrm{s},\qquad
\tau = 1.2\,\mathrm{s},\qquad
\alpha=\exp(-\Delta t/\tau)
=0.846481724890614.
\]

The code carries two delayed physical samples. With zero-indexed notation and zero initial delay state, the candidate target entering the first-order sensor at sample `n` is the physical concentration two native samples earlier:

\[
D_n=C_{n-2}^{s,k}.
\]

The persistent candidate sensor state is

\[
R_n^{s,k}
=
\alpha R_{n-1}^{s,k}
+
(1-\alpha)D_n.
\]

Equivalently,

\[
R_n^{s,k}
=
\alpha R_{n-1}^{s,k}
+
(1-\alpha)C_{n-2}^{s,k},
\]

with the first two delayed inputs initialized to zero. The resulting dead-time component is `2 * 0.2 = 0.4 s`.

Crucially, `R_n` is **not reset at a waypoint, source update, or physical stop**. It is propagated over all trajectory samples, including motion between stops.

### 5.3 Stop event after stateful transduction

For threshold

\[
\theta=0.1\,\mathrm{ppm},
\]

and a completed stop interval `I_b` consisting of the first `80` valid stop samples (`16 s`), the predicted stop event is

\[
Z_{sbk}
=
\mathbf 1
\left[
\max_{n\in I_b}R_n^{s,k}>\theta
\right].
\]

The real observed event uses the authoritative measured tape directly:

\[
Y_b
=
\mathbf 1
\left[
\max_{n\in I_b}M_n^{obs}>\theta
\right].
\]

The observation tape is not filtered again.

### 5.4 Why the state is mathematically load-bearing

Suppose two candidate histories have identical current concentration `C_n` but different `C_{n-2}` or different previous state `R_{n-1}`. Then

\[
R_n^{(1)}-R_n^{(2)}
=
\alpha\left(R_{n-1}^{(1)}-R_{n-1}^{(2)}\right)
+
(1-\alpha)\left(C_{n-2}^{(1)}-C_{n-2}^{(2)}\right),
\]

which is generally non-zero. Therefore a memoryless mapping from only the current concentration to detection is not sufficient when `alpha>0` or the delay is non-zero.

### 5.5 Development evidence and boundary

A H01 development-only strict leave-one-predictive-member-out ablation over five frozen routes produced:

- normalized true-source rank: `0.1498425 -> 0.1325125`, relative reduction `11.57%`, `39/1/0`;
- posterior-mean localization error: `2.72847 m -> 2.53935 m`, relative reduction `6.93%`, `39/1/0`;
- all five routes improved in mean error.

This is **development evidence only** because the uploaded archive does not contain the original reserved observation members. It does not authorize a paper-level M2 PASS until disjoint reserved/fresh observation worlds reproduce the increment.

### 5.6 Collision boundary

The novelty claim is **not** “first use of gas-sensor dynamics”. Sensor response/recovery dynamics already exist in GSL literature.

The intended secondary innovation is narrower:

> the candidate-interventional physical tape and its persistent sensor state are propagated as one causal hypothesis-conditioned observation operator, with state carried through robot motion and reused consistently by the source likelihood.

---

## 6. M3 — Stop-Resolved Reachability/Detection Composite Likelihood

### 6.1 Failure mechanism addressed

Fresh cross-airflow experiments rejected exact first-passage phase as a robust source signal. Dynamic transport-member identity was also rejected. However, reachability/detection remained strongly source-informative.

The historical `cpir_m1` and explicit A1/A2 comparators introduce another
information bottleneck: after computing a predictive detection probability for
every stop, they average those probabilities and use only the **number** of hit
stops. The final A3 path removes this bottleneck by preserving stop identity.

M3 removes exactly that compression and nothing else.

### 6.2 Per-stop predictive probability

Let

\[
h_{sb}=\sum_{k=1}^{M} Z_{sbk}
\]

be the number of predictive transport members that produce a hit for source `s` at stop `b`.

Use a fixed Jeffreys prior

\[
\vartheta_{sb}\sim \operatorname{Beta}(1/2,1/2)
\]

for the unknown member-level hit probability. After observing `h_{sb}` hits in `M` predictive members, the posterior predictive probability of a detection is

\[
q_{sb}
=
\mathbb E[\vartheta_{sb}\mid h_{sb}]
=
\frac{h_{sb}+1/2}{M+1}.
\]

For the current runtime `M=8`,

\[
q_{sb}=\frac{h_{sb}+0.5}{9},
\]

which is exactly the smoothing already computed in `CPIR.cpp` before it collapses stop identity.

For strict leave-one-member-out development with seven predictive members, the denominator becomes `8`, again with no tuned parameter.

### 6.3 Current count-collapsed score

The current runtime forms

\[
\bar q_s
=
\frac{1}{B}\sum_{b=1}^{B}q_{sb},
\]

and

\[
H_+=\sum_{b=1}^{B}Y_b.
\]

It then uses

\[
\ell_{\mathrm{count}}(s)
=
H_+\log \bar q_s
+
(B-H_+)\log(1-\bar q_s).
\]

This score knows only how many completed stops were hits.

### 6.4 M3 stop-resolved composite score

M3 keeps the exact same observed events and exact same `q_{sb}`, but preserves stop identity:

\[
\ell_{\mathrm{M3}}(s)
=
\sum_{b=1}^{B}
\left[
Y_b\log q_{sb}
+
(1-Y_b)\log(1-q_{sb})
\right].
\]

The carrier posterior is

\[
Q_t^C(s)
\propto
\pi_0^C(s)
\exp\big(\ell_{\mathrm{M3},t}(s)\big).
\]

At each source update, only newly completed physical stops may be appended to the ledger; recomputing the cumulative score from the ledger and incrementally adding only new stops must be numerically identical.

### 6.5 Why this is called a composite likelihood

The project has explicitly rejected the claim that the eight transport members form a validated persistent or Markov hidden state. Therefore M3 does **not** invent a false joint transport model across stops.

Each factor

\[
q_{sb}^{Y_b}(1-q_{sb})^{1-Y_b}
\]

is a valid stop-level marginal predictive event model. Their product is used as a **stop-resolved composite likelihood / generalized-Bayes score**. It is not claimed to be the exact joint probability of the whole turbulent trajectory.

This distinction is essential: the method preserves spatial stop identity without resurrecting a rejected temporal transport state.

### 6.6 Information-loss proposition

If every stop has the same source-conditioned event probability,

\[
q_{s1}=q_{s2}=\cdots=q_{sB}=q_s,
\]

then the full Bernoulli likelihood depends on the data only through

\[
H_+=\sum_bY_b,
\]

so the hit count is sufficient.

When `q_{sb}` varies with stop identity, the likelihood ratio between two sources depends on the specific detection pattern:

\[
\log\frac{L(s_i)}{L(s_j)}
=
\sum_bY_b\log\frac{q_{i b}}{q_{j b}}
+
\sum_b(1-Y_b)\log\frac{1-q_{i b}}{1-q_{j b}}.
\]

In general this cannot be reduced to a function of `H_+` alone. Therefore count collapse is information-preserving only under a restrictive equal-probability condition that does not hold in obstacle-dependent mobile sensing.

### 6.7 Non-detection as censored evidence

Let `T_b` be the latent first threshold-crossing time within stop `b`. A no-hit stop means

\[
T_b > |I_b|\Delta t = 16\,\mathrm{s}.
\]

Thus a non-detection is not “no information”; it is a fixed-window right-censored event. M3 uses the robust binary consequence of that censoring but deliberately does **not** use exact first-passage phase, which has already failed cross-airflow validation.

### 6.8 H01 development evidence

Using the same H01 predictive8 archive, five frozen routes, stateful sensor forward model, and strict leave-one-member-out evaluation:

- stop-resolved rank: `0.1325125`;
- count-collapsed rank: `0.2101427`;
- stop-resolved vs count-collapsed: `40/0/0` development units;
- stop-resolved posterior-mean error: `2.53935 m`;
- count-collapsed posterior-mean error: `3.25873 m`;
- stop-resolved vs count-collapsed error: `40/0/0`;
- reversing the stop-response identity degrades rank to `0.39910` and error to `3.57139 m`.

All five routes improve in mean error under stop-resolved scoring.

This is strong **development** evidence that physical stop identity is load-bearing. It is not fresh confirmation because the same predictive8 family is used in leave-one-member-out form.

### 6.9 Collision boundary

The novelty claim is **not** “first use of detection/non-detection”. Detection and non-detection likelihoods already exist in GSL.

The intended secondary innovation is the specific factorization:

\[
do(S=s)
\rightarrow
\text{native stochastic response}
\rightarrow
\text{persistent sensor state}
\rightarrow
\text{stop-specific predictive hit probability}
\rightarrow
\text{repeated stop-resolved composite evidence}.
\]

The paper must perform equation-level collision audit against existing GSL likelihoods before claiming novelty.

---

## 7. The complete three-module inference

For every candidate source `s`, member `k`, and completed stop `b`:

### M1

\[
C_{1:N}^{s,k}
=
F_{\mathrm{GADEN}}(do(S=s),K=k,X_{1:N},E).
\]

### M2

\[
R_n^{s,k}
=
\alpha R_{n-1}^{s,k}
+
(1-\alpha)C_{n-2}^{s,k},
\]

\[
Z_{sbk}
=
\mathbf 1\!\left[\max_{n\in I_b}R_n^{s,k}>\theta\right].
\]

### Transport nuisance marginalization

\[
q_{sb}
=
\frac{\frac12+\sum_{k=1}^{M}Z_{sbk}}{M+1}.
\]

### M3

\[
\ell_b(s)
=
Y_b\log q_{sb}
+(1-Y_b)\log(1-q_{sb}),
\]

\[
L_t(s)=\sum_{b\in\mathcal B_t}\ell_b(s),
\]

\[
Q_t^C(s)
=
\frac{\pi_0^C(s)\exp L_t(s)}
{\sum_j\pi_0^C(j)\exp L_t(j)}.
\]

The three modules are therefore not a loose collection. They form one generative-to-inverse chain:

\[
\boxed{
 do(S)
 \xrightarrow{M1}
 C
 \xrightarrow{M2}
 R,Z
 \xrightarrow{\text{marginalize }K}
 q
 \xrightarrow{M3}
 Q^C(S)
}
\]

---

## 8. Carrier-to-cell PMFS interface: information-projection theorem

This is necessary for correctness but is not counted as a scientific module.

Let `C_i` be the set of free PMFS cells inside carrier `i`. Let `p_ref(c)` be a pre-gas reference cell distribution that has **not already consumed the same gas observations**. Define the within-carrier conditional reference

\[
\rho(c\mid i)
=
\frac{p_{ref}(c)}{\sum_{u\in C_i}p_{ref}(u)}.
\]

The desired cell posterior must satisfy the carrier marginal constraints

\[
\sum_{c\in C_i}Q_t^{cell}(c)=Q_t^C(i).
\]

The unique distribution minimizing

\[
D_{KL}(Q^{cell}\Vert p_{ref})
\]

subject to those carrier constraints is

\[
Q_t^{cell}(c)
=
Q_t^C(i(c))\,\rho(c\mid i(c)).
\]

This follows from a Lagrange multiplier for each carrier. It preserves the new causal carrier mass while retaining only the pre-gas within-carrier geometry/conditional structure.

A uniform carrier fill is the special case where `p_ref` is uniform inside each carrier. Copying the same unnormalized carrier score to each cell before global normalization is **not generally equivalent** when carriers have different numbers of free cells.

The interface must therefore pass:

- exact carrier mass conservation;
- within-carrier odds preservation;
- row/tie-order invariance;
- identity reconstruction when new carrier marginals equal reference carrier marginals;
- no use of a PMFS posterior that has already consumed the same gas observation.

---

## 9. Single-consumption and online update contract

For ON mode:

1. PMFS mapping, motion state machine, navigation and planner remain authoritative unless separately preregistered.
2. Real measured gas is read once.
3. The native PMFS source gas-likelihood write is disabled for observations consumed by CPIR.
4. CPIR maintains a monotone raw-sample ledger and completed-stop ledger.
5. M2 candidate states are advanced over every newly observed trajectory sample exactly once.
6. M3 appends each completed physical stop exactly once.
7. Carrier posterior is lifted to cells through Section 8 exactly once.
8. The planner consumes the resulting posterior; no posterior blend, temperature or rescue gate is permitted.

Batch/recursive parity requirement:

\[
L_t^{batch}(s)
=
\sum_{b\le B_t}\ell_b(s)
=
L_{t-1}^{online}(s)
+
\sum_{b\in\Delta_t}\ell_b(s)
\]

must hold numerically at every source update.

---

## 10. Formal nested ablation contract

A paper-level three-module claim requires the following nested arms with **all other factors frozen**.

### A0 — authoritative PMFS

Original `main_v8` source inference and planner.

### A1 — M1 only

- native `do(S=s)` physical bank;
- memoryless raw concentration threshold per stop;
- count-collapsed likelihood.

This isolates the causal native physical intervention increment.

### A2 — M1 + M2

- same physical bank;
- persistent sensor-state transduction;
- same count-collapsed likelihood.

Therefore

\[
\Delta M2=A2-A1
\]

contains only the persistent sensor-state increment.

### A3 — M1 + M2 + M3

- same physical bank;
- same persistent sensor state;
- stop-resolved likelihood instead of count collapse.

Therefore

\[
\Delta M3=A3-A2
\]

contains only the stop-identity/history increment.

### Destructive controls

At minimum:

- `M2_RESET_AT_STOP`: reset sensor state at every physical stop;
- `M2_MEMORYLESS_RAW`: remove sensor memory while keeping all events/thresholds fixed;
- `M3_COUNT_ONLY`: current pooled-count score;
- `M3_REVERSE_STOP`: reverse or deterministically permute stop-response identity while preserving hit counts;
- source-label destruction;
- predictive-member / observation-member disjointness audit.

No arm may change the source candidate set, number of predictive members, threshold, stop length, route, observation tape or evaluator.

---

## 11. Evidence status after theory freeze

| Object | Current status | What is established | What remains |
|---|---|---|---|
| native candidate physical bank / M1 mechanism | strong positive | source-conditioned physical family contains source information; CPIR-base shadow is large | clean M1-only nested ablation and true closed loop |
| M2 persistent sensor state | H01 development positive | 39/40 development units improve; rank and error improve | disjoint reserved/fresh H01, then H02/H03 |
| M3 stop-resolved likelihood | H01 development positive | 40/40 vs count collapse and 40/40 vs reverse-stop in development | disjoint reserved/fresh H01, then H02/H03 |
| three-module full method | not yet validated | unified theory is now specified | proper nested cross-House shadow, then paired closed loop |
| dynamic transport M2 | terminal NO-GO | member identity is not a validated Markov state | never restore |
| neural local-wind hazard | terminal NO-GO | current local-wind input/solver does not generalize | never use as main module |

---

## 12. Current CPIR-base shadow: correct interpretation

The frozen fixed-trajectory shadow currently reported as “M1-only” has:

- 30-pair PMFS mean error `5.1823 m`;
- CPIR-base mean error `2.6808 m`;
- pooled mean improvement `48.27%`;
- `23/7/0` wins/losses/ties;
- one-sided exact sign-test `p = 0.00261`;
- H01 `45.46%`, `8/2`;
- H02 `9.82%`, `5/5`;
- H03 `67.11%`, `10/0`.

Because the runtime already propagates the persistent sensor state, this result must not be used to claim a pure M1 increment after M2 is separated scientifically. It remains valuable as evidence that the **current CPIR base pipeline** is promising on fixed trajectories.

The next offline report must replace this ambiguous label with the explicit nested arms A1/A2/A3.

---

## 13. Theory lineage and collision boundaries

The purpose of cross-domain references is to motivate scientific principles, not to claim those principles are new by themselves.

### M1 remote-field principle

High-fidelity simulation-based forward inference in modern astrophysics/cosmology demonstrates the value of inferring hidden causes through a realistic simulator rather than relying only on simplified summary likelihoods. A representative example is the SimBIG framework in *Nature Astronomy* (2024), DOI `10.1038/s41550-024-02344-2`.

**Transfer:** hypothesis-conditioned high-fidelity forward response under nuisance uncertainty.

**Not transferred:** cosmology architecture, deep generative network, or its target parameters.

**GSL collision boundary:** physical dispersion/source likelihoods already exist in GSL; novelty must be claimed only at the intervention-defined stochastic native-response replacement and its audited nuisance/single-consumption contract.

### M2 remote-field principle

Biophysical sensory adaptation in the retina shows that dynamic stimulus-to-observation transduction must carry an internal sensory state; a memoryless observation mapping can fail under changing inputs. Representative: Idrees et al., *Nature Communications* 2024, DOI `10.1038/s41467-024-50114-5`.

**Transfer:** a physical internal sensor state is part of the observation operator.

**Not transferred:** retinal equations, neural-network architecture or learned parameters.

**GSL collision boundary:** gas sensor response/recovery is known, including ICRA 2024 “Sense in Motion with Belief Clustering”. The claim must therefore be about persistent candidate-interventional state propagation inside the source likelihood, not “first sensor dynamics”.

### M3 remote-field principle

Repeated-visit ecological occupancy/detection models distinguish latent state from imperfect repeated observations and treat location/visit identity as part of the likelihood rather than collapsing observations to one count. Representative example: *Nature Ecology & Evolution* 2025, DOI `10.1038/s41559-025-02688-6`.

**Transfer:** repeated location-specific detection/non-detection factors retain information that aggregate counts may discard.

**Not transferred:** ecological occupancy covariates or species model.

**GSL collision boundary:** detection/non-detection likelihoods already exist in GSL; the claim must be narrowed to stop-resolved event probabilities generated by M1+M2 and used as an audited composite source likelihood without exact first-passage or invalid transport-state semantics.

General GSL collision reference: Francis, “Gas source localization and mapping with mobile robots: A review”, *Journal of Field Robotics* 2022, DOI `10.1002/rob.22109`.

---

## 14. Falsification gates before closed loop

### M1 gate

Cross-House fixed-trajectory A1 must beat PMFS on pooled localization error and must not rely on hidden observation-world member identity.

### M2 gate

On disjoint observation worlds:

- A2 must improve over A1 in both source ordering and official localization error;
- state reset must destroy or significantly reduce the gain;
- all three Houses must be checked; no result-dependent sensor parameter fitting.

### M3 gate

On disjoint observation worlds:

- A3 must improve over A2;
- full stop-resolved score must beat `COUNT_ONLY`;
- stop permutation/reversal must reduce the advantage;
- source-label destruction must eliminate true-source ordering;
- no exact first-passage phase may enter the primary score.

### Full-method gate

Only after A1/A2/A3 cross-House offline evidence is frozen may paired 300 s closed loop run:

```text
H01/H02/H03 x seeds1,2,3
PMFS OFF vs FULL A3 ON
```

Primary target remains pooled final localization-error improvement `>=10%`, with pairwise wins/losses, per-House means and catastrophic regressions reported.

---

## 15. Implementation tasks implied by this theory freeze

No scientific formula may be changed while implementing these tasks unless a new preregistration explicitly supersedes this document.

1. Rename paper-level reporting of the current `CPIR M1-only` path to `CPIR-base / M1+fixed-sensor/count-only` until nested ablation exists.
2. Add a true A1 memoryless-raw arm without altering source candidates, threshold, members or measurement tape.
3. Preserve the current stateful candidate sensor path as A2.
4. Implement A3 by replacing only `ell_count(s)` with `ell_M3(s)`; reuse the already-computed per-stop `q_sb` values.
5. Implement the carrier-to-cell information projection from Section 8; do not count it as M4.
6. Add recursive-vs-batch score parity tests.
7. Add `RESET_AT_STOP`, `COUNT_ONLY`, `REVERSE_STOP`, source-label and member-disjointness controls.
8. Run fixed-trajectory nested ablation before any new closed-loop claim.
9. Keep all rejected transport-state and neural routes unreachable in the full A3 configuration.

---

## 16. Final frozen method statement

The proposed three-module method is:

> **CPIR performs source intervention through a stochastic native physical response family (M1), transforms each candidate response through a carried physical sensor state (M2), and accumulates the resulting repeated stop-specific detection/non-detection evidence without collapsing stop identity (M3). Transport members are marginalized as nuisance samples and are not assigned unsupported temporal state semantics.**

In equations,

\[
\boxed{
 do(S=s)
 \xrightarrow{\mathrm{M1}}
 C^{s,k}_{1:N}
 \xrightarrow{\mathrm{M2}}
 R^{s,k}_{1:N},Z_{sbk}
 \xrightarrow{\sum_k}
 q_{sb}
 \xrightarrow{\mathrm{M3}}
 Q^C(S\mid Y_{1:B})
}
\]

This is the formula set to which future code, ablations and paper text must align.
