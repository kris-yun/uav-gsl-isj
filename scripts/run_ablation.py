"""Ablation experiment framework for DQA-AS V2.

Tests each innovation module individually and in combination:
- DQA_AS (baseline)
- DQA_AS + MEMP only
- DQA_AS + BPFM only  
- DQA_AS + FDPOE only
- DQA_AS + MEMP + BPFM (no FDPOE)
- DQA_AS + MEMP + FDPOE (no BPFM)
- DQA_AS + BPFM + FDPOE (no MEMP)
- DQA_AS + MEMP + BPFM + FDPOE (full V2)

Also tests blend_alpha sensitivity:
- alpha in {0, 0.25, 0.5, 0.75, 1.0}
- posterior = alpha * MEMP + (1-alpha) * BPFM
"""
import os, sys, json, csv, subprocess, time

PYTHON = sys.executable
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BATCH_SCRIPT = os.path.join(PROJECT_ROOT, "workspace", "uav_diagsense", "scripts", "run_batch.py")
OUT_DIR = os.path.join(PROJECT_ROOT, "experiments", "official_baselines", "ablation")
os.makedirs(OUT_DIR, exist_ok=True)

# Log file for debugging
LOG_FILE = os.path.join(OUT_DIR, "ablation_run.log")
log_fh = open(LOG_FILE, "w", encoding="utf-8")
def log(msg):
    print(msg, flush=True)
    log_fh.write(msg + "\n")
    log_fh.flush()

# Load verified starts
STARTS_FILE = os.path.join(PROJECT_ROOT, "experiments", "official_baselines", "verified_starts.json")
with open(STARTS_FILE) as f:
    ALL_STARTS = json.load(f)

# Ablation configurations
ABLATIONS = {
    "DQA_AS":           {"memp": False, "bpfm": False, "fdpoe": False},
    "DQA_AS+MEMP":      {"memp": True,  "bpfm": False, "fdpoe": False},
    "DQA_AS+BPFM":      {"memp": False, "bpfm": True,  "fdpoe": False},
    "DQA_AS+FDPOE":     {"memp": False, "bpfm": False, "fdpoe": True},
    "DQA_AS+MEMP+BPFM": {"memp": True,  "bpfm": True,  "fdpoe": False},
    "DQA_AS+MEMP+FDPOE":{"memp": True,  "bpfm": False, "fdpoe": True},
    "DQA_AS+BPFM+FDPOE":{"memp": False, "bpfm": True,  "fdpoe": True},
    "DQA_AS_V2":        {"memp": True,  "bpfm": True,  "fdpoe": True},
}

# Blend alpha values
ALPHA_VALUES = [0.0, 0.25, 0.5, 0.75, 1.0]


def run_ablation(house, config_id, source, starts_str, ablation_name, ablation_config, max_steps=100):
    """Run one ablation configuration."""
    out_csv = os.path.join(OUT_DIR, f"ablation_{house}_{ablation_name}.csv")

    # Set environment variables for ablation flags
    env = os.environ.copy()
    env["DQA_MEMP"] = "1" if ablation_config["memp"] else "0"
    env["DQA_BPFM"] = "1" if ablation_config["bpfm"] else "0"
    env["DQA_FDPOE"] = "1" if ablation_config["fdpoe"] else "0"

    cmd = [
        PYTHON, BATCH_SCRIPT,
        f"--house={house}",
        f"--config_id={config_id}",
        f"--source={source}",
        f"--starts={starts_str}",
        "--methods", "DQA_AS_V2",
        f"--max_steps={max_steps}",
        "--sensor", "ideal",
        f"--out={out_csv}",
    ]

    log(f"  Running {ablation_name} on {house}...")
    t0 = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=900)
        elapsed = time.time() - t0

        if result.returncode != 0:
            log(f"    FAILED (rc={result.returncode}): {result.stderr[:300]}")
            log(f"    STDOUT: {result.stdout[:300]}")
            return None

        log(f"    Done in {elapsed:.0f}s: {result.stdout.strip()[:100]}")
        return out_csv
    except subprocess.TimeoutExpired:
        elapsed = time.time() - t0
        log(f"    TIMEOUT after {elapsed:.0f}s")
        return None


def run_alpha_sweep(house, config_id, source, starts_str, alpha, max_steps=100):
    """Run one blend_alpha value."""
    out_csv = os.path.join(OUT_DIR, f"alpha_{house}_a{alpha:.2f}.csv")

    env = os.environ.copy()
    env["DQA_MEMP"] = "1"
    env["DQA_BPFM"] = "1"
    env["DQA_FDPOE"] = "1"
    env["DQA_BLEND_ALPHA"] = str(alpha)

    cmd = [
        PYTHON, BATCH_SCRIPT,
        f"--house={house}",
        f"--config_id={config_id}",
        f"--source={source}",
        f"--starts={starts_str}",
        "--methods", "DQA_AS_V2",
        f"--max_steps={max_steps}",
        "--sensor", "ideal",
        f"--out={out_csv}",
    ]

    log(f"  alpha={alpha:.2f} on {house}...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=900)

        if result.returncode != 0:
            log(f"    FAILED (rc={result.returncode}): {result.stderr[:300]}")
            return None
        log(f"    Done: {result.stdout.strip()[:100]}")
        return out_csv
    except subprocess.TimeoutExpired:
        log(f"    TIMEOUT")
        return None


if __name__ == "__main__":
    log("=" * 60)
    log("ABLATION EXPERIMENT - ALL 3 HOUSES")
    log("=" * 60)

    HOUSES = ["House01", "House02", "House03"]
    all_results = {}
    all_alpha_results = {}

    for house in HOUSES:
        log(f"\n{'=' * 60}")
        log(f"HOUSE: {house}")
        log(f"{'=' * 60}")

        info = ALL_STARTS[house]
        source = ",".join(str(x) for x in info["source"])
        starts_list = info["starts"]  # Use all 8 seeds
        starts_str = ";".join(f"{s[0]},{s[1]}" for s in starts_list)

        log(f"  source={source}  n_starts={len(starts_list)}")

        # Ablation for this house
        house_results = {}
        for name, config in ABLATIONS.items():
            csv_path = run_ablation(house, info["config_id"], source, starts_str, name, config)
            house_results[name] = csv_path

        all_results[house] = house_results

        # Alpha sweep for House01 and House02 only
        if house in ("House01", "House02"):
            log(f"\n  --- Alpha sensitivity for {house} ---")
            house_alpha = {}
            for alpha in ALPHA_VALUES:
                csv_path = run_alpha_sweep(house, info["config_id"], source, starts_str, alpha)
                house_alpha[alpha] = csv_path
            all_alpha_results[house] = house_alpha

    # Save summary
    summary = {
        "ablation": all_results,
        "alpha_sweep": all_alpha_results,
    }
    with open(os.path.join(OUT_DIR, "ablation_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    log("\nDone! Results in: " + OUT_DIR)
    log_fh.close()
