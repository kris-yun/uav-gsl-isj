import os, shutil
houses = ["House02","House03","House04","House05","House06","House07","House08","House09","House10","House11","House12","House13","House14","House15","House16","House17","House18","House19","House20"]
needed = ["OccupancyGrid3D.csv", "occupancy.pgm", "occupancy.yaml"]
for h in houses:
    base = f"/home/zyc/vgr_data_scenarios/{h}"
    src_dir = f"{base}/{h}"
    for f in needed:
        src = f"{src_dir}/{f}"
        dst = f"{base}/{f}"
        if os.path.isfile(src) and not os.path.isfile(dst):
            shutil.copy2(src, dst)
            print(f"Copied: {h}/{f}")
        elif os.path.isfile(dst):
            pass
        else:
            print(f"Missing: {h}/{f}")
print("Done")
