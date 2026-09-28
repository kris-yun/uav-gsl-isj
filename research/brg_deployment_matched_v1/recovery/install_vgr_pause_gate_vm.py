"""Prevent paused t=0 pseudo-samples in the opt-in BRG V1 physical replay."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import py_compile

TARGET = Path("/home/zyc/brg_closedloop_20260927/vgr_execution_v2/vgr_bridge/vgr_sim_node.py")
EXPECTED = "02c43e2b35f388d4428bc89bc694e8cf837daaf86882bf5587ace42be433c252"
OLD = "if str(self.get_parameter('gaden_iteration_mode').value) == 'recorded_snapshot_time_replay':\n            publish_observation = advancing and within_evidence_horizon"
NEW = "if str(self.get_parameter('gaden_iteration_mode').value) in ('recorded_snapshot_time_replay', 'physical_time_replay_300s'):\n            publish_observation = advancing and within_evidence_horizon"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if sha(TARGET) != EXPECTED:
        raise RuntimeError("VGR overlay drift; refusing startup gate patch")
    source = TARGET.read_text()
    if source.count(OLD) != 1:
        raise RuntimeError("paused-publish anchor mismatch")
    backup = TARGET.with_name(TARGET.name + ".pre_brg_v1_pause_gate_20260928")
    if backup.exists():
        if sha(backup) != EXPECTED:
            raise RuntimeError("existing pause-gate backup mismatch")
    else:
        backup.write_bytes(TARGET.read_bytes())
    TARGET.write_text(source.replace(OLD, NEW))
    py_compile.compile(str(TARGET), doraise=True)
    result = {"status": "VGR_PAUSED_T0_OBSERVATION_GATE_INSTALLED", "target": str(TARGET),
              "backup": str(backup), "original_sha256": EXPECTED,
              "patched_sha256": sha(TARGET),
              "cause": "new physical replay mode inherited paused readiness gas/wind publishing",
              "changed_behavior": "withhold gas/wind while clock paused at t=0 in physical mode"}
    out = Path("/home/zyc/brg_v1_recovery_20260928/VGR_PAUSE_GATE_PATCH.json")
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
