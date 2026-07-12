import os, shutil

exp_dir = "/tmp/cp_sbd_exp"
keep_dirs = ["eta_ablation"]
keep_files = ["pmfs_results.csv", "baselines_final.csv", "ablation_eprocess_v2.csv"]

moved = 0
for item in os.listdir(exp_dir):
    path = os.path.join(exp_dir, item)
    if os.path.isdir(path):
        if item not in keep_dirs:
            shutil.rmtree(path)
            print(f"Removed dir: {item}")
            moved += 1
    else:
        if item not in keep_files and item != "results.csv":
            os.remove(path)
            print(f"Removed file: {item}")
            moved += 1

print(f"\nTotal removed: {moved}")
print(f"\nRemaining:")
for item in sorted(os.listdir(exp_dir)):
    path = os.path.join(exp_dir, item)
    if os.path.isdir(path):
        print(f"  [DIR] {item}/")
    else:
        size = os.path.getsize(path)
        print(f"  {item} ({size} bytes)")
