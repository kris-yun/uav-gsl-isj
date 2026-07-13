# KAN for Temporal Data: Time Series and Sequential Processing

---

## KEY PAPERS

### TimeKAN (ICLR 2025, 50 cites)
**"KAN-based Frequency Decomposition Learning Architecture for Long-term Time Series Forecasting"**
- KAN for time series
- Frequency decomposition
- **Relevance**: Our sequential observations

### C-KAN (Mathematics 2024, 44 cites)
**"Convolutional KAN for Time-Series Forecasting"**
- KAN + Convolution
- **Relevance**: Spatial-temporal processing

### MoEKAN (2025, 2 cites)
**"Multi-Scale Transformer-Based Gating KAN Experts Network"**
- Multi-scale KAN
- **Relevance**: Multi-scale processing

### WaveKoop-KAN (IEEE Access 2026, 1 cite)
**"Wavelet-Decomposed Koopman-Gated Temporal Convolution Hybrid With KAN"**
- Wavelet + KAN
- **Relevance**: Frequency analysis

### AR-KAN (2025, 0 cites)
**"Autoregressive-Weight-Enhanced KAN for Time Series"**
- Autoregressive KAN
- **Relevance**: Sequential processing

### TC-KAN (2026, 0 cites)
**"Time-Conditioned KAN with Time-Dependent Activations"**
- Time-dependent activations
- **Relevance**: Time-varying functions

### CDR-KAN (2026, 0 cites)
**"Adaptive Multi-Scale KAN with Meta-Cognitive Routing"**
- Multi-scale KAN
- **Relevance**: Industrial time series

---

## OUR TEMPORAL STRATEGY

### Current Approach:
- Process each observation independently
- No temporal dependencies
- KAN residual: f(c_t, w_x, w_y, d, t)

### Enhanced Approach (if needed):
```python
# Use TimeKAN architecture
from timekan import TimeKAN

# Create temporal KAN
model = TimeKAN(
    input_dim=5,  # (c_t, w_x, w_y, d, t)
    hidden_dim=16,
    output_dim=1,
    seq_len=30  # trajectory length
)

# Train on GADEN sequences
model.fit(dataset, opt='LBFGS', steps=100)
```

**Advantages:**
- Captures temporal dependencies
- Better for sequential observations
- Can learn temporal patterns

### Alternative: Use Current Approach
- Process each observation independently
- KAN residual: f(c_t, w_x, w_y, d, t)
- Simpler implementation
- Still interpretable

**Recommendation:** Start with current approach (simpler). Add temporal processing if needed.

---

## CONCLUSION

KAN has been successfully applied to time series with 7+ papers:

1. **TimeKAN** (ICLR 2025, 50 cites) - Frequency decomposition
2. **C-KAN** (2024, 44 cites) - Convolutional KAN
3. **MoEKAN** (2025, 2 cites) - Multi-scale KAN
4. **WaveKoop-KAN** (2026, 1 cite) - Wavelet KAN
5. **AR-KAN** (2025, 0 cites) - Autoregressive KAN
6. **TC-KAN** (2026, 0 cites) - Time-conditioned KAN
7. **CDR-KAN** (2026, 0 cites) - Multi-scale KAN

**Recommendation: Start with current approach (simpler). Add temporal processing if needed.**