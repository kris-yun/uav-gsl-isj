# Iteration 1: Baseline Audit

## Objective
Verify that baselines use official implementations, not simplified versions.

## Task
Compare current baseline implementations with official GitHub repos.

---

## Step 1: Check SurgeCast Implementation

### Official Algorithm (MAPIRlab/Gas-Source-Localization)

From paper "Active Source Localization" (2020):
`
SURGE-CAST algorithm:
1. If gas detected:
   - Phase = SURGE
   - Move upwind (toward source)
   - cast_amplitude = step_size
   
2. If gas not detected:
   - Phase = CAST
   - Move perpendicular to wind
   - cast_amplitude *= expand_factor
   - If consecutive_misses % 10 == 0:
     cast_direction *= -1
`

### Current Implementation

File: workspace/uav_diagsense/src/baselines/simple_planners.py

`python
class SurgeCastPlanner:
    # Check implementation here
`

### Comparison Checklist

- [ ] Gas threshold matches paper
- [ ] Upwind direction calculation correct
- [ ] Cast amplitude expansion correct
- [ ] Cast direction flip logic correct
- [ ] Drift toward last hit position correct

### Action
If differences found:
1. Document in utomation/results/iter1_baseline_audit.md
2. Fix implementation OR note why deviation is acceptable

---

## Step 2: Check Infotaxis Implementation

### Official Algorithm (Vergassola et al., 2007)

`
INFOTAXIS algorithm:
1. For each candidate waypoint w:
   - Compute p_hit = P(gas detected at w | source hypothesis)
   - Compute H_hit = entropy if hit at w
   - Compute H_miss = entropy if miss at w
   - EIG(w) = H_current - (p_hit * H_hit + (1-p_hit) * H_miss)

2. Select waypoint with max EIG
`

### Current Implementation

File: workspace/uav_diagsense/src/baselines/info_planners.py

`python
class InfotaxisPlanner:
    # Check implementation here
`

### Comparison Checklist

- [ ] Candidate generation matches paper
- [ ] Hit probability calculation correct
- [ ] Entropy calculation correct
- [ ] EIG formula correct
- [ ] Selection logic correct

---

## Step 3: Check KLD Implementation

### Official Algorithm (Infotaxis variant)

`
KLD-based active sensing:
1. For each candidate waypoint w:
   - Compute KL divergence between posterior and uniform
   - Select waypoint that maximizes KL divergence

2. OR: Select waypoint that maximizes expected KL divergence
`

### Current Implementation

File: workspace/uav_diagsense/src/baselines/info_planners.py

`python
class KLDPlanner:
    # Check implementation here
`

---

## Step 4: Document Findings

Write to utomation/results/iter1_baseline_audit.md:

`markdown
# Baseline Audit Report

## SurgeCast
- Source: [official paper/repo]
- Current implementation: [file path]
- Differences: [list differences]
- Recommendation: [use official / keep current / fix]

## Infotaxis
- Source: [official paper/repo]
- Current implementation: [file path]
- Differences: [list differences]
- Recommendation: [use official / keep current / fix]

## KLD
- Source: [official paper/repo]
- Current implementation: [file path]
- Differences: [list differences]
- Recommendation: [use official / keep current / fix]

## Summary
- Total baselines: 5
- Using official: X
- Need fixes: X
- Acceptable deviations: X
`

---

## Step 5: Check Available Official Implementations

### GitHub Repos Found

1. **MAPIRlab/Gas-Source-Localization** (C++)
   - Algorithms: PMFS, GrGSL, surge_cast, spiral, particle_filter
   - Language: C++ (ROS2)
   - Status: Available

2. **smueller18/TDKernelDMVW** (Python)
   - Algorithms: KernelDM, TD-KernelDM, KernelDM+V, KernelDM+W
   - Language: Python
   - Status: Available

3. **Your Modules** (Python)
   - Location: workspace/modules/
   - Algorithms: Various (bgar, crcf, mast_gsl, etc.)
   - Status: Available

### Recommendation

For Python implementation:
- Keep current implementations if they match algorithm logic
- Use official Python packages where available (TDKernelDMVW)
- Port C++ algorithms to Python if needed

---

## Deliverable

When complete, say:
"Iteration 1 complete. Baseline audit saved to automation/results/iter1_baseline_audit.md"
