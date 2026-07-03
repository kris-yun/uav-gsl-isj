# WUBI-R v6 Multi-Dataset SLE Benchmark

## Primary Metric: Source Localization Error (SLE)

**SLE_2D** = Euclidean distance between estimated source (MAP or point estimate) and true source in 2D.

**SLE_3D** = Same but in 3D if altitude data is available.

This is the PRIMARY metric for ranking algorithms. Region-based metrics (CR90 coverage, area ratio) are SECONDARY and reported only for methods that produce posteriors.

## Why SLE, Not SCAR

- SLE is directly interpretable: "the method estimated the source X meters from the truth."
- SLE is comparable across datasets with different spatial scales.
- SLE does not require a candidate grid or credible region construction.
- SLE is the standard metric in the gas source localization literature.
- CR90/area metrics are useful for uncertainty quantification but should not be the primary ranking criterion.

## Datasets

### DATA_PASS (Immediately Usable)

| Dataset | Type | Cases | Source XY | Wind | Gas | Notes |
|---------|------|-------|-----------|------|-----|-------|
| MATRIX | Real UAV | 14-18 | YES | u,v | CH4 | Primary dataset |

### DATA_READY (Needs Adapter)

| Dataset | Type | Cases | Source XY | Wind | Gas | Notes |
|---------|------|-------|-----------|------|-----|-------|
| BTEX | Ground stations | ? | UNKNOWN | SODAR | BTEX | Zip exists, needs extraction |
| VGR | Simulation | multiple | YES | simulation | simulation | GADEN files, 31GB |
| RED:VAPOR | Wind tunnel | 22 fly-through | NO | u,v | NH3/NO2/CO/PID | No source position in data |

### DATA_TODO (Not Yet Available)

| Dataset | Type | Notes |
|---------|------|-------|
| FFT-07 | Field | No local data |
| METEC | Field | No local data |

## Unified Data Format

Every dataset adapter must output a DataFrame with these columns:

```
case_id: str           # Unique case/trial identifier
dataset: str           # Dataset name (MATRIX, BTEX, VGR, etc.)
sample_x: float        # Sample x position (m)
sample_y: float        # Sample y position (m)
sample_z: float        # Sample z position (m), 0 if 2D
concentration: float   # Raw gas concentration
enhancement: float     # Concentration above background (if available)
wind_u: float          # Wind u-component (m/s)
wind_v: float          # Wind v-component (m/s)
source_x: float        # TRUE source x (EVALUATION ONLY)
source_y: float        # TRUE source y (EVALUATION ONLY)
source_z: float        # TRUE source z (EVALUATION ONLY), 0 if 2D
```

## Algorithm Interface

Every algorithm must implement:

```python
def estimate_source(data: pd.DataFrame) -> dict:
    """
    Args:
        data: DataFrame with unified columns (NO source_x/y/z in input)
    Returns:
        dict with keys:
            'source_x': float  # Estimated source x
            'source_y': float  # Estimated source y
            'source_z': float  # Estimated source z (0 if 2D)
            'runtime_ms': float
            'posterior_map': np.ndarray or None  # Optional posterior
            'grid_x': np.ndarray or None
            'grid_y': np.ndarray or None
    """
```

## Baselines

1. **MaxHit**: Position of maximum concentration sample.
2. **WeightedCentroid**: Concentration-weighted centroid of all samples.
3. **GasKDE**: Kernel density estimation on concentration field, take mode.
4. **UpwindProjection**: Project high-concentration samples upwind by estimated plume distance.
5. **PointWindGaussianGrid**: Gaussian plume posterior on grid (from v4).
6. **BayesianGrid**: Wind-uncertainty likelihood posterior on grid (WUL_MML).

## WUBI-R v6 Method

BEE + WUE + WEE + RPE + GSE + MOE pipeline:
- BEE: Background Enhancement Estimation
- WUE: Wind Uncertainty Estimation
- WEE: Wind Evidence Enhancement
- RPE: Rank-based Posterior Estimation
- GSE: Grid-based Source Estimation
- MOE: Multi-observation Evidence fusion

## Constraints

1. NO per-dataset test source error tuning.
2. NO source_xy in candidate grid construction.
3. SLE is the primary metric in the main table.
4. All algorithms use the same data preprocessing.
5. Calibration parameters are selected on a calibration split, not per-dataset.
