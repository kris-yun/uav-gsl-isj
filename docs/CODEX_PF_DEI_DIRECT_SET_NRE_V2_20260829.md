# CODEX — PF-DEI Direct Set-NRE V2 minimal correction experiment

Date: 2026-08-29
Branch: `research/pf-dei-direct-set-nre-v2-20260829`
Execution class: EXISTING-BANK / ONE MODEL / H01 DEVELOPMENT DIAGNOSTIC

## Why this experiment exists

Residual Set-NRE V1 is frozen NO-GO for localization. Do not reinterpret that result as proof that conditioned Deep Set / NRE is intrinsically useless. Inspection of the frozen V1 code reveals two contract problems:

1. the generating source and negative candidate were both sampled from a randomly chosen historical PMFS posterior `q`, while the generated pseudo-observation was produced independently from a simulator trajectory/source/member; therefore the PMFS posterior supplied as model context did not correspond to that pseudo-observation;
2. historical H01 trajectories 0..9 were included in neural training trajectories 0..24 and later reused for historical evaluation, so trajectory support was not held out.

V2 changes only the inference-training definition needed to test these issues. It does not change the physical bank, sensor model, Deep Set concept, optimizer family, hidden width, block semantics, or training budget.

## Hard prohibitions

Do NOT run GADEN, generate new physical data, use TCN/Transformer/TrajCast, tune temperature/blend/A0, alter H01 historical outcomes, train H02/H03, launch shared/LOHO, run shadow, or run closed loop.

Do not use historical H01 localization error, true carrier, or rank to select checkpoint or hyperparameters.

## Frozen V2 files

Use:

- `experiments/cg_pc_ctt/pf_dei_direct_set_nre_v2.py`
- `experiments/cg_pc_ctt/train_pf_dei_direct_set_nre_v2.py`
- `experiments/cg_pc_ctt/evaluate_pf_dei_direct_set_nre_v2_historical.py`

Do not silently fall back to residual V1 files.

## Scientific contract

### Training source proposal

For every pseudo-observation pair:

- `S ~ Uniform({0,...,209})`, independent of trajectory/update and independent of all historical PMFS posteriors;
- observation `D ~ p_sim(D | S)` from one held-out physical nuisance member;
- candidate prediction set excludes that held-out member (strict 8 -> 7 LOMO);
- negative candidate `S- ~ Uniform({0,...,209})` independently of `S` and `D`.

Under balanced joint-vs-product binary NRE, the population-optimal logit is, up to a D-only constant,

`f*(s,D) = log p_sim(D|s) - log p_pi(D)`

because the proposal over source is the same in joint and product distributions. It is therefore a source likelihood factor and may be combined with the independently frozen geometry prior only after scoring:

`q(s|D) proportional q0(s) * exp(f_theta(s,D))`.

No PMFS posterior enters the network, sampler, or final direct posterior. PMFS is an evaluation baseline only.

### Trajectory split

- historical H01 trajectories 0..9: neural holdout / one-shot evaluation only;
- train: 10..24;
- validation: 25..29.

Any overlap is a contract failure.

### Architecture

Keep the small conditioned Deep Set structure and block representation from the committed V2 code. No architecture search. Candidate features must not include PMFS posterior mass/entropy/mean/spread or q0 prior mass.

### Budget

- seed: 3201;
- AdamW 3e-4, weight decay 1e-4;
- pairs/batch: 8;
- max steps: 12000;
- validation every 250 steps;
- checkpoint: minimum simulated validation BCE only;
- no restart based on historical H01 outcome.

Before full training, run a 500-step timing smoke. If projected 12000-step wall time exceeds about 10 minutes on the same machine, diagnose I/O/implementation; do not reduce sources, members, updates, or holdout constraints.

## Required pre-evaluation checks

1. Python syntax/import PASS for all V2 files.
2. Member permutation invariance within numerical tolerance.
3. Block permutation invariance if block context is permuted with its block.
4. Strict held-out member absent from positive and negative predictive sets.
5. PMFS posterior file is not opened by the training process.
6. Source exposure audit from the completed 12000-step draw: report min/median/max positive counts over 210 carriers. No carrier may have zero exposure.
7. Training trajectory indices disjoint from `{0,...,9}` and validation indices disjoint from both.
8. Checkpoint selected only by simulated validation BCE.

## One-shot H01 historical evaluation

After training is frozen, evaluate once on H01 seeds0..9 x updates1..5 using the authoritative observed-block manifest and all 8 predictive members. PMFS posterior may be loaded only to report the Classic baseline.

Report per case and aggregate:

- direct true-source rank and normalized rank;
- Top1/Top5/Top10;
- q0-based direct posterior truth mass;
- direct posterior carrier-centroid expected error;
- Classic PMFS rank and expected error baseline;
- source-update 1..5 tables separately;
- per-seed rank/error trajectories;
- inference wall time.

## Predeclared decision

This is still H01 development, not paper confirmation.

Call `PF_DEI_DIRECT_SET_NRE_V2_PROMISING` only if all hold:

1. mean carrier-centroid expected error improves >=10% relative to frozen Classic PMFS 4.899306 m;
2. no source-update index has mean expected-error degradation >5% relative to Classic PMFS at that same update;
3. direct median normalized true-source rank <=0.25 overall;
4. direct Top10 >=10/50;
5. update-1 mean expected error does not degrade >5% vs Classic PMFS.

Otherwise call `PF_DEI_DIRECT_SET_NRE_V2_NO_GO`.

Regardless of verdict, STOP after this one model/evaluation. Do not tune, retrain, expand House, or enter closed loop.

## Expected cost

Reuse existing materialized dataset and bank. No GADEN. V1 took about 194 s for 12000 steps; V2 should remain minutes-scale. Total task should normally be well below one hour including checks, and scientific compute should be minutes-scale.
