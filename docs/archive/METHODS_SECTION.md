# Methods Section (Draft)

## 3. Method

### 3.1 Overview

We formulate UAV gas source localization as a sequential decision problem in which a UAV equipped with gas and wind sensors must locate an emission source while deciding when to terminate the search. Our framework consists of three integrated components: (i) a Bayesian posterior update for source estimation, (ii) a risk-adjusted information-directed search strategy, and (iii) an anytime-valid stopping criterion based on e-processes. These components are unified through Blackwell's theory of approachability.

### 3.2 Bayesian Posterior Update

Let $s^* \in \mathcal{X} \subset \mathbb{R}^2$ denote the unknown source position. At each time step $t$, the UAV at position $x_t$ receives a gas concentration reading $z_t$ and a wind vector measurement $w_t$. The posterior distribution over source positions is updated via Bayes' rule:

$$\pi_{t+1}(s) \propto \pi_t(s) \cdot p(z_t \mid x_t, s, w_t)$$

where $p(z_t \mid x_t, s, w_t)$ is the observation likelihood. We employ a wind-relative spatial field estimation (WATS) approach that builds a nonparametric estimate of the concentration field conditioned on wind direction. The posterior is maintained as an ensemble of particles, enabling uncertainty quantification without parametric assumptions.

The MAP estimate is obtained as $\hat{s}_t = \arg\max_s \pi_t(s)$, and the posterior entropy is computed as $H(\pi_t) = -\int \pi_t(s) \log \pi_t(s) \, ds$.

### 3.3 Search Strategy: Risk-Adjusted Information-Directed Sampling

The UAV selects its next measurement position to maximize information gain while controlling risk. Define the expected information gain (EIG) of action $a$ as:

$$\text{EIG}(a \mid \pi_t) = H(\pi_t) - \mathbb{E}_{z \sim p(z \mid a, \pi_t)}[H(\pi_{t+1})]$$

A standard information-theoretic search (Infotaxis) selects $a^* = \arg\max_a \text{EIG}(a \mid \pi_t)$. However, this risk-neutral approach may lead to overly aggressive exploration in uncertain environments.

We employ a risk-adjusted variant, which we call W-RAIG (Weighted Risk-Adjusted Information Gain):

$$a^* = \arg\max_a \left[ \text{EIG}(a \mid \pi_t) - \beta \sqrt{\text{Var}[\text{EIG}(a \mid \pi_t)]} \right]$$

where $\beta > 0$ controls the risk aversion parameter. When $\beta = 0$, this reduces to standard Infotaxis; as $\beta \to \infty$, the strategy becomes maximally conservative.

**Connection to Blackwell Approachability.** In the Blackwell framework, the UAV (player) chooses action $a_t$ while the environment (adversary) determines conditions $b_t$ (wind patterns, plume structure). The vector-valued payoff $m(a_t, b_t) = (\text{coverage}_t, \text{efficiency}_t)$ measures whether the MAP estimate is within distance $\varepsilon$ of the source. The W-RAIG strategy can be interpreted as approximately minimizing the distance to the target set $\mathcal{C} = \{(c, e) : c \geq 1-\alpha, e \geq -\varepsilon\}$, which is the geometric solution to Blackwell's approachability problem.

### 3.4 Stopping Criterion: Anytime-Valid e-Process

A critical and under-studied problem in GSL is deciding *when* to stop searching. Existing methods either run for a fixed number of steps or timeout—neither provides guarantees on false termination probability. We address this by constructing an anytime-valid e-process from posterior convergence indicators.

#### 3.4.1 Sequential Hypothesis Test

We formulate the stopping decision as a sequential hypothesis test:

- $H_0$: "The MAP estimate has not converged to the source" ($\hat{s}_t \notin B_\varepsilon(s^*)$)
- $H_1$: "The MAP estimate has converged" ($\hat{s}_t \in B_\varepsilon(s^*)$)

#### 3.4.2 e-Value Construction

At each step $t$, we compute an e-value $E_t$ that measures evidence for $H_1$ versus $H_0$:

$$E_t = \exp\left(\eta \cdot (\theta - r_t)\right)$$

where $r_t = \|\hat{s}_t - \hat{s}_{t-1}\|$ is the MAP residual (movement between consecutive MAP estimates), $\theta$ is the convergence threshold, and $\eta > 0$ is a learning rate.

The e-value has the following properties:
- When $r_t < \theta$ (converging): $E_t > 1$ (evidence for $H_1$)
- When $r_t > \theta$ (not converged): $E_t < 1$ (evidence for $H_0$)
- Under $H_0$: $\mathbb{E}[E_t] \leq 1$ (super-martingale condition)

#### 3.4.3 e-Process and Stopping Rule

The e-process is the cumulative product of e-values:

$$M_T = \prod_{t=1}^{T} E_t$$

The stopping rule is:

$$\tau = \min\{T : M_T \geq 1/\delta\}$$

**Theorem 1 (Anytime-Valid Stopping).** Under the super-martingale condition $\mathbb{E}[E_t \mid \mathcal{F}_{t-1}] \leq 1$ for all $t$:

$$\mathbb{P}\left(\sup_T M_T \geq 1/\delta\right) \leq \delta$$

This is a consequence of Ville's inequality for non-negative super-martingales. The key advantage over conformal prediction approaches is that **no exchangeability assumption is required**—the guarantee holds for any stopping time $\tau$, including data-dependent stopping rules.

#### 3.4.4 Practical Implementation

We implement a warm-up period of $N = 15$ steps during which the e-process does not evaluate, allowing the posterior to burn in. After the warm-up, the e-process accumulates evidence from MAP residuals. The convergence threshold $\theta$ and significance level $\delta$ are set as parameters (default: $\theta = 1.5$m, $\delta = 0.10$).

The DDM (Drift-Diffusion Model) component provides a complementary evidence accumulation mechanism using posterior entropy change rates as the log-likelihood ratio, with a 5-step warm-up to prevent false positives in the initial search phase.

### 3.5 Unified Framework via Blackwell Approachability

The three components—search, stopping, and risk control—are unified through Blackwell's theory of approachability [Principato & Stoltz, 2025]. We model the GSL problem as a repeated two-player vector-valued game:

- **Player (UAV)**: chooses action $a_t \in \mathcal{A}$ (next position or STOP)
- **Adversary (Environment)**: chooses $b_t \in \mathcal{B}$ (wind/plume conditions)
- **Payoff**: $m(a_t, b_t) = (\text{coverage}_t, \text{efficiency}_t) \in \mathbb{R}^2$

**Proposition 0 (Approachability).** Under the conditions that (i) the posterior update is consistent ($\pi_t \to \delta_{s^*}$ as $t \to \infty$ under identifiability) and (ii) the action space is rich enough ($\exists a : \text{EIG}(a \mid \pi_t) > 0$ for all $\pi_t \neq \delta_{s^*}$), the target set $\mathcal{C}$ is approachable by Blackwell's theorem.

This means that for any sequence of environment conditions (adversary actions), there exists a UAV strategy such that the long-run average payoff converges to $\mathcal{C}$—i.e., the UAV achieves both sufficient coverage and efficiency.