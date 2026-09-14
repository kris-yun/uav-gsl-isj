import itertools
import math


sources = ("A", "B")
prior = {"A": 0.5, "B": 0.5}
logging = {"A": 0.75, "B": 0.25}
seq_prob = {
    "A": {"00": 0.4, "01": 0.1, "10": 0.1, "11": 0.4},
    "B": {"00": 0.1, "01": 0.4, "10": 0.4, "11": 0.1},
}
observed = "11"


def normalize(values):
    total = sum(values.values())
    return {key: value / total for key, value in values.items()}


# S1-S6, population-optimum dry run under the intended reading: both BCE arms
# are reweighted to the declared prior before forming J/M.
prefix = observed[:1]
p_prefix = {
    s: sum(prob for seq, prob in seq_prob[s].items() if seq.startswith(prefix))
    for s in sources
}
m_prefix = sum(prior[s] * p_prefix[s] for s in sources)
f_prefix = {s: math.log(p_prefix[s] / m_prefix) for s in sources}

p_full = {s: seq_prob[s][observed] for s in sources}
m_full = sum(prior[s] * p_full[s] for s in sources)
f_full = {s: math.log(p_full[s] / m_full) for s in sources}
posterior = normalize({s: prior[s] * math.exp(f_full[s]) for s in sources})
increments = {s: f_full[s] - f_prefix[s] for s in sources}
delta_a_b = increments["A"] - increments["B"]
full_margin = math.log(posterior["A"] / posterior["B"])

# Independently constructed fair naive: same labelled histories, prior, budget,
# and deployment inputs, but a pointwise current-record likelihood multiplied
# across time; it has no sequence encoder and no joint/product classifier.
point_prob = {}
for s in sources:
    for t in (0, 1):
        for y in ("0", "1"):
            point_prob[(s, t, y)] = sum(
                prob for seq, prob in seq_prob[s].items() if seq[t] == y
            )
naive_unnormalized = {}
for s in sources:
    like = 1.0
    for t, y in enumerate(observed):
        like *= point_prob[(s, t, y)]
    naive_unnormalized[s] = prior[s] * like
naive_posterior = normalize(naive_unnormalized)
naive_margin = math.log(naive_posterior["A"] / naive_posterior["B"])

# Break-attempt for exact candidate-list permutation equivariance.
logits_original = [f_full[s] for s in sources]
permuted_sources = tuple(reversed(sources))
logits_permuted = [f_full[s] for s in permuted_sources]
expected_permuted = list(reversed(logits_original))
equivariance_max_abs_error = max(
    abs(a - b) for a, b in zip(logits_permuted, expected_permuted)
)

# Dual reading of Step 3. If only the negative arm is reweighted to p_ref,
# the positive remains q(s)p(H|s), so the prior is silently replaced by q.
m_logging_full = sum(logging[s] * p_full[s] for s in sources)
f_negative_only = {
    s: math.log(
        (logging[s] * p_full[s]) / (prior[s] * m_logging_full)
    )
    for s in sources
}
posterior_negative_only = normalize(
    {s: prior[s] * math.exp(f_negative_only[s]) for s in sources}
)
correct_prior_posterior = normalize({s: prior[s] * p_full[s] for s in sources})
negative_only_moment = 0.0
for seq in seq_prob["A"]:
    m_q = sum(logging[s] * seq_prob[s][seq] for s in sources)
    for s in sources:
        f_wrong = math.log(
            (logging[s] * seq_prob[s][seq]) / (prior[s] * m_q)
        )
        negative_only_moment += prior[s] * m_q * math.exp(f_wrong)

# Degenerate probe: a prior-positive but never logged grid cell has no positive
# pair and inverse-frequency weighting is undefined.
prior_c = 0.2
logging_c = 0.0
inverse_weight_c = math.inf if logging_c == 0.0 else prior_c / logging_c

print(f"p_prefix={p_prefix}; M_prefix={m_prefix:.6f}; f_prefix={f_prefix}")
print(f"p_full={p_full}; M_full={m_full:.6f}; f_full={f_full}")
print(f"posterior={posterior}; increments={increments}; delta_A_B={delta_a_b:.6f}; full_margin={full_margin:.6f}")
print(f"naive_posterior={naive_posterior}; naive_margin={naive_margin:.6f}; margin_divergence={full_margin-naive_margin:.6f}")
print(f"equivariance_max_abs_error={equivariance_max_abs_error:.1f}")
print(f"negative_only_logits={f_negative_only}; negative_only_posterior={posterior_negative_only}; correct_prior_posterior={correct_prior_posterior}")
print(f"negative_only_odds={posterior_negative_only['A']/posterior_negative_only['B']:.6f}; correct_prior_odds={correct_prior_posterior['A']/correct_prior_posterior['B']:.6f}")
print(f"negative_only_ratio_moment_over_all_histories={negative_only_moment:.6f} (forced normalization identity)")
print(f"zero_support: pi0_C={prior_c:.1f}, q_C={logging_c:.1f}, pi0_C/q_C={inverse_weight_c}, positive_pairs_C=0")
