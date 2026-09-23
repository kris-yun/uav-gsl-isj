# CODEX CHARTER — SAFE-B0 Anytime-Valid PMFS Source Evidence Replay

Date: 2026-09-23  
Target branch: \`research/anytime-valid-source-eprocess-v1\`  
Priority: main-candidate falsification, not production integration.

## 0. Purpose

Test whether candidate-wise e-process evidence has **usable power** on already frozen PMFS data before modifying PMFS movement or closed-loop behavior.

Do not optimize endpoint error.  
Do not tune anything using source truth.  
Do not alter old R1 evidence.

The first question is simply:

> Given the same raw PMFS HIT/MISS stream and the same candidate forward hit maps, can an anytime-valid candidate confidence set contract while retaining the truth-containing candidate?

If no, M2 is not ready to be a main innovation.

---

## 1. Frozen evidence source

Use the corrected R1 archive from the completed Native baseline-recovery worktree/branch:

\`research/native-pmfs-baseline-recovery-v1\`

Repository path:

\`evidence/native_pmfs_baseline_recovery_v1/R1_R2_source_corrected_House01_seed0_20260923/R1_R2_SOURCE_CORRECTED_House01_S0_20260923_FULL_RAW.tar.gz\`

Reported archive SHA256:

\`447e7c25f71fd8a3010642b32aca29208d817a7a2ac05008be52404e29a8805c\`

If using the user's local worktrees, first locate the existing archive rather than downloading or regenerating it.

Do not copy the truth-evaluation JSON or runtime manifest into the source-blind working directory until all SAFE-B0 trajectories are frozen.

---

## 2. Stage B0-SCHEMA — inspect, do not assume

Extract the archive into a fresh read-only input directory.

Locate and hash at minimum:

- \`measurement_events.csv\`;
- candidate geometry CSV;
- measured-map snapshot;
- candidate hit maps for the corrected **B** and **C** arms if present;
- map/grid metadata needed to map measurement coordinates to candidate hit-map cells;
- any event/stop IDs.

Generate:

\`evidence/anytime_valid_source_eprocess_v1/SAFE_B0_INPUT_SCHEMA_20260923.md\`

and machine-readable JSON.

The report must state:

- exact event columns;
- number of raw events;
- unique robot stops/positions;
- HIT count and MISS count;
- threshold semantics used to construct HIT/MISS;
- whether several events occur at the same stop;
- map dimensions and cell ordering;
- number of candidate maps;
- whether map values are in [0,1];
- exact method used to extract each candidate prediction \(h_s(x_t)\).

No source coordinate may be read in this stage.

Fail closed on ambiguous indexing.

---

## 3. Stage B0-PRED — freeze the predictive matrix

Construct, separately for each chosen forward arm, the matrix

\[
H_{t,s}=h_s(x_t)
\]

for every frozen measurement event \(t\) and candidate \(s\).

Primary first arm:

- **C:** official humble source + ground-truth wind + official parameters.

Diagnostic second arm:

- **B:** frozen R2 source + ground-truth wind + R2 parameters.

Do not use A/GMRF as the primary safe-inference arm.

Write:

- \`SAFE_B0_C_PREDICTIONS.csv.zst\` or equivalent compact artifact;
- \`SAFE_B0_B_PREDICTIONS.csv.zst\`;
- hashes;
- min/median/max prediction;
- fraction exactly 0/1;
- pairwise candidate-prediction separation summaries at observed positions.

Freeze these before any truth evaluation.

---

## 4. Stage B0-POINT — point-null e-process, no robust rescue yet

For each candidate \(s\), define the point null

\[
I_{s,t}=\{H_{t,s}\}.
\]

Use \(\epsilon_p=10^{-6}\) only as a numerical probability clip, fixed before truth reveal.

### 4.1 Alternative q — fixed, source-blind, predictable

For the first run use the **uniform other-candidate mixture**:

\[
q_{s,t}
=
\frac{1}{|S|-1}
\sum_{r\ne s} H_{t,r}.
\]

This uses no truth and no future observation.

Do not use the final PMFS source scores as weights, because those scores were computed from the full observation snapshot and would leak future observations into early e-factors.

A second, clearly labeled adaptive arm may use only past e-process values/survivor status, but only after the fixed-mixture arm is frozen.

### 4.2 e-factor

For observed HIT/MISS \(Y_t\):

\[
e_{s,t}
=
\frac{
q_{s,t}^{Y_t}(1-q_{s,t})^{1-Y_t}
}{
H_{t,s}^{Y_t}(1-H_{t,s})^{1-Y_t}
}.
\]

Accumulate in log space:

\[
\log E_t(s)=\sum_{\tau\le t}\log e_{s,\tau}.
\]

Use candidate rejection threshold:

\[
E_t(s)\ge1/\alpha,
\qquad \alpha=0.05.
\]

Important:
**do not divide alpha by the number of candidates** for single-source confidence-set coverage.

### 4.3 Outputs before truth reveal

For every event:

- survivor count;
- rejected candidate IDs;
- max/median/min log E;
- candidate-set IDs;
- event coordinate / stop ID;
- q and h summaries.

Also report:
- first time survivor count <= 20, <= 10, <= 5, 1;
- whether no such time occurs;
- fraction of candidate-event pairs with near-zero expected evidence separation.

Freeze output hashes.

---

## 5. Stage B0-THIN — dependence sensitivity

PMFS can take repeated measurements at one stop. A point-null Bernoulli e-process is only justified if \(H_{t,s}\) describes the relevant **conditional** hit probability.

Therefore run predeclared event-stream variants:

A. all raw events;  
B. first event per robot stop;  
C. last event per robot stop;  
D. one deterministic event per stop (middle index if available).

Do NOT pick whichever gives the best truth behavior.

Compare:
- survivor contraction;
- e-process volatility;
- candidate rejection overlap.

If all-event results are dramatically stronger than one-per-stop variants, flag likely dependence/pseudoreplication risk.

No claim of statistical validity may rely on independence that PMFS does not model.

---

## 6. Stage B0-COMPOSITE-DIAGNOSTIC — only after point-null freeze

The point-null simulator is likely misspecified. Test composite nulls only as **predeclared diagnostics**, not as truth-tuned calibration.

### Composite C1 — fixed absolute envelope panel

Run a sensitivity panel:

\[
I_{s,t}=
[\max(0,h_{s,t}-\delta),\min(1,h_{s,t}+\delta)]
\]

for

\[
\delta\in\{0.025,0.05,0.10,0.20\}.
\]

This panel is diagnostic. Do not select a winning delta after truth reveal.

### Composite C2 — B/C cross-contract envelope

Where B and C predictions are aligned on the same candidate/event geometry, define

\[
I_{s,t}
=
[
\min(h^B_{s,t},h^C_{s,t}),
\max(h^B_{s,t},h^C_{s,t})
].
\]

Label this **FORWARD-CONTRACT STRESS ENVELOPE**, not a calibrated confidence interval and not a guarantee of real-world coverage.

Its purpose is to answer:
- how quickly does e-process power collapse when the null is widened to include a major forward-contract variation?

Do not use A/GMRF in this envelope.

---

## 7. Truth reveal — only after all trajectories freeze

After:
- schema,
- predictive matrices,
- point-null runs,
- thinning variants,
- composite panel

are all hashed and frozen, read the truth-containing candidate ID from the recovery evidence.

Report for every predeclared arm:

- whether truth candidate was ever rejected;
- first truth-rejection event if any;
- truth candidate max log E;
- final survivor count;
- whether a unique survivor was reached;
- survivor-set inclusion of truth at every event;
- Native PMFS official truth-source rank for context only.

Hard interpretation:

### Positive signal
Point-null or a source-blind composite arm:
- keeps truth candidate through the stream;
- removes a meaningful number of false candidates;
- result is not entirely dependent on using all repeated within-stop events.

### Negative signal
- truth is rejected early;
- or honest/wide intervals cause almost zero contraction;
- or apparent power vanishes under one-event-per-stop thinning.

No endpoint/centroid rescue.

---

## 8. SAFE-B0 does NOT establish the final guarantee

Even if truth survives one replay, do not claim coverage.

A true anytime-valid source-confidence guarantee requires:
- the candidate null to contain the **conditional** HIT probability process when that source is correct;
- validation across independent plume realizations;
- a defensible source-blind construction of composite intervals.

SAFE-B0 is a power/interface falsification only.

---

## 9. Stage B0-HITBEARING — mandatory follow-up if House01 is all/mostly miss

If House01's frozen 20-event stream is all-miss or extremely hit-sparse, do not promote or kill M2 based on it alone.

Use the existing recovered Native runner to create a **House02 seed0 hit-bearing frozen snapshot** under the same baseline-integrity contract.

Requirements:
- no method changes;
- source-blind snapshot trigger declared before truth;
- export raw events and all official candidate hit maps;
- freeze before truth;
- repeat SAFE-B0 exactly.

If House02 seed0 is also unsuitable, choose the next predeclared hit-bearing case by event statistics only, never truth rank.

---

## 10. Required commits

Commit after:

1. schema inspection;
2. predictive-matrix freeze;
3. point-null + thinning evidence;
4. composite diagnostic;
5. truth evaluation;
6. hit-bearing follow-up if required.

Suggested prefixes:
- \`safe-audit:\`
- \`safe-evidence:\`

---

## 11. Final decision file

Create:

\`evidence/anytime_valid_source_eprocess_v1/SAFE_B0_DECISION_20260923.md\`

Answer exactly:

1. Was the raw PMFS HIT/MISS stream reconstructible without ambiguity?
2. Did the point-null e-process contract the candidate set?
3. Did it keep the truth candidate?
4. How sensitive was contraction to one-event-per-stop thinning?
5. How quickly did power collapse as the composite null widened?
6. Did the B/C contract envelope still allow useful evidence growth?
7. Is a hit-bearing independent case required/completed?
8. Is M2 worth advancing to SAFE-B1?

Do not modify PMFS movement in this task.
