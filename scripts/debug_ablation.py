"""Debug single ablation run."""
import os, sys, json, subprocess, time

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
starts_str = ";".join(f"{s[0]},{s[1]}" for s in starts_list)
out_csv = os.path.join(OUT_DIR, "ablation_House01_DQA_AS.csv")

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

print("CMD:", cmd)
print("starts_str:", starts_str[:200])
print()
t0 = time.time()
result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=900)
elapsed = time.time() - t0
print(f"Return code: {result.returncode}")
print(f"Elapsed: {elapsed:.0f}s")
print(f"STDOUT:\n{result.stdout[:500]}")
print(f"STDERR:\n{result.stderr[:500]}")
print(f"CSV exists: {os.path.exists(out_csv)}")
