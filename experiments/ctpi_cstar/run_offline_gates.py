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
            "--output", str(args.out_dir / "M1_GATE.json"),
        ]),
        run([
            sys.executable, str(root / "m2_cpo/offline.py"),
            "--manifest", str(args.manifest),
            "--output", str(args.out_dir / "M2_GATE.json"),
        ]),
    ]
    panel = args.m3_panel or (args.out_dir / "MISSING_COUNTERFACTUAL_PANEL.json")
    jobs.append(run([
        sys.executable, str(root / "m3_phs/offline_panel.py"),
        "--panel", str(panel),
        "--output", str(args.out_dir / "M3_GATE.json"),
    ]))

    states = []
    for name in ("M1", "M2", "M3"):
        path = args.out_dir / f"{name}_GATE.json"
        states.append(
            json.loads(path.read_text(encoding="utf-8"))
            if path.is_file()
            else {"verdict": f"{name}_MISSING", "pass": False}
        )

    replay_all_pass = all(state.get("pass") is True for state in states)
    report = {
        "contract": "CSTAR_SPENT_OFFLINE_REPLAY_ORCHESTRATOR_V2",
        "jobs": jobs,
        "modules": states,
        "offline_replay_all_pass": replay_all_pass,
        "formal_closed_loop_authorized": False,
        "authorization_rule": (
            "Spent/fixed-trajectory replay is a premise and implementation screen only. "
            "Formal closed loop requires separate controlled/source-diverse M1 and M2 evidence, "
            "a genuine M3 counterfactual panel, frozen model hashes, production-mode integration, "
            "and a causal runtime smoke audit. Use authorize_closed_loop.py after those artifacts exist."
        ),
        "verdict": (
            "CSTAR_SPENT_OFFLINE_REPLAY=PASS"
            if replay_all_pass
            else "CSTAR_SPENT_OFFLINE_REPLAY=NO_GO_OR_BLOCKED"
        ),
    }
    (args.out_dir / "CSTAR_OFFLINE_SUMMARY.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(report["verdict"])
    print("CSTAR_FORMAL_CLOSED_LOOP_AUTHORIZED=FALSE")
    return 0 if replay_all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
