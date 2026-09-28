# CD-D0 read-only action-sensory alignment diagnostic

## Frozen inputs

- The 48 H01/H02 archived Native VGR trajectories and the one H02 crosshouse Native trajectory in `evidence/ds_pmfs_identity_d1/ASSET_FREEZE.json`. Exclude H03 because its only Native truth is absent from the Native legal support. No LF controller or AOD-filter trajectory is used.
- `evidence/ds_pmfs_identity_d1/COMPACT_EVENTS.json` supplies deployed concentrations and actual robot positions, already parity-checked against the archived original logs. Each five consecutive measurement events forms one completed stop; its five positions must be identical. Mean concentration across those five events is the stop readout. Only stops present at the last Native source update are used.
- H01/H02 full Native legal candidate bank and the same `u`/`rawu` observation operator as D1. Both methods use the same candidate order, 0.20 m physical footprint, and B2 nonnegative gain-profile SSE. The user-specified truth is used only for evaluation.

## Alignment comparison

For consecutive completed stops, calculate observed `dy[j]=y[j+1]-y[j]` and candidate template `dm[s,j]=m_s(x[j+1])-m_s(x[j])`. Fit one nonnegative gain per source over the entire difference vector and rank all legal sources by SSE. The candidate templates are static wind-ensemble means. This is an action-conditioned contrast diagnostic, not a temporally resolved transport predictor.

The destructive control applies one source-blind permutation of the transition index to every candidate `dm[s,:]` while leaving the real `dy` sequence fixed. It therefore preserves each candidate's multiset of spatial template changes but destroys the specific action-sensory pairing. For each trajectory, generate 200 permutations with `numpy.random.default_rng(2026092805 + ordinal)`; reject identity permutations. Preserve the same permutations for `u` and `rawu`.

Compare the real CD rank and best-wrong margin to the trajectory-specific permutation distribution. Also compute ordinary absolute-level B2 on the **same completed stops**, with the same source support and gain rule. This baseline checks whether differencing adds source discrimination beyond the already available location-conditioned template fit.

Use the final completed Native source-update stop as the primary descriptive endpoint. Earlier completed source-update stops are saved as trajectory diagnostics. First aggregate trajectories by physical source, then House; same-source runs, two H02 winds, and repeated updates are not independent scientific units.

## Interpretation boundary

This is an OPEN development diagnostic after the D1 readout results were seen. No numeric scientific PASS threshold was provided by the user before this data inspection. Even a positive real-versus-permuted contrast cannot establish a fresh main innovation or prove a neural corollary-discharge mechanism. It may only justify a separately frozen confirmation. No planner repair, probability fusion, new simulation, training, or VGR run is authorized by this protocol.
