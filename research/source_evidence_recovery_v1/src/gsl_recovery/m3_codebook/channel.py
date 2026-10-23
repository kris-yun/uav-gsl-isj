"""Declared extra contamination; ordinary plume randomness stays in p(c)."""
from __future__ import annotations
from dataclasses import dataclass
import itertools
import numpy as np
from .codebook import binary_words


@dataclass(frozen=True)
class CorruptionChannel:
    max_flips: int = 0
    max_erasures: int = 0
    max_burst: int = 0

    def __post_init__(self):
        if min(self.max_flips, self.max_erasures, self.max_burst) < 0:
            raise ValueError("Corruption budgets must be nonnegative")

    def neighborhoods(self, length):
        """Return observed alphabet and clean->observed index neighborhoods.

        max_burst permits one additional contiguous interval whose bits may
        be arbitrarily changed; erasures are explicitly marked -1. Budgets
        combine conservatively rather than being counted as plume variation.
        """
        clean = binary_words(length)
        symbol_set = (-1, 0, 1) if self.max_erasures else (0, 1)
        observed = np.array(list(itertools.product(symbol_set, repeat=length)), dtype=np.int8)
        neighborhoods = []
        intervals = [set()]
        for size in range(1, min(length, self.max_burst)+1):
            intervals += [set(range(start, start+size)) for start in range(length-size+1)]
        for word in clean:
            members = []
            for index, value in enumerate(observed):
                erased = set(np.flatnonzero(value == -1))
                if len(erased) > self.max_erasures:
                    continue
                changed = set(np.flatnonzero((value != word) & (value != -1)))
                if any(len(changed - interval) <= self.max_flips for interval in intervals):
                    members.append(index)
            neighborhoods.append(np.array(members, dtype=int))
        return observed, neighborhoods
