# START HERE — CTT final-agent handoff (2026-08-30)

This branch is the authoritative **handoff entry point** for the next agent.

## 0. Checkout

```bash
git fetch origin
git checkout handoff/ctt-final-agent-resume-20260830
```

Then read, in this order:

1. `docs/CTT_AGENT_HANDOFF_FULL_STATE_20260830.md`
2. `docs/CTT_AGENT_NEXT_EXECUTION_CONTRACT_20260830.md`
3. Existing frozen contracts referenced there.

Do **not** infer state from old experiment names alone.

## 1. Immediate user-provided filesystem fact

The user says the already-unpacked/shared dataset is under Windows:

```text
D:\ZYC\A-gas\workspace
```

The previous Codex mistakenly started a Zenodo download, then stopped after the user clarified the dataset is already in the VMware shared folder. **Do not redownload the dataset unless the shared folder is proven incomplete.** First inspect the VMware shared-folder mapping and `/mnt/hgfs` (or the actual mounted path) and map it back to the Windows path above.

## 2. Current scientific state — do not overwrite

Frozen facts:

```text
CTT_H01_WIND_CONDITIONED_NEURAL_M1_PHYSICAL_NO_GO
CROSS_WIND_NATIVE_FIRST_PASSAGE_PASS
CLOSED_LOOP_NOT_AUTHORIZED
```

Interpretation:

- Native physical/sensor chain is valid.
- Native 0.2-s first-passage carries cross-wind source ordering.
- Arrival timing adds information beyond survival/reachability.
- The old fixed 33-feature wind-conditioned MLP failed held-out physical generalization.
- Therefore the physical/temporal mechanism remains viable, but the current neural surrogate is rejected.

Do not reuse the failed 33-feature MLP for closed loop.

## 3. Immediate blocker / next action

The previous agent stopped while checking whether **genuinely fresh H01 wind fields** exist for final neural confirmation and later closed-loop development.

It had locally observed only `wind_iteration_0..10` in one location and believed contexts 0..9 had consumed iterations 1..10, leaving only one unused field. It then learned the user's full dataset is already in the shared folder and had not yet completed the shared-folder inventory.

**Your first task is therefore not training.** It is:

```text
FRESH_WIND_INVENTORY
```

Inspect `D:\ZYC\A-gas\workspace` through the VMware share and enumerate every House01 wind/OpenFOAM/GADEN airflow realization, hash it, and mark whether it has already been consumed.

Logical labels `10..15` are only labels. They do NOT require files literally named `wind_iteration_11..16`. Any genuinely unused independent House01 airflow realization may be assigned a fresh logical context ID after provenance is frozen.

If fewer than six real unused H01 wind contexts exist, do not copy, rename, rotate, perturb, or noise-inject old fields. Report `FRESH_WIND_INPUT_BLOCKED` and preserve the evidence.

## 4. No fresh TEST opening before freeze

Before generating/sampling any future confirmatory test performance:

- freeze the final spatial wind/map encoder + first-passage hazard decoder architecture;
- freeze exact input schema/order, normalization, optimizer, LR, batch size, epochs/patience, seed, checkpoint tie-break, controls/bootstrap settings;
- commit and hash the freeze;
- ensure runtime-available vs simulator-only wind inputs are explicitly labeled.

Contexts 1 and 2 are now diagnostic-only forever and may never be reused to claim confirmatory PASS.

## 5. Closed-loop rule

Do not start 300-s closed loop until BOTH fresh neural gates and runtime qualification pass.

If the final fresh neural M1 passes and runtime parity/single-consumption gates pass, proceed automatically to the pre-registered H01 300-s paired OFF/ON development experiment described in the next-execution contract. Do not return to method ideation.

## 6. Important frozen threshold semantics

Native measured first-passage threshold semantics remain **strict**:

```text
measured_ppm > 0.1
```

Do not silently change this to `>= 0.1`.

## 7. Protected review branches

Do not modify these frozen review branches/PRs:

- PR #8 — residual-TCN V1–V7 audit, head `484fb9f330a21c8f2969fdcced8ce7c578217df2`.
- PR #9 — causal first-passage offline chain, review head `7fcab1606a059f07fcf7959675ae7a0d275d9243`.

The previous working branch at handoff was:

```text
codex/ctt-h01-wind-bank-freeze-20260830
aacf30f427d8a23a4b5ba936b78d0d0a21bdaf29
```

This handoff branch was created from that exact commit.
