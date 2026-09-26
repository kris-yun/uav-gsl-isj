# U diagnostic amendment — user authorized 2026-09-27

If M fails its original six gates, U supports
`ME_PMFS_D0_MARK_INFORMATION_FORWARD_INADEQUATE` if and only if:

1. All three environment mean incremental paired-neighbor mark log-odds > 0.
2. U mean true-source rank <= B0 in all three environments.
3. U strictly improves mean true-source rank in at least two environments.
4. U Top-1 >= B0 in all three environments.

Otherwise the decision is `ME_PMFS_D0_NULL_OR_ADVERSE`.
The six original M gates remain unchanged.
U uses the same PMFS B0 occurrence term and the reference-only conditional
positive concentration mean for each (time, probe), followed by the supplied
profiled conditional-mark likelihood. No target tuning is allowed.
