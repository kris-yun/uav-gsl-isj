# Step 3b ¡ª Replace SDM with Fisher Information Action Selection (FDPOE)

## Why Replace SDM
- SDM (L1 deconvolution) only 5% improvement ¡ª too parameter-dependent
- Deconvolution kernel is wind-specific ¡ª not robust across environments
- User requirement: no dataset-specific tuning

## New Module: FDPOE (Fisher-Driven Posterior Optimal Exploration)

**Source domain**: Seismology / Medical Imaging (D-optimal experimental design)
**Key reference**: Optimal sensor placement for source localization (IEEE TSP, multiple papers)

### Core Idea
Instead of scoring actions by entropy reduction (ERR) alone, also consider the **Fisher Information** of each measurement. Actions that maximize the Fisher Information about the source location are most informative.

**Why this is better than SDM**:
- No deconvolution kernel to tune
- Works for ANY wind direction automatically
- Fisher Information is a geometric property of the observation model ¡ª dataset-independent
- D-optimal design is well-established in seismology (50+ years of theory)

### Cross-domain mapping
- Seismic sensors ¡ú gas sensors
- Earthquake epicenter ¡ú gas source
- Sensor array geometry ¡ú UAV action selection
- D-optimal criterion ¡ú action scoring

## Implementation (single batch)

### File 1: `workspace/uav_diagsense/src/fdpoe/fdpoe_scorer.py`

```python
class FDPOEScorer:
    """Fisher Information action scorer.
    
    Replaces SDM. Computes Fisher Information Matrix (FIM) for each
    candidate action and uses D-optimal criterion (max det(FIM)) 
    as additional scoring term.
    """
    def __init__(self, grid, obs_model, lam_F=0.3):
        self.grid = grid
        self.obs_model = obs_model
        self.lam_F = lam_F  # weight for Fisher term
    
    def fisher_score(self, action_xy, post, wind):
        """Compute D-optimal Fisher score for an action.
        
        FIM = sum_s post(s) * grad_s(log p(obs|s)) * grad_s(log p(obs|s))^T
        
        D-optimal score = det(FIM)
        """
        # For each grid cell s, compute gradient of log-likelihood
        # with respect to source location s
        grads = []
        weights = []
        for i, s in enumerate(self.grid):
            p = self.obs_model.hit_prob(s, action_xy, wind)
            # Numerical gradient of p w.r.t. s
            eps = 0.1
            dp_dx = (self.obs_model.hit_prob(s + [eps,0], action_xy, wind) - 
                     self.obs_model.hit_prob(s - [eps,0], action_xy, wind)) / (2*eps)
            dp_dy = (self.obs_model.hit_prob(s + [0,eps], action_xy, wind) - 
                     self.obs_model.hit_prob(s - [0,eps], action_xy, wind)) / (2*eps)
            
            # grad log p = (1/p) * grad p
            if p > 1e-12:
                grad_log_p = np.array([dp_dx / p, dp_dy / p])
            else:
                grad_log_p = np.array([0.0, 0.0])
            
            grads.append(grad_log_p)
            weights.append(post[i])
        
        # FIM = sum_s w(s) * grad * grad^T
        FIM = np.zeros((2, 2))
        for g, w in zip(grads, weights):
            FIM += w * np.outer(g, g)
        
        # D-optimal score = det(FIM)
        return float(np.linalg.det(FIM))
```

### File 2: `workspace/uav_diagsense/src/fdpoe/fdpoe_planner.py`
- Inherits from DQAASPlanner
- Adds `lam_F * fisher_score` to action scoring
- Rest identical to DQA-AS

### File 3: `workspace/uav_diagsense/tests/test_fdpoe.py`
- test_fim_positive_semidefinite
- test_fisher_score_higher_for_informative_action
- test_fdpoe_selects_different_actions_than_dqaas

## Experiment
- Compare: DQA-AS vs DQA-AS+MEMP vs DQA-AS+BPFM vs DQA-AS+FDPOE
- Same synthetic plume, 5 seeds
- Save to `automation/results/iter9_fdpoe.csv` and `iter9_fdpoe.md`

## Acceptance
- FIM is positive semi-definite (verified by test)
- Fisher score distinguishes informative vs uninformative actions
- Fair comparison with DQA-AS baseline
- NO parameter tuning for specific dataset
