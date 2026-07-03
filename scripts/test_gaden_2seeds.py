"""Test: 2 seeds in one process with playSimulation + stopPlaying."""
import sys, os, time
import numpy as np

sys.path.insert(0, "workspace/uav_diagsense/src")
sys.path.insert(0, "workspace/uav_diagsense/src/dqa_as")
sys.path.insert(0, "workspace/uav_diagsense/src/baselines")
sys.path.insert(0, "workspace/rearch/gsl_budgeted_declaration/src")
sys.path.insert(0, "workspace/rearch/gsl_budgeted_declaration")
sys.path.insert(0, "workspace/rearch/gsl_budgeted_declaration/FINAL_SUMMARY/08_v28_sparse_physics_moe")

from gadentools.Simulation import Simulation as GadenSim
from v28_modules.occupancy_utils import load_occupancy_2d
from grid_utils import build_candidate_grid
from common_runner import run_episode, parse_occ_meta, load_wind
from simple_planners import RandomPlanner

VGR = "workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House01"
occ_file = os.path.join(VGR, "OccupancyGrid3D.csv")
gp = os.path.join(VGR, "gas_simulations/2,4-1_fast/FilamentSimulation_gasType_10_sourcePosition_-0.40_-2.90_-0.30")

emin, emax = parse_occ_meta(occ_file)
occ_2d, _, occ_meta = load_occupancy_2d(occ_file, z_min=0.5, z_max=2.0, inflate_cells=1)
cell_size = occ_meta['cell_size']
wd = load_wind(os.path.join(VGR, "wind_simulations"), "2,4-1_fast")
grid, grid_ij, mask, grid_info = build_candidate_grid(emin, emax, 1.0, occ_2d, cell_size, free_only=True)

source = (-0.4, -2.9, -0.3)
starts = [(-5, -5), (-3, -3)]

for seed, (sx, sy) in enumerate(starts):
    print(f"Seed {seed}: creating sim...")
    sim = GadenSim(gp, occ_file)
    planner = RandomPlanner(grid, occ_2d, emin, cell_size)

    print(f"  Running episode (max_steps=20)...")
    try:
        metrics, _ = run_episode(
            sim, source, (sx, sy), emin, emax, wd, occ_2d, cell_size,
            grid, planner, seed=seed, max_steps=20, sensor_model="ideal")
        print(f"  OK: n_enc={metrics['n_encounters']}, err={metrics['censored_error_m']:.2f}m")
    except Exception as e:
        print(f"  FAIL: {e}")

    print(f"  Stopping sim...")
    sim.stopPlaying()
    time.sleep(0.5)
    del sim
    print(f"  Cleaned up.")
    time.sleep(0.5)

print("Done!")
