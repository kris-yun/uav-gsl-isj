"""
PIOE-GSL Module 1: WDFP — Wind-Field Divergence-Free Projection
================================================================

Solves  laplacian(phi) = div(v)  via Jacobi iteration with Neumann BC.
Then:  v_corrected = v - grad(phi)  is divergence-free.

References
----------
[1] Chorin (1968) Math. Comp. 22, 745-762.
[2] Temam (1969) Arch. Rat. Mech. Anal. 32, 135-153.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class WDFPConfig:
    """Configuration for Wind-Field Divergence-Free Projection."""
    grid_resolution: float = 0.25
    jacobi_max_iter: int = 500
    jacobi_tol: float = 1e-6
    interp_power: float = 2.0
    amplitude_preserve_ratio: float = 0.5  # min ||v_corr||/||v_orig|| before fallback


@dataclass
class WindObservation:
    """A single wind speed observation."""
    x: float
    y: float
    u: float
    v: float


class WDFPProcessor:
    """Wind-Field Divergence-Free Projection processor."""

    def __init__(self, config: Optional[WDFPConfig] = None):
        self.config = config or WDFPConfig()

    def project(
        self,
        observations: list[WindObservation],
        domain_bounds: Tuple[float, float, float, float],
        obstacle_mask: Optional[NDArray[np.bool_]] = None,
    ) -> dict:
        cfg = self.config
        xmin, xmax, ymin, ymax = domain_bounds
        dx = cfg.grid_resolution

        nx = max(2, int(np.ceil((xmax - xmin) / dx)) + 1)
        ny = max(2, int(np.ceil((ymax - ymin) / dx)) + 1)
        gx = xmin + np.arange(nx) * dx
        gy = ymin + np.arange(ny) * dx
        XX, YY = np.meshgrid(gx, gy)

        U, V = self._idw_interpolate(observations, XX, YY, nx, ny)

        if obstacle_mask is not None and obstacle_mask.shape == (ny, nx):
            U[obstacle_mask] = 0.0
            V[obstacle_mask] = 0.0

        div_before = self._compute_divergence(U, V, dx)
        phi = self._solve_poisson_jacobi(div_before, obstacle_mask, dx, cfg, ny, nx)
        dphi_dx, dphi_dy = self._compute_gradient(phi, dx)
        U_corr = U - dphi_dx
        V_corr = V - dphi_dy

        if obstacle_mask is not None and obstacle_mask.shape == (ny, nx):
            U_corr[obstacle_mask] = 0.0
            V_corr[obstacle_mask] = 0.0

        # --- Amplitude preservation ---
        # The Poisson correction can drastically change wind magnitude.
        # Rescale so that ||v_corr|| ~ ||v_orig||, preserving the
        # divergence-free direction but not the spurious amplitude shift.
        norm_orig = np.sqrt(U**2 + V**2)
        norm_corr = np.sqrt(U_corr**2 + V_corr**2)
        sum_orig = float(np.sum(norm_orig))
        sum_corr = float(np.sum(norm_corr))

        if sum_corr > 1e-12 and sum_orig > 1e-12:
            ratio = sum_corr / sum_orig
            if ratio < cfg.amplitude_preserve_ratio:
                # Correction destroyed the wind field -- fall back to original
                U_corr = U.copy()
                V_corr = V.copy()
            elif ratio < 1.0:
                # Rescale to preserve original amplitude
                scale = sum_orig / sum_corr
                U_corr = U_corr * scale
                V_corr = V_corr * scale

        if obstacle_mask is not None and obstacle_mask.shape == (ny, nx):
            U_corr[obstacle_mask] = 0.0
            V_corr[obstacle_mask] = 0.0

        div_after = self._compute_divergence(U_corr, V_corr, dx)

        return {
            'u_corr': U_corr, 'v_corr': V_corr,
            'div_before': div_before, 'div_after': div_after,
            'phi': phi, 'grid_x': gx, 'grid_y': gy,
            'grid_resolution': dx, 'domain_bounds': domain_bounds,
        }

    def _idw_interpolate(self, obs, XX, YY, nx, ny):
        if len(obs) == 0:
            return np.zeros((ny, nx)), np.zeros((ny, nx))

        ox = np.array([o.x for o in obs])
        oy = np.array([o.y for o in obs])
        ou = np.array([o.u for o in obs])
        ov = np.array([o.v for o in obs])

        dx_all = XX[:, :, np.newaxis] - ox[np.newaxis, np.newaxis, :]
        dy_all = YY[:, :, np.newaxis] - oy[np.newaxis, np.newaxis, :]
        dist = np.sqrt(dx_all**2 + dy_all**2)

        min_dist = dist.min(axis=2, keepdims=True)
        exact_mask = min_dist < 1e-10
        dist_safe = np.where(dist < 1e-10, 1.0, dist)
        w = 1.0 / (dist_safe ** self.config.interp_power)
        if np.any(exact_mask):
            w = np.where(exact_mask & (dist < 1e-10), 1.0, w * (~exact_mask))

        w_sum = w.sum(axis=2, keepdims=True)
        w_sum = np.where(w_sum < 1e-30, 1.0, w_sum)
        U = (w * ou[np.newaxis, np.newaxis, :]).sum(axis=2) / w_sum[:, :, 0]
        V = (w * ov[np.newaxis, np.newaxis, :]).sum(axis=2) / w_sum[:, :, 0]
        return U, V

    @staticmethod
    def _compute_divergence(U, V, dx):
        ny, nx = U.shape
        dudx = np.zeros_like(U)
        dudx[:, 1:-1] = (U[:, 2:] - U[:, :-2]) / (2 * dx)
        dudx[:, 0] = (U[:, 1] - U[:, 0]) / dx
        dudx[:, -1] = (U[:, -1] - U[:, -2]) / dx
        dvdy = np.zeros_like(V)
        dvdy[1:-1, :] = (V[2:, :] - V[:-2, :]) / (2 * dx)
        dvdy[0, :] = (V[1, :] - V[0, :]) / dx
        dvdy[-1, :] = (V[-1, :] - V[-2, :]) / dx
        return dudx + dvdy

    @staticmethod
    def _compute_gradient(phi, dx):
        dphi_dx = np.zeros_like(phi)
        dphi_dy = np.zeros_like(phi)
        dphi_dx[:, 1:-1] = (phi[:, 2:] - phi[:, :-2]) / (2 * dx)
        dphi_dx[:, 0] = (phi[:, 1] - phi[:, 0]) / dx
        dphi_dx[:, -1] = (phi[:, -1] - phi[:, -2]) / dx
        dphi_dy[1:-1, :] = (phi[2:, :] - phi[:-2, :]) / (2 * dx)
        dphi_dy[0, :] = (phi[1, :] - phi[0, :]) / dx
        dphi_dy[-1, :] = (phi[-1, :] - phi[-2, :]) / dx
        return dphi_dx, dphi_dy

    @staticmethod
    def _solve_poisson_jacobi(rhs, obstacle_mask, dx, cfg, ny, nx):
        """Solve laplacian(phi) = rhs with Jacobi iteration + Neumann BC."""
        phi = np.zeros((ny, nx), dtype=np.float64)
        dx2 = dx * dx

        interior = np.ones((ny, nx), dtype=bool)
        if obstacle_mask is not None:
            interior &= ~obstacle_mask

        # 1-D neighbour index arrays (no extra dimension)
        i_n = np.clip(np.arange(ny) - 1, 0, ny - 1)
        i_s = np.clip(np.arange(ny) + 1, 0, ny - 1)
        j_w = np.clip(np.arange(nx) - 1, 0, nx - 1)
        j_e = np.clip(np.arange(nx) + 1, 0, nx - 1)

        for iteration in range(cfg.jacobi_max_iter):
            phi_n = phi[i_n, :]   # shape (ny, nx)
            phi_s = phi[i_s, :]
            phi_w = phi[:, j_w]
            phi_e = phi[:, j_e]

            phi_new = (phi_n + phi_s + phi_w + phi_e - rhs * dx2) / 4.0
            phi_new = np.where(interior, phi_new, phi)
            phi_new -= phi_new[0, 0]  # pin for uniqueness

            max_diff = np.max(np.abs(phi_new - phi))
            phi = phi_new
            if max_diff < cfg.jacobi_tol:
                break

        return phi


def compute_divergence_free_wind(observations, domain_bounds, obstacle_mask=None, config=None):
    processor = WDFPProcessor(config)
    return processor.project(observations, domain_bounds, obstacle_mask)
