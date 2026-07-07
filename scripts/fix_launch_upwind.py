#!/usr/bin/env python3
for path in [
    "/home/zyc/gsl_ws/src/vgr_bridge/launch/vgr_edpa.launch.py",
    "/home/zyc/gsl_ws/install/vgr_bridge/share/vgr_bridge/launch/vgr_edpa.launch.py"
]:
    with open(path, "r") as f:
        c = f.read()
    c = c.replace('"opgsl.modules.upwind_tracking": False', '"opgsl.modules.upwind_tracking": True')
    with open(path, "w") as f:
        f.write(c)
print("Enabled upwind_tracking in launch files")
