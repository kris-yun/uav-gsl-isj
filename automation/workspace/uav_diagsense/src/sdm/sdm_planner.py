"""SDM Planner — uses deconvolved posterior for action selection.

Combines SDM-sharpened posterior with KLD waypoint scoring.
The deconvolution removes wind-induced blur, giving a sharper
source estimate that improves waypoint selection.
"""
import sys, os
import numpy as np

_src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from sdm.sdm_estimator import SDMEstimator

EPS = 1e-12


class SDMPlanner:
    """Planner using SDM-deconvolved posterior.

    Key advantage: The deconvolved posterior is sharper than the raw
    Bayesian posterior, especially in strong wind conditions where
    the plume is stretched far downwind.
    """

    def __init__(self, grid, occ_2d, emin, cell_size,
                 n_candidates=12, deconv_interval=5, **kwargs):
        self.grid = np.asarray(grid, dtype=np.float64)
        self.occ_2d = occ_2d
        self.emin = np.asarray(emin, dtype=np.float64)
        self.cell_size = cell_size
        self.n_candidates = n_candidates
        self.deconv_interval = deconv_interval
        self._last_wind = np.array([1.0, 0.0])

        self.estimator = SDMEstimator(grid, occ_2d, emin, cell_size, **kwargs)

    def __call__(self, state, est, obs_history, step):
        # Sync observation
        if obs_history:
            last = obs_history[-1]
            wind = np.asarray(last["wind"][:2])
            x = np.asarray(state.pos[:2])
            hit = float(last.get("gas", 0.0)) > 0.01
            self.estimator.update(x, wind, hit)
            self._last_wind = wind

        # Deconvolve periodically (expensive)
        if step % self.deconv_interval == 0 and step > 0:
            self.estimator.deconvolve(self._last_wind)

        post = self.estimator.posterior()
        Hn = self.estimator.entropy_norm()
        gas = float(obs_history[-1].get("gas", 0.0)) if obs_history else 0.0
        wind = self._last_wind
        wn = np.linalg.norm(wind)
        wind_hat = wind / max(wn, EPS)

        # Generate candidates
        candidates = []
        radius = 3.0 if Hn > 0.5 else 2.0
        for i in range(self.n_candidates):
            angle = 2 * np.pi * i / self.n_candidates
            target = state.pos[:2] + np.array([np.cos(angle), np.sin(angle)]) * radius
            candidates.append(target)

        candidates.append(self.estimator.map_estimate()[:2])

        # Upwind candidates when gas detected
        if gas > 0.01:
            candidates.append(state.pos[:2] - wind_hat * 2.0)
            candidates.append(state.pos[:2] - wind_hat * 4.0)

        # Score with KLD
        best_target = candidates[0]
        best_score = -float('inf')
        for target in candidates:
            score = self._kld_score(target, post)
            if score > best_score:
                best_score = score
                best_target = target

        # Mode selection
        if Hn > 0.7:
            mode, speed = "fast", 0.8
        elif gas > 0.01 and float(post.max()) > 0.15:
            mode, speed = "slow", 0.2
        elif float(post.max()) > 0.30:
            mode, speed = "hover", 0.0
        else:
            mode, speed = "slow", 0.25

        return best_target, {
            "name": "sdm", "mode": mode, "speed": speed,
            "kld": best_score, "deconvolved": step % self.deconv_interval == 0,
        }

    def _kld_score(self, target, post):
        dists = np.linalg.norm(self.grid - target[None, :], axis=1)
        p_hit_local = np.exp(-dists / 3.0)
        p_hit_local /= p_hit_local.sum() + EPS
        post_new = post * (1 + p_hit_local)
        post_new /= post_new.sum() + EPS
        return float(np.sum(post_new * np.log((post_new + EPS) / (post + EPS))))
