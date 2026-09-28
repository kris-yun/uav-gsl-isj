"""Add an opt-in 300 s causal frame mode to the existing VGR timebase.

The old seeded_time_replay and fixed_debug modes remain byte-for-byte intact.
This installer is anchored to the audited VM source SHA and makes a backup.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import py_compile


TARGET = Path("/home/zyc/ros2_ws/src/vgr_bridge/vgr_bridge/sim_timebase.py")
EXPECTED = "a104873911f23c27dba39001d1919092a5f58195f03e37f86fc76b0040c4351f"
BACKUP = TARGET.with_name(TARGET.name + ".pre_brg_v1_20260928")
MARKER = '        if mode == "physical_time_replay_300s":'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    before = TARGET.read_text()
    if MARKER in before:
        raise RuntimeError("optional physical replay already installed; inspect before rerun")
    if sha(TARGET) != EXPECTED:
        raise RuntimeError("VM VGR source drift; refusing automatic patch")
    if BACKUP.exists():
        if sha(BACKUP) != EXPECTED:
            raise RuntimeError("existing VGR backup SHA mismatch")
    else:
        BACKUP.write_bytes(TARGET.read_bytes())
    import_anchor = "import math\n"
    if before.count(import_anchor) != 1:
        raise RuntimeError("VGR import anchor mismatch")
    after = before.replace(import_anchor, import_anchor + "import bisect\nimport functools\nimport struct\n")
    class_anchor = "@dataclass\nclass DeterministicTimebase:"
    helper = '''def _f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


@functools.lru_cache(maxsize=1)
def _physical_frame_times_300s() -> tuple[float, ...]:
    t, last_save = _f32(0), -_f32(3.4028234663852886e38)
    times = []
    while t < _f32(300):
        if t > _f32(last_save + _f32(.5)):
            times.append(t)
            last_save = t
        t = _f32(t + _f32(.1))
    if len(times) != 566 or abs(times[-1] - 299.80908203125) > 1e-6:
        raise RuntimeError("GADEN writer time-map parity failed")
    return tuple(times)


'''
    if after.count(class_anchor) != 1:
        raise RuntimeError("VGR class anchor mismatch")
    after = after.replace(class_anchor, helper + class_anchor)
    mode_anchor = '        if mode == "seeded_time_replay":\n'
    mode_code = '''        if mode == "physical_time_replay_300s":
            if max_iteration != 565:
                raise ValueError("frozen 300s physical replay requires frames 0..565")
            return max(0, min(max_iteration,
                bisect.bisect_right(_physical_frame_times_300s(), self.time_s) - 1))
'''
    if after.count(mode_anchor) != 1:
        raise RuntimeError("VGR mode anchor mismatch")
    after = after.replace(mode_anchor, mode_code + mode_anchor)
    TARGET.write_text(after)
    py_compile.compile(str(TARGET), doraise=True)
    provenance = {"target": str(TARGET), "backup": str(BACKUP),
                  "original_sha256": EXPECTED, "patched_sha256": sha(TARGET),
                  "mode": "physical_time_replay_300s", "frame_count": 566,
                  "writer_config": {"duration_s": 300, "delta_s": 0.1, "save_interval_s": 0.5}}
    out = Path("/home/zyc/brg_v1_recovery_20260928/VGR_PHYSICAL_REPLAY_PATCH.json")
    out.write_text(json.dumps(provenance, indent=2) + "\n")
    print(json.dumps(provenance))


if __name__ == "__main__":
    main()
