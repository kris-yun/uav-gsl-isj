# CORE-M1S H01 seed10 replication result

Status: **M1S_MULTI_SEED_NO_GO; NO_H02_H03_SEED10_EXPANSION**.

M1S was kept byte-for-byte unchanged and evaluated with algorithm seed10 using
the same binary SHA256 as its paired A0,
`6265de98c58e30431353b05debe956a4ee71b2ae54a8a0a6c98f17996a91ebf6`.
The physical replay remained sensor seed12 under the existing environment
certificate.

| Metric | A0 | M1S | A0 minus M1S |
|---|---:|---:|---:|
| final error (m) | 2.6718720029 | 6.0704942138 | -3.3986222109 |
| distance AUC (m s) | 1247.0961091289 | 1590.4344067278 | -343.3382975989 |

Both metrics worsened, so the one-House early gate returns NO-GO and H02/H03
seed10 are not run.  The earlier House123 seed11 majority PASS remains valid as
a one-seed result, but M1S is not multi-seed effective.

## Next mechanism, not rescue tuning

M1S uses one stochastic PMFS transport realization per candidate.  Reversing
from a strong seed11 gain to a strong seed10 loss identifies Monte Carlo
transport nuisance as an unintegrated source of posterior variance.  M1E will
retain the same centered log-odds estimand and sequential event-time update but
marginalize the likelihood over the already-defined three native transport
replicas.  This is causal nuisance marginalization; it introduces no learned
weight, House rule or truth access.  M1E is screened on a different algorithm
seed.
