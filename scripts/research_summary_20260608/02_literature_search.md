# 02 Literature Search Results

## Search Method
- Semantic Scholar API with S2 API key
- Search period: 2023-2026
- Multiple query formulations per topic

## Current State-of-the-Art: MAPIRlab Dominance

The GSL field is dominated by ONE group: MAPIRlab at Universidad de Málaga
(Ojeda, Monroy, Gonzalez-Jimenez).

| Paper | Journal | Year | Citations | Key Innovation |
|-------|---------|------|-----------|----------------|
| **PMFS** | IEEE T-RO | 2024 | ~20 | Filament simulation + gas-hit map + Bayesian estimation |
| **GrGSL** | IEEE RAL | 2021 | ~50 | Grid-based information propagation |
| **SemanticPMFS/GrGSL** | — | 2024 | — | Semantic scene understanding added to GSL |
| **PSGSL** | arXiv | 2025 | — | Abstract probabilistic framework for semantic GSL |
| **IGDM** | Sensors | 2023 | — | Information-driven GDM with GW-GMRF + POMDP |
| **GADEN/GADEN-RT** | Sensors/SoftwareX | 2017/2025 | 86 | 3D gas dispersion simulator |

## Other Recent Papers (2024-2026)

| Paper | Venue | Year | Cites | Approach |
|-------|-------|------|-------|----------|
| "Sense in Motion with Belief Clustering" | ICRA | 2024 | 2 | Continuous sampling (not stop-and-measure) |
| "SniffySquad: Patchiness-Aware GSL" | ACM TOSN | 2024 | 3 | Multi-robot, patchiness-aware plume model |
| "Gas Source Localization Using PGNN" | ISOEN | 2024 | 7 | Physics-Guided Neural Network for GSL |
| "PGNN for Distributed Sparse GSL" | EUSIPCO | 2024 | 3 | PGNN + Poisson + Green's function |
| "Dueling DQN with Quadruped Robot" | IJARS | 2024 | 9 | RL on quadruped robot |
| "PF-WOA 3D GSL" | Robotica | 2024 | 1 | Particle filter + whale optimization |
| "Dual-Mode Info-Theoretic Search" | RAL | 2025 | 5 | Dual-mode information-theoretic GSL |
| "3D-Extended Entrotaxis" | CAC | 2025 | 0 | 3D entrotaxis for UAV |
| "3D Infotaxis + PF for UAV" | CCC | 2024 | 1 | 3D infotaxis + particle filter for UAV |
| "RL-UAV CO Source Localization" | IEEE Sensors Letters | 2025 | 1 | RL-based UAV CO localization |
| "Reactive-Probabilistic Hybrid" | SICE | 2024 | 1 | Reactive + probabilistic hybrid |
| "Deep Learning Topography-Aware GSL" | ICRA | 2025 | 0 | U-Net + SLAM for GSL |
| "LLM-OSL" | Sensors | 2024 | 4 | LLM for vision+olfaction fusion |
| "CGRInfotaxis" | Entropy | 2025 | 2 | Cooperative gravitational-Rényi infotaxis |
| "Calibration-Free GSL" | arXiv | 2026 | 0 | Concentration ranking (no calibration needed) |
| "Multi-Agent RL for UAV Chemical GSL" | arXiv | 2026 | 0 | Multi-agent RL for UAV |
| "CO2 Source Tracking with UAV" | EPREC | 2026 | 0 | WASG* algorithm for UAV |
| "Feed Forward NN for UAV CO2 GSL" | Sensors Conf | 2025 | 0 | FFNN for UAV CO2 tracking |
| "Chasing Ghosts: Sim-to-Real" | Sensors | 2026 | 1 | Sim-to-real olfactory navigation |

## UAV-Specific GSL Papers (Very Few)
- **3D Infotaxis + PF** (CCC 2024): 3D infotaxis + particle filter for UAV
- **3D Entrotaxis** (CAC 2025): 3D entrotaxis for UAV odor localization
- **RL-UAV** (IEEE Sensors Letters 2025): RL-based UAV navigation
- **Multi-Agent RL UAV** (arXiv 2026): Multi-agent RL for UAV chemical GSL
- **PPO-UAV** (Nanjing University): PPO+LSTM for methane plume tracing (student project)

## Key Observation
Most GSL research focuses on ground robots in 2D indoor environments.
UAV-based 3D GSL is significantly under-explored.

## Key Datasets
| Dataset | Type | Year | Access |
|---------|------|------|--------|
| **VGR Dataset** | Simulation (GADEN) | 2023 | MAPIRlab GitHub |
| **GSL-Bench** | Benchmark tool | 2024 | ICRA |
| **Red:Vapor** | Real wind tunnel 3D | 2026 | Zenodo (open access) |
| **MATRIX** | Real outdoor UAV | — | User has data |
| **ICASSP 2025 Challenge** | Real wind tunnel | 2025 | IEEE DataPort |
