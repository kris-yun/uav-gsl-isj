"""
PIOE-GSL Module 2: ADCF — Advection-Diffusion Consistency Filter
=================================================================

Solves:  min_C  ||C - C_raw||^2 / sigma^2 + lambda * ||L(C)||^2
where L(C) = u*dC/dx + v*dC/dy - D*laplacian(C)

References
----------
[1] Seinfeld & Pandis (2006) Atmospheric Chemistry and Physics.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class ADCFConfig:
    """Configuration for Advection-Diffusion Consistency Filter."""
    grid_resolution: float = 0.25
    diffusion_coeff: float = 0.01
    lambda_phys: float = 0.05       # physics as soft constraint (was 0.5)
    sigma_c: float = 0.2            # wider data fidelity window (was 0.05)
    max_iter: int = 100
    convergence_tol: float = 1e-6
    min_amplitude_ratio: float = 0.5  # C_filtered >= ratio * C_raw


@dataclass
class ConcentrationObservation:
    """A single concentration + wind observation."""
    x: float
    y: float
    concentration: float
    u: float
    v: float
    timestamp: float = 0.0


class ADCFProcessor:
    """Advection-Diffusion Consistency Filter."""

    def __init__(self, config: Optional[ADCFConfig] = None):
        self.config = config or ADCFConfig()

    def filter_observations(self, observations, domain_bounds, obstacle_mask=None):
        cfg = self.config
        xmin, xmax, ymin, ymax = domain_bounds
        dx = cfg.grid_resolution

        nx = max(2, int(np.ceil((xmax - xmin) / dx)) + 1)
        ny = max(2, int(np.ceil((ymax - ymin) / dx)) + 1)
        gx = xmin + np.arange(nx) * dx
        gy = ymin + np.arange(ny) * dx
        XX, YY = np.meshgrid(gx, gy)

        C_raw = self._idw_c(observations, XX, YY, nx, ny)
        U, V = self._idw_uv(observations, XX, YY, nx, ny)

        steady_ratio = self._check_steady_state(observations)
        C_filtered = self._solve(C_raw, U, V, obstacle_mask, cfg, ny, nx, dx)
        residual = self._physics_residual(C_filtered, U, V, cfg.diffusion_coeff, dx, ny, nx)

        return {
            'C_filtered': C_filtered, 'C_raw': C_raw,
            'residual': residual, 'steady_ratio': steady_ratio,
            'grid_x': gx, 'grid_y': gy,
            'grid_resolution': dx, 'nx': nx, 'ny': ny,
        }

    # IDW helpers

    def _idw_c(self, obs, XX, YY, nx, ny):
        if not obs:
            return np.zeros((ny, nx))
        ox = np.array([o.x for o in obs])
        oy = np.array([o.y for o in obs])
        oc = np.array([o.concentration for o in obs])
        return self._idw(ox, oy, oc, XX, YY)

    def _idw_uv(self, obs, XX, YY, nx, ny):
        if not obs:
            return np.zeros((ny, nx)), np.zeros((ny, nx))
        ox = np.array([o.x for o in obs])
        oy = np.array([o.y for o in obs])
        ou = np.array([o.u for o in obs])
        ov = np.array([o.v for o in obs])
        return self._idw(ox, oy, ou, XX, YY), self._idw(ox, oy, ov, XX, YY)

    @staticmethod
    def _idw(ox, oy, oval, XX, YY):
        dx_all = XX[:, :, np.newaxis] - ox[np.newaxis, np.newaxis, :]
        dy_all = YY[:, :, np.newaxis] - oy[np.newaxis, np.newaxis, :]
        dist = np.sqrt(dx_all**2 + dy_all**2)
        min_dist = dist.min(axis=2, keepdims=True)
        exact_mask = min_dist < 1e-10
        dist_safe = np.where(dist < 1e-10, 1.0, dist)
        w = 1.0 / (dist_safe ** 2.0)
        if np.any(exact_mask):
            w = np.where(exact_mask & (dist < 1e-10), 1.0, w * (~exact_mask))
        w_sum = w.sum(axis=2, keepdims=True)
        w_sum = np.where(w_sum < 1e-30, 1.0, w_sum)
        return (w * oval[np.newaxis, np.newaxis, :]).sum(axis=2) / w_sum[:, :, 0]

    @staticmethod
    def _check_steady_state(obs):
        if len(obs) < 2:
            return 0.0
        ts = np.array([o.timestamp for o in obs])
        if ts.max() - ts.min() < 0.1:
            return 0.0
        concs = np.array([o.concentration for o in obs])
        return float(np.std(concs) / max(1.0, ts.max() - ts.min()))

    # Solver

    def _solve(self, C_raw, U, V, obstacle_mask, cfg, ny, nx, dx):
        C = C_raw.copy().astype(np.float64)
        D = cfg.diffusion_coeff
        lam = cfg.lambda_phys
        s2 = cfg.sigma_c ** 2
        dx2 = dx * dx

        valid = np.ones((ny, nx), dtype=bool)
        if obstacle_mask is not None:
            valid &= ~obstacle_mask

        # 1-D neighbour indices
        i_n = np.clip(np.arange(ny) - 1, 0, ny - 1)
        i_s = np.clip(np.arange(ny) + 1, 0, ny - 1)
        j_w = np.clip(np.arange(nx) - 1, 0, nx - 1)
        j_e = np.clip(np.arange(nx) + 1, 0, nx - 1)

        # Adaptive step size
        u_max = max(np.max(np.abs(U)), 0.1)
        spectral = 4.0 * D**2 / dx2**2 + u_max**2 / dx2
        alpha = 1.0 / (1.0 / s2 + lam * spectral + 1e-10)
        alpha = min(alpha, 0.5)

        for iteration in range(cfg.max_iter):
            C_old = C.copy()

            r = self._ad_op(C, U, V, D, dx, i_n, i_s, j_w, j_e, ny, nx)
            LT_r = self._adjoint(r, U, V, D, dx, i_n, i_s, j_w, j_e, ny, nx)
            grad = (C - C_raw) / s2 + lam * LT_r
            grad = np.where(valid, grad, 0.0)

            C = C - alpha * grad
            C = np.maximum(C, 0.0)
            if obstacle_mask is not None:
                C[obstacle_mask] = C_raw[obstacle_mask]

            if np.max(np.abs(C - C_old)) < cfg.convergence_tol:
                break

        # --- Concentration amplitude protection ---
        # Prevent the filter from suppressing concentration below
        # a configurable fraction of the raw interpolated value.
        ratio = cfg.min_amplitude_ratio
        C = np.maximum(C, C_raw * ratio)
        C = np.maximum(C, 0.0)

        return C

    # Operators (1-D indices)

    @staticmethod
    def _ad_op(C, U, V, D, dx, i_n, i_s, j_w, j_e, ny, nx):
        C_n = C[i_n, :]
        C_s = C[i_s, :]
        C_w = C[:, j_w]
        C_e = C[:, j_e]
        dCdx = (C_e - C_w) / (2 * dx)
        dCdy = (C_s - C_n) / (2 * dx)
        lapC = (C_n + C_s + C_w + C_e - 4 * C) / (dx * dx)
        return U * dCdx + V * dCdy - D * lapC

    @staticmethod
    def _adjoint(r, U, V, D, dx, i_n, i_s, j_w, j_e, ny, nx):
        ur = U * r
        vr = V * r
        dur_dx = (ur[:, j_e] - ur[:, j_w]) / (2 * dx)
        dvr_dy = (vr[i_s, :] - vr[i_n, :]) / (2 * dx)
        r_n = r[i_n, :]
        r_s = r[i_s, :]
        r_w = r[:, j_w]
        r_e = r[:, j_e]
        lap_r = (r_n + r_s + r_w + r_e - 4 * r) / (dx * dx)
        return -dur_dx - dvr_dy - D * lap_r

    @staticmethod
    def _physics_residual(C, U, V, D, dx, ny, nx):
        i_n = np.clip(np.arange(ny) - 1, 0, ny - 1)
        i_s = np.clip(np.arange(ny) + 1, 0, ny - 1)
        j_w = np.clip(np.arange(nx) - 1, 0, nx - 1)
        j_e = np.clip(np.arange(nx) + 1, 0, nx - 1)
        C_n = C[i_n, :]
        C_s = C[i_s, :]
        C_w = C[:, j_w]
        C_e = C[:, j_e]
        dCdx = (C_e - C_w) / (2 * dx)
        dCdy = (C_s - C_n) / (2 * dx)
        lapC = (C_n + C_s + C_w + C_e - 4 * C) / (dx * dx)
        return np.abs(U * dCdx + V * dCdy - D * lapC)


def filter_concentration_adcf(observations, domain_bounds, obstacle_mask=None, config=None):
    processor = ADCFProcessor(config)
    return processor.filter_observations(observations, domain_bounds, obstacle_mask)
