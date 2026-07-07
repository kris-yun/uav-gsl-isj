with open('/home/zyc/ros2_ws/src/vgr_bridge/launch/vgr_gsl_wranf.launch.py','r') as f:
    content = f.read()
oracle = content.replace('"useWindGroundTruth": False', '"useWindGroundTruth": True')
oracle = oracle.replace('"use_wranf_supervisor": True', '"use_wranf_supervisor": False')
with open('/home/zyc/ros2_ws/src/vgr_bridge/launch/vgr_gsl_oracle.launch.py','w') as f:
    f.write(oracle)
print('DONE')
