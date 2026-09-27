"""
PIOE-GSL Pipeline: Physics-Informed Observation Enhancement
============================================================

Chains the three modules in order:
    Raw observations -> WDFP -> ADCF -> CFSI -> Enhanced observations -> Backend

This is the main entry point for the ROS2 integration node.

Usage
-----
    from modules.pioe_pipeline import PIOEPipeline, PIOEConfig

    pipe = PIOEPipeline()
    result = pipe.process(gas_obs, wind_obs, domain_bounds, obstacle_mask)
    # result['C_enhanced'], result['U_corrected'], result['V_corrected']
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from dataclasses import dataclass
from typing import Optional, Tuple, List

from modules.wdpf_module import WDFPProcessor, WDFPConfig, WindObservation
from modules.adcf_module import ADCFProcessor, ADCFConfig, ConcentrationObservation
from modules.cfsi_module import CFSIProcessor, CFSIConfig


@dataclass
class PIOEConfig:
    """Configuration for the full PIOE-GSL pipeline."""
    wdfp: WDFPConfig = None
    adcf: ADCFConfig = None
    cfsi: CFSIConfig = None
    enable_wdfp: bool = True
    enable_adcf: bool = True
    enable_cfsi: bool = True
    grid_resolution: float = 0.25

    def __post_init__(self):
        if self.wdfp is None:
            self.wdfp = WDFPConfig(grid_resolution=self.grid_resolution)
        if self.adcf is None:
            self.adcf = ADCFConfig(grid_resolution=self.grid_resolution)
        if self.cfsi is None:
            self.cfsi = CFSIConfig()


@dataclass
class PIOEObservation:
    """A combined gas + wind observation at a single point."""
    x: float
    y: float
    concentration: float
    wind_u: float
    wind_v: float
    timestamp: float = 0.0


class PIOEPipeline:
    """PIOE-GSL pipeline: WDFP -> ADCF -> CFSI.

    Takes raw gas+wind observations and produces physically
    enhanced observations suitable for any GSL backend.
    """

    def __init__(self, config: Optional[PIOEConfig] = None):
        self.config = config or PIOEConfig()
        self.wdfp = WDFPProcessor(self.config.wdfp) if self.config.enable_wdfp else None
        self.adcf = ADCFProcessor(self.config.adcf) if self.config.enable_adcf else None
        self.cfsi = CFSIProcessor(self.config.cfsi) if self.config.enable_cfsi else None

    def process(
        self,
        observations: List[PIOEObservation],
        domain_bounds: Tuple[float, float, float, float],
        obstacle_mask: Optional[NDArray[np.bool_]] = None,
    ) -> dict:
        """Run the full PIOE-GSL pipeline.

        Parameters
        ----------
        observations : list of PIOEObservation
            Combined gas concentration + wind measurements.
        domain_bounds : (xmin, xmax, ymin, ymax)
            Physical domain bounds.
        obstacle_mask : 2-D bool array, optional
            True where cells are obstacles.

        Returns
        -------
        dict with keys:
            'C_enhanced'    : final enhanced concentration field (2-D)
            'U_corrected'   : divergence-free wind U field (2-D)
            'V_corrected'   : divergence-free wind V field (2-D)
            'wdfp_result'   : WDFP output (or None)
            'adcf_result'   : ADCF output (or None)
            'cfsi_result'   : CFSI output (or None)
            'grid_x', 'grid_y' : 1-D coordinate arrays
            'modules_active' : dict of which modules were active
        """
        # Convert observations to module-specific formats
        wind_obs = [
            WindObservation(o.x, o.y, o.wind_u, o.wind_v)
            for o in observations
        ]
        conc_obs = [
            ConcentrationObservation(o.x, o.y, o.concentration, o.wind_u, o.wind_v, o.timestamp)
            for o in observations
        ]

        # Get grid parameters
        xmin, xmax, ymin, ymax = domain_bounds
        dx = self.config.grid_resolution
        nx = max(2, int(np.ceil((xmax - xmin) / dx)) + 1)
        ny = max(2, int(np.ceil((ymax - ymin) / dx)) + 1)
        gx = xmin + np.arange(nx) * dx
        gy = ymin + np.arange(ny) * dx

        # ---- Stage 1: WDFP (wind field correction) ----
        wdfp_result = None
        if self.wdfp is not None:
            wdfp_result = self.wdfp.project(wind_obs, domain_bounds, obstacle_mask)
            U = wdfp_result['u_corr']
            V = wdfp_result['v_corr']
            print("WDFP: divergence corrected")
        else:
            # Fall back to raw IDW interpolation
            from modules.wdpf_module import WDFPProcessor
            U, V = WDFPProcessor()._idw_interpolate(wind_obs, *np.meshgrid(gx, gy), nx, ny)

        # ---- Stage 2: ADCF (concentration filtering) ----
        adcf_result = None
        if self.adcf is not None:
            adcf_result = self.adcf.filter_observations(conc_obs, domain_bounds, obstacle_mask)
            C = adcf_result['C_filtered']
            print("ADCF: physics constraint applied")
        else:
            # Fall back to raw IDW interpolation
            from modules.adcf_module import ADCFProcessor
            C = ADCFProcessor()._idw_interpolate_concentration(
                conc_obs, *np.meshgrid(gx, gy), nx, ny
            )

        # ---- Stage 3: CFSI (source enhancement) ----
        cfsi_result = None
        if self.cfsi is not None:
            cfsi_result = self.cfsi.enhance(C, U, V, dx, obstacle_mask)
            C = cfsi_result['C_enhanced']
            print("CFSI: flux divergence computed")

        return {
            'C_enhanced': C,
            'U_corrected': U,
            'V_corrected': V,
            'wdfp_result': wdfp_result,
            'adcf_result': adcf_result,
            'cfsi_result': cfsi_result,
            'grid_x': gx,
            'grid_y': gy,
            'grid_resolution': dx,
            'nx': nx,
            'ny': ny,
            'modules_active': {
                'WDFP': self.wdfp is not None,
                'ADCF': self.adcf is not None,
                'CFSI': self.cfsi is not None,
            },
        }
