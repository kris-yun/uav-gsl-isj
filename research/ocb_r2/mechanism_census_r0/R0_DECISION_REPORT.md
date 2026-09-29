# OCB-R2 source-information mechanism census R0

**Frozen mechanism label: `OCB_R2_MECH_CROSS_TIME_STABLE`.** This is a discovery-only mechanism result, not a localization method, confirmation result, or closed-loop result. The full spatial marginal already discriminated the two configured sources in all 64 targets, so the cross-time increment is **margin enlargement**, with no localization rescue demonstrated.

## Inputs and execution

- Base protocol: `OCB_R2_SOURCE_INFORMATION_MECHANISM_CENSUS_R0.md`, commit `85cd41cb136be08e440d26f8cf8f36a5d35b852c`. The operational choices and scorer were committed at `1e9aef6a18c243e5e0275c7b4ae788db3cb4b66f` before scoring.
- Metadata-only D0A re-audit: `OCB_R2_D0A_SOURCE_COMPARABILITY_PASS` across 8/8 fixed H01/H02 House–wind–gas–occupancy–generator–timeline contexts; each had two original configured sources and four independent realizations per source.
- Data: 64 SHA-checked AOD-R2 F0 discovery tensors using the already-frozen E1 30 probes, `50:50:500 s` time mapping, native concentration extractor, and strict `concentration > 0` encounter definition. H01/H02 confirmation and H03 remained sealed. No new GADEN, PMFS forward, neural model, or closed loop.
- Scores: equal K=3 truth and alternative references in every held-out case; complete 300D marginal scores and full-trajectory fair-U Energy Score. C1 and C2 used 1,000 surrogates per candidate/reference view, and all 320,000 banks in each intervention passed binary and marginal preservation checks. All C2 banks also passed whole-snapshot multiset preservation.

## Layer results

| Layer | House01 median group margin/effect | House02 median group margin/effect | Positive groups | Positive contexts |
| --- | ---: | ---: | ---: | ---: |
| M-TIME margin | 0.02404 | 0.04274 | 16/16 | 8/8 |
| M-SPACE margin | 0.13520 | 0.17552 | 16/16 | 8/8 |
| M-FULL margin | 0.19852 | 0.23889 | 16/16 | 8/8 |
| I_SPATIAL = C2−C1 | 0.00699 | 0.00664 | 15/16 | 8/8 |
| **I_CROSS = RAW−C2** | **0.03414** | **0.04158** | **16/16** | **8/8** |

M-FULL truth-vs-alternative margins were positive in **64/64** held-out targets. The pooled median source×context **I_CROSS** effect was **+0.03838** Energy Score units. Its eight leave-one-context-out medians were all positive (range `+0.03414` to `+0.04158`); the largest context accounted for 29.4% of the sum of absolute context effects, below the frozen 40% cap. The 10,000-draw source-label sign-flip reference was `0.00320` in the observed direction. All four alternative-source 3-of-4 omissions retained positive pooled and both-House medians (pooled medians `+0.02998` to `+0.05348`). Every frozen CROSS_TIME gate condition passed.

I_SPATIAL also met its analogous directional checks: pooled median `+0.00664`, 15/16 positive groups, 8/8 positive contexts, and sign-flip reference `0.00320`. The protocol assigns one label and gives CROSS_TIME precedence when its gate passes. **The evidence does not say spatial joint structure is absent.** It says the additional intact cross-time pairing effect remains after each-time spatial snapshot structure is preserved.

The source-label randomization value is a reference for these eight contexts, not a universal p-value. The same physical source positions recur under several winds/gases, and there are only two configured sources per House. These data cannot establish arbitrary-source, unseen-House, calibrated posterior, or full-map benefits.

## Verification and stop

Two complete scoring passes produced nine byte-identical scientific files. An independent implementation recomputed all 64 primary M-TIME/M-SPACE/M-FULL and RAW fair-U margins from the frozen tensors; maximum RAW difference was `2.67e−15` and marginal differences were zero. The bottom quartile by M-FULL margin was reported only descriptively and did not enter the gate.

**STOP.** No paper search, theory selection, method construction, confirmation/H03 opening, or closed-loop evaluation follows from this run automatically. The result licenses a later human decision about a path-space dependence hypothesis and an untouched confirmation test.
