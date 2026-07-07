filepath = "/home/zyc/gsl_ws/src/vgr_bridge/launch/vgr_ablation.launch.py"
with open(filepath) as f:
    content = f.read()

old = '"opgsl.event_driven.alpha_w": 0.5,'
new = '"opgsl.event_driven.alpha_w": 0.5,\n                "useWindGroundTruth": True,'
content = content.replace(old, new, 1)

with open(filepath, "w") as f:
    f.write(content)
print("Added useWindGroundTruth parameter")
