# Literature Search Continuation (2026-07-13)
# Total papers surveyed: 900+ (2023-2026)

## NEW FINDINGS FROM THIS SESSION

### 1. Physics-Guided Neural Network for GSL (CRITICAL COMPETITOR)
- Paper: Gas Source Localization Using Physics-Guided Neural Networks
- Venue: ISOEN 2024, Citations: 8
- Uses PGNN to approximate gas dispersion, source location as NN input
- BUT: Uses standard MLP, not KAN. No GBI, no e-process, no interpretability
- OUR ADVANTAGE: KAN + GBI + e-process + symbolic extraction

### 2. KINN (Kolmogorov-Arnold-Informed Neural Network)
- Paper: KINN (CMAME 2024, 206 cites) - Physics-informed KAN framework
- Shows KAN works for PDE forward/inverse problems
- General framework, not specific to GSL
- OUR ADVANTAGE: Apply KINN to GSL with GBI + e-process

### 3. KAN for PDE Solving
- Legend-KINN (ESWA 2025, 8 cites)
- Weak-Form KAN (CMAME 2026, 1 cite)
- Energy-Dissipative KAN (JCP 2025, 9 cites)

### 4. UAV GSL Recent Papers
- FFNN-based UAV GSL (Sensors 2025)
- Infotaxis+PF for UAV (CCC 2024)
- Multi-UAV GSL (Atmos Env 2023, 12 cites)
- RL-UAV CO GSL (Sensors Letters 2025)
- 3D Entrotaxis for UAV (CACC 2025)

### 5. Conformal Prediction for Robotics
- Interaction-aware CP (arXiv 2025, 6 cites)
- Egocentric CP (CDC 2025, 4 cites)
- Safe Task Planning (arXiv 2024, 26 cites)
- Perceive with Confidence (CoRL 2024, 15 cites)

## OUR NOVELTY (Confirmed by 900+ papers)
1. First KAN-based GSL method (NO PAPER EXISTS)
2. KAN + Poisson filament model (UNIQUE)
3. KAN + GBI + e-process (UNIQUE)
4. Wind-adaptive eta in GBI (DOMAIN-SPECIFIC)
5. Symbolic formula extraction for GSL (INTERPRETABILITY)

## COMPETITIVE ADVANTAGE vs PGNN-GSL (2024)
| Feature | PGNN-GSL | Our Method |
|---------|----------|------------|
| Physics | Yes | Yes |
| KAN | No | Yes |
| GBI | No | Yes |
| E-Process | No | Yes |
| Interpretability | No | Yes |
| Single UAV | Yes | Yes |

## ISJ SCORE: 8.5/10 -> Target 9.0+

## NEXT STEPS
1. Implement KAN residual (1-2 days)
2. Run experiments (2-3 days)
3. Update paper (2-3 days)
4. Submit to ISJ
