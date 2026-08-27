# CG-PC-CTT V3 cross-representation evidence and runtime-reuse decision — 2026-08-27

Status: **THEORY / DIAGNOSTIC ONLY**. This does not replace the missing exact H02 hard-28 CTT product and does not alter frozen Gate V2.

## 1. New partial H02 recovery asset

The recovery package contains a frozen House02 V12-M response bank with:

- magic `V12BNKR1`;
- grid `27 x 39`, 1053 cells, 631 free cells;
- 201 carriers, all 201 physical coordinates unique;
- 8 transport members;
- 200 recorded timesteps;
- method seed `20260818`;
- transport substream `6077111455669390931`;
- SHA-256 `c5b768a5b8123d0736048c601fe6534293b12aaed3e5e84140d9e527c83bdf6e`.

This bank contains PMFS hit-probability response maps. It is **not** the CTT first-passage hard-28 bank and must never be relabeled as `phi[28,201,8,D]` hard-case evidence.

## 2. Cross-representation local tangent diagnostic

The V3 2-D local tangent diagnostic was applied to the V12 hit-probability response representation, using only the frozen response bank and source geometry. This asks a different question from hard-28:

> Does observation-conditioned geometric rank loss persist after the transport field is represented as PMFS hit-probability response maps?

At full 631-cell support:

- fraction of 201 physical source positions with `lambda_min(F_s)>0`: `1.0`;
- median `gamma_xy=sqrt(lambda_min/lambda_max)`: approximately `0.4659`;
- 5th percentile `gamma_xy`: approximately `0.1999`.

With frozen random free-cell subsets, mean fractions with positive second tangent eigenvalue were approximately:

| observed support Q | fraction lambda_min>0 | mean median gamma_xy |
|---:|---:|---:|
| 1 | 0.0139 | 0.0000 |
| 2 | 0.0139 | 0.0000 |
| 4 | 0.0945 | 0.0000 |
| 8 | 0.2478 | 0.0124 |
| 16 | 0.6587 | 0.1500 |
| 32 | 0.8308 | 0.3213 |
| 64 | 0.9532 | 0.4187 |
| 128 | 0.9672 | 0.4578 |
| 256 | 1.0000 | 0.4617 |
| 631 | 1.0000 | 0.4659 |

This qualitatively reproduces the sparse-support rank-loss curve previously observed in the H03 CTT first-passage representation. Therefore the V3 observation-conditioned 2-D resolution premise is not specific to one response encoding: sparse support destroys two-coordinate source information in both transport-side and hit-probability response representations.

A reproducible parser/audit is committed as:

`experiments/cg_pc_ctt/v12_response_bank_tangent_audit.py`.

## 3. Runtime reuse: no second online simulator is required

The existing PMFS `applyEnsembleEcEdcl()` code already constructs the core V3 observation object. For each candidate source `s`, replica `m`, and actually observed event `e`, it:

1. runs the existing `simulateSourceInPosition()` physical forward kernel;
2. samples the resulting `hitMap` at the measured event cell;
3. stores the value in `rawProbabilities[s][m][e]`;
4. only afterwards performs the old EC-ECDL Hellinger normalization/projection.

Thus the existing raw tensor is already the deployable observation operator

`z[s,m,e] = H_e phi[s,m]`.

### Binding V3 runtime decision

For an eventual V3 runtime prototype:

- reuse the existing candidate set, event ledger, keyed transport replicas, and `simulateSourceInPosition()` calls;
- compute the physical-coordinate quotient and 2-D tangent information from **rawProbabilities before Hellinger normalization**;
- do not introduce a second Torch/CTT online simulator merely to materialize `H_e phi`;
- keep the CTT first-passage bank as offline transport-mechanism evidence, not as a mandatory online data structure.

This sharply reduces runtime integration work and keeps the observation-resolution formula aligned with an existing ROS data path.

## 4. Consequence for the missing H02 hard-28

The exact hard-28 CTT bank/margins are still required for the frozen V2/bridge falsification protocol. The V12 response bank cannot replace them.

However, hard-28 recovery and V3 runtime engineering are now decoupled:

- hard-28 restoration continues only for the frozen scientific falsification endpoint;
- observation-conditioned local resolution can be prototyped from the existing PMFS event-by-replica response path without waiting for `.cttbin` recovery.
