# M1 derivation v2 — Transition-Ambiguous PMFS and Guaranteed Source Separability

Date: 2026-09-23  
Branch: \`research/maximin-transport-design-v1\`  
Status: **theory/interface derivation; wait for repaired Native baseline before truth-based test**

## 0. Main change after prior-art audit

Do **not** implement "Rényi/Sibson infotaxis" as the main idea.

Do **not** claim "DRO + gas + wind + sensor placement" as novel: Zi et al. already used distributionally robust optimization for fixed methane sensor placement under wind uncertainty (IEEE Sensors Journal 2022, DOI 10.1109/JSEN.2022.3214176).

The stronger candidate is:

> **Transition-Ambiguous PMFS:** put a physically calibrated ambiguity set on PMFS's stochastic filament transition law itself, propagate that uncertainty into candidate hit-map envelopes, and move only toward locations whose source-candidate separation survives the worst admissible transport perturbation.

This preserves the native PMFS probability-map / candidate-source / closed-loop shell.

## 1. Exact PMFS transport interface

Official \`humble\` PMFS moves each filament as

\`\`\`cpp
velocity = wind.dataAt(indices.x, indices.y)
         + Vector2(N(0, noiseSTDev), N(0, noiseSTDev));
newPos = filament.position + deltaTime * velocity;
\`\`\`

Before obstacle handling, the one-step stochastic dynamics are

\[
X_{k+1}=X_k+\Delta t\,[w(X_k)+\varepsilon_k],
\qquad
\varepsilon_k\sim \mathcal N(0,\sigma^2 I).
\]

Thus the nominal transition kernel at state \(x\) is

\[
P_0(\cdot|x)
=
\mathcal N(
x+\Delta t\,w(x),
\Delta t^2\sigma^2 I
).
\]

## 2. Physical meaning of a local KL ambiguity radius

Suppose the real local drift differs by \(\delta w(x)\), while keeping the same diffusion/noise covariance:

\[
P_{\delta w}(\cdot|x)
=
\mathcal N(
x+\Delta t[w(x)+\delta w(x)],
\Delta t^2\sigma^2 I
).
\]

For identical covariance Gaussians,

\[
\boxed{
D_{\rm KL}
(P_{\delta w}\Vert P_0)
=
\frac{\|\delta w(x)\|^2}{2\sigma^2}
}
\]

so \(\Delta t\) cancels.

Equivalently,

\[
\boxed{
\|\delta w(x)\|
\le
\sigma\sqrt{2\eta(x)}
}
\]

for a local KL radius \(\eta(x)\).

For official PMFS \(\sigma=\texttt{noiseSTDev}=0.5\):

- drift tolerance 0.05 m/s -> \(\eta=0.005\);
- 0.10 m/s -> \(\eta=0.02\);
- 0.20 m/s -> \(\eta=0.08\);
- 0.25 m/s -> \(\eta=0.125\);
- 0.50 m/s -> \(\eta=0.5\).

This is a physical interpretation, not permission to tune \(\eta\) from source truth.

## 3. Why a single whole-path KL ball is rejected

For a Markov path,

\[
D_{\rm KL}(Q_{0:H}\Vert P_{0:H})
=
\mathbb E_Q
\sum_{k=0}^{H-1}
D_{\rm KL}
(Q_k(\cdot|X_k)\Vert P_k(\cdot|X_k)).
\]

PMFS releases many filaments over warm-up + recording steps. A crude global path-KL budget grows with the transition count and can make the induced hit-probability envelope vacuous.

**Decision:** reject the global-path-ball implementation.

Use state-wise / one-step rectangular ambiguity:

\[
\mathcal U_i(\eta_i)
=
\{
q_i\in\Delta:
D_{\rm KL}(q_i\Vert p_i)\le\eta_i,
\operatorname{supp}(q_i)\subseteq\operatorname{supp}(p_i)
\}.
\]

The nominal discrete \(p_i\) must include PMFS obstacle / stopping behavior rather than only a free-space Gaussian.

## 4. Robust one-step expectation operator

For downstream value \(V(j)\),

\[
\underline{\mathcal T}_{\eta_i}V(i)
=
\inf_{q_i\in\mathcal U_i(\eta_i)}
\sum_j q_i(j)V(j)
\]

and

\[
\overline{\mathcal T}_{\eta_i}V(i)
=
\sup_{q_i\in\mathcal U_i(\eta_i)}
\sum_j q_i(j)V(j).
\]

For KL ambiguity these admit scalar dual forms:

\[
\underline{\mathcal T}_{\eta}V
=
\sup_{\lambda>0}
\left[
-\lambda\eta
-
\lambda\log
\sum_j p_j e^{-V_j/\lambda}
\right],
\]

\[
\overline{\mathcal T}_{\eta}V
=
\inf_{\lambda>0}
\left[
\lambda\eta
+
\lambda\log
\sum_j p_j e^{V_j/\lambda}
\right].
\]

Thus the inner adversary requires only a one-dimensional optimization per robust Bellman backup, not a trained neural model.

## 5. From transition ambiguity to candidate hit-map envelopes

For source candidate \(s\) and cell \(c\), seek

\[
\underline h_s(c)
\le
h_s^{\rm real}(c)
\le
\overline h_s(c).
\]

The final method should obtain these by propagating the local robust transition operator through the filament dynamics, with an absorbing outside state and PMFS obstacle semantics.

For a single filament of age \(a\), terminal occupancy bounds at \(c\) follow from robust DP with terminal value

\[
V_a(j)=\mathbf 1[j=c].
\]

Birth cohorts and PMFS's five-filaments-per-iteration rule can then be composed into bounds on the per-timestep event "at least one active filament occupies c", followed by the same recording-time average used by PMFS.

### Engineering warning

A separate robust DP for every source × measurement cell can be expensive. Before full implementation:

- exploit sparse/local transition support;
- restrict robust evaluation to open/visible movement cells when possible;
- cache transition kernels per wind update;
- benchmark a reduced-cell implementation first.

Do not silently replace this with arbitrary independent output intervals.

## 6. Robustify the quantity PMFS actually uses

Official PMFS computes

\[
V_{\rm native}(c)
=
\operatorname{Var}_{s\sim\pi}[h_s(c)].
\]

This is stored as \`varianceOfHitProb\` and is used by \`MovingStatePMFS::informationValue()\` during Search. The mutual-information alternative exists in source but is commented out at the movement-scoring line.

Given transport envelopes

\[
I_s(c)
=
[\underline h_s(c),\overline h_s(c)],
\]

define **Guaranteed Source Identifiability (GSI)**:

\[
\boxed{
V_{\rm GSI}(c)
=
\min_{q_s\in I_s(c)}
\operatorname{Var}_{s\sim\pi}[q_s]
}
\]

Interpretation:

> Nature uses admissible transport error to make different source hypotheses look as similar as possible. A cell is valuable only when source predictions remain separated after this worst-case collapse.

This directly targets the previously observed pathology that nominal candidate variance can be highly stable while selected cells still worsen truth-source rank.

## 7. Closed-form structure of the GSI inner problem

Let normalized weights \(w_s=\pi(s)\), \(\sum_s w_s=1\), and intervals \([l_s,u_s]\).

Solve

\[
\min_{l_s\le q_s\le u_s}
\left[
\sum_s w_s q_s^2
-
\left(\sum_s w_s q_s\right)^2
\right].
\]

This is a convex box-constrained quadratic problem.

At an optimum, with

\[
\mu=\sum_s w_s q_s,
\]

the KKT conditions imply

\[
\boxed{
q_s^\star
=
\operatorname{clip}(\mu,l_s,u_s)
}
\]

where \(\mu\) satisfies

\[
\boxed{
\mu
=
\sum_s
w_s
\operatorname{clip}(\mu,l_s,u_s).
}
\]

Consequences:

1. If all intervals have a common intersection, \(V_{\rm GSI}=0\): admissible transport error can erase source discrimination.
2. If they remain separated, \(V_{\rm GSI}>0\): the cell has guaranteed rather than merely nominal source information.
3. The inner problem is cheap: one scalar root/fixed-point solve plus a weighted variance.

## 8. Pairwise interpretation

For two source intervals

\[
I_a=[l_a,u_a],
\qquad
I_b=[l_b,u_b],
\]

the guaranteed Bernoulli-parameter gap is

\[
g_{ab}
=
\max(0,l_a-u_b,l_b-u_a).
\]

Overlapping intervals mean those two sources can be made observationally indistinguishable at that cell within the ambiguity budget.

GSI is the multi-candidate weighted analogue.

## 9. Source update: not frozen yet

The main idea can first be falsified through movement/source-identifiability without replacing PMFS's source score.

If a robust source update is later required, two predeclared options are:

### A. Worst-case PMFS compatibility

Native per-cell compatibility:

\[
r(o,h)=1-c\gamma|o-h|.
\]

Robust guarantee:

\[
r^{-}(o,[l,u])
=
1-c\gamma
\max(|o-l|,|o-u|).
\]

### B. Profile compatibility — diagnostic only

\[
r^{+}(o,[l,u])
=
1-c\gamma
\operatorname{dist}(o,[l,u]).
\]

B resembles partial identification and risks rewarding overly wide uncertainty sets; a previous generic partial-identification line already failed. Do not rescue M1 by choosing A/B after seeing truth.

## 10. Critical prior-art boundaries

### 10.1 Distributionally robust transition decision-making is not new

Shafiei et al., *Distributionally robust free energy principle for decision-making*, Nature Communications, 2025, DOI 10.1038/s41467-025-67348-6.

This is the remote-field parent idea, not our novelty.

### 10.2 Distributionally robust Markov models are not new

Li & Shapiro, *Rectangularity and Duality of Distributionally Robust Markov Decision Processes*, Mathematical Programming, 2025, DOI 10.1007/s10107-025-02297-y.

### 10.3 DRO gas sensor placement already exists

Zi et al., *Distributionally Robust Optimal Sensor Placement Method for Site-Scale Methane-Emission Monitoring*, IEEE Sensors Journal 22(23), 2022, DOI 10.1109/JSEN.2022.3214176.

They hedge fixed sensor placement against wind uncertainty and optimize worst-case detection performance.

Therefore do not claim:
- first DRO for gas sensing;
- first wind-uncertainty-aware robust sensor placement;
- first worst-case gas detector placement.

Remaining distinction:
- sequential mobile source localization;
- source-belief map rather than fixed leak-detection time;
- ambiguity on PMFS's **local filament transition law**;
- transport-induced hit-map envelopes for each source hypothesis;
- movement based on **worst-case source-candidate separability**.

### 10.4 Rényi information in OSL already exists

Jia et al., Entropy 2025, DOI 10.3390/e27080826.

Alpha/Rényi information itself is not the novelty.

### 10.5 Multiple wrong plume models in OSL already exist

Piro et al., Journal of Turbulence 2025, DOI 10.1080/14685248.2025.2492711.

Model ensembles / blending are not the novelty.

## 11. Hard falsification gates after Native PMFS recovery

### T0 — envelope non-vacuity

With source-blind physically plausible ambiguity:

- measure fractions of intervals that are near-point, partial, or nearly [0,1];
- **kill** if realistic ambiguity makes almost all source × cell envelopes vacuous.

### T1 — nominal-vs-guaranteed discriminability

At every frozen source update compare:

- Native \`varianceOfHitProb\`;
- \(V_{\rm GSI}\);
- random/reachable control.

Report top-k overlap, rank correlation, and cells where native variance is high but GSI is near zero.

This stage is source-blind.

### T2 — truth-source-rank intervention — HARD GATE

Using repaired Native PMFS and independent plume realizations, hold measurement budget fixed and compare observation selection driven by Native vs GSI.

Primary endpoint:

- truth-containing source-candidate rank.

No endpoint/top-5-centroid rescue.

### T3 — mismatch gradient

Predeclare matched / moderate / strong transport mismatch.

Expected mechanistic signature:

- matched: GSI approaches Native;
- moderate mismatch: GSI advantage increases;
- extreme mismatch: GSI becomes conservative / both eventually fail.

If performance does not covary with mismatch, the mechanism is doubtful.

### T4 — destructive null

Break spatial/transport coherence while preserving marginal interval widths.

GSI advantage should disappear.

## 12. Current verdict

This is materially stronger than the initial Sibson-MI idea because it modifies PMFS's actual stochastic transport assumption and its actual movement statistic.

The single biggest unresolved bottleneck is now:

> Can local transition ambiguity be propagated into candidate hit-map envelopes that are both computationally practical and non-vacuous?

Do not build the full closed-loop method until T0/T1 answer that question.
