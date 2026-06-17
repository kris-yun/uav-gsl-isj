import os
d = "/tmp/uav_gsl_dqa/incremental"
for house in ["House02", "House03"]:
    for cond in ["baseline", "sdr"]:
        print(f"=== {house} {cond.upper()} ===")
        for s in range(5):
            f = os.path.join(d, f"{house}_{cond}_s{s}.csv")
            if os.path.exists(f):
                with open(f) as fh:
                    lines = fh.readlines()
                    last = lines[-1].strip() if lines else "EMPTY"
                    # Parse error (4th field)
                    parts = last.split()
                    err = parts[3] if len(parts) > 3 else "?"
                    status = "OK" if not last.startswith("FAILED") else "FAIL"
                    print(f"  s{s}: err={err}m [{status}]")
            else:
                print(f"  s{s}: MISSING")
