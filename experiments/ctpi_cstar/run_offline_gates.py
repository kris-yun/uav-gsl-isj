from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run(cmd):
    p = subprocess.run(cmd, text=True, capture_output=True)
    return {
        "cmd": " ".join(map(str, cmd)),
        "returncode": p.returncode,
        "stdout": p.stdout[-4000:],
        "stderr": p.stderr[-4000:],
    }


def read_state(path: Path, missing_verdict: str) -> dict:
    if not path.is_file():
        return {"verdict": missing_verdict, "pass": False}
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--m3-panel", type=Path)
    args = ap.parse_args()
    root = Path(__file__).resolve().parent
    args.out_dir.mkdir(parents=True, exist_ok=True)

    jobs = [
        run([
            sys.executable, str(root / "m1_picr/offline.py"),
            "--manifest", str(args.manifest),
            "--output", str(args.out_dir / "M1_PREMISE.json"),
        ]),
        run([
            sys.executable, str(root / "m2_cpo/offline.py"),
            "--manifest", str(args.manifest),
            "--output", str(args.out_dir / "M2_PREMISE.json"),
        ]),
    ]

    m1 = read_state(args.out_dir / "M1_PREMISE.json", "M1_PREMISE_MISSING")
    m2 = read_state(args.out_dir / "M2_PREMISE.json", "M2_PREMISE_MISSING")

    m3 = {
        "contract": "CSTAR_M3_STAGE_STATUS_V1",
        "pass": None,
        "verdict": "M3_NOT_REQUESTED_IN_SPENT_PREMISE_STAGE",
        "scientific_no_go": False,
    }
    if args.m3_panel is not None:
        jobs.append(run([
            sys.executable, str(root / "m3_phs/offline_panel.py"),
            "--panel", str(args.m3_panel),
            "--output", str(args.out_dir / "M3_GATE.json"),
        ]))
        m3 = read_state(args.out_dir / "M3_GATE.json", "M3_GATE_MISSING")

    premise_pass = m1.get("pass") is True and m2.get("pass") is True
    report = {
        "contract": "CSTAR_SPENT_OFFLINE_REPLAY_ORCHESTRATOR_V3",
        "jobs": jobs,
        "m1_spent_premise": m1,
        "m2_spent_observational_premise": m2,
        "m3_stage": m3,
        "spent_m1_m2_premise_pass": premise_pass,
        "formal_closed_loop_authorized": False,
        "stage_semantics": (
            "M3 is not required for the spent M1/M2 premise screen. A missing M3 panel at this "
            "stage is NOT a scientific M3 failure. M3 is evaluated later only after a genuine "
            "same-context multi-route counterfactual panel exists."
        ),
        "authorization_rule": (
            "Spent replay never authorizes formal closed loop. Formal M1/M2 gate producers, "
            "real route/intervention identity, destructive controls, frozen checkpoint hashes, "
            "M3 counterfactual evidence, cstar_v1 production integration and full-stack smoke "
            "must all exist before authorize_closed_loop.py can pass."
        ),
        "verdict": (
            "CSTAR_SPENT_M1_M2_PREMISE=PASS"
            if premise_pass
            else "CSTAR_SPENT_M1_M2_PREMISE=NO_GO_OR_BLOCKED"
        ),
    }
    (args.out_dir / "CSTAR_OFFLINE_SUMMARY.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(report["verdict"])
    print("CSTAR_FORMAL_CLOSED_LOOP_AUTHORIZED=FALSE")
    return 0 if premise_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
