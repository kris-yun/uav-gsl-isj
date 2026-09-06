# CSTAR M3 frozen-bank counterfactual panel plan

Date: 2026-09-06
Status: implementation plan only; do not call M3 PASS.

The existing CPIR frozen lookup bank can be reused as an **offline evaluator asset only**, never as the final CSTAR runtime provider.

The repository verifier establishes the fixed binary contract:

- magic `PFV3STR1`;
- `member_count = 8`;
- `time_count = 1500`;
- one binary per source-carrier per member;
- each file contains a per-cell length table followed by float time series for every free cell;
- `cell_manifest.csv` maps stream ordinal to native cell and physical `(x,y)`.

This enables a low-cost M3 counterfactual panel without launching new GADEN:

1. M1 PICR must first pass its real spent-data gate and provide frozen posterior snapshots for selected historical decision contexts.
2. Use a fixed member split before outcomes, e.g. members `0..3` to construct a baseline route-law provider and members `4..7` only as independent outcome realizations.
3. Use one predeclared route abstraction for all policies. Preferred: real navigation paths if recoverable; otherwise a declared endpoint+dwell abstraction. Never invent straight paths through obstacles.
4. For each context, source hypothesis and route, planning members generate first-passage/no-hit laws under the same threshold/sensor contract.
5. PHS scores routes using only the planning-member laws and the frozen M1 posterior.
6. Independent evaluator members produce realized outcome/risk for **every** candidate route, yielding the `CSTAR_M3_COUNTERFACTUAL_PANEL_V1` asset.
7. The native/baseline route must be included in the same candidate set. PHS may not read evaluator-member outcomes before choosing.
8. Swap member roles as a destructive/robustness check; a result dependent on one lucky split is not a M3 PASS.

This panel is allowed for offline falsification because it is not used at deployment. Final `cstar_v1` remains bank-free.

Do not build the panel with an invented source posterior. M1 real offline evidence comes first, then the posterior snapshots are frozen and passed to this builder.
