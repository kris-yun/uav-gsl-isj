# 03 Cross-Domain Search Results

## Search Strategy
Searched for methods from: biology, physics, math, medicine, epidemiology,
seismology, signal processing, computer vision, control theory, RL.

## S2 API Search Results

### Biology: Optimal Foraging Theory
- **Levy flight + Bayesian + sparse search = 10 papers** (very few, novel for GSL)
- Levy flights are optimal for sparse target search (Viswanathan et al., Nature 1999)
- No paper combines Levy flight with Bayesian GSL

### Biology: Bacterial Chemotaxis
- **"bacterial chemotaxis" + "run and tumble" + robot + source localization = 0 papers**
- Completely novel direction

### Medicine: EEG Brain Source Localization
- **"brain source localization" + "spatial smoothness" + particle filter = 173 papers**
- LORETA (Pascual-Marqui 1994): spatial smoothness constraint for inverse problems
- Very few applications outside neuroscience

### Epidemiology: Contact Tracing
- **Backward trajectory analysis** (Riley 2003, Wallinga & Teunis 2004)
- Tracing infection chains along transport networks → upwind back-trace for GSL
- Applied in BPFM (Bayesian Particle Flow Mapping) from paper_summary code

### Seismology: Fisher Information
- **D-optimal experimental design** for sensor placement
- Fisher Information Matrix → optimal UAV waypoint selection
- Applied in FDPOE (Fisher-Driven Posterior Optimal Exploration)

### Signal Processing: Scale-Space Theory
- **"spatial coherence" OR "spatial smoothness" + posterior + source estimation = 1 result**
- Lindeberg 1994: multi-scale analysis for image features
- Applied to GSL posterior: analyze at multiple spatial resolutions

### Statistics: Sequential Analysis
- **"stopping rule" OR "optimal stopping" + gas source localization = 0 papers**
- Wald SPRT (1945): sequential probability ratio test
- Applied to GSL: when to stop searching and declare source found

### Atmospheric Science: Lagrangian Particle Tracking
- **"Lagrangian particle" + "source localization" + gas/odor = 0 papers**
- HYSPLIT / FLEXPART: Lagrangian particle dispersion models
- Physics-constrained particle dynamics (advection + diffusion + settling)

### Computer Vision: Multi-Modal Fusion
- **"multi-modal" + "gas source localization" + vision = 8 papers**
- Vision + olfaction fusion is emerging (LLM-OSL, PSGSL)
- Thermal + gas fusion is NOT explored

### Control Theory: Adaptive Control
- **Phase-adaptive control** for switching between exploration and exploitation
- Settling time concept for post-declaration refinement
