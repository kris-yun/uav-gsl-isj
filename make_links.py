import os
houses = ["House02","House03","House04","House05","House06","House07","House08","House09","House10","House11","House12","House13","House14","House15","House16","House17","House18","House19","House20"]
for h in houses:
    base = f"/home/zyc/vgr_data_scenarios/{h}"
    src = f"{base}/{h}/OccupancyGrid3D.csv"
    dst = f"{base}/OccupancyGrid3D.csv"
    if os.path.isfile(src) and not os.path.lexists(dst):
        os.symlink(src, dst)
        print(f"Linked: {h}")
    elif os.path.isfile(dst):
        print(f"Exists: {h}")
    else:
        print(f"No data: {h}")
