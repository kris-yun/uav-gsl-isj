c = open("/home/zyc/ros2_ws/src/vgr_bridge/launch/vgr_gsl_ablation_noWRANF.launch.py").read()
c = c.replace('"convergence_thr": 100', '"convergence_thr": 1.5')
open("/home/zyc/ros2_ws/src/vgr_bridge/launch/vgr_gsl_ablation_noWRANF.launch.py","w").write(c)
print("restored to 1.5")
