import numpy as np
import os

path = "/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House01/wind_simulations/2,4-1_fast/2,4-1_fast_0.csv_U"
fsize = os.path.getsize(path)
print(f"File size: {fsize} bytes")
print(f"float64 count: {fsize // 8}")
print(f"float32 count: {fsize // 4}")

# Try float32
d32 = np.fromfile(path, dtype=np.float32)
print(f"\nfloat32: shape={d32.shape}, min={d32.min():.6f}, max={d32.max():.6f}")
print(f"first 10: {d32[:10]}")
print(f"non-zero count: {np.count_nonzero(d32)}")

# Try skipping first 4 bytes (header)
d32_skip = np.fromfile(path, dtype=np.float32, offset=4)
print(f"\nfloat32 skip4: shape={d32_skip.shape}")
print(f"first 10: {d32_skip[:10]}")
