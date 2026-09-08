# CORE-M1E H01 seed8 early-screen result

Status: **H01_SEED8_NO_GO; NO_H02_H03_EXPANSION**.

Both paired arms used algorithm binary SHA256
`2a92c82e7cb2d3bab043a95ed18eb394c41ca3edc934ade8dd5f99de43f47400`
and reached the frozen 240 s horizon in the certified H01 environment.

| Arm | Final error (m) | Distance AUC (m s) |
|---|---:|---:|
| A0 | 6.7250947949 | 1709.4879314268 |
| M1E | 7.1861603099 | 1640.6545809703 |

M1E improves distance AUC by `+68.8333504566 m s`, but worsens final error by
`-0.4610655151 m`.  The preregistered one-world screen requires both metrics to
improve, so the result is NO-GO.  H02 and H03 seed8 were deliberately not run.

This negative result is retained because it falsifies multi-seed stability of
the current M1E implementation.  Together with the seed9 results, it indicates
that transport-member marginalization makes integrated trajectory error more
consistent, but does not make the terminal estimate reliable.  The next
revision must address a structural timing mismatch rather than tune planner
weights or expand the failed seed.

The environment still fixes sensor/replay seed12.  Algorithm seed8 therefore
does not constitute an independent plume realization.
