# Experiment Plan: Clean Code + Fix Issues + KAN Training
# Date: 2026-07-13

## Phase 1: Code Cleanup (Remove Useless Modules)

Modules to REMOVE (negative or unused):
1. DDM (Drift-Diffusion Model) - NEGATIVE, hurts 0.27m
2. WRAIG (Wasserstein Risk-Aware IG) - not contributing
3. SBD (Sequential Bayesian Design) - not contributing
4. EDPA (Event-Driven Posterior) - not used
5. BH-EX (Basin-Hopping) - not used
6. WAZ (Wind-Aligned Zigzag) - not used
7. SC (Surge-Cast internal) - not used
8. EIG Height (legacy) - not used

Modules to KEEP (validated):
1. GBI Posterior (SourcePosterior3D) - core
2. Wind-Adaptive eta - core contribution
3. E-Process Stopping (CP_Stopping) - core contribution
4. 3-Phase Navigation - core
5. GP Height Selection - core contribution
6. Levy Flight - exploration (validated)
7. Bout-Level - behavioral (validated)
8. Adaptive Step - step size (validated)

Expected: ~1950 lines reduced to ~1200 lines

## Phase 2: Fix Source Position Config

Current: batch_proven.sh hardcodes positions
Fix: Create centralized config source_positions.yaml

Positions (to verify):
- House01: (-0.40, -2.90, -0.30) near ground
- House02: (0.00, -1.00, 0.20) low height
- House03: (-0.45, 1.9, -0.1) near ground (overridden)
- House04: TBD (need to check GADEN)
- House05: TBD (need to check GADEN)

## Phase 3: Run Clean Baseline (10-seed x 3-house)

3.1 Build cleaned code
3.2 Run our method: 30 runs (~3 hours)
3.3 Run baselines: SurgeCast/GrGSL/PMFS x 10 seeds x 3 houses = 90 runs (~9 hours)
3.4 Statistical analysis: mean, std, Wilcoxon test, Cohen d

## Phase 4: KAN Residual Training

4.1 Install pykan on VM (0.1MB)
4.2 Prepare data: GADEN House01-03, input=(conc,wx,wy,dist,step), output=residual
4.3 Train KAN: width=[5,16,8,1], grid=5, k=3, LBFGS, 100 epochs (~1 hour)
4.4 Extract symbolic formula via suggest_symbolic()
4.5 Implement formula in C++ (no runtime NN)
4.6 Validate KAN vs MLP ablation

## Phase 5: Final Experiments (5-house)

5.1 Expand to House04-05 with verified positions
5.2 Run all methods: 10 seeds x 5 houses x 4 methods = 200 runs
5.3 Comprehensive analysis

## Phase 6: Paper Update

6.1 Remove DDM from method description
6.2 Add KINN reference and KAN theory
6.3 Update experiments with 5-house results
6.4 Add interpretability analysis (symbolic formula)

## Timeline (~1 week)
- Phase 1-2: 3-4 hours
- Phase 3: 12 hours
- Phase 4: 1-2 days
- Phase 5: 1-2 days
- Phase 6: 2-3 days

## Success Criteria for ISJ (7.5+)
1. Our method beats SurgeCast on 3+ houses
2. Statistical significance (p < 0.05)
3. KAN adds clear interpretability
4. 5-house experiments completed
5. Clean code (no negative modules)