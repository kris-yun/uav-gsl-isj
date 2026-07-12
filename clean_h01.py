lines = open("/tmp/cp_sbd_exp/eta_ablation/results.csv").readlines()
header = lines[0]
clean = [l for l in lines[1:] if "House01" in l]
seen = set()
deduped = []
for l in clean:
    parts = l.strip().split(",")
    key = (parts[0], parts[1], parts[2])
    if key not in seen:
        seen.add(key)
        deduped.append(l)
with open("/tmp/cp_sbd_exp/eta_ablation/results.csv", "w") as f:
    f.write(header)
    for l in deduped:
        f.write(l)
print(f"Kept {len(deduped)} clean entries")
for l in deduped:
    print(f"  {l.strip()}")
