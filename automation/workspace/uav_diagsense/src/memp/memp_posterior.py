"""Medical Evidence Mass Processing (MEMP) for Gas Source Localization.

Borrowed from: EEG source localization (LORETA family)
Paper: Pascual-Marqui et al., "Low resolution electromagnetic tomography",
       1994, 2002

Key Innovation: Spatial smoothness constraint via graph Laplacian
prevents posterior collapse and isolated peaks.

Cross-domain mapping:
- EEG sensors -> gas sensors
- Brain dipole -> gas source
- Volume conductor -> wind transport
- Spatial smoothness -> plume continuity
"""
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve

EPS = 1e-12


class MEMPPosteriorEstimator:
    """MEMP-based posterior estimator for gas source localization.

    Core idea: Standard Bayesian posterior + Laplacian smoothness constraint

    Standard Bayes:
        P(s | z) ~ P(z | s) * P(s)

    MEMP Bayes:
        P(s | z) ~ P(z | s) * P(s) * exp(-lambda * ||L * s||^2)

    Where:
        L = graph Laplacian of free-space grid
        lambda = smoothness weight (hyperparameter)
    """

    def __init__(self, grid, occ_2d, emin, cell_size,
                 sigma=3.0, lr=15.0, ld=20.0,
                 smoothness_weight=0.1):
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

        # Map (i,j) to linear index among free cells
        cell_to_idx = {}
        idx = 0
        for i in range(nx):
            for j in range(ny):
                if free_mask[i, j]:
                    cell_to_idx[(i, j)] = idx
                    idx += 1

        n_free = idx

        # Build adjacency
        rows = []
        cols = []
        data = []

        for i in range(nx):
            for j in range(ny):
                if not free_mask[i, j]:
                    continue
                idx_i = cell_to_idx[(i, j)]

                # 4-connected neighbors
                for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ni, nj = i + di, j + dj
                    if 0 <= ni < nx and 0 <= nj < ny and free_mask[ni, nj]:
                        idx_j = cell_to_idx[(ni, nj)]
                        rows.append(idx_i)
                        cols.append(idx_j)
                        data.append(-1.0)

                # Degree: number of free neighbors
                degree = 0
                for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ni, nj = i + di, j + dj
                    if 0 <= ni < nx and 0 <= nj < ny and free_mask[ni, nj]:
                        degree += 1
                rows.append(idx_i)
                cols.append(idx_i)
                data.append(float(degree))

        L = sparse.csr_matrix((data, (rows, cols)),
                               shape=(n_free, n_free),
                               dtype=np.float64)
        return L

    def _grid_to_free_idx(self, grid_idx):
        """Map from full grid index to free-cell index."""
        g = self.grid[grid_idx]
        # Find (i,j) in occupancy grid
        fi = int(round((g[0] - self.emin[0]) / self.cell_size))
        fj = int(round((g[1] - self.emin[1]) / self.cell_size))
        fi = np.clip(fi, 0, self.nx - 1)
        fj = np.clip(fj, 0, self.ny - 1)
        return fi, fj

    def _laplacian_smooth(self):
        """Compute Laplacian smoothness penalty.

        penalty = lambda * L^T * L * p
        This penalizes isolated peaks in the posterior.
        """
        # Extract posterior for free cells only
        post = self._get_posterior()

        # Map grid posterior to free-cell space
        free_indices = []
        grid_to_free = {}
        idx = 0
        for i in range(self.nx):
            for j in range(self.ny):
                if self.free_mask[i, j]:
                    grid_key = (round(float(self.emin[0] + i * self.cell_size), 2),
                                round(float(self.emin[1] + j * self.cell_size), 2))
                    if grid_key in self.grid_to_idx:
                        grid_to_free[grid_key] = idx
                    idx += 1

        # Build free-space posterior vector
        n_free = self.L.shape[0]
        p_free = np.ones(n_free, dtype=np.float64) / max(n_free, 1)

        for key, gi in self.grid_to_idx.items():
            if key in grid_to_free:
                fi = grid_to_free[key]
                if fi < n_free:
                    p_free[fi] = max(post[gi], EPS)

        # Normalize
        p_free = p_free / (p_free.sum() + EPS)

        # Compute L^T * L * p (Laplacian quadratic form gradient)
        Lp = self.L.dot(p_free)
        penalty_free = self.smoothness_weight * self.L.T.dot(Lp)

        # Map back to full grid
        penalty = np.zeros(self.N, dtype=np.float64)
        for key, gi in self.grid_to_idx.items():
            if key in grid_to_free:
                fi = grid_to_free[key]
                if fi < n_free:
                    penalty[gi] = penalty_free[fi]

        return penalty

    def _get_posterior(self):
        """Get normalized posterior from log-space."""
        lp = self.lp - self.lp.max()
        post = np.exp(lp)
        post = post / (post.sum() + EPS)
        return post

    def update(self, x, wind, hit):
        """Update posterior with a new observation.

        Args:
            x: (2,) observation position
            wind: (2,) wind vector
            hit: bool, gas detected or not
        """
        x = np.asarray(x, dtype=np.float64)
        wind = np.asarray(wind, dtype=np.float64)

        # Compute hit probability at each grid cell
        wind_norm = np.linalg.norm(wind) + EPS
        wind_dir = wind / wind_norm

        # Distance from each grid cell to observation point
        diff = self.grid - x[None, :]
        dist = np.linalg.norm(diff, axis=1)

        # Wind factor: higher probability upwind of source
        # Dot product of (source - obs) with wind direction
        upwind_proj = np.dot(diff, wind_dir)

        # Hit probability model (advection-diffusion inspired)
        # p(hit | s) ~ exp(-dist^2 / (2*sigma^2)) * exp(max(0, upwind_proj) / lr)
        p_hit = np.exp(-dist ** 2 / (2 * self.sigma ** 2))
        # Upwind bonus: sources upwind of sensor are more likely
        p_hit *= np.exp(np.clip(upwind_proj / self.lr, -5, 5))
        # Distance decay
        p_hit *= np.exp(-dist / self.ld)

        # Normalize
        p_hit = p_hit / (p_hit.sum() + EPS)

        # Bayesian update in log-space
        if hit:
            self.lp += np.log(p_hit + EPS)
        else:
            # Miss: slightly reduce probability at nearby cells
            self.lp += np.log(1.0 - 0.5 * p_hit + EPS)

        # Apply Laplacian smoothing
        penalty = self._laplacian_smooth()
        self.lp -= penalty

        # Normalize log-posterior for numerical stability
        self.lp -= self.lp.max()

    def posterior(self):
        """Return normalized posterior distribution."""
        return self._get_posterior()

    def entropy(self):
        """Compute posterior entropy."""
        post = self._get_posterior()
        return -np.sum(post * np.log(post + EPS))

    def entropy_norm(self):
        """Compute normalized posterior entropy (0 to 1)."""
        H = self.entropy()
        H_max = np.log(max(self.N, 2))
        return H / (H_max + EPS)

    def map_estimate(self):
        """Return MAP (maximum a posteriori) estimate."""
        idx = np.argmax(self.lp)
        return self.grid[idx].copy()


# ---- Unit Tests ----

def test_laplacian_construction():
    """Test that Laplacian is correctly built."""
    occ_2d = np.zeros((5, 5), dtype=int)
    grid = np.array([[i, j] for i in range(5) for j in range(5)], dtype=float)
    emin = np.array([0, 0])
    cell_size = 1.0

    est = MEMPPosteriorEstimator(grid, occ_2d, emin, cell_size, smoothness_weight=0.5)

    # Laplacian should be 25x25 (all free)
    assert est.L.shape == (25, 25), f"Laplacian shape {est.L.shape}, expected (25, 25)"

    # Laplacian should be symmetric
    diff = est.L - est.L.T
    assert diff.nnz == 0 or np.abs(diff.data).max() < 1e-10, "Laplacian not symmetric"

    # Diagonal should be non-negative (degree)
    diag = est.L.diagonal()
    assert np.all(diag >= 0), "Laplacian diagonal has negative values"

    # Row sums should be zero (for Laplacian)
    row_sums = np.array(est.L.sum(axis=1)).flatten()
    assert np.allclose(row_sums, 0, atol=1e-10), "Laplacian row sums not zero"

    print("[OK] Laplacian construction test passed")


def test_smoothness_constraint():
    """Test that Laplacian penalizes isolated peaks."""
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

    print("[OK] Smoothness constraint test passed")


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

    print("[OK] Posterior convergence test passed")


if __name__ == "__main__":
    test_laplacian_construction()
    test_smoothness_constraint()
    test_posterior_convergence()
    print("\n=== All MEMP tests passed! ===")
