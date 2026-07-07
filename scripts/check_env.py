#!/usr/bin/env python3
lines = open("/home/zyc/enva_vgr/OccupancyGrid3D.csv").readlines()
data_lines = [l for l in lines if not l.startswith("#")]
z_idx = 3
grid = []
for i in range(100):
    row = data_lines[z_idx*100+i].strip().split()
    grid.append([int(x) for x in row])

# Print area around start and source
print("Around start x=0-3, y=0-3:")
for i in range(0, 30, 2):
    s = ""
    for j in range(0, 30, 2):
        s += "." if grid[i][j]==0 else "#"
    print(f"  {i*0.1:.1f} {s}")

print("Around source x=3-7, y=4-8:")
for i in range(30, 80, 2):
    s = ""
    for j in range(40, 80, 2):
        s += "." if grid[i][j]==0 else "#"
    print(f"  {i*0.1:.1f} {s}")

# Check wall at x=1.5
print("Wall at x=1.5:")
for j in range(0, 100, 5):
    print(f"  y={j*0.1:.1f}: grid[15][{j}]={grid[15][j]}")
