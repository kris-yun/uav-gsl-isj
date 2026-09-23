# M1 v2 — Transition-KL Credal PMFS

Date: 2026-09-23
Status: DERIVED / WAITING FOR REPAIRED-BASELINE FALSIFICATION
Parent branch: research/maximin-transport-design-v1

## 1. Main scientific thesis

PMFS currently treats each candidate-source filament simulator as one precise forward model.

M1-v2 replaces that point forward model with a **distributionally robust transport set** around the PMFS filament transition kernel. The output is not a bank of hand-picked plume models and not a new entropy score. It is a **set-valued forward probability map** that contains the outcomes of admissible transport mismatch.

The resulting source representation is a **credal source map**:

- each candidate source has a range of observation likelihoods rather than one exact likelihood;
- source posterior probability has lower/upper bounds;
- a measurement position is valuable only when source identity remains distinguishable under the worst admissible transport law;
- source declaration is permitted only when source dominance survives the ambiguity set.

The recognizable PMFS shell remains:
candidate sources -> plume/hit maps -> source probability map -> movement -> online update.

The scientific assumption changes from:
"one simulated plume is trusted"

to:
"the simulator is a nominal transport law and reality may lie in a calibrated neighborhood around it."

## 2. Remote-field parent

Primary parent:
Shafiei, Jesawada, Friston, Russo,
"Distributionally robust free energy principle for decision-making,"
Nature Communications, published 17 Dec 2025 / volume 17 (2026), article 707.
DOI: 10.1038/s41467-025-67348-6.

Their central transferable idea is to put a KL ambiguity set around a learned/environment transition model and choose decisions against the worst environment in that set.

Important: we do NOT claim distributionally robust transition kernels are new. The novelty candidate is their transport-native use inside PMFS source inference and active source identifiability.

## 3. Exact connection to the official PMFS filament dynamics

Official PMFS uses:

    velocity = wind.dataAt(cell) + Normal(0, noiseSTDev)^2
    newPos = position + deltaTime * velocity

Ignoring obstacle clipping for one proposed move, at position z:

    X_{k+1} | X_k=z ~ N(z + dt*w(z), dt^2*sigma^2 I)

where sigma = noiseSTDev.

If the actual drift is w(z)+delta_w(z), with unchanged covariance:

    K_delta(.|z) = N(z + dt*(w+delta_w), dt^2*sigma^2 I)

and the KL divergence is exactly

    D_KL(K_delta || K_0)
      = 0.5 * (dt*delta_w)^T (dt^2*sigma^2 I)^(-1) (dt*delta_w)
      = ||delta_w||^2 / (2 sigma^2).

Important consequence:

    ||delta_w|| <= sigma * sqrt(2 eta)

for a one-step KL ambiguity radius eta.

The time step cancels. Thus eta has a direct PMFS-native velocity-error interpretation rather than being an arbitrary "robustness temperature".

For the official sigma=0.5 m/s:
- eta=0.02 corresponds to |delta_w| <= 0.10 m/s;
- eta=0.08 corresponds to <= 0.20 m/s;
- eta=0.125 corresponds to <= 0.25 m/s;
- eta=0.50 corresponds to <= 0.50 m/s.

Obstacle handling in PMFS is a deterministic transformation of the proposed move. By data processing, applying that deterministic wall/path mapping cannot increase KL divergence. Therefore the pre-obstacle Gaussian expression is a conservative upper control on the resulting transition mismatch.

## 4. Distributionally robust transition operator

For nominal discrete transition probabilities p_j = K_0(j|z), define

    B_eta(p) = {q: KL(q||p) <= eta}.

For any next-state value function V(j),

    sup_{q in B_eta(p)} E_q[V]
      = inf_{lambda>0}
          lambda * eta
          + lambda * log(sum_j p_j exp(V_j/lambda)).

Similarly,

    inf_{q in B_eta(p)} E_q[V]
      = - inf_{lambda>0}
          lambda * eta
          + lambda * log(sum_j p_j exp(-V_j/lambda)).

Thus the adversarial transition does NOT require enumerating a bank of plume models.
The inner worst-case step reduces to scalar convex optimization.

This is the key computational bridge from DR-FREE-style transition ambiguity to the PMFS grid/filament model.

## 5. Target full forward object

For candidate source s, the intended full method computes robust occupancy/hit envelopes

    h_s^-(x) <= h_s^true(x) <= h_s^+(x)

under all admissible transition kernels.

The exact multi-filament PMFS hit event ("at least one active filament occupies a cell at a recorded timestep") needs careful treatment. Do NOT claim this part is solved by the single-filament Bellman relation without validation.

Two implementation levels are therefore separated:

### Level A — conservative hit-law contraction probe

Start from nominal PMFS hit probability h_s(x).

Use a KL ambiguity set directly on the induced Bernoulli observation law:

    C_eta(h) = {q in [0,1] : kl_Bern(q||h) <= eta}.

This gives an exact scalar interval [l,u] for the relaxed hit-law ambiguity set.

This is the first offline falsification interface because it requires only frozen candidate hit maps.

It is NOT yet the final transport-native implementation.

### Level B — transition-native robust filament propagation

Construct a discrete PMFS transition kernel from the same wind, sigma and obstacle geometry; solve lower/upper occupancy propagation under per-state KL transition balls; then map the resulting occupancy envelopes to PMFS's any-filament hit convention.

Only Level B can support the strongest paper claim.

Advance from A to B only if A gives a source-rank positive signal.

## 6. Exact robust source-information objective for Level A

For a measurement cell x:

- prior source weights: pi_s;
- nominal hit probabilities: h_s(x);
- robust intervals from Bernoulli KL balls:
  [l_s(x), u_s(x)].

Define the robust binary source information:

    RMI(x)
      = min_{q_s in [l_s,u_s]}
          I_pi(S;Y)

where Y|S=s ~ Bernoulli(q_s).

For fixed pi, mutual information is convex in the observation channel. For the binary rectangular ambiguity set, the minimizer has a simple consensus form.

Let

    q_s*(c) = clip(c, l_s, u_s).

Choose c satisfying

    c = sum_s pi_s q_s*(c).

Then

    RMI(x) = I_pi(S;Y; q*).

This can be solved by one-dimensional bisection.

Consequences:

- if all candidate intervals share a common overlap, RMI=0;
- a cell with huge nominal variance can become useless if admissible transport mismatch can make all candidate hit probabilities agree;
- a modest nominal-information cell can outrank it if its source separation survives ambiguity.

This directly targets the pathology observed in the killed native-candidate-variance probe:
"simulator-discriminative" need not mean "reality-identifying."

## 7. Exact credal posterior bounds for one hit/miss observation

After observing y in {0,1}, each candidate likelihood lies in an interval.

If y=1:
    L_s in [l_s,u_s].

If y=0:
    L_s in [1-u_s, 1-l_s].

For prior pi_s and rectangular likelihood intervals [a_s,b_s], posterior bounds for candidate s are:

    lower P(s|y)
      = pi_s a_s /
        (pi_s a_s + sum_{j!=s} pi_j b_j)

    upper P(s|y)
      = pi_s b_s /
        (pi_s b_s + sum_{j!=s} pi_j a_j).

Therefore a set-valued source map can be updated analytically without Monte Carlo.

This gives M1-v2 three coupled objects from ONE ambiguity principle:

1. robust forward hit envelope;
2. robust active-identifiability objective;
3. robust source-belief / declaration bounds.

That coupling is important. If only item 2 is used, the contribution collapses back toward "another acquisition function."

## 8. Source declaration rule

A candidate s can be called robustly dominant only if, for example,

    lower P(s) > max_{j!=s} upper P(j).

This is deliberately stronger than PMFS's point-posterior confidence.

Do not fix this exact stopping rule before data; compare it against coverage/abstention metrics and derive the final declaration rule source-blind.

A 2026 auxiliary direction exists:
W. Zhou, A. Orfanoudaki, S. Zhu,
"Conformalized Decision Risk Assessment," ICLR 2026.

This may later provide a principled risk certificate for declaration/abstention, but it is NOT part of M1-v2 until the main source-rank gate passes.

## 9. Ambiguity-radius calibration

This is the main unresolved technical risk.

NOT ALLOWED:
- tune eta against truth-source rank;
- one eta per House selected after looking at source truth;
- call eta a physical quantity without a source-blind calibration route.

Candidate source-blind signal:

    r_t = observed_wind_t - predicted_wind_before_assimilating_t

and

    e_t = ||r_t||^2 / (2 sigma^2).

The "before assimilating" requirement prevents trivial self-fit residuals.

Potential auxiliary parent:
W. Zhou, S. Zhu,
"Calibrating Decision Robustness via Inverse Conformal Risk Control,"
ICML 2026.

ICRC is relevant because it addresses the otherwise arbitrary choice of robustness radius. It can only become auxiliary A1 if we can define calibration loss/regret without source truth at deployment.

For the first offline probe, use a predeclared eta sensitivity panel and never select the best eta by truth.

## 10. Novelty collisions / claims forbidden

Already-known close neighbors mean we must NOT claim:

- first OSL method robust to model mismatch;
- first use of multiple/wrong plume models;
- first information-driven active OSL;
- first use of Renyi information in OSL;
- first robust optimal experimental design for inverse problems.

Specific collisions:

1. Wiedemann et al. 2019 — model mismatch in model-based GSL.
2. Piro et al., Journal of Turbulence 2025 — many wrong plume models, ranking/blending.
3. Jia et al., Entropy 2025 — Renyi-infotaxis in OSL.
4. Robust nonlinear-PDE OED exists outside GSL.

The candidate survives novelty audit only as:

    distributionally robust TRANSPORT-KERNEL uncertainty
    -> set-valued PMFS forward map
    -> worst-case source identifiability
    -> credal source posterior / declaration

inside closed-loop mobile GSL.

## 11. Hard falsification after repaired baseline arrives

### F0 — mathematical sanity
No GSL performance claim.

Verify:
- eta=0 gives nominal hit probabilities and nominal MI;
- interval width grows monotonically with eta;
- robust MI never exceeds nominal MI;
- common interval overlap gives robust MI zero;
- posterior point interval collapses to Bayes when eta=0;
- runtime scales acceptably with candidate count.

### F1 — frozen-map source-rank intervention

Using repaired Native PMFS candidate hit maps and the exact same observed measurements:

Compare:
A. nominal PMFS scoring/update;
B. nominal variance / nominal Shannon information;
C. Level-A credal update + robust MI.

Truth-containing candidate rank is the primary endpoint.

No eta chosen using truth.
Report the full predeclared eta panel.

### F2 — mismatch stress

Create predeclared forward mismatch that does NOT use the true source:
- wind-vector bias/rotation/scale perturbations;
- noiseSTDev mismatch;
- selected official-vs-adapted transport differences where scientifically valid.

Expected signature:
- matched simulator: robust method should approach nominal as eta shrinks;
- mismatched simulator: robust method should degrade more slowly than nominal.

### F3 — destructive null

Destroy the relation between transport uncertainty and spatial forward structure while preserving simple marginals.

The robust advantage must disappear.

### F4 — Level-B investment gate

Implement transition-native robust filament propagation ONLY if F1/F2 improve truth-source rank on multiple independent plume realizations.

## 12. Kill conditions

Kill M1-v2 if any is true:

- Level-A source-rank signal is absent after baseline repair;
- improvement is endpoint-only;
- improvement requires truth-tuned eta;
- robust MI is effectively just monotonic re-ranking of nominal entropy;
- advantage survives destructive transport nulls;
- repaired Native PMFS eliminates the observed fragility entirely and no mismatch stress exposes a robust-identifiability benefit;
- full transition-native propagation is computationally incompatible with PMFS online use and no principled approximation preserves the signal.

## 13. Current status

Compared with M1-v1, this is materially stronger:

M1-v1:
    "use maximin / Sibson information."

M1-v2:
    "wrap the PMFS filament transition law itself in a KL ambiguity set;
     propagate that uncertainty into hit-map sets, source-belief sets,
     active identifiability, and declaration."

This is the version worth testing when the repaired Native PMFS artifacts arrive.
