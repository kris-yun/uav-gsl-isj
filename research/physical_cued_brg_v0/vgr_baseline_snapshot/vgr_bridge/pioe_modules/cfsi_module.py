"""
PIOE-GSL Module 3: CFSI — Flux-Divergence Source Indicator
===========================================================

Scientific Problem
------------------
Near a gas source, the net outward flux of gas is negative (gas is being
emitted, not dispersed away).  This is captured by the flux divergence:

    div(Cv) = d(Cu)/dx + d(Cv)/dy

In source-free regions, gas is transported away by wind and diffused outward,
so div(Cv) >= 0 (or close to zero at steady state).  Near the source,
div(Cv) < 0 indicates net gas emission.

CFSI computes this flux divergence from the (ADCF-filtered) concentration
and (WDFP-corrected) wind fields, then uses it to enhance the concentration
signal near likely source locations.

Cross-domain source
-------------------
Atmospheric pollution source identification (Seinfeld & Pandis, 2006;
Sharan et al., 1996).  Flux divergence analysis is standard in environmental
engineering for locating emission sources from downwind concentration
measurements.

References
----------
[1] Seinfeld, J.H. & Pandis, S.N. (2006) Atmospheric Chemistry and Physics.
[2] Sharan, M., Yadav, A.K., Singh, M.P. (1996) "Comparison of
    the sigma schemes for estimation of mixing height." Atmos. Env.
[3] Dall'Anese, E., Marden, J.R., Wierman, A. (2012) "Distributed
    optimization for pollution source identification."
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class CFSIConfig:
    """Configuration for Flux-Divergence Source Indicator."""
    beta: float = 0.3                   # enhancement strength
    use_tanh_limit: bool = True          # tanh saturation for safety
    tanh_threshold: float = 0.01         # flux divergence normalisation threshold
    min_enhancement: float = 0.8         # floor for C_enhanced / C_raw ratio
    max_enhancement: float = 1.5         # ceiling for C_enhanced / C_raw ratio


class CFSIProcessor:
    """Flux-Divergence Source Indicator.

    Computes  div(Cv)  from the concentration and wind fields,
    then enhances concentration near negative flux divergence (source).

    Enhancement formula:
        indicator = max(0, -div(Cv)) / threshold
        C_enhanced = C_raw * (1 + beta * tanh(indicator))

    The tanh function limits the enhancement to prevent extreme
    amplification that could fool backend hit/miss thresholds.
    """

    def __init__(self, config: Optional[CFSIConfig] = None):
        self.config = config or CFSIConfig()

    def enhance(
        self,
        C_field: NDArray,
        U_field: NDArray,
        V_field: NDArray,
        dx: float,
        obstacle_mask: Optional[NDArray[np.bool_]] = None,
    ) -> dict:
        """Apply CFSI enhancement to a concentration field.

        Parameters
        ----------
        C_field : 2-D array (ny, nx)
            Concentration field (e.g. ADCF output).
        U_field, V_field : 2-D arrays (ny, nx)
            Wind components (e.g. WDFP output).
        dx : float
            Grid resolution (m).
        obstacle_mask : 2-D bool array, optional
            True where cells are obstacles.

        Returns
        -------
        dict with keys:
            'C_enhanced'    : enhanced concentration field
            'flux_div'      : raw flux divergence field
            'indicator'     : source indicator field (positive near source)
            'enhancement_ratio' : C_enhanced / C_raw ratio
        """
        cfg = self.config
        ny, nx = C_field.shape

        # Step 1: Compute flux  F = C * v
        Fx = C_field * U_field
        Fy = C_field * V_field

        # Step 2: Compute divergence of flux:  div(Cv) = dFx/dx + dFy/dy
        flux_div = self._compute_divergence(Fx, Fy, dx)

        # Step 3: Source indicator: negative flux_div indicates source
        # Only source regions (negative divergence) get enhanced
        indicator = np.maximum(0.0, -flux_div)

        # Normalise
        if cfg.tanh_threshold > 0:
            indicator_norm = indicator / cfg.tanh_threshold
        else:
            indicator_norm = indicator

        # Step 4: Enhancement factor with tanh saturation
        if cfg.use_tanh_limit:
            enhancement = 1.0 + cfg.beta * np.tanh(indicator_norm)
        else:
            enhancement = 1.0 + cfg.beta * indicator_norm

        # Clip enhancement ratio for safety
        enhancement = np.clip(enhancement, cfg.min_enhancement, cfg.max_enhancement)

        # Step 5: Apply enhancement
        C_enhanced = C_field * enhancement

        # Apply obstacle mask
        if obstacle_mask is not None and obstacle_mask.shape == (ny, nx):
            C_enhanced[obstacle_mask] = 0.0
            enhancement[obstacle_mask] = 1.0

        return {
            'C_enhanced': C_enhanced,
            'flux_div': flux_div,
            'indicator': indicator,
            'enhancement_ratio': enhancement,
        }

    @staticmethod
    def _compute_divergence(Fx: NDArray, Fy: NDArray, dx: float) -> NDArray:
        """Compute divergence: div(F) = dFx/dx + dFy/dy.
        
        Handles both 2-D (ny>1) and 1-D (ny==1) cases.
        For 1-D, only computes dFx/dx (no y-component).
        """
        ny, nx = Fx.shape

        dFx_dx = np.zeros_like(Fx)
        if nx >= 3:
            dFx_dx[:, 1:-1] = (Fx[:, 2:] - Fx[:, :-2]) / (2 * dx)
        if nx >= 2:
            dFx_dx[:, 0] = (Fx[:, 1] - Fx[:, 0]) / dx
            dFx_dx[:, -1] = (Fx[:, -1] - Fx[:, -2]) / dx

        dFy_dy = np.zeros_like(Fy)
        if ny >= 3:
            dFy_dy[1:-1, :] = (Fy[2:, :] - Fy[:-2, :]) / (2 * dx)
        if ny >= 2:
            dFy_dy[0, :] = (Fy[1, :] - Fy[0, :]) / dx
            dFy_dy[-1, :] = (Fy[-1, :] - Fy[-2, :]) / dx

        return dFx_dx + dFy_dy


def enhance_concentration_cfsi(
    C_field: NDArray,
    U_field: NDArray,
    V_field: NDArray,
    dx: float,
    obstacle_mask: Optional[NDArray[np.bool_]] = None,
    config: Optional[CFSIConfig] = None,
) -> dict:
    """Convenience function: run CFSI."""
    processor = CFSIProcessor(config)
    return processor.enhance(C_field, U_field, V_field, dx, obstacle_mask)
