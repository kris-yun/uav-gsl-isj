import os
d = "/tmp/uav_gsl_dqa/incremental"
for cond in ["baseline", "sdr"]:
    print(f"=== {cond.upper()} ===")
    for s in range(10):
        f = os.path.join(d, f"House01_{cond}_s{s}.csv")
        if os.path.exists(f):
            with open(f) as fh:
                lines = fh.readlines()
                last = lines[-1].strip() if lines else "EMPTY"
                print(f"  s{s}: {last}")
        else:
            print(f"  s{s}: MISSING")
