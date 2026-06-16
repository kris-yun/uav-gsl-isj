# UAV-GSL-ISJ

UAV Gas Source Localization method for IEEE Sensors Journal.

## Method: DQA-AS (Dynamic Quality-Adaptive Source estimation)

Three cross-domain innovation modules:
1. **SDR** - Spatial Deconvolution Refinement (medical imaging)
2. **TDC** - Temporal Deconvolution Correction (signal processing)
3. **MHC** - Morphological Hit-map Cleanup (image processing)

Combined via DQA pipeline with conditional activation based on signal quality.

## Results (seed=0)

| Dataset | Baseline | DQA-AS | Improvement |
|---------|----------|--------|-------------|
| VGR House01 | 3.27m | 2.66m | -18.7% |
| VGR House02 | 4.22m | 3.27m | -22.5% |

## Repository Structure

- `code/` - Modified PMFS source code with DQA modules
- `data/` - Experimental results (CSV + audit)
- `docs/` - Scientific problem, module design, experiment design
- `results/` - Aggregated results and analysis

## VM Setup

- ROS2 Humble on 192.168.111.128
- Official MAPIRlab GSL package with fix overlay
- VGR dataset at /mnt/hgfs/workspace/data/VGR/
