"""Test different seed counts to find segfault threshold."""
import os, sys, json, subprocess

PYTHON = sys.executable
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BATCH_SCRIPT = os.path.join(PROJECT_ROOT, "workspace", "uav_diagsense", "scripts", "run_batch.py")
OUT_DIR = os.path.join(PROJECT_ROOT, "experiments", "official_baselines", "ablation")
os.makedirs(OUT_DIR, exist_ok=True)

STARTS_FILE = os.path.join(PROJECT_ROOT, "experiments", "official_baselines", "verified_starts.json")
with open(STARTS_FILE) as f:
    ALL_STARTS = json.load(f)

house = "House01"
info = ALL_STARTS[house]
source = ",".join(str(x) for x in info["source"])
starts_list = info["starts"]

for n in [2, 3, 4, 5, 6, 7, 8]:
    subset = starts_list[:n]
    starts_str = ";".join(f"{s[0]},{s[1]}" for s in subset)
    out_csv = os.path.join(OUT_DIR, f"debug_n{n}.csv")

    env = os.environ.copy()
    env["DQA_MEMP"] = "0"
    env["DQA_BPFM"] = "0"
    env["DQA_FDPOE"] = "0"

    cmd = [
        PYTHON, BATCH_SCRIPT,
        f"--house={house}",
        f"--config_id={info['config_id']}",
        f"--source={source}",
        f"--starts={starts_str}",
        "--methods", "DQA_AS_V2",
        "--max_steps=100",
        "--sensor", "ideal",
        f"--out={out_csv}",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=300)
    rc = result.returncode
    exists = os.path.exists(out_csv)
    print(f"n={n}: rc={rc} csv_exists={exists} stdout={result.stdout.strip()[:80]}")
    sys.stdout.flush()

    if rc != 0:
        print(f"  STDERR: {result.stderr[:200]}")
        break
