# WUBI-SRI v3 Parameter Sensitivity Analysis

## Overview

US_HIT_SHRINK_CAL has 5 key parameters, all selected on calibration data only.
The calibration sweep tested 1200 configurations (5 x 5 x 4 x 3 x 4).
Below we analyze each parameter's sensitivity and justify the selected value.

---

## 1. Enhancement Percentile = 90

**What it does**: Controls which observations are classified as "high enhancement" and contribute positive votes to the upwind sector. Percentile 90 means only the top 10% of positive enhancement values are used.

**Sensitivity**: LOW (coverage range: 0.860 - 0.900, delta=0.040)

**Why 90 is reasonable**:
- Lower percentiles (70, 75, 80) include more observations, but many of these are noisy background fluctuations that add spurious upwind sectors
- Higher percentiles (95) would be too restrictive, potentially leaving too few observations for reliable sector construction
- The 90th percentile balances noise rejection (only strong signals) with having enough observations (typically 30+ per trial)
- The low sensitivity indicates the method is robust to this choice within the tested range

**Risk**: If the plume is very weak (all enhancements near background), even the 90th percentile may include noise. This is partly why low-wind trials fail.

---

## 2. Sector Width Multiplier = 0.75

**What it does**: Multiplies the wind direction standard deviation to set the sector half-angle. A multiplier of 0.75 with wind_std=15deg gives a half-angle of max(10, 0.75*15) = 11.25 degrees.

**Sensitivity**: MODERATE (coverage range: 0.783 - 0.929, delta=0.145)

**Why 0.75 is reasonable**:
- The default (1.0) uses the full wind uncertainty as the sector width, which is conservative
- A narrower sector (0.75) reduces the area significantly while still capturing the true source direction
- The min_sector_angle=10 provides a floor: even with low wind_std, the sector is at least 10 degrees
- The moderate sensitivity means this parameter matters: too narrow (< 0.5) risks missing the source, too wide (> 1.5) inflates area

**Tradeoff**: Narrower sectors reduce area but increase the risk of missing the source when wind direction uncertainty is high. The calibration finds 0.75 as the sweet spot for the MATRIX dataset.

---

## 3. Minimum Sector Angle = 10 degrees

**What it does**: Sets a floor on the sector half-angle. Even if wind_std is very small (e.g., 5 degrees), the sector will be at least 10 degrees half-angle.

**Sensitivity**: LOW (coverage range: 0.870 - 0.899, delta=0.029)

**Why 10 is reasonable**:
- Prevents degenerate cases where very consistent wind creates an unrealistically narrow sector
- 10 degrees is wide enough to accommodate small wind measurement errors
- The low sensitivity means the exact value doesn't matter much as long as it's in the 10-30 range
- A larger minimum angle (20, 30) would increase area without meaningful coverage improvement

**Note**: This parameter only activates when wind_std is very low (< 13 degrees for multiplier=0.75). For typical MATRIX trials (wind_std 12-55 degrees), the sector width is dominated by the multiplier * wind_std product.

---

## 4. Distance Decay = 1.0

**What it does**: Applies exponential decay to the sector score based on distance from the observation. Score *= exp(-distance * decay / 100). With decay=1.0, a cell 100m away gets 37% of the score of a cell at the observation location.

**Sensitivity**: HIGH (coverage range: 0.793 - 0.946, delta=0.153)

**Why 1.0 is reasonable**:
- Without decay (0.0), all cells in the sector get equal weight regardless of distance, leading to large areas
- With decay=1.0, nearby cells are preferred, which compresses the credible region toward the observation cluster
- This is the primary mechanism for area reduction: it brings the area ratio from ~0.20 (no decay) down to ~0.08
- The high sensitivity means this is the most impactful parameter for the coverage-area tradeoff

**Risk**: Too strong decay would concentrate the posterior near the observations rather than upwind of them. The value 1.0 is moderate: it reduces far-field contributions without eliminating them entirely.

---

## 5. Posterior Temperature = 0.5

**What it does**: Divides the score by the temperature before normalization. Temperature < 1.0 broadens the posterior (more uniform), temperature > 1.0 sharpens it.

**Sensitivity**: LOW (coverage range: 0.884 - 0.884, delta=0.000)

**Why 0.5 is reasonable (and why it doesn't collapse coverage)**:
- For US_HIT_SHRINK_CAL, the posterior is already constructed as a sum of sector votes (not a product of likelihoods)
- The temperature=0.5 simply makes the distribution more uniform, which helps prevent over-concentration
- Unlike WUL_MML where temperature is critical (the log-likelihood sum creates extreme peaks), the sector posterior is naturally smoother
- The zero sensitivity in calibration suggests temperature has minimal effect on the sector method's coverage

**Contrast with WUL_MML**: For the Bayesian WUL_MML, temperature=5.14 was needed to achieve even 50% coverage. This is because the multiplicative likelihood creates a near-delta posterior. The sector method doesn't have this problem.

---

## Summary: Parameter Sensitivity Ranking

| Parameter | Value | Sensitivity | Role |
|-----------|-------|-------------|------|
| Enhancement percentile | 90 | LOW | Noise rejection |
| Sector width multiplier | 0.75 | MODERATE | Sector width control |
| Min sector angle | 10 deg | LOW | Prevents degenerate sectors |
| Distance decay | 1.0 | **HIGH** | Primary area compression |
| Posterior temperature | 0.5 | LOW | Fine-tuning (minimal effect) |

**Key insight**: Distance decay is the most sensitive parameter and the primary lever for controlling the coverage-area tradeoff. The other parameters are relatively robust within their tested ranges.

**Practical recommendation**: For a new dataset, prioritize calibrating distance decay and sector width multiplier. Enhancement percentile and min sector angle can use default values (90 and 10) with minimal risk.
