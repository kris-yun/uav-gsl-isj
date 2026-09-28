# AEC-D0 self-competence predictability audit

Decision: **`AEC_D0_NO_CROSS_HOUSE_PREDICTIVE_SIGNAL`**. Stop the proposed self-competence routing mechanism at D0. This result does not reverse House03's frozen AOD result or test a different adaptive-coding method.

## Frozen calculation

The simulator-only `Top10` competence calculation was specified and committed before reading the existing target outcomes. It scored each of 88 source-conditioned PMFS members against the complete archived legal bank, excluded that member from its own source's mean template, and compared `rawu-ABS` with `u-ABS`. The units for the final comparison are physical source: four in House01, five in House02, and twelve in House03. H02 winds and all repeated routes were aggregated within source; House03's eight realizations and two paths were likewise aggregated within source.

The H01/H02 truth-source products were deterministically replayed from the frozen PMFS binary, input files, wind states, and seeds. Every product SHA256 matched its original forward inventory. This was 1,144 PMFS replay calls, **zero new GADEN plumes**, and no new independent samples. H03 reused its existing candidate archive. The first pseudo-`u` attempt stopped because C++ per-run `u` did not match the OpenCV-reconstructed `u` used by the archived B2 mean bank on some low-signal cells. The corrected run used the original B2 OpenCV observation operator on each per-run `rawu`; the first output was preserved and the repair recorded separately. All final self-mean parity checks passed before target outcomes were read.

The simulator-only table and SHA256 were committed as `11b21679987b121925afa94503d783adefa64186`. Only then was `Delta_G = mean truth rank(u-ABS) - mean truth rank(rawu-ABS)` obtained from the earlier frozen R0.75 and House03 F1 outcomes. Positive `Delta_G` means rawu improves rank.

## Physical-source results

| House | Sources | Spearman(Delta_C, Delta_G) | Nonzero sign agreement | Fixed u mean rank | Fixed rawu mean rank | Source-aware competence selector mean rank |
|---|---:|---:|---:|---:|---:|---:|
| House01 | 4 | −0.20 | 3/4 | 242.00 | 231.56 | 230.50 |
| House02 | 5 | **−0.80** | **1/5** | 75.30 | 75.75 | **78.90** |
| House03 | 12 | +0.13 | 7/12 | 115.46 | 116.43 | 114.90 |

The House02 direction is strongly opposite the proposed competence prediction. Its source-aware selector is worse than both fixed encodings. House01 has only four sources and a negative rank association despite 3/4 sign agreement. House03's association is weak; simulator competence favors rawu for only 2/12 sources while the archived rawu ABS arm gains unique Top1 on 11 target paths and harms one. The competence selector would keep eight of those 11 rescues and avoid the one harm, but also discard three rescues; it therefore does not beat always-rawu on House03 unique Top1.

The source-aware selector is **only a diagnostic**: it selects an encoding using the physical source ID and is not an online `sum_s q_t(s) C_e(s)` router. Its small rank improvement in H01/H03 cannot rescue the failed cross-House association or the House02 reversal. There was no trained gate, fusion weight, posterior update, planner, or closed-loop run.

## Integrity and limits

The final simulator-only output has 146 route/operator rows and 21 source rows. It passed archived bank hashes and the source-mean parity gate. Both competence scoring and source-level outcome joining were repeated, with six output files byte-identical. Detailed source-level values, route values, input hashes, pseudo vectors, and deterministic-repeat hashes are in `evidence/aec_d0/`.

The old target outcomes had already been inspected in prior R0.75/R1 work, so AEC-D0 is an OPEN development audit, not a fresh confirmation. H01/H02 Native paths are action-dependent. In particular, this experiment cannot justify a main-innovation claim about adaptive sensory coding. The concrete self-competence estimator proposed here fails its cross-House predictive gate. Do not tune TopK, add CENTERED, fit routing weights, or start a closed-loop AEC campaign on these outcomes.
