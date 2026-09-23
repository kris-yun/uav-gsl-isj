# Baseline-recovery implications for the main-innovation search

Date: 2026-09-23  
Target branch: \`research/maximin-transport-design-v1\`  
Evidence source: \`research/native-pmfs-baseline-recovery-v1\`, corrected R1.

## 1. What is now established

### Official package/source integrity
The user's local \`GasSourceLocalization-humble.zip\` was compared against MAPIRlab/GasSourceLocalization \`humble\`; 27/27 audited PMFS/launch/CMake files were byte-identical in scope.

### Recovered Native wind path
R0 proved the isolated recovery binary:
- was built with \`USE_GADEN=1\`;
- entered \`GADEN_GROUND_TRUTH\`;
- made 21 successful wind queries and zero fallbacks;
- matched all 626 free-cell internal wind vectors to the service after official float32 storage.

Therefore the old GMRF-wind anomaly must not be treated as evidence of an original PMFS wind bug.

## 2. Corrected R1 three-arm result

Frozen source update:
- same 20 observations;
- same 87 source candidates;
- deterministic repeat/hash checks;
- truth revealed only after scores froze.

Corrected truth-source rank:

| Arm | Forward contract | Rank |
|---|---|---:|
| A | frozen R2 source + GMRF + R2 params | 48/87 |
| B | frozen R2 source + ground-truth wind + R2 params | 18/87 |
| C | official humble source + ground-truth wind + official params | 47/87 |

Important:
- old preliminary A/B 47/14 is superseded;
- historical R2 executable was not found, so A/B are source-level faithful rather than byte-identical to that old executable;
- this is one House01 source-update snapshot, not a 300 s or six-run conclusion.

## 3. What the result does NOT justify

Do not claim:
- that GMRF wind alone explains all previous poor source ranks;
- that official Native PMFS is generally poor on VGR;
- that the full official parameter set is worse than R2;
- that a fixed forward family is already proven to be fundamentally inadequate;
- that any innovation line has passed because C is 47/87.

House01 is also a weak case for final mechanism claims if the measurement history is sparse/all-miss dominated.

## 4. What the result DOES motivate

The source identity is highly sensitive to the **joint forward-model contract**.

A→B changes wind semantics/path and improves rank strongly.

B→C keeps ground-truth wind but changes the PMFS source/transport/hit-map contract and rank returns near A.

Thus the data are compatible with a broader scientific problem:

> source evidence and forward-model/transport nuisance are entangled; a candidate can appear plausible or implausible because of the forward contract rather than source identity alone.

This is stronger motivation for **source-vs-transport deconfounding** than for a one-off wind correction.

## 5. Consequence for the candidate innovation

Do not frame the main idea as:
- "fix PMFS wind";
- "use a better diffusion model";
- "use ground-truth wind";
- "replace variance by a robust reward."

The current research target should be framed at the higher level:

> **Active source identifiability under transport nuisance / semiparametric active deconfounding.**

Core hypothesis:

> Nominal disagreement among candidate plume simulations contains a transport-confounded component. Mobile sensing should seek complementary observations whose source-discriminative component cannot be explained by shared admissible transport variation.

V5 transport-orthogonal sequential identification is one concrete implementation of this thesis, not the thesis itself.

## 6. Why the planned toy test is only a unit test

A PMFS-like drift-diffusion toy is useful only to test the mechanism:
- can two individually confounded measurements become jointly source-identifying?
- does transport-orthogonal acquisition beat nominal variance under controlled mismatch?
- does the gain disappear under destructive nulls?

It is NOT:
- the remote-field parent idea;
- the paper's main novelty;
- evidence of real-House benefit;
- a replacement for repaired Native tests.

Any toy result must be labeled \`MECHANISM_UNIT_TEST\`.

## 7. Revised next empirical order

1. Keep toy only as a fast mechanism kill test.
2. Ask baseline recovery to proceed to a hit-bearing case / R2-R3 when available.
3. On recovered Native candidate maps, estimate source-blind transport sensitivity.
4. Measure whether high native \`varianceOfHitProb\` is actually transport-confounded.
5. Only if that diagnostic is positive, run the equal-budget truth-rank intervention.
6. Do not build a full closed-loop new method before this gate.

## 8. Current status

\`KEEP — MAIN THESIS CANDIDATE: ACTIVE SOURCE/TRANSPORT DECONFOUNDING\`

\`IMPLEMENTATION CANDIDATE: TRANSPORT-ORTHOGONAL SEQUENTIAL IDENTIFICATION (V5)\`

\`TOY STATUS: MECHANISM UNIT TEST ONLY, NOT NOVELTY\`
