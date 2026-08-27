# CG-PC-CTT V3 pre-mortem — ways this can still fail before we spend a full experiment

Date: 2026-08-27

Purpose: identify failure modes now, bind a diagnostic/safeguard now, and avoid explaining them away after H02 or closed-loop results are visible.

| Potential failure | Why it is plausible | Bound safeguard / interpretation |
|---|---|---|
| Global V2 passes with almost no trajectory information | empirically observed: global rank remains strong on tiny feature subsets | V2 becomes model-side premise only; source precision comes from observation-conditioned local quotient |
| Duplicate candidate IDs look like physical ambiguity | observed in H02 166-ID feasibility bank: 144 unique coordinates | exact coordinate quotient before physical-resolution analysis; alias drift must be zero |
| Many samples all constrain one spatial direction | source is 2-D; collinear/path-redundant observations can leave one direction weak | local 2x2 tangent information `F_i`; inspect `lambda_min`, not point count alone |
| M1 transport field is separable but the physical sensor cannot see the difference | M1 is transport/first-passage; actual gas sensor adds response dynamics/thresholding | call quotient a transport-resolution condition; final release also requires sensor/outcome bridge evidence and adequacy |
| All 8 transport members agree on the same wrong model bias | cross-member replication removes random member noise, not common bias | absolute outcome/model adequacy screen; if no candidate is compatible with observed Y, exact abstention |
| Proximal `R` accidentally contains source-downstream gas variables | earlier candidate R suggestions included encounter/sensor history | `qualify_bridge_causal_contract.py` rejects gas/hit/concentration/encounter/sensor-state in primary R before training |
| Project-specific proxies do not satisfy a general proximal theorem | hidden plume U and source/query semantics are not a textbook treatment-confounding setup | describe sieve-GMM bridge as an operational causal/proxy moment model; never claim general proximal identification unless assumptions are independently established |
| Host-aware residual becomes naive centering under a new name | naive exact-context centering previously failed overall | host-aware V3 must use source-balanced event groups and context interaction; compare against uncentered/direct and naive-centering comparators |
| Bridge operator is weakly identified | plausible when R has little information about unresolved transport U | singular spectrum / numerical rank is a hard diagnostic; weak operator = `WEAK_IDENTIFICATION`, not more epochs |
| Observation quotient over-merges through chains of weak local edges | connected-component transitive closure is deliberately conservative | log component diameter/size; treat over-coarsening as loss of power, never as evidence. Do not tune graph K on H02; use physical adjacency/Delaunay |
| Too many abstentions produce no closed-loop improvement | early trajectory can remain coarse | no threshold weakening. PMFS planner remains unchanged and continues sampling. First-release time is logged; primary 300-s endpoint automatically penalizes late/no release |
| Dynamic block marker is biologically inspired but useless for gas sensing | OSDR transfers a principle, not its equations | fixed 4-D marker; time-reversal/destruction control. If it adds no held-out margin, reject marker rather than adding features |
| Current 626 feature columns cannot be mapped to robot observations | current H03 NPZ lacks query feature coordinates/cell indices | V3 field products require `query_xy` and/or exact `query_cell_index`; `qualify_observation_support_contract.py` fails otherwise |
| H02 feasibility 166-candidate product is mistaken for frozen hard-28 201-candidate data | exact hard-28 artifact is still missing | never substitute; feasibility evidence is diagnostic only |
| Off-grid truth makes categorical Top-1 misleading | real source need not equal one candidate point | primary closed-loop endpoint remains PMFS top-5 expected location error; source quotient represents regions/classes, not categorical truth claims |
| Sequential repeated tests inflate nominal p-values | online windows are repeated and dependent | do not interpret per-window sign-flip p as a sequential Type-I guarantee; posterior release additionally requires even/odd fold directional agreement |
| Runtime becomes too expensive | candidate x 8-member forward simulation can dominate | reuse the existing TADM/ME-ACI eight transport replicas at source-update cadence; V3 must not launch a second duplicate simulator bank per measurement |
| Closed-loop distribution shifts once ON changes the path | offline panels use fixed paths; ON planner trajectory will diverge | unchanged planner but posterior changes path. Full 3-House x10-seed OFF/ON is the actual confirmatory endpoint; offline margin is only permission to spend that experiment |

## Fail-closed rule

No single diagnostic above is allowed to be repaired by an H02/House/seed-specific threshold after held-out outcomes are seen. A failure either:

1. triggers exact abstention / coarse quotient with the baseline planner continuing;
2. rejects that submodule; or
3. creates a separately versioned method before new held-out data are opened.

The fastest scientifically valid path remains: exact hard-28 + valid bridge/controls -> one frozen offline verdict -> full pre-registered 60-run multi-seed matrix.
