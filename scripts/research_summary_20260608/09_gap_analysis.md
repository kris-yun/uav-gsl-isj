# 09 Gap Analysis

## Three Questions (User's Framework)

### Q1: Why must this problem be solved NOW?
Because three things appeared in 2024-2026 that didn't exist before:
1. **GSL-Bench (ICRA 2024)** — first standardized GSL benchmark
2. **Red:Vapor (Nature Sci Data, 2026)** — first public 3D real wind tunnel dataset
3. **Low-cost UAV + gas sensors** — industrial inspection and emergency response
   demand for UAV GSL just emerged

**Bottom line: Datasets and hardware are ready, but methods are still from 2024
ground-robot era.**

### Q2: Where did predecessors get stuck?
Three specific gaps:
1. **PMFS (IEEE T-RO 2024, current SOTA)** only works in 2D on ground robots.
   It needs known environment geometry (GMRF needs walls/doors info). Fails outdoors.
2. **SurgeCast** is excellent in simple environments (0.2m) but degrades badly
   in complex ones (House02: 4.15m). No posterior estimate — doesn't know "how
   confident am I."
3. **No one has validated UAV methods on Red:Vapor or GSL-Bench.**
   All UAV GSL papers use custom simulation. No standardized comparison.

**Bottom line: PMFS can't fly, SurgeCast isn't reliable, UAV methods lack
standardized validation.**

### Q3: Who will care?
Three specific teams:
1. **MAPIRlab (Ojeda/Monroy/Gonzalez-Jimenez, Univ. Málaga)** — wrote PMFS,
   GrGSL, GADEN, GSL-Bench. Their PSGSL (2025) explicitly says "future work:
   extending to UAV platforms." If you do it first with their GSL-Bench, they
   MUST cite you.
2. **DLR Sensor Processing (Shutin/Hinsen/Lilienthal)** — made Red:Vapor and
   ICASSP 2025 GSL Challenge. Their dataset paper's motivation is "advance
   robotic olfaction and autonomous robotic exploration." First UAV GSL method
   validated on Red:Vapor → they MUST cite you.
3. **Nanjing University CH4 UAV Team** — doing PPO+LSTM UAV methane tracing.
   They use RL, no Bayesian posterior. If your method outperforms RL with less
   training data, they WILL cite you as comparison baseline.

## Identified Gaps (Ranked by Novelty × Feasibility)

### Gap 1: UAV 3D GSL with Altitude Adaptation
- **Novelty**: HIGH — no one has formally optimized UAV altitude for GSL
- **Feasibility**: MEDIUM — needs 3D data (Red:Vapor or GADEN)
- **Risk**: MAPIRlab may do this themselves within 1-2 years

### Gap 2: Multi-Modal Sensor Fusion for GSL (Thermal + Gas)
- **Novelty**: HIGH — thermal cameras used for leak detection but not for GSL
- **Feasibility**: LOW — needs thermal data, not available in current datasets
- **Risk**: High implementation effort

### Gap 3: Physics-Informed Particle Filter for GSL
- **Novelty**: MEDIUM-HIGH — S2 confirms 0 overlap
- **Feasibility**: HIGH — modifies existing PF code (~100 lines)
- **Risk**: Small improvement (3.3% on real data)

### Gap 4: Environment-Adaptive Strategy Selection
- **Novelty**: MEDIUM — meta-learning for GSL strategy selection is new
- **Feasibility**: MEDIUM — needs to run multiple algorithms
- **Risk**: Might be seen as "wrapping existing methods"

### Gap 5: Learned Plume Model + PF
- **Novelty**: HIGH — S2 confirms 0 overlap
- **Feasibility**: HIGH — simple NN training
- **Risk**: FAILED — data leakage, overfitting, no theoretical basis

### Gap 6: Multi-Source GSL
- **Novelty**: HIGH — very few papers address multiple simultaneous sources
- **Feasibility**: LOW — complex problem, needs multi-source data
- **Risk**: Too ambitious for Q3 paper
