CG-PC-CTT V3-ORR FULL 60-ARM EVIDENCE PACKAGE (2026-08-27)

STATUS
======
Frozen confirmatory verdict: CG_PC_CTT_MULTI_SEED_NOT_GO

This package preserves the complete contemporaneous closed-loop matrix:
  House01 / House02 / House03 x seeds 0..9 x PMFS OFF / V3-ORR ON
  30 matched pairs, 60 complete 300-second arms
  TIMEOUT_SEC=300, STEPS_SOURCE_UPDATE=3

PRIMARY FROZEN RESULT
=====================
Primary metric: PMFS ExpectedValue(sourceProbability, 0.05) localization error
Improved pairs: 18 / 30
Pooled relative reduction: 0.04016577825514959 (4.02%)
One-sided paired sign-test p: 0.1807973040267825
Bootstrap 95% CI: [-0.08295382896495226, 0.1446779659740934]

Per-House pooled reduction:
  House01: -6.84% (degradation), 5/10 pairs improved
  House02: +7.20%, 6/10 pairs improved
  House03: +10.03%, 7/10 pairs improved

The method therefore shows heterogeneous positive signal, strongest in House03,
but does not meet the frozen cross-House >=10% criterion or paired significance
criterion and is not established as a generalizable main innovation.

FROZEN IDENTITIES
=================
Git SHA: 172968b0d18d32e81f7059519f467f7b1ec5b6b6
Binary SHA-256: a088505d0bfd79a40652295f3f0e4b43f3a0fabf38a7de0ac5b0b3cf0e02d097
Launch SHA-256: 0cd1ae4ad852bf548fd1ebc131e7f46f0d6d20603a2e4e71ae37c6831e40f2c9

PACKAGE LAYOUT
==============
results/          all 60 raw arm outputs, case results, posteriors, trajectories,
                  traces, context exports, V3 update audits, pair logs, and the
                  preregistered aggregate verdict
analysis/         descriptive 30-pair table and mechanism-count audit
source/           frozen source bundle, integration patch, and execution protocol
freeze/           freeze manifest, hashes, dispatcher log, and self-test evidence
smoke/            House02 seed314159 infrastructure-smoke evidence
bank_verification/ preserved H02 reconstructed-bank verification metadata
tooling/          read-only descriptive summarizer used for analysis/ outputs
SHA256SUMS.txt    package-content hashes

INTERPRETATION GUARDRAIL
========================
Do not tune thresholds, seeds, planner, or scientific equations against these
confirmatory outcomes and then relabel the same matrix held-out evidence. Any next
method version must be named separately and tested on a new prospective protocol.
