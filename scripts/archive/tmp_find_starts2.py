import numpy as np

# House03 1-2,5_fast: source (-0.45, 1.90)
# House03 5-3_fast: source (8.20, 5.00)
# Need start positions 3-5m from source in free space

houses = [
    ("House03", "/home/zyc/vgr_data_scenarios/House03/House03",
     [(-0.45, 1.90), (8.20, 5.00)]),
]

for name, base, sources in houses:
    occ_file = base + "/OccupancyGrid3D.csv"
    with open(occ_file, 'r') as f:
        all_lines = f.readlines()
    
    env_min = np.array([-5.0, -5.0])
    env_max = np.array([5.0, 5.0])
    z_min = -1.0
    num_cells = np.array([100, 100, 20])
    cell_size = 0.1
    
    header_count = 0
    for line in all_lines:
        if line.startswith('#'):
            header_count += 1
            parts = line.strip().split()
            if 'env_min' in line:
                env_min = np.array([float(parts[1]), float(parts[2])])
                z_min = float(parts[3])
            elif 'env_max' in line:
                env_max = np.array([float(parts[1]), float(parts[2])])
            elif 'num_cells' in line:
                num_cells = np.array([int(parts[1]), int(parts[2]), int(parts[3])])
            elif 'cell_size' in line:
                cell_size = float(parts[1])
    
    nx, ny, nz = int(num_cells[0]), int(num_cells[1]), int(num_cells[2])
    grid_3d = np.zeros((nz, nx, ny), dtype=int)
    z = 0
    row_in_layer = 0
    for i in range(header_count, len(all_lines)):
        line = all_lines[i].strip()
        if not line or line.startswith('#') or line.startswith(';'):
            continue
        try:
            vals = [int(v) for v in line.split()]
        except ValueError:
            continue
        if len(vals) != ny:
            continue
        grid_3d[z, row_in_layer, :] = vals
        row_in_layer += 1
        if row_in_layer >= nx:
            row_in_layer = 0
            z += 1
            if z >= nz:
                break
    
    z_idx = int((0.3 - z_min) / cell_size)
    z_idx = max(0, min(nz-1, z_idx))
    layer = grid_3d[z_idx]
    
    for src in sources:
        free_cells = []
        for ix in range(nx):
            for iy in range(ny):
                if layer[ix, iy] == 0:
                    x = env_min[0] + (ix + 0.5) * cell_size
                    y = env_min[1] + (iy + 0.5) * cell_size
                    dist = np.sqrt((x - src[0])**2 + (y - src[1])**2)
                    if 3.0 < dist < 5.0:
                        free_cells.append((x, y, dist))
        
        if free_cells:
            free_cells.sort(key=lambda p: p[2])
            best = free_cells[0]
            print(name + " src=(" + str(src[0]) + "," + str(src[1]) + ") best_start=(" + str(round(best[0],2)) + "," + str(round(best[1],2)) + ") dist=" + str(round(best[2],2)))
        else:
            print(name + " src=(" + str(src[0]) + "," + str(src[1]) + ") NO free cells in 3-5m range")