# CSTAR — Codex handoff after independent review

Date: 2026-09-06
Branch: `g3-cstar-revise-before-exec-20260906`
Base reviewed snapshot: `0866ad8b3b6af6ba46ad125e74508ff2b5ede503`
Status: **REVISE_BEFORE_EXECUTION**

This file supersedes the previous instruction to continue directly from VM checks
to the 12-run closed-loop matrix.

## 0. Current decision

Keep the three-module candidate direction:

- M1 PICR — causal source representation;
- M2 CPO — source/route-conditioned first-passage prediction;
- M3 PHS — prospective source-hypothesis resolution.

Do **not** reopen the innovation search and do not return to GMRF tuning.

However, the current task is **not** to run the 12-case closed loop. First close
the reviewed audit, identity and formal-gate gaps, then run only a limited
controlled validation bundle and stop for review.

No command in this handoff authorizes formal 12-run performance experiments.

## 1. Pull exactly this branch

```bash
set -euo pipefail
REPO=/home/zyc/gsl_ws/src/GasSourceLocalization
BRANCH=g3-cstar-revise-before-exec-20260906
cd "$REPO"
git fetch origin
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"
git status --short
git rev-parse HEAD
```

If unrelated local edits exist, preserve them and use a clean worktree.

Create a fresh evidence directory:

```bash
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
EVID=/mnt/hgfs/workspace/CSTAR_REVISE_${STAMP}
mkdir -p "$EVID"
git rev-parse HEAD > "$EVID/START_GIT_SHA.txt"
```

## 2. Read in this order

1. `docs/CSTAR_REVISE_BEFORE_EXECUTION_CODEX_HANDOFF_20260906.md`
2. `docs/CSTAR_M1_IDENTIFIABILITY_BOUNDARY_20260906.md`
3. `experiments/ctpi_cstar/CSTAR_CONTROLLED_CAUSAL_ASSET_CONTRACT_V1.json`
4. `experiments/ctpi_cstar/CSTAR_REQUIRED_EVIDENCE_CONTRACTS_V1.json`
5. `experiments/ctpi_cstar/CSTAR_CASE_AUDIT_SCHEMA_V1.json`
6. `experiments/ctpi_cstar/m1_picr/model.py`
7. `experiments/ctpi_cstar/m1_picr/offline.py`
8. `experiments/ctpi_cstar/m2_cpo/offline.py`
9. `experiments/ctpi_cstar/authorize_closed_loop.py`
10. `tools/cstar_seed12_crosshouse_performance.py`

The older `CODEX_CSTAR_VM_TO_CLOSED_LOOP_20260906.md` is historical and is not
the active execution authority after this review.

## 3. Phase R0 — mandatory regression tests before real data

Run:

```bash
python3 experiments/ctpi_cstar/run_reference_selftests.py \
  2>&1 | tee "$EVID/reference_and_review_selftests.log"
```

Required behavior now includes:

- minimal `{contract, pass:true}` evidence cannot authorize closed loop;
- a single correct source estimate at t=239 cannot receive 240 s AUC=0;
- AUC uses causal forward zero-order hold, not future/backward interpolation;
- left-padded PICR sequences are rejected instead of producing version-dependent NaN;
- no valid candidate support emits explicit abstention;
- if `zS` is held constant and the candidate set is fixed, changing wind cannot
  change the source posterior through a hidden candidate-relative bypass.

Record:

```bash
python3 --version > "$EVID/python_version.txt"
python3 - <<'PY' > "$EVID/torch_version.txt"
import torch
print(torch.__version__)
print(torch.version.cuda)
PY
```

If any mandatory regression fails on the VM, stop and fix the implementation
without changing its scientific meaning.

## 4. Phase R1 — spent replay is premise only

Run the strict trace preflight and spent replay if the old seed12 assets are
available.

Important semantics:

- the M1 output is `CSTAR_M1_SPENT_REPLAY_PREMISE_V3`;
- the M2 output is `CSTAR_M2_SPENT_OBSERVATIONAL_REPLAY_V2`;
- historical subsequently executed future path is **not** `do(route)` evidence;
- the derived gas EMA channel is explicitly **not** an audited FOPDT sensor state;
- a missing M3 panel at this stage is **not** an M3 scientific NO-GO;
- no spent result can be consumed by `authorize_closed_loop.py` as a formal gate.

Do not regenerate old spent closed-loop runs.

## 5. Phase R2 — audit actual controlled-data possibilities before generating data

First inspect existing frozen banks/world manifests/route logs and determine what
already satisfies the typed controlled-data contract.

Use:

```bash
python3 experiments/ctpi_cstar/audit_bank_causal_pairs.py ...
```

and build a candidate manifest conforming to:

`experiments/ctpi_cstar/CSTAR_CONTROLLED_CAUSAL_ASSET_CONTRACT_V1.json`.

Then run:

```bash
python3 experiments/ctpi_cstar/validate_controlled_assets.py \
  --manifest /path/to/CSTAR_CONTROLLED_CAUSAL_ASSET_V1.json \
  --output "$EVID/CSTAR_CONTROLLED_CAUSAL_ASSET_AUDIT_V1.json"
```

Hard rules:

### M1

- exact-source invariance pairs require identical `source_xyz_m`;
- at least one declared nuisance realization/mechanism differs;
- region/carrier identity is not exact-source identity;
- candidate domain must be truth-independent;
- formal sensor state must be a genuinely audited FOPDT internal state or the
  feature must be absent; do not relabel gas EMA;
- formal training examples must represent causal prefixes or a frozen bounded
  causal history window, not only the last part of a completed run;
- low-information examples must remain available for uncertainty tests.

### M2

A formal route case is legal only when:

- `route_kind` is `decision_locked_planned_route` or `controlled_open_loop_route`;
- the route was frozen by/before decision time;
- it does not encode later policy reactions to future gas observations;
- source placements are diverse;
- realized outcome is held out from route-law construction;
- planned-vs-executed deviation is reported.

Do not generate large new data yet. First inventory existing assets and report
exactly what is missing.

## 6. Phase R3 — complete the formal M1 producer

The current spent trainer is not the formal producer.

Implement a separate versioned formal trainer/gate that writes exactly:

`CSTAR_M1_CONTROLLED_CAUSAL_GATE_V1.json`.

It must save a real checkpoint and raw result manifest.

Required comparisons/controls:

1. full PICR;
2. matched unconstrained temporal encoder;
3. context-only baseline;
4. `zS` zero/mask control;
5. `zS` permutation within preregistered matched-context groups;
6. source-label permutation;
7. no-intervention-loss ablation.

Required metrics include at least:

- held-out source cross-entropy / proper score;
- localization error on the fixed truth-independent candidate domain;
- same-exact-source nuisance-intervention `zS` distance;
- matched-context different-source separation;
- posterior entropy/max probability on low-information controls;
- leave-one-House-out direction where the available controlled asset permits it.

A formal PASS is forbidden if source performance can be reproduced without
`zS`, if label permutation retains the gain, if intervention ablation does not
hurt invariance, or if low-information inputs become unsupported sharp beliefs.

Do not claim a global source-identifiability theorem. Follow
`CSTAR_M1_IDENTIFIABILITY_BOUNDARY_20260906.md`.

## 7. Phase R4 — complete the formal M2 producer

Implement a separate formal producer for:

`CSTAR_M2_SOURCE_DIVERSE_PREDICTIVE_GATE_V1.json`.

It must save a real checkpoint and raw result manifest.

The formal M2 trainer must **not** use retrospective adaptive future trajectory
segments as `do(route)` inputs.

Required providers/baselines:

1. named causal Gaussian-plume + audited FOPDT provider;
2. named verified-physics prior/provider based on the already corrected
   conservative transport implementation;
3. learned CPO.

Freeze the event threshold before held-out outcomes are inspected.

Report at least:

- first-passage NLL;
- first-passage Brier score;
- encounter-CDF / committor calibration;
- first-step-hit fraction;
- no-hit fraction;
- threshold/event saturation diagnostic;
- source/House/transport held-out breakdown;
- planned-vs-executed route deviation where applicable.

CPO must improve in the preregistered direction over **both** named baselines to
obtain formal M2 PASS.

## 8. Phase R5 — M3 counterfactual gate

Keep the current PHS mathematics, but use only a genuine same-decision-context
multi-route panel with independently realized/evaluated outcomes.

Run the deterministic route-law destructive shuffle.

Do not reinterpret one historical executed route as multiple counterfactual
routes.

## 9. Stop point for this Codex run

Even if R2-R5 look positive, **stop before production `cstar_v1` smoke and before
any H01/H02/H03 × seed12 × A0/F00/F10/F11 performance run**.

Push back a revision-validation bundle containing:

- final git SHA;
- mandatory selftest log + Python/Torch versions;
- spent premise reports, if runnable;
- controlled asset inventory and validator output;
- exact data-generation gap list;
- formal M1 producer code/config/checkpoint/hash/results if completed;
- formal M2 producer code/config/checkpoint/hash/results if completed;
- M3 counterfactual result if a real panel exists;
- all negative/destructive-control results;
- `CSTAR_REVISION_VALIDATION_SUMMARY.json`.

The summary must classify each item as one of:

- `IMPLEMENTATION_PASS`;
- `SCIENTIFIC_PREMISE_PASS`;
- `SCIENTIFIC_NO_GO`;
- `BLOCKED_MISSING_CONTROLLED_ASSET`;
- `NOT_RUN`.

No missing asset may be converted into a PASS.

## 10. What Codex may fix without asking for a new scientific design

Allowed:

- Python/Torch compatibility and masking implementation;
- strict CSV/typed dataset adapters;
- checkpoint serialization and SHA manifests;
- source/candidate normalization that is global/frozen and does not use held-out
  House identity or source truth as an input;
- actual FOPDT state extraction;
- decision-time route-plan logging;
- controlled open-loop route materialization;
- verified-physics baseline adapter;
- exact formal gate producers and destructive controls described above;
- logging/audit fields needed by the frozen contracts.

Not allowed:

- changing M1/M2/M3 scientific identity after seeing outcomes;
- House/seed-specific tuning;
- replacing M1 by ordinary Bayesian nuisance marginalization;
- calling historical adaptive future path `do(route)`;
- relabeling gas EMA as FOPDT state;
- using source truth/House/member/future gas/future wind as model inputs;
- runtime predictive-bank lookup;
- starting the 12-run matrix in this revision-validation run.

## 11. Exit condition

The correct output of this Codex task is a **reviewable, finite validation
bundle**, not a 12-run result.

After that bundle is reviewed, only then decide whether the project status can
move from `REVISE_BEFORE_EXECUTION` to `READY_FOR_PRODUCTION_SMOKE` and later to
`READY_FOR_12RUN`.
