"""Iter11: DQA_AS_V2 vs baselines on GADEN VGR Houses - subprocess-isolated, parallel seeds."""
import sys, os, csv, time, subprocess, json, tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

SCENARIOS = [
    {"house": "House01", "config_id": "2,4-1_fast", "source": "-0.4,-2.9,-0.3"},
    {"house": "House02", "config_id": "3,5-1_fast", "source": "0,-1,0.2"},
    {"house": "House03", "config_id": "1-2,5_fast", "source": "-0.45,1.9,-0.1"},
]
STARTS = "0,-5;-3,-1;0,0;-1,2;-4,-3"
MAX_STEPS = 100
METHODS = ["Random", "GreedyMAP", "Infotaxis", "KLD", "DQA_AS", "DQA_AS_V2"]
WORKER = os.path.join(SCRIPT_DIR, "_iter11_worker.py")

WORKER_CODE = '''\
import sys, os, time, json, traceback
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
UAV_DIR = os.path.join(PROJECT_ROOT, "workspace", "uav_diagsense")
SRC_DIR = os.path.join(UAV_DIR, "src")
sys.path.insert(0, SRC_DIR)
sys.path.insert(0, os.path.join(SRC_DIR, "dqa_as"))
sys.path.insert(0, os.path.join(SRC_DIR, "baselines"))
sys.path.insert(0, os.path.join(SRC_DIR, "memp"))
sys.path.insert(0, os.path.join(SRC_DIR, "bpfm"))
sys.path.insert(0, os.path.join(SRC_DIR, "fdpoe"))
SHARED = os.path.join(PROJECT_ROOT, "workspace", "rearch", "gsl_budgeted_declaration")
sys.path.insert(0, os.path.join(SHARED, "src"))
sys.path.insert(0, SHARED)
sys.path.insert(0, os.path.join(SHARED, "FINAL_SUMMARY", "08_v28_sparse_physics_moe"))

from gadentools.Simulation import Simulation as GadenSim
from v28_modules.occupancy_utils import load_occupancy_2d
from grid_utils import build_candidate_grid
from common_runner import run_episode, parse_occ_meta, load_wind

from simple_planners import RandomPlanner, GreedyMAPPlanner, SurgeCastPlanner
from info_planners import InfotaxisPlanner, KLDWaypointPlanner
from dqa_as_planner import DQAASPlanner
from dqa_as_v2_planner import DQAASV2Planner

METHODS_MAP = {
    "Random": RandomPlanner, "GreedyMAP": GreedyMAPPlanner,
    "SurgeCast": SurgeCastPlanner, "Infotaxis": InfotaxisPlanner,
    "KLD": KLDWaypointPlanner, "DQA_AS": DQAASPlanner, "DQA_AS_V2": DQAASV2Planner,
}

method = sys.argv[1]
house = sys.argv[2]
config_id = sys.argv[3]
source = tuple(float(x) for x in sys.argv[4].split(","))
starts = [tuple(float(x) for x in s.split(",")) for s in sys.argv[5].split(";")]
max_steps = int(sys.argv[6])
out_json = sys.argv[7]
seed = int(sys.argv[8])
sx, sy = starts[seed]

VGR_BASE = os.path.join(PROJECT_ROOT, "workspace", "data", "VGR", "GADEN_files", "GADEN_files", "scenarios")
VGR = os.path.join(VGR_BASE, house)
occ_file = os.path.join(VGR, "OccupancyGrid3D.csv")
emin, emax = parse_occ_meta(occ_file)
occ_2d, _, occ_meta = load_occupancy_2d(occ_file, z_min=0.5, z_max=2.0, inflate_cells=1)
cell_size = occ_meta["cell_size"]

gd = os.path.join(VGR, "gas_simulations", config_id)
gp = [os.path.join(gd, d) for d in os.listdir(gd) if d.startswith("Filament")][0]
wd = load_wind(os.path.join(VGR, "wind_simulations"), config_id)
grid, grid_ij, mask, grid_info = build_candidate_grid(emin, emax, 1.0, occ_2d, cell_size, free_only=True)

PlannerClass = METHODS_MAP[method]
sim = GadenSim(gp, occ_file)
planner_fn = PlannerClass(grid, occ_2d, emin, cell_size)

try:
    metrics, step_log = run_episode(
        sim, source, (sx, sy), emin, emax, wd, occ_2d, cell_size,
        grid, planner_fn, seed=seed, max_steps=max_steps, sensor_model="ideal")
    metrics.update({"house": house, "config_id": config_id, "seed": seed,
                   "start_x": sx, "start_y": sy,
                   "source_x": source[0], "source_y": source[1],
                   "method": method, "sensor": "ideal"})
    with open(out_json, "w") as f:
        json.dump([metrics], f)
    print(f"OK", flush=True)
except Exception as e:
    traceback.print_exc()
    result = {"method": method, "house": house, "seed": seed,
              "declared": 0, "success_at_1m": 0, "success_at_2m": 0,
              "censored_error_m": float("inf"), "error": str(e)}
    with open(out_json, "w") as f:
        json.dump([result], f)
    print(f"FAIL: {e}", flush=True)
'''


def run_single(method, house, config_id, source, starts, max_steps, seed_idx, worker, max_retries=2):
    """Run one (method, seed) combination. Returns (metrics_dict, status_str). Retries on crash."""
    for attempt in range(max_retries + 1):
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, dir=os.path.join(PROJECT_ROOT, "automation", "results"))
        tmp_path = tmp.name
        tmp.close()

        cmd = [
            r"D:\Anaconda\python.exe", "-u", worker,
            method, house, config_id, source, starts,
            str(max_steps), tmp_path, str(seed_idx),
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            status = result.stdout.strip() if result.stdout else ""
            if result.returncode == 0 and os.path.exists(tmp_path):
                try:
                    with open(tmp_path) as f:
                        content = f.read().strip()
                    if content:
                        seed_data = json.loads(content)
                        os.unlink(tmp_path)
                        retry_tag = f" (retry {attempt})" if attempt > 0 else ""
                        return seed_data[0], status + retry_tag
                    else:
                        raise ValueError("empty file")
                except (json.JSONDecodeError, ValueError):
                    if attempt < max_retries:
                        os.unlink(tmp_path)
                        continue
                    os.unlink(tmp_path)
                    return {
                        "method": method, "house": house, "seed": seed_idx,
                        "declared": 0, "success_at_1m": 0, "success_at_2m": 0,
                        "censored_error_m": float('inf'), "error": "crash-no-data",
                    }, "CRASH"
            else:
                # Non-zero exit code (crash) - retry
                if attempt < max_retries:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                    continue
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                return {
                    "method": method, "house": house, "seed": seed_idx,
                    "declared": 0, "success_at_1m": 0, "success_at_2m": 0,
                    "censored_error_m": float('inf'),
                    "error": f"exit={result.returncode} after {max_retries+1} attempts",
                }, f"CRASH(exit={result.returncode})"
        except subprocess.TimeoutExpired:
            if attempt < max_retries:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                continue
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            return {
                "method": method, "house": house, "seed": seed_idx,
                "declared": 0, "success_at_1m": 0, "success_at_2m": 0,
                "censored_error_m": float('inf'), "error": "timeout",
            }, "TIMEOUT"

    # Should not reach here
    return {
        "method": method, "house": house, "seed": seed_idx,
        "declared": 0, "success_at_1m": 0, "success_at_2m": 0,
        "censored_error_m": float('inf'), "error": "unknown",
    }, "UNKNOWN"


def run_house(scenario, worker):
    """Run all methods × 5 seeds for a single house."""
    house = scenario["house"]
    config_id = scenario["config_id"]
    source = scenario["source"]
    out_csv = os.path.join(PROJECT_ROOT, "automation", "results", f"iter11_gaden_{house.lower()}.csv")

    print(f"\n{'='*60}")
    print(f"Running {house} (source={source}, config={config_id})")
    print(f"Output: {out_csv}")
    print(f"{'='*60}\n", flush=True)

    tasks = [(m, s) for m in METHODS for s in range(len(STARTS.split(";")))]
    all_results = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {}
        for method, seed_idx in tasks:
            fut = executor.submit(run_single, method, house, config_id, source, STARTS, MAX_STEPS, seed_idx, worker)
            futures[fut] = f"{method}_s{seed_idx}"

        done_count = 0
        for fut in as_completed(futures):
            done_count += 1
            key = futures[fut]
            try:
                metrics, status = fut.result()
                all_results.append(metrics)
                print(f"  [{done_count}/{len(tasks)}] {key}: {status}", flush=True)
            except Exception as e:
                print(f"  [{done_count}/{len(tasks)}] {key}: EXCEPTION {e}", flush=True)
                method, seed_s = key.rsplit("_s", 1)
                all_results.append({
                    "method": method, "house": house, "seed": int(seed_s),
                    "declared": 0, "success_at_1m": 0, "success_at_2m": 0,
                    "censored_error_m": float('inf'), "error": str(e),
                })

    all_results.sort(key=lambda r: (r["method"], r.get("seed", 0)))

    if all_results:
        keys = sorted(all_results[0].keys())
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            for r in all_results:
                w.writerow(r)

    print(f"\n{house} Summary ({len(all_results)} rows):")
    for method in METHODS:
        mr = [r for r in all_results if r["method"] == method]
        cens = [r["censored_error_m"] for r in mr if np.isfinite(r.get("censored_error_m", 9999))]
        mc = float(np.median(cens)) if cens else float('inf')
        nd = sum(r.get("declared", 0) for r in mr)
        s1 = sum(r.get("success_at_1m", 0) for r in mr)
        s2 = sum(r.get("success_at_2m", 0) for r in mr)
        print(f"  {method:12s}: d={nd}/5 S@1m={s1} S@2m={s2} med_err={mc:.2f}m", flush=True)

    print(f"\nSaved {len(all_results)} results to {out_csv}")
    return all_results


def main():
    with open(WORKER, "w", encoding="utf-8") as f:
        f.write(WORKER_CODE)

    t0 = time.time()
    all_house_results = {}

    for scenario in SCENARIOS:
        results = run_house(scenario, WORKER)
        all_house_results[scenario["house"]] = results

    elapsed = time.time() - t0
    print(f"\n{'='*60}")
    print(f"ALL HOUSES COMPLETE in {elapsed:.0f}s ({elapsed/60:.1f}min)")
    print(f"{'='*60}")

    if os.path.exists(WORKER):
        os.unlink(WORKER)


if __name__ == "__main__":
    main()
