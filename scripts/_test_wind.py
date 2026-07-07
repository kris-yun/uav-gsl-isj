import numpy as np
d = np.fromfile("/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House01/wind_simulations/2,4-1_fast/2,4-1_fast_0.csv_U", dtype=np.float64)
print(f"shape={d.shape}, min={d.min():.6f}, max={d.max():.6f}, mean={d.mean():.6f}")
print(f"first 10 values: {d[:10]}")
