# R0.75 relative-versus-action attribution: pre-score contract

## Scope and immutable inputs

Read-only development audit of the same 49 complete H01/H02 Native VGR trajectories used in CD-D0. The exact asset freeze is `evidence/ds_pmfs_identity_d1/ASSET_FREEZE.json` (SHA256 `c4b87c1a11571ba792bd79f1b82c9205ea17f3f32fb7e161aab42441adbd2328`). Deployed events come from `evidence/ds_pmfs_identity_d1/COMPACT_EVENTS.json` (SHA256 `47b8fffb2764737ff0eb3b3f6a93bc495cfdf00c53e99bf8fa6a105128372051`). D1 and CD-D0 results remain frozen at SHA256 `13ae829bd9ef06ebe4857ea2676f56eaeb46261e9aa545f3e1bf23e2e8d6c558` and `f40e51dec94665e951d78b1e79079070f4069a80167dc52520e13f88815ce282`.

Use the same full Native legal candidate support and ordering per environment, the same saved `u` and `rawu` products, 0.20 m physical footprint, `EPS=1e-9` before projection contrast, and one nonnegative gain-profile SSE per candidate. No extra calibration, weighting, threshold selection, target-dependent filtering, or posterior conversion. Truth enters only the evaluation step after every candidate score is formed.

Five deployed measurement events at exactly the same pose form one completed stop; use their mean concentration. Use Native source-update prefixes 20, 35, 50, and 65 when present. The final complete prefix per trajectory is the primary descriptive endpoint. Earlier prefixes are saved as within-trajectory diagnostics. H02 source positions repeated under two winds remain the same physical-source unit in House aggregation.

## Four frozen arms

For stop observations `y` and candidate template `m_s`:

1. `ABS`: `min_(g>=0) ||y-g m_s||^2`.
2. `CENTERED`: independently subtract each vector's stop mean, then `min_(g>=0) ||(y-mean(y))-g(m_s-mean(m_s))||^2`. This uses no stop order. All-pair differences are algebraically equivalent up to a common factor and are not a fifth arm.
3. `REAL_ADJ`: in the recorded stop order, `min_(g>=0) ||D y-g D m_s||^2`, with `D v=(v_2-v_1,...,v_n-v_(n-1))`.
4. `JOINT_SHUFFLED_ADJ`: draw 200 nonidentity permutations of the **stop indices** per trajectory with `numpy.random.default_rng(2026092805 + ordinal)`, where ordinal is the fixed H01/H02 trajectory order in the D1 asset freeze. The same permutation is applied to `y` and every candidate's `m_s`, and the same 200 permutations serve `u` and `rawu`. Then apply the same adjacent-difference B2 score. This preserves every observation-template spatial pairing and changes only which visited stops are neighbors. Do not shuffle candidate predictions alone. Save the 200 rank and best-wrong-margin values for independent recomputation. Joint permutations are evaluated at the final complete prefix; all three unpermuted arms are evaluated at each update prefix.

Every arm reports truth rank, unique Top-1, Top-3, and best-wrong SSE margin (`min wrong SSE - truth SSE`). Lower rank and larger margin are better within an arm. Raw margin magnitudes across ABS, CENTERED, and ADJ use different transformed observation norms, so they are not interpreted as directly comparable effect sizes; report sign and source-level direction, and optionally normalized margin using each arm's own observation norm.

## Attribution and limits

Primary comparisons are `ABS -> CENTERED`, `CENTERED -> REAL_ADJ`, and `REAL_ADJ` versus the trajectory-specific median `JOINT_SHUFFLED_ADJ`. Aggregate trajectories first within physical source, then within House. Do not count repeated updates, wind repeats, or 200 permutations as independent scientific replicates. Report every physical source and both Houses, including harmed sources.

This is an OPEN audit after D1 and CD-D0 were inspected. There is no fresh confirmation or numeric main-innovation PASS threshold. If CENTERED accounts for the adjacent-difference improvement, stop the action-specific interpretation. If REAL_ADJ is consistently better than CENTERED and joint-shuffled adjacency across both Houses and most physical sources, record a development mechanism signal only; a new untouched environment is still required before promotion to Action-Equivariant source inference. No VGR, GADEN, PMFS repair, probability fusion, or new method implementation follows automatically.
