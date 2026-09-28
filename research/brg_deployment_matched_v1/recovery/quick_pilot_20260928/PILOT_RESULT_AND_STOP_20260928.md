# BRG V1 Native-only three-case development pilot

The frozen ordinals 009, 021, and 065 each completed four 300 s VGR runs
under the same original plume, start, Native legal candidate support, sensor
contract, and geometric endpoint. The three learned models used the fresh
Native-only ten-epoch weights chosen by the original eight-episode dev
source-update NLL; all three selected epoch 1. This is a development pilot,
not the original full V1 campaign or a confirmatory science gate.

| Case | Native error m | GRU error m | BRG error m | Ungated error m |
| --- | ---: | ---: | ---: | ---: |
| 009 H01 | 6.0824 | 10.7806 | 10.2609 | 10.3788 |
| 021 H01 | 6.5225 | 11.6927 | 10.2284 | 10.2282 |
| 065 H02 | 1.4037 | 10.6144 | 10.7336 | 10.7336 |

All 12 finished by the 300 s time budget, with finite source estimates, no
algorithm declaration, no wrong declaration, and geometric success 0 under
the frozen 0.5 m rule. Finite-error medians are Native 6.0824 m, GRU
10.7806 m, BRG 10.2609 m, and ungated 10.3788 m. No trained arm improves
Native geometric success or terminal source error in these three cases.

The separately verified navigation audit reports that every one of the 12
runs sent five goals and every sent goal was `(0,0)`. Each learned sidecar
received one RESET and 25–30 successful STEP messages; the training and fixed
coverage switches were false. Thus the inference services operated, but
this pilot did not exhibit policy-dependent navigation. The equal path
lengths across arms within each case are consistent with the raw goal logs.
These runs do not establish an active-search benefit or a BRG architecture
advantage; the three cases also cannot establish a population success rate.

The initial 009 learned-arm attempts failed before model observations at the
TCP RESET token check. Their three raw archives are preserved. A documented
identity-token infrastructure patch enabled the 12 effective runs without
altering the case, weights, plume, navigation algorithm, or scoring contract.
The valid Native 009 run was reused. Total VGR executions were 15, of which
three were recorded infrastructure failures and 12 are the frozen pilot
comparison. No new GADEN plume, candidate forward, coverage trajectory, or
self-rollout was generated in this pilot.

The campaign stops here as requested. The remaining coverage, self-rollout,
and original 32-run campaign are not resumed. Any further algorithm or
navigation change would require a separately frozen development version;
these three inspected cases must be treated as development evidence.

Evidence: `BRG_V1_PILOT_3CASE_SUMMARY.json`,
`BRG_V1_PILOT_3CASE_RUNS.csv`,
`BRG_V1_PILOT_NAVIGATION_AUDIT.json`, and all original VGR raw log archives.
Navigation audit SHA256:
`2daa663e88a250e4dbe25bf222fd52f15b1b8e3e0d3827b79da8fa7d483e9800`.
