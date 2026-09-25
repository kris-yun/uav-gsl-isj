# DATA ADAPTER CHECKLIST

Codex should write a repo-local adapter, not edit old data.

Required adapter behavior:

1. Locate authoritative R0 arrays from the R0 PASS evidence.
2. Verify source and realization IDs.
3. Recover explicit 10×30 ordering from metadata/code that produced R0.
4. Export canonical_r0.npz without changing values.
5. Emit before/after hashes and equality checks.

Required assertions:

```python
assert X.shape == (18,16,10,30)
assert np.isfinite(X).all()
assert len(np.unique(source_ids)) == 18
for s in range(18):
    assert len(set(realization_ids[s].tolist())) == 16
```

Do not use the above shape assertion to FORCE a reshape.
Only run it after provenance has independently established the shape.

If the source observable is boolean/uint8, preserve that in cache and cast only inside analysis.

If R0 used a mask/support definition, preserve it exactly.
