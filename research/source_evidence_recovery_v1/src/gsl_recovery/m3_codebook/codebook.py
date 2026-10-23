from __future__ import annotations
from dataclasses import dataclass
import itertools
import numpy as np


def binary_words(length):
    if not 1 <= int(length) <= 8:
        raise ValueError("Exact V1 codebooks require 1 <= block length <= 8")
    return np.array(list(itertools.product((0, 1), repeat=int(length))), dtype=np.int8)


def encode_word(word):
    word = np.asarray(word, dtype=int)
    if np.any((word != 0) & (word != 1)):
        raise ValueError("Clean codeword symbols must be 0 or 1")
    return int(word @ (1 << np.arange(len(word)-1, -1, -1)))


@dataclass
class SoftCodebook:
    actions: tuple
    probabilities: np.ndarray  # [source, mechanism, joint binary word]
    model_version: str = "v1"
    draws: int = 0
    tv_radius: np.ndarray | None = None
    confidence_failure_probability: float = 0.0
    exact: bool = False
    cost: float = 1.0
    threshold: float = 0.5

    def __post_init__(self):
        self.actions = tuple(self.actions)
        self.probabilities = np.asarray(self.probabilities, float)
        p = self.probabilities
        if p.ndim != 3 or p.shape[-1] != 2 ** len(self.actions):
            raise ValueError("Soft codebook must have shape [N,E,2**L]")
        if np.any(p < 0) or not np.all(np.isfinite(p)) or not np.allclose(p.sum(-1), 1, atol=1e-9):
            raise ValueError("Every source-mechanism codeword distribution must sum to one")
        if self.tv_radius is None:
            # Only an explicitly exact codebook can claim zero MC uncertainty.
            self.tv_radius = np.zeros(p.shape[:2]) if self.exact else np.ones(p.shape[:2])
        self.tv_radius = np.broadcast_to(self.tv_radius, p.shape[:2]).copy()
        if np.any(self.tv_radius < 0) or np.any(self.tv_radius > 1):
            raise ValueError("TV radii must lie in [0,1]")
        if self.cost <= 0:
            raise ValueError("Action cost must be positive")

    @property
    def length(self):
        return len(self.actions)


class JointCodebookBuilder:
    """Sample whole causal trajectories, never multiply marginal bit rates.

    The finite-alphabet concentration radius covers sampling error *inside*
    the generator. It says nothing about simulator/physical model mismatch.
    """
    def __init__(self, generator, threshold=0.5, model_version="v1"):
        self.generator = generator
        self.threshold = float(threshold)
        self.model_version = str(model_version)

    def build(self, history, action_blocks, sources, mechanisms, draws=512, rng=None,
              delta=0.01, costs=None, max_rollout_observations=2000000, wall_seconds=None):
        import time
        started=time.perf_counter()
        rng = np.random.default_rng() if rng is None else rng
        if draws < 1 or not 0 < delta < 1:
            raise ValueError("draws must be positive and delta in (0,1)")
        blocks = [tuple(b) for b in action_blocks]
        if not blocks:
            raise ValueError("No legal action blocks supplied")
        operations=sum(len(b) for b in blocks)*len(sources)*len(mechanisms)*draws
        if operations>max_rollout_observations:
            raise RuntimeError('BLOCKED_CODEBOOK_BUDGET: retain full source support; increase qualified budget or vectorize')
        all_cells = len(blocks) * len(sources) * len(mechanisms)
        out = []
        for block_index, actions in enumerate(blocks):
            words = binary_words(len(actions))
            p = np.zeros((len(sources), len(mechanisms), len(words)))
            for i, source in enumerate(sources):
                for j, mechanism in enumerate(mechanisms):
                    if wall_seconds is not None and time.perf_counter()-started>wall_seconds:
                        raise RuntimeError('BLOCKED_CODEBOOK_WALL_TIME: no partial book may be used')
                    for _ in range(int(draws)):
                        future = self.generator.sample_future(history, actions, source, mechanism, rng)
                        if len(future) != len(actions):
                            raise ValueError("Generator returned wrong future trajectory length")
                        word = [int(o.gas > self.threshold) for o in future]
                        p[i, j, encode_word(word)] += 1
            p /= int(draws)
            # Bretagnolle-Huber-Carol / finite-alphabet union bound:
            # P(TV(p_hat,p)>r) <= 2**K exp(-2*n*r**2).
            radius = min(1.0, np.sqrt((len(words)*np.log(2) + np.log(all_cells/delta))/(2*draws)))
            cost = sum(float(a.dwell) for a in actions) if costs is None else float(costs[block_index])
            out.append(SoftCodebook(actions, p, self.model_version, int(draws),
                                   np.full(p.shape[:2], radius), delta, False, cost, self.threshold))
        return out
