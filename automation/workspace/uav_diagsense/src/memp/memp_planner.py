"""MEMP-enhanced planner for gas source localization.

Combines DQA-AS action selection with MEMP posterior.
"""
import sys
import os
import numpy as np

# Add parent directories to path for imports
_src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from memp.memp_posterior import MEMPPosteriorEstimator
from dqa_as.dqa_as_planner import DQAASPlanner

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
        self.memp_estimator = MEMPPosteriorEstimator(
            grid, occ_2d, emin, cell_size,
            smoothness_weight=smoothness_weight
        )

    def __call__(self, state, est, obs_history, step):
        """Select action using MEMP posterior.

        Key innovation: Use Laplacian-smoothed posterior for action selection.
        """
        # Sync observations to MEMP estimator
        if obs_history:
            last = obs_history[-1]
            wind = np.array(last["wind"][:2])
            x = np.array(state.pos[:2])
            hit = float(last.get("gas", 0.0)) > 0.01
            self.memp_estimator.update(x, wind, hit)

        # Use MEMP posterior instead of standard posterior
        post = self.memp_estimator.posterior()
        wind = np.array(obs_history[-1]["wind"][:2]) if obs_history else np.array([0.5, 0.2])

        # Generate candidate actions
        actions = self.action_lib.generate(state, est, wind, obs_history)

        if not actions:
            return self.memp_estimator.map_estimate()[:2], {
                "name": "fallback_map", "mode": "fast", "speed": 0.5
            }

        # Score each action using MEMP posterior
        best_action = actions[0]
        best_score = -float('inf')
        Hn = self.memp_estimator.entropy_norm()

        for action in actions:
            score = self._score_action(action, state, post, wind)

            # Exploration bonus when entropy high
            if Hn > 0.6:
                dist_from_current = np.linalg.norm(action.target_xy - state.pos[:2])
                exploration_bonus = 0.3 * min(dist_from_current / 3.0, 1.0)
                if action.name == "HoverConfirm":
                    exploration_bonus -= 0.5
                score += exploration_bonus

            # Revisit penalty
            target_key = (round(float(action.target_xy[0]), 1),
                          round(float(action.target_xy[1]), 1))
            revisit_count = self.visit_counts.get(target_key, 0)
            revisit_penalty = self.lam_R * revisit_count
            score -= revisit_penalty

            if score > best_score:
                best_score = score
                best_action = action

        # Update visit count
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

    def _score_action(self, action, state, post, wind):
        """Score action using MEMP posterior.

        Score = [ERR + lam_D * D] * Q / (T + lam_E * E + lam_J * J) - lam_B * BAE
        """
        err = self._expected_risk_reduction(action, state, post, wind)
        dis = self._disambiguation_score(action, post, wind)
        q = self.sensor_model.quality_score(
            action.speed, action.mode, state.time_since_hit)
        bae = self._bae_penalty(action, state)

        T = action.duration + EPS
        E = action.energy_proxy
        J = action.yaw_jerk_proxy

        numerator = (err + self.lam_D * dis) * q
        denominator = T + self.lam_E * E + self.lam_J * J + EPS
        score = numerator / denominator - self.lam_B * bae
        return score

    def _expected_risk_reduction(self, action, state, post, wind):
        """ERR using MEMP posterior."""
        mu_P = np.sum(self.grid * post[:, None], axis=0)
        R_current = float(np.sum(post * np.sum((self.grid - mu_P[None, :]) ** 2, axis=1)))

        total_R_new = 0.0
        for _ in range(self.mc_samples):
            p_hit = np.array([self.obs_model.hit_prob(self.grid[i], action.target_xy, wind)
                              for i in range(len(self.grid))])
            p_hit = p_hit / (p_hit.sum() + EPS)
            hit_prob = float(np.sum(post * p_hit))
            hit = np.random.random() < hit_prob

            if hit:
                post_new = post * (1 + 2.0 * p_hit)
            else:
                post_new = post * (1 - 0.3 * p_hit)
            post_new = np.maximum(post_new, EPS)
            post_new = post_new / (post_new.sum() + EPS)

            mu_new = np.sum(self.grid * post_new[:, None], axis=0)
            R_new = float(np.sum(post_new * np.sum((self.grid - mu_new[None, :]) ** 2, axis=1)))
            total_R_new += R_new

        R_expected_new = total_R_new / self.mc_samples
        return max(0, R_current - R_expected_new)

    def _disambiguation_score(self, action, post, wind):
        """False-source disambiguation using top-2 peak JS divergence."""
        top_idx = np.argsort(post)[-5:]
        if len(top_idx) < 2:
            return 0.0

        p_hits = []
        for idx in top_idx:
            p = self.obs_model.hit_prob(self.grid[idx], action.target_xy, wind)
            p_hits.append(p)

        p1, p2 = p_hits[-1], p_hits[-2]
        p1 = np.clip(p1, EPS, 1 - EPS)
        p2 = np.clip(p2, EPS, 1 - EPS)
        m = 0.5 * (p1 + p2)
        js = 0.5 * (p1 * np.log(p1 / m) + (1 - p1) * np.log((1 - p1) / (1 - m))) + \
             0.5 * (p2 * np.log(p2 / m) + (1 - p2) * np.log((1 - p2) / (1 - m)))
        return float(abs(js))

    def _bae_penalty(self, action, state):
        """BAE penalty (model mismatch risk)."""
        sigma0 = 0.05
        k_speed = 0.10
        speed_penalty = k_speed * action.speed
        mode_penalty = 0.1 if action.mode == "fast" else 0.0
        return sigma0 + speed_penalty + mode_penalty
