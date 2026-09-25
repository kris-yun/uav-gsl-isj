# House02 reuse diagnosis

The geometry-only E1A/E1B decision is `E1_H02_D1R_CONTRACT_ACCEPTED_AS_LEGACY_ONLY`:
the new FPS30 and legacy D1R30 pooled-index sets have **0/30 exact overlap**.
Only 21/30 legacy blocks pass the additional PMFS navigation-valid rule used by E1.

Existing House02 `(10,83,119)` concentration cubes can technically be sampled at
the new 30 blocks. The technical check successfully produced a finite 300-value
vector from one retained cube for each of `3,5-1_fast`, `3,5-1_slow`, and
`4,5-3_slow`, after the geometry decision was fixed.

This does **not** make the E1 six-source panel reusable. Independently joining
the six frozen House02 source coordinates to retained cube source/wind/seed
records finds **zero matching cube runs** in the three proposed winds. Gate1A
compact 300-value vectors are tied to the old probe contract and cannot be
re-extracted. The provisional first-stage shortfall is therefore 72 House02
runs plus 96 House01/House03 runs = **168 new plume runs**.

This number is an audit output, not authorization to generate any plume.
