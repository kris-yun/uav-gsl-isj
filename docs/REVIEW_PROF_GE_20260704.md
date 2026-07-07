============================================================
REVIEW REPORT: UAV GSL Paper for IEEE Sensors Journal
Reviewer: Prof. 葛泉波 (Ge Quanbo), NUIST
Date: 2026-07-04
Subject: Event-Driven Bayesian Gas Source Localization
============================================================

## OVERALL ASSESSMENT

Current state: NOT SUBMITTABLE. The paper has a genuinely interesting core
idea (event-driven Bayesian inference for filament-based gas dispersion),
but is undermined by three fatal gaps: (1) mathematical errors in theorems,
(2) a complete code-theory disconnect where the implementation bears no
resemblance to the claimed Poisson binary event model, and (3) experimental
data that was generated under engineering heuristics, not the proposed
theoretical framework.

The existing dual-perspective review (DUAL_PERSPECTIVE_REVIEW_20260704.md)
is largely correct in its diagnoses. This report provides the technical
depth needed to actually fix the problems.

============================================================
## PART 1: MATHEMATICAL FRAMEWORK (V3) — THEOREM-BY-THEOREM AUDIT
============================================================

### 1.1 Lemma 1: Non-degenerate Identifiability
File: MATHEMATICAL_FRAMEWORK_V3.tex, lines ~35-40

STATUS: **Stated correctly but proof sketch is absent.**

The claim that kappa_id(s,r) > 0 under ||w||>0, lambda_0>0 is physically
intuitive: with nonzero wind, the cosine modulation creates directional
asymmetry in the rate function, making distinct source positions yield
distinguishable rate fields. The decay rate exp(-r/ell) is also correct
since the exponential kernel's distinguishability degrades with source
separation relative to the length scale.

ISSUES:
- The proof is missing. For ISJ, you need at least a proof sketch showing
  that the FIM is positive definite for r < r_max. Specifically: compute
  the FIM integral for the Bernoulli model and show that the angular
  modulation from wind breaks the rotational symmetry that would otherwise
  make the FIM singular.
- Definition 1 defines Fisher Information for a SINGLE observation at
  position x, but Lemma 1's coefficient integrates over the entire domain
  X. The sequential, adaptive nature of where x_t is chosen is ignored.
  In the actual UAV setting, x_t is chosen by the algorithm, not
  uniformly distributed over X. The identifiability coefficient should
  account for the sampling distribution induced by the search policy.

VERDICT: Fixable. Add a proof sketch and clarify the sampling model.

### 1.2 Theorem 1: ED-EIG Quantitative Lower Bound
File: MATHEMATICAL_FRAMEWORK_V3.tex, lines ~45-55

STATUS: **Contains a quantitative error.**

The bound states:
  ED-EIG(x|pi_t) >= p_bar(1-p_bar) * (lambda(x,s1)-lambda(x,s2))^2 * dt^2 / 2
                     * exp(-max(lambda(x,s1), lambda(x,s2)) * dt)

ERROR ANALYSIS:
- The EIG for a binary observation is:
  EIG = H(d|x,pi) - E_s[H(d|x,s)]
  where H is binary entropy.
- For small lambda*dt: P(d=1) ~ lambda*dt, so binary entropy H ~ lambda*dt*log(1/(lambda*dt))
- The difference (lambda1-lambda2)*dt drives the information gain
- The stated bound scales as O(dt^2), which means information per unit
  time scales as O(dt) -> 0 as dt -> 0.

This is CORRECT but MISLEADING. The paper claims "When lambda*dt->0:
bound scales as O(dt^2)" and then asserts binary model "maintains
positive information in zero-concentration regimes." But the bound
goes to zero! The paper conflates two regimes:
  (a) lambda > 0 but small (far from source): bound ~ dt^2 > 0 but tiny
  (b) lambda = 0 (truly no gas): bound = 0, no information

The Remark comparing with continuous model is also flawed:
  "Under event model, when d=0: I(s;d=0|x) >= (lambda2-lambda1)*dt * exp(-lambda_max*dt) > 0"
This only holds when lambda1 != lambda2, i.e., when the two candidate
sources produce different rates at x. If both candidates produce
lambda ~ 0 at x (far from both), then the information gain is
negligible regardless of model.

FIX: Separate the claims. The binary model IS superior to continuous
for the intermittent-contact regime, but the bound needs to be:
  (a) Tighter: use the exact KL(Bern(p1), Bern(p2)) instead of the
      quadratic approximation
  (b) Honest: acknowledge that information vanishes when ALL candidates
      have lambda ~ 0 at the observation location
  (c) The real insight is that d=0 provides info proportional to the
      DIFFERENCE in rates, not the absolute level

### 1.3 Theorem 2: Non-Detection Information Bound
File: MATHEMATICAL_FRAMEWORK_V3.tex, lines ~60-75

STATUS: **Correct in spirit, bound needs tighter derivation.**

The KL divergence formula is correct:
  I(s;d=0|x,pi_t) = KL(pi_t || pi_t^{(0)})
  where pi_t^{(0)}(s) prop pi_t(s) * exp(-lambda(x,s)*dt)

The Pinsker-type lower bound:
  I >= (E_pi[lambda] - E_{pi^(0)}[lambda])^2 / (2 * sup_s lambda(x,s))

is a valid application of the chi-square / Pinsker inequality direction.

ISSUE: The claim "I ~ O(lambda_max * dt)" when x is near high-probability
region needs justification. For small dt:
  pi_t^{(0)}(s) prop pi_t(s) * exp(-lambda(x,s)*dt) ~ pi_t(s)(1 - lambda(x,s)*dt)
The KL is approximately dt^2 * Var_{pi_t}[lambda(x,s)] / 2 for small dt.
This is O(dt^2), not O(lambda_max * dt) as claimed.

FIX: Correct the asymptotic. The information from non-detection scales
as dt^2 * Var(lambda) for small dt. The correct scaling with lambda_max
is: I ~ O(lambda_max^2 * dt^2) when lambda varies proportionally to
lambda_max.

### 1.4 Theorem 3: Adaptive Exponential Contraction
File: MATHEMATICAL_FRAMEWORK_V3.tex, lines ~85-100

STATUS: **Standard result, but several issues.**

The contraction rate E[R_t^2] <= R_0^2 * exp(-c1 * sum D(pi_k)^2 * dt) + c2/sqrt(N)

ISSUES:
(a) N is undefined. If N = number of observations, then c2/sqrt(N) is
    a standard parametric rate floor. But the paper says "bounded by
    sensor resolution c2/sqrt(N)" which conflates sample size with
    sensor precision.

(b) The proof requires the likelihood to be correctly specified. Since
    the code doesn't use the Poisson binary model, this theorem doesn't
    apply to the actual system.

(c) The "adaptive" claim (rate adapts to posterior geometry via D(pi_k))
    is standard in Bayesian asymptotics (see van der Vaart, Asymptotic
    Statistics, Ch. 10). What's the GSL-specific contribution?

(d) The distinction between "early fast exclusion" and "late fine
    discrimination" is a direct consequence of D(pi) decreasing as
    the posterior concentrates. This is well-known. The contribution
    would be in QUANTIFYING D(pi) for the specific Poisson binary
    model on a filament-based plume.

FIX: Either (a) derive explicit expressions for D(pi) under the
Poisson binary model with filament arrival rates, showing how the
GSL-specific physics affects contraction, or (b) remove this theorem
and cite standard Bayesian consistency results.

### 1.5 Theorem 4: Posterior e-Process
File: MATHEMATICAL_FRAMEWORK_V3.tex, lines ~105-115

STATUS: **Standard result, correctly stated.**

M_t = prod_{k=1}^{t} P(d_k|x_k, s_hat_k) / P(d_k|x_k, s_0)

This is a likelihood ratio process. Under H_0 (source at s_0), E[M_t] = 1
by the tower property. Ville's inequality gives the anytime-valid bound.

CRITICAL ISSUE: This is a textbook application (Ville 1939, Doob 1953,
Ramdas et al. 2023 "Testing by Betting"). It is NOT a contribution.
Any reviewer familiar with sequential testing will recognize this
immediately.

The e-process as stated has a deeper problem: it tests whether the
source is at a specific point s_0 versus s_hat_k (which changes over
time). This is a composite-vs-composite test where the alternative
is data-dependent. The supermartingale property only holds under the
simple null H_0: s = s_0. If s_0 is chosen after seeing data (e.g.,
"the source is NOT at the MAP"), the test is invalid.

FIX: To make this a genuine contribution:
(a) Define s_0 as a fixed "null location" (e.g., the initial position
    or a region known to not contain the source)
(b) Show that the e-process provides a stopping rule that is BOTH
    anytime-valid and GSL-specific (e.g., "stop when we have evidence
    the source is within distance r of the MAP")
(c) Better yet: construct a CONFIDENCE SEQUENCE for the source location,
    not just a point hypothesis test

### 1.6 Proposition 1: Convergence Phase Transition
File: MATHEMATICAL_FRAMEWORK_V3.tex, lines ~120-130

STATUS: **Interesting claim, NO proof provided.**

The critical distance r* = ell * log(2) / log(1 + lambda_0*dt/ell)
is presented without derivation.

QUICK CHECK: For small dt, log(1 + lambda_0*dt/ell) ~ lambda_0*dt/ell,
so r* ~ ell^2 * log(2) / (lambda_0 * dt). This diverges as dt -> 0,
which is physically wrong (you shouldn't need infinite distance for
smaller time steps).

The formula appears to come from equating two rate scales: the spatial
decay (exp(-r/ell)) and the temporal accumulation (lambda_0*dt per step).
But the derivation is missing and the formula has suspicious behavior.

FIX: Provide the full derivation or remove this proposition.

============================================================
## PART 2: CODE-THEORY ALIGNMENT — THE CRITICAL MISMATCH
============================================================

### 2.1 What the Paper Claims

The paper (methodology.tex) states:
  "Binary detection d_t = 1{z_t > tau} with Poisson arrival rate:
   lambda(x,s) = lambda_0 exp(-||x-s||/ell)(1 + alpha_w cos theta)
   Detection probability: P(d=1) = 1 - exp(-lambda*dt)"
   
Key claim: "Non-detection at position x near candidate s yields large
lambda, small P(d=0), effectively excluding s. Every observation
provides information."

### 2.2 What the Code Actually Does

The code in OPGSL.cpp implements THREE separate systems that have
NO connection to the Poisson binary event model:

#### System A: plumeLogLikelihood() [lines 202-260]
This is the CORE of the posterior update. It computes:

  NO WIND: log_lik = -0.4 * dist - 0.15 * dist^2
  WITH WIND: log_lik = -d_par^2/(2*sig_par^2) - d_perp^2/(2*sig_perp^2)
                         - dz^2/(2*sig_z^2) - upwind_penalty - 0.15*dist

This is a GAUSSIAN-STYLE ANISOTROPIC KERNEL. It has:
  - No lambda_0 (baseline rate)
  - No exponential spatial decay exp(-||x-s||/ell)
  - No wind modulation term (1 + alpha_w * cos theta)
  - No Poisson rate lambda(x,s)
  - No binary event model P(d=1) = 1-exp(-lambda*dt)
  - No dt (time step) anywhere

The kernel returns a log-likelihood that is ALWAYS NEGATIVE and
monotonically decreasing with distance. It's essentially computing
a Gaussian mixture log-density, not a Poisson event likelihood.

#### System B: Posterior Update [lines 262-305]
The update rule is:

  grid[i][j][k] += weight * plumeLogLikelihood(...)

where:
  - Detection (c > 0.01): weight = clamp(sqrt(concentration) * 1.5, 0, 3)
  - Non-detection (c <= 0.01): weight = 0.001

THIS IS THE FATAL MISMATCH:

1. The weight for detections (1.5*sqrt(c)) is a PURE HEURISTIC.
   There is no theoretical justification. The sqrt() transformation
   and the constant 1.5 are engineering tuning parameters.

2. The weight for non-detections (0.001) is 1500x SMALLER than a
   typical detection weight (sqrt(0.5)*1.5 ~ 1.06). This means
   non-detection provides essentially ZERO information, directly
   contradicting the paper's central claim that "non-detection at
   position x near candidate s yields large lambda, small P(d=0),
   effectively excluding s."

3. The update is ADDITIVE in log-space (grid += weight * log_lik),
   not multiplicative as a proper Bayesian update should be. A
   proper update would be: grid[i][j][k] += log P(d_t | x_t, s_ij).

4. The temporal decay (0.995) applied every step is an engineering
   hack to prevent the posterior from becoming too peaked. There
   is no theoretical basis for this in the Poisson model.

#### System C: Stopping Criteria [lines 1330-1430]
The convergence check uses:
  - MAP distance < 1.5m
  - Best hit distance < 1.0m
  - Field entropy threshold
  - Best concentration > 0.08
  - CP stopping (shouldStop())
  - DDM stopping (shouldStop())
  - Fast exit: step >= 20, best_c > 0.05, near_best_hit, map_dist < 2.5
  - Hard timeout: 295 seconds

NONE of these use the e-process M_t from Theorem 4.
The e-process M_t is NEVER COMPUTED in the code.

The CP and DDM stopping criteria are independent engineering modules,
not connected to the Poisson binary event model or the e-process.

### 2.3 Quantifying the Mismatch

| Aspect | Paper Claims | Code Implements |
|--------|-------------|-----------------|
| Observation model | Binary d_t = 1{z_t > tau} | Continuous concentration z_t |
| Likelihood | Bernoulli: P(d=1)=1-exp(-lambda*dt) | Gaussian kernel: exp(-dist^2/sigma^2) |
| Rate function | lambda_0*exp(-r/ell)*(1+alpha*cos) | No explicit rate; kernel parameters |
| Non-detection info | P(d=0)=exp(-lambda*dt), substantial | weight=0.001, negligible |
| Posterior update | log P(d|x,s) additive | weight * log_lik (heuristic weight) |
| Stopping rule | e-process M_t via Ville's inequality | Engineering thresholds + CP/DDM |
| Key constant | lambda_0 (physical rate) | 1.5 (sqrt-weight tuning param) |

This is not a minor discrepancy. The paper's entire theoretical
framework is disconnected from the implementation. The experiments
were run using the HEURISTIC code, not the THEORETICAL model.

============================================================
## PART 3: MINIMUM VIABLE THEORETICAL CONTRIBUTION FOR ISJ
============================================================

### 3.1 What ISJ Wants

IEEE Sensors Journal values:
(a) Sensor-driven methodology with practical grounding
(b) Signal/information-theoretic analysis applied to sensing
(c) Clear improvement over baselines on realistic scenarios
(d) Reproducible methods with validated implementations

ISJ is NOT a theory journal. Elaborate proofs are not required,
but the theoretical claims MUST match the implementation.

### 3.2 Minimum Contribution Bar

For ISJ acceptance, the paper needs:

1. CORRECT LIKELIHOOD MODEL (non-negotiable)
   The Poisson binary event model must be IMPLEMENTED, not just
   theorized. This means: convert concentration to binary,
   compute lambda(x,s) from the rate function, and update the
   posterior using the correct Bernoulli likelihood.

2. ONE CLEAN THEOREM WITH PROOF
   The non-detection information result (Theorem 2 in v3) is
   the most novel and GSL-relevant. Tighten it:
   
   "Under the Poisson binary event model with rate lambda(x,s),
   a non-detection observation d=0 at position x reduces the
   posterior KL divergence by at least:
     Delta KL >= (dt^2/2) * Var_{pi_t}[lambda(x,s)]
   This is strictly positive whenever the posterior has not
   collapsed to a point mass, and is largest when x is chosen
   to maximize rate variance across candidate sources."
   
   This is provable, novel (in the GSL context), and directly
   motivates the NBV strategy.

3. EXPERIMENTAL VALIDATION ON POOLFS/VGR
   - Minimum 10 seeds per environment (reviewer expectation 2026)
   - Statistical tests (Wilcoxon signed-rank at minimum)
   - Include PMFS dataset for fair comparison
   - Report mean +- std for all metrics

4. CODE-THEORY ALIGNMENT
   The code MUST implement the model described in the paper.
   Period.

### 3.3 Sufficient Contribution (Acceptance Target)

To go from "minimum" to "strong accept":

(a) Domain-specific insight: "In filament-based gas dispersion,
    non-detection is informative" — formalize this with the
    Poisson model and show it leads to better search in
    intermittent-contact regimes.

(b) Novel stopping rule: Derive a GSL-specific stopping criterion
    from the posterior credible region (not the generic e-process
    from sequential testing). Something like: "Stop when the
    posterior 95% credible set has diameter < r_min."

(c) Clean ablation: Show that the Poisson binary model specifically
    (not just "simpler-is-better") outperforms the continuous
    Gaussian model, especially in weak-signal scenarios.

============================================================
## PART 4: CONCRETE CODE CHANGES TO ALIGN WITH POISSON MODEL
============================================================

### 4.1 Fix 1: Replace plumeLogLikelihood with Poisson Rate Model

CURRENT (Gaussian kernel):
  log_lik = -d_par^2/(2*sig_par^2) - d_perp^2/(2*sig_perp^2) - ...

PROPOSED (Poisson filament rate):
  float rateLambda(float sx, float sy, float sz,
                   float cx, float cy, float cz,
                   float wind_x, float wind_y) {
      float dx = cx - sx, dy = cy - sy, dz = cz - sz;
      float dist = sqrt(dx*dx + dy*dy + dz*dz);
      float wn = sqrt(wind_x*wind_x + wind_y*wind_y);
      float cos_theta = (wn > 0.05f) ? (dx*wind_x + dy*wind_y) / (dist * wn + 1e-6f) : 0.0f;
      return lambda_0 * exp(-dist / ell) * (1.0f + alpha_w * cos_theta);
  }

Parameters to estimate or set:
  - lambda_0: baseline filament arrival rate (from GADEN or calibration)
  - ell: correlation length (from plume statistics)
  - alpha_w: wind modulation depth (typically 0.3-0.7)

### 4.2 Fix 2: Replace Posterior Update with Bernoulli Log-Likelihood

CURRENT (heuristic weight * kernel):
  weight = (c > 0.01) ? clamp(sqrt(c)*1.5, 0, 3) : 0.001;
  grid[i][j][k] += weight * plumeLogLikelihood(...);

PROPOSED (Bernoulli update):
  // Convert to binary
  bool detected = (concentration > tau);
  float lambda_ij = rateLambda(sx, sy, sz, cx, cy, cz, wind_x, wind_y);
  float p_det = 1.0f - exp(-lambda_ij * dt);
  p_det = clamp(p_det, 1e-10f, 1.0f - 1e-10f);  // numerical safety
  
  float log_lik;
  if (detected) {
      log_lik = log(p_det);
  } else {
      log_lik = log(1.0f - p_det);  // = -lambda_ij * dt
  }
  grid[i][j][k] += log_lik;  // Proper Bayesian update

THIS IS THE SINGLE MOST IMPORTANT CHANGE. With this:
  - Non-detection at a cell with high lambda_ij gives large negative
    log_lik, strongly downweighting that source candidate
  - Detection gives positive log_lik proportional to the rate
  - The update is a proper Bayesian likelihood multiplication
    (additive in log space)
  - The temporal decay hack (0.995) can be REMOVED

### 4.3 Fix 3: Remove Heuristic Weights

The following parameters should be DELETED from the code:
  - ig_cfg_.exploration_weight = 0.3f;  (line 132)
  - ig_cfg_.wind_bonus = 0.5f;          (line 132)
  - ig_cfg_.uncertainty_weight = 0.4f;  (line 133)
  - ig_cfg_.visit_penalty = 0.2f;       (line 133)
  
These are all superseded by the proper Bayesian posterior.
The NBV (Next Best View) should be selected by maximizing
the expected information gain UNDER THE POISSON MODEL, not
under ad-hoc weight combinations.

### 4.4 Fix 4: Implement the e-Process

CURRENT: e-process not computed at all.

PROPOSED:
  // Track log-likelihood ratio for e-process
  float e_process_log_M = 0.0f;
  float s0_x = initial_guess_x, s0_y = initial_guess_y;  // null hypothesis
  
  void updateEProcess(float cx, float cy, float cz,
                      bool detected, float dt) {
      float lambda_hat = rateLambda(map_x, map_y, map_z,
                                     cx, cy, cz, wind_x, wind_y);
      float lambda_null = rateLambda(s0_x, s0_y, 0,
                                      cx, cy, cz, wind_x, wind_y);
      float p_hat = 1.0f - exp(-lambda_hat * dt);
      float p_null = 1.0f - exp(-lambda_null * dt);
      p_hat = clamp(p_hat, 1e-10f, 1.0f - 1e-10f);
      p_null = clamp(p_null, 1e-10f, 1.0f - 1e-10f);
      
      if (detected) {
          e_process_log_M += log(p_hat / p_null);
      } else {
          e_process_log_M += log((1.0f - p_hat) / (1.0f - p_null));
      }
  }
  
  bool shouldStopEProcess(float alpha = 0.05f) {
      return e_process_log_M > log(1.0f / alpha);
  }

### 4.5 Fix 5: Proper Stopping via Posterior Credible Region

CURRENT: Engineering thresholds (1.5m, entropy < 4, etc.)

PROPOSED:
  // Compute 95% credible region diameter from posterior
  float credibleRegionDiameter() {
      // Find set of cells containing 95% of posterior mass
      // Return bounding box diameter
      vector<float> probs;
      for each cell: probs.push_back(exp(grid[i][j][k]));
      sort descending;
      float cumsum = 0;
      float min_x=INF, max_x=-INF, min_y=INF, max_y=-INF;
      for each cell in sorted order:
          if cumsum < 0.95:
              update bounding box
          cumsum += prob
      return sqrt((max_x-min_x)^2 + (max_y-min_y)^2);
  }
  
  bool shouldStop(float r_min = 0.5f) {
      return credibleRegionDiameter() < r_min;
  }

============================================================
## PART 5: LITERATURE CONTEXT (2023-2026)
============================================================

### 5.1 E-Processes and Anytime-Valid Inference

The field is EXPLODING. Recent papers found via arXiv:

1. "Halt Fast! Early Stopping for Certified Robustness" (Cullen,
   Montague, Rubinstein, arXiv 2606.27694, 2026)
   - Uses e-processes for anytime-valid stopping with 20x sample
     reduction. Shows e-processes are practical for real systems.
   - RELEVANCE: Directly demonstrates that e-process stopping is
     viable. But this paper adds a META-LEARNED prior, which is
     the contribution, not the e-process itself.

2. "CELEUS: Certifiable and Efficient LLM Evaluation via E-Processes"
   (Zhou et al., arXiv 2606.20820, 2026)
   - Proves near-parametric contraction rates for e-process CIs.
   - RELEVANCE: Shows e-process CIs can shrink at optimal rates,
     supporting the contraction theorem in your framework.

3. "PACE: Anytime-Valid Acceptance Tests for Self-Evolving Agents"
   (arXiv 2606.08106, 2026)
   - E-process for sequential commit decisions. Prevents "p-hacking"
     in iterative self-improvement.
   - RELEVANCE: Analogy to GSL stopping: don't stop until you have
     DECISIVE evidence the source is localized.

4. "Anytime-Valid Federated Conformal RAG" (Dubey & Huo,
   arXiv 2605.29139, 2026)
   - Extends conformal prediction to anytime-valid sequential
     coverage. Shows naive composition fails.
   - RELEVANCE: Your CP stopping module is the naive version.
     This paper shows you need the summable deviation budget
     approach for proper anytime validity.

5. "Optimal Rates for Differentially Private Hypothesis Testing
   with E-values" (Jacobsen et al., arXiv 2605.28952, 2026)
   - Characterizes optimal e-power under privacy constraints.
   - RELEVANCE: Less directly relevant, but shows e-processes
     are becoming a standard tool.

KEY TAKEAWAY: Simply applying e-processes to GSL is NOT a
contribution in 2026. You need a GSL-specific construction.

### 5.2 Poisson Models for Gas Dispersion

- GADEN (Real Robot Experiment Simulator for Gas Dispersion, 2017+)
  uses filament-based dispersion, which naturally produces Poisson
  arrival statistics. Your model should be grounded in GADEN physics.
  
- Vergassola et al. (2007, Nature) "Infotaxis" uses a Poisson
  model for odor plume encounters: P(hit) = 1-exp(-lambda*dt).
  This is the ORIGINAL source for your binary event model.
  Cite this prominently.

- "Merging of Bayes and quasi-Bayes empirical Bayes for Poisson
  compound decisions" (Favaro & Fortini, arXiv 2607.02340, 2026)
  - Establishes posterior concentration rates for Poisson mixtures.
  - RELEVANCE: Your posterior contraction theorem (Thm 3) is a
    special case of this general framework. Cite and differentiate.

### 5.3 Recent GSL Methods in Top Venues

Key recent GSL references to position against:
- PMFS (Monroy et al., RAL 2023+): Particle-based, wind-relative
- SurgeCast (2024): Upwind tracking, wind-only
- WATS/Infotaxis variants (various 2023-2025)

None of these provide formal stopping guarantees or use event-driven
Bayesian inference. This IS your differentiation, IF you implement it
correctly.

============================================================
## PART 6: FINAL VERDICT AND ACTION PLAN
============================================================

### 6.1 Fatal Issues (Must Fix)

1. CODE-THEORY DISCONNECT: The entire posterior update system must
   be rewritten to use the Poisson binary event model. This is not
   optional; it's the foundation of the paper.

2. E-PROCESS NOT IMPLEMENTED: Either implement it or remove the
   claim. Presenting a theorem for something not implemented is
   scientific misconduct if submitted as experimental work.

3. THEOREM 1 BOUND ERROR: The O(dt^2) bound is correct but the
   interpretation is wrong. Fix the asymptotic analysis.

4. EXPERIMENTAL DATA INVALID: All experiments must be re-run with
   the corrected Poisson-model code. Minimum 10 seeds.

### 6.2 Serious Issues (Should Fix)

5. THEOREM 3 undefined N and inapplicable proof.
6. THEOREM 4 is a textbook result, not a contribution.
7. PROPOSITION 1 formula has suspicious dt->0 behavior, no proof.
8. Only 3 experimental seeds.

### 6.3 Suggested Rewrite Timeline

Week 1: Implement Poisson binary model in code (Fixes 1-2 above)
Week 2: Fix mathematical framework (Fixes 3, 5-7)
Week 3: Re-run experiments (10+ seeds, VGR + PMFS)
Week 4: Rewrite paper with new narrative
Week 5: Internal review + polish
Week 6: Submit

### 6.4 Honest Assessment

The core PHYSICAL INSIGHT is correct and interesting: gas filaments
arrive as discrete events, non-detection is informative, and a
Poisson binary model naturally captures this. This insight has not
been formalized in the GSL literature.

But the gap between insight and execution is enormous. The code
implements none of the theory. The proofs have errors. The experiments
were run on a different algorithm than what the paper describes.

The student needs to: (1) implement the actual model, (2) fix the
proofs, (3) re-run experiments. In that order. Theory without
implementation is empty; implementation without theory is blind.

============================================================
END OF REVIEW
============================================================
