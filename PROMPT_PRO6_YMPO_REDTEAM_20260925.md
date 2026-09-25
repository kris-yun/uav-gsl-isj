# PRO6 NEXT TASK — Young-Measure Plume Operator (YMPO) Red-Team

Date: 2026-09-25

Primary-thread status:
- IPTO mainline: STOP;
- Blackwell route: HOLD as evaluation theory only;
- LSC: validated mechanism/evaluation geometry, not standalone algorithm;
- current leading candidate: **YMPO — Young-Measure Plume Operator**.

Do not run simulations.

## Empirical facts you must treat as fixed

D1R House02/W2 contains 168 sources x16 realizations x10 time slices x30 probes.

Fresh same-source 6-fit/2-cal/8-test results:
- per-probe mean field: about -3.22 / -3.39 bit;
- mean+std+hit: about -2.13 / -2.18;
- empirical-distribution summary (mean,std,q25,q50,q75,max,hit): about -2.01 / -2.04.

Temporal-order destruction:
- sorting each probe's ten amplitudes removes time order but retains essentially the same performance as ordered 10x30 log-ppm;
- orderless distribution summaries improve proper score further.

Global-histogram negative control:
- pooling all probes into one global empirical distribution collapses performance to about -4.75 / -5.00 bit.

Thus the candidate object is a **spatial field of local measures**, not one global histogram.

Generic measure-method controls lose to the hand summary:
- RBF KME + LDA ~ -2.79 / -2.77;
- histogram + LDA ~ -2.74 / -2.66;
- direct Wasserstein posterior ~ -3.77 / -3.81;
- direct Hellinger/Bhattacharyya posterior ~ -3.72 / -3.63;
- quantile-function PCA + LDA ~ -2.24 / -2.37.

Whole-source checkerboard holdout with full 168-candidate support:

Point mean field:
-4.450, -4.178, -4.203, -4.311 bit.

Full ordered raw 300-D field:
-4.389, -4.605, -4.253, -4.644.

Mean+std field:
-4.387, -4.680, -4.151, -4.605.

Quantile measure field:
**-4.025, -3.668, -3.718, -3.692**.

Thus the local distribution field wins all four unseen-source scenarios, including versus the higher-dimensional ordered raw field and ordinary mean+variance representation.

Five-snapshot disjoint time subsets:
- even5 mean field: -3.275 / -3.370;
- even5 measure field: -2.090 / -2.122;
- odd5 mean field: -3.246 / -3.412;
- odd5 measure field: -2.134 / -2.207.

The late five-snapshot block is weaker, so the safe object is **protocol-conditioned local measure**, not a stationary PDF.

## Mother theory under audit

Primary 2026 anchor:
Butori, Flandoli, Luongo, Tahraoui,
'Background Vlasov equations and Young measures for passive scalar and vector advection equations under special stochastic scaling limits',
Probability Theory and Related Fields, 2026, DOI 10.1007/s00440-026-01471-3.

The paper shows non-trivial Young measures retaining fluctuation/oscillation information beyond deterministic diffusive limits under special stochastic scaling assumptions.

Do NOT assume those theorem assumptions hold for GADEN.

## Strong ordinary GSL prior art already known

- concentration mean grid maps;
- Kernel DM+V mean+variance maps;
- Gaussian-process mixture maps;
- GMRF mean/uncertainty maps;
- intermittency/detection maps;
- stochastic encounter likelihoods;
- physics-guided neural source/dispersion models.

Current targeted search has not found the exact source-conditioned **spatial field of local empirical concentration measures** used as the forward object for PMFS source inference. This is not proof of novelty.

## Your tasks

### 1. Theory legitimacy
Map the 2026 passive-scalar Young-measure theory to the GSL object carefully.
State:
- what is a legitimate analogy;
- what would be an overclaim;
- whether 'Young-measure plume field/operator' is mathematically defensible terminology for a finite protocol-conditioned empirical-measure field.

### 2. Prior-art kill search
Deeply search GSL/olfaction/turbulent-plume literature for:
- local concentration PDFs per spatial cell;
- distribution-valued gas maps;
- histograms/quantile fields used for source localization;
- measure-valued / Young-measure plume models;
- source-conditioned distribution fields;
- distribution regression for GSL.

Identify the closest actual paper and whether it kills, narrows or leaves the candidate.

### 3. Ordinary-explanation attack
Attack whether the D1R gain can be fully described as:
- variance/intermittency engineering;
- robust temporal pooling;
- feature denoising;
- distributional statistics + LDA;
- Kernel DM+V with extra moments.

State what empirical result must remain unexplained for YMPO to deserve main-innovation status.

### 4. D1 design audit
Audit the drafted House02/4,5-3_fast cross-wind gate:
`research/young_measure_plume_operator_v0/YMPO_D1_CROSS_WIND_96RUN_DRAFT_20260925.md`

Draft design:
- full posterior support remains 168 sources;
- 24 geometry-only anchor/query adjacent pairs;
- 48 generated source locations;
- 2 seeds/source = 96 new runs;
- anchors visible, query sources locked;
- all representation/KRR/calibration choices frozen from W2;
- target physical wind = House02/4,5-3_fast;
- primary endpoint = fresh query-source proper score.

Decide whether 96 runs is scientifically enough for a mechanism gate.
Do not inflate the budget without a quantitative reason.

### 5. Sim-to-real boundary
Explain how a real UAV could estimate local empirical measures from a short dwell/window without requiring repeated source releases.
Distinguish:
- repeated samples within one online observation window;
- repeated plume realizations used only for offline science;
- exhaustive per-source calibration, which is not acceptable.

### 6. Main + auxiliaries architecture
If YMPO survives, propose exactly:
- one main innovation: measure-valued plume transport/source inference;
- two auxiliary innovations that are scientifically necessary and have 2025/2026 far-domain theory anchors.

Do not use ordinary LDA/quantiles as claimed innovations.

Candidate auxiliary families you may audit:
- finite-sample empirical-measure estimation / distribution regression;
- LSC / finite-sample stochastic distinguishability for posterior calibration/model selection;
- adaptive dwell based on convergence of empirical measure, if scientifically justified.

## Deliver only

1. YMPO_THEORY_LEGITIMACY.md
2. YMPO_GSL_PRIOR_ART_KILL_SEARCH.md
3. YMPO_ORDINARY_EXPLANATION_REDTEAM.md
4. YMPO_D1_96RUN_REVIEW.md
5. YMPO_SIM_TO_REAL_AND_3MODULE_ARCHITECTURE.md
6. one-page final recommendation: ADVANCE / HOLD / STOP.

Do not run GADEN.
Do not write a new neural architecture unless the main scientific object survives the prior-art/ordinary-baseline attack.
Do not claim theorem-level Young-measure equivalence to GADEN.