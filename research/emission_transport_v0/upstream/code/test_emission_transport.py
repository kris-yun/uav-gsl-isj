"""Deterministic mathematical/software checks only. NO GADEN data/run."""
import json
import math
from pathlib import Path
import time
import numpy as np
from emission_transport import (MarkedTransport, convolve, direct_path_law,
    source_posterior, log_likelihood, mix_shared_regime, grid_kernel,
    ComputationBudgetExceeded, binned_log_likelihood, ModelSupportMismatch)

records = []

def check(name, condition, details=None):
    if not bool(condition):
        raise AssertionError(name)
    records.append({'test': name, 'passed': True, 'details': details})


def err(a, b):
    return max((abs(a.get(k, 0.) - b.get(k, 0.)) for k in set(a) | set(b)), default=0.)


def moments(law):
    keys, p = np.array(list(law), float), np.array(list(law.values()))
    mu = p @ keys
    cov = (keys - mu).T @ (p[:, None] * (keys - mu))
    return mu, cov


def main():
    start = time.perf_counter()
    rng = np.random.default_rng(2026092601)
    p = rng.uniform(.1, 1., size=(3, 4, 4))
    p /= p.sum(axis=2, keepdims=True)
    h = np.zeros((3, 4, 3), int)
    for k in range(3):
        h[k, :, k] = [0, 1, 2, 1]
    model = MarkedTransport(p, h)
    fields = model.backward()
    maxerr = 0.
    for birth in range(3):
        for s in range(4):
            backward = {k: float(v[s]) for k, v in fields[birth].items() if v[s] > 0}
            maxerr = max(maxerr, err(backward, direct_path_law(p, h, s, birth)))
    check('all-source backward equals independent forward path enumeration', maxerr < 1e-13,
          {'max_abs_probability_error': maxerr, 'start_birth_cases': 12})

    counts = [{2: 1.}, {1: 1.}, {0: 1.}]
    laws = model.all_source_laws(range(4), counts)
    direct = []
    for s in range(4):
        one0, one1 = direct_path_law(p, h, s, 0), direct_path_law(p, h, s, 1)
        direct.append(convolve(convolve(one0, one0), one1))
    check('fixed releases compose correctly', max(err(a, b) for a, b in zip(laws, direct)) < 1e-12)
    check('all candidate laws conserve mass', max(abs(math.fsum(a.values()) - 1) for a in laws) < 1e-12,
          {'candidate_count': 4, 'atom_counts': [len(x) for x in laws]})

    countmix = model.all_source_laws([0], [{0: .25, 1: .75}, {0: 1.}, {0: 1.}])[0]
    expected = {k: .75 * v for k, v in direct_path_law(p, h, 0).items()}
    expected[(0, 0, 0)] = expected.get((0, 0, 0), 0.) + .25
    check('finite release-count PGF mixture', err(countmix, expected) < 1e-13)

    # A and B have equal first two moments. No fitted data; exact laws.
    a = {(0,): .5, (2,): .5}
    b = {(0,): 1/3, (1,): .5, (3,): 1/6}
    ma, va = moments(a); mb, vb = moments(b)
    accuracy = .5 * sum(max(a.get(k, 0), b.get(k, 0)) for k in set(a) | set(b))
    check('equal moments can hide real source information',
          np.allclose(ma, mb) and np.allclose(va, vb) and abs(accuracy - 5/6) < 1e-14,
          {'mean_A': ma.tolist(), 'mean_B': mb.tolist(),
           'variance_A': va.tolist(), 'variance_B': vb.tolist(),
           'exact_noiseless_Bayes_accuracy': accuracy,
           'identical_Gaussian_moment_models_accuracy': .5,
           'interpretation': 'Constructed mathematical example; NOT GADEN performance'})

    # Realise these laws by a transition, not only supplying finished densities.
    pa = np.array([[.5, 0, .5, 0], [1/3, .5, 0, 1/6], [0, 0, 1, 0], [0, 0, 0, 1]])[None]
    ha = np.arange(4)[None, :, None]
    from_kernel = MarkedTransport(pa, ha).all_source_laws([0, 1], [{1: 1.}])
    check('equal-moment example is generated from transport transition',
          err(from_kernel[0], a) < 1e-14 and err(from_kernel[1], b) < 1e-14)

    edges = [np.array([-np.inf, .5, 1.5, 2.5, np.inf])]
    binll = binned_log_likelihood([a, b], np.array([2.]), np.array([1.]), edges)
    binq = source_posterior(binll, np.array([.5, .5]))
    check('noiseless quantized observations keep genuine zero likelihood',
          np.isneginf(binll[1]) and np.array_equal(binq, [1., 0.]))
    try:
        source_posterior(np.array([-np.inf, -np.inf]), np.array([.5, .5]))
        refused = False
    except ModelSupportMismatch:
        refused = True
    check('out-of-support observation is not hidden by a floor', refused)

    shared = mix_shared_regime([[{(0,): 1.}], [{(2,): 1.}]], np.array([.5, .5]))[0]
    wrong = convolve({(0,): .5, (1,): .5}, {(0,): .5, (1,): .5})
    check('shared regime must be integrated after release composition',
          shared.get((1,), 0.) == 0 and wrong[(1,)] == .5,
          {'correct_population_law': str(shared), 'incorrect_per_packet_mix': str(wrong)})

    ll = log_likelihood(from_kernel, np.array([2.]), np.array([1.]), np.array([.2]))
    q = source_posterior(ll, np.array([.5, .5]))
    check('calibrated measurement-channel source posterior', np.isfinite(q).all() and
          abs(q.sum() - 1) < 1e-14 and q[0] > .99,
          {'illustrative_observation': [2.], 'sensor_sd': [.2], 'posterior': q.tolist()})
    prior = np.array([.2, .8])
    alias_ll = log_likelihood([a, a], np.array([1.]), np.array([1.]), np.array([.3]))
    qa = source_posterior(alias_ll, prior)
    check('indistinguishable sources preserve prior odds', np.allclose(qa, prior, atol=1e-14))

    # Marginalising prefixes, not multiplying repeated prefix likelihoods.
    joint = laws[:2]
    prefix = []
    for law in joint:
        small = {}
        for key, prob in law.items(): small[key[:1]] = small.get(key[:1], 0.) + prob
        prefix.append(small)
    full_ll = log_likelihood(joint, np.array([1., 2., 1.]), np.ones(3), np.full(3, .5))
    pre_ll = log_likelihood(prefix, np.array([1.]), np.ones(1), np.full(1, .5))
    full_q = source_posterior(full_ll, np.array([.5, .5]))
    pre_q = source_posterior(pre_ll, np.array([.5, .5]))
    sequential_q = source_posterior(full_ll-pre_ll, pre_q)
    check('prefix conditional update avoids double counting', np.allclose(full_q, sequential_q, atol=1e-14))

    free = np.ones((3, 4), bool); free[1, 1] = False
    wind = np.zeros((3, 4, 2)); wind[..., 0] = .2
    gridp, cells = grid_kernel(free, wind, 1., .1, .2)
    check('example grid transition nonnegative and conservative',
          gridp.min() >= 0 and np.allclose(gridp.sum(axis=1), 1), {'free_states': len(cells)})
    try:
        grid_kernel(free, wind, 1., .1, 100.)
        raised = False
    except ValueError: raised = True
    check('unstable grid step is refused rather than renormalized', raised)

    try:
        MarkedTransport(p, h, max_terms=1).backward()
        raised = False
    except ComputationBudgetExceeded: raised = True
    check('computation-budget failure is explicit, not probability truncation', raised)

    # Perfectly coupled split packets sum to original law; independent packets don't.
    original = {(0,): .5, (2,): .5}
    coupled_split_sum = {(0,): .5, (2,): .5}
    independent_split_sum = convolve({(0,): .5, (1,): .5}, {(0,): .5, (1,): .5})
    check('packetization dependence is exposed', err(original, coupled_split_sum) == 0 and
          float(moments(independent_split_sum)[1][0, 0]) == .5 and
          float(moments(original)[1][0, 0]) == 1.,
          {'original_variance': 1., 'independent_split_variance': .5})

    # Laplace field at nonnegative arguments is bounded, including atoms at zero.
    lam = np.array([.2, .7, .3])
    for law in laws:
        phi = sum(prob * np.exp(-np.dot(lam, key)) for key, prob in law.items())
        assert 0 <= phi <= 1 + 1e-12
    check('nonnegative Laplace function bounded without plume moments', True)

    result = {'scope': 'Mathematical finite-state toy tests ONLY; no plume/GADEN/held-out score',
              'status': 'ALL_UNIT_TESTS_PASSED', 'test_count': len(records),
              'seed': 2026092601, 'elapsed_seconds': time.perf_counter() - start,
              'records': records}
    path = Path(__file__).resolve().parents[1] / 'evidence' / 'UNIT_TEST_RESULTS.json'
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
