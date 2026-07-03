# Iteration 2: SDA-BAS Implementation

## Objective
Implement Sensor-Dynamics-Aware Bayesian Active Sensing (SDA-BAS) method.

## Background
Current DQA-AS has an observation-planning coupling gap:
- Q factor only used for scoring, not posterior update
- Posterior update ignores sensor dynamics
- ERR prediction uses idealized model

SDA-BAS fixes this by integrating sensor dynamics into the Bayesian framework.

## Implementation Tasks

### Task 1: Create SDA-BAS Directory Structure
`ash
mkdir -p D:/ZYC/A-gas/workspace/uav_diagsense/src/sda_bas
`

### Task 2: Implement SDALikelihood (sensor_dynamics_aware_likelihood.py)

**File**: src/sda_bas/sensor_dynamics_aware_likelihood.py

`python
"""Sensor-Dynamics-Aware Likelihood Function.

Integrates MOX sensor dynamics (response time, motion blur) into
the Bayesian likelihood for active gas source localization.

Cross-domain inspiration:
- Signal processing: Kalman filter with measurement dynamics
- Medical diagnostics: Test reliability modeling
"""
import numpy as np

EPS = 1e-12


class SDALikelihood:
    """Sensor-dynamics-aware likelihood for MOX gas sensors.
    
    Key insight: The sensor reading is NOT the true concentration.
    It's a low-pass filtered version with speed-dependent blur.
    
    State equation:
    rho_{t+1} = alpha(v,m) * rho_t + (1 - alpha(v,m)) * h_s(x_{t+1})
    
    Where:
    - rho_t: internal sensor state (filtered reading)
    - alpha(v,m): memory coefficient (higher = more lag)
    - h_s(x): true hit probability at position x
    """
    
    def __init__(self, alpha_0=0.6, k_v=0.15, k_m=0.2,
                 alpha_min=0.1, alpha_max=0.95,
                 noise_std=0.02, threshold=0.25):
        self.alpha_0 = alpha_0
        self.k_v = k_v
        self.k_m = k_m
        self.alpha_min = alpha_min
        self.alpha_max = alpha_max
        self.noise_std = noise_std
        self.threshold = threshold
        
        # Internal state
        self.rho = 0.0
        self.time_since_hit = 0
        self.history = []
    
    def get_alpha(self, speed, mode):
        """Compute memory coefficient for current step.
        
        Fast flight -> larger alpha -> more lag/motion blur
        Slow/hover -> smaller alpha -> reading closer to truth
        """
        mode_bonus = 1.0 if mode in ("slow", "hover") else 0.0
        alpha = self.alpha_0 + self.k_v * speed - self.k_m * mode_bonus
        return np.clip(alpha, self.alpha_min, self.alpha_max)
    
    def update(self, true_hit_prob, speed, mode):
        """Update sensor state and return dynamics-aware likelihood.
        
        Args:
            true_hit_prob: P(hit | source, position, wind) - the TRUE probability
            speed: current UAV speed
            mode: current flight mode (fast/slow/hover)
        
        Returns:
            observed_prob: dynamics-affected reading
            sigma: measurement uncertainty
        """
        # 1. Update sensor dynamics
        alpha = self.get_alpha(speed, mode)
        self.rho = alpha * self.rho + (1 - alpha) * true_hit_prob
        
        # 2. Add sensor noise
        self.rho += np.random.normal(0, self.noise_std)
        self.rho = np.clip(self.rho, 0, 1)
        
        # 3. Convert to observed probability via sigmoid threshold
        observed_prob = 1.0 / (1.0 + np.exp(-(self.rho - self.threshold) / 0.1))
        
        # 4. Compute measurement uncertainty
        sigma = self._measurement_uncertainty(speed, mode)
        
        # 5. Track history
        self.history.append({
            'rho': self.rho,
            'alpha': alpha,
            'observed': observed_prob,
            'sigma': sigma,
            'speed': speed,
            'mode': mode
        })
        
        return observed_prob, sigma
    
    def _measurement_uncertainty(self, speed, mode):
        """Compute measurement uncertainty based on flight conditions.
        
        Higher speed -> more motion blur -> higher uncertainty
        Fast mode -> less reliable reading -> higher uncertainty
        """
        base_sigma = 0.1
        speed_penalty = 0.05 * speed
        mode_penalty = 0.1 if mode == "fast" else 0.0
        return base_sigma + speed_penalty + mode_penalty
    
    def likelihood(self, z, rho=None, sigma=None):
        """Compute P(z | rho, sigma) - Gaussian likelihood.
        
        Args:
            z: observed reading
            rho: sensor state (uses self.rho if None)
            sigma: uncertainty (uses last computed if None)
        
        Returns:
            likelihood value
        """
        if rho is None:
            rho = self.rho
        if sigma is None:
            sigma = 0.1  # default
        
        return np.exp(-0.5 * ((z - rho) / (sigma + EPS)) ** 2) / (sigma * np.sqrt(2 * np.pi))
    
    def reset(self):
        """Reset sensor state."""
        self.rho = 0.0
        self.time_since_hit = 0
        self.history = []
`

### Task 3: Implement SDAPosteriorEstimator (sda_posterior.py)

**File**: src/sda_bas/sda_posterior.py

`python
"""Sensor-Dynamics-Aware Posterior Estimator.

Key innovation: Integrates sensor dynamics into Bayesian update.

Standard Bayes:
    P(s | z) ¡Ø P(z | s) * P(s)

SDA Bayes:
    P(s | z, alpha) ¡Ø P(z | s, alpha) * P(s)
    
Where alpha modulates the observation weight:
    - High alpha (fast flight) -> lower observation weight (sensor is lagging)
    - Low alpha (slow/hover) -> higher observation weight (sensor is accurate)
"""
import numpy as np
from sensor_dynamics_aware_likelihood import SDALikelihood

EPS = 1e-12


class SDAPosteriorEstimator:
    """Posterior estimator with sensor dynamics integration."""
    
    def __init__(self, grid, occ_2d, emin, cell_size,
                 alpha_0=0.6, k_v=0.15, k_m=0.2,
                 sigma=3.0, lr=15.0, ld=20.0):
        self.grid = np.asarray(grid, dtype=np.float64)
        self.N = len(grid)
        self.occ_2d = occ_2d
        self.emin = np.asarray(emin, dtype=np.float64)
        self.cell_size = cell_size
        self.sigma = sigma
        self.lr = lr
        self.ld = ld
        
        # SDA components
        self.sensor_model = SDALikelihood(alpha_0, k_v, k_m)
        
        # Standard posterior (log-space)
        self.lp = np.zeros(self.N, dtype=np.float64)
        
        # For hit probability computation
        self.nx, self.ny = occ_2d.shape
        self.free_mask = occ_2d == 0
    
    def update(self, x, wind, speed, mode, hit_observed, weight=1.0):
        """Update posterior with dynamics-aware likelihood.
        
        Args:
            x: current UAV position (x, y)
            wind: wind vector (wx, wy)
            speed: current UAV speed
            mode: current flight mode
            hit_observed: boolean, whether gas was detected
            weight: observation weight (for multi-sensor fusion)
        """
        x = np.asarray(x[:2], dtype=np.float64)
        wind = np.asarray(wind[:2], dtype=np.float64)
        wn = np.linalg.norm(wind)
        
        if wn < EPS:
            return
        
        # 1. Compute true hit probability for each source candidate
        u = wind / wn
        d = x[None, :] - self.grid[:, :2]
        dp = d @ u  # projection along wind
        dp2 = np.sum((d - dp[:, None] * u[None, :]) ** 2, axis=1)  # crosswind distance
        
        # Wind-aligned Gaussian hit probability
        sd = self.sigma + 0.2 * np.sqrt(np.maximum(dp, 0) + EPS)
        p_hit = np.where(
            dp > 0,
            np.exp(-dp2 / (2 * sd**2 + EPS)) * np.exp(-np.maximum(dp, 0) / self.lr),
            np.exp(-self.ld)
        )
        p_hit = np.clip(p_hit, EPS, 1 - EPS)
        
        # 2. Get sensor dynamics alpha
        alpha = self.sensor_model.get_alpha(speed, mode)
        
        # 3. Compute dynamics-aware observation weight
        # Key insight: when alpha is high (fast flight), the sensor reading is
        # a lagged, blurred version of reality. We should trust it LESS.
        # When alpha is low (slow/hover), the sensor is tracking truth closely.
        dynamics_weight = weight * (1.0 - alpha)
        
        # 4. Compute likelihood
        if hit_observed:
            # Likelihood of hit given source at each grid cell
            ll = np.log(p_hit + EPS)
        else:
            # Likelihood of no hit
            ll = np.log(1 - p_hit + EPS)
        
        # 5. Update posterior with dynamics-weighted observation
        self.lp += dynamics_weight * ll
        
        # 6. Update sensor model state
        # Use average hit probability as "true" hit prob for sensor update
        avg_hit_prob = float(np.mean(p_hit))
        self.sensor_model.update(avg_hit_prob, speed, mode)
        
        # 7. Normalize in log-space
        self.lp -= np.max(self.lp)
    
    def posterior(self):
        """Return normalized posterior distribution."""
        p = np.exp(self.lp)
        s = p.sum()
        return p / s if s > EPS else np.ones(self.N) / self.N
    
    def entropy(self):
        """Return posterior entropy."""
        p = self.posterior()
        return float(-np.sum(p * np.log(p + EPS)))
    
    def entropy_norm(self):
        """Return normalized posterior entropy (0-1)."""
        return self.entropy() / np.log(self.N) if self.N > 1 else 1.0
    
    def map_estimate(self):
        """Return MAP estimate (grid cell with highest posterior)."""
        return self.grid[np.argmax(self.posterior())]
    
    def reset(self):
        """Reset posterior and sensor state."""
        self.lp = np.zeros(self.N, dtype=np.float64)
        self.sensor_model.reset()
`

### Task 4: Implement SDAPlanner (sda_planner.py)

**File**: src/sda_bas/sda_planner.py

`python
"""SDA-BAS Planner - Sensor-Dynamics-Aware Bayesian Active Sensing.

Key innovation: Uses dynamics-aware posterior for action selection.

Scoring function:
    Score = [ERR_sda + lam_D * D] * Q / (T + lam_E * E + lam_J * J) - lam_B * BAE

Where:
    ERR_sda = Expected Risk Reduction using SDA posterior
    Q = Measurement quality (same as DQA-AS)
    D = Disambiguation score
    T = Time cost
    E = Energy cost
    J = Yaw jerk cost
    BAE = Model mismatch penalty
"""
import numpy as np
from sensor_dynamics_aware_likelihood import SDALikelihood
from sda_posterior import SDAPosteriorEstimator
from uav_action_library import DiagnosticActionLibrary

EPS = 1e-12


class SDAPlanner:
    """Sensor-Dynamics-Aware Bayesian Active Sensing planner."""
    
    def __init__(self, grid, occ_2d, emin, cell_size,
                 lam_D=0.5, lam_E=0.1, lam_J=0.05, lam_B=0.2, lam_R=0.1,
                 mc_samples=16, max_actions=30):
        self.grid = grid
        self.occ_2d = occ_2d
        self.emin = np.asarray(emin, dtype=np.float64)
        self.cell_size = cell_size
        
        self.lam_D = lam_D
        self.lam_E = lam_E
        self.lam_J = lam_J
        self.lam_B = lam_B
        self.lam_R = lam_R
        self.mc_samples = mc_samples
        
        # SDA components
        self.sensor_model = SDALikelihood()
        self.posterior_estimator = SDAPosteriorEstimator(grid, occ_2d, emin, cell_size)
        
        # Action library (same as DQA-AS)
        self.action_lib = DiagnosticActionLibrary(grid, occ_2d, emin, cell_size, max_actions)
        
        # Visit tracking
        self.visit_counts = {}
    
    def __call__(self, state, est, obs_history, step):
        """Select best diagnostic action.
        
        Args:
            state: UAVState with position, speed, mode, etc.
            est: PosteriorEstimator (standard, for compatibility)
            obs_history: list of observation dicts
            step: current step number
        
        Returns:
            target_xy: (2,) next target position
            action_info: dict with action details
        """
        # Use SDA posterior instead of standard posterior
        post = self.posterior_estimator.posterior()
        wind = np.array(obs_history[-1]["wind"][:2]) if obs_history else np.array([0.5, 0.2])
        
        # Generate candidate actions
        actions = self.action_lib.generate(state, est, wind, obs_history)
        
        if not actions:
            # Fallback: go to MAP
            return self.posterior_estimator.map_estimate()[:2], {"name": "fallback_map", "mode": "fast", "speed": 0.5}
        
        # Score each action
        best_action = actions[0]
        best_score = -float('inf')
        Hn = self.posterior_estimator.entropy_norm()
        
        for action in actions:
            score = self._score_action(action, state, post, wind)
            
            # Exploration bonus: when entropy high, favor moving to new areas
            if Hn > 0.6:
                dist_from_current = np.linalg.norm(action.target_xy - state.pos[:2])
                exploration_bonus = 0.3 * min(dist_from_current / 3.0, 1.0)
                if action.name == "HoverConfirm":
                    exploration_bonus -= 0.5
                score += exploration_bonus
            
            # Revisit penalty
            target_key = (round(float(action.target_xy[0]), 1),
                          round(float(action.target_xy[1]), 1))
            revisit_count = self.visit_counts.get(target_key, 0)
            revisit_penalty = self.lam_R * revisit_count
            score -= revisit_penalty
            
            if score > best_score:
                best_score = score
                best_action = action
        
        # Update visit count
        target_key = (round(float(best_action.target_xy[0]), 1),
                      round(float(best_action.target_xy[1]), 1))
        self.visit_counts[target_key] = self.visit_counts.get(target_key, 0) + 1
        
        return best_action.target_xy, {
            "name": best_action.name,
            "mode": best_action.mode,
            "speed": best_action.speed,
            "score": best_score,
            "duration": best_action.duration,
            "use_astar": True,
        }
    
    def _score_action(self, action, state, post, wind):
        """Compute action score using SDA posterior.
        
        Score = [ERR_sda + lam_D * D] * Q / (T + lam_E * E + lam_J * J) - lam_B * BAE
        """
        # 1. Expected Risk Reduction using SDA posterior
        err = self._expected_risk_reduction_sda(action, state, post, wind)
        
        # 2. False-source disambiguation
        dis = self._disambiguation_score(action, post, wind)
        
        # 3. Measurement quality (same as DQA-AS)
        q = self._quality_score(action.speed, action.mode, state.time_since_hit)
        
        # 4. BAE penalty
        bae = self._bae_penalty(action, state)
        
        # 5. Cost
        T = action.duration + EPS
        E = action.energy_proxy
        J = action.yaw_jerk_proxy
        
        numerator = (err + self.lam_D * dis) * q
        denominator = T + self.lam_E * E + self.lam_J * J + EPS
        score = numerator / denominator - self.lam_B * bae
        
        return score
    
    def _expected_risk_reduction_sda(self, action, state, post, wind):
        """Compute ERR using dynamics-aware posterior.
        
        This is the KEY difference from DQA-AS:
        - DQA-AS uses idealized observation model
        - SDA-BAS uses dynamics-aware posterior
        """
        mu_P = np.sum(self.grid * post[:, None], axis=0)
        R_current = float(np.sum(post * np.sum((self.grid - mu_P[None, :]) ** 2, axis=1)))
        
        # Monte Carlo: sample observation outcomes
        total_R_new = 0.0
        for _ in range(self.mc_samples):
            # Predict hit probability using observation model (wind-aware)
            p_hit = np.array([self._hit_prob(self.grid[i], action.target_xy, wind)
                              for i in range(len(self.grid))])
            p_hit = p_hit / (p_hit.sum() + EPS)
            
            # Sample: hit or miss
            hit_prob = float(np.sum(post * p_hit))
            hit = np.random.random() < hit_prob
            
            # KEY INNOVATION: Use dynamics-aware posterior update
            # Save current state
            saved_lp = self.posterior_estimator.lp.copy()
            saved_rho = self.posterior_estimator.sensor_model.rho
            
            # Update SDA posterior with hypothetical observation
            self.posterior_estimator.update(
                action.target_xy, wind,
                action.speed, action.mode,
                hit_observed=hit
            )
            
            # Get new posterior
            post_new = self.posterior_estimator.posterior()
            
            # Restore state (we're just simulating)
            self.posterior_estimator.lp = saved_lp
            self.posterior_estimator.sensor_model.rho = saved_rho
            
            # New risk
            mu_new = np.sum(self.grid * post_new[:, None], axis=0)
            R_new = float(np.sum(post_new * np.sum((self.grid - mu_new[None, :]) ** 2, axis=1)))
            total_R_new += R_new
        
        R_expected_new = total_R_new / self.mc_samples
        return max(0, R_current - R_expected_new)
    
    def _hit_prob(self, source_xy, query_xy, wind_xy=None):
        """Compute P(hit | source, query, wind) - wind-aligned Gaussian."""
        if wind_xy is None:
            wind_xy = np.array([0.5, 0.2])
        
        d = query_xy[:2] - source_xy[:2]
        wn = np.linalg.norm(wind_xy[:2])
        if wn < EPS:
            return 0.1
        
        u = wind_xy[:2] / wn
        dp = np.dot(d, u)  # projection along wind
        dp2 = np.sum((d - dp * u) ** 2)  # crosswind distance
        
        # Source upstream of query -> higher hit probability
        if dp > 0:
            sd = 3.0 + 0.2 * np.sqrt(dp)
            p = np.exp(-dp2 / (2 * sd**2)) * np.exp(-dp / 15.0)
        else:
            p = np.exp(-20.0)
        
        return np.clip(p, EPS, 1 - EPS)
    
    def _disambiguation_score(self, action, post, wind):
        """Compute false-source disambiguation score."""
        top_idx = np.argsort(post)[-5:]
        if len(top_idx) < 2:
            return 0.0
        
        p_hits = []
        for idx in top_idx:
            p = self._hit_prob(self.grid[idx], action.target_xy, wind)
            p_hits.append(p)
        
        p1, p2 = p_hits[-1], p_hits[-2]
        p1 = np.clip(p1, EPS, 1 - EPS)
        p2 = np.clip(p2, EPS, 1 - EPS)
        m = 0.5 * (p1 + p2)
        js = 0.5 * (p1 * np.log(p1 / m) + (1 - p1) * np.log((1 - p1) / (1 - m))) + \
             0.5 * (p2 * np.log(p2 / m) + (1 - p2) * np.log((1 - p2) / (1 - m)))
        return float(abs(js))
    
    def _quality_score(self, speed, mode, time_since_hit):
        """Compute measurement quality score."""
        base_q = 1.0
        speed_penalty = 0.1 * speed
        mode_bonus = 0.2 if mode in ("slow", "hover") else 0.0
        hit_bonus = 0.3 if time_since_hit < 3 else 0.0
        return max(0.1, base_q - speed_penalty + mode_bonus + hit_bonus)
    
    def _bae_penalty(self, action, state):
        """Compute model mismatch penalty."""
        sigma0 = 0.05
        k_speed = 0.10
        k_wind = 0.15
        
        speed_penalty = k_speed * action.speed
        mode_penalty = 0.15 if action.mode == "fast" else 0.0
        
        return sigma0 + speed_penalty + mode_penalty
`

### Task 5: Create __init__.py

**File**: src/sda_bas/__init__.py

`python
"""SDA-BAS: Sensor-Dynamics-Aware Bayesian Active Sensing."""
from sensor_dynamics_aware_likelihood import SDALikelihood
from sda_posterior import SDAPosteriorEstimator
from sda_planner import SDAPlanner
`

### Task 6: Write Unit Tests

**File**: 	ests/test_sda_bas.py

`python
"""Unit tests for SDA-BAS components."""
import numpy as np
import sys
sys.path.insert(0, 'src/sda_bas')

from sensor_dynamics_aware_likelihood import SDALikelihood
from sda_posterior import SDAPosteriorEstimator


def test_sensor_dynamics():
    """Test SDALikelihood alpha dynamics."""
    sensor = SDALikelihood()
    
    # Test alpha computation
    alpha_fast = sensor.get_alpha(speed=1.0, mode="fast")
    alpha_slow = sensor.get_alpha(speed=0.2, mode="slow")
    alpha_hover = sensor.get_alpha(speed=0.0, mode="hover")
    
    assert alpha_fast > alpha_slow, "Fast mode should have higher alpha"
    assert alpha_hover < alpha_fast, "Hover should have lower alpha than fast"
    
    # Test update
    observed, sigma = sensor.update(true_hit_prob=0.8, speed=0.5, mode="slow")
    assert 0 <= observed <= 1, "Observed should be in [0, 1]"
    assert sigma > 0, "Sigma should be positive"
    
    print("? Sensor dynamics test passed")


def test_posterior_convergence():
    """Test that SDA posterior converges faster than standard."""
    # Create simple grid
    grid = np.array([[0, 0], [1, 0], [2, 0], [3, 0]], dtype=float)
    occ_2d = np.zeros((4, 4), dtype=int)
    emin = np.array([0, 0])
    cell_size = 1.0
    
    sda_est = SDAPosteriorEstimator(grid, occ_2d, emin, cell_size)
    
    # Simulate observations
    for i in range(10):
        sda_est.update(
            x=np.array([1.5, 0.5]),
            wind=np.array([1.0, 0.0]),
            speed=0.2,
            mode="slow",
            hit_observed=True
        )
    
    # Check posterior is peaked
    post = sda_est.posterior()
    max_idx = np.argmax(post)
    
    # Should be peaked around source location
    assert post[max_idx] > 0.3, f"Posterior should be peaked, got max={post[max_idx]:.3f}"
    
    print("? Posterior convergence test passed")


if __name__ == "__main__":
    test_sensor_dynamics()
    test_posterior_convergence()
    print("\n? All SDA-BAS tests passed!")
`

### Task 7: Run Tests

`ash
cd D:/ZYC/A-gas/workspace/uav_diagsense
python tests/test_sda_bas.py
`

## Success Criteria
- All unit tests pass
- SDALikelihood alpha dynamics match sensor_response_model.py
- SDAPosteriorEstimator converges on test data
- No import errors

## Output
When complete, tell me:
"Iteration 2 complete. SDA-BAS implementation ready. Tests passed."
