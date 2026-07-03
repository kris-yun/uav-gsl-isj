# SDA-BAS Automation: Start Here for Claude Code

## IMPORTANT: User Requirements

1. **Baselines must use official implementations** from GitHub, not simplified versions
2. **3 innovations from non-robotics domains** (medical, biomath, computer vision)
3. **Do NOT borrow from robotics/olfaction** (avoid repackaging accusations)
4. **Use Semantic Scholar API** for literature search (key: s2k-DJ79WAMVOUXsjHZFtpjAKTOqMIqKoZpKTIvHZUV5)

---

## Three Innovations to Implement

### Innovation 1: MEMP (Medical Evidence Mass Processing)
- **From**: EEG Brain Source Localization (LORETA)
- **Idea**: Spatial smoothness constraint via graph Laplacian
- **Fixes**: Posterior collapse, isolated peaks
- **Spec**: automation/specs/iter2_memp_implementation.md

### Innovation 2: BPFM (Bayesian Particle Flow Mapping)
- **From**: Epidemiological Source Estimation
- **Idea**: Particles flow along wind transport network
- **Fixes**: Random diffusion, slow convergence

### Innovation 3: SDM (Sparse Deconvolution Mapping)
- **From**: Image Deblurring (L1 deconvolution)
- **Idea**: Deconvolve wind-blurred posterior
- **Fixes**: Wind-blurred posterior

---

## Your Tasks (In Order)

### Task 1: Baseline Audit
Read utomation/specs/iter1_baseline_audit.md
- Compare current baselines with official implementations
- Write audit report to utomation/results/iter1_baseline_audit.md

### Task 2: Implement MEMP
Read utomation/specs/iter2_memp_implementation.md
- Create workspace/uav_diagsense/src/memp/ directory
- Implement MEMPPosteriorEstimator
- Write unit tests
- Run tests

### Task 3: Run Experiment
Read utomation/specs/iter3_experiment.md
- Run MEMP vs baselines on House01
- Save results to utomation/results/iter3_comparison.csv
- Write summary

---

## Output Format

When you complete a task, say:

`
## Task N Complete

### Results
- [Key metric]: [value]
- [Status]: PASS/FAIL

### Files Created
- automation/results/iterN_*.csv
- automation/results/iterN_summary.md

### Ready for Review
Awaiting your review and next task.
`

---

## File Structure

`
automation/
├── START_HERE.md              <- This file
├── specs/
│   ├── iter1_baseline_audit.md
│   ├── iter2_memp_implementation.md
│   └── iter3_experiment.md
├── results/                   <- Your output goes here
└── reviews/                   <- My reviews go here
`

---

## Current Status

**Task**: 1 (Baseline Audit)
**Spec**: automation/specs/iter1_baseline_audit.md
**Action**: Execute the baseline audit.
