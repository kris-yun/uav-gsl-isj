#!/usr/bin/env python3
"""Scientific regression tests for CG-PC-CTT Gate V2.

These are contract tests, not performance evidence. They cover the finite-M
failure that invalidated V1.
"""
import numpy as np
from completeness_gate import GateConfig, compute_gate, no_update_posterior


def make_case(signal=3.0, noise=0.2, collapse=False, seed=0):
    rng = np.random.default_rng(seed)
    S, M, D = 4, 8, 12
    basis = np.zeros((S, D), dtype=np.float64)
    basis[0, 0] = 1.0
    basis[1, 1] = 1.0
    basis[2, 2] = 1.0
    basis[3, :3] = -1.0
    if collapse:
        basis[:, 2] *= 1e-4
    return signal * basis[:, None, :] + noise * rng.normal(size=(S, M, D))


CFG = GateConfig(
    gamma_min=0.05,
    p_max=0.01,
    rank_k=3,
    member_semantics='exchangeable_realizations',
)

strong = compute_gate(make_case(signal=3.0), CFG)
weak = compute_gate(make_case(signal=0.01), CFG)
null = compute_gate(make_case(signal=0.0), CFG)
collapsed = compute_gate(make_case(signal=3.0, collapse=True), CFG)

assert strong.accepted, strong
assert strong.inferential_valid, strong
assert strong.null_patterns == 128, strong

# V1 scientific failure modes. None may pass V2.
assert not weak.accepted, weak
assert not null.accepted, null
assert not collapsed.accepted, collapsed

# Destroy candidate identity independently in every member. A replicated source
# effect must disappear; if this passes, cross-member alignment is leaking.
x = make_case(signal=3.0)
rng = np.random.default_rng(99173)
shuffled = x.copy()
for m in range(x.shape[1]):
    shuffled[:, m, :] = x[rng.permutation(x.shape[0]), m, :]
member_candidate_shuffle = compute_gate(shuffled, CFG)
assert not member_candidate_shuffle.accepted, member_candidate_shuffle

# Reordering transport members is only a representation change. The statistic
# and exhaustive sign-flip p-value must be invariant to member order.
order = np.asarray([6, 1, 4, 0, 7, 3, 5, 2])
reordered = compute_gate(x[:, order, :], CFG)
assert np.isclose(strong.alpha_cf, reordered.alpha_cf, rtol=1e-10, atol=1e-10)
assert np.isclose(strong.gamma_cf, reordered.gamma_cf, rtol=1e-10, atol=1e-10)
assert np.isclose(strong.p_signflip, reordered.p_signflip, rtol=0, atol=0)

# Fixed deterministic nuisance support points are not exchangeable samples.
fixed = compute_gate(
    x,
    GateConfig(
        gamma_min=0.05,
        p_max=0.01,
        rank_k=3,
        member_semantics='fixed_nuisance_design',
    ),
)
assert not fixed.accepted and not fixed.inferential_valid, fixed
assert 'FIXED_DESIGN' in fixed.reason, fixed

undeclared = compute_gate(x, GateConfig(member_semantics='UNDECLARED'))
assert not undeclared.accepted and not undeclared.inferential_valid, undeclared
assert 'UNDECLARED' in undeclared.reason, undeclared

# Exact ABSTAIN contract.
q = np.asarray([0.1, 0.2, 0.3, 0.4])
q_after = no_update_posterior(q)
assert np.array_equal(q, q_after), (q, q_after)

print('SELFTEST V2 PASS')
for name, result in [
    ('strong', strong),
    ('weak', weak),
    ('null', null),
    ('collapsed', collapsed),
    ('member_candidate_shuffle', member_candidate_shuffle),
    ('fixed_design', fixed),
]:
    print(name, result)
