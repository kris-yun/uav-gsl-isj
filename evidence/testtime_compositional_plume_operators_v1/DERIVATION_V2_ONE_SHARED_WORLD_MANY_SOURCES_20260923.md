# M7 Derivation v2 — One Shared Environment World, Many Counterfactual Sources

Date: 2026-09-23  
Branch: \`research/testtime-compositional-plume-operators-v1\`  
Status: **gas-specific second derivation; do not implement before O0 passes**

## 1. Inverse-source structure missing from the parent operator-splitting papers

The parent 2025–2026 compositional-operator literature asks:

> Given a new physical system/dynamics, which operator or operator composition explains its evolution?

PMFS asks a different inverse question:

> In one fixed real environment, which source hypothesis generated the measurements?

The environment is shared by all source hypotheses.

Therefore candidate-source forward models must not be independently adapted.

## 2. Shared environment latent

Let

\[
E_t
\]

denote the current transport environment/world state, containing:

- known wind field \(W_t\);
- obstacle geometry \(O\);
- frozen known numerical mechanisms;
- a latent/frozen composition of unresolved residual operators.

Write:

\[
\mathcal T_{E_t}
=
\mathcal B_O
\circ
\mathcal R_{z_t}
\circ
\mathcal D_0
\circ
\mathcal A_{W_t}
\]

where \(\mathcal R_{z_t}\) may itself be a short sequence/composition selected from a learned library.

Crucially:

\[
\boxed{
\mathcal T_{E_t}
\text{ is shared by every source candidate.}
}
\]

## 3. Source candidates as counterfactual interventions

Each PMFS source candidate changes only source injection:

\[
\mathcal J_s.
\]

The candidate forward model is

\[
\boxed{
C_s
=
\mathcal T_{E_t}
[
\mathcal J_s
].
}
\]

Thus PMFS source evaluation becomes:

\[
do(S=s)
\quad\text{under one shared environment world }E_t.
\]

This retains the PMFS source-candidate philosophy while making the environment representation modular and reusable.

## 4. Why per-source adaptation is physically wrong

An unconstrained learned forward method might solve

\[
z_s^\star
=
\arg\max_z
p(Y\mid s,z)
\]

separately for every candidate.

Then candidate score becomes

\[
\max_z p(Y\mid s,z).
\]

This allows each candidate source to choose a different transport world.

A wrong source can be rescued by an implausibly favorable transport composition.

That confounds:
- source uncertainty;
- environment/model uncertainty.

The physical world does not change when the hypothesis label changes.

Therefore M7 forbids source-specific environment compositions.

## 5. Source-blind shared environment inference

If the residual composition cannot be inferred from wind/geometry alone, infer it from past gas observations while marginalizing source uncertainty.

Let:
- \(z\): candidate environment/operator composition;
- \(\pi_t(s)\): current PMFS source belief;
- \(Y_{1:t}\): measurement history.

Define shared-environment evidence:

\[
\boxed{
\mathcal L_t(z)
=
\sum_s
\pi_{t^-}(s)
\,
p(
Y_{1:t}
\mid
\mathcal T_z,\mathcal J_s
)
}
\]

or log-sum-exp equivalent.

Then choose:

\[
\boxed{
z_t^\star
=
\arg\max_{z\in\mathcal Z}
\mathcal L_t(z).
}
\]

Only after \(z_t^\star\) is frozen do we update/rank individual sources:

\[
\pi_t(s)
\propto
\pi_{t^-}(s)
p(
Y_t
\mid
\mathcal T_{z_t^\star},\mathcal J_s
).
\]

No source truth is used.

## 6. Prequential version to avoid same-batch overfitting

Preferred first implementation:

At update \(t\):

1. use history through \(t-1\) to choose environment composition
   \[
   z_t^\star=f(Y_{1:t-1},W,O,\pi_{t-1});
   \]
2. freeze \(z_t^\star\);
3. receive/evaluate the next observation batch \(Y_t\);
4. score all source candidates under the same \(z_t^\star\).

This gives a clean scientific test:

> can a shared world model selected from the past improve prediction/source identity on future observations?

It prevents selecting a composition that directly overfits the same measurements used to rank the source.

## 7. Test-time operator composition

Let the residual library be

\[
\mathcal R
=
\{R_1,\ldots,R_K\}.
\]

A composition code may be:

\[
z=(k_1,\ldots,k_m,\alpha_1,\ldots,\alpha_m)
\]

with a deliberately small predeclared search depth.

The ICML-2026-style test-time computation searches over \(z\), but in M7:

- the objective is source-marginalized predictive evidence;
- the selected \(z\) becomes a single shared environment world;
- that world is reused across every PMFS source counterfactual.

This is the inverse-source-specific second derivation.

## 8. Strong no-overfitting baseline

Compare:

### Shared composition

\[
z^\star
=
\arg\max_z
\sum_s\pi(s)p(Y\mid s,z)
\]

then rank all \(s\) with the same \(z^\star\).

### Per-source oracle-like adaptation

\[
z_s^\star
=
\arg\max_z p(Y\mid s,z).
\]

The per-source version may fit observations better but should be treated as a **negative control**, not the proposed method.

Expected failure mode:
- broader candidate ambiguity;
- flatter source ranking;
- false sources rescued by source-specific transport explanations.

If shared composition offers no source-identifiability advantage, the gas-specific second derivation is unsupported.

## 9. Relationship to previous multiple-dispersion-model OSL

Important prior-art boundary:

Older and recent OSL work already uses:
- multiple predefined dispersion models;
- model weighting/ranking;
- joint source/model uncertainty.

Therefore M7 cannot claim:
- first source localization with multiple forward models;
- first joint source/model reasoning.

The distinction must be:

1. environment models are **compositions of reusable learned physical mechanisms**, not a fixed hand-enumerated plume-model bank;
2. unseen environment dynamics can be synthesized at test time from the mechanism library;
3. known wind/source/obstacle physics remain explicit;
4. one shared composition is used for all source interventions.

If experiments reduce M7 to choosing among a small static bank of hand-written plume models, the main novelty is lost.

## 10. PMFS probability-map integration

For each source update:

### Environment stage

\[
z_t^\star
=
\text{SharedWorldSelect}
(
Y_{<t},W_t,O,\pi_{t-1}
).
\]

### Candidate forward stage

For every source candidate \(s\):

\[
H_s
=
\text{SensorMap}
\left(
\mathcal T_{z_t^\star}
[
\mathcal J_s
]
\right).
\]

### PMFS belief stage

Use one frozen likelihood/compatibility rule:

\[
\pi_t(s)
\propto
\pi_{t-1}(s)L(Y_t,H_s).
\]

Initially keep Native PMFS source update if possible to isolate the forward-model effect.

## 11. New hard falsification signature

If M7 reaches O2/O3, compare:

A. Native PMFS;  
B. fixed analytical split;  
C. monolithic learned residual;  
D. per-source independently adapted operator composition;  
E. **shared-environment M7 composition**.

Hard scientific signature:

- D may reduce field error;
- E must produce better **truth-source rank / source separation** than D and C.

This would show that enforcing one physical world across counterfactual sources matters for inverse-source identification.

## 12. Why this elevates M7 to a world-model thesis

The object being inferred is no longer merely a plume map.

It is:

\[
\boxed{
\text{one reusable physical world model }E_t
}
\]

that supports many counterfactual queries:

\[
do(S=s_1),\ldots,do(S=s_N).
\]

This is a more natural “world model” interpretation for PMFS than an end-to-end source predictor.

The environment world is inferred once; source hypotheses are interventions into that world.

## 13. Kill conditions

Kill this second derivation if:

- source-specific operator adaptation does not hurt source identifiability;
- shared composition gives no source-rank advantage;
- the shared environment cannot be inferred source-blind;
- the selected composition varies wildly with tiny posterior/source changes;
- the method collapses into choosing among a static predefined model bank;
- candidate ranking improves only when the environment composition is tuned using source truth.

## 14. Current status

\`THEORY KEEP\`

Implementation order remains:

1. O0 analytical splitting;
2. O1 source-transferable residual mechanism;
3. only then O2 shared test-time environment composition;
4. O3 truth-source rank.
