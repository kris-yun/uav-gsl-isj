"""Iter11: Test GADEN getConcentration without playSimulation."""
import sys, os, json
sys.path.insert(0, "workspace/uav_diagsense/src")
sys.path.insert(0, "workspace/uav_diagsense/src/dqa_as")
sys.path.insert(0, "workspace/rearch/gsl_budgeted_declaration/src")
sys.path.insert(0, "workspace/rearch/gsl_budgeted_declaration")
sys.path.insert(0, "workspace/rearch/gsl_budgeted_declaration/FINAL_SUMMARY/08_v28_sparse_physics_moe")

from gadentools.Simulation import Simulation as GadenSim
from gadentools.Utils import Vector3 as GVec

gp = "workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House01/gas_simulations/2,4-1_fast/FilamentSimulation_gasType_10_sourcePosition_-0.40_-2.90_-0.30"
occ = "workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House01/OccupancyGrid3D.csv"

print("Creating sim...")
sim = GadenSim(gp, occ)
print(f"Source: {sim.source_position}")

# Test with iteration 100
print("Testing iteration 100...")
gvec = GVec(-0.4, -2.9, -0.3)
c = sim.getConcentration(100, gvec)
print(f"Concentration at source, iter=100: {c:.6f} ppm")

# Test a few more iterations
for it in [100, 150, 200, 500, 1000]:
    c = sim.getConcentration(it, gvec)
    print(f"  iter={it}: {c:.6f} ppm")

# Test at different positions
print("Position scan at iter=200:")
for dx in [-2, -1, 0, 1, 2]:
    for dy in [-2, -1, 0, 1, 2]:
        p = GVec(-0.4 + dx, -2.9 + dy, 0.3)
        c = sim.getConcentration(200, p)
        if c > 0.01:
            print(f"  ({-0.4+dx:.1f}, {-2.9+dy:.1f}): {c:.4f} ppm")

print("Done - no crash!")
