import shutil, os
base = "/home/zyc/vgr_data_scenarios/House03"
nested = f"{base}/House03"
for d in ["wind_simulations", "launch", "cad_models"]:
    src = f"{nested}/{d}"
    dst = f"{base}/{d}"
    if os.path.isdir(src) and not os.path.isdir(dst):
        shutil.copytree(src, dst)
        print(f"Copied: {d}")
    else:
        print(f"Skip: {d}")
