# Iteration 0: Baseline Audit & Innovation Design

## Objective
1. Verify baselines use official implementations (not simplified)
2. Design 3 innovations from non-robotics domains

---

## Part 1: Baseline Audit

### Current Baselines in DQA-AS

| Method | Source | Status |
|--------|--------|--------|
| Random | Custom (simple_planners.py) | OK - trivial |
| GreedyMAP | Custom (simple_planners.py) | OK - trivial |
| SurgeCast | Custom (simple_planners.py) | NEED VERIFICATION |
| Infotaxis | Custom (info_planners.py) | NEED VERIFICATION |
| KLD | Custom (info_planners.py) | NEED VERIFICATION |

### Official Implementations Found

| Method | GitHub Repo | Status |
|--------|-------------|--------|
| SurgeCast | MAPIRlab/Gas-Source-Localization (C++) | Available |
| Spiral | MAPIRlab/Gas-Source-Localization (C++) | Available |
| ParticleFilter | MAPIRlab/Gas-Source-Localization (C++) | Available |
| PMFS | MAPIRlab/Gas-Source-Localization (C++) | Available |
| TDKernelDMVW | smueller18/TDKernelDMVW (Python) | Available |

### Task: Verify SurgeCast Implementation

**Official Algorithm** (from MAPIRlab paper):
`
if gas_detected:
    phase = SURGE
    move upwind (toward source)
    cast_amplitude = step_size
else:
    phase = CAST
    move perpendicular to wind
    cast_amplitude *= expand_factor
    if consecutive_misses % 10 == 0:
        cast_direction *= -1
`

**Current Implementation** (simple_planners.py):
`python
# Check if matches official algorithm
`

### Task: Verify Infotaxis Implementation

**Official Algorithm** (Vergassola et al., 2007):
`
for each candidate waypoint:
    compute E[entropy] = p_hit * H_hit + p_miss * H_miss
    select waypoint with max EIG = H_current - E[entropy]
`

**Current Implementation** (info_planners.py):
`python
# Check if matches official algorithm
`

### Deliverable
Write utomation/results/iter0_baseline_audit.md with:
1. Each baseline: official vs current comparison
2. Differences found
3. Recommendation: use official or keep current

---

## Part 2: Innovation Design (3 Innovations from Non-Robotics Domains)

### Design Constraints
1. NOT from robotics/olfaction domain (avoid repackaging accusations)
2. Borrow from: medical imaging, biomath, signal processing, computer vision
3. Must be implementable in Python
4. Must address a real failure mode in current GSL methods

### Innovation 1: MEMP - Medical Evidence Mass Processing
**Source Domain**: Brain Source Localization (EEG/MEG)

**Original Problem**: In EEG, multiple sensors detect brain electrical activity. The goal is to localize the source (dipole) from noisy, sparse sensor readings.

**Key Technique**: LORETA (Low Resolution Electromagnetic Tomography)
- Assumes source is spatially smooth
- Uses Laplacian constraint for regularization
- Fast computation via matrix inversion

**Borrowed to GSL**:
- Gas sensors = EEG sensors
- Gas source = brain dipole
- Wind = volume conductor (current flow)

**Implementation**:
`python
class MEMPEstimator:
    """Medical Evidence Mass Processing for GSL.
    
    Borrowed from: EEG source localization (LORETA family)
    Key idea: Spatial smoothness constraint prevents posterior collapse
    """
    def __init__(self, grid, occ_2d, emin, cell_size):
        self.grid = grid
        # Build Laplacian matrix for spatial smoothness
        self.L = self._build_laplacian(occ_2d)
    
    def _build_laplacian(self, occ_2d):
        """Build graph Laplacian for free-space cells."""
        # Similar to LORETA's Laplacian constraint
        pass
    
    def update(self, x, wind, hit, weight=1.0):
        """Update posterior with spatial smoothness constraint."""
        # Standard likelihood
        ll = self._likelihood(x, wind, hit)
        
        # Apply Laplacian smoothing (prevents isolated peaks)
        ll_smooth = ll - 0.1 * self.L @ ll
        
        # Update posterior
        self.lp += weight * ll_smooth
`

**Why This Works**:
- Current methods: posterior can have spurious isolated peaks
- MEMP: Laplacian constraint enforces spatial coherence
- Result: smoother posterior, better source estimate

**Paper Claim**: "First application of EEG source localization techniques to gas source localization"

---

### Innovation 2: BPFM - Bayesian Particle Flow Mapping
**Source Domain**: Biomathematics (Population Dynamics / Epidemic Spreading)

**Original Problem**: In epidemiology, disease spreads through a population. The goal is to estimate the source (patient zero) from observed infection patterns.

**Key Technique**: Particle Flow ( Sequential Monte Carlo for source estimation)
- Uses SIR/SEIR dynamics as forward model
- Particles flow from observations toward source
- Accounts for transmission network structure

**Borrowed to GSL**:
- Disease spread = gas dispersion
- Infection network = wind transport network
- Patient zero = gas source

**Implementation**:
`python
class BPFMEstimator:
    """Bayesian Particle Flow Mapping for GSL.
    
    Borrowed from: Epidemiological source estimation
    Key idea: Particles flow along wind transport network, not random walk
    """
    def __init__(self, grid, occ_2d, emin, cell_size, n_particles=1000):
        self.particles = self._init_particles(grid, n_particles)
        self.weights = np.ones(n_particles) / n_particles
    
    def update(self, x, wind, hit):
        """Update particles using wind-transport flow."""
        # 1. Compute flow field (wind-aligned)
        flow = self._compute_flow(wind)
        
        # 2. Move particles along flow (toward source)
        self.particles = self._flow_particles(self.particles, flow)
        
        # 3. Reweight based on observation
        if hit:
            # Particles near observation get higher weight
            self.weights *= self._hit_likelihood(x)
        else:
            # Particles far from observation get higher weight
            self.weights *= self._miss_likelihood(x)
        
        # 4. Resample if needed
        if self._ess() < 0.5 * len(self.particles):
            self._resample()
    
    def _flow_particles(self, particles, flow):
        """Move particles along wind-transport network."""
        # Key innovation: particles flow UPWIND (toward source)
        # Not random diffusion like standard particle filter
        pass
`

**Why This Works**:
- Standard particle filter: particles diffuse randomly
- BPFM: particles flow along wind network (upwind toward source)
- Result: faster convergence, fewer particles needed

**Paper Claim**: "First application of epidemiological source estimation to gas source localization"

---

### Innovation 3: SDM - Sparse Deconvolution Mapping
**Source Domain**: Computer Vision (Image Deblurring / Super-Resolution)

**Original Problem**: In image processing, a blurred image is the convolution of the sharp image with a blur kernel. The goal is to recover the sharp image (deconvolution).

**Key Technique**: Sparse Deconvolution (L1 regularization)
- Assumes the sharp image is sparse (few bright points)
- Uses L1 penalty to enforce sparsity
- Fast algorithms (ADMM, ISTA)

**Borrowed to GSL**:
- Blurred image = gas concentration map (smeared by wind)
- Blur kernel = wind dispersion kernel
- Sharp image = true source location (sparse: 1 point)

**Implementation**:
`python
class SDMEstimator:
    """Sparse Deconvolution Mapping for GSL.
    
    Borrowed from: Image deblurring (L1 deconvolution)
    Key idea: Gas map is blurred source convolved with wind kernel
    """
    def __init__(self, grid, occ_2d, emin, cell_size):
        self.grid = grid
        # Build wind dispersion kernel
        self.K = self._build_kernel(wind)
    
    def _build_kernel(self, wind):
        """Build wind-aligned dispersion kernel."""
        # Gaussian kernel elongated along wind direction
        pass
    
    def update(self, x, wind, hit):
        """Update using sparse deconvolution."""
        # 1. Build observation vector
        obs = self._build_observation(x, hit)
        
        # 2. Solve L1 deconvolution
        # min ||K * s - obs||^2 + lambda * ||s||_1
        # where s is source distribution (sparse)
        source_est = self._solve_l1(obs, self.K)
        
        # 3. Update posterior
        self.posterior = source_est
`

**Why This Works**:
- Current methods: posterior is blurred by wind dispersion
- SDM: deconvolution recovers sharp source location
- Result: more precise source estimate

**Paper Claim**: "First application of sparse deconvolution to gas source localization"

---

## Summary: Three Innovations

| # | Name | Source Domain | Key Idea | Fixes |
|---|------|--------------|----------|-------|
| 1 | MEMP | EEG Brain Source Localization | Spatial smoothness constraint | Posterior collapse |
| 2 | BPFM | Epidemiological Source Estimation | Wind-transport particle flow | Random diffusion |
| 3 | SDM | Image Deblurring | Sparse L1 deconvolution | Wind-blurred posterior |

## Paper Framing

**Title**: "Cross-Domain Innovations for UAV Gas Source Localization: 
         EEG-Informed Spatial Regularization, Epidemiological Particle Flow, 
         and Sparse Deconvolution Mapping"

**Novelty**: First systematic transfer of techniques from medical imaging, 
epidemiology, and computer vision to gas source localization.

---

## Next Steps

1. Run baseline audit (verify official implementations)
2. Implement MEMP (simplest, most likely to work)
3. Test MEMP vs baselines
4. If MEMP works, implement BPFM and SDM
5. Full comparison

## Deliverable for This Iteration

Write to utomation/results/iter0_innovation_design.md:
1. Baseline audit results
2. Detailed MEMP implementation spec
3. Expected improvements
