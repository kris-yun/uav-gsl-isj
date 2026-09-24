# Failed / Held Route Ledger — Do Not Restart from Scratch

Date: 2026-09-24

Purpose: prevent a second researcher/model from repeating already-falsified directions.

This is a research-decision ledger, not a chronological diary.

---

## 1. TNQC V5 — Transport-Nuisance Quotient / projection

Status: **NO-GO / HOLD closed**

What was tested:
- frozen 300 s offline protocol;
- six cases H01/H02/H03 × seed0/1;
- integrity passed.

Representative result:
- aggregate decision HOLD;
- fused-vs-native changes were near zero or slightly worse;
- typical deltas approximately -0.007% to -0.061%;
- one H02 case exactly unchanged.

Why it failed:
- quotient/projection did not separate true source from confounded transport strongly enough;
- the improvement magnitude was far below a publishable main innovation;
- projection/quotient ideas also have prior art.

Reusable lesson:
- algebraic nuisance removal is insufficient if the nuisance and source information are entangled in the same observables.

Do not restart as:
- another normalization;
- another quotient;
- another PMFS local reweighting.

---

## 2. Active Deconfounding

Status: **NO-GO**

What was tested:
- fixed transport values;
- grid-off controls;
- equal-budget strategies.

Result:
- 0/6 passed.

Why it failed:
- selected interventions/conditions did not reliably separate true from false source hypotheses.

Reusable lesson:
- active intervention alone does not repair an uninformative or confounded source representation.

Do not restart as generic active experimental design.

---

## 3. DRPE / posterior reweighting

Status: **HOLD then retired**

Theory parent:
NeurIPS 2025.

Idea:
retain native likelihood, learn posterior/reweighting correction.

Problems:
- phase-1 reference behavior was not convincingly reproduced;
- native baseline reproduction itself was fine;
- similar ideas already exist in olfaction;
- 2025 origin did not meet the desired 2026-level novelty target.

Reusable lesson:
- learned posterior correction without a stronger new physical/statistical object is too close to method-level reweighting.

---

## 4. MIPO Active Observability

Status: **retired before further testing**

Evidence:
- branch/evidence around `research/mipo-active-observability-v1`;
- 18 valid anchors;
- 141,120 rows.

Why retired:
- the specific observability idea already had relevant prior art;
- insufficient novelty as the paper-level main idea.

Reusable lesson:
- do not spend simulation budget on a specific mechanism after novelty boundary already fails.

---

## 5. HCMC v1

Status:
`HCMC_V1_INDEPENDENT_OFFLINE_NO_GO`

What mattered:
- some old/offline data appeared promising;
- fresh independent data did not preserve the signal.

Representative native six-case errors were roughly:
4.60, 4.27, 6.93, 4.36, 7.95, 7.96 m.

Why it failed:
- apparent mechanism did not survive independent validation.

Reusable lesson:
- no route is trusted because it works on previously inspected data.
- fresh independent plume/source evidence is mandatory.

---

## 6. Dynamic export / parity route

Status:
`DYNAMIC_EXPORT_STOP_PARITY_NOT_ESTABLISHED`

Key findings:
- offline candidate forward budget was actually 200 × 0.2 s = 40 s;
- ON/OFF had ~154 candidates;
- native PMFS final hit map is a static frequency map;
- historical intermediate estimated-wind grids had been overwritten, preventing exact replay.

Why stopped:
- exact parity contract could not be established.

Reusable lesson:
- do not build a main claim on historical intermediate state that cannot be exactly reconstructed.

---

## 7. M4-v2 / C0.5 compositional operator

Status: **HOLD**

Positive signal:
- on held-out S2×W2, operator field error beat monolithic model;
- reproduced for multiple training seeds / independent plumes.

Failure:
- source-ranking diagnostic already had truth rank 1 for both compared arms;
- therefore better field prediction did not yield source-identification gain;
- wind-swap effect was weak/inconsistent.

Reusable lesson:
- field-prediction quality is not a sufficient objective.
- every candidate must be judged on arbitrary-source identity/ranking.

---

## 8. M4-v3 / D0

Status:
`D0_FAIL_STOP_M4_V3`

Failures:
- held-out wind-response cosine only ~0.341–0.383, below frozen >0.5 gate;
- source superposition error >1e-5;
- one field-error comparison worse than monolithic.

Action:
- no extra seeds;
- no closed loop.

Reusable lesson:
- if basic physical operator properties fail, stop before localization tests.

---

## 9. Source-Lineage Lagrangian v2

Branch:
`research/source-lineage-lagrangian-v2`

Decision:
`L1_FAIL_STOP_SOURCE_LINEAGE_MAINLINE`

Important result:
- deterministic 3D physics improved one-step centroid prediction over 2D by ~74–75%;
- learned lineage residual added only ~0–2%;
- lineage destruction did not remove the apparent gain.

Physical diagnosis:
- GADEN filament stochastic noise produced a one-step random-walk floor approximately matching the observed residual error.

Why it failed:
- deterministic physics was already near the stochastic floor;
- the learned lineage component was not load-bearing.

Reusable lesson:
- once prediction reaches the simulator's stochastic floor, another deterministic learner cannot create source information.

Also note:
generic backward transport / Schrödinger-bridge source localization became occupied by 2026 prior art, so do not restart generic backward-transport as the main novelty.

---

## 10. Causal Biorthogonal Green / Non-Hermitian source-sensor duality

Branch:
`research/causal-biorthogonal-green-v1`

Gate:
exact-physics source-identifiability oracle on 630 arbitrary source candidates.

Decision:
`GATE1A_FAIL_STOP_SOURCE_TO_SENSOR_GREEN_FAMILY`

Frozen result:
- S2_W2_A truth rank mean/C/D = 1 / 2 / 1;
- S2_W2_B = 7 / 7 / 4.

Independent review confirmed:
- no W1/W2 mismatch;
- no scientific-contract-changing infrastructure patch;
- B's top errors remained geographically close to truth.

Scientific diagnosis:
- exact deterministic forward physics identifies the correct local source basin;
- independent stochastic plume realization can still reorder nearby 0.3 m source cells.

Why the family stopped:
- if exact frozen source→sensor physics itself is not realization-robust enough under the gate, a learned Green compression cannot be claimed as the main solution.

Reusable infrastructure:
- 630-source exact-forward C/D bank;
- fixed 30 probes × 10 times;
- W2 contracts;
- exact arbitrary-source benchmark.

Do not rerun the 630×2 bank unless a contract changes for a justified future experiment.

---

## 11. Mori–Zwanzig / realization-invariant source signature

Branch:
`research/realization-invariant-source-signature-v0`

### D0 positive signal
Per-time L1 spatial mass fraction followed by temporal aggregation changed:
- S2 A/B raw = 1/7
- projected static signature = 2/3.

Same-source A/B discrepancy decreased substantially.

### D1 positive signal
Full off-diagonal temporal covariance improved S2 ranks to 1/2, while diagonal/no-memory controls did not.

### D2 positive signal
Target-blind finite-memory rule:
- memory 0: B rank 7
- memory 1: 4
- memory 3: 3
- memory >=4: 2
- automatic horizon = 7.

Decision at this stage:
`D2_ADVANCE_FINITE_MEMORY_SOURCE_LIKELIHOOD`.

### D3 fresh second-source falsification

Truth S1:
`pmfs_10_17 = (-2.242730141,-2.200880051,0.20)`

Result:
- S1_A raw / D0 / diagonal / D2 = **1 / 9 / 6 / 5**
- S1_B = **1 / 1 / 1 / 1**

Decision:
`D3_FAIL_STOP_MZ_SOURCE_INFERENCE_MAINLINE`

Critical interpretation:
- MZ-style memory itself was not disproved;
- the mainline failed because it globally removed absolute plume mass before inference.

For S1:
- absolute concentration was stable and informative.

For S2:
- absolute amplitude was much more realization-sensitive.

630-source audit then showed stochastic variability ranges roughly 1.5%–57.5%.

Therefore:
**global realization invariance is the wrong abstraction.**

Do not rescue with:
- raw + normalized mixing after seeing D3;
- source-dependent hand weights;
- changing memory horizon;
- another normalization.

Reusable lesson:
the stochastic distribution itself must be source conditioned.

---

## 12. Current transition: Path-Action Source Inference (PASI)

Status at handoff creation:
**active fresh S3 confirmation in progress**.

Why this route is different:
it does not attempt to make every source share the same invariant representation.

Instead it scores an observation under each candidate's own stochastic uncertainty.

This is the first post-D3 route designed explicitly around the 630-source heteroscedasticity diagnosis.

See:
- `docs/PRO6_PROJECT_HANDOFF_20260924.md`
- `01_idea/PATH_ACTION_SOURCE_INFERENCE_FREEZE_20260924.md`
- `CODEX_PASI_D0_S3_HANDOFF_20260924.md`

Do not restart any route above unless there is a genuinely new scientific object that directly addresses its recorded failure mechanism.
