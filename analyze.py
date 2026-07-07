import csv, statistics

ed, bl = [], []
with open("/tmp/edbayes_exp/results.csv") as f:
    for row in csv.DictReader(f):
        try:
            err = float(row["final_error"])
        except:
            continue
        if row["method"] == "ED_Bayes": ed.append(err)
        elif row["method"] == "Baseline": bl.append(err)

print("ED-Bayes:", [round(x,3) for x in ed])
print(f"  Mean: {statistics.mean(ed):.3f}")
print(f"  Median: {statistics.median(ed):.3f}")
print(f"  Std: {statistics.stdev(ed):.3f}")
print(f"  Success@2m: {sum(1 for x in ed if x < 2.0)}/{len(ed)}")
print()
print("Baseline:", [round(x,3) for x in bl])
print(f"  Mean: {statistics.mean(bl):.3f}")
print(f"  Median: {statistics.median(bl):.3f}")
print(f"  Std: {statistics.stdev(bl):.3f}")
print(f"  Success@2m: {sum(1 for x in bl if x < 2.0)}/{len(bl)}")
