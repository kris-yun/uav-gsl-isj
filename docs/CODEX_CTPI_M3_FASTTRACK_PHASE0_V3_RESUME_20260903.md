# Codex — CTPI M3 fast-track Phase 0 V3 resume

Use repository `kris-yun/uav-gsl-isj`, branch `research/ctpi-m3-fasttrack-20260903`, and the exact final V3 HEAD supplied by ChatGPT.

The previous authoritative heads `998beb23553ec4153536a4925c155a3ed0ba6769` and `7e1c3f29a700179a991cdcd3bc9b90f140b74795` are superseded.

## V3 patch packaging contract

The checked-in file `patches/CTPI_M3_FASTTRACK_RUNTIME_INTEGRATION_20260903.patch` is the byte-identical V2 source body with SHA-256:

`a054a28c593f095956469e87713350e89baf3f30c94a9d23e8708b63379f4713`

It intentionally remains unchanged because its scientific hunk content is frozen. The V2 failure established that this source body lacks only the final LF required by `git apply`.

Do **not** run `git apply` directly on that source file and do not edit it locally.

`tools/ctpi_m3_runtime_patch_materializer.py` must append exactly one LF into a fresh temporary file and must verify the resulting complete patch SHA-256 is exactly:

`96e1e425a7c4e6e97ad123c1d46e67120dc86574b3d3927a370e5b99d1020743`

No hunk content may change.

## Restart Phase 0

Create a fresh clean checkout/worktree at the exact V3 HEAD and run only:

```bash
python3 tools/ctpi_m3_fasttrack_handoff_check.py \
  --repo-root "$PWD" \
  --output /tmp/CTPI_M3_FASTTRACK_HANDOFF_CHECK_V3.json
```

Required terminal line:

`CTPI_M3_FASTTRACK_CODEX_HANDOFF=PASS`

The V3 checker itself materializes the complete temporary patch and runs `git apply --check` on that temporary patch. If any check fails, stop and return the exact failed checks. Do not build, access banks, or run smoke.

## After Phase 0 PASS only

Continue with `docs/CODEX_CTPI_M3_FASTTRACK_TRUE_CLOSED_LOOP_FROM_HANDOFF_20260903.md` beginning at Phase 1.

`closed_loop/ctpi/prepare_ctpi_m3_fasttrack_vm_20260903.sh` calls the frozen applicator, which again materializes and verifies the same complete temporary patch before applying it.

Do not change M1, TSDC, PIP, action domain, tie-break, 3/3/1 cadence, 240 s horizon, banks, or any Gate.
