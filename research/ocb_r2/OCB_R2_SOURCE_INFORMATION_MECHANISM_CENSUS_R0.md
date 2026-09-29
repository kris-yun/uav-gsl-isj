# OCB-R2 Source-Information Mechanism Census R0

Date: 2026-09-30

Status: **PREREGISTERED DISCOVERY-ONLY / NOT EXECUTED**

## Purpose

This is not a method test and not a literature-driven route.

The purpose is to identify which source-relevant information layer is stably
present across the repaired OCB-R2 discovery benchmark before selecting any
new far-domain mother theory.

Use only the already-qualified H01/H02 discovery data:

- S2: 32 original-config runs
- S2X: 32 matched-source crossover runs
- total: 64 targets
- 8 fixed House-wind-gas-occupancy-generator contexts
- 2 source positions/context
- 4 independent realizations/source

H01/H02 confirmation and House03 remain sealed.

No new GADEN, no PMFS closed loop, no neural model, no new candidate bank.

## 0. Hard preflight

Rerun metadata-only D0A on combined S2+S2X.

Required contract:

- 8/8 fixed non-source contexts
- exactly 2 source positions/context
- exactly 4 independent realizations/source
- identical House, wind, gas, occupancy, generator SHA and native timeline
  within each source comparison

If this fails, STOP with:

`OCB_R2_CENSUS_HOLD_COMPARABILITY`

If it passes, record:

`OCB_R2_D0A_SOURCE_COMPARABILITY_PASS`

## 1. Observation contract

Reuse the already-frozen AOD-R2 F0 discovery observation contract exactly.

- H01/H02 E1 30 source-blind probes
- z = 0.20 m observation plane
- requested physical times = 50,100,...,500 s
- already-frozen nearest-native-record mapping
- already-frozen concentration extractor
- reuse already-extracted 64 target tensors if hashes match

Do not choose new probes, times, thresholds or extraction settings.

Primary encounter tensor:

`B[t,q] = 1[C[t,q] > 0]`

No fitted concentration threshold.

## 2. Cross-fitting

For each context c, source s in {A,B}, realization r in {1,2,3,4}:

- target = realization r of source s
- truth reference = the other three realizations of source s
- alternative reference = the three realizations of the other source after
  omitting the same replicate index r

Thus both candidate sources use K=3 references.

Primary comparison uses this same-index omission rule.

Robustness later repeats the alternative-source score under all four possible
3-of-4 omission choices to verify that the result is not an artifact of the
arbitrary replicate-index alignment.

## 3. Marginal anatomy diagnostics

These diagnostics identify where source information exists before any joint
dependence is considered.

### M-TIME

At each time, average across probes.

Candidate mean:

`mu_time_s[t] = mean_q p_s[t,q]`

Target:

`y_time[t] = mean_q B_target[t,q]`

Score with mean squared Brier-type loss over 10 times.

### M-SPACE

At each probe, average across times.

Candidate mean:

`mu_space_s[q] = mean_t p_s[t,q]`

Target:

`y_space[q] = mean_t B_target[t,q]`

Score with mean squared Brier-type loss over 30 probes.

### M-FULL

Full 10x30 marginal field:

`p_s[t,q] = mean_i B_s[i,t,q]`

Score:

`S_MFULL(s,y) = mean_{t,q} (y[t,q] - p_s[t,q])^2`

For each marginal diagnostic define the true-vs-alternative discrimination
margin:

`G = S_alt - S_truth`

Positive G means the true source is better supported.

These are mechanism diagnostics. Do not tune or select a model from them.

## 4. Dependence interventions using one common score family

Use the fair U-statistic Energy Score with Euclidean distance on the flattened
10x30 binary tensor.

Lower score is better.

### C1 — marginals only

Within each candidate source, independently permute the K realization labels at
every coordinate (t,q).

This preserves exactly:

- every empirical p_s(t,q)
- binary support
- expected encounter count at every time

It destroys:

- within-time cross-probe pairing
- cross-time realization pairing

Generate exactly 1000 surrogate banks using frozen RNG seed `2026093001`.

### C2 — each-time spatial snapshots preserved

At each time t, independently permute the K complete 30-D snapshots across
realization labels.

This preserves exactly:

- every empirical p_s(t,q)
- the complete empirical set of 30-D snapshots at each time
- each-time encounter-count distribution
- within-time spatial co-occurrence

It destroys only:

- which snapshots at different times belong to the same realization

Generate exactly 1000 surrogate banks using frozen RNG seed `2026093002`.

### RAW — intact 10x30 trajectories

Use the original K=3 realization tensors without permutation.

This preserves both within-time spatial structure and cross-time realization
pairing.

## 5. Source-discrimination margins

For RAW:

`G_RAW = ES_RAW(alt,target) - ES_RAW(truth,target)`

For each C1/C2 surrogate repetition b:

`G_C1[b] = ES_C1_b(alt,target) - ES_C1_b(truth,target)`

`G_C2[b] = ES_C2_b(alt,target) - ES_C2_b(truth,target)`

Use surrogate medians for the descriptive layer margins:

`Gbar_C1 = median_b G_C1[b]`

`Gbar_C2 = median_b G_C2[b]`

Define the two key incremental mechanisms:

### Instantaneous spatial-joint increment

`I_SPATIAL = Gbar_C2 - Gbar_C1`

Positive means preserving the complete each-time spatial snapshot structure
adds source discrimination beyond coordinate-wise marginals.

### Cross-time increment

`I_CROSS = G_RAW - Gbar_C2`

Positive means intact cross-time realization pairing adds source
discrimination beyond complete each-time spatial snapshots.

Also report:

`I_TOTAL_DEP = G_RAW - Gbar_C1`

No fusion coefficient or learned model is permitted in R0.

## 6. Aggregation hierarchy

Primary unit is a source×context group:

- 16 groups total
- each group aggregates its four held-out target realizations

Report target-level values, but do not treat the 64 targets as 64 independent
source populations.

For every mechanism report:

- 64 target-level effects
- 16 source×context group means/medians
- 8 context means/medians
- House01 median
- House02 median
- fast/slow strata
- gas10/gas13 strata
- source identity
- leave-one-context-out pooled result

## 7. Ceiling and difficulty diagnostics

Report M-FULL truth-vs-alternative margins for all targets.

If M-FULL is 64/64 correct, do not call a positive dependence margin a
localization rescue.

Instead report whether I_SPATIAL or I_CROSS consistently enlarges or shrinks
the source margin.

Also report the bottom quartile of M-FULL margins as a **descriptive**
hard-target diagnostic only. It must not change the frozen decision.

## 8. Robustness / destructive controls

### Reference-omission robustness

Repeat the alternative-source candidate score using all four possible 3-of-4
reference omissions while keeping K=3.

The sign of the aggregate mechanism result must not depend on the primary
same-index omission convention.

### Preservation assertions

For every C1/C2 surrogate verify exactly:

- coordinate marginals preserved for C1 and C2
- each-time snapshot multiset preserved for C2
- binary support preserved
- K unchanged

Any violation => STOP.

### Source-label null

Within each fixed context, randomly swap the two source labels at the
source×context group level using 10000 fixed-seed sign-flip draws
(`2026093003`) to obtain a null distribution for the pooled directional
effect.

Treat this as a randomization reference, not a universal p-value.

## 9. Mechanism decisions

R0 is a mechanism census. It does not select a final method.

### A. `OCB_R2_MECH_CROSS_TIME_STABLE`

Use only if all hold:

1. House01 median I_CROSS > 0
2. House02 median I_CROSS > 0
3. at least 12/16 source×context groups have mean I_CROSS > 0
4. at least 6/8 contexts have positive context-level I_CROSS
5. every leave-one-context-out pooled median remains > 0
6. source-label randomization reference is <= 0.05 in the observed direction
7. same direction survives all alternative-source omission choices
8. no single context contributes more than 40% of the absolute pooled effect
9. C2 preservation assertions all pass

Interpretation:

cross-time realization coupling is a stable source-information mechanism on the
repaired H01/H02 discovery benchmark.

This licenses a targeted search for a far-domain mother theory about
trajectory/path-space dependence, but not yet a method.

### B. `OCB_R2_MECH_SPATIAL_JOINT_STABLE`

Use if the CROSS_TIME gate fails but all analogous directional conditions hold
for I_SPATIAL.

Interpretation:

the stable extra source information is instantaneous spatial co-occurrence
beyond marginals.

This licenses a targeted search for a far-domain mother theory about spatial
random fields / collective spatial structure, not a temporal theory.

### C. `OCB_R2_MECH_MARGINAL_DOMINANT`

Use if neither joint gate passes, while M-FULL source discrimination is stable
across both Houses and at least 12/16 source×context groups have positive mean
M-FULL margin.

Then compare M-TIME versus M-SPACE descriptively:

- if M-SPACE is much more stable than M-TIME, flag spatial-footprint dominance
- if M-TIME is much more stable than M-SPACE, flag temporal-rate dominance
- if both are needed for M-FULL, flag spatiotemporal-marginal interaction

Interpretation:

complex joint modeling is not justified by discovery evidence. The next
scientific question should be why passive marginal evidence still leaves
full-map localization ambiguity.

### D. `OCB_R2_MECH_OBSERVATION_INSUFFICIENT`

Use if M-FULL itself is not directionally stable across Houses/contexts and no
joint mechanism passes.

Interpretation:

the current passive observation contract does not provide a stable source
signature. Future theory search should target observability / active sensing /
sensing-by-acting rather than richer passive inference.

### E. `OCB_R2_MECH_INCONSISTENT_HOLD`

Use when effects are mixed and no layer meets a stable interpretation.

Do not rescue with a learned model.

## 10. Stop boundary

After assigning exactly one R0 mechanism label:

- STOP
- do not search papers automatically
- do not implement a new method
- do not open H01/H02 confirmation
- do not open House03
- do not run closed loop

The next human review decides which far-domain mother-theory family is
scientifically matched to the observed mechanism.

## 11. Required outputs

- `research/ocb_r2/mechanism_census_r0/R0_PROTOCOL_FROZEN.md`
- `evidence/ocb_r2/mechanism_census_r0/R0_D0A_REAUDIT.json`
- `evidence/ocb_r2/mechanism_census_r0/R0_INPUT_HASHES.json`
- `evidence/ocb_r2/mechanism_census_r0/R0_MARGINAL_ANATOMY.tsv`
- `evidence/ocb_r2/mechanism_census_r0/R0_TARGET_EFFECTS.tsv`
- `evidence/ocb_r2/mechanism_census_r0/R0_GROUP_EFFECTS.tsv`
- `evidence/ocb_r2/mechanism_census_r0/R0_CONTEXT_EFFECTS.tsv`
- `evidence/ocb_r2/mechanism_census_r0/R0_PRESERVATION_AUDIT.json`
- `evidence/ocb_r2/mechanism_census_r0/R0_REFERENCE_OMISSION_ROBUSTNESS.tsv`
- `evidence/ocb_r2/mechanism_census_r0/R0_NULL_REFERENCE.json`
- `research/ocb_r2/mechanism_census_r0/R0_DECISION_REPORT.md`

