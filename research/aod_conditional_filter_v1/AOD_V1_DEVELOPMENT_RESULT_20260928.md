# AOD v1 joint-calibration development result

Decision: **`AOD_V1_DEV_SCREEN_FAIL_STOP_BEFORE_PLANNER`**.

The older three-House VGR comparison remains unchanged: Native and the original
AOD filter each achieved 0/3 geometric successes. This follow-up used no new
plume, template, neural network, or closed-loop run. The eight dev episodes and
the H02 run were already OPEN; they are development diagnostics.

The prefit contract was committed as `bb947d6b5f6ee19f774e4b8be45e6a6f3408d3f4`
before fitting. Its SHA256 is
`844726f875424ac03214b30d12ff7be307e541c419d7313d1da07dc1e768b7f9`.
The four fixed optimizer starts converged to essentially the same train
objective. All 40 original train episodes, including all-zero episodes, were
retained. The model remains the original two-state positive-gain plus
event-correlated discrepancy family; only calibration changed.

| Metric | Original parameters | Joint train likelihood fit |
|---|---:|---:|
| Train equal-environment negative log density/event | 1.3224 | 1.0174 |
| Eight-dev true-source log density/event | -1.0875 | -0.6440 |
| Eight-dev mean true-source posterior NLL | 9.9276 | 9.8321 |
| Eight-dev mean true-source rank / 596 | 567.375 | 565.250 |

The uniform candidate prior gives dev NLL `log(596)=6.3902`. Thus improved
predictive density did **not** make the source posterior reliable. The new
parameters also hit both prespecified lower bounds: gain envelope mean
`0.005` and white observation standard deviation `0.020`; discrepancy
variance `3.7423`, correlation time `54.29 s`, gain variance `0.1590`.
This is a fit-at-the-boundary warning, not a reason to move the bounds after
seeing results. Dev standardized innovations have mean per-case RMS `0.301`
and mean lag-one correlation `0.240`, further limiting a calibration claim.

The independently computed old-model dev ranks exactly match the frozen
`OPEN_DEV_CHECK.json`; maximum old NLL difference is below `1.6e-14`.

H02 post-screen explanation was computed only after the failed dev decision.
For the historical wrong source `pmfs_6_36` versus truth `pmfs_2_37`, its
odds dropped from `489:1` to `35:1`, but the truth still ranks 27th on that
same observed path. The old odds split reproduces the supplied independent
review (shape `+0.1094`, gain prior `+7.3247`, determinant `-1.2419` nats).
The new split is shape `+0.3156`, gain prior `+4.5819`, determinant `-1.3373`
nats. Neither the H02 case nor the eight dev episodes selected parameters.

The prefit dev screen required new NLL to beat both old AOD and uniform
support, with a better mean truth rank. The uniform comparison failed.
Therefore no conditional-prediction planner was connected and none of the
proposed six additional VGR development runs was started. The existing
decision core remains a mathematical reference, not a deployed policy.
