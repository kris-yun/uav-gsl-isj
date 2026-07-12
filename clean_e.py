# Clean bad entropy results, keep only header
with open("/tmp/cp_sbd_exp/eta_ablation/results_entropy.csv", "w") as f:
    f.write("method,house,seed,eta,dist,steps,elapsed,converge_type\n")
print("Cleaned results_entropy.csv")
