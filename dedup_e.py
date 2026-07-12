lines = open("/tmp/cp_sbd_exp/eta_ablation/results_entropy.csv").readlines()
header = lines[0]
data = lines[1:]
seen = set()
deduped = []
for l in data:
    parts = l.strip().split(",")
    key = (parts[0], parts[1], parts[2])
    if key not in seen:
        seen.add(key)
        deduped.append(l)
with open("/tmp/cp_sbd_exp/eta_ablation/results_entropy.csv", "w") as f:
    f.write(header)
    for l in deduped:
        f.write(l)
print(f"Deduped: {len(data)} -> {len(deduped)}")
