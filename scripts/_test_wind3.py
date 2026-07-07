import numpy as np
path = "/mnt/hgfs/workspace/data/VGR/GADEN_files/GADEN_files/scenarios/House01/wind_simulations/2,4-1_fast/2,4-1_fast_0.csv_U"
d = np.fromfile(path, dtype=np.float64)
nz = np.nonzero(d)[0]
if len(nz) > 0:
    print(f"First non-zero at index {nz[0]}: {d[nz[0]]}")
    print(f"Non-zero count: {len(nz)} out of {len(d)}")
    print(f"Sample non-zero values: {d[nz[:10]]}")
    total = len(d)
    print(f"Total elements: {total}")
    cube = round(total ** (1/3))
    print(f"Cube root: {cube}")
    print(f"Grid: {cube}x{cube}x{cube} = {cube**3}")
    # Check last non-zero
    print(f"Last non-zero at index {nz[-1]}: {d[nz[-1]]}")
else:
    print("All zeros!")
