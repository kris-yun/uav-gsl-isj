#!/usr/bin/env python3
"""Record and package the frozen SOLICM-G0 numerical interruption."""
import hashlib
import io
import json
import tarfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "evidence/solicm_v0/g0"
RUNS = Path(r"D:\ZYC\A-gas\_staging\SOLICM_G0_RUNS_20260926")
FAILED = Path(r"D:\ZYC\A-gas\_staging\SOLICM_G0_RUNS_20260926_FAILED")
PACKAGE = Path(r"D:\ZYC\A-gas\_staging\SOLICM_G0_INCOMPLETE_REVIEW_20260926.tar.gz")


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main():
    locksha = sha(OUT / "SOLICM_G0_PRE_RUN_LOCK.json")
    completed = sorted(RUNS.glob("*/COMPLETE.json"))
    assert len(completed) == 49, len(completed)
    completed_names = []
    for p in completed:
        done = json.loads(p.read_text())
        assert done["pre_run_lock_sha256"] == locksha
        assert sha(p.parent / "heldout_logits.npy") == done["heldout_logits_sha256"]
        assert sha(p.parent / "best_checkpoint.pt") == done["checkpoint_sha256"]
        completed_names.append(p.parent.name)
    failed_id = "W2_to_W0__fold0__seed0__PL_ONLY"
    first = FAILED / (failed_id + "_first_attempt") / "config.json"
    retry = FAILED / (failed_id + "_retry") / "config.json"
    assert first.exists() and retry.exists() and sha(first) == sha(retry)
    config = json.loads(first.read_text())
    assert config["pre_run_lock_sha256"] == locksha
    assert config["direction"] == "W2_to_W0" and config["fold"] == 0
    assert config["seed"] == 0 and config["variant"] == "PL_ONLY"
    log = FAILED / (failed_id + "_retry_stdout.txt")
    diagnostic = FAILED / (failed_id + "_diagnostic.txt")
    logtext = log.read_text()
    assert all(f"EPOCH {failed_id} {n} source_risk nan" in logtext for n in (10, 20, 30, 40))
    assert "AssertionError" in logtext
    diagnostic_text = diagnostic.read_text()
    assert "bad_params []" in diagnostic_text
    assert "running_var" in diagnostic_text and "eval_source_risk nan" in diagnostic_text
    bank = np.load(OUT / "SOLICM_G0_H02_W0_W2_16x10x30.npy", allow_pickle=False)
    assert bank.shape == (2, 6, 16, 10, 30)
    src = bank[1].reshape(96, 10, 30).astype(np.float64)
    tgt = bank[0].reshape(96, 10, 30).astype(np.float64)
    std = src.std(axis=(0, 1))
    std[std == 0] = 1
    scaled = (tgt - src.mean(axis=(0, 1))) / std
    result = {
        "status": "SOLICM_G0_INCOMPLETE_NUMERICAL_FAILURE",
        "scientific_decision": None,
        "frozen_gates_evaluated": False,
        "new_plume_runs": 0,
        "completed_training_runs": 49,
        "planned_training_runs": 96,
        "completed_run_ids": completed_names,
        "failed_run_id": failed_id,
        "repeat_attempt_count": 2,
        "failure": "At all four frozen checkpoint epochs, source evaluation risk is NaN. Exact rerun repeated the failure. Diagnostic rerun found finite model parameters but nonfinite feature-extractor BatchNorm running statistics by epoch 1-2 after target-domain batches.",
        "source_scaler_std_min_nonzero": float(std.min()),
        "target_scaled_abs_max": float(np.abs(scaled).max()),
        "target_scaled_abs_p99": float(np.quantile(np.abs(scaled), .99)),
        "input_bank_sha256": sha(OUT / "SOLICM_G0_H02_W0_W2_16x10x30.npy"),
        "pre_run_lock_sha256": locksha,
        "failed_config_sha256": sha(first),
        "retry_stdout_sha256": sha(log),
        "diagnostic_stdout_sha256": sha(diagnostic),
        "interpretation": "Input source/probe correspondence passed A0. This is a numerical failure of the pinned implementation under the frozen source-only z-score and target batches. No PASS/HOLD/STOP scientific gate is assigned because all four arms were not valid across both directions.",
        "upstream_pseudolabel_caveat": "Pinned classifier softmax followed by a second six-class softmax cannot exceed the 0.99 pseudo-label threshold."
    }
    resultfile = OUT / "SOLICM_G0_INCOMPLETE_RESULT.json"
    resultfile.write_bytes((json.dumps(result, sort_keys=True, indent=2) + "\n").encode("utf-8"))
    include = {}
    for p in OUT.rglob("*"):
        if p.is_file():
            include[f"evidence/solicm_v0/g0/{p.relative_to(OUT).as_posix()}"] = p
    for p in (ROOT / "research/solicm_v0").rglob("*"):
        if p.is_file() and p.suffix != ".pyc":
            include[f"research/solicm_v0/{p.relative_to(ROOT / 'research/solicm_v0').as_posix()}"] = p
    for p in RUNS.rglob("*"):
        if p.is_file():
            include[f"runs/{p.relative_to(RUNS).as_posix()}"] = p
    for p in FAILED.rglob("*"):
        if p.is_file():
            include[f"failed_runs/{p.relative_to(FAILED).as_posix()}"] = p
    inventory = "".join(f"{sha(p)}  {name}\n" for name, p in sorted(include.items())).encode()
    if PACKAGE.exists():
        raise FileExistsError(PACKAGE)
    with tarfile.open(PACKAGE, "w:gz") as tar:
        for name, p in sorted(include.items()):
            tar.add(p, arcname=name, recursive=False)
        info = tarfile.TarInfo("SHA256SUMS")
        info.size = len(inventory)
        tar.addfile(info, io.BytesIO(inventory))
    with tarfile.open(PACKAGE, "r:gz") as tar:
        lines = tar.extractfile("SHA256SUMS").read().decode().splitlines()
        assert len(lines) == len(include)
        for line in lines:
            expected, name = line.split("  ", 1)
            assert hashlib.sha256(tar.extractfile(name).read()).hexdigest() == expected, name
    print(json.dumps({"status": result["status"], "scientific_decision": None,
                      "package": str(PACKAGE), "bytes": PACKAGE.stat().st_size,
                      "sha256": sha(PACKAGE), "files": len(include) + 1}, indent=2))


if __name__ == "__main__":
    main()
