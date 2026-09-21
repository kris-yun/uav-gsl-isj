# VGR House 300 s primary feasibility gate — 2026-09-20

## Correction of evaluation contract

The Orebro3DSEN experiments in this repository are **external measured-data falsification only**. They are useful for checking whether quotient/canonicalized spatial representations preserve source identity under release/airflow nuisance, but they are **not** the project's primary feasibility test.

The project feasibility test is the user's VGR/GADEN House benchmark under the same online contract used by PMFS / ME-ACI:

- House01, House02, House03;
- seeds 0 and 1;
- 300 simulation seconds;
- primary endpoint: PMFS `ExpectedValue(sourceProbability, 0.05)` localization error at the terminal 300 s budget;
- same source, start point, sensor, wind, planner, map, and PMFS settings across compared arms.

Do not substitute 2/5/10-minute classification windows for this endpoint.

## Where the House data live

The frozen runner identifies the authoritative VGR/GADEN scenario roots as:

- `/mnt/hgfs/workspace/GADEN_files/scenarios/House01`
- `/mnt/hgfs/workspace/GADEN_files/scenarios/House02`
- `/mnt/hgfs/workspace/GADEN_files/scenarios/House03`

These are VM-side datasets. The GitHub repository contains the frozen code and selected evidence artifacts, not a complete copy of the raw House scenario directories.

## Required order before a planner-coupled closed loop

### Gate V0 — build / invariance / project-data mechanism sanity

Run the standalone TNQC quotient test and confirm exact affine invariance,
monotone local-order invariance, the candidate-ranking reversal counterexample,
the candidate-bank concordance abstention rule, negative reversed-field
evidence, and insufficient-support abstention.

Then reproduce the frozen **concentration-space** project-data mechanism record:

```bash
python3 reference/tnqc_vgr_offline_240s.py \
  --json-out /tmp/tnqc_vgr_240s_spatial.json
```

It must agree with
`evidence/TNQC_VGR_240S_SPATIAL_MECHANISM_20260921.json`. In particular,
the affine concentration-space quotient is 12/12 at 240 s. The historical
two-source concordance screen releases 11/12 cases and is 11/11 correct; this
is motivation for the hierarchy only, not direct evidence for the V4 online
hit-logit partition-measure gate. This remains a mechanism sanity check, not
the 300-s GO.

### Gate V1 — 300 s native-trajectory shadow test

Run the native PMFS trajectory for the full 300 s budget while computing TNQC in `shadow` mode only. Shadow must not alter PMFS score, posterior, planner, or stopping state.

Required outputs for each House/seed pair:

1. final native PMFS top-5% error at 300 s;
2. candidate-level TNQC diagnostics at every source update;
3. enough frozen candidate/posterior state to construct a **read-only quotient-rescored posterior** on the same native trajectory;
4. final read-only quotient-rescored top-5% error;
5. OFF-vs-SHADOW byte/trajectory determinism check.

The read-only quotient-rescored posterior is the correct first VGR feasibility test because it directly evaluates the online hit-logit representation while isolating inference from navigation feedback. V4 requires the gate to use terminal active leaves weighted by represented free-cell measure.

### Gate V2 — decision to enter closed loop

TNQC may enter planner-coupled `fused` closed-loop testing only if the V1 read-only 300 s result gives a positive signal without source-truth tuning.

Frozen development advancement rule:

- pooled top-5% error reduction versus native PMFS >= 10%;
- at least 4/6 House/seed pairs improve;
- no pair degrades by >25%;
- no false confident collapse.

If V1 fails, reject or redesign TNQC before any planner-coupled claim.

### Gate V3 — closed-loop comparison

Only after V1 passes:

- native PMFS OFF;
- TNQC fused;
- frozen ME-ACI V10;
- ME-ACI V10 + TNQC fused;

all under the same 300 s contract.

## Status

As of this checkpoint, **the VGR project-data spatial mechanism screen is
positive, while the authoritative VGR House 300-s localization gate has not
yet been executed in this ChatGPT environment.**  Orebro remains auxiliary
external evidence only.

Therefore the scientifically valid project status is:

**TNQC VGR-MECHANISM POSITIVE / VGR-300S PRIMARY GATE PENDING / CLOSED-LOOP HOLD.**
