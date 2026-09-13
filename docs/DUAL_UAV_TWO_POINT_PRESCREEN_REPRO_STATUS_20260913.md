# Uploaded two-point pre-screen reproduction status

Date: 2026-09-13

The supplied ZIP was verified against its internal SHA-256 manifest. It
contains the findings, theory, execution contract, gate JSON, and reproduction
script. It does not contain the authoritative `FEATURES.csv` or
`V3_SELECTIONS.csv` inputs quoted by the findings, and neither input exists in
the current checkout or the supplied attachment directory.

Therefore the numerical route-pair pre-screen was not independently rerun in
this task. Its values remain external development claims. The reproduction
script is preserved at `tools/reproduce_uploaded_two_point_prescreen.py` for a
later input-bound check.

This does not block the primary raw-cache premise audit because the full R3B
cache is independently present. The following distinction remains frozen:

```text
VIRTUAL_ROUTE_PAIR != SYNCHRONIZED_DUAL_RECEIVER
```
