#!/usr/bin/env python3
"""Small deterministic tests for CTT H01 bank parsing and sensor memory."""

from __future__ import annotations

import struct
import tempfile
from pathlib import Path

import numpy as np

from ctt_h01_wind_bank_io import (
    FIRST_PASSAGE_THRESHOLD_PPM,
    STREAM_MAGIC,
    WIND_MAGIC,
    first_passage,
    read_physical,
    read_wind,
    sensor_forward,
)


def write(path: Path, magic: bytes, arrays: list[np.ndarray], width: int) -> None:
    with path.open("wb") as target:
        target.write(magic)
        target.write(struct.pack("<I", len(arrays)))
        target.write(struct.pack(f"<{len(arrays)}I", *(len(array) for array in arrays)))
        for array in arrays:
            target.write(np.asarray(array, dtype="<f4").reshape(-1, width).tobytes())


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        physical = [np.arange(4, dtype=np.float32), np.ones(3, dtype=np.float32)]
        write(root / "p.bin", STREAM_MAGIC, physical, 1)
        loaded = read_physical(root / "p.bin")
        assert all(np.array_equal(left, right) for left, right in zip(physical, loaded))
        wind = [np.arange(12, dtype=np.float32).reshape(4, 3)]
        write(root / "w.bin", WIND_MAGIC, wind, 3)
        assert np.array_equal(wind[0], read_wind(root / "w.bin")[0])
    impulse = np.zeros(100, dtype=np.float64)
    impulse[0] = 1.0
    measured = sensor_forward(impulse)
    assert measured[0] == 0.0 and measured[1] == 0.0 and measured[2] > 0.0
    continuation = sensor_forward(np.concatenate([np.zeros(20), np.ones(80)]))
    assert np.all(np.diff(continuation[22:]) >= -1e-12)
    no_hit = np.full(80, FIRST_PASSAGE_THRESHOLD_PPM)
    assert first_passage(no_hit) == 80
    hit = no_hit.copy(); hit[17] = FIRST_PASSAGE_THRESHOLD_PPM + 1e-6
    assert first_passage(hit) == 17
    print("CTT_H01_WIND_BANK_SELFTEST=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
