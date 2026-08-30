# CTT M2 K0 runtime parity closure

Date: 2026-08-31

The first prospective Gate attempt stopped before generating any new transport
seed because its `OMP_NUM_THREADS=1` P0 sentinel did not match the frozen
formal bank. The failed output is preserved at
`/home/zyc/CTT_M2_FIXED_U_PROSPECTIVE_K_BANK_20260831_R1`.

One fixed carrier (`quadtree_0_0_2_2`), source coordinates, seed 101, wind
context 0 and all five route schedules were regenerated across an explicit
runtime matrix. Only the historical runtime setting reproduced the frozen
formal shard:

| OMP threads | explicit `GADEN_RNG_SEED=101` | byte match |
|---:|---:|---:|
| 1 | no | no |
| 2 | no | no |
| 3 | no | no |
| 4 | no | **yes** |
| 6 | no | no |
| 8 | no | no |
| 12 | no | no |
| 1,2,3,4,6,8,12 | yes | no for every setting |

Frozen formal shard SHA-256 and reproduced OMP=4 SHA-256:

```text
6cb0dd00f8abbe396249818e0d1e010117a31a4fff238c57ed6ee57f5597f3e0
```

Conclusion: OpenMP thread count is part of the historical native stochastic
forward generator. The corrected prospective Gate freezes OMP at 4, leaves
`GADEN_RNG_SEED` unset as in the historical run, uses three concurrent
processes on the 12-core VM, and still requires 210/210 P0 byte matches before
generating any prospective realization. This is infrastructure closure, not a
scientific formula or result-driven parameter change.
