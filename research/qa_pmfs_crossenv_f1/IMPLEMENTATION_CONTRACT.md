# Implementation frozen before target opening

Use the supplied qa_pmfs_core.py unchanged. Each environment has six candidates, twelve reference realizations per candidate, four historical JTD E2 fresh targets per candidate, ten time slices and thirty probes. Threshold pooled concentration > 0. Use all 300 binary observations without projection.

Jeffreys smoothing is (hit_count + 0.5)/(K + 1), matching the supplied R0 prototype definition. In LOO, remove the held reference from its own candidate, leaving eleven references; maximize the sum of true-source held-reference predictive log likelihood, matching the supplied reference-only selection definition. M1 uses L=1 and rho=0.1,...,0.8; M2 uses L=2,5,10 and the same rho grid. Exact selection ties choose smaller L, then smaller rho. M3 is always L=10,rho=0.6. Final reference fits use K=12 for every model.

Use 40-node Gauss-Hermite quadrature from the supplied core. Consecutive time blocks are time_index // L; all thirty probes at a time share that block's latent variable. All four models share exactly the same marginal probability array, candidate support and uniform six-source prior. Normalize log posterior using logsumexp. No posterior/NLL clipping or calibration fitting.

True-source rank is 1 plus the number of candidates with strictly greater log likelihood, matching the historical JTD E2 rank convention. Top-1 is the MAP classification fraction, with deterministic first-candidate-index tie breaking. Top-3 is rank <=3. Report MAP tie frequency. Mean rank, MRR, NLL and MAP spatial error are source-averaged (four targets per source). Improved/harmed counts compare each source's mean rank to M0; also report M2 versus M1.

Apply G1-G7 literally, with the user-supplied G7 amendment. Any G7 failure is NOT_CROSS_ENV_GENERAL. Otherwise all seven gates must pass for CONFIRMED. The CALIBRATION_ONLY special case requires neutral mean ranks in all environments, no Top-1 deterioration beyond the permitted one target, and improved pooled M3 NLL. All other failures are NOT_CROSS_ENV_GENERAL. Preserve complete per-target metrics, candidate scores and log posteriors so alternative descriptive metrics can be recomputed without changing this gate.

No historical JTD scoring algorithm is run. Historical targets have previously been inspected for JTD; they remain excluded from QA model selection and this implementation freeze. No new simulation or closed loop is authorized.
