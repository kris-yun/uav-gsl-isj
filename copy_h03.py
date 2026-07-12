import shutil, os
src = "/home/zyc/vgr_data_scenarios/House03/House03/gas_simulations"
dst = "/home/zyc/vgr_data_scenarios/House03/gas_simulations"
if os.path.isdir(src) and not os.path.isdir(dst):
    print(f"Copying {src} -> {dst} ...")
    shutil.copytree(src, dst)
    print("Done")
elif os.path.isdir(dst):
    print("Already exists")
else:
    print("Source not found")
