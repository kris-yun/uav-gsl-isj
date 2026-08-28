# CODEX TASK — V6 separate hard-component failure from transport-family failure

Date: 2026-08-28

Branch: `research/cg-pc-ctt-v6-dynamic-transport-sbi`

Read first:

`docs/CG_PC_CTT_V6_DYNAMIC_TRANSPORT_INFERENCE_FREEZE_20260828.md`

## Objective

Do NOT continue the V5 Active Probe smoke yet.

V5 passive replay produced 0/30 ACCEPT, but `CONTEXT_LOO_COMPONENT_DISAGREE` alone does not distinguish:

1. hard source-component fragmentation as resolution increases; from
2. genuine continuous source-ranking inconsistency caused by transport-model misspecification.

Resolve this ambiguity first using the already materialized 150 truth-blind contexts. This should be cheap and requires no trace-bank rebuild.

## Stage 0 — sync and immutable checks

Pull the exact V6 branch and record HEAD.

Run:

```bash
cd /home/zyc/uav-gsl-isj
python3 experiments/cg_pc_ctt/selftest_v4_final_reference.py
python3 experiments/cg_pc_ctt/selftest_v5_active_sequential_reference.py
python3 experiments/cg_pc_ctt/selftest_ctt_bank_io.py
```

All existing science/I/O tests must PASS.

Do not edit V4/V5 formulas to make V6-A pass.

## Stage 1 — quantify V5 component fragmentation

From the existing V5 passive ledger CSV, produce a table by House and update index with:

- median / min / max component count;
- median unique-stop count;
- component count divided by persistent source-carrier count;
- failure-reason distribution.

Also report per House the ratio:

`final_component_count / first_context_component_count`.

This is descriptive only. Do not tune a component threshold.

Deliver:

`artifacts/v6a_continuous_diagnostic/v5_component_fragmentation.csv`

and include the table in the report.

## Stage 2 — run V6-A continuous source-transfer diagnostic

Reuse the already frozen NPZs exactly:

`/home/zyc/V4_TRUTHBLIND_COVERAGE_20260828_R1/contexts`

Run:

```bash
cd /home/zyc/uav-gsl-isj
python3 experiments/cg_pc_ctt/v6a_continuous_source_diagnostic.py \
  /home/zyc/V4_TRUTHBLIND_COVERAGE_20260828_R1/contexts \
  --out-json artifacts/v6a_continuous_diagnostic/v6a_continuous_source_diagnostic.json \
  --out-csv artifacts/v6a_continuous_diagnostic/v6a_continuous_source_folds.csv
```

The diagnostic is truth-blind and component-free.

For each run report:

- source-transfer pass;
- absolute-null pass;
- number of strictly positive source-transfer contexts;
- posterior entropy and max mass;
- minimum/maximum held-out source-transfer gain;
- minimum held-out absolute gain.

Aggregate H01/H02/H03 separately.

## Stage 3 — required interpretation

### Case A — at least 20/30 continuous predictive passes

Verdict:

`V6A_HARD_COMPONENT_IDENTITY_PRIMARY_BLOCKER_CANDIDATE`

Meaning:

The current transport family has at least enough continuous source evidence to transfer in the number of runs required by the downstream development endpoint, while the hard component identity killed V5.

Do NOT resurrect the old component Gate.

Next, freeze a component-free candidate posterior formula from V6-A and create a separate dev-truth replay. Do not implement C++ before that source-validity replay.

### Case B — fewer than 20/30 continuous predictive passes

Verdict:

`V6A_CONTINUOUS_SOURCE_TRANSFER_INSUFFICIENT`

Meaning:

Hard-component fragmentation is not sufficient to explain V5. Existing frequency-only source evidence itself does not transfer across enough contexts.

Proceed to Stage 4. Do not implement V5 Active Probe and do not change a Gate.

## Stage 4 — V6-B dynamic-observation feasibility materialization

Only run this stage after Case B.

The purpose is to test information currently destroyed by collapsing eight ordered blocks to one mean hit fraction.

### 4.1 Archive fields to retain

For every physical stop in all 30 development OFF runs, preserve:

- ordered eight completed-block HIT/NOTHING outcomes;
- ordered eight `avg_gas` values from the authoritative action log;
- physical cell id and stop pose;
- source-update/context id;
- context wind snapshot provenance;
- no source truth or localization error in the truth-blind payload.

Do not replace the eight-block tape with only its mean.

### 4.2 Forward trace fields

The CTT V13 `.cttbin` records already contain:

- `firstHitBins[cell_count]`;
- `occupancyWords[T, words_per_step]` with `T=200`.

For each source/member at the ACTUAL observed physical stop, extract the full temporal occupancy tape or sufficient exact transition counts. Stream/rebuild banks and delete temporary banks as in V4 materialization to respect disk limits.

Do not generate predictions for unobserved cells and call them observations.

### 4.3 Timing contract

Determine from frozen runtime/builder provenance whether CTT record steps have a known physical mapping to the PMFS measurement-block interval.

- if exact mapping exists, document it and use it;
- if not, do not guess a dilation or optimize one against truth/performance;
- use a timing/phase-invariant transition likelihood as the first frozen dynamic reference.

### 4.4 Minimum dynamic reference

Implement a source/member/stop likelihood that distinguishes ordered tapes with equal hit fraction.

At minimum it must distinguish a persistent tape such as

`00001111`

from a high-transition tape such as

`01010101`

when the predicted temporal occupancy processes differ but their mean occupancy is equal.

Use Jeffreys-smoothed binary transition probabilities so no zero-probability tuning constant is introduced.

Context-level member identity is a nuisance variable. Source is global across contexts; member may differ by context.

Do NOT require one common hard source component.

### 4.5 V6-B held-out validation

Use the same held-out questions as V6-A:

1. Does training-context source evidence improve held-out prediction over a geometry-prior source mixture?
2. Does the model beat a source-independent dynamic observation null?
3. Does leave-one-scoring-member-out preserve ACCEPT, not merely avoid a different accepted basin?

Required outputs:

- `experiments/cg_pc_ctt/v6_dynamic_trace_reference.py`
- `experiments/cg_pc_ctt/selftest_v6_dynamic_trace_reference.py`
- `artifacts/v6_dynamic_trace/...` truth-blind summaries
- `docs/V6_DYNAMIC_TRACE_TRUTHBLIND_REPORT_20260828.md`

## Stage 5 — one-time development-truth source-validity test

Only after the V6-B formula, temporal mapping rule, member marginalization and held-out tests are frozen and committed.

Then, and only then, open development source truth for seeds 0..9 in a SEPARATE script/report.

Compare frozen V6 posterior with Classic PMFS on the SAME archived OFF observations.

Report:

- final expected-location error per run;
- pooled percentage change;
- number of 30 runs improved;
- per-House pooled change;
- nearest-true-carrier rank and posterior mass where meaningful.

No V6 parameter, prior, lag, feature, member set, threshold or formula may change after this report is opened.

Interpretation:

- If frozen V6 gives pooled error improvement >=10%, >=20/30 runs improve, and no House degrades >5% on the OFF-replay posterior endpoint, authorize C++/closed-loop development.
- Otherwise reject V6-B as the main method. Do not threshold-tune it.

This offline criterion intentionally mirrors the already frozen closed-loop development target. It is a pre-C++ source-validity screen, not confirmatory evidence.

## Stage 6 — if V6-B fails, stop using the fixed eight-member CTT family

Do not make V6-C another feature patch.

Create a separate proposal for physics-factorized GADEN simulation inference:

- global latent source `s`;
- context transport latent `z_c`;
- sensor/noise latent where identifiable;
- randomized forward simulations spanning transport changes;
- conditional neural ratio/posterior estimator;
- held-out House and transport perturbation evaluation.

The architecture should be motivated by the 2026 CIGaRS end-to-end physics/SBI approach and should represent both displacement and mass/dilution transport degrees of freedom, rather than only more fixed plume members.

Do not start its expensive simulation generation until the V6-B source-validity result has shown the fixed family cannot be rescued by ordered dynamics.

## Forbidden shortcuts

- no V5 Active Probe smoke before V6-A is interpreted;
- no lowering the absolute null;
- no House/seed-specific rule;
- no truth inside V6-A/V6-B construction;
- no selecting temporal lag or feature set using localization error;
- no treating component count as proof of source validity;
- no claiming invariance equals Pearl/Rubin causal identification;
- no 60-arm run before a frozen source-validity candidate exists.

## Final deliverable now

Commit Stage 1 + Stage 2 results first and stop at the branch decision.

Return one of exactly:

- `V6A_HARD_COMPONENT_IDENTITY_PRIMARY_BLOCKER_CANDIDATE`
- `V6A_CONTINUOUS_SOURCE_TRANSFER_INSUFFICIENT`

with exact House/run counts and the report path.
