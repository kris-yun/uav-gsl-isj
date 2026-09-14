# Observability-aware learning falsification — final result

The first candidate main-innovation route was tested using only the committed C2 ordered plus/minus processed traces. The teacher label had non-zero variation in all three rich targets, so the failure is not caused by a constant-label dataset.

Frozen split:

- train: `W_fast`, `AO_00`–`AO_07`;
- development: `W_fast`, `AO_08`–`AO_11`;
- held: `W_slow`, `AO_08`–`AO_11`.

The full standardized Ridge model failed the promotion gate:

- held rich error was 54.4% worse than the constant predictor;
- held rich error was 73.8% worse than gas-only;
- development rich error was 64.6% worse than constant;
- time reversal degraded performance strongly, but wind reversal degraded only 1.2%;
- zeroing motion improved performance rather than degrading it.

Therefore temporal order was being used without transferable physical conditioning. The candidate is rejected as a main innovation:

`OBSERVABILITY_AWARE_LEARNING_FALSIFICATION = NO_GO`  
`MAIN_INNOVATION_STATUS = NOT_CONFIRMED`  
`MAIN_INNOVATION_CLAIM = NOT_AUTHORIZED`

This result does not justify tuning the split, labels, windows, model, or controls after inspection. The next mechanism must address the upstream sensing-support failure exposed by C0–C3: source information is not sufficiently supported within the fixed 150 s measurement horizon.
