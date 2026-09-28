# AEC-D0 self-competence predictability audit

Status: read-only development audit, frozen before target outcomes are loaded by the AEC evaluator.

## Scope and claim boundary

The only question is whether simulator-only source-specific encoding competence predicts the observed `rawu` versus `u` ABS-B2 advantage. Encodings are exactly `u-ABS` and `rawu-ABS`. No CENTERED, posterior fusion, routing weight, network, GADEN, VGR, or closed loop. These H01/H02 and House03 outcomes have already been used in earlier research; this is **not fresh confirmation** and cannot by itself establish a main innovation.

## Source and observation units

- H01: the four physical truth sources in frozen DS-PMFS D1 env 0, final completed Native route per episode; legal 596-source bank.
- H02: the physical truth sources across frozen D1 env 1 and 2; legal 630-source bank per wind. Aggregate episodes and winds within a physical source before House-level association.
- H03: 12 frozen F1 truth sources, eight realizations and two paths each; full 624-source bank. Nominal 11-state condition is primary; state0 is diagnostic only.
- Real target truth is used only after all simulator competence values and hashes are frozen. A route's visited positions are permitted in simulator competence, but H01/H02 routes arose from Native target-dependent action; this is a selection limitation, not a source-blind held-out design.

## Simulator-only competence

For each physical source and each frozen route, use 88 PMFS forward products from the frozen 11 wind states and eight transport seeds. Project each one through the same archived physical 0.20 m footprint (H01/H02) or frozen F1 path operator (H03), with the same `EPS=1e-9` and nonnegative gain-profile SSE as the original ABS-B2 arm.

Score each projected product as a pseudo-observation against the complete legal candidate mean bank. The self candidate's mean template excludes that exact realization; all other candidate means stay fixed. The self-exclusion is `m_s^(-k) = (88*m_s - x_{s,k})/87`, with the 88-product mean verified against the archived mean bank. If parity fails, stop that environment rather than substituting a mismatched six-source bank. No real target concentration is an input to this stage.

Use average rank for exact SSE ties, as in the archived House03 F1 evaluator. Primary competence is `C_e(s) = mean_k 1{rank_e(s|x_{s,k}) <= 10}`. The prespecified `TopK` is 10 for each full support. Secondary values: mean pseudo rank and mean reciprocal rank. Average routes/episodes first within each physical source, then any H02 winds within the same source. `Delta_C = C_rawu - C_u`. Zero Delta_C means abstain; do not break ties from target data.

## Target outcome and association

After simulator competence CSV and its SHA256 are committed, read frozen original ABS-B2 final-route outcomes from R0.75 for H01/H02 and the original nominal F1 ABS-B2 target metrics for H03. Recompute or verify the original scores; do not use CENTERED outcomes. `Delta_G(s)=mean_truth_rank_u - mean_truth_rank_rawu`, with positive indicating rawu improves rank. Also report paired Top1 rescue/harm counts and source-mean Top1 difference. Aggregate by physical source before calculating within-House Spearman association and nonzero-sign agreement. Do not treat episodes, realizations, paths, wind repeats, or pseudo-realizations as independent source samples.

Report all source rows, including abstentions and harmed sources. Compare a competence-sign selector's *source-level descriptive* rank gain with always-u and always-rawu; this selector knows the source index and is **not an online router**. A deployable `sum_s q_t(s)C_e(s)` rule is not evaluated here.

AEC-D0 can be called an OPEN predictive signal only if all three Houses have nonconstant Delta_C and a positive association with Delta_G, sign agreement above 1/2 among nonzero predictions, and competence-sign source-level rank gain exceeds both fixed encodings in each House. Otherwise label `AEC_D0_NO_CROSS_HOUSE_PREDICTIVE_SIGNAL` or `AEC_D0_INCONCLUSIVE_ASSET_OR_SAMPLE`. Regardless of outcome, a future untouched environment and an online q-weighted rule would be required for main-innovation promotion.

## Asset integrity

The H01 corrected Native legal mean bank was rebuilt after the original six-source bank. Its old per-realization outputs cannot be mixed into the corrected legal bank. Reproduce only the needed H01 physical-source PMFS forwards from the frozen corrected input/binary and verify their 88-run mean against the archived bank before scoring. H02 truth-source PMFS forwards can likewise be reproduced from frozen full-support inputs to enforce exact self-exclusion. These are deterministic PMFS replays, not new GADEN plumes or independent samples. H03 reuses the existing 54,912-row candidate archive. Record executable, input, bank, route, pseudo-vector, and outcome hashes. Stop on a parity failure.
