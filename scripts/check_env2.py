#!/usr/bin/env python3
lines = open("/home/zyc/enva_vgr/OccupancyGrid3D.csv").readlines()
data_lines = []
for l in lines:
    l = l.strip()
    if l.startswith("#") or l == "":
        continue
    vals = l.split()
    try:
        data_lines.append([int(x) for x in vals])
    except:
        pass

print(f"Total data lines: {len(data_lines)}")
print(f"Expected: 100*100*30 = {100*100*30}")

z_idx = 3
grid = []
for i in range(100):
    idx = z_idx * 100 + i
    if idx < len(data_lines):
        grid.append(data_lines[idx])

print(f"Grid rows: {len(grid)}")

if len(grid) >= 100:
    print("Around start x=0-3, y=0-3:")
    for i in range(0, 30, 3):
        s = ""
        for j in range(0, 30, 3):
            if j < len(grid[i]):
                s += "." if grid[i][j]==0 else "#"
        print(f"  {i*0.1:.1f} {s}")

    print("Around source x=3-7, y=4-8:")
    for i in range(30, 80, 3):
        s = ""
        for j in range(40, 80, 3):
            if j < len(grid[i]):
                s += "." if grid[i][j]==0 else "#"
        print(f"  {i*0.1:.1f} {s}")
