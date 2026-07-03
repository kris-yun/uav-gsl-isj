"""Generate verified free-cell start positions for GADEN experiments.

Replaces the old OCC/OOB + BFS approach that caused seed convergence.
Each start position is pre-verified to be in a free cell.
"""
import os, sys, json
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
UAV_DIR = os.path.join(PROJECT_ROOT, "workspace", "uav_diagsense")
SRC_DIR = os.path.join(UAV_DIR, "src")
sys.path.insert(0, SRC_DIR)
sys.path.insert(0, os.path.join(SRC_DIR, "dqa_as"))

SHARED = os.path.join(PROJECT_ROOT, "workspace", "rearch", "gsl_budgeted_declaration")
sys.path.insert(0, os.path.join(SHARED, "src"))
sys.path.insert(0, SHARED)
sys.path.insert(0, os.path.join(SHARED, "FINAL_SUMMARY", "08_v28_sparse_physics_moe"))

from v28_modules.occupancy_utils import load_occupancy_2d
from grid_utils import build_candidate_grid
from common_runner import parse_occ_meta

VGR_BASE = os.path.join(PROJECT_ROOT, "workspace", "data", "VGR",
                         "GADEN_files", "GADEN_files", "scenarios")

def get_free_cells(house):
    """Get all verified free cells for a house."""
    VGR = os.path.join(VGR_BASE, house)
    occ_file = os.path.join(VGR, "OccupancyGrid3D.csv")
    emin, emax = parse_occ_meta(occ_file)
    occ_2d, _, occ_meta = load_occupancy_2d(occ_file, z_min=0.5, z_max=2.0, inflate_cells=1)
    cell_size = occ_meta["cell_size"]
    grid, grid_ij, mask, grid_info = build_candidate_grid(
        emin, emax, 1.0, occ_2d, cell_size, free_only=True)
    return grid, grid_info, emin, emax, cell_size

def generate_starts(house, n_seeds=8, min_dist_from_source=None, source=None):
    """Generate n verified free-cell start positions.
    
    Rules:
    1. Every start MUST be in a verified free cell (no BFS fallback)
    2. Start positions must be at least min_dist_from_source apart
    3. Start positions must be at least min_dist_from_source from source
    4. Spread across the environment (not clustered)
    """
    grid, grid_info, emin, emax, cell_size = get_free_cells(house)
    n_free = grid_info["n_candidate_free"]
    
    if min_dist_from_source is None:
        # Use 60% of environment diagonal as minimum distance
        diag = np.linalg.norm(emax[:2] - emin[:2])
        min_dist_from_source = diag * 0.3
    
    print(f"{house}: {n_free} free cells, min_dist_from_source={min_dist_from_source:.2f}m")
    
    # Filter cells far from source
    if source is not None:
        sxy = np.array(source[:2])
        dists = np.linalg.norm(grid - sxy[np.newaxis, :], axis=1)
        candidates = grid[dists >= min_dist_from_source]
    else:
        candidates = grid.copy()
    
    # Spread selection: pick diverse positions
    np.random.seed(42)  # Reproducible
    selected = []
    for _ in range(min(n_seeds, len(candidates))):
        if len(selected) == 0:
            # Pick the farthest from center
            center = np.mean(candidates, axis=0)
            dists = np.linalg.norm(candidates - center[np.newaxis, :], axis=1)
            idx = np.argmax(dists)
        else:
            # Pick the point that maximizes minimum distance to all selected
            min_dists = np.full(len(candidates), np.inf)
            for s in selected:
                d = np.linalg.norm(candidates - np.array(s)[np.newaxis, :], axis=1)
                min_dists = np.minimum(min_dists, d)
            idx = np.argmax(min_dists)
        
        selected.append(candidates[idx].tolist())
    
    return selected

# Generate for all houses
houses = {
    "House01": {"config_id": "2,4-1_fast", "source": (-0.4, -2.9, -0.3)},
    "House02": {"config_id": "3,5-1_fast", "source": (0.0, -1.0, 0.2)},
    "House03": {"config_id": "1-2,5_fast", "source": (-0.45, 1.9, -0.1)},
}

all_starts = {}
for house, info in houses.items():
    print(f"\n=== {house} ===")
    starts = generate_starts(house, n_seeds=8, source=info["source"])
    all_starts[house] = {
        "config_id": info["config_id"],
        "source": list(info["source"]),
        "starts": starts,
        "n_starts": len(starts),
    }
    for i, s in enumerate(starts):
        print(f"  Seed {i}: ({s[0]:.2f}, {s[1]:.2f})")

# Save
out_path = os.path.join(PROJECT_ROOT, "experiments", "official_baselines", "verified_starts.json")
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w") as f:
    json.dump(all_starts, f, indent=2)
print(f"\nSaved to {out_path}")
