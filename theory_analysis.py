"""
Theoretical Analysis: Surprisal-Weighted GBI for Binary Gas Sensing
==================================================================

This script works through the mathematics to verify if our proposed
theorems are actually provable and non-trivial.
"""

import numpy as np
from scipy.stats import norm
from scipy.optimize import minimize_scalar
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

print("=" * 70)
print("THEOREM 1: Binary Observation Fisher Information Efficiency")
print("=" * 70)
print()
print("Setup:")
print("  Continuous observation: z = C(s) + eps, eps ~ N(0, sigma^2)")
print("  Binary observation: y = 1[z > tau]  (threshold tau)")
print("  Detection probability: p(s) = Phi((C(s) - tau) / sigma)")
print()
print("Fisher Information ratio: I_bin / I_cont = phi(u)^2 / (Phi(u) * Phi(-u))")
print("  where u = (C(s) - tau) / sigma")
print()

# Compute the ratio for different u values
u_vals = np.linspace(-3, 3, 100)
phi_vals = norm.pdf(u_vals)
Phi_vals = norm.cdf(u_vals)
ratio = phi_vals**2 / (Phi_vals * (1 - Phi_vals))

# Find maximum
max_idx = np.argmax(ratio)
max_ratio = ratio[max_idx]
max_u = u_vals[max_idx]

print(f"Maximum efficiency: {max_ratio:.4f} = 2/pi = {2/np.pi:.4f}")
print(f"Achieved at u = {max_u:.3f} (i.e., threshold at signal mean)")
print(f"Binary observation preserves up to {max_ratio*100:.1f}% of Fisher information")
print()

# Plot
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

axes[0].plot(u_vals, ratio, 'b-', linewidth=2)
axes[0].axhline(y=2/np.pi, color='r', linestyle='--', label=f'2/pi = {2/np.pi:.3f}')
axes[0].axvline(x=0, color='gray', linestyle=':', alpha=0.5)
axes[0].set_xlabel('u = (C(s) - tau) / sigma', fontsize=12)
axes[0].set_ylabel('I_binary / I_continuous', fontsize=12)
axes[0].set_title('Theorem 1: Binary Observation Efficiency', fontsize=13)
axes[0].legend(fontsize=11)
axes[0].grid(True, alpha=0.3)
axes[0].set_ylim([0, 0.7])

print("=" * 70)
print("THEOREM 2: Surprisal Weight Optimality")
print("=" * 70)
print()
print("Claim: Among all weights w = f(y, pi_MAP),")
print("  w* = -log P(y | MAP) maximizes E[KL(pi_t || pi_{t-1})]")
print()
print("For binary observations with detection probability p_MAP:")
print("  If detected (y=1): w* = -log(p_MAP)")
print("  If not detected (y=0): w* = -log(1-p_MAP)")
print()

# Compute optimal weight for different p_MAP values
p_range = np.linspace(0.01, 0.99, 100)

# Surprisal weight
w_detect = -np.log(p_range)
w_nodetect = -np.log(1 - p_range)

# Compare with fixed weight w=1
# Expected KL divergence for weight w:
# E[KL] = p * KL(pi || pi*w_p) + (1-p) * KL(pi || pi*w_np)
# where w_p = w * log(p) and w_np = w * log(1-p)

# For a simple 2-hypothesis case:
# H0: source at s0 (p0 = P(detect|s0))
# H1: source at s1 (p1 = P(detect|s1))

# Log-likelihood ratio for binary observation:
# L(y) = y * log(p1/p0) + (1-y) * log((1-p1)/(1-p0))

# Under H0:
# E[L(y)] = p0 * log(p1/p0) + (1-p0) * log((1-p1)/(1-p0)) = -KL(p0 || p1)

# The posterior update with weight w:
# log(pi_1/pi_0) += w * L(y)

# Expected change in log-odds:
# E[Delta log-odds] = w * E[L(y)] = -w * KL(p0 || p1)

# For the posterior to converge correctly, we need E[Delta] < 0 under H0

# Surprisal weight: w = -log P(y | MAP)
# If MAP = s0 (correct): w = -log(p0) when y=1, w = -log(1-p0) when y=0
# Expected weight: E[w] = p0 * (-log p0) + (1-p0) * (-log(1-p0)) = H(p0)

# This is the ENTROPY of the detection probability!

print("Expected surprisal weight = E[w*] = H(p_MAP) = binary entropy")
print("  This means: more uncertain observations get higher average weight")
print("  When p_MAP near 0 or 1: w* is small (observation expected)")
print("  When p_MAP near 0.5: w* is large (observation uncertain)")
print()

# Plot expected weight vs p
expected_w = -p_range * np.log(p_range) - (1-p_range) * np.log(1-p_range)

axes[1].plot(p_range, expected_w, 'b-', linewidth=2, label='E[w*] = H(p_MAP)')
axes[1].axhline(y=np.log(2), color='r', linestyle='--', label=f'log(2) = {np.log(2):.3f}')
axes[1].set_xlabel('P(detect | MAP)', fontsize=12)
axes[1].set_ylabel('Expected Surprisal Weight', fontsize=12)
axes[1].set_title('Theorem 2: Expected Surprisal = Binary Entropy', fontsize=13)
axes[1].legend(fontsize=11)
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(r'D:\ZYC\A-gas\theory_plots.png', dpi=150, bbox_inches='tight')
print("Plots saved to D:\\ZYC\\A-gas\\theory_plots.png")
print()

print("=" * 70)
print("THEOREM 3: Negative Information Lower Bound")
print("=" * 70)
print()
print("Claim: Under wind-modulated binary detection,")
print("  the KL divergence from a non-detection event is bounded below.")
print()
print("For non-detection (y=0):")
print("  KL(pi_post || pi_prior) = sum_s pi(s) * log(pi(s)/pi_prior(s))")
print("  where pi(s) ∝ pi_prior(s) * (1 - p(s))")
print()
print("  The KL divergence is minimized when p(s) is uniform.")
print("  Lower bound: KL >= -log(1 - max_s p(s)) * (1 - pi(MAP))")
print()

# Compute KL divergence for non-detection under different scenarios
distances = np.linspace(0.1, 5.0, 50)
d0, gamma = 1.5, 2.0

# Detection probability at distance d
p_detect = 1.0 / (1.0 + np.exp(gamma * (distances - d0)))

# KL divergence from non-detection (approximate)
# For a simple 1D case with source at 0:
# Prior: uniform over grid
# Posterior after non-detection: proportional to (1 - p(s))

# The KL divergence depends on how concentrated the prior is
# For a flat prior, the posterior concentrates where p(s) is low

# Key insight: non-detection at CLOSE range (high p_detect) 
# provides MORE information than at far range (low p_detect)

fig2, ax2 = plt.subplots(figsize=(8, 5))
ax2.plot(distances, p_detect, 'b-', linewidth=2, label='P(detect | d)')
ax2.plot(distances, -np.log(1 - p_detect + 1e-10), 'r-', linewidth=2, label='Surprisal if non-detected')
ax2.axvline(x=d0, color='gray', linestyle=':', alpha=0.5, label=f'd0 = {d0}m')
ax2.set_xlabel('Distance from source (m)', fontsize=12)
ax2.set_ylabel('Value', fontsize=12)
ax2.set_title('Theorem 3: Non-Detection Information Content', fontsize=13)
ax2.legend(fontsize=11)
ax2.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(r'D:\ZYC\A-gas\theory_negative_info.png', dpi=150, bbox_inches='tight')
print("Plot saved to theory_negative_info.png")
print()

print("=" * 70)
print("SUMMARY: Are these theorems non-trivial?")
print("=" * 70)
print()
print("Theorem 1 (Binary Efficiency):")
print("  - The 2/pi bound is a KNOWN result in quantization theory")
print("  - BUT applying it to GSL and showing it's near-optimal is NEW")
print("  - Verdict: Moderate novelty (quantization application)")
print()
print("Theorem 2 (Surprisal Optimality):")
print("  - Expected surprisal = binary entropy is a clean result")
print("  - The connection to GBI framework is novel")
print("  - Verdict: HIGH novelty if proved rigorously")
print()
print("Theorem 3 (Negative Information Bound):")
print("  - The bound itself is straightforward")
print("  - The insight that non-detection at close range is informative is nice")
print("  - Verdict: LOW-MODERATE novelty (supporting lemma)")
print()
print("CONCLUSION:")
print("  Theorem 2 is the core contribution. If we can prove that")
print("  surprisal weighting maximizes expected information gain")
print("  in binary observation models, that's a genuine theoretical result.")
print("  Theorem 1 supports the binary model choice.")
print("  Theorem 3 is a supporting lemma.")
