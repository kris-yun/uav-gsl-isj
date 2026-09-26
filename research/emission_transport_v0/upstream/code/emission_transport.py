"""Exact finite-state emission/transport distribution, not a GADEN adapter.

All-start-state backward propagation of marked Markov paths; independent
release superposition is CONDITIONAL on a shared physical regime. Marks are
integer numerical concentration bins, not physical molecule/encounter counts.
No training data or source labels are required to construct a law.

Complexity can grow exponentially in observation dimension. The term budget
raises explicitly; no probability clipping, pruning, temperature or fallback.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Iterable, Sequence, Tuple
import math
import numpy as np
from scipy.special import logsumexp

Key = Tuple[int, ...]
Law = Dict[Key, float]
VectorLaw = Dict[Key, np.ndarray]

class ComputationBudgetExceeded(RuntimeError):
    pass

class ModelSupportMismatch(ValueError):
    pass


def _checked_law(law: Law, dim: int | None = None) -> Law:
    if not law:
        raise ValueError('Empty probability law')
    d = len(next(iter(law))) if dim is None else dim
    if any(len(k) != d or any(int(x) != x or x < 0 for x in k)
           or not math.isfinite(v) or v < 0 for k, v in law.items()):
        raise ValueError('Invalid probability law')
    total = math.fsum(law.values())
    if not math.isclose(total, 1.0, abs_tol=2e-10, rel_tol=2e-10):
        raise ValueError(f'Probability mass is {total}, expected one')
    return law


def convolve(a: Law, b: Law, max_terms: int = 50000) -> Law:
    d = len(next(iter(a)))
    out: Law = {}
    for ka, va in a.items():
        for kb, vb in b.items():
            k = tuple(ka[j] + kb[j] for j in range(d))
            out[k] = out.get(k, 0.0) + va * vb
            if len(out) > max_terms:
                raise ComputationBudgetExceeded('Convolution exceeded atom budget')
    return _checked_law(out, d)


@dataclass(frozen=True)
class MarkedTransport:
    """P[k] moves state immediately BEFORE step k to AFTER step k.

    marks[k,x] is concentration-bin contribution at that step. Zero at
    unobserved steps. Birth b injects at its source immediately before P[b].
    State must include all variables needed for Markov closure (age/radius,
    for example). This demonstrator does not infer such a closure.
    """
    transitions: np.ndarray                 # [time,state,state]
    marks: np.ndarray                       # [time,state,observation]
    max_terms: int = 50000

    def __post_init__(self) -> None:
        p = np.asarray(self.transitions, dtype=float)
        h = np.asarray(self.marks)
        if p.ndim != 3 or p.shape[1] != p.shape[2]:
            raise ValueError('P must have shape [time,state,state]')
        if h.ndim != 3 or h.shape[:2] != p.shape[:2] or h.shape[2] < 1:
            raise ValueError('marks must have shape [time,state,observation]')
        if not np.isfinite(p).all() or (p < 0).any():
            raise ValueError('P must be finite and nonnegative')
        if not np.allclose(p.sum(axis=2), 1.0, rtol=0, atol=1e-12):
            raise ValueError('Each P row must sum to one; include absorbing state')
        if not np.isfinite(h).all() or (h < 0).any() or not np.equal(h, np.floor(h)).all():
            raise ValueError('marks must be nonnegative integer numerical bins')
        object.__setattr__(self, 'transitions', p)
        object.__setattr__(self, 'marks', h.astype(np.int64))
        if self.max_terms < 1:
            raise ValueError('Positive atom budget required')

    def backward(self) -> list[VectorLaw]:
        """Return one-emission law for every possible birth and start state."""
        t, n, _ = self.transitions.shape
        m = self.marks.shape[2]
        out: list[VectorLaw] = [{} for _ in range(t + 1)]
        out[t] = {(0,) * m: np.ones(n)}
        for k in range(t - 1, -1, -1):
            nxt: VectorLaw = {}
            p = self.transitions[k]
            for old_key, old_vec in out[k + 1].items():
                for x in range(n):
                    if old_vec[x] == 0 or not np.any(p[:, x]):
                        continue
                    new_key = tuple(old_key[j] + int(self.marks[k, x, j])
                                    for j in range(m))
                    if new_key not in nxt:
                        nxt[new_key] = np.zeros(n)
                    nxt[new_key] += p[:, x] * old_vec[x]
                    if len(nxt) > self.max_terms:
                        raise ComputationBudgetExceeded('Backward law exceeded atom budget')
            masses = np.sum(np.stack(list(nxt.values())), axis=0)
            if not np.allclose(masses, 1., rtol=0, atol=2e-10):
                raise ArithmeticError('Backward probability-mass defect')
            out[k] = nxt
        return out

    def all_source_laws(self, source_states: Sequence[int],
                        birth_count_pmfs: Sequence[dict[int, float]]) -> list[Law]:
        """Compose finite count PGFs. Fixed b releases use {b:1.0}.

        Counts must be independent across slots, conditionally on regime;
        emissions in a slot iid. Correlated births require a different joint
        count law, not this interface. Infinite Poisson counts not silently
        truncated. Empty slots represented by {0:1.0}.
        """
        t, n, _ = self.transitions.shape
        m = self.marks.shape[2]
        if len(birth_count_pmfs) != t:
            raise ValueError('One count PMF per transition step required')
        for pmf in birth_count_pmfs:
            if (not pmf or any(c < 0 or int(c) != c or v < 0 or not np.isfinite(v)
                               for c, v in pmf.items()) or
                not math.isclose(math.fsum(pmf.values()), 1., abs_tol=1e-12)):
                raise ValueError('Count PMF invalid')
        if any(s < 0 or s >= n for s in source_states):
            raise ValueError('Source-state index out of range')
        fields = self.backward()
        results: list[Law] = []
        zero = (0,) * m
        for s in source_states:
            total = {zero: 1.}
            for b, pmf in enumerate(birth_count_pmfs):
                one = {key: float(val[s]) for key, val in fields[b].items() if val[s] > 0}
                powers: list[Law] = [{zero: 1.}]
                for _ in range(max(pmf)):
                    powers.append(convolve(powers[-1], one, self.max_terms))
                group: Law = {}
                for c, weight in pmf.items():
                    for key, prob in powers[c].items():
                        group[key] = group.get(key, 0.) + weight * prob
                total = convolve(total, _checked_law(group), self.max_terms)
            results.append(_checked_law(total))
        return results


def mix_shared_regime(regime_laws: Sequence[Sequence[Law]], weights: np.ndarray) -> list[Law]:
    """Mix the WHOLE release-superposed law, not each packet/kernel separately."""
    w = np.asarray(weights, float)
    if w.shape != (len(regime_laws),) or (w < 0).any() or not np.isfinite(w).all():
        raise ValueError('Invalid regime weights')
    if not np.isclose(w.sum(), 1., atol=1e-12, rtol=0):
        raise ValueError('Regime weights must sum to one')
    ns = len(regime_laws[0])
    if any(len(x) != ns for x in regime_laws):
        raise ValueError('Different candidate support in regimes')
    result = []
    for s in range(ns):
        mixed: Law = {}
        for weight, laws in zip(w, regime_laws):
            for key, prob in _checked_law(laws[s]).items():
                mixed[key] = mixed.get(key, 0.) + weight * prob
        result.append(_checked_law(mixed))
    return result


def log_likelihood(laws: Sequence[Law], y: np.ndarray, bin_width: np.ndarray,
                   sensor_sd: np.ndarray) -> np.ndarray:
    """Independent Gaussian MEASUREMENT channel over exact discrete laws.

    Gaussian refers to calibrated observation noise, NOT a plume-law fit.
    sigma must be strictly positive and externally fixed, never a target-tuned
    probability floor. Correlated sensor noise needs the corresponding channel.
    """
    y, h, sd = (np.asarray(x, float) for x in (y, bin_width, sensor_sd))
    if y.ndim != 1 or h.shape != y.shape or sd.shape != y.shape:
        raise ValueError('Observation, widths and sensor SD must have same vector shape')
    if not all(np.isfinite(x).all() for x in (y, h, sd)) or (h <= 0).any() or (sd <= 0).any():
        raise ValueError('Finite observations, positive bin widths and sensor SD required')
    out = []
    norm = np.sum(np.log(sd)) + y.size * math.log(2 * math.pi) / 2
    for law in laws:
        _checked_law(law, y.size)
        atoms = np.asarray(list(law), float) * h
        probs = np.asarray(list(law.values()))
        keep = probs > 0
        with np.errstate(over='raise', invalid='raise'):
            terms = np.log(probs[keep]) - .5 * np.sum(((y - atoms[keep]) / sd)**2, axis=1) - norm
        out.append(float(logsumexp(terms)))
    arr = np.asarray(out)
    if not np.isfinite(arr).all():
        raise FloatingPointError('Nonfinite likelihood; no floor/fallback applied')
    return arr


def source_posterior(loglikes: np.ndarray, prior: np.ndarray) -> np.ndarray:
    a, p = np.asarray(loglikes, float), np.asarray(prior, float)
    if a.ndim != 1 or a.shape != p.shape or np.isnan(a).any() or np.isposinf(a).any():
        raise ValueError('Invalid log-likelihood vector')
    if np.isneginf(a).all():
        raise ModelSupportMismatch('All candidates assign zero likelihood; no uniform fallback')
    if not np.isfinite(p).all() or (p <= 0).any() or not np.isclose(p.sum(), 1.):
        raise ValueError('Strictly positive normalized frozen prior required')
    logq = np.log(p) + a
    return np.exp(logq - logsumexp(logq))



def binned_log_likelihood(laws: Sequence[Law], observation: np.ndarray,
                          bin_width: np.ndarray,
                          observation_edges: Sequence[np.ndarray]) -> np.ndarray:
    """Exact noiseless BIN probabilities for a finite discrete concentration law.

    Edges are frozen independently of the target. Bins are [a,b), with final
    bin including +inf. Zero probability is -inf, not a numerical error or an
    excuse to introduce a likelihood floor. Returned distribution is exact
    only for the supplied quantized law, not a continuous GADEN law.
    """
    y = np.asarray(observation, float)
    h = np.asarray(bin_width, float)
    if y.ndim != 1 or h.shape != y.shape or len(observation_edges) != len(y):
        raise ValueError('Incompatible observation/quantization dimensions')
    if not np.isfinite(y).all() or not np.isfinite(h).all() or (h <= 0).any():
        raise ValueError('Invalid observation or quantization width')
    bounds = []
    for value, edges in zip(y, observation_edges):
        e = np.asarray(edges, float)
        if (e.ndim != 1 or len(e) < 2 or np.isnan(e).any() or
            not np.all(np.diff(e) > 0) or e[0] != -np.inf or e[-1] != np.inf):
            raise ValueError('Strictly increasing edges from -inf to inf required')
        j = int(np.searchsorted(e, value, side='right') - 1)
        bounds.append((e[j], e[j+1]))
    out = []
    for law in laws:
        _checked_law(law, len(y))
        prob = math.fsum(v for key, v in law.items()
                         if all(lo <= h[j]*key[j] < hi
                                for j, (lo, hi) in enumerate(bounds)))
        out.append(math.log(prob) if prob > 0 else -np.inf)
    return np.asarray(out)

def grid_kernel(free: np.ndarray, wind: np.ndarray, dx: float,
                diffusivity: float, dt: float) -> tuple[np.ndarray, np.ndarray]:
    """2D upwind diffusion jump kernel; no-flux wall convention.

    Educational finite-volume approximation, NOT pinned GADEN transition law.
    Every blocked-neighbor jump is suppressed. Rates v+/dx + D/dx^2;
    P=I+dt*Q. CFL checked, not silently renormalized. Returns cells[y,x].
    """
    free = np.asarray(free, bool)
    wind = np.asarray(wind, float)
    if free.ndim != 2 or wind.shape != free.shape + (2,) or not np.isfinite(wind).all():
        raise ValueError('free[y,x], wind[y,x,(vx,vy)] required')
    if dx <= 0 or dt <= 0 or diffusivity < 0:
        raise ValueError('Invalid physical/discretization parameters')
    cells = np.argwhere(free)
    if len(cells) == 0:
        raise ValueError('No free states')
    ids = {tuple(cell): i for i, cell in enumerate(cells)}
    q = np.zeros((len(cells), len(cells)))
    for i, (y, x) in enumerate(cells):
        vx, vy = wind[y, x]
        for dy, ddx, v in [(0, 1, vx), (0, -1, -vx), (1, 0, vy), (-1, 0, -vy)]:
            target = (int(y + dy), int(x + ddx))
            if target in ids:
                rate = max(v, 0.) / dx + diffusivity / dx**2
                q[i, ids[target]] += rate
                q[i, i] -= rate
    if np.max(-np.diag(q)) * dt > 1 + 1e-14:
        raise ValueError('CFL violated; choose grid/time step before data evaluation')
    return np.eye(len(cells)) + dt * q, cells


def direct_path_law(p: np.ndarray, marks: np.ndarray, source: int, birth: int = 0) -> Law:
    """Independent small-case forward path enumeration used only in tests."""
    m = marks.shape[2]
    frontier = {(source, (0,) * m): 1.}
    for k in range(birth, p.shape[0]):
        nxt = {}
        for (state, key), prob in frontier.items():
            for x, px in enumerate(p[k, state]):
                if px == 0:
                    continue
                new = tuple(key[j] + int(marks[k, x, j]) for j in range(m))
                kk = (x, new)
                nxt[kk] = nxt.get(kk, 0.) + prob * px
        frontier = nxt
    out: Law = {}
    for (_, key), prob in frontier.items():
        out[key] = out.get(key, 0.) + prob
    return _checked_law(out)
