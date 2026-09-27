# Full-support OPEN training contract

## Data

Use only already-OPEN H01/H02 observation trajectories used by the Pro package.

Keep the original plume split:
- original train plumes remain train;
- original dev plumes remain dev;
- no crop/start/path from one plume crosses the split.

Do not use House03 gas observations for training or checkpoint selection.

## Candidate support

For each training environment, construct the FULL legal PMFS source-candidate
bank from model-generated PMFS predictions only.

For every legal candidate provide exactly the same cue fields used by the
supplied package:
- native occurrence prediction `p`;
- unblurred amplitude prediction `rawu`;
- candidate xy.

No GADEN counterfactual concentration from unobserved candidate sources may be
used as network context.

If a full legal H01/H02 candidate bank cannot be reconstructed from auditable
assets, STOP:
`BRG_HOLD_FULL_SUPPORT_TRAINING_BANK`.

## Models

Architecture and features are frozen to the supplied implementation.

Train exactly:
1. `candidate_gru` — active-parameter matched ordinary GRU;
2. `brg` — feedback-gated model;
3. `brg_ungated` — same BRG recurrent rounds with feedback gate disabled.

Same:
- train/dev trajectories;
- route augmentation count;
- optimizer;
- epochs;
- seed;
- early-stopping metric/budget.

Do not tune BRG separately.

Checkpoint selection remains OPEN dev final-prefix NLL.

Report, but do not gate execution on:
- dev NLL;
- dev accuracy;
- Brier;
- candidate count per environment.

The purpose is support alignment, not another method-selection experiment.
