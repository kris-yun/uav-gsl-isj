import re
path = "/home/zyc/ros2_ws/src/vgr_bridge/launch/vgr_gsl_ablation_noWRANF.launch.py"
with open(path) as f:
    c = f.read()
# Change convergence_thr from 1.5 to 100
c = c.replace('"convergence_thr": 1.5', '"convergence_thr": 100')
with open(path, 'w') as f:
    f.write(c)
print("OK: convergence_thr -> 100")
