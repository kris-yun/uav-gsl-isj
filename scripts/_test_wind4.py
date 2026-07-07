import numpy as np

# Read the OccupancyGrid3D to understand the grid
occ = np.loadtxt("/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House01/OccupancyGrid3D.csv", delimiter=",", dtype=int)
print(f"Occupancy shape: {occ.shape}")
print(f"Total cells: {occ.size}")
print(f"Free cells: {np.sum(occ == 0)}")
print(f"Occupied cells: {np.sum(occ == 1)}")

# Check the wind file structure more carefully
import struct
path = "/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House01/wind_simulations/2,4-1_fast/2,4-1_fast_0.csv"
with open(path, 'rb') as f:
    header = f.read(100)
    print(f"\nFirst file header bytes: {header[:20].hex()}")
    print(f"First 4 bytes as int32: {struct.unpack('<i', header[:4])[0]}")
    print(f"First 4 bytes as float32: {struct.unpack('<f', header[:4])[0]}")
