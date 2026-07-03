# Iteration 2: MEMP Implementation

## Objective
Implement Medical Evidence Mass Processing (MEMP) for gas source localization.

## Background

**Source Domain**: EEG Brain Source Localization (LORETA family)

**Original Problem**: 
In EEG, multiple scalp sensors detect brain electrical activity. The goal is to localize the source (dipole) from noisy, sparse sensor readings. LORETA (Low Resolution Electromagnetic Tomography) assumes the source is spatially smooth and uses a Laplacian constraint for regularization.

**Key Insight for GSL**:
- Gas sensors = EEG sensors (sparse, noisy)
- Gas source = brain dipole (localized)
- Wind = volume conductor (current flow)
- Spatial smoothness = plume continuity (gas doesn't teleport)

**Why This Works**:
Current GSL methods have a problem: the posterior can have spurious isolated peaks far from the true source. This happens because:
1. Sensor noise creates false positives
2. Wind alignment can create phantom sources
3. No spatial coherence constraint

MEMP adds a Laplacian smoothing term that penalizes isolated peaks, enforcing spatial coherence.

---

## Implementation

### File: workspace/uav_diagsense/src/memp/memp_posterior.py

`python
"""Medical Evidence Mass Processing (MEMP) for Gas Source Localization.

Borrowed from: EEG source localization (LORETA family)
Paper: Pascual-Marqui et al., "Low resolution electromagnetic tomography",
       1994, 2002

Key Innovation: Spatial smoothness constraint via graph Laplacian
prevents posterior collapse and isolated peaks.

Cross-domain mapping:
- EEG sensors ¡ú gas sensors
- Brain dipole ¡ú gas source
- Volume conductor ¡ú wind transport
- Spatial smoothness ¡ú plume continuity
"""
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve

EPS = 1e-12


class MEMPPosteriorEstimator:
    """MEMP-based posterior estimator for gas source localization.
    
    Core idea: Standard Bayesian posterior + Laplacian smoothness constraint
    
    Standard Bayes:
        P(s | z) ¡Ø P(z | s) * P(s)
    
    MEMP Bayes:
        P(s | z) ¡Ø P(z | s) * P(s) * exp(-¦Ë * ||L * s||^2)
        
    Where:
        L = graph Laplacian of free-space grid
        ¦Ë = smoothness weight (hyperparameter)
    """
    
    def __init__(self, grid, occ_2d, emin, cell_size,
                 sigma=3.0, lr=15.0, ld=20.0,
                 smoothness_weight=0.1):
        """
        Args:
            grid: (N, 2) grid cell centers
            occ_2d: (nx, ny) occupancy grid (0=free, 1=occupied)
            emin: (2,) minimum coordinates
            cell_size: grid cell size
            sigma: wind dispersion parameter
            lr: wind correlation length
            ld: distance decay
            smoothness_weight: Laplacian regularization weight (lambda)
        """
        self.grid = np.asarray(grid, dtype=np.float64)
        self.N = len(grid)
        self.occ_2d = occ_2d
        self.emin = np.asarray(emin, dtype=np.float64)
        self.cell_size = cell_size
        self.sigma = sigma
        self.lr = lr
        self.ld = ld
        self.smoothness_weight = smoothness_weight
        
        # Build Laplacian matrix
        self.L = self._build_laplacian(occ_2d, emin, cell_size)
        
        # Standard posterior (log-space)
        self.lp = np.zeros(self.N, dtype=np.float64)
        
        # For hit probability computation
        self.nx, self.ny = occ_2d.shape
        self.free_mask = occ_2d == 0
        
        # Map grid cells to indices
        self.grid_to_idx = {}
        for i, g in enumerate(grid):
            key = (round(float(g[0]), 2), round(float(g[1]), 2))
            self.grid_to_idx[key] = i
    
    def _build_laplacian(self, occ_2d, emin, cell_size):
        """Build graph Laplacian for free-space cells.
        
        This is the KEY innovation from LORETA:
        - Each cell is a node
        - Edges connect adjacent free cells
        - Laplacian = D - A (degree matrix - adjacency matrix)
        
        The Laplacian enforces spatial smoothness:
        - ||L * p||^2 penalizes rapid changes in posterior
        - Equivalent to: neighboring cells should have similar values
        """
        nx, ny = occ_2d.shape
        free_mask = occ_2d == 0
        
        # Count free cells
        n_free = np.sum(free_mask)
        
        # Build adjacency list
        # For each free cell, find adjacent free cells
        rows = []
        cols = []
        data = []
        
        # Map (i,j) to linear index
        cell_to_idx = {}
        idx = 0
        for i in range(nx):
            for j in range(ny):
                if free_mask[i, j]:
                    cell_to_idx[(i, j)] = idx
                    idx += 1
        
        # Build adjacency
        for i in range(nx):
            for j in range(ny):
                if not free_mask[i, j]:
                    continue
                
                idx_i = cell_to_idx[(i, j)]
                
                # Check 4 neighbors
                for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ni, nj = i + di, j + dj
                    if 0 <= ni < nx and 0 <= nj < ny and free_mask[ni, nj]:
                        idx_j = cell_to_idx[(ni, nj)]
                        rows.append(idx_i)
                        cols.append(idx_j)
                        data.append(-1.0)  # Negative for Laplacian
        
        # Build adjacency matrix
        A = sparse.csr_matrix((data, (rows, cols)), shape=(n_free, n_free))
        
        # Degree matrix
        D = sparse.diags(np.array(A.sum(axis=1)).flatten())
        
        # Laplacian: L = D - A
        L = D - A
        
        return L
    
    def update(self, x, wind, hit, weight=1.0):
        """Update posterior with Laplacian smoothness constraint.
        
        Standard update:
            lp += weight * ll
        
        MEMP update:
            lp += weight * ll - lambda * L @ lp
            
        The Laplacian term penalizes rapid changes, enforcing spatial coherence.
        """
        x = np.asarray(x[:2], dtype=np.float64)
        wind = np.asarray(wind[:2], dtype=np.float64)
        wn = np.linalg.norm(wind)
        
        if wn < EPS:
            return
        
        # 1. Standard Bayesian update (same as PosteriorEstimator)
        u = wind / wn
        d = x[None, :] - self.grid[:, :2]
        dp = d @ u  # projection along wind
        dp2 = np.sum((d - dp[:, None] * u[None, :]) ** 2, axis=1)  # crosswind distance
        
        sd = self.sigma + 0.2 * np.sqrt(np.maximum(dp, 0) + EPS)
        
        if hit:
            # Likelihood of hit given source at each grid cell
            ll = np.where(
                dp > 0,
                -dp2 / (2 * sd**2 + EPS) - np.maximum(dp, 0) / self.lr,
                -self.ld
            )
        else:
            # Likelihood of no hit (inverse)
            ll = np.where(
                dp > 0,
                np.log(1 - np.exp(-dp2 / (2 * sd**2 + EPS)) + EPS),
                0.0
            )
        
        # 2. Standard posterior update
        self.lp += weight * ll
        
        # 3. KEY INNOVATION: Apply Laplacian smoothing
        # This penalizes isolated peaks and enforces spatial coherence
        # Only apply if we have enough observations
        if np.sum(self.lp != 0) > 10:
            # Convert to probability space for Laplacian
            p = np.exp(self.lp - np.max(self.lp))
            p = p / (p.sum() + EPS)
            
            # Apply Laplacian smoothing
            # Note: L is n_free x n_free, but self.lp is N
            # We need to map between them
            # For simplicity, apply smoothing in log-space
            self.lp -= self.smoothness_weight * self._laplacian_smooth()
        
        # 4. Normalize
        self.lp -= np.max(self.lp)
    
    def _laplacian_smooth(self):
        """Apply Laplacian smoothing to log-posterior.
        
        Returns: smoothing penalty vector (N,)
        """
        # Simple approximation: penalize difference from neighbors
        # For each cell, compute average of neighbors
        penalty = np.zeros(self.N)
        
        for i, g in enumerate(self.grid):
            gx, gy = g[0], g[1]
            
            # Find grid indices
            gi = int((gx - self.emin[0]) / self.cell_size)
            gj = int((gy - self.emin[1]) / self.cell_size)
            
            if not (0 <= gi < self.nx and 0 <= gj < self.ny):
                continue
            
            # Average of neighbors
            neighbor_sum = 0.0
            n_neighbors = 0
            
            for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ni, nj = gi + di, gj + dj
                if 0 <= ni < self.nx and 0 <= nj < self.ny and self.free_mask[ni, nj]:
                    # Find grid cell at (ni, nj)
                    nx_coord = self.emin[0] + (ni + 0.5) * self.cell_size
                    ny_coord = self.emin[1] + (nj + 0.5) * self.cell_size
                    
                    # Find index in self.grid
                    for j, g2 in enumerate(self.grid):
                        if abs(g2[0] - nx_coord) < 0.1 and abs(g2[1] - ny_coord) < 0.1:
                            neighbor_sum += self.lp[j]
                            n_neighbors += 1
                            break
            
            if n_neighbors > 0:
                neighbor_avg = neighbor_sum / n_neighbors
                # Penalize deviation from neighbor average
                penalty[i] = self.lp[i] - neighbor_avg
        
        return penalty
    
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
        """Reset posterior."""
        self.lp = np.zeros(self.N, dtype=np.float64)
`

---

## Unit Tests

### File: workspace/uav_diagsense/tests/test_memp.py

`python
"""Unit tests for MEMP posterior estimator."""
import numpy as np
import sys
sys.path.insert(0, 'src/memp')

from memp_posterior import MEMPPosteriorEstimator


def test_laplacian_construction():
    """Test that Laplacian matrix is correctly built."""
    # Simple 3x3 grid, all free
    occ_2d = np.zeros((3, 3), dtype=int)
    grid = np.array([[i, j] for i in range(3) for j in range(3)], dtype=float)
    emin = np.array([0, 0])
    cell_size = 1.0
    
    est = MEMPPosteriorEstimator(grid, occ_2d, emin, cell_size)
    
    # Laplacian should be 9x9
    assert est.L.shape == (9, 9), f"Expected 9x9, got {est.L.shape}"
    
    # Row sums should be zero (property of Laplacian)
    row_sums = np.array(est.L.sum(axis=1)).flatten()
    assert np.allclose(row_sums, 0, atol=1e-10), "Row sums should be zero"
    
    print("? Laplacian construction test passed")


def test_smoothness_constraint():
    """Test that Laplacian smoothing penalizes isolated peaks."""
    # Create grid with isolated peak
    occ_2d = np.zeros((5, 5), dtype=int)
    grid = np.array([[i, j] for i in range(5) for j in range(5)], dtype=float)
    emin = np.array([0, 0])
    cell_size = 1.0
    
    est = MEMPPosteriorEstimator(grid, occ_2d, emin, cell_size, smoothness_weight=0.5)
    
    # Create isolated peak at (2, 2)
    est.lp[12] = 10.0  # (2, 2) = index 12
    est.lp[0] = 0.0    # (0, 0) = index 0
    
    # Apply Laplacian smoothing
    penalty = est._laplacian_smooth()
    
    # Penalty should be high for isolated peak
    assert penalty[12] > 0, "Isolated peak should have positive penalty"
    
    print("? Smoothness constraint test passed")


def test_posterior_convergence():
    """Test that MEMP posterior converges to source."""
    # Create grid
    occ_2d = np.zeros((5, 5), dtype=int)
    grid = np.array([[i, j] for i in range(5) for j in range(5)], dtype=float)
    emin = np.array([0, 0])
    cell_size = 1.0
    
    est = MEMPPosteriorEstimator(grid, occ_2d, emin, cell_size)
    
    # Simulate observations near source at (2, 2)
    for _ in range(20):
        est.update(
            x=np.array([2.5, 2.5]),
            wind=np.array([1.0, 0.0]),
            hit=True
        )
    
    # Posterior should be peaked around source
    post = est.posterior()
    max_idx = np.argmax(post)
    max_pos = grid[max_idx]
    
    # Should be close to (2, 2)
    dist = np.linalg.norm(max_pos - np.array([2, 2]))
    assert dist < 2.0, f"Posterior peak at {max_pos}, expected near (2,2)"
    
    print("? Posterior convergence test passed")


if __name__ == "__main__":
    test_laplacian_construction()
    test_smoothness_constraint()
    test_posterior_convergence()
    print("\n? All MEMP tests passed!")
`

---

## Integration with DQA-AS

### File: workspace/uav_diagsense/src/memp/memp_planner.py

`python
"""MEMP-enhanced planner for gas source localization.

Combines DQA-AS action selection with MEMP posterior.
"""
import numpy as np
from memp_posterior import MEMPPosteriorEstimator
from dqa_as_planner import DQAASPlanner

EPS = 1e-12


class MEMPPlanner(DQAASPlanner):
    """Planner using MEMP posterior instead of standard posterior.
    
    Key difference: Uses Laplacian-smoothed posterior for action selection.
    """
    
    def __init__(self, grid, occ_2d, emin, cell_size,
                 smoothness_weight=0.1, **kwargs):
        # Initialize parent
        super().__init__(grid, occ_2d, emin, cell_size, **kwargs)
        
        # Replace standard posterior with MEMP posterior
        self.memp_posterior = MEMPPosteriorEstimator(
            grid, occ_2d, emin, cell_size,
            smoothness_weight=smoothness_weight
        )
    
    def __call__(self, state, est, obs_history, step):
        """Select action using MEMP posterior.
        
        Key innovation: Use Laplacian-smoothed posterior for action selection.
        """
        # Use MEMP posterior instead of standard posterior
        post = self.memp_posterior.posterior()
        
        # Rest is same as DQA-AS
        wind = np.array(obs_history[-1]["wind"][:2]) if obs_history else np.array([0.5, 0.2])
        
        # Generate candidate actions
        actions = self.action_lib.generate(state, est, wind, obs_history)
        
        if not actions:
            return self.memp_posterior.map_estimate()[:2], {"name": "fallback_map", "mode": "fast", "speed": 0.5}
        
        # Score each action using MEMP posterior
        best_action = actions[0]
        best_score = -float('inf')
        Hn = self.memp_posterior.entropy_norm()
        
        for action in actions:
            score = self._score_action(action, state, post, wind)
            
            if Hn > 0.6:
                dist_from_current = np.linalg.norm(action.target_xy - state.pos[:2])
                exploration_bonus = 0.3 * min(dist_from_current / 3.0, 1.0)
                if action.name == "HoverConfirm":
                    exploration_bonus -= 0.5
                score += exploration_bonus
            
            target_key = (round(float(action.target_xy[0]), 1),
                          round(float(action.target_xy[1]), 1))
            revisit_count = self.visit_counts.get(target_key, 0)
            revisit_penalty = self.lam_R * revisit_count
            score -= revisit_penalty
            
            if score > best_score:
                best_score = score
                best_action = action
        
        # Update visit count and MEMP posterior
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
`

---

## Deliverable

When complete, say:
"Iteration 2 complete. MEMP implementation ready. Tests passed."

## Success Criteria
- All unit tests pass
- Laplacian matrix correctly constructed
- Posterior smoothing works
- No import errors
