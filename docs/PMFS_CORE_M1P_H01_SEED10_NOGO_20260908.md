# CORE-M1P H01 seed10 early-screen result

Status: **M1P_NO_GO; NO_H02_H03_EXPANSION**.

M1P corrected the causal-unit mismatch exactly: the four source-update windows
committed 4, 3, 3 and 3 physical-stop events instead of M1S's 32, 24, 24 and
24 internal measurement-block events.  Both A0 and M1P used binary SHA256
`6265de98c58e30431353b05debe956a4ee71b2ae54a8a0a6c98f17996a91ebf6`
and reached the frozen 240 s horizon.

| Metric | A0 minus M1P | Direction |
|---|---:|---|
| final error | +0.3729809659 m | improved |
| distance AUC | -339.9727793236 m s | worsened |

The early gate requires both metrics to improve and therefore returns NO-GO.
H02/H03 were not launched.  The terminal-only physical-stop observation loses
too much within-stop temporal information for useful early navigation; this
version remains preserved and is not rescue-tuned.

This negative does not revoke the frozen M1S House123 seed11 majority PASS.
The next experiment is a second algorithm-seed test of unchanged M1S, not a
new M1P variant.
