# HCMC V1 discovery replay with linked-native endpoint

Verdict: `HCMC_V1_DISCOVERY_REPLAY_ONLY`

The frozen six discovery cases reproduce Native mean error `5.55506029235827 m`. The authoritative linked C++ endpoint gives HCMC errors:

`[2.0435386068169326, 2.181015472391614, 1.235953832436307, 3.085178347552927, 1.2979341409527343, 4.745835038249523] m`

The HCMC mean is `2.431575906400006 m`, a `56.227731501943104%` reduction, with `6/6` non-worse. All Native logged-endpoint parity deltas pass the frozen `0.011 m` tolerance, and all three 1500-row trace-integrity checks pass in all cases.

The prompt's approximate HCMC mean `2.42308 m` is produced by a Python stable tie-break at the top-5% cutoff. The linked native C++ function compares probability only with `std::sort`; rank-derived HCMC posteriors contain equal-probability cutoff ties, so native tie ordering selects a slightly different boundary subset. The linked-native values above are authoritative. No HCMC definition or endpoint implementation was changed to force the approximate Python values.

Controls on discovery replay remain decisively worse than real HCMC: random-leaf pooled mean `4.481822177829603 m` and spatial-shuffle pooled mean `4.953219877466213 m`; the fraction of null replicates as good as real HCMC is zero for both families. These results are only a replay/parity qualification and are not independent evidence.
