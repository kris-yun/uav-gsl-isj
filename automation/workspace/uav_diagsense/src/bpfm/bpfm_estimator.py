"""Bayesian Particle Flow Mapping (BPFM) for Gas Source Localization.

Borrowed from: Epidemiological source estimation (Riley et al., 2003;
Wallinga & Teunis, 2004 — back-tracing infection chains along transport networks).

Core idea: Maintain particles representing candidate source locations.
Particles flow along wind trajectories instead of random diffusion:
  - Gas detected  → particles flow UPWIND (toward source)
  - No gas        → particles diffuse slightly (exploration)

Cross-domain mapping:
  - Transport network → wind field
  - Infection chain   → gas plume trajectory
  - Contact tracing   → upwind back-trace
  - Superspreader     → high-concentration zone
"""
import numpy as np

EPS = 1e-12


class BPFMEstimator:
    """Particle-based posterior estimator with wind-driven flow.

    Maintains N particles in 2D space. Each step:
      1. Flow: move particles along wind (upwind on hit, diffuse on miss)
      2. Weight: reweight by observation likelihood
      3. Resample: systematic resampling when ESS drops below threshold

    The posterior is a kernel density estimate over particle positions.
    """

    def __init__(self, grid, occ_2d, emin, cell_size,
                 n_particles=200, flow_speed=0.8, diffusion_sigma=0.3,
                 sigma_obs=2.0, ess_threshold=0.5):
        self.grid = np.asarray(grid, dtype=np.float64)
        self.occ_2d = occ_2d
        self.emin = np.asarray(emin, dtype=np.float64)
        self.cell_size = cell_size
        self.n_particles = n_particles
        self.flow_speed = flow_speed
        self.diffusion_sigma = diffusion_sigma
        self.sigma_obs = sigma_obs
        self.ess_threshold = ess_threshold

        self.nx, self.ny = occ_2d.shape
        self.free_mask = occ_2d == 0

        # Initialize particles uniformly over free grid cells
        free_idx = np.array([i for i, g in enumerate(grid)
                             if self._is_free(g)])
        if len(free_idx) == 0:
            free_idx = np.arange(len(grid))
        init_idx = np.random.default_rng(42).choice(
            free_idx, size=n_particles, replace=True)
        self.particles = self.grid[init_idx].copy()
        self.weights = np.ones(n_particles) / n_particles

        # Grid-to-index for KDE on grid
        self.N = len(grid)

    def _is_free(self, xy):
        fi = int(round((xy[0] - self.emin[0]) / self.cell_size))
        fj = int(round((xy[1] - self.emin[1]) / self.cell_size))
        if 0 <= fi < self.nx and 0 <= fj < self.ny:
            return self.free_mask[fi, fj]
        return False

    def _clip_to_free(self, xy):
        """Clip position to environment bounds."""
        xy[0] = np.clip(xy[0], self.emin[0],
                        self.emin[0] + self.nx * self.cell_size)
        xy[1] = np.clip(xy[1], self.emin[1],
                        self.emin[1] + self.ny * self.cell_size)
        return xy

    def update(self, x, wind, hit):
        """Update particles with new observation.

        Args:
            x: (2,) observation position
            wind: (2,) wind vector
            hit: bool, gas detected
        """
        x = np.asarray(x[:2], dtype=np.float64)
        wind = np.asarray(wind[:2], dtype=np.float64)
        wn = np.linalg.norm(wind)
        if wn < EPS:
            wind_hat = np.array([1.0, 0.0])
        else:
            wind_hat = wind / wn

        rng = np.random.default_rng(
            int(x[0] * 1000 + x[1] * 100) % 2**31)

        # --- Flow step ---
        if hit:
            # Upwind flow: if gas detected at x, source is upwind
            flow = -wind_hat * self.flow_speed
            self.particles += flow
            # Small isotropic diffusion
            self.particles += rng.normal(0, self.diffusion_sigma * 0.2,
                                        self.particles.shape)
        else:
            # No gas: diffuse particles (explore)
            self.particles += rng.normal(0, self.diffusion_sigma,
                                        self.particles.shape)

        # Clip to bounds
        for i in range(self.n_particles):
            self._clip_to_free(self.particles[i])

        # --- Weight update ---
        # Source is upwind of observation when gas is detected
        diff = self.particles - x[None, :]  # particle - obs
        dists = np.linalg.norm(diff, axis=1)
        if hit:
            # Upwind likelihood: particles upwind of x are better source candidates
            upwind_proj = -diff @ wind_hat  # positive = particle is upwind of x
            crosswind = np.sqrt(np.maximum(dists**2 - upwind_proj**2, 0))
            # High weight for particles upwind and aligned with plume axis
            ll = np.exp(-upwind_proj.clip(max=0)**2 / (2 * self.sigma_obs**2)
                        - crosswind**2 / (2 * (self.sigma_obs * 0.5)**2))
            # Penalize particles too far downwind
            ll *= np.exp(-np.maximum(-upwind_proj, 0) / (self.sigma_obs * 2))
        else:
            # Miss: penalize particles near observation (source not here)
            ll = 1.0 - 0.5 * np.exp(-dists ** 2 / (2 * self.sigma_obs ** 2))
            ll = np.maximum(ll, EPS)

        self.weights *= ll
        self.weights /= self.weights.sum() + EPS

        # --- Resample if ESS too low ---
        ess = 1.0 / (np.sum(self.weights ** 2) + EPS)
        if ess < self.ess_threshold * self.n_particles:
            self._systematic_resample(rng)

    def _systematic_resample(self, rng):
        """Systematic resampling to combat particle degeneracy."""
        n = self.n_particles
        positions = (np.arange(n) + rng.uniform()) / n
        cumsum = np.cumsum(self.weights)
        cumsum[-1] = 1.0
        indices = np.searchsorted(cumsum, positions)
        indices = np.clip(indices, 0, n - 1)
        self.particles = self.particles[indices].copy()
        self.weights = np.ones(n) / n
        # Add jitter to prevent collapse
        self.particles += rng.normal(0, 0.15, self.particles.shape)

    def posterior(self):
        """KDE over grid from weighted particles."""
        post = np.zeros(self.N, dtype=np.float64)
        for i, g in enumerate(self.grid):
            dists = np.linalg.norm(self.particles - g[None, :], axis=1)
            k = np.exp(-dists ** 2 / (2 * self.cell_size ** 2))
            post[i] = np.sum(self.weights * k)
        s = post.sum()
        return post / s if s > EPS else np.ones(self.N) / self.N

    def entropy(self):
        p = self.posterior()
        return float(-np.sum(p * np.log(p + EPS)))

    def entropy_norm(self):
        return self.entropy() / np.log(self.N) if self.N > 1 else 1.0

    def map_estimate(self):
        p = self.posterior()
        return self.grid[np.argmax(p)].copy()

    def particle_centroid(self):
        return np.average(self.particles, axis=0, weights=self.weights)
