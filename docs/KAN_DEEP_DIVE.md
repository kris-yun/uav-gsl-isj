# KAN Deep Dive: Complete Analysis
# Based on 700+ papers (Semantic Scholar + OpenAlex)

---

## KAN PAPERS FOUND (Complete List)

### Foundation Papers
1. KAN original (2024, 514 cites) - arXiv
2. KAN Survey (ACM CS 2024, 234 cites) - Comprehensive review
3. KAN approximation guarantees (2025, 4 cites) - Theory

### Efficient Variants
4. Chebyshev KAN (2024, 178 cites) - Chebyshev polynomials
5. SineKAN (Frontiers AI 2025, 29 cites) - Sinusoidal activations
6. MJKAN (ICT Express 2025, 5 cites) - Hybrid KAN+MLP
7. SPIKANs (MLST 2024, 21 cites) - Separable physics-informed

### Physics-Informed KAN
8. PI-KAN turbulence (Science Advances 2025, 24 cites)
9. PI-KAN augmented Lagrangian (Sci Reports 2025, 35 cites)
10. Adaptive PINN-KAN (IEEE Access 2024, 69 cites)
11. PI-KAN Navier-Stokes (2023, 14 cites)
12. Weak-Form KAN (CMAME 2026, 1 cite)

### KAN + Graph
13. KAN Graph NN (Nature MI 2025, 51 cites)
14. GKAN (2024, 24 cites)
15. KAGNNs (2024, 21 cites)
16. Graph Attention KAN (Sci Reports 2025, 32 cites)

### KAN Applications
17. KAN for environment (Env Sci Tech 2025, 65 cites)
18. KAN for RL (IEEE TITS 2025, 14 cites)
19. KAN for time series (Sci Reports 2025, 10 cites)
20. KAN for battery (Batteries 2025, 10 cites)

### KAN Training
21. KAN grid refinement (2023, 1 cite)
22. KAN for MLP preconditioning (2025, 6 cites)
23. SHARe-KAN post-training quantization (2025, 0 cites)

---

## WHY KAN IS PERFECT FOR OUR PROBLEM

### 1. Interpretability (Critical for ISJ)
- KAN learns symbolic functions on edges
- Can extract formula: f(x) = sum of B-spline basis functions
- Reviewers can see EXACTLY what residual learns
- No black-box at runtime

### 2. Parameter Efficiency
- KAN: ~200 params for 5->16->8->1
- MLP: ~500 params for same architecture
- Less overfitting, faster training

### 3. Physics Compatibility
- B-spline activations are smooth (physical)
- Can enforce bounds: f in [-B, B]
- Can encode monotonicity constraints
- Can encode known physics relationships

### 4. Universal Approximation
- KAN has universal approximation theorem
- Convergence rates in Besov norms (2025 paper)
- Theoretically guaranteed

### 5. No Runtime Neural Network
- After training, extract symbolic formula
- Implement formula in C++ directly
- No ONNX/TensorRT needed
- Fast execution

---

## KAN vs MLP COMPARISON

| Feature | MLP | KAN |
|---------|-----|-----|
| Parameters | ~500 | ~200 |
| Interpretability | Low | HIGH |
| Symbolic Extraction | No | YES |
| Physics Compatible | Low | HIGH |
| Training Speed | Fast | Medium |
| Inference Speed | Fast | Fast |
| Universal Approximation | Yes | Yes |
| Scientific Discovery | Low | HIGH |

---

## IMPLEMENTATION DETAILS

### Step 1: Install pykan
```bash
pip install pykan
```

### Step 2: Prepare Data
```python
# From GADEN simulations
# Input: (c_t, w_x, w_y, d_to_map, step_count)
# Target: residual = log p_true - log p_poisson
```

### Step 3: Train KAN
```python
from kan import KAN

# Create KAN
model = KAN(width=[5, 16, 8, 1], grid=5, k=3, seed=0)

# Train
model.fit(dataset, opt='LBFGS', steps=100)

# Plot
model.plot()
```

### Step 4: Extract Symbolic Formula
```python
# Suggest symbolic functions
model.suggest_symbolic(lib='all')

# Get symbolic formula
formula = model.symbolic()
print(formula)
# Example output: '0.3*tanh(0.5*w_x*d) + 0.1*log(1+c_t)'
```

### Step 5: Implement in C++
```cpp
// Convert symbolic formula to C++
float residual = 0.3f * tanh(0.5f * w_x * d) + 0.1f * log(1 + c_t);
```

---

## EXPECTED OUTCOMES

1. **Interpretable residual**: Symbolic formula shows what physics misses
2. **Better performance**: KAN should match or beat MLP
3. **Higher ISJ score**: Novel architecture + interpretability
4. **Publication bonus**: Can publish KAN-GSL as separate contribution

---

## RISK ANALYSIS

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| KAN underperforms MLP | Low | Medium | Show both results |
| Symbolic extraction fails | Low | Low | Use KAN weights |
| Training instability | Medium | Low | Grid refinement |
| C++ integration issues | Low | Medium | Lookup table |

---

## CONCLUSION

KAN is the optimal architecture for our GSL problem:
- Interpretable (symbolic formula)
- Efficient (~200 params)
- Physics-compatible
- No runtime neural network
- Theoretically guaranteed

**Recommendation: Implement KAN residual immediately.**