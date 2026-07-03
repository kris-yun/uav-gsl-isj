"""Sparse Deconvolution Mapping (SDM) for Gas Source Localization.

Borrowed from: Image deblurring / L1 sparse deconvolution
Papers: Beck & Teboulle (2009) ISTA/FISTA; Rudin-Osher-Fatemi (1992) TV denoising

Core idea: Wind causes the gas plume to be "smeared" downwind, like motion blur
in images. The Bayesian posterior inherits this blur — the source appears shifted
and spread in the downwind direction. SDM deconvolves this blur using L1-regularized
sparse recovery, sharpening the posterior to recover the true source location.

Cross-domain mapping:
  - Motion blur kernel  → wind-induced smearing (asymmetric, downwind)
  - Blurred image       → blurred posterior
  - Sparse original     → sparse source (one or few point sources)
  - L1 regularization   → source sparsity prior
"""
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import LinearOperator

EPS = 1e-12


class SDMEstimator:
    """Sparse Deconvolution posterior estimator.

    Wraps a standard posterior estimator and applies wind-aware
    L1 deconvolution to sharpen the result.

    Algorithm (ISTA — Iterative Shrinkage/Thresholding):
        s_{k+1} = soft_threshold(s_k - alpha * K^T(K*s_k - b), lambda*alpha)

    Where:
        b = observed (blurred) posterior
        K = wind blur kernel (asymmetric Gaussian elongated downwind)
        s = deconvolved (sharp) source distribution
        lambda = sparsity weight
    """

    def __init__(self, grid, occ_2d, emin, cell_size,
                 blur_sigma_cross=1.0, blur_sigma_along=3.0,
                 sparsity_weight=0.05, n_iter=20):
        self.grid = np.asarray(grid, dtype=np.float64)
        self.N = len(grid)
        self.occ_2d = occ_2d
        self.emin = np.asarray(emin, dtype=np.float64)
        self.cell_size = cell_size
        self.blur_sigma_cross = blur_sigma_cross
        self.blur_sigma_along = blur_sigma_along
        self.sparsity_weight = sparsity_weight
        self.n_iter = n_iter

        # Internal log-posterior (standard Bayesian)
        self.lp = np.zeros(self.N, dtype=np.float64)
        self._deconvolved = np.ones(self.N) / self.N

    def update(self, x, wind, hit, weight=1.0):
        """Standard Bayesian update to internal posterior.

        Args:
            x: (2,) observation position
            wind: (2,) wind vector
            hit: bool, gas detected
            weight: observation weight
        """
        x = np.asarray(x[:2], dtype=np.float64)
        wind = np.asarray(wind[:2], dtype=np.float64)
        wn = np.linalg.norm(wind)
        if wn < EPS:
            return
        u = wind / wn

        # Distance decomposition: along-wind and cross-wind
        d = x[None, :] - self.grid
        dp = d @ u  # along-wind projection
        dp2 = np.sum((d - dp[:, None] * u[None, :]) ** 2, axis=1)  # cross-wind dist^2

        sigma = 3.0
        lr = 15.0
        ld = 20.0
        sd = sigma + 0.2 * np.sqrt(np.maximum(dp, 0) + EPS)

        if hit:
            ll = np.where(
                dp > 0,
                -dp2 / (2 * sd**2 + EPS) - np.maximum(dp, 0) / lr,
                -ld
            )
        else:
            ll = np.where(
                dp > 0,
                np.log(1 - np.exp(-dp2 / (2 * sd**2 + EPS)) + EPS),
                0.0
            )

        self.lp += weight * ll
        self.lp -= np.max(self.lp)

    def _build_blur_kernel(self, wind):
        """Build asymmetric blur kernel aligned with wind direction.

        The kernel is elongated in the downwind direction (motion blur analogy):
        - Cross-wind sigma: small (sharp perpendicular to wind)
        - Along-wind sigma: large (smeared downwind)
        """
        wn = np.linalg.norm(wind)
        if wn < EPS:
            u = np.array([1.0, 0.0])
        else:
            u = wind / wn
        perp = np.array([-u[1], u[0]])

        K = np.zeros((self.N, self.N), dtype=np.float64)
        for i in range(self.N):
            diff = self.grid - self.grid[i]
            along = diff @ u  # positive = downwind of cell i
            cross = diff @ perp
            # Asymmetric: only smear downwind (positive along)
            kernel_val = np.exp(
                -np.maximum(along, 0)**2 / (2 * self.blur_sigma_along**2)
                - cross**2 / (2 * self.blur_sigma_cross**2)
            )
            # Also allow small upwind contribution
            kernel_val += 0.1 * np.exp(
                -np.maximum(-along, 0)**2 / (2 * self.blur_sigma_cross**2)
                - cross**2 / (2 * self.blur_sigma_cross**2)
            )
            K[i] = kernel_val / (kernel_val.sum() + EPS)
        return K

    def deconvolve(self, wind):
        """Apply L1 deconvolution to sharpen the blurred posterior.

        Solves: min_s ||K*s - b||^2 + lambda * ||s||_1
        via ISTA (Iterative Shrinkage/Thresholding Algorithm).

        Args:
            wind: (2,) current wind vector for kernel construction
        """
        b = self.posterior_raw()
        if b.sum() < EPS:
            self._deconvolved = np.ones(self.N) / self.N
            return

        K = self._build_blur_kernel(wind)
        KT = K.T

        # ISTA parameters
        # Lipschitz constant estimate: ||K^T K||_2 ≈ max eigenvalue
        # Conservative estimate: use max row sum of K^T K
        KtK = KT @ K
        L = float(np.max(np.abs(KtK.sum(axis=1)))) + EPS
        alpha = 1.0 / L  # step size

        s = b.copy()  # initialize with blurred posterior
        lam = self.sparsity_weight

        for _ in range(self.n_iter):
            # Gradient step
            residual = K @ s - b
            grad = KT @ residual
            s_new = s - alpha * grad

            # Soft thresholding (L1 proximal operator)
            s_new = np.sign(s_new) * np.maximum(np.abs(s_new) - lam * alpha, 0)

            # Non-negativity and normalization
            s_new = np.maximum(s_new, 0)
            s_sum = s_new.sum()
            if s_sum > EPS:
                s_new /= s_sum
            else:
                s_new = b.copy()

            s = s_new

        self._deconvolved = s

    def posterior_raw(self):
        """Blurred posterior (standard Bayesian)."""
        p = np.exp(self.lp)
        s = p.sum()
        return p / s if s > EPS else np.ones(self.N) / self.N

    def posterior(self):
        """Deconvolved (sharp) posterior."""
        return self._deconvolved

    def entropy(self):
        p = self.posterior()
        return float(-np.sum(p * np.log(p + EPS)))

    def entropy_norm(self):
        return self.entropy() / np.log(self.N) if self.N > 1 else 1.0

    def map_estimate(self):
        return self.grid[np.argmax(self.posterior())].copy()

    def reset(self):
        self.lp = np.zeros(self.N, dtype=np.float64)
        self._deconvolved = np.ones(self.N) / self.N
