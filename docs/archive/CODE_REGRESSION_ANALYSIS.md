# OPGSL Code Regression Analysis

**Date**: 2026-07-03
**Investigator**: Codex automated analysis
**Severity**: CRITICAL - Algorithm produces 30x worse results than previous version

---

## 1. Executive Summary

The OPGSL algorithm regressed from sub-meter accuracy (House01 median 0.07m, House02 median 0.03m) to multi-meter errors (House01 median ~2.4m, House02 median ~1.86m).

**Root cause**: Three changes introduced between the working version (OPGSL.cpp.bak2, 20:52 Jul 2) and the current compiled binary (22:10 Jul 2) collectively destroyed performance. The **primary culprit is deterministic RNG seeding** that changes the Phase 1 exploration pattern, compounded by a **TIME FALLBACK that forces premature convergence** and a **CP module that is enabled but never used for stopping**.

Additionally, the current source file (OPGSL.cpp, 22:18 Jul 2) has a **compilation error** on line 916 (prev_mx undefined) from an incomplete BUG-1 fix.

---

## 2. Timeline of Code Versions

| Time (Jul 2) | File | Role |
|---|---|---|
| 14:51 | OPGSL.cpp.pre_sbd | Pre-SBD baseline (no SBD/CP modules) |
| ~18:00 | Compiled binary | Used for **Phase 1 good results** (bak2-era code) |
| 18:50-20:32 | Phase 1 tests | **GOOD RESULTS**: H01=0.07m, H02=0.03m, H03=0.55m |
| 20:52 | OPGSL.cpp.bak2 | Snapshot after Phase 1 |
| ~21:10 | Compiled binary | Used for Phase 2 tests |
| 21:11-21:47 | Phase 2 tests | Mixed results (many N/A) |
| **22:10** | **Compiled binary** | **Currently installed binary** |
| 22:18:30 | OPGSL.cpp.bugfix_bak | Added CP module, RNG seed, TIME FALLBACK |
| 22:18:31 | OPGSL.cpp | Current source (has prev_mx compile error) |
| 23:13-23:27 | cp_sbd_quick tests | **BAD RESULTS**: process crashes, 1-4.5m errors |

**Key finding**: The binary at 22:10 was compiled from code between bak2 and bugfix_bak. The Phase 1 good results used an EARLIER binary (before bak2).

---

## 3. Exact Code Changes Between Versions

### 3.1 bak2 -> bugfix_bak (4 changes)

#### Change A: CP Module Initialization (declareParameters)
```cpp
// ADDED in bugfix_bak:
use_cp_ = getParam<bool>("opgsl.modules.cp", true);  // DEFAULT: true
cp_width_threshold_ = getParam<float>("opgsl.cp.width_threshold", 1.5f);
cp_stable_required_ = getParam<int>("opgsl.cp.stable_steps", 3);
CP::StoppingConfig cp_cfg;
cp_cfg.alpha = getParam<float>("opgsl.cp.alpha", 0.10f);
cp_cfg.w_thresh = cp_width_threshold_;
cp_cfg.stable_req = cp_stable_required_;
cp_stopping_ = CP::OnlineConformalStopping(cp_cfg);
```

#### Change B: RNG Seeding (declareParameters) **[PRIMARY CAUSE]**
```cpp
// ADDED in bugfix_bak:
int seed_param = getParam<int>("opgsl.seed", -1);
if (seed_param >= 0) {
    rng_.seed(static_cast<unsigned int>(seed_param));
    GSL_INFO("RNG seeded with {}", seed_param);
}
```
**Before (bak2)**: rng_.seed(std::random_device{}()) - always random.
**After**: rng_.seed(seed_param) - deterministic when seed >= 0.

#### Change C: CP Residual Tracking (processGasAndWindMeasurements)
```cpp
// ADDED in bugfix_bak:
if (use_cp_) {
    float mx, my, mz;
    posterior3d_.getMAP(mx, my, mz);
    cp_region_.addMAP(mx, my, mz);
    static float prev_mx = cx, prev_my = cy;
    float residual = std::sqrt((mx - prev_mx)*(mx - prev_mx) + (my - prev_my)*(my - prev_my));
    cp_stopping_.addObs(residual);
    prev_mx = mx; prev_my = my;
}
```

#### Change D: TIME FALLBACK (checkSourceFound)
```cpp
// ADDED in bugfix_bak:
if (elapsed_time_ > 250.0f && !convergence_reported_) {
    float mx, my, mz; posterior3d_.getMAP(mx, my, mz);
    GSL_INFO("TIME FALLBACK: MAP=({:.2f},{:.2f},{:.2f})", mx, my, mz);
    convergence_reported_ = true; return GSLResult::Success;
}
```

### 3.2 bugfix_bak -> Current OPGSL.cpp (2 changes)

#### Change E: SimpleGP LDLT
```cpp
// BEFORE: Eigen::MatrixXf K_inv = K.inverse();
// AFTER:  auto K_ldlt = K.ldlt();
```

#### Change F: CP Residual Fix (LINE 916 - **COMPILE ERROR**)
```cpp
// BEFORE (bugfix_bak - CORRECT):
static float prev_mx = cx, prev_my = cy;
float residual = std::sqrt((mx - prev_mx)*(mx - prev_mx) + (my - prev_my)*(my - prev_my));

// AFTER (current - BROKEN):
float residual = std::sqrt(
    (mx - cp_prev_mx_) * (mx - prev_mx) +   // <-- prev_mx UNDEFINED!
    (my - cp_prev_my_) * (my - cp_prev_my_)
);
```

---

## 4. Root Cause Analysis

### 4.1 PRIMARY: Deterministic RNG Seeding (Change B)

**Impact**: CRITICAL - Completely changes Phase 1 exploration trajectory.

The algorithm rng_ is used for:
- Phase 1 exploration steps (random directions when no wind data)
- Levy flight exploration
- Random fallback navigation
- Bhex stagnation jumps

In bak2, the RNG was always seeded from std::random_device (truly random). In bugfix_bak, the launch file passes seed=0,1,2,... which now seeds the **algorithm RNG** deterministically.

The launch file passes the same seed parameter to BOTH vgr_sim_node (simulation) and gsl_server (algorithm). This is correct for the simulation (reproducible gas plumes) but **wrong for the algorithm** - the algorithm should explore differently each time, not follow a fixed path.

**Evidence**: In the Phase 1 good test (random RNG), House01 seeds 1-4 converged at step 20 with 0.06-0.07m error. In the bad test (deterministic RNG), the same seeds produced different exploration patterns and failed to converge.

### 4.2 SECONDARY: TIME FALLBACK at 250s (Change D)

**Impact**: MODERATE - Forces premature convergence for slow runs.

The Phase 1 good results show House01 seed 1 took 273.4s (101 steps) to converge. The new TIME FALLBACK would have cut this off at 250s with whatever MAP was available.

### 4.3 TERTIARY: CP Module Enabled but Unused (Changes A, C)

**Impact**: LOW - Dead code, no functional impact on results.

The CP module (use_cp_ = true by default) tracks MAP residuals and confidence regions, but cp_stopping_.shouldStop() is **NEVER called** in checkSourceFound().

### 4.4 STRUCTURAL BUG: SBD CUSUM Always Triggers

**Impact**: HIGH - The EIG-max exploration path is dead code.

The computePosteriorKL() function computes KL divergence between prev_posterior_ (initialized to all zeros) and the current log-field:

```cpp
prev_posterior_ = Eigen::MatrixXf::Zero(n_cells_, n_cells_);  // All zeros
float p = std::exp(prev(i, j));  // exp(0) = 1.0 for EVERY cell
```

When prev_posterior_ is all zeros, exp(0) = 1.0 for all 1600 cells (40x40 grid). This is NOT a valid probability distribution (sums to 1600, not 1). The resulting KL divergence is enormous (~14,000), causing the CUSUM to **always trigger immediately** when SBD activates (step > 16).

**Evidence from logs**: SBD: CUSUM triggered (stat=14320.607 > 10000.0) - even with threshold 10000, it triggers on the first SBD step.

**Consequence**: The EIG-max exploration, interim analysis, and adaptive allocation code are **never reached**. The SBD module effectively reduces to "navigate to MAP after step 16".

### 4.5 BUG: Current Source Compile Error (Change F)

**Impact**: BLOCKING - Current OPGSL.cpp cannot compile.

Line 916 references prev_mx which is undefined. The BUG-1 fix intended to replace static float prev_mx with member variable cp_prev_mx_, but only updated the first occurrence.

---

## 5. Process Crash Analysis

Multiple test runs show process_died with exit code -9 (SIGKILL):

| Run | Exit Code | Likely Cause |
|---|---|---|
| House01 s0 cp_sbd_quick | -9 (SIGKILL) | OOM kill - GSL server killed at startup |
| House01 s1 cp_sbd_quick | -9 then Python traceback | GSL OOM killed; vgr_sim cascading failure |
| House01 s2 cp_sbd_quick | Running normally | Algorithm runs but produces bad result |
| House03 s2 cp_sbd_quick | -6 (SIGABRT) | runtime_error: goal does not exist |

---

## 6. Launch File Analysis

File: /home/zyc/gsl_ws/src/vgr_bridge/launch/vgr_ablation.launch.py

```python
"distanceThreshold": -1.0,           # Correct: no ground truth stopping
"opgsl.sbd.cusum_threshold": 5.0,    # Ineffective: CUSUM stat is ~14000
"opgsl.sbd.eig_threshold": 0.0005,   # Never reached: CUSUM triggers first
"opgsl.seed": _int("seed"),          # WRONG: seeds algorithm RNG
"opgsl.modules.cp": true,            # CP enabled but never used for stopping
```

---

## 7. Fix Recommendations

### Fix 1: Remove Algorithm RNG Seeding (CRITICAL)

```cpp
// REMOVE THIS from declareParameters():
int seed_param = getParam<int>("opgsl.seed", -1);
if (seed_param >= 0) {
    rng_.seed(static_cast<unsigned int>(seed_param));
}

// KEEP THIS (always random for algorithm exploration):
rng_.seed(std::random_device{}());
```

If reproducibility is needed, use a SEPARATE parameter:
```cpp
int alg_seed = getParam<int>("opgsl.alg_seed", -1);
if (alg_seed >= 0) rng_.seed(static_cast<unsigned int>(alg_seed));
else rng_.seed(std::random_device{}());
```

### Fix 2: Fix CUSUM Initialization (CRITICAL)

```cpp
if (use_sbd_) {
    eig_field_ = Eigen::MatrixXf::Zero(n_cells_, n_cells_);
    // FIX: Initialize to uniform log-probability (log(1/N^2))
    float uniform_log = -std::log(float(n_cells_ * n_cells_));
    prev_posterior_ = Eigen::MatrixXf::Constant(n_cells_, n_cells_, uniform_log);
}
```

### Fix 3: Remove or Increase TIME FALLBACK (MODERATE)

```cpp
// Option A: Remove entirely (delete the elapsed_time_ > 250 block)
// Option B: Increase threshold to 500s
```

### Fix 4: Fix CP Residual Bug (LINE 916)

```cpp
float residual = std::sqrt(
    (mx - cp_prev_mx_) * (mx - cp_prev_mx_) +
    (my - cp_prev_my_) * (my - cp_prev_my_)
);
```

### Fix 5: Disable CP Module by Default

```cpp
use_cp_ = getParam<bool>("opgsl.modules.cp", false);  // Was: true
```

Or integrate into checkSourceFound():
```cpp
if (use_cp_ && cp_stopping_.shouldStop()) {
    float mx, my, mz; posterior3d_.getMAP(mx, my, mz);
    convergence_reported_ = true; return GSLResult::Success;
}
```

### Fix 6: Investigate OOM (VM-SIDE)

```bash
free -h
ps aux | grep gsl_actionserver
```

---

## 8. Is the SBD Module Fundamentally Broken?

**No, but it is not working as designed.** The SBD concept is sound (EIG-max sequential experiments from clinical trial design), but the current implementation has three issues:

1. **CUSUM initialization bug** -> CUSUM always triggers immediately -> EIG-max code never runs
2. **No integration of CP stopping** -> CP module is dead code
3. **RNG coupling** -> Algorithm RNG shares seed with simulation

The good Phase 1 results were achieved WITHOUT the SBD module's EIG-max logic (because the CUSUM bug caused it to skip straight to MAP). The good results came from the base SDNBV algorithm + upwind tracking + FAST EXIT convergence, with SBD merely navigating to MAP as a fallback.

---

## 9. Verification Checklist

After applying fixes, verify:

- [ ] prev_posterior_ initialized to log(1/N^2) not 0
- [ ] CUSUM stat at step 17 should be < threshold (not 14000)
- [ ] EIG-max exploration log messages appear in Phase 2
- [ ] House01 seeds 0-4: median < 0.5m
- [ ] House02 seeds 0-4: median < 0.3m
- [ ] House03 seeds 0-4: median < 1.0m
- [ ] No SIGKILL / OOM errors
- [ ] No prev_mx compile errors
- [ ] Algorithm RNG is NOT seeded with simulation seed

---

## 10. Appendix: Diff Summary

### OPGSL.cpp.pre_sbd -> OPGSL.cpp (Full diff)

| Category | Lines Changed | Description |
|---|---|---|
| SimpleGP | 31-46 | K.inverse() -> K.ldlt() |
| Parameters | 75-99 | Added SBD, CP, RNG seed params |
| Initialization | 115-121 | SBD field initialization |
| SBD module | 536-606 | EIG field + CUSUM + navigation |
| SDNBV indent | 607 | Re-indented SDNBV block |
| EIG functions | 832-892 | computeEIGField, computePosteriorKL |
| CP tracking | 907-917 | CP residual in processGasAndWind |
| Convergence | 1248-1302 | convergence_reported_ + TIME FALLBACK |

### OPGSL.hpp.pre_sbd -> OPGSL.hpp

| Category | Lines Changed | Description |
|---|---|---|
| Include | 17 | Added #include "CP_Stopping.hpp" |
| Convergence | 128 | Added convergence_reported_ |
| SBD members | 292-310 | SBD variables, EIG functions, CP objects |
