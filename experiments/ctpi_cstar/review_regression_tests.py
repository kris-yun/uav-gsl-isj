from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]


def load_performance_module():
    path = REPO / "tools" / "cstar_seed12_crosshouse_performance.py"
    spec = importlib.util.spec_from_file_location("cstar_perf", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("CSTAR_REVIEW_TEST_IMPORT_PERFORMANCE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_auc_rejects_late_single_estimate() -> None:
    perf = load_performance_module()
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "source_estimate_trace.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(
                f,
                fieldnames=["sim_time", "estimate_available", "estimate_x", "estimate_y"],
            )
            w.writeheader()
            # H02 true source, but only at t=239. The reviewed evaluator used to
            # back-fill this point and report 240 s AUC=0. It must now fail.
            w.writerow({
                "sim_time": "239", "estimate_available": "true",
                "estimate_x": "0", "estimate_y": "-1",
            })
        try:
            perf.metrics(path, "H02")
        except RuntimeError as exc:
            if "MISSING_T0_ESTIMATE" not in str(exc):
                raise
        else:
            raise AssertionError("CSTAR_REVIEW_AUC_LATE_SINGLE_POINT_NOT_REJECTED")


def test_auc_uses_forward_hold_not_future_interpolation() -> None:
    perf = load_performance_module()
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "source_estimate_trace.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(
                f,
                fieldnames=["sim_time", "estimate_available", "estimate_x", "estimate_y"],
            )
            w.writeheader()
            # H02 source=(0,-1). Error is 10 m until exactly 240 s, then 0.
            # Causal zero-order hold must give 10*240=2400, not a trapezoid that
            # leaks the future correct estimate backward.
            w.writerow({
                "sim_time": "0", "estimate_available": "true",
                "estimate_x": "10", "estimate_y": "-1",
            })
            w.writerow({
                "sim_time": "240", "estimate_available": "true",
                "estimate_x": "0", "estimate_y": "-1",
            })
        result = perf.metrics(path, "H02")
        if abs(result["error_auc_m_s"] - 2400.0) > 1e-9:
            raise AssertionError(f"CSTAR_REVIEW_AUC_NOT_FORWARD_HOLD:{result}")


def test_authorizer_rejects_contract_pass_only_fixtures() -> None:
    contracts = {
        "m1": "CSTAR_M1_CONTROLLED_CAUSAL_GATE_V1",
        "m2": "CSTAR_M2_SOURCE_DIVERSE_PREDICTIVE_GATE_V1",
        "m3": "CSTAR_M3_COUNTERFACTUAL_GATE_V1",
        "models": "CSTAR_FROZEN_MODEL_MANIFEST_V1",
        "production": "CSTAR_PRODUCTION_MODE_MANIFEST_V1",
        "smoke": "CSTAR_RUNTIME_SMOKE_V1",
    }
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        paths = {}
        for label, contract in contracts.items():
            p = td / f"{label}.json"
            p.write_text(json.dumps({"contract": contract, "pass": True}) + "\n", encoding="utf-8")
            paths[label] = p
        out = td / "authorization.json"
        cmd = [
            sys.executable, str(ROOT / "authorize_closed_loop.py"),
            "--m1", str(paths["m1"]),
            "--m2", str(paths["m2"]),
            "--m3", str(paths["m3"]),
            "--models", str(paths["models"]),
            "--production", str(paths["production"]),
            "--smoke", str(paths["smoke"]),
            "--repo-root", str(REPO),
            "--output", str(out),
        ]
        proc = subprocess.run(cmd, text=True, capture_output=True)
        if proc.returncode == 0:
            raise AssertionError(
                "CSTAR_REVIEW_AUTHORIZER_ACCEPTED_CONTRACT_PASS_ONLY_FIXTURES\n"
                + proc.stdout + proc.stderr
            )
        if out.exists():
            raise AssertionError("CSTAR_REVIEW_AUTHORIZER_WROTE_PASS_ARTIFACT_ON_FAILURE")


def main() -> None:
    test_auc_rejects_late_single_estimate()
    test_auc_uses_forward_hold_not_future_interpolation()
    test_authorizer_rejects_contract_pass_only_fixtures()
    print("CSTAR_REVIEW_REGRESSION_TESTS PASS")


if __name__ == "__main__":
    main()
