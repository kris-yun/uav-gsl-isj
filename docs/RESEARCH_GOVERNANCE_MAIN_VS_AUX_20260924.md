# Research Governance — Mainline vs Auxiliary Pro

Date: 2026-09-24

Project:
UAV gas source localization with GADEN -> offline falsification -> PMFS closed loop -> later real flight.

## 1. Role ownership

### Mainline lead: primary ChatGPT thread

The primary thread owns all scientific decisions.

Only the primary thread may:

1. define / revise the scientific problem;
2. define the benchmark and evaluation ruler;
3. freeze experimental contracts;
4. set PASS / HOLD / STOP / NO-GO thresholds;
5. decide whether a route is promoted, held, or killed;
6. decide which mother theory becomes the next mainline;
7. authorize new simulations;
8. authorize cross-house / cross-wind tests;
9. authorize PMFS closed-loop experiments;
10. integrate literature, theory, data and reproducibility evidence into the final paper architecture.

The primary thread must independently recompute all decisive experimental results before promotion.

### Auxiliary role: second Pro account

The second Pro is an **auxiliary theory/literature expert**.

It may:

1. deeply search 2025/2026 literature;
2. map prior art and novelty boundaries;
3. derive candidate mathematical formulations;
4. compare alternative formulations of the same frozen scientific object;
5. identify mathematical weaknesses and hidden assumptions;
6. propose possible second-order innovations;
7. propose falsification tests on paper;
8. inspect whether a proposed innovation is genuinely different from failed routes;
9. prepare paper-safe theoretical language and derivations.

It may NOT:

1. change the active R0 benchmark;
2. change R0 thresholds;
3. decide R0 PASS/HOLD/STOP;
4. declare a main innovation established;
5. create a competing scientific mainline before primary-thread authorization;
6. launch new GADEN/PMFS experiments without authorization;
7. rescue a failed frozen gate;
8. promote a literature idea directly to “the main innovation”;
9. overwrite active execution branches.

---

## 2. Current mainline state

PASI is frozen:

`PASI_D0_FAIL_STOP_PATH_ACTION_MAINLINE`

The active work is:

`R0 stochastic benchmark refoundation`

R0 asks:

> Which source-conditioned stochastic plume statistics are reproducibly estimable from finite independent realizations under the current 10×30 observation operator?

R0 is already frozen and being executed.

The auxiliary Pro should not redesign R0 now.

---

## 3. What the auxiliary Pro should do before R0 returns

The primary thread owns the ruler.

The auxiliary Pro should use the waiting time to build a **conditional theory library**, not choose a winner.

### Track A — finite-realization stochastic identifiability

Deeply review current work on:

- finite-sample stochastic-process inference;
- trajectory identifiability;
- sample complexity of variance/covariance/path statistics;
- sparse trajectory inference;
- model indistinguishability;
- uncertainty of source-/state-conditioned stochastic descriptors.

Deliver:
- what can realistically stabilize with K=16;
- what likely requires much larger K;
- which statistics have known finite-sample guarantees or robust estimators.

### Track B — turbulent plume statistical objects

Deeply review:

- concentration intermittency;
- encounter statistics;
- zero/nonzero / blank duration statistics;
- first-passage / first-arrival statistics;
- burst duration and inter-encounter intervals;
- heavy-tailed concentration distributions;
- spatial/temporal correlation;
- plume meandering vs relative dispersion;
- robust descriptors across independent realizations.

Deliver:
a map from each physical stochastic object to:
- theoretical origin;
- recent 2025/2026 evidence;
- likely sample complexity;
- whether it can carry source identity;
- whether it has already been used in GSL/olfaction.

### Track C — conditional mother-theory derivations

Do not select a main theory yet.

Prepare mathematically serious derivations for three possible R0 outcomes:

#### If R0 shows full path distributions are stable
Explore:
- path-space likelihood;
- stochastic action / large deviations;
- source-conditioned path geometry;
- distributional distance / likelihood-ratio formulations.

#### If R0 shows only encounter/intermittency statistics are stable
Explore:
- point-process / renewal-process representations;
- event-based source inference;
- survival / first-passage theory;
- stochastic geometry of odor encounters.

#### If R0 shows only basin-scale spatial quantities are stable
Explore:
- coarse source-basin probability;
- multiscale localization;
- information geometry / coarse-grained state representations;
- theories that explicitly distinguish identifiable macrostate from unidentifiable microstate.

For each conditional direction, derive:
1. mother theory;
2. the exact new mathematical object;
3. GSL-specific second-order adaptation;
4. how it maps to a PMFS probability map;
5. what data would immediately falsify it;
6. novelty boundary against existing GSL/olfaction.

---

## 4. What the auxiliary Pro may derive now

The second Pro is encouraged to derive **candidate second-order innovations** in advance, but only conditionally.

A valid derivation must be written as:

> IF R0 establishes X as reproducible, THEN candidate innovation Y is mathematically justified because ...

Not:

> We should now switch to Y.

Each derivation must identify which empirical premise it depends on.

No premise may be assumed before R0.

---

## 5. Output format required from auxiliary Pro

The auxiliary Pro should return at most three compact deliverables:

### A. Literature evidence matrix

Columns:
- stochastic object;
- far-domain theory;
- 2025/2026 anchor papers;
- code availability;
- finite-sample requirements;
- prior use in GSL/olfaction;
- novelty risk.

### B. Conditional derivation notebook / memo

One section for each R0 outcome:
- full path stable;
- encounter statistics stable;
- only coarse basin stable / path unstable.

Each section includes equations and a possible second-order innovation, but clearly marked **conditional**.

### C. Red-team memo

For every candidate derivation:
- strongest reason it may fail;
- nearest prior art;
- minimum offline falsification;
- STOP condition.

No long brainstorm list.

---

## 6. Handoff after R0

When R0 completes:

1. primary thread independently recomputes R0;
2. primary thread assigns PASS/HOLD/STOP;
3. primary thread identifies the empirically stable stochastic object;
4. primary thread sends one narrow object to auxiliary Pro;
5. auxiliary Pro deepens literature and second-order derivation only for that object;
6. primary thread chooses whether to promote it into the next experimental mainline.

This preserves one scientific authority and prevents parallel drift.

---

## 7. Rule of evidence

Literature can motivate a theory.

Only frozen independent data can promote it.

The auxiliary Pro is therefore a **theory multiplier**, not an experiment governor.
