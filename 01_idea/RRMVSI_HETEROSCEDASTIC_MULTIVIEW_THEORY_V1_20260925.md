# RR-MVSI GSL-Specific Theory V1 — Heteroscedastic Repeated-View Factorization

Date: 2026-09-25

Status: **THEORY CANDIDATE FOR D1; CCA ITSELF IS NOT CLAIMED AS NOVEL**

## 1. Scientific problem

Previous failed routes showed that plume-realization noise is source/location dependent. A useful invariant representation must therefore tolerate heteroscedastic nuisance rather than assume one source-independent noise law.

## 2. Repeated-realization view model

For a fixed environment/observation contract E and source S, let two independent plume realizations be:

Y^(1) = mu_S + eps^(1)
Y^(2) = mu_S + eps^(2).

Assume only:

1. E[eps^(r) | S,E] = 0;
2. Cov(eps^(1), eps^(2) | S,E) = 0 for independently seeded plume realizations;
3. the nuisance covariance Sigma_S = Cov(eps | S,E) may depend arbitrarily on S.

No homoscedasticity across source cells is required.

## 3. Cross-view content theorem

After centering over the source prior:

Cov(Y^(1),Y^(2)) = Cov_S(mu_S) := B.

The single-view covariance is:

Cov(Y) = B + E_S[Sigma_S] := B + W.

Therefore the generalized eigenproblem

B v = lambda (B+W) v

ranks directions by

lambda(v) = (v^T B v) / (v^T (B+W) v).

lambda is the fraction of total variance along v that is reproducibly source-shared across independent plume realizations.

Source-dependent heteroscedasticity enters W but does not contaminate the cross-view moment B when the paired realizations are conditionally independent.

This explains why a paired-view CCA/generalized-eigen lower bound can suppress turbulent realization nuisance without assuming one global source noise covariance.

## 4. What is classical versus candidate-new

Classical / not novel:
- CCA and generalized eigenvalue decompositions;
- multi-view representation learning;
- content/style disentanglement;
- supervised contrastive learning;
- covariance whitening.

Candidate GSL-specific contribution:

1. formulate independently seeded stochastic plume realizations of the same candidate source as repeated views;
2. use cross-realization moments to isolate source-shared observation content despite source-dependent heteroscedastic plume variance;
3. learn a source-context encoder that predicts the shared content code from candidate source position + geometry + wind, so unseen candidate sources require no repeated release;
4. compare a single online plume observation to every candidate source-content code and return a calibrated PMFS microcell posterior;
5. validate both fresh-realization invariance and completely unseen-source transfer.

## 5. Nonlinear second-order model

A future nonlinear RR-MVSI candidate should contain:

- observation content encoder f_c(Y);
- optional private/nuisance encoder f_n(Y);
- source-context encoder g(S, map, wind);
- same-source paired-view agreement/whitened cross-covariance objective;
- anti-collapse variance/covariance constraint;
- source-context/content alignment;
- nuisance/private reconstruction or orthogonality term;
- calibrated compatibility likelihood over all PMFS candidate cells.

One schematic objective is:

L = L_crossview + beta L_context + gamma L_varcov + delta L_private.

L_crossview must reward agreement of independently seeded same-source views without directly turning into a source-class softmax.

L_context aligns the shared view content with a representation obtainable from source/map/wind context, which is essential for unseen-source and sim-to-real use.

## 6. PMFS-compatible inference

For one online observation y and candidate source cells s_i:

z_y = f_c(y)
z_i = g(s_i, map, wind).

A preregistered calibrated compatibility score produces:

P(S=s_i | y,map,wind) proportional to pi_i * exp(compat(z_y,z_i)/tau).

The output remains a normalized probability over the original PMFS source cells.

## 7. Why the current D0 is relevant

The linear paired-view generalized-eigen representation uses same-source pairing but no explicit source-class discrimination objective.

With train-source-only hyperparameter selection and completely heldout source classes, it improves full-168-support proper log score by roughly one bit/target over PCA+KRR and other ordinary linear baselines.

This is evidence that cross-realization shared moments contain transferable source information beyond ordinary low-rank variance.

## 8. Theory boundary

The theorem above is a moment decomposition, not a full nonlinear identifiability theorem.

Recent ICML/ICLR 2025 work provides far-domain motivation for identifiable multi-view and content/style representations, but their assumptions must not be copied verbatim onto turbulent plume data.

The mainline may use 'identifiability' only if D1 establishes a defensible mapping between plume repeated views and the required assumptions. Otherwise use the safer phrase 'repeated-realization invariant source representation'.