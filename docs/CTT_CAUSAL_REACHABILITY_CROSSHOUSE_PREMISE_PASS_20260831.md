# CTT causal-reachability cross-House premise PASS

Date: 2026-08-31  
Frozen code commit: `0290ae7`  
Terminal verdict: `CTT_CAUSAL_REACHABILITY_CROSSHOUSE_PREMISE_PASS`

The preregistered train8-to-reserved4 Gate completed without generating a new
GADEN world, training a network, reading a PMFS posterior, or using historical
localization error. All 7,404 bank shards and all H01/H02/H03 seed0..9 route
hashes were verified before scoring.

## Primary source-ordering result

| Scope | Mean normalized true-source rank | Exact-phase ablation | Cases |
|---|---:|---:|---:|
| H01 | 0.112244 | 0.112692 | 8,400 |
| H02 | 0.096024 | 0.100653 | 8,040 |
| H03 | 0.197244 | 0.214440 | 8,240 |
| pooled over 12 independent units | **0.135171** | report only | 24,680 |

Random source ordering has expected normalized rank about 0.5. All 12
`House x reserved-member` independent units were below 0.35; all three House
source-label destruction tests and the pooled test achieved the minimum
256-replicate empirical value `p=1/257=0.00389105`. Candidate, observation
source, and predictive-member invariances had maximum absolute discrepancy
`2.13e-14`, below the frozen `1e-12` tolerance. Every hard rule passed.

The report-only exact first-passage model was slightly worse than reachability
in every House on the pooled mean, most clearly in H03. This supports the
frozen scientific boundary: the robust temporal object is persistent-sensor
reachability/censoring; precise arrival phase is not the main mechanism.

## What this proves and what it does not

This Gate establishes that the requested two-module chain contains
cross-House source-identifying information:

```text
native GADEN do(S=s) physical response + persistent sensor
    -> transport-marginalized physical-stop reachability evidence.
```

It does not yet establish PMFS localization improvement or closed-loop gain.
The next authorized test is a measured-only source-update shadow on the 30
existing OFF runs. A trajectory-independent native lookup, exact single
consumption and planner closure remain required before paired 300-s ON runs.

## Evidence

Local evidence directory:

`D:\ZYC\A-gas\_staging\CTT_CAUSAL_REACHABILITY_CROSSHOUSE_PASS_20260831_R1`

Key SHA-256 values:

- `SUMMARY.json`: `7a9fc8ea61102da463c100739233f47daaf47daec8b8f6cbd6f3f8b6740adde6`
- `CASES.csv`: `a7f868a3ab7b9befd1e9b2401c891bab76015753b6f2f1c893fd49b032ce3c67`
- `INDEPENDENT_UNITS.csv`: `c5713ca8b9bb20efd4cc4a4de37cb81c5ae1466eb87ef26566fa2bb1f0b83876`
- `SOURCE_LABEL_NULLS.csv`: `491d883f2ac37bf66ed8acef67346a827614f116a32d236fe704232aff776b7e`
