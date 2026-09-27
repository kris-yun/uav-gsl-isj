"""Minimal result_contract stub for gsl_benchmark_runner.

Provides the utility functions needed by the benchmark runner.
"""
import hashlib
import json
import subprocess
import csv
import math
from pathlib import Path
from datetime import datetime


# Canonical method list
CANONICAL = {
    "B4_PMFS_official": {"algorithm": "PMFS", "type": "baseline", "use_sepf": 1},
    "B5_GrGSL_official": {"algorithm": "GrGSL", "type": "baseline", "use_sepf": 1},
    "B3_surge_cast_pf_official": {"algorithm": "SurgeCast", "type": "baseline", "use_sepf": 1},
    "M7_full_saisc_pf": {"algorithm": "OPGSL", "type": "proposed", "use_sepf": 1},
    "CTPI_CREL_TSDC_PIP": {"algorithm": "PMFS", "type": "proposed", "use_sepf": 0},
}


def git_commit_or_fail(repo_root="."):
    """Get current git commit hash, or 'unknown' if not a git repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root, capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "unknown"


def _position_xy(position):
    if isinstance(position, dict):
        return float(position["x"]), float(position["y"])
    return float(position[1]), float(position[2])


def _position_t(position):
    if isinstance(position, dict):
        return float(position.get("timestamp", position.get("t", 0.0)))
    return float(position[0])


def compute_path_length_xy(positions):
    """Compute total XY path length from a list of (t, x, y, z) tuples or dicts."""
    if len(positions) < 2:
        return 0.0
    total = 0.0
    prev_x, prev_y = _position_xy(positions[0])
    for i in range(1, len(positions)):
        x, y = _position_xy(positions[i])
        dx = x - prev_x
        dy = y - prev_y
        total += (dx*dx + dy*dy) ** 0.5
        prev_x, prev_y = x, y
    return total


def max_speed_xy(positions):
    """Compute max XY speed from a list of (t, x, y, z) tuples or dicts."""
    if len(positions) < 2:
        return 0.0
    max_spd = 0.0
    for i in range(1, len(positions)):
        dt = _position_t(positions[i]) - _position_t(positions[i-1])
        if dt <= 0:
            continue
        x, y = _position_xy(positions[i])
        px, py = _position_xy(positions[i-1])
        dx = x - px
        dy = y - py
        spd = (dx*dx + dy*dy) ** 0.5 / dt
        max_spd = max(max_spd, spd)
    return max_spd


def sha256_file(path):
    """Compute SHA256 hash of a file."""
    if isinstance(path, str):
        path = Path(path)
    if not path.exists():
        return "missing"
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_json(obj):
    """Compute SHA256 hash of a JSON-serializable object."""
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def make_run_record(**kwargs):
    """Create a run record dict, computing the derived localization/outcome
    fields the benchmark runner expects."""
    record = dict(kwargs)
    fx = float(kwargs.get("final_estimate_x", float("nan")))
    fy = float(kwargs.get("final_estimate_y", float("nan")))
    gx = float(kwargs.get("ground_truth_x", float("nan")))
    gy = float(kwargs.get("ground_truth_y", float("nan")))
    record["final_error_m"] = math.hypot(fx - gx, fy - gy)
    record["localized_success_2m"] = bool(record["final_error_m"] <= 2.0)
    record["timeout"] = (str(kwargs.get("termination_reason", "")) == "time_budget_timeout")
    return record


def write_record(path, record):
    """Write a run record to a CSV file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=record.keys())
        writer.writeheader()
        writer.writerow(record)
