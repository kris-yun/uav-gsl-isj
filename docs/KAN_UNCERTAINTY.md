# KAN Uncertainty Quantification: Conformalized-KANs and Beyond

---

## KEY PAPERS

### Conformalized-KANs (MLST 2025, 4 cites)
**"Uncertainty quantification with coverage guarantees for KANs in scientific machine learning"**
- KAN + Conformal Prediction
- Coverage guarantees
- **Relevance**: Add uncertainty to our KAN residual

### KAN-UG (IEEE TGRS 2026, 2 cites)
**"KAN-Based Difference Feature Enhancement With Uncertainty Guidance for Change Detection"**
- KAN with uncertainty guidance
- **Relevance**: Uncertainty-aware KAN

### SVGP KAN (MLST 2025, 1 cite)
**"Sparse Variational Gaussian Process KAN"**
- KAN + Gaussian Process
- Uncertainty quantification
- **Relevance**: GP-enhanced KAN

---

## OUR UNCERTAINTY STRATEGY

### Option 1: Conformalized-KANs (Recommended)
```python
# After training KAN, add conformal prediction
from conformalized_kan import ConformalizedKAN

# Train KAN
model = KAN(width=[5, 16, 8, 1], grid=5, k=3)
model.fit(dataset, opt='LBFGS', steps=100)

# Add conformal prediction
conf_model = ConformalizedKAN(model, alpha=0.05)
# Now conf_model provides prediction intervals
```

**Advantages:**
- Distribution-free coverage guarantees
- No assumptions on data distribution
- Finite-sample validity
- Easy to implement

### Option 2: SVGP KAN
```python
# Combine KAN with Gaussian Process
from svgp_kan import SVGP_KAN

# Create SVGP-KAN
model = SVGP_KAN(width=[5, 16, 8, 1], grid=5, k=3)
model.fit(dataset, opt='LBFGS', steps=100)
# Now model provides uncertainty estimates
```

**Advantages:**
- Full Bayesian treatment
- Uncertainty propagation
- Can be combined with GBI

### Option 3: Ensemble KAN
```python
# Train multiple KANs with different seeds
models = []
for seed in range(5):
    model = KAN(width=[5, 16, 8, 1], grid=5, k=3, seed=seed)
    model.fit(dataset, opt='LBFGS', steps=100)
    models.append(model)

# Uncertainty = variance across models
uncertainty = np.std([m.predict(x) for m in models])
```

**Advantages:**
- Simple to implement
- No additional theory needed
- Well-established

---

## INTEGRATION WITH GBI

### Current GBI Posterior:
```
pi_T(s) ∝ pi_0(s) * exp(-η * Σ_t loss_t(s))
```

### With KAN Uncertainty:
```
pi_T(s) ∝ pi_0(s) * exp(-η * Σ_t [loss_t(s) + beta * uncertainty_t(s)])
```

Where:
- loss_t(s) = Poisson log-likelihood + KAN residual
- uncertainty_t(s) = KAN uncertainty estimate
- beta = uncertainty weight (hyperparameter)

**Effect:** Posterior concentrates more in regions with low uncertainty.

---

## CONCLUSION

KAN uncertainty quantification is available through:
1. Conformalized-KANs (coverage guarantees)
2. SVGP KAN (Bayesian treatment)
3. Ensemble KAN (simple approach)

**Recommendation: Use Conformalized-KANs for distribution-free coverage guarantees.**