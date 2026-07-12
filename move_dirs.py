import os
dirs_needed = ["gas_simulations", "wind_simulations", "launch", "cad_models"]
moved = 0
for i in range(1, 21):
    h = f"House{i:02d}"
    base = f"/home/zyc/vgr_data_scenarios/{h}"
    nested = f"{base}/{h}"
    if not os.path.isdir(nested):
        continue
    for d in dirs_needed:
        src = f"{nested}/{d}"
        dst = f"{base}/{d}"
        if os.path.isdir(src) and not os.path.isdir(dst):
            os.rename(src, dst)
            print(f"Moved: {h}/{d}")
            moved += 1
        elif os.path.isdir(dst):
            pass
        else:
            pass
print(f"Total moved: {moved}")
