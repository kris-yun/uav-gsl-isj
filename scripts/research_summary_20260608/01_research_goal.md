# 01 Research Goal

## Paper Requirements
- **Target**: SCI Q3 journal (NOT MDPI Sensors, but not top-tier either)
  - Candidates: Robotica, ISA Transactions, Measurement, J. Field Robotics
- **Innovation level**: 3 distinct modules with ablation studies
  - Each module must have theoretical support from a different domain
  - Each module must independently contribute (verified by ablation)
  - NOT just "use a new dataset" — must be genuine method innovation
- **Performance**: At least 10% improvement over classical methods
- **No data leakage or overfitting**: All experiments must run on real/simulated data, NOT synthetic training data
- **Comparison**: Must compare against official implementations of PMFS, GrGSL, SurgeCast (from MAPIRlab GSL package)
- **Cross-domain ideas required**: At least some modules should borrow ideas from other fields (biology, physics, math, medicine, etc.) — NOT just combining existing GSL methods

## User's Two Strategies for Innovation
1. **"Borrow the boat" (借船出海)**: Take an existing framework from another field and apply it to GSL
2. **"Swap the core" (换芯升级)**: Replace a core component of a classical model with something better

## Constraints
- User's VM has the official MAPIRlab GSL package installed (PMFS, GrGSL, SurgeCast, etc.)
- VM runs ROS2 Humble with GADEN simulator
- User has MATRIX outdoor dataset (14 trials) and access to VGR indoor dataset (30 houses)
- User has Red:Vapor wind tunnel dataset available
- All experiments must run on VM with real data, NOT synthetic local data
