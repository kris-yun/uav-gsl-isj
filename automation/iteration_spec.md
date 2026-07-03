# SDA-BAS Automation Iteration Spec
## For Claude Code in VS Code

**Goal**: Implement and validate Sensor-Dynamics-Aware Bayesian Active Sensing (SDA-BAS)
**Loop**: Design ¡ú Implement ¡ú Experiment ¡ú Review ¡ú Improve ¡ú Repeat

---

## ITERATION 1: Baseline Validation (Day 1)

### Task
Verify current DQA-AS performance and establish baseline.

### Steps
1. Run DQA-AS on House01 with 5 seeds (ideal + slow_mox sensor)
2. Record: mean_error, success@1m, path_length, n_encounters
3. Save results to utomation/results/iter1_baseline.csv

### Command
`ash
cd D:\ZYC\A-gas\workspace\uav_diagsense
python scripts/run_batch.py --method DQA_AS --seeds 0-4 --sensor ideal slow_mox --house House01
`

### Expected Output
`
automation/results/iter1_baseline.csv
`

### Success Criteria
- Results match existing h01_final_fair.csv (¡À5%)
- No crashes or errors

---

## ITERATION 2: SDA-BAS Module 1 - Dynamics-Aware Likelihood (Day 2)

### Task
Implement sensor-dynamics-aware likelihood function.

### Specification

**File**: src/sda_bas/sda_likelihood.py

**Core Logic**:
`python
class SDALikelihood:
    def __init__(self, alpha_0=0.6, k_v=0.15, k_m=0.2):
        self.alpha_0 = alpha_0
        self.k_v = k_v
        self.k_m = k_m
        self.rho = 0.0  # sensor state
        self.time_since_hit = 0
    
    def update(self, true_hit_prob, speed, mode):
        """Update sensor state and return dynamics-aware likelihood."""
        # 1. Update sensor dynamics
        alpha = self._get_alpha(speed, mode)
        self.rho = alpha * self.rho + (1 - alpha) * true_hit_prob
        
        # 2. Compute measurement uncertainty
        sigma = self._measurement_uncertainty(speed, mode)
        
        # 3. Return likelihood
        return self._likelihood(self.rho, sigma)
    
    def _get_alpha(self, speed, mode):
        mode_bonus = 1.0 if mode in ("slow", "hover") else 0.0
        alpha = self.alpha_0 + self.k_v * speed - self.k_m * mode_bonus
        return np.clip(alpha, 0.1, 0.95)
    
    def _measurement_uncertainty(self, speed, mode):
        base_sigma = 0.1
        speed_penalty = 0.05 * speed
        mode_penalty = 0.1 if mode == "fast" else 0.0
        return base_sigma + speed_penalty + mode_penalty
`

### Steps
1. Create src/sda_bas/ directory
2. Implement sda_likelihood.py
3. Write unit test: 	ests/test_sda_likelihood.py
4. Run test to verify

### Success Criteria
- Unit test passes
- Alpha dynamics match sensor_response_model.py
- Likelihood function is normalized

---

## ITERATION 3: SDA-BAS Module 2 - Dynamics-Aware Posterior (Day 3)

### Task
Integrate dynamics-aware likelihood into posterior update.

### Specification

**File**: src/sda_bas/sda_posterior.py

**Core Logic**:
`python
class SDAPosteriorEstimator:
    def __init__(self, grid, sensor_model, sigma=3.0, lr=15.0, ld=20.0):
        self.grid = grid
        self.N = len(grid)
        self.sensor_model = sensor_model
        self.lp = np.zeros(self.N)
    
    def update(self, x, wind, speed, mode, weight=1.0):
        """Update posterior with dynamics-aware likelihood."""
        # 1. Compute true hit probability for each source candidate
        p_hits = np.array([self._hit_prob(s, x, wind) for s in self.grid])
        
        # 2. Get dynamics-aware likelihood
        alpha = self.sensor_model._get_alpha(speed, mode)
        
        # 3. Weighted update
        observation_weight = weight * (1 - alpha)
        prior_weight = alpha
        
        # 4. Standard Bayesian update with weighted likelihood
        ll = np.where(p_hits > 0, np.log(p_hits + 1e-12), -20.0)
        self.lp += observation_weight * ll
`

### Steps
1. Implement sda_posterior.py
2. Compare with standard PosteriorEstimator
3. Write comparison test

### Success Criteria
- SDA posterior converges faster than standard on slow_mox
- No numerical instability

---

## ITERATION 4: SDA-BAS Module 3 - Dynamics-Aware Planning (Day 4)

### Task
Implement SDA-BAS planner using dynamics-aware posterior.

### Specification

**File**: src/sda_bas/sda_planner.py

**Core Logic**:
`python
class SDAPlanner:
    def __init__(self, grid, occ_2d, emin, cell_size, ...):
        self.sensor_model = SDALikelihood()
        self.posterior = SDAPosteriorEstimator(grid, self.sensor_model)
        # ... same as DQA-AS but use SDA posterior
    
    def __call__(self, state, est, obs_history, step):
        # 1. Generate candidate actions (same as DQA-AS)
        actions = self.action_lib.generate(state, est, wind, obs_history)
        
        # 2. Score with dynamics-aware ERR
        for action in actions:
            score = self._score_action_sda(action, state, est, wind)
        
        # 3. Return best action
        return best_action.target_xy, action_info
`

### Steps
1. Implement sda_planner.py
2. Integrate with common_runner.py
3. Run smoke test (1 seed)

### Success Criteria
- SDA planner runs without errors
- Produces different actions than DQA-AS

---

## ITERATION 5: Full Experiment (Day 5)

### Task
Run full comparison: SDA-BAS vs DQA-AS vs baselines.

### Steps
1. Run SDA-BAS on House01, 5 seeds, ideal + slow_mox
2. Run baselines: Random, GreedyMAP, Infotaxis, KLD, DQA-AS
3. Save to utomation/results/iter5_comparison.csv
4. Generate summary table

### Command
`ash
python scripts/run_batch.py --method SDA_BAS DQA_AS Random GreedyMAP Infotaxis KLD --seeds 0-4 --sensor ideal slow_mox --house House01
`

### Expected Output
`
automation/results/iter5_comparison.csv
automation/results/iter5_summary.md
`

### Success Criteria
- SDA-BAS mean_error < DQA-AS mean_error on slow_mox
- SDA-BAS mean_error <= GreedyMAP mean_error on slow_mox
- No crashes

---

## ITERATION 6: Review & Improve (Day 6)

### Task
I will review results and provide improvement directions.

### What I'll Check
1. Does SDA-BAS beat DQA-AS? (Primary metric)
2. Does SDA-BAS beat baselines? (Secondary metric)
3. Where does SDA-BAS fail? (Failure analysis)
4. What parameters need tuning? (Sensitivity analysis)

### Possible Improvements
- Tune alpha_0, k_v, k_m parameters
- Adjust observation_weight calculation
- Add adaptive exploration bonus
- Fix edge cases in posterior update

### Output
`
automation/reviews/iter6_review.md
`

---

## ITERATION 7+: Refinement Loop

### Process
1. I review results -> identify issues
2. I write improvement spec
3. You (Claude Code) implement
4. Run experiments
5. Repeat until success criteria met

### Termination Conditions
- SDA-BAS beats all baselines on slow_mox (GO)
- 3 iterations without improvement (NO-GO, try new direction)
- Time budget exhausted (NO-GO)

---

## File Structure

`
automation/
©À©¤©¤ iteration_spec.md          <- This file
©À©¤©¤ results/
©¦   ©À©¤©¤ iter1_baseline.csv
©¦   ©À©¤©¤ iter5_comparison.csv
©¦   ©¸©¤©¤ iter5_summary.md
©À©¤©¤ reviews/
©¦   ©¸©¤©¤ iter6_review.md
©¸©¤©¤ specs/
    ©À©¤©¤ iter2_module1.md
    ©À©¤©¤ iter3_module2.md
    ©¸©¤©¤ iter4_module3.md
`

---

## Communication Protocol

### From Me to You (Claude Code)
- specs/iterN_spec.md: Detailed implementation spec
- eviews/iterN_review.md: Results review and improvement directions

### From You to Me
- esults/iterN_*.csv: Experiment results
- esults/iterN_summary.md: Quick summary

### Iteration Handoff
When you finish an iteration:
1. Save results to esults/
2. Write summary to esults/iterN_summary.md
3. Tell me "Iteration N complete, ready for review"
4. I'll review and provide next spec

---

## Current Status

**Iteration**: 0 (setup)
**Next Step**: Create directory structure and start Iteration 1
