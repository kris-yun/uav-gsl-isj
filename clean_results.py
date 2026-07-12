# Clean results.csv: remove House02 entries (all NaN/bad) and duplicate seed=3
lines = open("/tmp/cp_sbd_exp/eta_ablation/results.csv").readlines()
header = lines[0]
data = lines[1:]
# Remove: any line with House02 (all bad due to missing file), and duplicates
seen = set()
clean = []
for line in data:
    parts = line.strip().split(",")
    key = (parts[0], parts[1], parts[2])  # method, house, seed
    if "House02" in line:
        continue  # skip all House02 (broken)
    if key in seen:
        continue  # skip duplicate
    seen.add(key)
    clean.append(line)
with open("/tmp/cp_sbd_exp/eta_ablation/results.csv", "w") as f:
    f.write(header)
    for line in clean:
        f.write(line)
print(f"Cleaned: {len(data)} -> {len(clean)} entries")
for line in clean:
    print(f"  {line.strip()}")
