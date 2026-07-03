import csv, os

base = "D:/ZYC/A-gas/HANDOFF/results"

for method in ["PMFS", "GrGSL", "surge_cast"]:
    for s in [0, 1]:
        f = f"{base}/House01_{method}_s{s}.csv"
        if os.path.exists(f):
            with open(f) as fh:
                content = fh.read()
            # Parse manually - get min_distance_to_source
            reader = csv.DictReader(content.strip().split('\n'))
            for row in reader:
                md = row.get("min_distance_to_source", "?")
                success = row.get("action_success", "?")
                timed = row.get("timed_out", "?")
                elapsed = row.get("elapsed_sec", "?")
                print(f"{method} s{s}: min_dist={md} success={success} timed_out={timed} elapsed={elapsed}")
                break
