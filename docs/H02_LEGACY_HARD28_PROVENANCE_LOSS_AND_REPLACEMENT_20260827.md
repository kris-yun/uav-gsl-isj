# H02 legacy hard-28 provenance loss and replacement challenge — 2026-08-27

Status: **FROZEN BEFORE REPLACEMENT-CHALLENGE OUTCOMES**

## 1. Disposition of the historical hard-28

The project has retained historical summary statements for a House02 simple-transport challenge (28/28 negative true-vs-wrong margins, mean approximately -34.22, true-source rank median approximately 118.5/201, wrong-source rank median approximately 5/201), but the exact primary artifact `h02_transport_gate_fast2.csv`, the 28-case identity list, the matching CTT first-passage member banks, and the corresponding frozen M1 margins have not been recovered from Git, PR discussions, surviving VM context-bank archives, or the bounded recovery package.

Therefore the historical artifact is reclassified as:

`LEGACY_HARD28_PROVENANCE_LOST`

The numerical summary may be mentioned only as historical development context. It must not be used as a confirmatory dataset, must not be reconstructed by matching those summary numbers, and must not be used to tune a new threshold.

The recovered V12 House02 `201 x 8 x 631` hit-probability response bank is a different representation and generation contract. It must not be relabeled as the lost CTT hard-28.

## 2. Why a replacement challenge is scientifically preferable to continued artifact hunting

The current main scientific question is not whether one missing CSV can be recreated. It is whether a truth-blind, observation-conditioned source-resolution rule prevents unsupported localization precision and whether the downstream evidence update improves source discrimination without common-mode or proxy leakage.

The replacement challenge is therefore newly preregistered before outcome inspection and uses current frozen physical contracts rather than reverse-engineering the lost historical result.

## 3. Replacement challenge name

`H02_RECONSTRUCTED_CHALLENGE_V1`

This is a new experiment. It is not the historical hard-28.

## 4. Case-manifest freeze rule

Before any bridge/source-margin truth evaluation:

1. scan all surviving House02 context-bank roots;
2. include every source-update context satisfying only structural/provenance criteria below;
3. freeze the resulting ordered manifest and SHA256;
4. if fewer than 18 structurally valid context atoms or fewer than 3 independent run/seed clusters survive, generate fresh House02 context-only qualification runs using frozen code and seeds generated before any outcome inspection until both minima are reached;
5. never select or remove a case because its source margin, gate result, or localization error is favourable/unfavourable.

Structural eligibility only:

- House02 environment;
- valid context-bank contract and finite observation/event data;
- measured wind, pose/event positions and timestamps available causally;
- no source truth/runtime oracle field in the online representation;
- candidate geometry can be mapped to the frozen 201-coordinate House02 carrier manifest;
- no duplicate `(run_uuid, source_update_id)`;
- CTT/PMFS predictive member generation completes for all 201 candidates and all 8 members under one frozen generator/key contract.

Truth is revealed only after the manifest, model coefficients (if any), and negative-control definitions are frozen.

## 5. Physical candidate support

Use the recovered House02 V12 201-row carrier manifest only as a **geometry-only source-query grid**. All 201 coordinates are unique. Its V12 hit-probability bank may be used for representation diagnostics but cannot substitute for newly generated CTT first-passage evidence when a CTT quantity is claimed.

Candidate ID is not a physical source state. Any future duplicate-coordinate grid must first be quotiented by exact coordinate equality before source-resolution analysis.

## 6. Runtime observation-conditioned object

For each context/event history `e`, construct the candidate-by-member response only at actually observed support:

`z[s,m,e] = H_e phi[s,m]`.

Preferred runtime implementation reuses the existing PMFS `rawProbabilities[source][replica][event]` dataflow before Hellinger normalization. The full unvisited field must not be counted as current localization evidence.

## 7. Local source-resolution criteria (truth blind)

Primary physical source parameter is 2-D `(x,y)`.

For each candidate neighbourhood, compute the observation-conditioned cross-member local tangent information

`F_s = sum_{m!=n} B_{s,m} B_{s,n}^T / [M(M-1)]`,

where `B` is the nuisance-whitened local response derivative with respect to physical source displacement.

Also compute local pair cross-member separation on Delaunay/neighbour edges using the V2 pair-difference nuisance scale.

No outcome-fitted threshold is introduced. Prototype release prerequisites are:

- local physical geometry rank is adequate for the local source manifold;
- required pair contrasts have positive cross-member strength;
- member sign-flip screen `p<=0.01` where used;
- leave-one-member-out pair strength remains positive;
- even/odd evidence folds agree on source-vs-rival ordering before posterior release.

Failure means exact abstention/coarser observational equivalence class, not a sharpened low-weight update.

## 8. Observation adequacy / wrong-but-reproducible guard

Cross-member replication alone cannot detect a forward family that is consistently wrong. Therefore every released source update must also evaluate observation compatibility between the actually observed outcome marker `Y_e` and the candidate predictive family.

Primary `R` for any proximal/host-aware bridge is restricted to source-independent context (wind, pose, action/motion, map/geometry). Gas, hit count, concentration history, encounter gaps, and sensor-state variables are outcome/downstream variables and must not enter the primary causal `R` contract.

## 9. Negative controls frozen before outcome inspection

At minimum run:

1. source-coordinate shuffle;
2. transport-member/candidate-identity destruction control that breaks stable source correspondence;
3. observation-position permutation within the admissible support;
4. temporal reversal/permutation for the within-stop dynamical marker when temporal structure is claimed.

A real improvement that survives equally under these destruction controls is not accepted as mechanism evidence.

## 10. Advancement rule to the full 30-pair closed loop

This replacement challenge is an engineering/scientific falsification gate, not the final paper endpoint. It does not need to reproduce the old number 28.

Advance to the already preregistered `3 Houses x 10 seeds x OFF/ON` closed-loop matrix only if all of the following hold:

- provenance/data-contract audits PASS;
- no outcome-based case selection occurred;
- real method mean and median true-vs-best-false margin change are both positive across eligible context atoms;
- at least 70% of independent run/seed clusters have positive mean margin change;
- source/observation destruction controls each retain at most 50% of the real mean margin gain;
- no false-confident-collapse diagnostic is triggered;
- no House/seed-specific tuning is introduced after manifest freeze.

The definitive localization claim remains the 30 matched-pair closed-loop endpoint already frozen in the fast-track branch: pooled PMFS top-5 error reduction >=10%, paired sign-test p<=0.05, no House mean degradation >5%, and zero false-confident collapse.

## 11. Binding scientific language

Allowed:

- `historical hard-28 summary exists but primary provenance was lost`;
- `H02_RECONSTRUCTED_CHALLENGE_V1 is a newly preregistered replacement challenge`;
- `V2 remains a model-side replicated-completeness premise unless new evidence proves reliability stratification`.

Forbidden:

- calling the reconstructed challenge the original hard-28;
- tuning new cases to reproduce the old -34.22 / rank medians;
- using V12 response-bank values as if they were CTT first-passage margins;
- claiming offline GO solely from global V2 PASS.
