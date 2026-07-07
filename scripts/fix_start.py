#!/usr/bin/env python3
path = r"D:\ZYC\A-gas\src\vgr_edpa_launch.py"
with open(path, "r", encoding="utf-8") as f:
    c = f.read()

# Fix start position to be inside the environment (0,0)-(10,10)
c = c.replace('"start_x", default_value="-0.9"', '"start_x", default_value="1.0"')
c = c.replace('"start_y", default_value="0.15"', '"start_y", default_value="1.0"')

with open(path, "w", encoding="utf-8") as f:
    f.write(c)
print("Fixed start position to (1.0, 1.0)")
