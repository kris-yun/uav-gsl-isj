import os, shutil

houses = ["House02","House03","House04","House05","House06","House07","House08","House09","House10","House11","House12","House13","House14","House15","House16","House17","House18","House19","House20"]
dirs_needed = ["gas_simulations", "wind_simulations", "launch", "cad_models"]

for h in houses:
    base = f"/home/zyc/vgr_data_scenarios/{h}"
    nested = f"{base}/{h}"
    if not os.path.isdir(nested):
        print(f"No nested dir: {h}")
        continue
    for d in dirs_needed:
        src = f"{nested}/{d}"
        dst = f"{base}/{d}"
        if os.path.isdir(src) and not os.path.isdir(dst):
            shutil.copytree(src, dst)
            print(f"Copied dir: {h}/{d}")
        elif os.path.isdir(dst):
            pass
        else:
            pass
print("Done")
