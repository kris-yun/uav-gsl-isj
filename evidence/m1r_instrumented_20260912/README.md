# M1R V4.1 instrumented development replication

Evidence label: `NEW_INSTRUMENTED_DEVELOPMENT_REPLICATION`.

This is the one permitted passive seed-12 replication for H01/H02/H03.  It
uses the historical rolling-block persistence behavior and adds attribution
logging; it does not claim byte or trajectory identity with the 8 September
binary.  All three runs reached the fixed 240 s budget with
`time_budget_timeout`.

The `RCLError: publisher's context is invalid` at the end of each launch log is
a shutdown race after SIGINT was sent at budget expiry.  Sensor, pose, wind,
navigation, source-estimate, and candidate-attribution traces were written
before shutdown.  It is retained rather than hidden.

Evaluation:

* `../m1r_mechanism/M1R_INSTRUMENTED_THREE_ARM_RESULT.json`
* `../m1r_mechanism/M1R_HISTORICAL_REPLICATION_COMPARISON.json`
* `../m1r_h03/H03_M1R_FAILURE_DECOMPOSITION.json`
