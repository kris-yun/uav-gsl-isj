#!/usr/bin/env python3
"""Frozen five-arm V2 active interface audit, not an efficacy experiment.

Run from this repository with the installed neural dependencies. Parameters
and arms are intentionally fixed. A nonempty output directory is never
overwritten, and the first failure/timeout stops the run with its logs intact.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = ROOT / "artifacts/v2/engineering_matrix/projected_evidence/model"
DEFAULT_OUT = ROOT / "runs/v2_active_controls_01"
DEFAULT_REFERENCE = ROOT / "artifacts/v2/active_demo/receipt.json"
ARMS = (
    ("m2_Aprime__m3_Aprime", "Aprime", "Aprime"),
    ("m2_B__m3_Aprime", "B", "Aprime"),
    ("m2_Bprime__m3_Aprime", "Bprime", "Aprime"),
    ("m2_Aprime__m3_Bprime", "Aprime", "Bprime"),
    ("m2_Bprime__m3_B_cluster", "Bprime", "B"),
)
PER_COMMAND_TIMEOUT = 175
OVERALL_GUARD_SECONDS = 600
SCOPE = "MANUFACTURED_BACKEND_ENGINEERING_ABLATION_ONLY_NOT_ACTIVE_GAIN"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def path_key(path):
    """Hash identities are relative inside the repo, absolute outside it."""
    path = Path(path).resolve()
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                    allow_nan=False), encoding="utf-8")
    temporary.replace(path)


def build_parser():
    parser = argparse.ArgumentParser(
        description="Run five frozen engineering controls; seed=42, rounds=3, draws=512, eig-draws=16.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL,
                        help="Complete engineering student checkpoint, inside or outside this repository")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT,
                        help="New or empty output directory; existing evidence is never overwritten")
    parser.add_argument("--reference-receipt", type=Path, default=DEFAULT_REFERENCE,
                        help="Read-only existing full Bprime+Bprime receipt; never rerun or overwrite it")
    return parser


def main(argv=None):
    # Argparse handles --help before paths are read or any directory is made.
    args = build_parser().parse_args(argv)
    MODEL = args.model.expanduser().resolve()
    OUT = args.out.expanduser().resolve()
    REFERENCE = args.reference_receipt.expanduser().resolve()
    if OUT.exists() and any(OUT.iterdir()):
        raise SystemExit("Refuse to overwrite nonempty active_controls evidence")
    model_metadata = json.loads((MODEL / "model.json").read_text())
    if (model_metadata.get("format") != "gsl_neural_joint_v2"
            or model_metadata["config"].get("scope") != "ENGINEERING_ONLY"
            or model_metadata["receipt"].get("status") != "COMPLETE"):
        raise SystemExit("Frozen complete engineering student is required")
    if digest(MODEL / "weights.pt") != model_metadata["weights_sha256"]:
        raise SystemExit("Frozen student weights checksum mismatch")
    reference = json.loads(REFERENCE.read_text()) if REFERENCE.exists() else None
    expected_seconds = (5 * float(reference["wall_seconds"]) + 30) if reference else None
    if expected_seconds is not None and expected_seconds > OVERALL_GUARD_SECONDS:
        raise SystemExit("Estimated audit exceeds ten minutes; report before starting")

    tracked = [
        Path(__file__).resolve(), MODEL / "model.json", MODEL / "weights.pt",
        *[ROOT / relative for relative in (
            "src/gsl_recovery/v2_cli.py", "src/gsl_recovery/v2_pipeline.py",
            "src/gsl_recovery/navigation/v2_session.py",
            "src/gsl_recovery/m1_neural/model.py",
            "src/gsl_recovery/m2_replay/engine.py",
            "src/gsl_recovery/m3_codebook/codebook.py",
            "src/gsl_recovery/m3_planner/planner.py",
            "src/gsl_recovery/m3_planner/diagnostics.py",
            "src/gsl_recovery/m3_planner/joint_eig.py",
        )],
    ]
    frozen_hashes = {path_key(p): digest(p) for p in tracked}
    env = dict(os.environ)
    env["OMP_NUM_THREADS"] = "1"
    env["OPENBLAS_NUM_THREADS"] = "1"
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    commands = []
    for arm, m2, m3 in ARMS:
        commands.append({
            "arm": arm, "m2": m2, "m3": m3,
            "argv": [sys.executable, "-m", "gsl_recovery.v2_cli", "demo",
                     "--model", str(MODEL), "--out", str(OUT / arm / "demo"),
                     "--rounds", "3", "--draws", "512", "--eig-draws", "16",
                     "--seed", "42", "--m2", m2, "--variant", m3],
        })
    OUT.mkdir(parents=True, exist_ok=True)
    protocol = {
        "format": "gsl_v2_active_controls_frozen_v1",
        "scope": SCOPE, "frozen_utc_before_first_command": utc_now(),
        "model_version": model_metadata["version"], "source_hashes": frozen_hashes,
        "hash_path_convention": "repository-relative inside ROOT; absolute outside ROOT",
        "seed": 42, "rounds": 3, "draws": 512, "eig_draws": 16,
        "per_command_timeout_seconds": PER_COMMAND_TIMEOUT,
        "overall_guard_seconds": OVERALL_GUARD_SECONDS,
        "estimated_wall_seconds_from_existing_full_arm": expected_seconds,
        "commands": commands,
        "environment": {k: env[k] for k in ("PYTHONPATH", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS")},
        "reference_only_not_a_new_arm": {
            "path": path_key(REFERENCE),
            "sha256": digest(REFERENCE) if REFERENCE.exists() else None,
            "receipt": reference,
            "policy": "Never overwrite or rerun the separately completed full Bprime+Bprime arm",
        },
        "decision_policy": "Fixed order, fixed model, fixed parameters; stop on first failure; no tuning or added tests",
        "not_a_multi_world_efficacy_experiment": True,
    }
    write_json(OUT / "PROTOCOL_FROZEN.json", protocol)
    protocol_sha = digest(OUT / "PROTOCOL_FROZEN.json")
    started = time.perf_counter()
    rows = []
    status = "RUNNING"

    def snapshot():
        summary = {
            "scope": SCOPE, "status": status, "protocol_sha256": protocol_sha,
            "completed_arms": len(rows), "planned_arms": len(commands),
            "wall_seconds": time.perf_counter() - started,
            "rows": rows, "active_gain_claimed": False,
        }
        write_json(OUT / "SUMMARY.json", summary)
        lines = ["# V2 主动消融接口执行收据", "", f"状态：{status}", "",
                 "固定单个制造环境、固定学生与种子；仅检查各独立控制是否真实进入闭环。不能据此主张主动定位增益。", "",
                 "| 控制 | 进程退出码 | 超时 | 观测数 | 反证检验数 | full-EIG fallback | MAP误差（仅本例） |", "|---|---:|---|---:|---:|---:|---:|"]
        for row in rows:
            receipt = row.get("receipt") or {}
            metric = receipt.get("evaluation_only", {})
            lines.append(f"| {row['arm']} | {row.get('exit_code')} | {row.get('timed_out', False)} | "
                         f"{receipt.get('observations', 'NA')} | {receipt.get('counterevidence_tests', 'NA')} | "
                         f"{receipt.get('full_joint_eig_fallbacks', 'NA')} | {metric.get('map_error_m', 'NA')} |")
        reference_note = (f"完整 Bprime+Bprime 参考仅从 {path_key(REFERENCE)} 读取，本脚本未覆盖或重跑。"
                          if reference else "未找到参考回执；本脚本没有新运行完整 Bprime+Bprime 组。")
        lines.extend(["", reference_note,
                      "各组的 argv、stdout、stderr、实际退出码、时间和原 CLI 收据均保留；所有方法差异仍只代表本例工程行为。", ""])
        (OUT / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")

    snapshot()
    for command in commands:
        if time.perf_counter() - started + PER_COMMAND_TIMEOUT > OVERALL_GUARD_SECONDS:
            status = "STOP_OVERALL_GUARD_BEFORE_NEW_ARM"
            break
        if any(digest(ROOT / p) != sha for p, sha in frozen_hashes.items()):
            status = "STOP_CODE_OR_MODEL_IDENTITY_CHANGED"
            break
        arm_dir = OUT / command["arm"]
        arm_dir.mkdir()
        write_json(arm_dir / "command.json", command)
        row = {"arm": command["arm"], "m2": command["m2"], "m3": command["m3"],
               "started_utc": utc_now(), "argv": command["argv"], "timed_out": False}
        arm_started = time.perf_counter()
        with (arm_dir / "stdout.txt").open("x", encoding="utf-8") as stdout, \
             (arm_dir / "stderr.txt").open("x", encoding="utf-8") as stderr:
            process = subprocess.Popen(command["argv"], cwd=ROOT, env=env, stdout=stdout, stderr=stderr)
            try:
                row["exit_code"] = process.wait(timeout=PER_COMMAND_TIMEOUT)
            except subprocess.TimeoutExpired:
                process.kill()
                row["exit_code"] = process.wait()
                row["timed_out"] = True
        row.update(finished_utc=utc_now(), wall_seconds=time.perf_counter() - arm_started)
        row["stdout_sha256"] = digest(arm_dir / "stdout.txt")
        row["stderr_sha256"] = digest(arm_dir / "stderr.txt")
        receipt_path = arm_dir / "demo/receipt.json"
        row["receipt"] = json.loads(receipt_path.read_text()) if receipt_path.exists() else None
        receipt = row["receipt"] or {}
        valid = (row["exit_code"] == 0 and not row["timed_out"]
                 and receipt.get("status") == "PASS_NEURAL_M1_M2_M3_CLOSED_LOOP"
                 and receipt.get("model_version") == model_metadata["version"]
                 and receipt.get("m2_variant") == command["m2"]
                 and receipt.get("m3_variant") == command["m3"]
                 and receipt.get("observations") == 9 and receipt.get("rounds") == 3
                 and receipt.get("teacher_or_hidden_state_in_online_input") is False)
        if any(digest(ROOT / p) != sha for p, sha in frozen_hashes.items()):
            valid = False
            row["identity_error"] = "Code or model changed during the command"
        row["status"] = "PASS_ENGINEERING_INTERFACE" if valid else "FAIL_OR_TIMEOUT"
        write_json(arm_dir / "execution.json", row)
        rows.append(row)
        print(json.dumps({"arm": row["arm"], "status": row["status"],
                          "exit_code": row["exit_code"], "wall_seconds": row["wall_seconds"]}), flush=True)
        if not valid:
            status = "STOP_ON_FIRST_FAILED_ARM"
            break
        snapshot()
    else:
        status = "PASS_ALL_FIVE_ENGINEERING_CONTROLS"
    snapshot()
    return 0 if status == "PASS_ALL_FIVE_ENGINEERING_CONTROLS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
