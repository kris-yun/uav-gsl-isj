# 10 Current Recommendation

## Status: Multiple directions explored, none fully satisfactory

## What We Know for Certain
1. PMFS is the SOTA but has clear limitations (premature declaration, 2D only)
2. SurgeCast achieves near-perfect results on simple environments (0.2m)
3. All methods fail on complex environments (House02: 4-5m)
4. UAV-based 3D GSL is under-explored
5. Red:Vapor dataset provides first real 3D validation data
6. Cross-domain ideas have potential but are hard to implement correctly

## Most Promising Direction: UAV 3D GSL

### Why
- PMFS can't fly (ground robot only)
- SurgeCast is ground-only
- No UAV method has been validated on Red:Vapor or GSL-Bench
- 3D altitude optimization is a clear, novel contribution
- MAPIRlab explicitly listed "UAV extension" as future work

### Proposed Title
"Altitude-Adaptive Bayesian Active Search for UAV-Based Gas Source Localization"

### Three Innovation Modules
1. **Altitude-Adaptive Observation Model**: Different gas concentrations at
   different heights. Use vertical wind profile to model altitude-dependent
   plume structure.
   - Cross-domain: atmospheric boundary layer theory

2. **3D Advection-Diffusion Particle Filter**: Extend particle filter to 3D
   with vertical dynamics (buoyancy, settling).
   - Cross-domain: Lagrangian particle tracking (HYSPLIT)

3. **Multi-Scale Exploration Strategy**: Coarse grid at high altitude for
   plume detection, fine grid at low altitude for source refinement.
   - Cross-domain: computer vision scale-space theory (Lindeberg 1994)

### Validation Plan
- Red:Vapor wind tunnel (real 3D data, primary)
- GADEN VGR 3D (simulation, comparison with PMFS)
- MATRIX outdoor (2D subset, generalization)

### Baselines
- PMFS (2D ground, from MAPIRlab)
- GrGSL (2D ground, from MAPIRlab)
- 3D Infotaxis (CCC 2024)
- 3D Entrotaxis (CAC 2025)
- Fixed-altitude version (ablation)

### Risk Assessment
- PMFS can't be directly compared (different dimensionality)
- Red:Vapor data might not have strong vertical gradients
- MAPIRlab might publish UAV extension before us

## Alternative Direction: Multi-Modal Fusion (Vision + Gas)

### Why
- PSGSL (2025) showed semantic info helps GSL
- Thermal cameras detect gas leaks (industry practice)
- No paper combines thermal + gas for GSL

### Risk
- Needs thermal data not in current datasets
- Higher implementation effort
- More speculative

## Recommendation
Go with UAV 3D GSL direction. It's the clearest gap with the best
available data (Red:Vapor) and the most natural extension of existing code.
