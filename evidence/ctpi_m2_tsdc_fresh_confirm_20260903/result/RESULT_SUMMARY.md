# CTPI M2 TSDC V0 fresh-confirm result

Terminal result: `CTPI_M2_TSDC_FRESH_CONFIRM=PASS`.

This is the first confirmatory result for TSDC V0. The prior 60 worlds remained
`DEV_SPENT`; the Gate used exactly 30 newly generated worlds, 10 per House, and
450 events. The predictive bank was read-only and was not regenerated.

## Frozen boundary

- frozen module SHA-256: `854a2fc8513201cdb2ae497a62c0cd3c5fa09fdae2f1bc309ad594a8b1aaacf7`
- fresh selection SHA-256: `0d4e6162863ca2a07bf93ef74f178b1d4ad5d058ab787345d291362fd8e9f431`
- fresh world manifest SHA-256: `f90303ee64c3dbe9d2b54e122d04c9341d5f2532b636fd63f9a1f7bb629257b2`
- pregen authorization SHA-256: `6323cfd12e07c6a276b410e879f136816b0af1f2d218b51b6f5dc71df93ea6fd`
- frozen one-shot evaluator SHA-256: `991fa2c04b4c02a6a073402b504a7108a01e7b066befe1f4582eeebd52980d36`
- Gate report SHA-256: `fff3898d7f922ccf48ce986eaf1cec64843100e2bff2d1f9874e12405632671d`

## Confirmatory metrics

- NLL: `0.300436 -> 0.182094` (39.39% lower); world wins/losses `27/3`,
  one-sided exact sign `p=4.215e-6`.
- Brier: `0.090933 -> 0.053068` (41.64% lower); world wins/losses `24/6`,
  one-sided exact sign `p=7.155e-4`.
- ECE-5: `0.035802 -> 0.034575`.
- H01 NLL wins: `8/10`; mean NLL `0.289132 -> 0.197841`.
- H02 NLL wins: `9/10`; mean NLL `0.231224 -> 0.108663`.
- H03 NLL wins: `10/10`; mean NLL `0.380954 -> 0.239777`.

Every preregistered conjunctive Gate criterion passed. An independent post-Gate
recomputation verified the causal previous-dwell decision state, frozen formula,
pooled metrics, world win counts, and all 30 generation audits.

## Authorization boundary

This result qualifies M2's direct fresh predictive Gate and authorizes only the
M3 offline action Gate. It does not yet prove M2's independent downstream robot
localization increment. C++, ROS, smoke closed-loop, and formal closed-loop
remain unauthorized until M3 and the factorial downstream comparisons pass.
