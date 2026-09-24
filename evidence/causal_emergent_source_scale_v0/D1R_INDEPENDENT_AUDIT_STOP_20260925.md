# D1R Independent Audit and Frozen IF-CV Decision — 2026-09-25

## Decision

**D1R_STOP_FSEI_NOT_DISTINCT_FROM_ORDINARY_POOLING**

This STOP is triggered before any D1C target generation.

The reason is not a post-result threshold change. Under the already frozen
IF-CV V1 contract, the strong fidelity certificate cannot admit any nontrivial
macro group at R=16, so the primary candidate collapses to the identity
partition and therefore cannot satisfy the required candidate > identity
reference prerequisite.

No final targets are authorized.

## 1. Independent package audit

Uploaded review package:

- archive SHA256:
  `8a784426654363a4d5c7faaae3723742ce24c54c364a1779212c1efb83cc82e5`
- archive bytes: 1,204,078
- Codex result commit:
  `3da623665c3b84b4edecb7c22887ff99156cfb48`

Independent checks:

- archive SHA matches reported SHA;
- all packaged files pass internal `SHA256SUMS.txt`;
- reference tensor shape is exactly `(168,16,10,30)`;
- dtype is float64;
- all entries finite and nonnegative;
- artifact inventory has exactly 2,688 rows;
- 168 unique sources;
- 16 replicates/source;
- 2,688 unique RNG seeds;
- zero duplicated source/replicate pairs;
- all seeds satisfy
  `2026105000 + 16*panel_index + replicate`;
- panel is the complete PMFS rectangle
  `i=1..24, j=12..18` = 168 source cells;
- packaged source-bank SHA256:
  `0e835c3a3d0f4651f9c4aa87b28a34892589cfb073a73daf6a84896d081824fb`;
- packaged Gate1A observation-contract SHA256:
  `68121bc9225646e37fcf0233e769b694d9dbaec382723f45b8e80ffc73cea334`.

The review package contains the 168x16x10x30 pooled reference tensor and the
artifact hash inventory, not all 2,688 extracted concentration cubes
themselves. Therefore the package independently verifies the inventory
structure and pooled data, but cannot re-hash VM-only cubes absent from the
archive.

## 2. Independently reproduced bank-quality metrics

From the packaged tensor:

- first8 vs last8 encounter-profile cosine:
  - median = **0.9886273717**
  - q10 = **0.9763982541**
- raw mean-profile relative L2:
  - median = **0.1226995407**
  - q75 = **0.2217023777**
  - q90 = **0.4089129724**
- per-source median total observed mass range:
  **43.0931 to 941.9911**
- per-source median zero-fraction range:
  **0.66333 to 0.87**

Thus D1R is a valid high-quality development/reference bank.

This is not a scientific PASS for the FSEI hypothesis.

## 3. Strong IF-CV certificate is underpowered by construction

Frozen IF-CV V1 required:

- simultaneous encounter-channel fidelity tolerance
  `epsilon_enc = 0.15`;
- simultaneous mark-channel tolerance
  `epsilon_mark = 0.20`;
- 168 sources;
- 300 registered queries;
- Bonferroni/Clopper-Pearson encounter uncertainty;
- DKW mark uncertainty;
- R=16 final reference realizations/source.

For the encounter channel, with nominal binary certificate error 0.025:

[
\alpha_{cell}=0.025/(168\times300).
]

At R=16, the **narrowest possible** two-sided Clopper-Pearson interval over
all hit counts 0..16 has width:

[
0.6134951328.
]

Therefore even the most favorable possible source-query count cannot support
a simultaneous pairwise TV upper bound <=0.15.

This is data-independent.

Minimum realization counts merely to make the narrowest simultaneous binary
interval width no larger than the requested tolerance are approximately:

- width <=0.20: **69 realizations/source**;
- width <=0.15: **94 realizations/source**.

For the mark-channel DKW construction,

[
\zeta_R=
\sqrt{\log(2Nd/0.025)/(2R)}.
]

At R=16:

[
\zeta_{16}=0.689424.
]

To obtain `zeta <= 0.20` requires approximately **191 realizations/source**;
for `zeta <= 0.15`, approximately **338/source**.

These are distribution-free worst-case scaling diagnostics, not a claim that
all such sample counts would be sufficient for the full plume problem.

They show that the frozen strong certificate is fundamentally mismatched to a
16-realization development budget.

Thresholds are not relaxed after seeing D1R.

## 4. Consequence for frozen IF-CV

Under the frozen IF-CV eligibility rule, no nontrivial group can satisfy the
encounter strong certificate at R=16.

Therefore the only admissible strong-claim partition is identity:

[
K=168.
]

Frozen D1R ADVANCE required:

1. nontrivial `1 < K < 168`;
2. non-vacuous fidelity constraints;
3. candidate reference OOF score > identity;
4. candidate > locked ordinary champion.

Conditions 1 and 2 are impossible, and condition 3 cannot hold when the
candidate itself collapses to identity.

Therefore:

**D1R_ADVANCE_IFCV_STRONG_MAINLINE is impossible under the frozen V1 contract.**

## 5. Secondary predictive screen

As a non-decision diagnostic, the packaged raw data were also screened under
the preregistered common working family:

- zero-hurdle + log-amplitude Student-t;
- source-stratified nested 4-fold reference CV;
- same 168-cell micro proper score;
- eta grid {0.5,1,2};
- inverse-temperature grid
  {0,1/300,1/100,1/30,1/10,1/3,1/2,1,2};
- connected hard-pooling cuts over a coarse preregistered subset
  K={168,96,60,36,21,14,7,1}.

Results:

### Geometry-connected hard pooling
Selected K=168 in all four outer folds.

Outer-fold mean true-source log2 scores:
- -3.2304316
- -3.1117856
- -3.1995095
- -3.2415469

### Encounter-profile connected hard pooling
Selected K=168 in all four outer folds, with the same identity scores.

This screen is not the complete ordinary-baseline portfolio and is not used
to claim that every pooling/shrinkage method fails.

It does show that there is no obvious hard-pooling signal hidden behind the
strong-certificate failure.

## 6. Scientific interpretation

D1R itself succeeded as a benchmark asset.

The strong FSEI/causal-emergence-inspired mainline did not.

The failure mechanism is informative:

> a distribution-free, source-level equivalence certificate strong enough to
> justify physical/statistical source macrostates requires far more repeated
> realizations than are practical for the intended GSL and sim-to-real use
> case.

Increasing the bank to tens or hundreds of realizations/source merely to make
the equivalence certificate non-vacuous would move the method away from the
deployment requirement that a new real environment must not need an exhaustive
per-source repeated-release bank.

Therefore the correct action is STOP the strong FSEI mainline rather than
increase R or loosen epsilon after seeing D1R.

## 7. What remains reusable

Retain:

- the 168x16 D1R reference bank as a high-quality benchmark;
- R0/D1R evidence that encounter/support profiles are highly reproducible;
- same-prior microcell proper-score discipline;
- uncertainty-preserving macro-to-micro lifting;
- the fixed-panel fresh-target firewall;
- strong ordinary pooling/shrinkage baselines for future routes.

Do not promote:

- source equivalence macrostates;
- causal emergence;
- IF-CV strong certificate;
- D1C final targets.

## 8. Next route requirement

The next main innovation must not require exhaustive source-wise equivalence
certification in every environment.

It should exploit a transferable scientific object learnable from finite
observations and later admit limited real calibration rather than a full
source bank.
