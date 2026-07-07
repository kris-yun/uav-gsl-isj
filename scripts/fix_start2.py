#!/usr/bin/env python3
path = r"D:\ZYC\A-gas\src\vgr_edpa_launch.py"
with open(path, "r", encoding="utf-8") as f:
    c = f.read()

# Change start to (4.0, 4.0) which is in the same room as the source
c = c.replace('"start_x", default_value="1.0"', '"start_x", default_value="4.0"')
c = c.replace('"start_y", default_value="1.0"', '"start_y", default_value="4.0"')

with open(path, "w", encoding="utf-8") as f:
    f.write(c)
print("Start position changed to (4.0, 4.0)")
