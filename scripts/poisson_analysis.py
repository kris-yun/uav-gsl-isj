import math

# Analysis: Poisson model behavior at key distances
# Source at (5.0, 6.2), UAV at various positions

def poisson_rate(dist, lambda0, ell, alpha_w, cos_theta):
    return lambda0 * math.exp(-dist / ell) * (1 + alpha_w * cos_theta)

def detection_prob(lam, dt):
    return 1 - math.exp(-lam * dt)

# Current "working" Gaussian heuristic weights
def gaussian_weight(conc, detected):
    if detected:
        return min(math.sqrt(conc) * 1.5, 3.0)
    else:
        return 0.3

# Key positions
positions = [
    ("Start (4.0,4.0)", 4.0, 4.0),
    ("Near source (5.0,5.5)", 5.0, 5.5),
    ("At source (5.0,6.2)", 5.0, 6.2),
    ("Past source (5.0,7.0)", 5.0, 7.0),
    ("Upwind (4.0,8.0)", 4.0, 8.0),
    ("Side (3.0,6.2)", 3.0, 6.2),
]

source = (5.0, 6.2)
wind = (0.0, -0.5)  # Wind blowing south (typical for this scenario)

print("=" * 80)
print("POISSON MODEL ANALYSIS")
print("Source: (5.0, 6.2), Wind: (0.0, -0.5)")
print("=" * 80)

# Test with different parameter sets
param_sets = [
    ("Current", 0.15, 4.0, 0.15, 0.3),
    ("Moderate", 0.50, 3.0, 0.30, 0.5),
    ("Conservative", 0.10, 5.0, 0.05, 0.2),
]

for name, lam0, ell, aw, dt in param_sets:
    print("\n--- %s (lam0=%.2f, ell=%.1f, aw=%.2f, dt=%.1f) ---" % (name, lam0, ell, aw, dt))
    print("%-25s %6s %8s %8s %10s %10s" % ("Position", "Dist", "cos_th", "lambda", "P(det)", "log_lik0"))
    
    for pos_name, px, py in positions:
        dx = px - source[0]
        dy = py - source[1]
        dist = math.sqrt(dx*dx + dy*dy)
        
        wn = math.sqrt(wind[0]**2 + wind[1]**2) + 1e-6
        wx, wy = wind[0]/wn, wind[1]/wn
        cos_theta = (dx * wx + dy * wy) / (dist + 1e-6)
        
        lam = poisson_rate(dist, lam0, ell, aw, cos_theta)
        p_det = detection_prob(lam, dt)
        log_lik0 = -lam * dt  # log P(d=0)
        
        print("%-25s %6.2f %8.3f %8.3f %10.3f %10.3f" % (pos_name, dist, cos_theta, lam, p_det, log_lik0))

# Key insight: how much does non-detection at start position affect the true source?
print("\n" + "=" * 80)
print("KEY QUESTION: After 10 non-detections at start (4.0,4.0), how much is true source penalized?")
start_dist = math.sqrt((4-5)**2 + (4-6.2)**2)
for name, lam0, ell, aw, dt in param_sets:
    lam = poisson_rate(start_dist, lam0, ell, aw, 0.5)
    log_lik0 = -lam * dt
    cum_effect = 10 * log_lik0
    print("%s: lambda=%.3f, single log_lik0=%.3f, cumulative(10)=%.3f, posterior_factor=%.6f" % 
          (name, lam, log_lik0, cum_effect, math.exp(cum_effect)))