# C0.5 sparse rank diagnostic freeze

This diagnostic was specified **after** the held-out field error was read but
**before** any source-rank score was computed. The two frozen v2 model seeds
and both S2-W2 plume seeds must be evaluated without model changes.

The probe set contains 30 equal-area 5×6 tile centers, each moved to its
nearest free cell using the House02 obstacle mask only. The same 30 cells are
sampled at all ten fixed times. This is a source-blind sparse sensor network,
not a UAV trajectory. It uses no concentration field to choose points.

For each model, compare squared error of predicted `log1p(concentration)` at
those probes under candidate S1-W2 versus candidate S2-W2. Lower error ranks
the candidate first. The true S2 rank must be 1 for both training seeds and
both plume seeds to count as a local positive rank diagnostic. The S2-W1
prediction is a transport-swap control: its error should exceed S2-W2 for
every paired evaluation. A source swap is represented by the S1-W2 candidate.

This two-candidate network diagnostic is **not** the charter's Native
PMFS-compatible source-rank replay. It cannot satisfy C0.5 ADVANCE or G3,
even if all eight comparisons are favorable. It is useful only to detect a
failure of source identity or transport conditioning before building a fuller
offline PMFS replay. The implementation is
`research/causal_compositional_plume_world_model_v1/c05_sparse_rank_diagnostic.py`.
