# Code Cleanup + Robustness + Third Module Plan

## Task 1: Remove Dead Code
- PwcCorrector: remove alpha parameter
- PMFS.hpp/cpp: remove hce_wind_dir_accum
- Build and verify

## Task 2: Fix Parameter Passing
- Verify mac_max_distance_weight reaches runtime

## Task 3: Inject MAC into Search Loop
- Run MAC estimation during processGasAndWindMeasurements
- Lower threshold from 10 to 5 hits
- Add probability boost at MAC estimate

## Task 4: Failure Data Analysis
- Run 8 seeds baseline on House01/02
- Classify: timeout vs converged-wrong vs converged-right
- Identify failure pattern

## Task 5: Third Innovation Module
- Based on failure analysis
- Cross-domain from medical/biomath/physics
