# OCB-R2 R3B/R3C — Prospective Multi-Source Generation and Frozen Scoring Contract

Date: 2026-09-30

Status: **PREREGISTERED BEFORE ANY R3 PLUME GENERATION**

Parent R3A design commit:

`9cfd0fbca70fc214c42ee7d733bf85716096b220`

Frozen source panel SHA256:

`11952617610c4b50d789ac73a5a05e8302a0f570f55eca504598872844e9017e`

Frozen 64-run runlist SHA256:

`15f2121eae2772989c7cff7f292825a31efe94c24efedc34f2a9ccd681f947d0`

Frozen generator SHA256:

`ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688`

## 0. Scientific boundary

R3 is a prospective discovery extension.

It tests whether the already-frozen broad-memory path evidence generalizes from
the repaired two-source discovery benchmark to new source locations in a
four-candidate source panel.

It does **not** yet establish a formal Partial Information Decomposition or
Partial Information Rate Decomposition synergy term.

The current mother-theory language remains a working hypothesis:

> dynamic synergistic / joint-path source information

The operational object remains the frozen candidate-wise path dependence term.

No confirmation, House03, neural model, diffusion/flow model, PMFS closed loop,
or post-target hyperparameter tuning is permitted.

---

# PART I — R3B DATASET GENERATION

## 1. Pre-run parity and source-config diff audit

Before the first GADEN process:

1. verify the R3A source panel and runlist hashes exactly;
2. verify the frozen generator hash exactly;
3. regenerate all 64 launch/config views **without running**;
4. compare every proposed launch/config to its parent S2 context.

Within a matched context, the only scientifically allowed changes relative to
the parent non-source contract are:

- source x/y/z;
- explicit master RNG seed;
- run/output identifiers and output path.

The following must remain inherited from the parent context:

- House / occupancy;
- wind asset and wind timeline;
- gas type;
- source emission / release-rate parameters;
- temperature and source geometry parameters other than xyz;
- simulation duration/timebase;
- save semantics;
- wind-update semantics;
- OpenMP / deterministic generator contract;
- all other non-source launch parameters.

Any unapproved scientific field difference => STOP:

`OCB_R2_R3B_CONFIG_PARITY_FAIL`

Export an explicit field-level diff audit before running.

## 2. Fresh storage preflight

Before the first smoke run:

- run a fresh VM `df -h`;
- verify the C: host archive has at least 20 GiB free;
- verify the VM has enough free space for the established one-run
  run->QC->hash->archive->verify->cleanup cadence;
- D: must not be used as the sole archive destination.

If the one-run cadence cannot be executed safely, STOP for infrastructure only.

## 3. Structural smoke

Run exactly 8 smoke cases first, one per context, alternating the two new
sources so that both custom source heights/IDs in each House are exercised.

Suggested deterministic smoke set:

- X00 / new1 / rep1
- X01 / new2 / rep1
- X02 / new1 / rep1
- X03 / new2 / rep1
- X04 / new1 / rep1
- X05 / new2 / rep1
- X06 / new1 / rep1
- X07 / new2 / rep1

Inspect **structural/provenance only**:

- generator SHA;
- requested and recorded seed;
- intended source xyz;
- parent gas type;
- parent wind/occupancy hashes;
- record count = 1803;
- first time = 0;
- last time approximately 999.502991 s;
- legal wind-index sequence;
- finite plume output;
- complete file inventory;
- VM->C archive SHA verification.

Do not extract E1 concentrations and do not compute any source score during
smoke.

Any smoke failure => STOP and repair infrastructure only.

## 4. Production

After 8/8 smoke structural PASS, run the remaining 56 frozen rows unchanged.

For every run:

1. generate one run;
2. structural QC;
3. make complete file inventory and SHA256 manifest;
4. copy to `C:\GADEN_OCB_R2_ARCHIVE\r3_multisource`;
5. verify host hashes against VM inventory;
6. only then remove that VM raw leaf.

Do not batch-retain the full 64 raw outputs on the VM.

## 5. R3B dataset gate

### `OCB_R2_R3B_MULTISOURCE_DATASET_PASS`

Requires all:

1. 64/64 frozen prospective runs complete;
2. 64/64 exact generator hash;
3. 64/64 exact intended custom source xyz;
4. 64/64 exact parent wind/gas/occupancy/non-source contract;
5. 64/64 qualified 1803-record timeline;
6. 64/64 host archive hash verification;
7. 64 seeds unique and equal to frozen runlist;
8. no confirmation or House03 touched;
9. no scientific target score computed before dataset PASS.

If any scientific contract fails, report dataset FAIL and STOP.

### Mandatory stop after R3B

Even if R3B passes:

- STOP;
- do not extract target tensors;
- do not execute R3C scoring in the same Codex run.

Human review must authorize target extraction/scoring.

---

# PART II — R3C SCORING CONTRACT (FROZEN NOW, EXECUTE ONLY AFTER R3B REVIEW)

This section is frozen before any R3 target exists so no scoring rule can be
changed after seeing outcomes.

## 6. Primary prospective target population

Primary targets are exactly the **64 new-source R3 runs**.

For each context, the candidate source panel is fixed to four sources:

- old configured source 1;
- old configured source 2;
- R3A new source 1;
- R3A new source 2.

Old S2/S2X targets may be scored only as a secondary continuity/bias audit.
They are not part of the primary prospective decision.

## 7. Observation contract

Use exactly the R0/R1/R2 observation operator:

- E1 30 source-blind probes;
- observation z = 0.20 m;
- requested physical times 50,100,...,500 s;
- nearest-native-record rule;
- binary encounter `B[t,q] = 1[C[t,q] > 0]`;
- no threshold fitting.

Extraction code and requested-time map must be frozen before reading R3
concentration values.

## 8. Fair K=3 candidate references

For a primary target with replicate index r:

- truth candidate: use the other 3 of its 4 realizations;
- every alternative candidate: primary view omits replicate index r and uses
  the remaining 3;
- old-source reference banks come from frozen S2+S2X;
- new-source reference banks come from R3B.

No candidate gets K=4.

For robustness, precompute each alternative candidate under all four possible
3-of-4 omissions. Candidate score computation may be cached.

## 9. Frozen candidate scores

### 9.1 M-FULL marginal baseline

For candidate s:

`p_s(t,q) = mean_i B_s(i,t,q)`

`S_M(s,y) = mean_tq [y(t,q)-p_s(t,q)]^2`

Lower is better.

### 9.2 Broad-memory RAW path score

For lag L in {1,2,3}, use the same 60-D lag-pair fair-U Energy Score as R1/R2
on intact K=3 realization pairs:

`ES_RAW_s,L(y)`

Freeze:

`S_RAW(s,y) = mean_{L=1..3} ES_RAW_s,L(y)`

Lower is better.

### 9.3 Marginal-preserving Q-time path score

For each candidate and lag, independently permute the second-snapshot
realization identity while preserving both complete 30-D snapshot multisets,
using exactly the R1/R2 Q-time implementation and frozen deterministic RNG
derivation.

Use 1000 surrogates.

`ES_Q_s,L(y) = median_b ES_Q_s,L,b(y)`

Freeze:

`S_Q(s,y) = mean_{L=1..3} ES_Q_s,L(y)`

Lower is better.

### 9.4 Candidate broad-memory factor

`E_BM(s,y) = S_Q(s,y) - S_RAW(s,y)`

Higher is better.

No lambda, learned fusion, logistic calibration, softmax, learned lag weights,
target-dependent lag choice or post-hoc score normalization is permitted.

## 10. Primary four-source margins

For each target define:

### Marginal baseline margin

`G_M = min_{wrong} S_M(wrong,y) - S_M(truth,y)`

### Q-time path margin

`G_Q = min_{wrong} S_Q(wrong,y) - S_Q(truth,y)`

### Intact path margin

`G_RAW = min_{wrong} S_RAW(wrong,y) - S_RAW(truth,y)`

### Source-conditioned broad-memory-factor margin

`G_E = E_BM(truth,y) - max_{wrong} E_BM(wrong,y)`

### Matched dependence increment

`I_PATH = G_RAW - G_Q`

Positive `I_PATH` means preserving the true cross-time realization structure
improves truth-vs-best-wrong separation relative to the exact
marginal-preserving Q-time intervention in the **same Energy Score family**.

## 11. Primary aggregation

Primary group unit:

new-source x context, averaging four target realizations.

Thus:

- 64 target rows;
- 16 new-source x context groups;
- 8 contexts;
- 8 House01 groups;
- 8 House02 groups.

Report for G_E and I_PATH:

- House medians;
- positive groups /16;
- positive contexts /8;
- leave-one-context-out pooled medians;
- exact one-sided 8-context sign-flip reference;
- largest absolute context contribution.

## 12. Frozen Gate C1 — unseen-source path-factor generalization

### `R3C_PATH_FACTOR_GENERALIZES`

Requires for group-mean G_E:

1. House01 median > 0;
2. House02 median > 0;
3. at least 12/16 groups > 0;
4. at least 6/8 context means > 0;
5. every leave-one-context-out pooled median > 0;
6. exact 8-context one-sided sign-flip <= 0.05;
7. no context contributes >40% of total absolute context effect;
8. all four synchronized alternative-omission views retain positive H01,
   H02 and pooled medians;
9. Q-time preservation audit passes;
10. deterministic repeat byte-identical.

This is the direct prospective test that the R2 candidate-wise broad-memory
term generalizes to new source locations.

## 13. Frozen Gate C2 — matched path-dependence increment

### `R3C_RAW_BEATS_QTIME`

Apply the same ten conditions above to group-mean `I_PATH`.

This gate is especially important because RAW and Q use the same score family
and differ only in preserved cross-time realization pairing.

## 14. Rank-level practical test

For M-FULL, Q, RAW and E_BM report:

- unique Top-1;
- truth rank 1..4;
- MRR;
- mean/median truth-vs-best-wrong margin;
- per-House values;
- per-source values;
- hard-neighbor confusion matrix.

For the matched RAW vs Q comparison also report:

- Q-wrong -> RAW-correct rescues;
- Q-correct -> RAW-wrong harms;
- rank improvements / ties / degradations.

Define rank-level practical improvement only if:

1. RAW unique Top-1 > Q unique Top-1;
2. RAW MRR > Q MRR;
3. rescues > harms;
4. neither House loses unique Top-1 accuracy.

No minimum arbitrary percentage improvement is imposed in discovery; the
continuous C2 stability gate is the primary inferential requirement.

## 15. Baseline-ceiling interpretation

M-FULL is a separate baseline with a different proper score scale.

Do not add M-FULL and E_BM numerically in R3C.

If M-FULL remains 64/64 unique Top-1:

- label it `M_FULL_CEILING`;
- do not claim improvement over the marginal baseline;
- the prospective result may still establish unseen-source path-factor
  generalization and RAW-vs-Q dependence benefit.

If M-FULL has errors/headroom, report whether RAW/E_BM evidence is positive on
those exact baseline-hard targets, but do not invent a fusion rule after seeing
them.

## 16. Candidate-bias audit

Because E_BM is candidate-specific, verify it is not merely a static
candidate-popularity score.

Report:

- how often each candidate wins E_BM over all primary targets;
- candidate mean E_BM across targets;
- truth-conditioned vs non-truth E_BM distributions;
- secondary old-source target results, clearly marked OPEN/legacy-continuity;
- whether one candidate wins >50% of all targets regardless of truth.

A popularity pattern cannot rescue C1 or C2 and must be discussed explicitly.

## 17. R3C decisions

### `OCB_R2_R3C_PROSPECTIVE_PATH_ADVANCE`

Use only if:

- C1 passes;
- C2 passes;
- rank-level RAW-vs-Q practical improvement passes.

Meaning:

the frozen broad-memory path mechanism generalizes prospectively to new source
locations and improves four-source ranking relative to a matched
dependence-destroyed baseline.

This licenses method construction / calibrated probability-map integration on
discovery data only.

### `OCB_R2_R3C_PATH_MARGIN_ONLY_HOLD`

Use if C1 and C2 pass but rank-level practical improvement does not.

Meaning:

the mechanism generalizes, but practical localization ranking benefit is not
yet established.

### `OCB_R2_R3C_FACTOR_ONLY_HOLD`

Use if C1 passes but C2 fails.

### `OCB_R2_R3C_NO_GO`

Use if C1 fails.

## 18. Stop boundary after R3C

After one R3C label:

- STOP;
- do not open H01/H02 confirmation;
- do not open House03;
- do not train diffusion/flow models;
- do not construct a fused PMFS map automatically;
- do not run closed loop.

Human review decides the next stage.

## 19. Required R3B outputs

- pre-run field-level config diff audit;
- fresh disk-space preflight;
- smoke-run structural report;
- 64-run structural results TSV;
- complete archive SHA inventory/proof;
- R3B dataset decision report.

## 20. Required R3C outputs

- input/extraction parity audit;
- 64 target tensors + hashes;
- candidate score table for M-FULL/Q/RAW/E_BM;
- target margin/rank table;
- 16-group summary;
- 8-context summary;
- omission robustness;
- candidate-bias audit;
- deterministic repeat proof;
- R3C decision report.
